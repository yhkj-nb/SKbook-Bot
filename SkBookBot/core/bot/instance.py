"""BotInstance - 单个机器人实例"""

import asyncio
from typing import Optional, Dict, Any, List
from ..base.logger import logger
from ..network.api_client import SkBookAPIClient
from ..message.event import MessageEvent
from ..message.sender import MessageSender
from ..base.context import get_app


class BotInstance:
    """SkBook 机器人实例"""

    def __init__(self, name: str, token: str, config: Dict[str, Any] = None):
        self.name = name
        self._token = token
        self._config = config or {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_message_id: Dict[str, int] = {}  # community_id -> last_message_id
        self._last_all_message_id: int = 0

        # API 客户端
        self.api = SkBookAPIClient(token)
        self.sender = MessageSender(self.api)

        # 监听配置
        self._communities: List[str] = self._config.get("communities", [])
        self._poll_interval: int = self._config.get("poll_interval", 3)
        self._command_prefix: str = self._config.get("command_prefix", "/")

        # 消息处理器
        self._handlers: list = []

    @property
    def token(self) -> str:
        return self._token

    @property
    def running(self) -> bool:
        return self._running

    @property
    def config(self) -> Dict[str, Any]:
        return self._config

    @property
    def command_prefix(self) -> str:
        return self._command_prefix

    def register_handler(self, handler) -> None:
        """注册消息处理器"""
        self._handlers.append(handler)

    async def start(self) -> None:
        """启动机器人"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"机器人 [{self.name}] 已启动")

    async def stop(self) -> None:
        """停止机器人"""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.api.close()
        logger.info(f"机器人 [{self.name}] 已停止")

    async def restart(self) -> None:
        """重启机器人"""
        await self.stop()
        await self.start()

    async def _poll_loop(self) -> None:
        """消息轮询循环"""
        while self._running:
            try:
                if self._communities:
                    # 轮询指定社区
                    for community_id in self._communities:
                        await self._poll_community(community_id)
                else:
                    # 轮询所有社区
                    await self._poll_all()
            except Exception as e:
                logger.error(f"机器人 [{self.name}] 轮询出错: {e}")

            await asyncio.sleep(self._poll_interval)

    async def _poll_community(self, community_id: str) -> None:
        """轮询单个社区的消息"""
        try:
            # 先获取频道列表
            channels = await self.api.get_channels(community_id)
            for channel in channels:
                channel_id = channel["channel_id"]
                last_id = self._last_message_id.get(f"{community_id}_{channel_id}")

                data = await self.api.get_messages(
                    community_id, channel_id,
                    message_id=last_id
                )
                messages = data.get("messages", [])
                if messages:
                    self._last_message_id[f"{community_id}_{channel_id}"] = messages[-1]["message_id"]

                for msg in messages:
                    await self._process_message(msg, community_id, channel_id)
        except Exception as e:
            logger.debug(f"轮询社区 {community_id} 出错: {e}")

    async def _poll_all(self) -> None:
        """轮询所有社区消息"""
        try:
            data = await self.api.get_all_messages(
                message_id=self._last_all_message_id or None
            )
            messages = data.get("messages", [])
            if messages:
                self._last_all_message_id = messages[-1]["message_id"]

            for msg in messages:
                await self._process_message(
                    msg,
                    msg.get("community_id", ""),
                    msg.get("channel_id", 0)
                )
        except Exception as e:
            logger.debug(f"全局轮询出错: {e}")

    async def _process_message(self, msg: Dict, community_id: str,
                                channel_id: int) -> None:
        """处理收到的消息"""
        event = MessageEvent(
            message_id=msg["message_id"],
            content=msg["content"],
            sender_id=msg["sender_id"],
            community_id=community_id,
            channel_id=channel_id,
            created_at=msg["created_at"],
            bot=self,
        )

        # 分发到插件处理器
        app = get_app()
        if app:
            await app.plugin_manager.dispatch(event)

        # 分发到本地处理器
        for handler in self._handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"消息处理器错误: {e}")