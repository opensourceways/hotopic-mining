from hotopic.input_data import fetch_all_data
from hotopic.config import SecureConfigManager

def test_fetch_all_data():
    config = SecureConfigManager(
        plain_config_path="conf/config.yaml",
        sensitive_config_path="conf/config.ini"
    )
    base_url = config.get_plain('data', 'soure_url')
    res = fetch_all_data(base_url)
    # print(res[0])
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
