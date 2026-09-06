"""插件上下文 - 提供给插件的 API"""

from typing import Optional, TYPE_CHECKING
from ..base.logger import logger
from ..base.context import get_app

if TYPE_CHECKING:
    from ..application import Application
    from ..bot.instance import BotInstance


class PluginContext:
    """插件上下文，插件可以通过 self.ctx 访问"""

    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        self._logger = logger.get_logger(f"plugin.{plugin_name}")

    @property
    def app(self) -> Optional["Application"]:
        """获取应用实例"""
        return get_app()

    @property
    def log(self):
        """获取日志器"""
        return self._logger

    def get_bot(self, name: str = None) -> Optional["BotInstance"]:
        """获取机器人实例"""
        app = self.app
        if not app:
            return None
        if name:
            return app.bot_registry.get(name)
        bots = app.bot_registry.list_active()
        return bots[0] if bots else None

    def get_all_bots(self) -> list:
        """获取所有机器人"""
        app = self.app
        if not app:
            return []
        return app.bot_registry.list()

    async def send_message(self, community_id: str, channel_id: int,
                           content: str, bot_name: str = None) -> bool:
        """发送频道消息"""
        bot = self.get_bot(bot_name)
        if not bot:
            self.log.error("未找到可用机器人")
            return False
        return await bot.sender.send_channel(community_id, channel_id, content)

    async def send_dm(self, community_id: str, user_id: int,
                      content: str, bot_name: str = None) -> bool:
        """发送私信"""
        bot = self.get_bot(bot_name)
        if not bot:
            self.log.error("未找到可用机器人")
            return False
        return await bot.sender.send_dm(community_id, user_id, content)