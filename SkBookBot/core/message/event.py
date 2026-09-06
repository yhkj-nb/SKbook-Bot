"""消息事件定义"""

from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from ..bot.instance import BotInstance


@dataclass
class MessageEvent:
    """SkBook 消息事件"""
    message_id: int
    content: str
    sender_id: int
    community_id: str
    channel_id: int
    created_at: str
    bot: "BotInstance" = field(repr=False)

    # 解析后的字段
    is_command: bool = False
    command_name: str = ""
    command_args: str = ""
    is_mention: bool = False
    is_plain_text: bool = True

    def __post_init__(self):
        self._parse()

    def _parse(self) -> None:
        """解析消息内容"""
        content = self.content.strip()

        # 检查是否为文本
        if content.startswith("{"):
            self.is_plain_text = False
            return

        # 检查是否为命令
        prefix = self.bot.command_prefix
        if content.startswith(prefix):
            self.is_command = True
            parts = content[len(prefix):].split(maxsplit=1)
            self.command_name = parts[0].lower() if parts else ""
            self.command_args = parts[1] if len(parts) > 1 else ""

    def reply(self, text: str) -> None:
        """快捷回复频道消息"""
        import asyncio
        asyncio.create_task(
            self.bot.sender.send_channel(
                self.community_id, self.channel_id, text
            )
        )

    def reply_dm(self, text: str) -> None:
        """快捷回复私信"""
        import asyncio
        asyncio.create_task(
            self.bot.sender.send_dm(
                self.community_id, self.sender_id, text
            )
        )


@dataclass
class CardMessage:
    """卡片消息构建器"""
    header: Optional[dict] = None
    title: str = ""
    title_color: str = ""
    rows: list = field(default_factory=list)
    avatars: list = field(default_factory=list)
    icon: bool = True
    button: Optional[dict] = None
    bg: str = ""
    border: str = ""
    width: str = ""
    click_url: str = ""

    def to_json(self) -> str:
        """导出为 JSON 字符串"""
        import json
        card = {"type": "card"}

        if self.header:
            card["header"] = self.header
        if self.title:
            card["title"] = self.title
        if self.title_color:
            card["title_color"] = self.title_color
        if self.rows:
            card["rows"] = self.rows
        if self.avatars:
            card["avatars"] = self.avatars
        card["icon"] = self.icon
        if self.button:
            card["button"] = self.button
        if self.bg:
            card["bg"] = self.bg
        if self.border:
            card["border"] = self.border
        if self.width:
            card["width"] = self.width
        if self.click_url:
            card["click_url"] = self.click_url

        return json.dumps(card, ensure_ascii=False)