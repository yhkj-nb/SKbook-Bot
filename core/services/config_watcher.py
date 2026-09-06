"""ConfigWatcher - 配置文件变更监视与自动重载"""

import asyncio
from pathlib import Path
from ..base.logger import logger
from ..base.config import config


class ConfigWatcher:
    """配置文件监视器"""

    def __init__(self):
        self._running = False
        self._task: asyncio.Task = None
        self._last_mod_time: float = 0

    async def start(self) -> None:
        """启动监视"""
        self._running = True
        self._task = asyncio.create_task(self._watch_loop())
        logger.info("配置监视器已启动")

    async def stop(self) -> None:
        """停止监视"""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _watch_loop(self) -> None:
        """监视循环"""
        # 每次轮询间隔
        while self._running:
            await asyncio.sleep(5)

            # 检查配置文件变更（简化实现）
            if config.config_dir:
                bot_yaml = config.config_dir / "bot.yaml"
                settings_yaml = config.config_dir / "settings.yaml"

                for path in [bot_yaml, settings_yaml]:
                    if path.exists():
                        mtime = path.stat().st_mtime
                        if mtime > self._last_mod_time + 1:
                            self._last_mod_time = mtime
                            logger.info(f"检测到配置文件变更: {path.name}")
                            await self._on_config_changed(path)

    async def _on_config_changed(self, path: Path) -> None:
        """配置文件变更回调"""
        from ..base.context import get_app
        app = get_app()
        if app:
            app.reload()