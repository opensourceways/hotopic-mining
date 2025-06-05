from hotopic.utils import MyLogger
from hotopic.schedule_timer import start_hotopic_schedule

logger = MyLogger()
# logger.configure("WARNING")
logger.configure("INFO")

if __name__ == "__main__":
    logger.info("Hotopic 定时任务调度器启动...")
    start_hotopic_schedule()