from hotopic.utils import MyLogger
from hotopic.schedule_timer import start_hotopic_schedule
from hotopic.config import SecureConfigManager

logger = MyLogger()
# logger.configure("WARNING")
logger.configure("INFO")

def load_config():
    config_manager = SecureConfigManager(
        plain_config_path="conf/config.yaml",
        sensitive_config_path="conf/config.ini"
    )

    embedding_name = config_manager.get_plain('llm', 'embedding_name')
    logger.info(f"load config successful, embedding model name: {embedding_name}.")


if __name__ == "__main__":
    load_config()
    logger.info("Hotopic 定时任务调度器启动...")
    start_hotopic_schedule()