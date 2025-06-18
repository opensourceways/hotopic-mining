import requests
import json
import time
from hotopic.utils import MyLogger
from hotopic.config import SecureConfigManager

logger = MyLogger()
logger.configure("INFO")

def encode_topics_output_data(clustered_result):
    clusterd_list = []
    for _, cluster in clustered_result.items():
        clusterd_list.append(cluster)
    
    return clusterd_list

def publish_all_data(base_url, output_data):
    """
    发布所有数据
    """
    headers = {
        "Content-Type": "application/json"
    }

    publish_data = encode_topics_output_data(output_data)
    payload = {
        "data": publish_data
    }

    try:
        start_time = time.time()
        response = requests.post(
            base_url,
            headers=headers,
            json=payload  # 自动序列化为JSON并设置Content-Type
        )
        
        # 输出响应结果
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response Body:\n{response.text}")
        end_time = time.time()
        logger.info(f"Request time: {end_time - start_time}s")
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return False

def post_output_data(output_data):
    config = SecureConfigManager(
        plain_config_path="conf/config.yaml",
        sensitive_config_path="conf/config.ini"
    )
    base_url = config.get_plain('data','publish_url')
    res = publish_all_data(base_url, output_data)
    if res:
        logger.info("发布成功")
    else:
        logger.error("发布失败")

if __name__ == "__main__":
    base_url = 'https://hotopic-data.test.osinfra.cn/internal/v1/hot-topic/openubmc/to-review'
    with open('tests/mock_data/clustered_run_2025_06_17.json', 'r') as clustered_file:
        clustered_data = json.load(clustered_file)
    res = publish_all_data(base_url, clustered_data)
    if res:
        logger.info("发布成功")
    else:
        logger.error("发布失败")
