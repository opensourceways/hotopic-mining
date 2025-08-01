from hotopic.config import SecureConfigManager
from hotopic.utils import MyLogger, decode_topics
from openai import OpenAI
from tqdm import tqdm
import time
import json

logger = MyLogger()
# logger.configure("WARNING")
logger.configure("INFO")

class Summary:
    _clustered_topics = None
    _summary_prompt = None
    _reranker_prompt = None
    _base_url = None
    _llm_model = None
    _rerank_llm_model = None
    _api_key = None
    def __init__(self):
        self._clustered_topics = {}
        config_manager = SecureConfigManager(
            plain_config_path="conf/config.yaml",
            sensitive_config_path="conf/config.ini"
        )
        self._base_url = config_manager.get_plain('llm', 'base_url')
        self._llm_model = config_manager.get_plain('llm', 'model_name')
        self._rerank_llm_model = config_manager.get_plain('llm', 'rerank_model_name')
        self._api_key = config_manager.get_sensitive('llm', 'api-key')
        self._summary_prompt = config_manager.get_plain('llm', 'summary_prompt')    
        self._reranker_prompt = config_manager.get_plain('llm','reranker_prompt')    

    def add_topics_from_discuss_list(self, clustered_list):
        if clustered_list:
            self._clustered_topics = decode_topics(clustered_list)

    def llm_summarize(self, content, model_name="deepseek-ai/DeepSeek-R1", system_prompt=None):
        """Use LLM to summarize the topic."""
        # Placeholder for LLM summarization logic
        # This should call an LLM API to generate a summary based on topic_info
        
        start_time = time.time()
        openai_api_key = self._api_key
        openai_api_base = self._base_url
        # logger.info(f"Using model: {model_name}, api_key: {openai_api_key}, base_url: {openai_api_base}")
        # logger.info(f"system_prompt: {system_prompt}")
        client = OpenAI(
            api_key=openai_api_key,
            base_url=openai_api_base,
        )
        try:         
        
            chat_outputs = client.chat.completions.create(
                model = model_name,
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content},
                ]
            )
        except Exception as e:
            logger.error(f"LLM API调用失败: {e}")
            return "<summary>LLM API调用失败，请稍后重试。</summary>"
        # print(chat_outputs.choices[0].message.content)
        end_time = time.time()
        elapsed_time= end_time - start_time
        logger.info(f"exec time: {elapsed_time} s")
        return chat_outputs.choices[0].message.content
    
    def summarize_clustered_topics(self):
        """Summarize topics using a summarizer."""
        with tqdm(self._clustered_topics.items(), desc="📊 处理进度", unit="topic", bar_format="{l_bar}{bar:20}{r_bar}") as pbar:
            for topic, contents in pbar:
                logger.info(f"\ntopic id: {topic}, cluster size: {len(contents['discussion'])}, titles:")
                content_titles = ""
                content_block = ""
                for discuss in contents["discussion"]:
                    content_titles += f"{discuss.get_title()}\n"
                    content_block += f"{discuss.get_content()}\n"
                logger.info(content_titles)
                content = f"""
                以下是社区关于该热点话题的标题和部分内容：
                标题：{content_titles}
                内容：{content_block}
                """
                llm_summary_result = self.llm_summarize(content, model_name=self._llm_model, system_prompt=self._summary_prompt)
                logger.info(f"topic id: {topic} summary: {llm_summary_result}")
                if '<summary>' in llm_summary_result:
                    summary = llm_summary_result.split('<summary>')[1].split('</summary>')[0].strip()
                    self._clustered_topics[topic]["summary"] = summary


    def reranker_clustered_topics(self):
        """Rerank topics using llm reranker."""
        tmp_texts = ""
        for topic, contents in self._clustered_topics.items():
            summary = contents.get("summary", "")
            tmp_texts += f"Topic: {topic}\nSummary: {summary}\n"
            tmp_texts += "Discussions:\n"
            discussion = contents.get("discussion", [])
            discussion_text = ""
            for i, discuss in enumerate(discussion):
                # logger.info(f"Topic: {topic}, Discussion {i+1}: {discuss}")
                title = discuss.get_title()
                discussion_text += f"{i+1}. {title}\n"
            tmp_texts += discussion_text
            tmp_texts += "\n"
    
        logger.info(f"Reranking llm input size: {len(tmp_texts)}\n")
        llm_rerank_result = self.llm_summarize(tmp_texts, model_name=self._rerank_llm_model,
                                               system_prompt=self._reranker_prompt)
        logger.info(f"Reranked Content: {llm_rerank_result}\n")
        if "<reranker>" in llm_rerank_result:
            llm_rerank_result = llm_rerank_result.split("<reranker>")[1].split("</reranker>")[0]
        try:
            reranked_content = json.loads(llm_rerank_result)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解码错误: {e}")
            return
        new_reranked_content = {}
        new_index = 0
        for _, item in enumerate(reranked_content):
            try:
                origin_id = item.get("topic")
            except Exception as e:
                logger.error(f"KeyError: {e} in item: {item}")
                return
            if not origin_id:
                continue
            content = self._clustered_topics.get(str(origin_id), {})
            if not content:
                continue
            content["label"] = item.get("label", "")
            new_reranked_content[str(new_index)] = content
            new_index += 1
            del self._clustered_topics[str(origin_id)]
        for _, item in enumerate(self._clustered_topics):
            content = self._clustered_topics.get(str(item), {})
            if not content:
                continue
            new_reranked_content[str(new_index)] = content
            new_index += 1
        
        self._clustered_topics = new_reranked_content
        logger.info(f"Reranked Topics: {len(self._clustered_topics)}")

    def get_clustered_topics(self):
        """get clustered topics."""
        return self._clustered_topics


    def summarize_pipeline(self, clustered_list):
        self.add_topics_from_discuss_list(clustered_list)
        self.summarize_clustered_topics()
        logger.info("话题摘要生成完成。")
        # 话题排序单独调试
        self.reranker_clustered_topics()
        res = self.get_clustered_topics()
        # logger.info(f"merge topics: {res}")
        return res
