import schedule # type: ignore
import time
import threading
from datetime import datetime
from hotopic.utils import MyLogger
from hotopic.cluster import Cluster

logger = MyLogger()
logger.configure("INFO")

def hotopic_mining_pipeline():
    """
    热帖挖掘主流程
    """
    # 1. 数据获取，包括存量数据、增量数据与已发布的话题数据
    # 2. 数据整理，历史数据合并
    # 3. 文本向量化，将文本转换为向量表示
    # 4. 相似度计算，计算向量之间的相似度
    # 5. 图算法生成，根据相似度构建图结构
    # 6. 话题生成，根据图的联通性生成话题描述
    cluster = Cluster()
    input_data = []
    cluster.load_input_data(input_data)
    cluster_result = cluster.run()
    # 7. 话题发布，将生成的话题发布到社区

def hotopic_run_job():
    """周五凌晨执行的任务"""
    # 单线程执行，可以不用加锁
    current_thread = threading.current_thread()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[{now}] - [{current_thread.ident}] 周五任务执行中...")
    # 这里添加你的实际任务代码
    # 比如数据备份、报告生成等操作

def start_hotopic_schedule():
    """启动定时任务调度器"""
    # 设置每周五凌晨00:00执行任务
    # schedule.every().friday.at("00:00").do(hotopic_run_job)
    # 测试时使用，每2分钟执行一次
    schedule.every(2).minutes.do(hotopic_run_job)

    logger.info("定时任务已启动，每周五凌晨00:00执行...")
    logger.info("按 Ctrl+C 退出程序")

    try:
        # 持续运行调度器
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次，减少CPU占用
    except KeyboardInterrupt:
        logger.warning("\n定时任务已停止")