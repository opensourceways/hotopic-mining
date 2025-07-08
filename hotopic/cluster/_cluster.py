import pandas as pd
import json
import networkx as nx
from hotopic.utils import *
from hotopic.summary import Summary

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
                url=discuss.get('url'),
                cleaned_data=discuss.get('clean_data', ''),
                created_at=discuss.get('created_at'),
                topic_summary=discuss.get('topic_summary', ''),
                source_type=discuss.get('source_type', 'unknown'),
                source_id=discuss.get('source_id', ''),
                source_closed=discuss.get('source_closed', False),
                source_deleted=discuss.get('source_deleted', False)
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
    
    def get_embedding_contexts(self, discuss_list):
        """获取所有讨论的内容列表，用于嵌入模型"""
        return [discuss.get_cleaned_content() for discuss in discuss_list]
    
    def get_published_discuss_contexts(self):
        """获取已发布话题的完整数据"""
        return self.get_embedding_contexts(self._published_discuss_list)
    
    def get_discuss_contexts(self):
        """获取所有讨论的内容列表"""
        return self.get_embedding_contexts(self._discuss_list)
    
    def calculate_similarity(self, contexts_a, contexts_b, threshold=0.75):
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
        topic_similarities = self.calculate_similarity(discuss_contexts, topic_summaries, threshold=0.75)
        if not topic_similarities:
            logger.warning("没有找到与已发布话题摘要相似的讨论内容")
            return
        debug_info = {}
        for topic_similarity in topic_similarities:
            i, j, similarity = topic_similarity
            discuss = self._discuss_list.pop(i)
            topic_summary = topic_summaries[j]
            discuss.set_summary(topic_summary)
            self._published_discuss_list.append(discuss)
            if topic_summary not in debug_info:
                debug_info[topic_summary] = []
            debug_info[topic_summary].append((discuss.get_id(), discuss.get_title(), similarity))
        for topic_summary, discuss_info in debug_info.items():
            discuss_info_str = "\n".join([f"id: {discuss_id}-title({title})-consin({similarity})" 
                                            for discuss_id, title, similarity in discuss_info])
            logger.info(f"话题摘要: {topic_summary}，新增讨论讨论内容:\n{discuss_info_str}")
    
    def try_append_discuss_content(self):
        """尝试将讨论内容添加到已发布话题中"""
        discuss_contexts = self.get_discuss_contexts()
        published_discuss_contexts = self.get_published_discuss_contexts()
        if not published_discuss_contexts:
            logger.warning("没有找到已发布的讨论内容")
            return
        published_similarities = self.calculate_similarity(discuss_contexts, published_discuss_contexts)
        if not published_similarities:
            logger.warning("没有找到与已发布讨论内容相似的讨论内容")
            return
        debug_info = {}
        to_delete_indices = set()
        for published_similarity in published_similarities:
            i, j, similarity = published_similarity
            discuss = self._discuss_list[i]
            to_delete_indices.add(i)
            published_discuss = self._published_discuss_list[j]
            # 校验结果的正确性
            # discuss_context = [discuss.get_cleaned_content()]
            # published_discuss_context = [published_discuss.get_cleaned_content()]
            # si = self.calculate_similarity(discuss_context, published_discuss_context, threshold=0.75)
            # logger.info(f"讨论内容与已发布讨论内容相似度: {si}")
            discuss.set_summary(published_discuss.get_summary())
            self._published_discuss_list.append(discuss)
            if published_discuss.get_summary() not in debug_info:
                debug_info[published_discuss.get_summary()] = []
            debug_info[published_discuss.get_summary()].append((discuss.get_id(), discuss.get_title(), 
                                published_discuss.get_id(), published_discuss.get_title(), similarity))
        self._discuss_list = [discuss for i, discuss in enumerate(self._discuss_list) if i not in to_delete_indices]

        for published_summary, discuss_info in debug_info.items():
            discuss_info_str = "\n".join(
                [f"(id: {discuss_id} {title})-(pub_id: {pub_id} {pub_title})-similarity({similarity})"
                    for discuss_id, title, pub_id, pub_title, similarity in discuss_info]
            )
            logger.info(f"publish 话题摘要: {published_summary}，讨论内容:\n{discuss_info_str}")

    
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
                    logger.debug(
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

    def calculate_closed_discuss_sync(self, published_topics):
        """同步已关闭的讨论源至未关闭的讨论源"""
        for topic_id, topic_info in published_topics.items():
            discussion = topic_info.get("discussion", [])
            open_discussion = []
            closed_discussion = []
            for discuss in discussion:
                if discuss.get_source_closed():
                    closed_discussion.append(discuss)
                else:
                    open_discussion.append(discuss)
            if not closed_discussion:
                discussion = [open_discussion]
                topic_info["discussion"] = discussion
                continue
            open_contexts = self.get_embedding_contexts(open_discussion)
            closed_contexts = self.get_embedding_contexts(closed_discussion)
            # 计算未关闭讨论源与已关闭讨论源之间的相似度
            topic_similarities = self.calculate_similarity(open_contexts, closed_contexts, threshold=0.75)
            similarity_map = {}
            open_del_index = []
            closed_del_index = []
            for i, j, similarity in topic_similarities:
                logger.info(f"closed: {j}-{i}-{similarity}")
                if j not in similarity_map:
                    similarity_map[j] = []
                similarity_map[j].append((i, similarity))
                open_del_index.append(i)
                closed_del_index.append(j)

            discussion_list = []
            for closed_index, item_list in similarity_map.items():
                item_list.sort(key=lambda x: x[1], reverse=True)
                closed_discussion_cluster = [closed_discussion[closed_index]]
                closed_discussion_cluster[0].set_closed_similarity(1.0)
                for item in item_list:
                    open_index = item[0]
                    similarity = item[1]
                    if open_index >= len(open_discussion):
                        logger.warning(f"open_index: {open_index} >= len(open_discussion): {len(open_discussion)}")
                        continue
                    open_discussion_to_closed = open_discussion[open_index]
                    open_discussion_to_closed.set_closed_similarity(round(float(similarity), 3))
                    closed_discussion_cluster.append(open_discussion_to_closed)
                discussion_list.append(closed_discussion_cluster)

            # 删除已处理的讨论源
            open_discussion = [open_discussion[i] for i in range(len(open_discussion)) if i not in open_del_index]
            closed_discussion = [closed_discussion[i] for i in range(len(closed_discussion)) if i not in closed_del_index]
            if closed_discussion:
                discussion_list.append(closed_discussion)
            if open_discussion:
                discussion_list.append(open_discussion)

            topic_info["discussion"] = discussion_list
            published_topics[topic_id] = topic_info

        return published_topics
            
        
    def sorted_discuss_by_similarity(self, topics):
        for topic_id, topic_info in topics.items():
            discussion = topic_info.get("discussion", [])
            discuss_contexts = self.get_embedding_contexts(discussion)
            summary_contexts = [topic_info.get("summary", "")]
            # 讨论源与话题之间进行相似度计算
            topic_similarities = self.calculate_similarity(discuss_contexts, summary_contexts, threshold=0.1)
            for i, _, similarity in topic_similarities:
                discussion[i].set_similarity(round(float(similarity), 3))
            
            discussion.sort(key=lambda x: x.get_similarity(), reverse=True)

            topics[topic_id]["discussion"] = discussion

        return topics
    
    def deal_clustered_topics(self, clustered_topics):
        """处理聚类后的话题"""
        for topic_id, topic_info in clustered_topics.items():
            discussion = topic_info.get("discussion", [])
            topic_info["discussion"] = [discussion]
            clustered_topics[topic_id] = topic_info
        return clustered_topics
    
    def encode_topics_out(self, topics):
        """编码话题输出"""
        for topic_id, topic_info in topics.items():
            discussion = topic_info.get("discussion", [])
            new_discussion = []
            for discuss_list in discussion:
                new_discussion.append([discuss.to_dict(debug=False) for discuss in discuss_list])
            topic_info["discussion"] = new_discussion
            topics[topic_id] = topic_info
        return topics

    def merge_published_and_clustered_topics(self, published_topics, clustered_topics):
        """Merge published topics and clustered topics."""
        # TODO: 已发布话题的closed讨论源与该话题的其他讨论源计算相似度，看是否具有借鉴性
        published_topics = self.sorted_discuss_by_similarity(published_topics)
        clustered_topics = self.sorted_discuss_by_similarity(clustered_topics)
        published_topics = self.calculate_closed_discuss_sync(published_topics)
        clustered_topics = self.deal_clustered_topics(clustered_topics)

        clustered_topics = self.encode_topics_out(clustered_topics)
        merged_topics = self.encode_topics_out(published_topics)
        published_topic_num = len(merged_topics)
        for topic_id, topic_info in clustered_topics.items():
            topic_id = str(int(topic_id) + published_topic_num)
            merged_topics[topic_id] = topic_info
        return merged_topics

    def run(self):
        """执行聚类流程"""
        self.try_append_topic()
        published_topics = decode_topics(self._published_discuss_list)
        if not published_topics:
            logger.warning("没有找到已发布的话题")
        clustered_topic = {}
        self.graph_cluster(threshold=0.75)
        summary = Summary()
        clustered_topic = summary.summarize_pipeline(self._clustered_discuss_list)
        result_topic = self.merge_published_and_clustered_topics(published_topics, clustered_topic)
        return result_topic
    
    def run_closed_calculate(self):
        """计算已关闭的讨论源"""
        published_topics = decode_topics(self._published_discuss_list)
        if not published_topics:
            logger.warning("没有找到已发布的话题")

        published_topics = self.calculate_closed_discuss_sync(published_topics)
        res_topics = self.encode_topics_out(published_topics)

        return res_topics

    def get_clustered_discuss(self):
        """获取聚类后的讨论列表"""
        result_map = {}
        for discuss in self._clustered_discuss_list:
            cluster_id = discuss.get_summary()
            if cluster_id not in result_map:
                result_map[cluster_id] = []
            result_map[cluster_id].append(discuss)
        return result_map
  