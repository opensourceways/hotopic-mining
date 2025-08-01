from hotopic.input_data import fetch_all_data
from hotopic.config import SecureConfigManager
import json

def save_input_data(res):
    res_new = []
    i = 0
    for item in res:
        new_item = {
            "title": item.get('title'),
            "data": item.get('clean_data'),
            "url": item.get('url'),
            "closed": item.get('source_closed')
        }
        i = i + 1
        if i % 3 == 0:
            print(f"已处理 {i} 条数据")
            res_new.append(new_item)
    # 测试时输出聚类的结果
    with open('tests/mock_data/input_data_new_3.json', 'w') as discuss_file:
        json.dump(res_new, discuss_file, ensure_ascii=False, indent=4)

def test_fetch_all_data():
    config = SecureConfigManager(
        plain_config_path="conf/config.yaml",
        sensitive_config_path="conf/config.ini"
    )
    base_url = config.get_plain('data', 'soure_url')
    res = fetch_all_data(base_url)
    # print(res[0])
    save_input_data(res)
    assert res is not None
    assert len(res) > 0
    assert isinstance(res, list)
    assert res[0].get('id') is not None
    assert res[0].get('title') is not None
    assert res[0].get('url') is not None
    assert res[0].get('clean_data') is not None
    assert res[0].get('created_at') is not None
    assert res[0].get('topic_summary') is not None
    assert res[0].get('source_type') is not None
    assert res[0].get('source_id') is not None
    assert res[0].get('source_closed') is not None
