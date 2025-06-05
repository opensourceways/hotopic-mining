from hotopic.backend import OpenAIBackend
from hotopic.utils import MyLogger
import openai

logger = MyLogger()
logger.configure("WARNING")
# logger.configure("INFO")

if __name__ == "__main__":
    API_KEY = "sk-xxxx"
    BASE_URL = "https://api.siliconflow.cn/v1"
    # EMBEDDING_MODLE = "BAAI/bge-m3"
    EMBEDDING_MODLE = "BAAI/bge-large-zh-v1.5"
    logger.info("Embedding - Transforming documents to embeddings.")

    def get_embedding_model(model_name):
        client = openai.OpenAI(api_key=API_KEY, base_url=BASE_URL)
        embedding_model = OpenAIBackend(client, model_name, batch_size=32)
        return embedding_model
    
    embedding_model = get_embedding_model(EMBEDDING_MODLE)
    texts = [
        "你好，世界！",
        "这是一个测试文本。",
        "我喜欢编程和人工智能。",
        "机器学习是未来的趋势。",
        "自然语言处理是计算机科学的一个重要分支。"
    ]
    vectors = embedding_model.embed(texts)
    logger.warning(f"Vectors shape: {vectors.shape}")