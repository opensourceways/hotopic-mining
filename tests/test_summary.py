from hotopic.summary import Summary
from hotopic.utils import *
import pytest
import json

def load_input_data(mock_path):
    with open(mock_path, 'r') as graph_file:
        graph_data = json.load(graph_file)
    return graph_data

def decode_topics(mock_path = "tests/mock_data/clustered_discuss.json"):
    cluster_data = load_input_data(mock_path)
    discuss_list = []
    for cluster_id, cluster in cluster_data.items():
        for discuss in cluster:
            discuss_data = DiscussData(
                id=discuss.get('id'),
                title=discuss.get('title'),
                body=discuss.get('body'),
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

def test_first_summary():
    """测试第一次生成摘要"""
    summary = Summary()
    published_discuss = []
    clustered_discuss = decode_topics()
    res = summary.summarize_pipeline(published_discuss, clustered_discuss)

    # 保存聚类结果
    # with open('tests/mock_data/clustered_summary.json', 'w') as summary_file:
    #     json.dump(res, summary_file, ensure_ascii=False, indent=4)

    assert res is not None
    assert len(res) == 5
    assert res["0"]["summary"] != "cluster-0"

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
