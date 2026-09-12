"""BotInstance - 单个 SkBook 机器人实例

每个实例对应一个 SkBook 机器人 TOKEN，独立轮询消息。
启动流程：
  1. 配置 TOKEN → 2. 验证社区权限(get_channels) → 3. 发现频道 → 4. 轮询消息
"""

import asyncio
from typing import Optional, Dict, Any, List, Set
from ..base.logger import logger
from ..network.api_client import SkBookAPIClient, SkBookAPIError
from ..message.event import MessageEvent
from ..message.sender import MessageSender
from ..base.context import get_app


class BotInstance:
    """SkBook 机器人实例

    每个实例对应一个机器人 TOKEN，独立轮询消息。
    支持指定社区和全局轮询两种模式。
    """

    # 退避参数
    INITIAL_BACKOFF = 1.0       # 初始退避（秒）
    MAX_BACKOFF = 60.0          # 最大退避（秒）
    BACKOFF_FACTOR = 2.0        # 退避倍数

    def __init__(self, name: str, token: str, config: Dict[str, Any] = None):
        self.name = name
        self._token = token
        self._config = config or {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._consecutive_failures = 0

        # 消息游标: "community_id:channel_id" -> last_message_id
        self._last_message_id: Dict[str, int] = {}
        # 全局游标（get_all_messages 模式）
        self._last_all_message_id: int = 0
        # 已处理消息 ID 防重（滑动窗口，最多 500 条）
        self._seen_message_ids: Set[int] = set()
        self._seen_window_size = 500

        # API 客户端
        self.api = SkBookAPIClient(token)
        self.sender = MessageSender(self.api)

        # 从配置读取参数
        self._communities: List[str] = self._config.get("communities", []) or []
        self._poll_interval: int = max(1, self._config.get("poll_interval", 3))
        self._command_prefix: str = self._config.get("command_prefix", "/")

        # 消息处理器（插件管理器注册的）
        self._handlers: list = []

    # ---- 属性 ----

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

    # ---- 处理器管理 ----

    def register_handler(self, handler) -> None:
        """注册自定义消息处理器"""
        self._handlers.append(handler)

    def _is_duplicate(self, message_id: int) -> bool:
        """检查消息是否已经处理过"""
        if message_id in self._seen_message_ids:
            return True
        self._seen_message_ids.add(message_id)
        # 控制滑动窗口大小
        if len(self._seen_message_ids) > self._seen_window_size:
            # 移除最早的一半
            old = list(self._seen_message_ids)[:self._seen_window_size // 2]
            for oid in old:
                self._seen_message_ids.discard(oid)
        return False

    # ---- 生命周期 ----

    async def start(self) -> None:
        """启动机器人消息轮询"""
        if self._running:
            return
        if not self._token:
            logger.warning("机器人 [%s] 未配置 TOKEN，跳过启动", self.name)
            return

        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("机器人 [%s] 已启动 (轮询间隔 %ds, 社区: %s)",
                     self.name, self._poll_interval,
                     ",".join(self._communities) if self._communities else "全局")

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
        logger.info("机器人 [%s] 已停止", self.name)

    async def restart(self) -> None:
        """重启机器人"""
        await self.stop()
        await self.start()

    # ---- 消息轮询主循环 ----

    async def _poll_loop(self) -> None:
        """消息轮询主循环

        策略：
        - 配置了 communities → 轮询指定社区的每个频道
        - communities 为空 → 使用 get_all_messages（需管理员授权白名单）
        """
        logger.info("机器人 [%s] 消息轮询已开始", self.name)

        while self._running:
            try:
                if self._communities:
                    for cid in self._communities:
                        if not self._running:
                            break
                        await self._poll_community(cid)
                else:
                    await self._poll_all()

                # 成功重置失败计数
                self._consecutive_failures = 0

            except SkBookAPIError as e:
                self._consecutive_failures += 1
                if e.is_auth_error:
                    logger.warning("机器人 [%s] 认证错误: %s", self.name, e.text)
                elif e.is_perm_error:
                    logger.warning("机器人 [%s] 权限错误: %s", self.name, e.text)
                else:
                    logger.error("机器人 [%s] API 错误: %s", self.name, e.text)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._consecutive_failures += 1
                logger.error("机器人 [%s] 轮询异常: %s", self.name, e)

            # 退避等待
            if self._consecutive_failures > 0:
                backoff = min(
                    self.INITIAL_BACKOFF * (self.BACKOFF_FACTOR ** (self._consecutive_failures - 1)),
                    self.MAX_BACKOFF,
                )
                await asyncio.sleep(backoff)
            else:
                await asyncio.sleep(self._poll_interval)

        logger.info("机器人 [%s] 轮询循环已退出", self.name)

    async def _poll_community(self, community_id: str) -> None:
        """轮询指定社区的所有频道消息"""
        try:
            channels = await self.api.get_channels(community_id)
        except SkBookAPIError as e:
            logger.warning(
                "机器人 [%s] 获取社区 %s 频道列表失败: %s",
                self.name, community_id, e.text,
            )
            return

        for channel in channels:
            if not self._running:
                break
            channel_id = channel["channel_id"]
            cursor_key = f"{community_id}:{channel_id}"
            last_id = self._last_message_id.get(cursor_key)

            try:
                data = await self.api.get_messages(
                    community_id, channel_id,
                    limit=20,
                    message_id=last_id,
                )
                messages = data.get("messages", [])

                if messages:
                    # 更新游标到最新消息
                    self._last_message_id[cursor_key] = messages[-1]["message_id"]

                    # 如果 has_more，继续拉取（处理积压）
                    while data.get("has_more") and self._running:
                        data = await self.api.get_messages(
                            community_id, channel_id,
                            limit=20,
                            message_id=self._last_message_id.get(cursor_key),
                        )
                        more_msgs = data.get("messages", [])
                        if more_msgs:
                            self._last_message_id[cursor_key] = more_msgs[-1]["message_id"]
                            messages.extend(more_msgs)
                        else:
                            break

                    for msg in messages:
                        if not self._running:
                            break
                        await self._process_message(msg, community_id, channel_id)

            except SkBookAPIError as e:
                logger.debug(
                    "机器人 [%s] 获取频道 %s 消息失败: %s",
                    self.name, channel_id, e.text,
                )

    async def _poll_all(self) -> None:
        """轮询所有社区消息（需管理员授权白名单）"""
        try:
            data = await self.api.get_all_messages(
                limit=20,
                message_id=self._last_all_message_id or None,
            )
            messages = data.get("messages", [])

            if messages:
                self._last_all_message_id = messages[-1]["message_id"]

                # 处理积压
                while data.get("has_more") and self._running:
                    data = await self.api.get_all_messages(
                        limit=20,
                        message_id=self._last_all_message_id or None,
                    )
                    more = data.get("messages", [])
                    if more:
                        self._last_all_message_id = more[-1]["message_id"]
                        messages.extend(more)
                    else:
                        break

                for msg in messages:
                    if not self._running:
                        break
                    await self._process_message(
                        msg,
                        msg.get("community_id", ""),
                        msg.get("channel_id", 0),
                    )
        except SkBookAPIError as e:
            if e.code == 40305:
                logger.warning(
                    "机器人 [%s] 未获得获取消息授权 | 请管理员在后台"
                    "「机器人获取消息白名单」中添加该机器人ID，"
                    "或为机器人开启「接收服务器所有消息」",
                    self.name,
                )
            elif e.code == 40301:
                # 没加入任何社区，静默跳过
                pass
            else:
                raise

    async def _process_message(
        self, msg: Dict, community_id: str, channel_id: int,
    ) -> None:
        """处理单条消息：去重 → 包装为 MessageEvent → 分发到插件"""
        message_id = msg["message_id"]

        # 去重
        if self._is_duplicate(message_id):
            return

        # 构造事件
        event = MessageEvent(
            message_id=message_id,
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

        # 分发到本地处理器
        for handler in self._handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    "机器人 [%s] 消息处理器错误: %s", self.name, e,
                )