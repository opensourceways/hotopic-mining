import schedule # type: ignore
import time
import json
import threading
from datetime import datetime
from hotopic.utils import MyLogger
from hotopic.cluster import Cluster
from hotopic.config import SecureConfigManager
from hotopic.input_data import get_input_data

logger = MyLogger()
logger.configure("INFO")

def hotopic_mining_pipeline(need_summary: bool = True):
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
    input_data = get_input_data()
    if not input_data:
        logger.warning("没有获取到任何数据，无法进行话题挖掘。")
        return
    cluster.load_input_data(input_data)
    cluster_result = cluster.run(need_summarize=need_summary)
    # 7. 话题发布，将生成的话题发布到社区

    return cluster_result

def hotopic_run_job():
    """周五凌晨执行的任务"""
    # 单线程执行，可以不用加锁
    current_thread = threading.current_thread()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[{now}] - [{current_thread.ident}] 周五任务执行中...")
    # 这里添加你的实际任务代码
    # 比如数据备份、报告生成等操作
    res = hotopic_mining_pipeline()



def start_hotopic_schedule():
    """启动定时任务调度器"""
    config_manager = SecureConfigManager(
        plain_config_path="conf/config.yaml",
        sensitive_config_path="conf/config.ini"
    )
    schedule_time = config_manager.get_plain('timer', 'schedule_time')
    # 设置每周五凌晨00:00执行任务
    # schedule.every().friday.at(str(schedule_time)).do(hotopic_run_job)
    # 测试时使用，每2分钟执行一次
    schedule.every(30).minutes.do(hotopic_run_job)

    logger.info("定时任务已启动，每周五凌晨00:00执行...")
    logger.info("按 Ctrl+C 退出程序")

    try:
        # 持续运行调度器
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次，减少CPU占用
    except KeyboardInterrupt:
        logger.warning("\n定时任务已停止")