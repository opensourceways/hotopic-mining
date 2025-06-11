from hotopic.summary import Summary
from hotopic.utils import *
import pytest
import json
try:
    from conftest import should_skip_unless_run_flag
except ImportError:
    print("Warning: conftest.should_skip_unless_run_flag not found, direct logic might be brittle.")
    pass # 保持使用导入版本的逻辑

def load_input_data(mock_path):
    with open(mock_path, 'r') as graph_file:
        graph_data = json.load(graph_file)

    for key, value in graph_data.items():
        discussion = value.get('discussion', [])
        discuss_list = []
        for discuss in discussion:
            discuss_data = DiscussData(
                id=discuss.get('id'),
                title=discuss.get('title'),
                url=discuss.get('url'),
                cleaned_data=discuss.get('clean_data', ''),
                created_at=discuss.get('created_at'),
                topic_summary=discuss.get('topic_summary', ''),
                source_type=discuss.get('source_type', 'unknown'),
                source_id=discuss.get('source_id', ''),
                source_closed=discuss.get('source_closed', False)
            )
            discuss_list.append(discuss_data)
        graph_data[key]['discussion'] = discuss_list

    return graph_data

def decode_topics(mock_path = "tests/mock_data/clustered_discuss.json"):
    cluster_data = load_input_data(mock_path)
    discuss_list = []
    for cluster_id, cluster in cluster_data.items():
        for discuss in cluster:
            discuss_data = DiscussData(
                id=discuss.get('id'),
                title=discuss.get('title'),
                url=discuss.get('url'),
                cleaned_data=discuss.get('clean_data', ''),
                created_at=discuss.get('created_at'),
                topic_summary=discuss.get('topic_summary', ''),
                source_type=discuss.get('source_type', 'unknown'),
                source_id=discuss.get('source_id', ''),
                source_closed=discuss.get('source_closed', False)
            )
            discuss_list.append(discuss_data)
    return discuss_list

def save_clustered_summary(res):
    for key, item in res.items():
        discussion = item.get('discussion', [])
        json_string = [ite.to_dict() for ite in discussion]
        item['discussion'] = json_string
    # 保存聚类结果
    with open('tests/mock_data/clustered_summary.json', 'w') as summary_file:
        json.dump(res, summary_file, ensure_ascii=False, indent=4)

@pytest.mark.skipif(should_skip_unless_run_flag(True), reason="需要修改配置文件config.ini为真实的API_KEY")
def test_first_summary():
    """测试第一次生成摘要"""
    summary = Summary()
    clustered_discuss = decode_topics()
    res = summary.summarize_pipeline(clustered_discuss)

    # save_clustered_summary(res)

    assert res is not None
    assert len(res) == 5
    assert res["0"]["summary"] != "cluster-0"

@pytest.mark.skipif(should_skip_unless_run_flag(True), reason="需要修改配置文件config.ini为真实的API_KEY")
def test_clustered_rerank():
    """测试聚类后重新排序"""
    summary = Summary()
    mock_path = 'tests/mock_data/clustered_summary.json'
    summary._clustered_topics = load_input_data(mock_path)
    summary.reranker_clustered_topics()
    res = summary._clustered_topics
    assert res is not None
    assert len(res) == 5
    assert res["0"]["label"] != ""
