from hotopic.cluster import Cluster
import pytest
import json

def load_input_data(mock_path):
    with open(mock_path, 'r') as graph_file:
        graph_data = json.load(graph_file)
    return graph_data

def test_first_cluster():
    cluster = Cluster()
    input_data = load_input_data("test/mock_data/data_0606.json")
    cluster.load_input_data(input_data)
    cluster.run()
    res = cluster.get_clustered_discuss()
    assert isinstance(res, dict)
    assert len(res) == 11
