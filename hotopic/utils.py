import logging
import numpy as np
from hotopic.backend import OpenAIBackend
from hotopic.config import SecureConfigManager
import openai
from datetime import datetime

class MyLogger:
    def __init__(self):
        self.logger = logging.getLogger("hotopic")

    def configure(self, level):
        self.set_level(level)
        self._add_handler()
        self.logger.propagate = False

    def info(self, message):
        self.logger.info(f"{message}")

    def warning(self, message):
        self.logger.warning(f"WARNING: {message}")

    def set_level(self, level):
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if level in levels:
            self.logger.setLevel(level)

    def _add_handler(self):
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(message)s"))
        self.logger.addHandler(sh)

        # Remove duplicate handlers
        if len(self.logger.handlers) > 1:
            self.logger.handlers = [self.logger.handlers[0]]

class DiscussData:
    _id = None
    _title = None
    _url = None
    _cleaned_data = None
    _created_at = None
    _topic_summary = None
    _source_type = None
    _source_id = None
    _source_closed = False
    _similarity = None
    _closed_similarity = None
    def __init__(self, id, title, url, cleaned_data, created_at,
                 topic_summary, source_type, source_id, source_closed=False):
        self._id = id
        self._title = title
        self._url = url
        self._cleaned_data = cleaned_data
        self._created_at = created_at
        # 话题摘要。刚聚类的话题，还没有生成摘要，设置为cluster id
        self._topic_summary = topic_summary
        self._source_type = source_type
        self._source_id = source_id
        self._source_closed = source_closed
        self._similarity = 0.0
        self._closed_similarity = 0.0
    
    def get_summary(self):
        return self._topic_summary
    
    def set_summary(self, summary):
        self._topic_summary = summary
    
    def get_id(self):
        return self._id
    
    def get_title(self):
        return self._title
    
    def get_url(self):
        return self._url
    
    def get_created_at(self):
        return self._created_at
    
    def get_source_type(self):
        return self._source_type
    
    def get_source_id(self):
        return self._source_id
    
    def get_source_closed(self):
        return self._source_closed

    def get_cleaned_content(self):
        content = f"- title: {self._title}\n- abstract: {self._cleaned_data}"
        return content[:768]
    
    def get_content(self):
        return self._cleaned_data[:1024]
    
    def set_similarity(self, similarity):
        """设置相似度"""
        self._similarity = similarity

    def get_similarity(self):
        """获取相似度"""
        return self._similarity
    
    def set_closed_similarity(self, similarity):
        """设置关闭相似度"""
        self._closed_similarity = similarity

    def get_closed_similarity(self):
        """获取关闭相似度"""
        return self._closed_similarity
    
    def to_dict(self, return_cleaned_data=True):
        """返回对象的字典表示，用于JSON序列化。"""
        created_at_str = self._created_at
        # 如果 _created_at 是 datetime 对象，转换为 ISO 格式字符串
        if isinstance(self._created_at, datetime):
            created_at_str = self._created_at.isoformat()
        # 如果 _created_at 已经是字符串或 None，则直接使用
        if not return_cleaned_data:
            return {
                "id": self._id,
                "title": self._title,
                "url": self._url,
                "created_at": created_at_str, 
                "topic_summary": self._topic_summary,
                "source_type": self._source_type,
                "source_id": self._source_id,
                "source_closed": self._source_closed,
                "cosine": self._similarity,
                "closed_cosine": self._closed_similarity
            }

        return {
            "id": self._id,
            "title": self._title,
            "url": self._url,
            "clean_data": self._cleaned_data,
            "created_at": created_at_str, 
            "topic_summary": self._topic_summary,
            "source_type": self._source_type,
            "source_id": self._source_id,
            "source_closed": self._source_closed,
            "cosine": self._similarity,
            "closed_cosine": self._closed_similarity
        }

def cosine_distance(a, b):
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    cosine_sim = dot_product / (norm_a * norm_b)
    return cosine_sim

def get_embedding_model():
    config_manager = SecureConfigManager(
        plain_config_path="conf/config.yaml",
        sensitive_config_path="conf/config.ini"
    )
    api_key = config_manager.get_sensitive('llm', 'api-key')
    base_url = config_manager.get_plain('llm', 'base_url')
    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    model_name = config_manager.get_plain('llm', 'embedding_name')
    if not model_name:
        raise ValueError("Embedding model name is not configured in config.yaml")
    embedding_model = OpenAIBackend(client, model_name, batch_size=32)
    return embedding_model

def decode_topics(discuss_list, using_embedding=False):
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
        # 按 created_at 降序排序
        cluster.sort(key=lambda item: item.get_created_at(), reverse=True)
        topics_map[topic] = {
            "summary": summary,
            "discussion_count": len(cluster),
            "discussion": cluster
        }
        topic_id += 1

    return topics_map
