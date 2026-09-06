"""BotRegistry - 多机器人注册表"""

from typing import Dict, Optional, List
from ..base.logger import logger
from .instance import BotInstance


class BotRegistry:
    """机器人注册表，管理所有 BotInstance"""

    def __init__(self):
        self._bots: Dict[str, BotInstance] = {}  # name -> BotInstance

    @property
    def bots(self) -> Dict[str, BotInstance]:
        return self._bots

    def register(self, instance: BotInstance) -> None:
        """注册机器人实例"""
        self._bots[instance.name] = instance
        logger.info(f"机器人 [{instance.name}] 已注册")

    def unregister(self, name: str) -> Optional[BotInstance]:
        """注销机器人实例"""
        instance = self._bots.pop(name, None)
        if instance:
            logger.info(f"机器人 [{name}] 已注销")
        return instance

    def get(self, name: str) -> Optional[BotInstance]:
        """获取机器人实例"""
        return self._bots.get(name)

    def get_by_token(self, token: str) -> Optional[BotInstance]:
        """通过 Token 查找机器人"""
        for bot in self._bots.values():
            if bot.token == token:
                return bot
        return None

    def list(self) -> List[BotInstance]:
        """列出所有机器人"""
        return list(self._bots.values())

    def list_active(self) -> List[BotInstance]:
        """列出运行中的机器人"""
        return [b for b in self._bots.values() if b.running]

    async def start_all(self) -> None:
        """启动所有机器人"""
        for bot in self._bots.values():
            await bot.start()

    async def stop_all(self) -> None:
        """停止所有机器人"""
        for bot in self._bots.values():
            await bot.stop()

    async def reload_all(self) -> None:
        """重载所有机器人"""
        for bot in self._bots.values():
            await bot.restart()