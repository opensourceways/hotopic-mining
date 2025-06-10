from hotopic.backend import OpenAIBackend
import openai
import pytest
try:
    from conftest import should_skip_unless_run_flag
except ImportError:
    print("Warning: conftest.should_skip_unless_run_flag not found, direct logic might be brittle.")
    pass # 保持使用导入版本的逻辑

@pytest.mark.skipif(should_skip_unless_run_flag(True), reason="需要指定真实的API_KEY")
def test_openai_backend():
    # 运行测试用例: python -m pytest
    # 需要填真实的 API Key 和 Base URL
    API_KEY = "sk-xxxxx"
    BASE_URL = "https://api.siliconflow.cn/v1"
    # EMBEDDING_MODLE = "BAAI/bge-m3"
    EMBEDDING_MODLE = "BAAI/bge-large-zh-v1.5"

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
    print("Vectors shape:", vectors.shape)
    assert vectors.shape == (5, 1024), "Expected shape (5, 768) for the embeddings"