import threading
import configparser
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

class SecureConfigManager:
    """
    安全配置管理器单例类
    同时处理明文配置（YAML）和敏感配置（INI）
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, 
                plain_config_path: str = 'config.yaml',
                sensitive_config_path: str = 'config.ini') -> 'SecureConfigManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SecureConfigManager, cls).__new__(cls)
                    cls._instance._initialize(plain_config_path, sensitive_config_path)
        return cls._instance

    def _initialize(self, plain_config_path: str, sensitive_config_path: str) -> None:
        """初始化配置管理器，加载两个配置文件"""
        self.plain_config_path = Path(plain_config_path)
        self.sensitive_config_path = Path(sensitive_config_path)
        
        # 加载明文配置 (YAML)
        try:
            with open(self.plain_config_path, 'r') as f:
                self._plain_config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            raise RuntimeError(f"明文配置文件未找到: {self.plain_config_path}")
        except yaml.YAMLError as e:
            raise RuntimeError(f"YAML配置文件解析错误: {e}")
        
        # 加载敏感配置 (INI)
        self._sensitive_config = configparser.ConfigParser()
        try:
            self._sensitive_config.read(self.sensitive_config_path)
        except configparser.Error as e:
            raise RuntimeError(f"INI配置文件解析错误: {e}")
        
        # 验证敏感配置文件是否存在
        if not self._sensitive_config.sections():
            raise RuntimeError(f"未加载到有效配置或文件不存在: {self.sensitive_config_path}")

    def get_plain(self, *keys: str, default: Optional[Any] = None) -> Any:
        """
        获取明文配置项（支持嵌套键）
        示例: get_plain('database', 'host') 对应 YAML 中的 database.host
        """
        current = self._plain_config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def get_sensitive(self, section: str, key: str, default: Optional[Any] = None) -> Any:
        """
        获取敏感配置项
        示例: get_sensitive('api_keys', 'openai') 对应 INI 中的 [api_keys] openai=...
        """
        try:
            return self._sensitive_config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def reload_configs(self) -> None:
        """重新加载配置文件（用于热更新配置）"""
        with self._lock:
            self._initialize(self.plain_config_path, self.sensitive_config_path)

    def list_sensitive_sections(self) -> list:
        """获取所有敏感配置的分区名称"""
        return self._sensitive_config.sections()

    def get_plain_config(self) -> Dict:
        """获取完整的明文配置（只读）"""
        return self._plain_config.copy()

# 使用示例
if __name__ == "__main__":
    # 首次初始化
    config = SecureConfigManager(
        plain_config_path="../config.yaml",
        sensitive_config_path="../config.ini"
    )
    
    # 获取明文配置
    model_name = config.get_plain('llm', 'model_name')
    embedding_name = config.get_plain('llm', 'embedding_name')
    
    # 获取敏感配置
    openai_key = config.get_sensitive('llm', 'api-key')
    
    # 列出所有敏感配置分区
    sensitive_sections = config.list_sensitive_sections()
    
    print(f"model name: {model_name}")
    print(f"embedding name: {embedding_name}")
    print(f"openai_key: {openai_key}")
    print(f"OpenAI Key: {'*' * len(openai_key) if openai_key else 'Not Found'}")
    print(f"Sensitive Sections: {sensitive_sections}")
    
    # 重新加载配置（热更新）
    config.reload_configs()
