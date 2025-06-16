from hotopic.schedule_timer import hotopic_mining_pipeline
import pytest
try:
    from conftest import should_skip_unless_run_flag
except ImportError:
    print("Warning: conftest.should_skip_unless_run_flag not found, direct logic might be brittle.")
    pass # 保持使用导入版本的逻辑

# python -m pytest -vs tests/test_cluster.py --run-specific-skips
@pytest.mark.skipif(should_skip_unless_run_flag(True), reason="需要修改配置文件config.ini为真实的API_KEY")
def test_hotopic_mining_pipeline():
    res = hotopic_mining_pipeline(False)
    assert res is not None
    assert len(res) > 0
    assert isinstance(res, dict)
    assert res["0"].get('summary') is not None
    discussion = res["0"].get('discussion', [])
    assert discussion[0][0].get('id') is not None
    assert discussion[0][0].get('title') is not None
    assert discussion[0][0].get('url') is not None
    assert discussion[0][0].get('created_at') is not None
    assert discussion[0][0].get('source_type') is not None
    assert discussion[0][0].get('source_id') is not None
    assert discussion[0][0].get('source_closed') is not None
    assert discussion[0][0].get('cosine') is not None
    assert discussion[0][0].get('closed_cosine') is not None
    
