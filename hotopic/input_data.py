import requests
import json
import time
from hotopic.utils import MyLogger
from hotopic.config import SecureConfigManager

logger = MyLogger()
logger.configure("INFO")

def fetch_all_data(base_url):
    all_data = []
    page = 1
    page_size=100
    total_pages = None
    total_num = 0
    
    while total_pages is None or page <= total_pages:
        # 添加分页参数
        url = f"{base_url}?page={page}&page_size={page_size}"
        logger.info(f"正在获取第 {page} 页数据...")
        try:
            response = requests.get(url)
            response.raise_for_status()  # 检查HTTP错误
            data = response.json()
            # 首次请求时获取总页数
            if total_pages is None:
                total_pages = data['pagination']['total_pages']
                total_num = data['pagination']['total_items']
                logger.info(f"总页数: {total_pages}, 总数据量: {total_num}")
            # 添加当前页数据
            all_data.extend(data['data'])
            # 显示进度
            logger.info(f"已获取 {len(data['data'])} 条数据，累计 {len(all_data)} 条, 总数据量: {total_num}")
            # 更新页码
            page += 1
            # 避免请求过快 (每0.5秒1次)
            time.sleep(0.5)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {e}")
            break
        except json.JSONDecodeError:
            logger.warning("响应解析失败")
            break
    
    return all_data

def get_input_data():
    config = SecureConfigManager(
        plain_config_path="conf/config.yaml",
        sensitive_config_path="conf/config.ini"
    )
    base_url = config.get_plain('data','soure_url')
    res = fetch_all_data(base_url)
    return res

if __name__ == "__main__":
    base_url = "https://hotopic-data.test.osinfra.cn/openubmc/api/v1/data"
    
    # 获取所有数据
    complete_data = fetch_all_data(base_url)
    
    # 保存到文件
    filename = "tests/mock_data/openubmc_complete_data.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            "status": "success",
            "count": len(complete_data),
            "data": complete_data
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n所有数据已保存到 {filename}")
    print(f"共获取 {len(complete_data)} 条记录")