# hotopic-mining
社区热点话题的数据相似度聚类，LLM 总结与排序

## 本地验证

### 测试用例本地执行

* 执行命令: `python -m pytest`
* 指定某个文件的测试用例执行: `python -m pytest -vs test/test_cluster.py`
* 指定某个特定的用例测试用例执行: `python -m pytest -vs tests/test_summary.py::test_first_summary`
* 通过执行参数运行skip的用例：`python -m pytest -vs tests/test_cluster.py --run-specific-skips`

### 本地执行 main 函数

* 执行命令: `python -m hotopic.main`

## 话题总结

### 话题总结策略

1. 聚类后的话题中的讨论源，先按创建时间排序，再用LLM生成摘要
