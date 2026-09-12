"""主插件"""

from core.plugin.decorators import on_command, on_message

@on_command(name="echo", aliases=["say"])
async def cmd_echo(event):
    """回声命令"""
    text = event.command_args or "你好！"
    await event.reply(text)

@on_message(pattern=r".*你好.*")
async def hello_reply(event):
    """自动回复"""
    await event.reply(f"你好！(来自 {event.sender_id})")