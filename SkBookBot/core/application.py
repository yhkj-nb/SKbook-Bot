"""Application - 顶层编排类，组合所有子系统"""

import asyncio
import signal
from typing import Optional
from pathlib import Path

from .base.config import config
from .base.logger import logger
from .base.context import AppContext
from .bot.registry import BotRegistry
from .bot.manager import BotManager
from .plugin.manager import PluginManager
from .server.http_server import HttpServer
from .services.config_watcher import ConfigWatcher


class Application:
    """SkBookBot 应用主类"""

    def __init__(self):
        self._running = False
        self._closed = False

        # 注册到全局上下文
        AppContext().app = self

        # 子系统
        self.bot_registry = BotRegistry()
        self.bot_manager = BotManager(self.bot_registry)
        self.plugin_manager = PluginManager()
        self.http_server = HttpServer()
        self.config_watcher = ConfigWatcher()

        # 事件循环
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._tasks: list = []

    @property
    def running(self) -> bool:
        return self._running

    async def initialize(self) -> None:
        """初始化所有子系统"""
        logger.info("正在初始化 SkBookBot...")

        # 初始化存储
        from .storage.database import db
        db_path = config.get("database.path", "./data/skbookbot.db")
        await db.initialize(db_path)

        # 初始化 HTTP 服务器
        await self.http_server.initialize()

        # 加载插件
        await self.plugin_manager.load_plugins()

        # 启动机器人
        await self.bot_manager.start_all()

        logger.info("SkBookBot 初始化完成")

    async def start(self) -> None:
        """启动应用"""
        if self._running:
            return
        self._running = True
        self._loop = asyncio.get_event_loop()

        # 注册信号处理
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                self._loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self.shutdown(s)))
            except NotImplementedError:
                pass

        # 启动 HTTP 服务器
        await self.http_server.start()

        # 启动配置监视
        if config.get("services.config_watcher", True):
            asyncio.create_task(self.config_watcher.start())

        logger.info("SkBookBot 启动完成")

        # 保持运行
        try:
            while self._running and not self._closed:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    async def shutdown(self, sig=None) -> None:
        """优雅关闭"""
        if self._closed:
            return
        self._closed = True
        self._running = False

        sig_name = sig.name if sig else "manual"
        logger.info(f"收到信号 {sig_name}，正在关闭...")

        # 停止配置监视
        await self.config_watcher.stop()

        # 停止所有机器人
        await self.bot_manager.stop_all()

        # 停止 HTTP 服务器
        await self.http_server.stop()

        # 关闭数据库
        from .storage.database import db
        await db.close()

        logger.info("SkBookBot 已关闭")

    def reload(self) -> None:
        """热重载配置"""
        logger.info("正在热重载配置...")
        # 重新加载机器人配置
        asyncio.create_task(self._reload_bots())

    async def _reload_bots(self) -> None:
        """重新加载机器人配置"""
        await self.bot_manager.reload_all()