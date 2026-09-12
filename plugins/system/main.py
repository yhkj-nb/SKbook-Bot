"""系统插件"""

from core.plugin.decorators import on_command, on_message

@on_command(name="help", aliases=["h", "帮助"])
async def cmd_help(event):
    """帮助命令"""
    text = "可用命令：\n/help - 显示帮助\n/ping - 检查机器人状态\n/echo - 回复消息"
    await event.reply(text)

@on_command(name="ping", aliases=["ping"])
async def cmd_ping(event):
    """Ping 命令"""
    await event.reply("pong!")