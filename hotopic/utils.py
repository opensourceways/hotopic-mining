import logging
import numpy as np
from hotopic.backend import OpenAIBackend
from hotopic.config import SecureConfigManager
import openai

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
    _body = None
    _url = None
    _cleaned_data = None
    _created_at = None
    _topic_summary = None
    _source_type = None
    _source_id = None
    def __init__(self, id, title, body, url, cleaned_data,
                 created_at, topic_summary, source_type, source_id):
        self._id = id
        self._title = title
        self._body = body
        self._url = url
        self._cleaned_data = cleaned_data
        self._created_at = created_at
        # 话题摘要。刚聚类的话题，还没有生成摘要，设置为cluster id
        self._topic_summary = topic_summary
        self._source_type = source_type
        self._source_id = source_id
    
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

    def get_cleaned_content(self):
        content = f"- title: {self._title}\n- abstract: {self._cleaned_data}"
        return content[:768]
    
    def get_content(self):
        return self._cleaned_data[:1024]

def cosine_distance(a, b):
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    cosine_sim = dot_product / (norm_a * norm_b)
    return cosine_sim

def get_embedding_model():
    config_manager = SecureConfigManager(
        plain_config_path="config.yaml",
        sensitive_config_path="config.ini"
    )
    api_key = config_manager.get_sensitive('llm', 'api-key')
    base_url = config_manager.get_plain('llm', 'base_url')
    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    model_name = config_manager.get_plain('llm', 'embedding_name')
    if not model_name:
        raise ValueError("Embedding model name is not configured in config.yaml")
    embedding_model = OpenAIBackend(client, model_name, batch_size=32)
    return embedding_model
