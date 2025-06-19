import schedule # type: ignore
import time
import json
import os
import threading
from datetime import datetime, timedelta
from hotopic.utils import MyLogger
from hotopic.cluster import Cluster
from hotopic.config import SecureConfigManager
from hotopic.input_data import get_input_data
from hotopic.output_data import post_output_data

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
    if need_summary:
        cluster_result = cluster.run()
    else:
        cluster_result = cluster.run_closed_calculate()
    # 7. 话题发布，将生成的话题发布到社区

    return cluster_result

def delete_old_data(path_dir="tests/mock_data/"):
    # 计算30天前的时间戳（以秒为单位）
    time_threshold = (datetime.datetime.now() - datetime.timedelta(days=30)).timestamp()
    # 遍历目录中的所有文件
    for root, dirs, files in os.walk(path_dir):
        for file in files:
            file_path = os.path.join(root, file)
            # 获取文件的最后修改时间
            file_mtime = os.path.getmtime(file_path)
            # 如果文件修改时间早于阈值，则删除
            if file_mtime < time_threshold:
                try:
                    os.remove(file_path)
                    logger.info(f"已删除: {file_path}")
                except Exception as e:
                    logger.error(f"删除失败 [{file_path}]: {str(e)}")

def hotopic_run_job():
    """周五凌晨执行的任务"""
    # 单线程执行，可以不用加锁
    thread_id = threading.get_ident()
    native_tid = threading.get_native_id()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[{now}] - [{native_tid}-{thread_id}] 周五任务执行中...")
    # 这里添加你的实际任务代码
    # 比如数据备份、报告生成等操作
    res = hotopic_mining_pipeline()

    day_str = datetime.now().strftime("%Y_%m_%d")
    with open(f'tests/mock_data/clustered_run_{day_str}.json', 'w') as discuss_file:
        json.dump(res, discuss_file, ensure_ascii=False, indent=4)

    post_output_data(res)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[{now}] - [{native_tid}-{thread_id}] 周五任务完成。")
    delete_old_data()

def hotopic_closed_calculate_job():
    """关闭的话题，相关性计算"""
    # 单线程执行，可以不用加锁
    thread_id = threading.get_ident()
    native_tid = threading.get_native_id()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[{now}] - [{native_tid}-{thread_id}] 关闭话题相关性计算任务执行中...")
    # 这里添加你的实际任务代码
    # 比如数据备份、报告生成等操作
    res = hotopic_mining_pipeline(need_summary=False)
    if not res:
        logger.warning("没有获取到任何数据，无法进行话题相关性计算。")
        return
    day_str = datetime.now().strftime("%Y_%m_%d")
    with open(f'tests/mock_data/clustered_closed_{day_str}.json', 'w') as discuss_file:
        json.dump(res, discuss_file, ensure_ascii=False, indent=4)
    logger.info(f"[{now}] - [{native_tid}-{thread_id}] 关闭话题相关性计算完成。")


# 在独立线程中运行任务的函数
def run_threaded(job_func, *args, **kwargs):
    job_thread = threading.Thread(target=job_func, args=args, kwargs=kwargs)
    job_thread.daemon = True  # 设置为守护线程
    job_thread.start()

# 设置定时任务
def setup_schedule():
    config_manager = SecureConfigManager(
        plain_config_path="conf/config.yaml",
        sensitive_config_path="conf/config.ini"
    )
    schedule_time = config_manager.get_plain('timer', 'schedule_time')
    time_str = str(schedule_time)
    logger.info(f"定时任务 hotopic_run_job 时间：{time_str}")
    # 设置每周五凌晨00:00执行任务
    schedule.every().friday.at(time_str).do(hotopic_run_job)
    # schedule.every().wednesday.at(str(schedule_time)).do(hotopic_run_job)
    # 设置每天凌晨00:00执行任务
    # schedule.every().days.at(str(schedule_time)).do(run_threaded, hotopic_run_job)
    # schedule.every().hours.at(":07").do(run_threaded, hotopic_run_job)
    # 每4个小时执行一次 closed similarity 计算
    # schedule.every(4).hours.do(run_threaded, hotopic_closed_calculate_job)
    day_str = datetime.now().strftime("%Y-%m-%d ")
    dt = datetime.strptime(day_str + time_str, "%Y-%m-%d %H:%M")
    result = dt + timedelta(hours=8) # 加 8 小时
    closed_time_str = result.strftime("%H:%M")
    schedule.every().hours.at(closed_time_str).do(run_threaded, hotopic_closed_calculate_job)

def start_hotopic_schedule():
    """启动定时任务调度器"""
    setup_schedule()

    logger.info("定时任务已启动，每周五凌晨00:00执行...")
    logger.info("按 Ctrl+C 退出程序")

    try:
        # 持续运行调度器
        while True:
            schedule.run_pending()
            time.sleep(5)  # 每分钟检查一次，减少CPU占用
    except KeyboardInterrupt:
        logger.warning("\n定时任务已停止")