# SkBookBot 插件开发文档

## 概述

SkBookBot 插件系统支持热加载，将插件文件放在 `plugins/` 目录下即可自动加载。支持两种插件形式：

1. **单文件插件**：`plugins/my_plugin.py`
2. **包插件**：`plugins/my_plugin/main.py`

## 快速开始

### 创建插件

在 `plugins/` 目录下创建 `.py` 文件：

```python
# plugins/hello_plugin.py
from core.plugin.decorators import on_command, on_message
from core.plugin.context import PluginContext


class HelloPlugin:
    """示例插件"""

    # 声明处理器
    _skbook_handlers = [
        {"type": "command", "name": "hello", "aliases": ["你好", "hi"]},
        {"type": "command", "name": "echo", "aliases": []},
    ]

    def __init__(self):
        self.ctx: PluginContext = None

    async def on_load(self):
        """插件加载时调用"""
        self.ctx.log.info("HelloPlugin 已加载")

    async def on_unload(self):
        """插件卸载时调用"""
        self.ctx.log.info("HelloPlugin 已卸载")

    async def hello(self, event):
        """处理 /hello 命令"""
        await event.reply(f"你好！你的用户ID是 {event.sender_id}")

    async def echo(self, event):
        """处理 /echo 命令 - 复读消息"""
        content = event.command_args or "请说点什么"
        await event.reply(f"你说：{content}")
```

### 消息匹配

除了命令匹配，还可以通过正则匹配消息：

```python
from core.plugin.decorators import on_message
import re


class GreetPlugin:
    _skbook_handlers = [
        {"type": "message", "pattern": re.compile(r"早安|晚安|你好")},
    ]

    def __init__(self):
        self.ctx = None

    async def on_message(self, event):
        await event.reply("你好！👋")
```

## 插件 API

### PluginContext

插件可以通过 `self.ctx` 访问框架能力：

```python
# 获取日志器
self.ctx.log.info("信息")
self.ctx.log.error("错误")

# 获取机器人实例
bot = self.ctx.get_bot("机器人名称")  # 指定名称
bot = self.ctx.get_bot()              # 获取第一个活跃机器人

# 获取所有机器人
bots = self.ctx.get_all_bots()

# 发送消息
await self.ctx.send_message("community_id", 123, "内容")
await self.ctx.send_dm("community_id", 456, "私信内容")
```

### MessageEvent

消息事件对象包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `message_id` | int | 消息 ID |
| `content` | str | 消息内容 |
| `sender_id` | int | 发送者用户 ID |
| `community_id` | str | 社区长 ID |
| `channel_id` | int | 频道 ID |
| `created_at` | str | 发送时间 |
| `bot` | BotInstance | 机器人实例 |
| `is_command` | bool | 是否为命令 |
| `command_name` | str | 命令名称 |
| `command_args` | str | 命令参数 |

快捷方法：

```python
# 回复频道消息
await event.reply("回复内容")

# 回复私信
await event.reply_dm("私信回复")
```

### 发送卡片消息

```python
from core.message.event import CardMessage

card = CardMessage(
    header={"text": "标题", "bg": "#E8F1FD", "color": "#3B82F6"},
    title="主标题",
    rows=[
        {"label": "说明：", "value": "内容", "unit": "单位"},
    ],
    avatars=["https://.../avatar.jpg"],
    button={"text": "按钮", "color": "#3B82F6", "url": "/page"},
    bg="#FFFFFF",
)

await event.reply(card.to_json())
```

## 装饰器方式

你也可以使用装饰器来注册处理器（函数级别）：

```python
from core.plugin.decorators import on_command, on_message


@on_command("time", aliases=["时间"])
async def time_handler(event):
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await event.reply(f"当前时间：{now}")
```

## 数据持久化

插件可以使用数据库存储数据：

```python
from core.storage.database import db

# 存储数据
await db.execute(
    "INSERT OR REPLACE INTO plugin_data (plugin_name, key, value) VALUES (?, ?, ?)",
    ("my_plugin", "counter", "42")
)

# 读取数据
row = await db.fetch_one(
    "SELECT value FROM plugin_data WHERE plugin_name = ? AND key = ?",
    ("my_plugin", "counter")
)
```

## 注意事项

1. 插件文件修改后会自动热重载（需开启 `config_watcher`）
2. 插件中的 `_skbook_handlers` 静态属性用于声明处理器
3. 处理器方法名需要与 `_skbook_handlers` 中的 `name` 字段对应
4. 插件类在加载时会自动注入 `ctx` 属性