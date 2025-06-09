import pandas as pd
import json
import networkx as nx
from hotopic.utils import *

logger = MyLogger()
# logger.configure("WARNING")
logger.configure("INFO")

class Cluster:
    # 已经发布的话题
    _published_discuss_list = None
    # 需要做聚类的讨论源
    _discuss_list = None
    # 聚类后的讨论源
    _clustered_discuss_list = None
    def __init__(self):
        self._published_discuss_list = []
        self._discuss_list = []
        self._clustered_discuss_list = []

    def load_input_data(self, input_data):
        """加载并处理输入数据
        Args:
            input_data: 可迭代的讨论数据集合，元素可以是字典或JSON字符串
        """
        for discuss in input_data:
            if isinstance(discuss, str):
                try:
                    discuss = json.loads(discuss)
                except json.JSONDecodeError:
                    logger.error(f"JSON解析失败: {discuss}")
                    continue
            discuss_data = DiscussData(
                id=discuss.get('id'),
                title=discuss.get('title'),
                body=discuss.get('body'),
                url=discuss.get('url'),
                cleaned_data=discuss.get('cleaned_data', ''),
                created_at=discuss.get('created_at'),
                topic_summary=discuss.get('topic_summary', ''),
                source_type=discuss.get('source_type', 'unknown'),
                source_id=discuss.get('source_id', '')
            )
            if discuss_data.get_id() is None:
                logger.warning(f"讨论数据缺少ID: {discuss}")
                continue
            topic_summary = discuss_data.get_summary()
            if topic_summary is None or topic_summary.strip() == "":
                self._discuss_list.append(discuss_data)
            else:
                self._published_discuss_list.append(discuss_data)

    def get_published_topics_summary(self):
        """获取已发布话题的摘要列表"""
        result_set = set()
        for discuss in self._published_discuss_list:
            summary = discuss.get_summary()
            if summary and summary.strip():
                result_set.add(summary)
        return list(result_set)
    
    def get_published_discuss_contexts(self):
        """获取已发布话题的完整数据"""
        return [discuss.get_cleaned_content() for discuss in self._published_discuss_list]
    
    def get_discuss_contexts(self):
        """获取所有讨论的内容列表"""
        return [discuss.get_cleaned_content() for discuss in self._discuss_list]
    
    def caculate_similarity(self, contexts_a, contexts_b, threshold=0.75):
        """计算讨论内容与已发布话题摘要的相似度"""
        similarity_results = []
        embedding_model = get_embedding_model()
        embeddings_a = embedding_model.embed_documents(contexts_a)
        embeddings_b = embedding_model.embed_documents(contexts_b)
        for i, embedding_a in enumerate(embeddings_a):
            max_similarity = -1
            max_j = -1
            for j, embedding_b in enumerate(embeddings_b):
                similarity = cosine_distance(embedding_a, embedding_b)
                if similarity > threshold and similarity > max_similarity:
                    max_similarity = similarity
                    max_j = j
            if max_j != -1:
                similarity_results.append((i, max_j, max_similarity))
        logger.info(f"总共有 {len(similarity_results)} 个相似度超过阈值 {threshold}")
        return similarity_results
    
    def try_append_published_topic(self):
        """尝试将已发布的话题添加到讨论列表中"""
        discuss_contexts = self.get_discuss_contexts()
        topic_summaries = self.get_published_topics_summary()
        if not topic_summaries:
            logger.warning("没有找到已发布的话题摘要")
            return
        topic_similarities = self.caculate_similarity(discuss_contexts, topic_summaries, threshold=0.7)
        if not topic_similarities:
            logger.warning("没有找到与已发布话题摘要相似的讨论内容")
            return
        for topic_similarity in topic_similarities:
            i, j, similarity = topic_similarity
            discuss = self._discuss_list.pop(i)
            topic_summary = topic_summaries[j]
            discuss.set_summary(topic_summary)
            self._published_discuss_list.append(discuss)
            logger.info(f"将讨论 {discuss.get_id()} 添加到已发布话题中，摘要: {topic_summary}，相似度: {similarity:.2f}")
    
    def try_append_discuss_content(self):
        """尝试将讨论内容添加到已发布话题中"""
        discuss_contexts = self.get_discuss_contexts()
        published_discuss_contexts = self.get_published_discuss_contexts()
        if not published_discuss_contexts:
            logger.warning("没有找到已发布的讨论内容")
            return
        published_similarities = self.caculate_similarity(discuss_contexts, published_discuss_contexts)
        if not published_similarities:
            logger.warning("没有找到与已发布讨论内容相似的讨论内容")
            return
        for published_similarity in published_similarities:
            i, j, similarity = published_similarity
            discuss = self._discuss_list.pop(i)
            published_discuss = self._published_discuss_list[j]
            discuss.set_summary(published_discuss.get_summary())
            self._published_discuss_list.append(discuss)
            logger.info(f"将讨论 {discuss.get_id()} 添加到已发布话题中，摘要: {published_discuss.get_summary()}，相似度: {similarity:.2f}")

    
    def try_append_topic(self):
        self.try_append_published_topic()
        self.try_append_discuss_content()

    def get_connected_graph_nodes(self, threshold=0.75):
        """获取未发布的连接图节点"""
        discuss_contexts = self.get_discuss_contexts()
        embedding_model = get_embedding_model()
        vectors = embedding_model.embed_documents(discuss_contexts)
        graph_nodes = []
        for i, vector in enumerate(vectors):
            for j in range(len(vectors)):
                if i >= j:
                    continue
                tmp_vector = vectors[j]
                cosine = cosine_distance(vector, tmp_vector)
                if cosine > threshold:
                    in_id = self._discuss_list[i].get_id()
                    in_title = self._discuss_list[i].get_title()
                    out_id = self._discuss_list[j].get_id()
                    out_title = self._discuss_list[j].get_title()
                    logger.info(
                        f"id: {in_id}, title: {in_title}, id: {out_id}, title: {out_title}, cosine: {cosine}"
                    )
                    graph_nodes.append({
                        "in_index": i,
                        "out_index": j,
                        "in_id": in_id,
                        "out_id": out_id,
                        "title_in": in_title,
                        "title_out": out_title,
                        "cosine": cosine
                    })
        df = pd.DataFrame(graph_nodes)
        return df if not df.empty else None
    
    def get_connected_graphs(self, nodes, debug_num=5):
        # 创建不连通的图
        G = nx.Graph()
        G.add_edges_from(nodes)
        # 获取所有连通分量
        components = list(nx.connected_components(G))
        # 生成子图列表
        subgraphs = [G.subgraph(c).copy() for c in components]
        # 输出每个子图的节点
        count = 0
        max_len = 0
        topic_graph = []
        # 使用sorted函数生成新排序列表
        for i, sg in enumerate(subgraphs):
            max_len = max(max_len, len(sg.nodes()))
            topic_graph.append(list(sg.nodes()))
            if len(sg.nodes()) > debug_num:
                count += 1
        logger.info(
            f"总共有 {len(subgraphs)} 个子图, 其中大于{debug_num}个节点的子图有 {count} 个, 最大的子图有 {max_len} 个节点"
        )
        sorted_arr = sorted(topic_graph, key=lambda x: len(x), reverse=True)
        return sorted_arr
        
    def graph_cluster(self, threshold=0.75):
        """图聚类"""
        df = self.get_connected_graph_nodes(threshold)
        if df is None:
            logger.warning("没有找到连接图节点")
            return
        graph_edges = []
        graph_nodes = []
        for _, row in df.iterrows():
            graph_node_in = row["in_index"]
            graph_node_out = row["out_index"]
            graph_edges.append((graph_node_in, graph_node_out))
            graph_nodes.append(graph_node_in)
            graph_nodes.append(graph_node_out)
        logger.info(f"graph nodes number: {len(set(graph_nodes))}, graph edges number: {len(graph_edges)}")
        topic_graph = self.get_connected_graphs(list(graph_edges))
        if not topic_graph:
            logger.warning("没有找到连通的图")
            return
        self._clustered_discuss_list = []
        for i, topic in enumerate(topic_graph):
            logger.info(f"topic {i} has {len(topic)} nodes")
            for node_index in topic:
                discuss = self._discuss_list[node_index]
                discuss.set_summary(f"cluster-{i}")
                self._clustered_discuss_list.append(discuss)

    def run(self):
        self.try_append_topic()
        self.graph_cluster(threshold=0.75)

    def get_clustered_discuss(self):
        """获取聚类后的讨论列表"""
        result_map = {}
        for discuss in self._clustered_discuss_list:
            cluster_id = discuss.get_summary()
            if cluster_id not in result_map:
                result_map[cluster_id] = []
            result_map[cluster_id].append(discuss)
        return result_map


    