"""插件装饰器"""

from typing import List, Callable, Optional, Pattern
import re
from ..base.logger import logger


class PluginDecorators:
    """插件装饰器集合"""

    @staticmethod
    def on_command(name: str, aliases: List[str] = None):
        """监听命令的装饰器

       用法:
           @plugin.on_command("hello")
           async def hello_handler(event: MessageEvent):
               event.reply("world")
       """
        def decorator(func: Callable):
            if not hasattr(func, "_skbook_handlers"):
                func._skbook_handlers = []
            func._skbook_handlers.append({
                "type": "command",
                "name": name,
                "aliases": aliases or [],
            })
            return func
        return decorator

    @staticmethod
    def on_message(matcher: Callable = None, pattern: str = None):
        """监听消息的装饰器

       用法:
           @plugin.on_message(pattern=r"你好")
           async def hello_handler(event):
               event.reply("你好！")
       """
        compiled = re.compile(pattern) if pattern else None

        def decorator(func: Callable):
            if not hasattr(func, "_skbook_handlers"):
                func._skbook_handlers = []
            func._skbook_handlers.append({
                "type": "message",
                "matcher": matcher,
                "pattern": compiled,
            })
            return func
        return decorator if pattern else decorator

    @staticmethod
    def on_event(event_type: str):
        """监听特定事件的装饰器"""
        def decorator(func: Callable):
            if not hasattr(func, "_skbook_handlers"):
                func._skbook_handlers = []
            func._skbook_handlers.append({
                "type": "event",
                "event_type": event_type,
            })
            return func
        return decorator


# 快捷引用
on_command = PluginDecorators.on_command
on_message = PluginDecorators.on_message
on_event = PluginDecorators.on_event