"""BotInstance - 单个 SkBook 机器人实例"""

import asyncio
from typing import Optional, Dict, Any, List
from ..base.logger import logger
from ..network.api_client import SkBookAPIClient, SkBookAPIError
from ..message.event import MessageEvent
from ..message.sender import MessageSender
from ..base.context import get_app


class BotInstance:
    """SkBook 机器人实例

    每个实例对应一个机器人 TOKEN，独立轮询消息。
    支持指定社区或全局轮询两种模式。
    """

    # 连续失败退避参数
    MAX_BACKOFF = 60  # 最大退避秒数
    INITIAL_BACKOFF = 1  # 初始退避秒数

    def __init__(self, name: str, token: str, config: Dict[str, Any] = None):
        self.name = name
        self._token = token
        self._config = config or {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._consecutive_failures = 0  # 连续失败计数

        # 消息游标
        self._last_message_id: Dict[str, int] = {}  # "community_id:channel_id" -> last_id
        self._last_all_message_id: int = 0

        # API 客户端
        self.api = SkBookAPIClient(token)
        self.sender = MessageSender(self.api)

        # 监听配置
        self._communities: List[str] = self._config.get("communities", [])
        self._poll_interval: int = max(1, self._config.get("poll_interval", 3))
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
        """注册自定义消息处理器"""
        self._handlers.append(handler)

    async def start(self) -> None:
        """启动机器人消息轮询"""
        if self._running:
            return
        if not self._token:
            logger.warning(f"机器人 [{self.name}] 未配置 TOKEN，跳过启动")
            return

        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"机器人 [{self.name}] 已启动")

    async def stop(self) -> None:
        """停止机器人"""
        if not self._running:
            return
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
        await self.api.close()
        logger.info(f"机器人 [{self.name}] 已停止")

    async def restart(self) -> None:
        """重启机器人"""
        await self.stop()
        await self.start()

    async def _poll_loop(self) -> None:
        """消息轮询主循环

        按固定间隔轮询消息：
        - 配置了 communities → 轮询指定社区
        - communities 为空 → 轮询所有已加入社区（需管理员授权）
        """
        while self._running:
            try:
                if self._communities:
                    for community_id in self._communities:
                        await self._poll_community(community_id)
                else:
                    await self._poll_all()

                # 成功后重置失败计数
                self._consecutive_failures = 0

            except SkBookAPIError as e:
                self._consecutive_failures += 1
                if e.code in (40101, 40301, 40305):
                    # 配置类错误，不重试，继续循环但降低频率
                    logger.warning(
                        f"机器人 [{self.name}] API 错误 [{e.code}]: {e.message}"
                    )
                else:
                    logger.error(
                        f"机器人 [{self.name}] API 错误 [{e.code}]: {e.message}"
                    )
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._consecutive_failures += 1
                logger.error(f"机器人 [{self.name}] 轮询异常: {e}")

            # 动态退避：连续失败越多，等待越长
            if self._consecutive_failures > 0:
                backoff = min(
                    self.INITIAL_BACKOFF * (2 ** (self._consecutive_failures - 1)),
                    self.MAX_BACKOFF,
                )
                await asyncio.sleep(backoff)
            else:
                await asyncio.sleep(self._poll_interval)

        logger.info(f"机器人 [{self.name}] 轮询循环已退出")

    async def _poll_community(self, community_id: str) -> None:
        """轮询指定社区的所有频道消息"""
        try:
            channels = await self.api.get_channels(community_id)
        except SkBookAPIError as e:
            # 40301 等权限错误不需要继续
            logger.warning(
                f"机器人 [{self.name}] 获取社区 {community_id} 频道列表失败: "
                f"[{e.code}] {e.message}"
            )
            return

        for channel in channels:
            channel_id = channel["channel_id"]
            cursor_key = f"{community_id}:{channel_id}"

            try:
                data = await self.api.get_messages(
                    community_id, channel_id,
                    message_id=self._last_message_id.get(cursor_key),
                )
                messages = data.get("messages", [])

                if messages:
                    # 更新游标
                    self._last_message_id[cursor_key] = messages[-1]["message_id"]

                    for msg in messages:
                        await self._process_message(msg, community_id, channel_id)

            except SkBookAPIError as e:
                logger.debug(
                    f"机器人 [{self.name}] 获取频道 {channel_id} 消息失败: "
                    f"[{e.code}] {e.message}"
                )
                continue

    async def _poll_all(self) -> None:
        """轮询所有社区消息（需管理员授权白名单）"""
        try:
            data = await self.api.get_all_messages(
                message_id=self._last_all_message_id or None,
            )
            messages = data.get("messages", [])

            if messages:
                self._last_all_message_id = messages[-1]["message_id"]

                for msg in messages:
                    await self._process_message(
                        msg,
                        msg.get("community_id", ""),
                        msg.get("channel_id", 0),
                    )
        except SkBookAPIError as e:
            if e.code == 40305:
                logger.warning(
                    f"机器人 [{self.name}] 未获得获取消息授权，"
                    f"请管理员在后台添加机器人到白名单"
                )
            elif e.code == 40301:
                logger.info(
                    f"机器人 [{self.name}] 尚未添加到任何社区"
                )
            else:
                raise

    async def _process_message(
        self, msg: Dict, community_id: str, channel_id: int,
    ) -> None:
        """处理单条消息：包装为 MessageEvent 并分发到插件"""
        event = MessageEvent(
            message_id=msg["message_id"],
            content=msg.get("content", ""),
            sender_id=msg.get("sender_id", 0),
            community_id=community_id,
            channel_id=channel_id,
            created_at=msg.get("created_at", ""),
            bot=self,
        )

        # 分发到插件管理器
        app = get_app()
        if app and app.plugin_manager:
            await app.plugin_manager.dispatch(event)

        # 分发到本地注册的处理器
        for handler in self._handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    f"机器人 [{self.name}] 消息处理器错误: {e}"
                )