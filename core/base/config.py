"""配置管理 - 加载 YAML 配置与环境变量"""

import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path


class Config:
    """层级配置管理器，支持 YAML 文件 + 环境变量覆盖"""

    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._config_dir: Optional[Path] = None

    def load_yaml(self, path: str) -> Dict[str, Any]:
        """加载 YAML 配置文件"""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        self._config_dir = path.parent
        return data

    def load_bot_config(self, path: str) -> Dict[str, Any]:
        """加载机器人配置"""
        data = self.load_yaml(path)
        self._data["bots"] = data.get("bots", [])
        return self._data["bots"]

    def load_settings(self, path: str) -> Dict[str, Any]:
        """加载框架设置"""
        data = self.load_yaml(path)
        self._data.update(data)
        return data

    def load_env(self, path: Optional[str] = None) -> None:
        """加载 .env 文件（可选）"""
        from dotenv import load_dotenv
        load_dotenv(path)

    def get(self, key: str, default: Any = None) -> Any:
        """通过点号分隔的 key 获取配置值，如 'server.port'"""
        keys = key.split(".")
        value = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split(".")
        target = self._data
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value

    @property
    def data(self) -> Dict[str, Any]:
        return self._data

    @property
    def config_dir(self) -> Optional[Path]:
        return self._config_dir

    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取环境变量"""
        return os.environ.get(key, default)

    def get_bots(self) -> list:
        """获取所有机器人配置"""
        return self._data.get("bots", [])

    def __repr__(self) -> str:
        return f"Config({len(self._data)} keys)"


# 全局配置实例
config = Config()