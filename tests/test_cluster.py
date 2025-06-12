from hotopic.cluster import Cluster
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
    return graph_data

def save_clustered_discuss(res):
    for key, item in res.items():
        json_string = [ite.to_dict() for ite in item]
        res[key] = json_string
    # 测试时输出聚类的结果
    with open('tests/mock_data/clustered_discuss.json', 'w') as discuss_file:
        json.dump(res, discuss_file, ensure_ascii=False, indent=4)

def save_clustered_result(res):
    # 测试时输出聚类的结果
    with open('tests/mock_data/clustered_result.json', 'w') as discuss_file:
        json.dump(res, discuss_file, ensure_ascii=False, indent=4)

def save_clustered_second_result(res):
    # 测试时输出聚类的结果
    with open('tests/mock_data/clustered_second_result.json', 'w') as discuss_file:
        json.dump(res, discuss_file, ensure_ascii=False, indent=4)

def delete_cleaned_data(cluster_result):
    for topic_id, topic_data in cluster_result.items():
        disscussion = topic_data.get('discussion', [])
        for item_list in disscussion:
            for discuss in item_list:
                del discuss["clean_data"]
        cluster_result[topic_id]['discussion'] = disscussion
    # 测试时输出聚类的结果
    return cluster_result

@pytest.mark.skipif(should_skip_unless_run_flag(True), reason="需要修改配置文件config.ini为真实的API_KEY")
def test_first_cluster():
    cluster = Cluster()
    input_data = load_input_data("tests/mock_data/first_data.json")
    cluster.load_input_data(input_data)
    res = cluster.run()
    save_clustered_result(res)
    res = cluster.get_clustered_discuss()
    # print(res)
    # save_clustered_discuss(res)
    assert isinstance(res, dict)
    assert len(res) > 1

@pytest.mark.skipif(should_skip_unless_run_flag(True), reason="需要修改配置文件config.ini为真实的API_KEY")
def test_second_cluster():
    cluster = Cluster()
    input_data = load_input_data("tests/mock_data/second_data.json")
    cluster.load_input_data(input_data)
    res = cluster.run()
    save_clustered_second_result(res)
    res = delete_cleaned_data(res)
    # print(res)
    res = cluster.get_clustered_discuss()
    # print(res)
    # save_clustered_discuss(res)
    assert isinstance(res, dict)
    assert len(res) > 1
