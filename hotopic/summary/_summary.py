from hotopic.config import SecureConfigManager
from hotopic.utils import MyLogger
from openai import OpenAI
from tqdm import tqdm
import time
import json

logger = MyLogger()
# logger.configure("WARNING")
logger.configure("INFO")

class Summary:
    _published_topics = None
    _clustered_topics = None
    _summary_prompt = None
    _reranker_prompt = None
    _base_url = None
    _llm_model = None
    _rerank_llm_model = None
    _api_key = None
    def __init__(self):
        self._published_topics = {}
        self._clustered_topics = {}
        config_manager = SecureConfigManager(
            plain_config_path="config.yaml",
            sensitive_config_path="config.ini"
        )
        self._base_url = config_manager.get_plain('llm', 'base_url')
        self._llm_model = config_manager.get_plain('llm', 'model_name')
        self._rerank_llm_model = config_manager.get_plain('llm', 'rerank_model_name')
        self._api_key = config_manager.get_sensitive('llm', 'api-key')
        self._summary_prompt = config_manager.get_plain('llm', 'summary_prompt')    
        self._reranker_prompt = config_manager.get_plain('llm','reranker_prompt')    


    def decode_topics(self, discuss_list):
        """Decode topics from discuss list using a mapping."""
        topic_clusters = {}
        for discuss in discuss_list:
            topic_summary = discuss.get_summary()
            if topic_summary not in topic_clusters:
                topic_clusters[topic_summary] = []
            topic_clusters[topic_summary].append(discuss)

        topic_id = 0
        topics_map = {}
        for summary, cluster in topic_clusters.items():
            if summary is None or summary.strip() == "":
                continue
            topic = str(topic_id)
            output_info = []
            output_info = []
            for discuss in cluster:
                output_info.append(
                    {
                        "id": discuss.get_id(),
                        "title": discuss.get_title(),
                        "url": discuss.get_url(),
                        "created_at": discuss.get_created_at(),
                        "source_type": discuss.get_source_type(),
                        "source_id": discuss.get_source_id(),
                        "source_closed": discuss.get_source_closed(),
                        "cosine": float(0.0), # round(float(cosine), 3) 保留3位小数
                        "content": discuss.get_content(), # 这个是完整内容，用于生成摘要
                    }
                )
            # 按 created_at 降序排序
            output_info.sort(key=lambda item: item["created_at"], reverse=True)
            topics_map[topic] = {
                "summary": summary,
                "discussion_count": len(output_info),
                "discussion": output_info
            }
            topic_id += 1

        return topics_map

    def add_topics_from_discuss_list(self, published_list, clustered_list):
        if published_list:
            self._published_topics = self.decode_topics(published_list)
        if clustered_list:
            self._clustered_topics = self.decode_topics(clustered_list)

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
        chat_outputs = client.chat.completions.create(
            model = model_name,
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ]
        )
        # print(chat_outputs.choices[0].message.content)
        end_time = time.time()
        elapsed_time= end_time - start_time
        logger.info(f"exec time: {elapsed_time} s")
        return chat_outputs.choices[0].message.content
    
    def summarize_clustered_topics(self):
        """Summarize topics using a summarizer."""
        with tqdm(self._clustered_topics.items(), desc="📊 处理进度", unit="topic", bar_format="{l_bar}{bar:20}{r_bar}") as pbar:
            for topic, contents in pbar:
                logger.info(f"\ntopic id: {topic}, cluster size: {len(contents)}, titles:")
                content_titles = ""
                content_block = ""
                for content in contents["discussion"]:
                    content_titles += f"{content["title"]}\n"
                    content_block += f"{content["content"]}\n"
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
            # print(f"Discussion Count: {discussion}")
            discussion_text = ""
            for i, doc in enumerate(discussion):
                discussion_text += f"{i+1}. {doc['title']}\n"
            tmp_texts += discussion_text
            tmp_texts += "\n"
    
        # logger.info(f"Reranking llm input: {tmp_texts}\n")
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
            origin_id = item.get("topic")
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

    def merge_published_and_clustered_topics(self):
        """Merge published topics and clustered topics."""
        merged_topics = {}
        for topic_id, topic_info in self._published_topics.items():
            discussion = topic_info.get("discussion", [])
            for item_dict in discussion:
                if 'content' in item_dict: # Good practice to check if the key exists
                    del item_dict['content']
            topic_info["discussion"] = discussion
            merged_topics[topic_id] = topic_info
        published_topic_num = len(merged_topics)
        for topic_id, topic_info in self._clustered_topics.items():
            topic_id = str(int(topic_id) + published_topic_num)
            discussion = topic_info.get("discussion", [])
            for item_dict in discussion:
                if 'content' in item_dict: # Good practice to check if the key exists
                    del item_dict['content']
            topic_info["discussion"] = discussion
            merged_topics[topic_id] = topic_info
        return merged_topics


    def summarize_pipeline(self, published_list, clustered_list):
        self.add_topics_from_discuss_list(published_list, clustered_list)
        self.summarize_clustered_topics()
        logger.info("话题摘要生成完成。")
        # 话题排序单独调试
        # self.reranker_clustered_topics()
        res = self.merge_published_and_clustered_topics()
        # logger.info(f"merge topics: {res}")
        return res
