"""HttpServer - 基于 aiohttp 的 HTTP 服务器"""

import json
import os
import secrets
import mimetypes
from typing import Optional, Dict, Any, List
from pathlib import Path

import yaml
from aiohttp import web

from ..base.logger import logger
from ..base.config import config
from ..base.context import get_app
from ..network.api_client import OAuth2Client, SkBookAPIError


# settings.yaml 可保存的键白名单
SETTINGS_ALLOWED_KEYS = {
    "server.host", "server.port",
    "web.enabled", "web.admin_password", "web.session_expire",
    "logging.level", "logging.file", "logging.max_size", "logging.backup_count",
    "database.path",
    "data_dir",
    "oauth2.client_id", "oauth2.client_secret", "oauth2.redirect_uri",
    "services.config_watcher", "services.media_cleanup", "services.message_cleanup_days",
}


def _mask_token(token: str) -> str:
    """脱敏显示 token，保留前 8 位"""
    if not token:
        return ""
    return token[:8] + "****" if len(token) > 8 else token + "****"


class HttpServer:
    """HTTP 服务器，提供 Web 管理面板 API"""

    def __init__(self):
        self._app: Optional[web.Application] = None
        self._runner: Optional[web.AppRunner] = None
        self._sessions: Dict[str, dict] = {}  # session_token -> session_data
        self._web_dir: Path = Path.cwd() / "web"

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
        self._app.router.add_post("/api/auth/password", self._handle_change_password)

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

        # 更新检查
        self._app.router.add_get("/api/update/check", self._handle_update_check)
        self._app.router.add_get("/api/update/version", self._handle_get_version)

        # 静态文件 + SPA 兜底（匹配所有非 API 的 GET 请求）
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

    # --- 认证路由 ---

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

    async def _handle_change_password(self, request: web.Request) -> web.Response:
        """修改管理员密码"""
        session = self._check_auth(request)
        if not session:
            return web.json_response({"success": False, "message": "未认证"}, status=401)

        try:
            body = await request.json()
        except Exception:
            return web.json_response({"success": False, "message": "无效的请求数据"}, status=400)

        old_password = body.get("old_password", "")
        new_password = body.get("new_password", "")

        admin_password = config.get("web.admin_password", "")

        # 如果已设置密码，必须验证旧密码
        if admin_password and old_password != admin_password:
            return web.json_response({"success": False, "message": "当前密码不正确"}, status=400)

        if not new_password:
            return web.json_response({"success": False, "message": "新密码不能为空"}, status=400)

        if len(new_password) < 6:
            return web.json_response({"success": False, "message": "新密码至少 6 位"}, status=400)

        config.set("web.admin_password", new_password)
        config.save_settings()
        return web.json_response({"success": True, "message": "密码已更新"})

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
        except Exception as e:
            return web.json_response({"success": False, "message": str(e)}, status=400)

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
        except Exception as e:
            return web.json_response({"success": False, "message": str(e)}, status=400)

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
        """获取全量配置（脱敏返回）"""
        if not self._check_auth(request):
            return web.json_response({"success": False, "message": "未认证"}, status=401)

        admin_pw = config.get("web.admin_password", "")
        oauth2_secret = config.get("oauth2.client_secret", "")

        cfg = {
            "server": {
                "host": config.get("server.host", "0.0.0.0"),
                "port": config.get("server.port", 5200),
                "has_web_secret_key": bool(config.get("server.web_secret_key", "")),
            },
            "web": {
                "enabled": config.get("web.enabled", True),
                "has_admin_password": bool(admin_pw),
                "session_expire": config.get("web.session_expire", 86400),
            },
            "oauth2": {
                "client_id": config.get("oauth2.client_id", ""),
                "has_client_secret": bool(oauth2_secret),
                "redirect_uri": config.get("oauth2.redirect_uri", ""),
            },
            "logging": {
                "level": config.get("logging.level", "INFO"),
                "file": config.get("logging.file", ""),
                "max_size": config.get("logging.max_size", 5242880),
                "backup_count": config.get("logging.backup_count", 3),
            },
            "database": {
                "path": config.get("database.path", "./data/skbookbot.db"),
            },
            "data_dir": config.get("data_dir", "./data"),
            "services": {
                "config_watcher": config.get("services.config_watcher", True),
                "media_cleanup": config.get("services.media_cleanup", False),
                "message_cleanup_days": config.get("services.message_cleanup_days", 30),
            },
            "bots": [
                {
                    "name": b.get("name", ""),
                    "token_masked": _mask_token(b.get("token", "")),
                    "enabled": b.get("enabled", True),
                    "communities": b.get("communities", []),
                    "poll_interval": b.get("poll_interval", 3),
                    "command_prefix": b.get("command_prefix", "/"),
                }
                for b in config.get_bots()
            ],
        }
        return web.json_response({"success": True, "data": cfg})

    async def _handle_update_config(self, request: web.Request) -> web.Response:
        """更新配置（settings 写 settings.yaml，bots 写 bot.yaml）"""
        if not self._check_auth(request):
            return web.json_response({"success": False, "message": "未认证"}, status=401)

        try:
            body = await request.json()
        except Exception:
            return web.json_response({"success": False, "message": "无效的请求数据"}, status=400)

        needs_restart = []

        # 保存 settings 相关字段
        for key, value in body.items():
            if key == "bots":
                continue  # 单独处理
            if key in SETTINGS_ALLOWED_KEYS:
                # 部分字段修改需要重启
                if key in ("server.host", "server.port", "logging.file", "logging.max_size",
                           "logging.backup_count", "database.path", "data_dir"):
                    needs_restart.append(key)
                config.set(key, value)

        config.save_settings()

        # 保存 bots 配置
        bots_data = body.get("bots")
        if bots_data is not None and isinstance(bots_data, list):
            # 将前端传入的 bot 配置合并到现有 bots（保留 token 原文）
            existing_bots = {b.get("name", ""): b for b in config.get_bots()}
            merged = []
            for item in bots_data:
                name = item.get("name", "")
                if name in existing_bots:
                    # 保留原有 token，除非前端传了新 token
                    merged_bot = dict(existing_bots[name])
                    merged_bot.update(item)
                    # 如果前端传的是脱敏 token，保留原值
                    if item.get("token", "").endswith("****") and item.get("token", "")[:8] == existing_bots[name].get("token", "")[:8]:
                        merged_bot["token"] = existing_bots[name]["token"]
                    merged.append(merged_bot)
                else:
                    merged.append(item)
            config.set_bots(merged)
            config.save_bots()
            # 尝试热加载 bot 配置
            try:
                config.load_bot_config(str(Path(config.config_dir) / "bot.yaml") if config.config_dir else "config/bot.yaml")
            except Exception:
                pass

        message = "配置已保存"
        if needs_restart:
            keys_str = "、".join(needs_restart)
            message += f"。以下配置需重启服务后生效：{keys_str}"

        return web.json_response({"success": True, "message": message})

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

    # --- 更新检查 ---

    CURRENT_VERSION = "v1.0.0"

    async def _handle_update_check(self, request: web.Request) -> web.Response:
        """检查框架更新"""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.github.com/repos/yhkj-nb/SKbook-Bot/releases/latest",
                    headers={"Accept": "application/vnd.github.v3+json"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    latest = data.get("tag_name", "")
                    has_update = latest != self.CURRENT_VERSION
                    return web.json_response({
                        "success": True,
                        "data": {
                            "has_update": has_update,
                            "current_version": self.CURRENT_VERSION,
                            "latest_version": latest,
                            "release_time": data.get("published_at", ""),
                            "release_notes": data.get("body", ""),
                            "download_url": data.get("html_url", ""),
                        }
                    })
        except Exception as e:
            logger.warning(f"检查更新失败: {e}")

        return web.json_response({
            "success": True,
            "data": {
                "has_update": False,
                "current_version": self.CURRENT_VERSION,
                "latest_version": self.CURRENT_VERSION,
                "release_time": "",
                "release_notes": "",
                "download_url": "",
            }
        })

    async def _handle_get_version(self, request: web.Request) -> web.Response:
        """获取当前版本"""
        return web.json_response({
            "success": True,
            "data": {
                "version": self.CURRENT_VERSION,
                "update_time": "2026-01-01",
            }
        })

    # --- 静态文件 + SPA 兜底 ---

    async def _handle_static_or_spa(self, request: web.Request) -> web.Response:
        """处理静态文件请求，未匹配到文件时返回 index.html（SPA 兜底）"""
        if request.method not in ("GET", "HEAD"):
            return web.json_response({"error": "Method not allowed"}, status=405)

        tail = request.match_info.get("tail", "")
        file_path = tail if tail else "index.html"
        full_path = self._web_dir / file_path

        try:
            full_path = full_path.resolve()
            if not str(full_path).startswith(str(self._web_dir.resolve())):
                return web.FileResponse(self._web_dir / "index.html")
        except (ValueError, OSError):
            return web.FileResponse(self._web_dir / "index.html")

        if full_path.exists() and full_path.is_file():
            content_type, _ = mimetypes.guess_type(str(full_path))
            if content_type is None:
                content_type = "application/octet-stream"
            return web.FileResponse(full_path, headers={
                "Content-Type": content_type,
                "Cache-Control": "no-cache" if file_path == "index.html" else "public, max-age=3600",
            })

        index_path = self._web_dir / "index.html"
        if index_path.exists():
            return web.FileResponse(index_path)
        else:
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
        .container { text-align: center; padding: 40px; }
        h1 { font-size: 36px; margin-bottom: 12px; }
        p { font-size: 16px; color: #94A3B8; margin-bottom: 8px; line-height: 1.8; }
        .status {
            display: inline-block; margin-top: 24px; padding: 12px 24px;
            background: rgba(59, 130, 246, 0.2); border: 1px solid rgba(59, 130, 246, 0.4);
            border-radius: 8px; color: #60A5FA; font-size: 14px;
        }
        .api-link {
            display: inline-block; margin-top: 16px; padding: 10px 20px;
            background: #3B82F6; color: #fff; text-decoration: none;
            border-radius: 8px; font-size: 14px;
        }
        .api-link:hover { background: #2563EB; }
        code {
            background: rgba(255,255,255,0.1); padding: 2px 6px;
            border-radius: 4px; font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>SkBookBot</h1>
        <p>后端服务运行中</p>
        <div class="status">✅ 服务器已启动</div>
        <p style="margin-top: 20px;">Web 管理面板前端未构建</p>
        <a class="api-link" href="/api/stats">查看 API 状态</a>
        <p style="margin-top: 20px; font-size: 14px; color: #94A3B8;">
            如需构建前端，请运行：
        </p>
        <p style="margin-top: 8px;"><code>cd frontend && npm install && npm run build</code></p>
    </div>
</body>
</html>"""