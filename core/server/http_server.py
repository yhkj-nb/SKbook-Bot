"""HttpServer - 基于 aiohttp 的 HTTP 服务器"""

import json
import os
import secrets
import mimetypes
from typing import Optional, Dict, Any
from pathlib import Path

from aiohttp import web

from ..base.logger import logger
from ..base.config import config
from ..base.context import get_app
from ..network.api_client import OAuth2Client, SkBookAPIError


class HttpServer:
    """HTTP 服务器，提供 Web 管理面板 API"""

    def __init__(self):
        self._app: Optional[web.Application] = None
        self._runner: Optional[web.AppRunner] = None
        self._sessions: Dict[str, dict] = {}  # session_token -> session_data

    async def initialize(self) -> None:
        """初始化路由"""
        self._app = web.Application()
        self._setup_routes()

    def _setup_routes(self) -> None:
        """设置路由 - API 路由优先，静态文件/SPA 兜底在后"""
        # 认证
        self._app.router.add_post("/api/auth/login", self._handle_login)
        self._app.router.add_get("/api/auth/oauth2/url", self._handle_oauth2_url)
        self._app.router.add_get("/api/auth/oauth2/callback", self._handle_oauth2_callback)
        self._app.router.add_post("/api/auth/logout", self._handle_logout)
        self._app.router.add_get("/api/auth/check", self._handle_auth_check)

        # 机器人管理
        self._app.router.add_get("/api/bots", self._handle_get_bots)
        self._app.router.add_post("/api/bots", self._handle_create_bot)
        self._app.router.add_delete("/api/bots/{name}", self._handle_delete_bot)
        self._app.router.add_post("/api/bots/{name}/restart", self._handle_restart_bot)

        # 社区/频道
        self._app.router.add_get("/api/communities", self._handle_get_communities)
        self._app.router.add_get("/api/channels", self._handle_get_channels)

        # 消息
        self._app.router.add_get("/api/messages", self._handle_get_messages)
        self._app.router.add_post("/api/messages/send", self._handle_send_message)

        # 插件管理
        self._app.router.add_get("/api/plugins", self._handle_get_plugins)
        self._app.router.add_post("/api/plugins/{name}/reload", self._handle_reload_plugin)

        # 配置管理
        self._app.router.add_get("/api/config", self._handle_get_config)
        self._app.router.add_post("/api/config", self._handle_update_config)

        # 仪表盘
        self._app.router.add_get("/api/stats", self._handle_get_stats)

        # 静态文件 + SPA 兜底（匹配所有非 API 的 GET 请求）
        self._web_dir = Path.cwd() / "web"
        self._app.router.add_get("/{tail:.*}", self._handle_static_or_spa)

    async def start(self) -> None:
        """启动 HTTP 服务器"""
        host = config.get("server.host", "0.0.0.0")
        port = config.get("server.port", 5200)

        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, host, port)
        await site.start()
        logger.info(f"HTTP 服务器已启动: http://{host}:{port}")

    async def stop(self) -> None:
        """停止 HTTP 服务器"""
        if self._runner:
            await self._runner.cleanup()
            logger.info("HTTP 服务器已停止")

    # --- 认证相关 ---

    def _check_auth(self, request: web.Request) -> Optional[dict]:
        """检查请求是否已认证"""
        token = request.headers.get("X-Session-Token", "")
        return self._sessions.get(token)

    def _create_session(self, data: dict) -> str:
        """创建会话"""
        token = secrets.token_hex(32)
        self._sessions[token] = data
        return token

    # --- 路由处理 ---

    async def _handle_login(self, request: web.Request) -> web.Response:
        """密码登录"""
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"success": False, "message": "无效的请求数据"}, status=400)

        password = body.get("password", "")
        admin_password = config.get("web.admin_password", "")

        if not admin_password:
            return web.json_response({"success": False, "message": "未配置管理员密码"}, status=403)

        if password == admin_password:
            token = self._create_session({"role": "admin", "login_type": "password"})
            return web.json_response({
                "success": True,
                "data": {"token": token, "role": "admin"}
            })

        return web.json_response({"success": False, "message": "密码错误"}, status=403)

    async def _handle_oauth2_url(self, request: web.Request) -> web.Response:
        """获取 OAuth2 授权 URL"""
        client_id = config.get("oauth2.client_id", "")
        redirect_uri = config.get("oauth2.redirect_uri", "")

        if not client_id:
            return web.json_response({"success": False, "message": "未配置 OAuth2"}, status=400)

        oauth2 = OAuth2Client(client_id, "", redirect_uri)
        state = secrets.token_hex(16)
        url = oauth2.get_authorize_url(state)

        return web.json_response({
            "success": True,
            "data": {"url": url, "state": state}
        })

    async def _handle_oauth2_callback(self, request: web.Request) -> web.Response:
        """OAuth2 回调处理"""
        code = request.query.get("code", "")
        state = request.query.get("state", "")

        client_id = config.get("oauth2.client_id", "")
        client_secret = config.get("oauth2.client_secret", "")
        redirect_uri = config.get("oauth2.redirect_uri", "")

        if not code:
            return web.json_response({"success": False, "message": "缺少 code 参数"}, status=400)

        oauth2 = OAuth2Client(client_id, client_secret, redirect_uri)
        try:
            token_data = await oauth2.exchange_code(code)
            access_token = token_data.get("access_token", "")
            user_info = await oauth2.get_userinfo(access_token)

            session_token = self._create_session({
                "role": "user",
                "login_type": "oauth2",
                "oauth2_token": access_token,
                "user_info": user_info,
            })

            return web.json_response({
                "success": True,
                "data": {
                    "token": session_token,
                    "user_info": user_info,
                }
            })
        except SkBookAPIError as e:
            return web.json_response({"success": False, "message": f"OAuth2 失败: {e.message}"}, status=400)
        except Exception as e:
            return web.json_response({"success": False, "message": f"OAuth2 失败: {e}"}, status=500)

    async def _handle_logout(self, request: web.Request) -> web.Response:
        """登出"""
        token = request.headers.get("X-Session-Token", "")
        self._sessions.pop(token, None)
        return web.json_response({"success": True})

    async def _handle_auth_check(self, request: web.Request) -> web.Response:
        """检查认证状态"""
        session = self._check_auth(request)
        if session:
            return web.json_response({
                "success": True,
                "data": {
                    "authenticated": True,
                    "role": session.get("role"),
                    "login_type": session.get("login_type"),
                    "user_info": session.get("user_info"),
                }
            })
        return web.json_response({
            "success": True,
            "data": {"authenticated": False}
        })

    # --- 机器人管理 ---

    async def _handle_get_bots(self, request: web.Request) -> web.Response:
        """获取机器人列表"""
        if not self._check_auth(request):
            return web.json_response({"success": False, "message": "未认证"}, status=401)

        app = get_app()
        if not app:
            return web.json_response({"success": False, "message": "应用未初始化"}, status=500)

        bots = []
        for bot in app.bot_registry.list():
            bots.append({
                "name": bot.name,
                "running": bot.running,
                "token_masked": bot.token[:8] + "****" if bot.token else "",
                "communities": bot._communities if hasattr(bot, "_communities") else [],
                "poll_interval": bot._poll_interval if hasattr(bot, "_poll_interval") else 3,
                "command_prefix": bot.command_prefix,
            })

        return web.json_response({"success": True, "data": {"bots": bots}})

    async def _handle_create_bot(self, request: web.Request) -> web.Response:
        """创建机器人"""
        if not self._check_auth(request):
            return web.json_response({"success": False, "message": "未认证"}, status=401)

        try:
            body = await request.json()
        except Exception:
            return web.json_response({"success": False, "message": "无效的请求数据"}, status=400)

        name = body.get("name", "")
        token = body.get("token", "")
        if not name or not token:
            return web.json_response({"success": False, "message": "名称和 Token 不能为空"}, status=400)

        app = get_app()
        if not app:
            return web.json_response({"success": False, "message": "应用未初始化"}, status=500)

        if app.bot_registry.get(name):
            return web.json_response({"success": False, "message": "机器人名称已存在"}, status=400)

        bot = app.bot_manager.create_bot(name, token, body)
        await bot.start()

        return web.json_response({"success": True, "data": {"name": name}})

    async def _handle_delete_bot(self, request: web.Request) -> web.Response:
        """删除机器人"""
        if not self._check_auth(request):
            return web.json_response({"success": False, "message": "未认证"}, status=401)

        name = request.match_info.get("name", "")
        app = get_app()
        if not app:
            return web.json_response({"success": False, "message": "应用未初始化"}, status=500)

        app.bot_manager.remove_bot(name)
        return web.json_response({"success": True})

    async def _handle_restart_bot(self, request: web.Request) -> web.Response:
        """重启机器人"""
        if not self._check_auth(request):
            return web.json_response({"success": False, "message": "未认证"}, status=401)

        name = request.match_info.get("name", "")
        app = get_app()
        if not app:
            return web.json_response({"success": False, "message": "应用未初始化"}, status=500)

        bot = app.bot_registry.get(name)
        if not bot:
            return web.json_response({"success": False, "message": "机器人不存在"}, status=404)

        await bot.restart()
        return web.json_response({"success": True})

    # --- 社区/频道 ---

    async def _handle_get_communities(self, request: web.Request) -> web.Response:
        """获取社区列表（通过机器人）"""
        # 简化实现：从机器人配置中读取
        app = get_app()
        if not app:
            return web.json_response({"success": False, "message": "应用未初始化"}, status=500)

        communities = []
        for bot in app.bot_registry.list():
            bot_comms = bot._communities if hasattr(bot, "_communities") else []
            for cid in bot_comms:
                communities.append({"id": cid, "bot_name": bot.name})

        return web.json_response({"success": True, "data": {"communities": communities}})

    async def _handle_get_channels(self, request: web.Request) -> web.Response:
        """获取频道列表"""
        if not self._check_auth(request):
            return web.json_response({"success": False, "message": "未认证"}, status=401)

        community_id = request.query.get("community_id", "")
        bot_name = request.query.get("bot_name", "")

        app = get_app()
        if not app:
            return web.json_response({"success": False, "message": "应用未初始化"}, status=500)

        bot = app.bot_registry.get(bot_name) if bot_name else app.bot_registry.list_active()[0]
        if not bot:
            return web.json_response({"success": False, "message": "未找到可用机器人"}, status=404)

        try:
            channels = await bot.api.get_channels(community_id)
            return web.json_response({"success": True, "data": {"channels": channels}})
        except SkBookAPIError as e:
            return web.json_response({"success": False, "message": e.message}, status=400)

    # --- 消息 ---

    async def _handle_get_messages(self, request: web.Request) -> web.Response:
        """获取消息记录"""
        if not self._check_auth(request):
            return web.json_response({"success": False, "message": "未认证"}, status=401)

        community_id = request.query.get("community_id", "")
        channel_id = request.query.get("channel_id", "")
        limit = int(request.query.get("limit", 20))
        bot_name = request.query.get("bot_name", "")

        app = get_app()
        if not app:
            return web.json_response({"success": False, "message": "应用未初始化"}, status=500)

        bot = app.bot_registry.get(bot_name) if bot_name else app.bot_registry.list_active()[0]
        if not bot:
            return web.json_response({"success": False, "message": "未找到可用机器人"}, status=404)

        try:
            data = await bot.api.get_messages(community_id, int(channel_id), limit)
            return web.json_response({"success": True, "data": data})
        except SkBookAPIError as e:
            return web.json_response({"success": False, "message": e.message}, status=400)

    async def _handle_send_message(self, request: web.Request) -> web.Response:
        """发送消息"""
        if not self._check_auth(request):
            return web.json_response({"success": False, "message": "未认证"}, status=401)

        try:
            body = await request.json()
        except Exception:
            return web.json_response({"success": False, "message": "无效的请求数据"}, status=400)

        community_id = body.get("community_id", "")
        channel_id = body.get("channel_id", "")
        content = body.get("content", "")
        bot_name = body.get("bot_name", "")

        app = get_app()
        if not app:
            return web.json_response({"success": False, "message": "应用未初始化"}, status=500)

        bot = app.bot_registry.get(bot_name) if bot_name else app.bot_registry.list_active()[0]
        if not bot:
            return web.json_response({"success": False, "message": "未找到可用机器人"}, status=404)

        success = await bot.sender.send_channel(community_id, int(channel_id), content)
        return web.json_response({"success": success})

    # --- 插件管理 ---

    async def _handle_get_plugins(self, request: web.Request) -> web.Response:
        """获取插件列表"""
        if not self._check_auth(request):
            return web.json_response({"success": False, "message": "未认证"}, status=401)

        app = get_app()
        if not app:
            return web.json_response({"success": False, "message": "应用未初始化"}, status=500)

        plugins = app.plugin_manager.get_plugin_list()
        return web.json_response({"success": True, "data": {"plugins": plugins}})

    async def _handle_reload_plugin(self, request: web.Request) -> web.Response:
        """重载插件"""
        if not self._check_auth(request):
            return web.json_response({"success": False, "message": "未认证"}, status=401)

        name = request.match_info.get("name", "")
        app = get_app()
        if not app:
            return web.json_response({"success": False, "message": "应用未初始化"}, status=500)

        success = await app.plugin_manager.reload_plugin(name)
        return web.json_response({"success": success})

    # --- 配置管理 ---

    async def _handle_get_config(self, request: web.Request) -> web.Response:
        """获取配置"""
        if not self._check_auth(request):
            return web.json_response({"success": False, "message": "未认证"}, status=401)

        # 返回脱敏后的配置
        cfg = {
            "server": {"host": config.get("server.host"), "port": config.get("server.port")},
            "web": {"enabled": config.get("web.enabled", True)},
            "oauth2": {
                "client_id": config.get("oauth2.client_id", ""),
                "redirect_uri": config.get("oauth2.redirect_uri", ""),
            },
            "logging": {"level": config.get("logging.level", "INFO")},
            "services": {
                "config_watcher": config.get("services.config_watcher", True),
                "message_cleanup_days": config.get("services.message_cleanup_days", 30),
            },
        }
        return web.json_response({"success": True, "data": cfg})

    async def _handle_update_config(self, request: web.Request) -> web.Response:
        """更新配置（简化实现）"""
        if not self._check_auth(request):
            return web.json_response({"success": False, "message": "未认证"}, status=401)

        try:
            body = await request.json()
        except Exception:
            return web.json_response({"success": False, "message": "无效的请求数据"}, status=400)

        for key, value in body.items():
            config.set(key, value)

        return web.json_response({"success": True})

    # --- 仪表盘 ---

    async def _handle_get_stats(self, request: web.Request) -> web.Response:
        """获取统计数据"""
        if not self._check_auth(request):
            return web.json_response({"success": False, "message": "未认证"}, status=401)

        import psutil
        app = get_app()

        stats = {
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_used": psutil.virtual_memory().used // (1024 * 1024),
                "memory_total": psutil.virtual_memory().total // (1024 * 1024),
            },
            "bots": {
                "total": len(app.bot_registry.list()) if app else 0,
                "active": len(app.bot_registry.list_active()) if app else 0,
            },
            "plugins": {
                "total": len(app.plugin_manager.plugins) if app else 0,
            },
        }
        return web.json_response({"success": True, "data": stats})

    # --- 静态文件 + SPA 兜底 ---

    async def _handle_static_or_spa(self, request: web.Request) -> web.Response:
        """处理静态文件请求，未匹配到文件时返回 index.html（SPA 兜底）

        路由匹配顺序: API 路由 > 静态文件 > index.html
        """
        # 只处理 GET/HEAD 请求
        if request.method not in ("GET", "HEAD"):
            return web.json_response({"error": "Method not allowed"}, status=405)

        # 获取请求路径
        tail = request.match_info.get("tail", "")
        # 处理根路径
        file_path = tail if tail else "index.html"

        # 构建完整的文件路径
        full_path = self._web_dir / file_path

        # 防止目录遍历攻击
        try:
            full_path = full_path.resolve()
            if not str(full_path).startswith(str(self._web_dir.resolve())):
                return web.FileResponse(self._web_dir / "index.html")
        except (ValueError, OSError):
            return web.FileResponse(self._web_dir / "index.html")

        # 如果文件存在，直接返回
        if full_path.exists() and full_path.is_file():
            content_type, _ = mimetypes.guess_type(str(full_path))
            if content_type is None:
                content_type = "application/octet-stream"
            return web.FileResponse(full_path, headers={
                "Content-Type": content_type,
                "Cache-Control": "no-cache" if file_path == "index.html" else "public, max-age=3600",
            })

        # 如果文件不存在，返回 index.html（SPA 兜底）
        index_path = self._web_dir / "index.html"
        if index_path.exists():
            return web.FileResponse(index_path)
        else:
            # 前端未构建时返回提示页面
            html = self._get_fallback_html()
            return web.Response(
                text=html,
                content_type="text/html",
                charset="utf-8",
            )

    def _get_fallback_html(self) -> str:
        """当 web/index.html 不存在时，返回内嵌的引导页面"""
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SkBookBot</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: #fff;
        }
        .container {
            text-align: center;
            padding: 40px;
        }
        h1 { font-size: 36px; margin-bottom: 12px; }
        p { font-size: 16px; color: #94A3B8; margin-bottom: 8px; line-height: 1.8; }
        .status {
            display: inline-block;
            margin-top: 24px;
            padding: 12px 24px;
            background: rgba(59, 130, 246, 0.2);
            border: 1px solid rgba(59, 130, 246, 0.4);
            border-radius: 8px;
            color: #60A5FA;
            font-size: 14px;
        }
        .api-link {
            display: inline-block;
            margin-top: 16px;
            padding: 10px 20px;
            background: #3B82F6;
            color: #fff;
            text-decoration: none;
            border-radius: 8px;
            font-size: 14px;
        }
        .api-link:hover { background: #2563EB; }
        .hint { margin-top: 24px; font-size: 13px; color: #64748B; }
        code {
            background: rgba(255,255,255,0.1);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>SkBookBot</h1>
        <p>后端服务运行中</p>
        <div class="status">✅ 服务器已启动</div>
        <p style="margin-top: 20px;">
            Web 管理面板前端未构建
        </p>
        <a class="api-link" href="/api/stats">查看 API 状态</a>
        <p style="margin-top: 20px; font-size: 14px; color: #94A3B8;">
            如需构建前端，请运行：
        </p>
        <p style="margin-top: 8px;">
            <code>cd frontend && npm install && npm run build</code>
        </p>
        <div class="hint">
            <p>API 端点: <code>/api/auth/check</code></p>
            <p>查看日志: <code>python3 main.py</code></p>
        </div>
    </div>
</body>
</html>"""