"""日志系统"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


class Logger:
    """日志管理器"""

    def __init__(self):
        self._logger: logging.Logger = logging.getLogger("SkBookBot")
        self._logger.setLevel(logging.INFO)
        self._initialized = False

    def setup(self, level: str = "INFO", file_path: str = None,
              max_size: int = 10485760, backup_count: int = 5) -> None:
        """初始化日志系统"""
        if self._initialized:
            return

        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        # 控制台输出
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        self._logger.addHandler(console_handler)

        # 文件输出
        if file_path:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                file_path, maxBytes=max_size, backupCount=backup_count,
                encoding="utf-8"
            )
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)-7s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            self._logger.addHandler(file_handler)

        self._initialized = True

    def get_logger(self, name: str = None) -> logging.Logger:
        """获取子日志器"""
        if name:
            return self._logger.getChild(name)
        return self._logger

    def debug(self, msg: str, *args, **kwargs) -> None:
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        self._logger.critical(msg, *args, **kwargs)


# 全局日志实例
logger = Logger()