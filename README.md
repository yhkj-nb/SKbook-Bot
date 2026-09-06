# SkBookBot

> SkBook 开放平台机器人框架 — 基于 Python 的多机器人管理框架，支持插件热重载与 Web 管理面板。

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![Vue](https://img.shields.io/badge/Vue-3.4%2B-4FC08D)](https://vuejs.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 概览

SkBookBot 是一个专为 [SkBook 开放平台](https://skbook.sk26.cn) 设计的机器人框架，对标 ElainaBot_v2 的架构设计，提供完整的机器人生命周期管理、插件系统和可视化面板。

```
┌─────────────────────────────────────────────────────┐
│                    SkBookBot                         │
├─────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │ 机器人管理 │  │ 插件系统  │  │ Web 管理面板 (Vue) │  │
│  ├─────────┤  ├──────────┤  ├───────────────────┤  │
│  │ 多实例   │  │ 热重载    │  │ 仪表盘 / 机器人   │  │
│  │ 消息轮询 │  │ 装饰器    │  │ 插件 / 消息 / 设置│  │
│  │ API 封装 │  │ 上下文    │  │ 密码 / OAuth2 登录│  │
│  └─────────┘  └──────────┘  └───────────────────┘  │
│  ┌──────────────────────────────────────────────┐   │
│  │       SkBook 开放平台 API                          │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## 架构

```
SkBookBot/
├── main.py                          # 主入口
├── config/                          # 配置文件
│   ├── bot.example.yaml             # 多机器人配置
│   └── settings.example.yaml        # 框架设置
├── core/                            # 核心框架
│   ├── application.py               # Application 编排
│   ├── base/                        # 基础层（配置/日志/上下文）
│   ├── bot/                         # 机器人管理（注册表/实例/管理器）
│   ├── network/                     # 网络层（API 客户端/OAuth2）
│   ├── message/                     # 消息处理（事件/发送器/卡片）
│   ├── plugin/                      # 插件系统（管理器/装饰器/上下文）
│   ├── server/                      # HTTP 服务器 + 管理 API
│   ├── storage/                     # 数据持久化
│   └── services/                    # 后台服务（配置热重载）
├── plugins/                         # 插件目录
│   └── system/main.py               # 系统插件
├── frontend/                        # Vue 3 前端源码
├── web/                             # 前端构建产物
└── docs/                            # 文档
    └── plugin-development.md        # 插件开发指南
```

## 特性

### 多机器人管理
- 支持同时运行多个机器人，独立配置 Token、社区、命令前缀
- 自动轮询 SkBook 频道消息，支持社区粒度或全局模式
- 运行时动态添加/删除/重启机器人

### 插件系统
- 插件热重载：修改插件文件后自动生效，无需重启框架
- 装饰器注册：通过 `@on_command` / `@on_message` 注册处理器
- 卡片消息：内置 `CardMessage` 构建器，支持完整 SkBook 卡片格式
- 数据持久化：插件可通过 SQLite 存储数据

### Web 管理面板
- 基于 Vue 3 + Pinia + Vue Router 构建
- 5 个管理页面：仪表盘、机器人管理、插件管理、消息记录、系统设置
- 支持管理员密码登录和 SkBook OAuth2 账号授权两种登录方式

### 消息类型
- **纯文本**：直接发送字符串
- **卡片消息**：JSON 格式，支持头部、标题、内容行、头像、按钮、配色
- **命令系统**：自定义命令前缀，路由到对应插件处理器

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+（仅开发前端时需要）

### 安装与运行

```bash
# 克隆仓库
git clone https://github.com/yhkj-nb/SKbook-Bot.git
cd SKbook-Bot

# 复制配置
cp .env.example .env
cp config/bot.example.yaml config/bot.yaml
cp config/settings.example.yaml config/settings.yaml

# 编辑配置
# .env 中设置 WEB_ADMIN_PASSWORD 管理员密码
# config/bot.yaml 中填入机器人 Token

# 安装依赖
pip install -r requirements.txt

# 启动
python3 main.py
```

浏览器访问 `http://localhost:5200`，使用管理员密码登录。

### Docker 部署

```bash
docker compose up -d
```

## 配置说明

### 环境变量 (.env)

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `WEB_HOST` | 服务器地址 | 0.0.0.0 |
| `WEB_PORT` | 服务器端口 | 5200 |
| `WEB_ADMIN_PASSWORD` | 管理员密码 | admin123 |
| `BOT_TOKEN` | 默认机器人 Token | - |
| `OAUTH2_CLIENT_ID` | OAuth2 Client ID | - |
| `OAUTH2_CLIENT_SECRET` | OAuth2 Client Secret | - |
| `OAUTH2_REDIRECT_URI` | OAuth2 回调地址 | - |

### 机器人配置 (config/bot.yaml)

支持多机器人配置：

```yaml
bots:
  - name: "机器人名称"
    token: "your-bot-token"
    enabled: true
    communities: []          # 监听社区（留空为全部）
    poll_interval: 3         # 轮询间隔（秒）
    command_prefix: "/"      # 命令前缀
```

## 登录方式

### 1. 密码登录
在 `.env` 中配置 `WEB_ADMIN_PASSWORD`，登录页输入密码即可。

### 2. OAuth2 登录
1. 在 SkBook 应用设置页开启 OAuth2，填写回调地址
2. 在 `.env` 中配置 `OAUTH2_CLIENT_ID` 和 `OAUTH2_CLIENT_SECRET`
3. 登录页选择「SkBook 账号授权」，跳转至 SkBook 授权页
4. 授权成功后获取用户信息（名称、头像、ID、手机号）

## 插件开发

```python
# plugins/hello_plugin.py
from core.plugin.decorators import on_command, on_message
from core.plugin.context import PluginContext

class HelloPlugin:
    _skbook_handlers = [
        {"type": "command", "name": "hello", "aliases": ["你好"]},
    ]

    def __init__(self):
        self.ctx: PluginContext = None

    async def on_load(self):
        self.ctx.log.info("插件已加载")

    async def hello(self, event):
        await event.reply(f"你好！你的用户ID是 {event.sender_id}")
```

详细文档见 [docs/plugin-development.md](docs/plugin-development.md)。

## API 概览

框架封装了 SkBook 开放平台的全部接口：

| 接口 | 方法 | 说明 |
|------|------|------|
| `get_channels/` | GET | 获取社区频道列表 |
| `get_messages/` | GET | 获取频道消息 |
| `get_all_messages/` | GET | 获取所有社区消息 |
| `send_channel_message/` | POST | 发送频道消息 |
| `send_dm_message/` | POST | 发送私信 |
| `mute_user/` | POST | 禁言用户 |
| `kick_member/` | POST | 移除用户 |
| OAuth2 流程 | - | 授权码换取用户信息 |

## 错误码

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 40001 | 参数缺失或格式错误 |
| 40101 | Token 无效 |
| 40301 | 机器人未添加到社区 |
| 50000 | 服务器内部错误 |

## 项目参考

本项目参考了 [ElainaBot_v2](https://github.com/ElainaCore/ElainaBot_v2) 的架构设计，针对 SkBook 开放平台重新实现。

## License

MIT