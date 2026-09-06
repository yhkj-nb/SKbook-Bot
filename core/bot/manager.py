"""BotManager - 机器人管理器，薄封装层"""

from typing import Optional
from ..base.config import config
from ..base.logger import logger
from .registry import BotRegistry
from .instance import BotInstance


class BotManager:
    """机器人管理器"""

    def __init__(self, registry: BotRegistry):
        self._registry = registry

    @property
    def registry(self) -> BotRegistry:
        return self._registry

    def create_bot(self, name: str, token: str,
                   bot_config: dict = None) -> BotInstance:
        """创建并注册机器人"""
        instance = BotInstance(name, token, bot_config)
        self._registry.register(instance)
        return instance

    def remove_bot(self, name: str) -> Optional[BotInstance]:
        """移除机器人"""
        instance = self._registry.get(name)
        if instance:
            import asyncio
            asyncio.create_task(instance.stop())
        return self._registry.unregister(name)

    async def start_all(self) -> None:
        """从配置加载并启动所有机器人"""
        bots_config = config.get_bots()
        for bot_cfg in bots_config:
            if not bot_cfg.get("enabled", True):
                continue
            name = bot_cfg.get("name", "unnamed")
            token = bot_cfg.get("token", "")
            if not token:
                logger.warning(f"机器人 [{name}] 未配置 Token，跳过")
                continue

            instance = BotInstance(name, token, bot_cfg)
            self._registry.register(instance)
            await instance.start()

    async def stop_all(self) -> None:
        """停止所有机器人"""
        await self._registry.stop_all()

    async def reload_all(self) -> None:
        """重载所有机器人"""
        # 停止现有机器人
        await self._registry.stop_all()
        self._registry._bots.clear()

        # 重新加载配置
        bots_config = config.get_bots()
        for bot_cfg in bots_config:
            if not bot_cfg.get("enabled", True):
                continue
            name = bot_cfg.get("name", "unnamed")
            token = bot_cfg.get("token", "")
            if not token:
                continue

            instance = BotInstance(name, token, bot_cfg)
            self._registry.register(instance)
            await instance.start()

        logger.info("所有机器人已重载")