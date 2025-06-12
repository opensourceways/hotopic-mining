from hotopic.config import SecureConfigManager

def test_config():
    # 首次初始化
    config = SecureConfigManager(
        plain_config_path="conf/config.yaml",
        sensitive_config_path="conf/config.ini"
    )
    
    # 获取明文配置
    model_name = config.get_plain('llm', 'model_name')
    embedding_name = config.get_plain('llm', 'embedding_name')
    base_url = config.get_plain('llm', 'base_url')
    
    # 获取敏感配置
    openai_key = config.get_sensitive('llm', 'api-key')
    
    # 列出所有敏感配置分区
    sensitive_sections = config.list_sensitive_sections()
    assert model_name == "deepseek-ai/DeepSeek-R1", "模型名称不匹配"
    assert embedding_name == "BAAI/bge-large-zh-v1.5", "嵌入模型名称不匹配"
    assert openai_key == "sk-xxxxx", "OpenAI API Key 不匹配"
    assert sensitive_sections == ['llm'], "敏感配置分区不匹配"
    assert base_url == "https://api.siliconflow.cn/v1", "Base URL 不匹配"

