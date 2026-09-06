"""系统插件 - 提供基础命令"""

import json
from core.plugin.context import PluginContext
from core.plugin.decorators import on_command, on_message
from core.message.event import CardMessage


class SystemPlugin:
    """系统插件 - 基础命令"""

    _skbook_handlers = [
        {"type": "command", "name": "ping", "aliases": []},
        {"type": "command", "name": "help", "aliases": ["菜单", "帮助"]},
        {"type": "command", "name": "status", "aliases": ["状态"]},
        {"type": "command", "name": "about", "aliases": ["关于"]},
    ]

    def __init__(self):
        self.ctx: PluginContext = None

    async def on_load(self):
        self.ctx.log.info("系统插件已加载")

    async def on_unload(self):
        self.ctx.log.info("系统插件已卸载")

    async def ping(self, event):
        """ping 命令 - 回复 pong"""
        await event.reply("pong! 🏓")

    async def help(self, event):
        """help 命令 - 显示帮助"""
        help_text = "**SkBookBot 可用命令**\n\n"
        help_text += "/ping - 测试机器人是否在线\n"
        help_text += "/help - 显示此帮助\n"
        help_text += "/status - 查看机器人状态\n"
        help_text += "/about - 关于 SkBookBot\n\n"
        help_text += "插件开发者可以在插件中注册更多命令。"

        card = CardMessage(
            header={"text": "SkBookBot 帮助", "bg": "#E8F1FD", "color": "#3B82F6"},
            title="可用命令",
            rows=[
                {"text": help_text, "color": "#5C6470"},
            ],
            button={"text": "查看文档", "url": "/"},
        )
        await event.reply(card.to_json())

    async def status(self, event):
        """status 命令 - 查看机器人状态"""
        bot_name = event.bot.name
        running = "✅ 运行中" if event.bot.running else "❌ 已停止"
        communities = event.bot._communities if hasattr(event.bot, "_communities") else []

        text = f"**机器人状态**\n\n"
        text += f"名称: {bot_name}\n"
        text += f"状态: {running}\n"
        text += f"监听社区: {len(communities)} 个\n"
        text += f"命令前缀: {event.bot.command_prefix}\n"
        await event.reply(text)

    async def about(self, event):
        """about 命令 - 关于信息"""
        text = "**SkBookBot**\n\n"
        text += "基于 SkBook 开放平台的机器人框架\n"
        text += "支持多机器人、插件热重载、Web 管理面板\n\n"
        text += "💡 使用 /help 查看可用命令"
        await event.reply(text)