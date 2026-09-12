"""SkBook 开放平台 API 客户端

严格依据 SkBook 开放平台 API 文档实现。
所有接口调用方式、参数、错误码均精确映射文档。

文档来源：https://skbook.sk26.cn/open/docs.php
"""

import asyncio
import json
from typing import Optional, Dict, Any, List, Union
from urllib.parse import urljoin

import httpx

from ..base.logger import logger


# ============================================================
# 错误码映射（精确对齐 API 文档错误码表）
# ============================================================
ERROR_CODE_MAP: Dict[int, str] = {
    0: "成功",
    # 4xxxx — 请求参数错误
    40001: "参数缺失或格式错误",
    40002: "社区不存在",
    40003: "频道不存在",
    40004: "用户不存在",
    # 401xx — 认证/凭证错误
    40101: "TOKEN / 凭证缺失或无效",
    40102: "访问令牌无效",
    40103: "访问令牌已过期",
    40104: "令牌对应的用户不存在",
    # 402xx — OAuth2 错误
    40201: "OAuth2 授权码无效",
    40202: "OAuth2 授权码已被使用",
    40203: "OAuth2 授权码已过期",
    40204: "redirect_uri 与授权/配置不一致",
    # 403xx — 权限错误
    40301: "机器人未添加到该社区",
    40302: "无对应社区权限 / 应用未开启 OAuth2",
    40303: "机器人未获得发送消息授权",
    40304: "频道不在机器人的授权范围内",
    40305: "机器人未获得获取消息授权",
    # 404xx — 路由错误
    40400: "未知接口或请求方式",
    # 5xxxx — 服务器错误
    50000: "服务器内部错误",
}

ERROR_CODE_MESSAGE_HINTS: Dict[int, str] = {
    40101: "请检查 BOT_TOKEN 是否在应用设置页中正确配置或已重置",
    40301: "请先在社区中安装/添加该机器人",
    40303: "请联系管理员在后台「机器人发送消息白名单」中添加上该机器人",
    40304: "请检查机器人添加时的频道授权范围是否包含目标频道",
    40305: "请联系管理员在后台「机器人获取消息白名单」中添加该机器人ID，或开启「接收服务器所有消息」",
    50000: "SkBook 服务器异常，短暂等待后可自动恢复",
}

ACTIONABLE_ERRORS = {40101, 40301, 40303, 40304, 40305}


class SkBookAPIError(Exception):
    """SkBook API 调用异常"""

    def __init__(self, code: int, message: str = "", raw_response: str = ""):
        self.code = code
        self.message = message or ERROR_CODE_MAP.get(code, f"未知错误 [{code}]")
        self.hint = ERROR_CODE_MESSAGE_HINTS.get(code, "")
        self.raw_response = raw_response
        super().__init__(self.text)

    @property
    def text(self) -> str:
        parts = [f"[{self.code}] {self.message}"]
        if self.hint:
            parts.append(f"→ {self.hint}")
        return " | ".join(parts)

    @property
    def is_actionable(self) -> bool:
        """是否为用户可以手动修复的错误"""
        return self.code in ACTIONABLE_ERRORS

    @property
    def is_auth_error(self) -> bool:
        """是否为认证/凭据错误"""
        return self.code in (40101, 40102, 40103, 40104)

    @property
    def is_perm_error(self) -> bool:
        """是否为权限错误"""
        return self.code in (40301, 40302, 40303, 40304, 40305)

    @property
    def is_retryable(self) -> bool:
        """是否可重试"""
        return self.code in (50000,) or self.code >= 50000


# ============================================================
# SkBook API 客户端
# ============================================================
class SkBookAPIClient:
    """SkBook 开放平台 API 客户端

    按照 API 文档封装所有机器人 Open API 接口。
    Token 一律通过 URL 查询参数 ?token=<TOKEN> 传递（GET/POST 均可）。
    所有接口均需机器人在对应社区内拥有相应权限。

    基址：https://skbook.sk26.cn/open/api/
    """

    BASE_URL = "https://skbook.sk26.cn/open/api/"
    REQUEST_TIMEOUT = 30.0
    CONNECT_TIMEOUT = 10.0
    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 1.0  # 指数退避基数（秒）

    def __init__(self, token: str = ""):
        self._token = token
        self._client: Optional[httpx.AsyncClient] = None
        self._retry_count = 0

    # ---- 客户端管理 ----

    async def ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.REQUEST_TIMEOUT, connect=self.CONNECT_TIMEOUT),
                follow_redirects=False,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, value: str) -> None:
        self._token = value

    # ---- URL 构建 ----

    def _build_url(self, endpoint: str) -> str:
        """构建带 token 的完整 API URL

        API 文档规定：
        - 机器人 Open API 通过 ?token=<TOKEN> 参数传递 TOKEN
        - GET / POST 均支持此方式
        """
        url = urljoin(self.BASE_URL, endpoint.lstrip("/"))
        if self._token:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}token={self._token}"
        return url

    # ---- 核心请求方法 ----

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """发送 API 请求（带自动重试和错误映射）

        返回统一结构的 dict（已校验 success=True）。
        失败时抛出 SkBookAPIError。
        """
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                return await self._do_request(method, endpoint, params, data)
            except SkBookAPIError:
                raise  # 业务错误直接抛出，不重试
            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as e:
                last_exc = e
                if attempt < self.MAX_RETRIES:
                    delay = self.RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    logger.warning(
                        "API 请求 %s %s 失败（第 %d/%d 次）: %s，%s 秒后重试",
                        method,
                        endpoint,
                        attempt,
                        self.MAX_RETRIES,
                        e,
                        delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "API 请求 %s %s 重试 %d 次均失败: %s",
                        method,
                        endpoint,
                        self.MAX_RETRIES,
                        e,
                    )
            except Exception as e:
                last_exc = e
                logger.error("API 请求 %s %s 未知错误: %s", method, endpoint, e)
                break

        raise SkBookAPIError(50000, f"网络请求失败: {last_exc}")

    async def _do_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """执行单次 HTTP 请求"""
        client = await self.ensure_client()
        url = self._build_url(endpoint)

        headers: Dict[str, str] = {}
        if method.upper() == "POST":
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        response = await client.request(
            method=method.upper(),
            url=url,
            params=params,
            data=data,
            headers=headers,
        )

        # 解析响应 JSON
        try:
            result = response.json()
        except (ValueError, json.JSONDecodeError) as e:
            body = response.text[:300]
            raise SkBookAPIError(50000, f"响应不是合法 JSON", raw_response=body)

        # 校验业务状态码
        if not result.get("success", False):
            code = result.get("code", -1)
            msg = result.get("message", "")
            raise SkBookAPIError(code, msg)

        return result

    # ================================================================
    # 机器人 Open API 接口
    # 文档：https://skbook.sk26.cn/open/api/
    # ================================================================

    # --- 1. 获取社区频道列表 ---

    async def get_channels(self, community_id: str) -> List[Dict[str, Any]]:
        """获取社区频道列表

        GET /open/api/get_channels/
        仅返回机器人授权范围内的频道。
        需要机器人已添加到该社区。

        Args:
            community_id: 社区长ID（10位数字）

        Returns:
            [{ "channel_id": int, "name": str }, ...]
        """
        result = await self.request(
            "GET", "get_channels/",
            params={"community_id": community_id},
        )
        return result.get("data", {}).get("channels", [])

    # --- 2. 获取频道消息 ---

    async def get_messages(
        self,
        community_id: str,
        channel_id: int,
        limit: int = 20,
        message_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """获取频道消息

        GET /open/api/get_messages/
        默认返回频道最新消息；携带 message_id 时返回该消息之后的消息。
        机器人未开启「接收服务器所有消息」时，仅返回 @机器人 的消息。

        Args:
            community_id: 社区长ID
            channel_id: 频道ID
            limit: 获取数量（1-100，默认20）
            message_id: 定位消息ID

        Returns:
            {"messages": [...], "has_more": bool}
        """
        params: Dict[str, str] = {
            "community_id": community_id,
            "channel_id": str(channel_id),
            "limit": str(max(1, min(limit, 100))),
        }
        if message_id is not None:
            params["message_id"] = str(message_id)

        result = await self.request("GET", "get_messages/", params=params)
        return result.get("data", {})

    # --- 3. 获取所有社区消息 ---

    async def get_all_messages(
        self,
        limit: int = 20,
        message_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """获取机器人已加入的所有社区的消息

        GET /open/api/get_all_messages/
        需管理员在后台「机器人获取消息白名单」中添加该机器人ID。

        Args:
            limit: 获取数量（1-100，默认20）
            message_id: 定位消息ID

        Returns:
            {"messages": [...], "has_more": bool}
            消息额外含 community_id、channel_id
        """
        params: Dict[str, str] = {
            "limit": str(max(1, min(limit, 100))),
        }
        if message_id is not None:
            params["message_id"] = str(message_id)

        result = await self.request("GET", "get_all_messages/", params=params)
        return result.get("data", {})

    # --- 4. 发送社区频道消息 ---

    async def send_channel_message(
        self,
        community_id: str,
        channel_id: int,
        content: str,
    ) -> Dict[str, Any]:
        """发送社区频道消息

        POST /open/api/send_channel_message/
        需管理员在后台「机器人发送消息白名单」中添加该机器人ID。
        消息内容支持普通文本或 JSON 字符串（纯文本 / 卡片）。

        Args:
            community_id: 社区长ID
            channel_id: 频道ID
            content: 消息内容（普通文本或 JSON 字符串）
        """
        result = await self.request(
            "POST", "send_channel_message/",
            data={
                "community_id": community_id,
                "channel_id": str(channel_id),
                "content": content,
            },
        )
        return result.get("data", {})

    # --- 5. 发送私信消息 ---

    async def send_dm_message(
        self,
        community_id: str,
        user_id: int,
        content: str,
    ) -> Dict[str, Any]:
        """发送私信消息

        POST /open/api/send_dm_message/
        需管理员授权；目标用户必须是该社区成员。

        Args:
            community_id: 社区长ID（用于校验机器人与用户关系）
            user_id: 目标用户ID
            content: 消息内容（普通文本或 JSON 字符串）
        """
        result = await self.request(
            "POST", "send_dm_message/",
            data={
                "community_id": community_id,
                "user_id": str(user_id),
                "content": content,
            },
        )
        return result.get("data", {})

    # --- 6. 禁言用户 ---

    async def mute_user(
        self,
        community_id: str,
        user_id: int,
        duration: int,
        reason: str = "",
    ) -> Dict[str, Any]:
        """禁言用户

        POST /open/api/mute_user/
        需要机器人拥有「社区禁言」权限。

        Args:
            community_id: 社区长ID
            user_id: 用户ID
            duration: 禁言时长（秒）
            reason: 禁言原因（可选）
        """
        data: Dict[str, str] = {
            "community_id": community_id,
            "user_id": str(user_id),
            "duration": str(duration),
        }
        if reason:
            data["reason"] = reason

        result = await self.request("POST", "mute_user/", data=data)
        return result.get("data", {})

    # --- 7. 移除用户 ---

    async def kick_member(
        self,
        community_id: str,
        user_id: int,
        add_blacklist: bool = False,
        clear_messages: bool = False,
    ) -> Dict[str, Any]:
        """移除用户

        POST /open/api/kick_member/
        需要机器人拥有「移除和拉黑成员」权限。

        Args:
            community_id: 社区长ID
            user_id: 用户ID
            add_blacklist: 是否加入黑名单
            clear_messages: 是否清空该用户7日内所有消息
        """
        result = await self.request(
            "POST", "kick_member/",
            data={
                "community_id": community_id,
                "user_id": str(user_id),
                "add_blacklist": "true" if add_blacklist else "false",
                "clear_messages": "true" if clear_messages else "false",
            },
        )
        return result.get("data", {})


# ============================================================
# OAuth2.0 客户端
# 文档：https://skbook.sk26.cn/open/api/oauth2/
# ============================================================

class OAuth2Client:
    """SkBook OAuth2.0 客户端

    使用 CLIENT ID / CLIENT SECRET。
    经过完整 OAuth2.0 流程后可获取用户信息。
    """

    AUTH_URL = "https://skbook.sk26.cn/open/oauth_authorize.php"
    API_URL = "https://skbook.sk26.cn/open/api/oauth2/"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._client: Optional[httpx.AsyncClient] = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def get_authorize_url(self, state: str = "") -> str:
        """第一步：生成用户授权页面 URL

        用户确认后跳转回调地址，携带 code 和 state。
        用户拒绝时返回 error=access_denied。
        未登录用户先跳转登录页，登录后返回。
        """
        url = f"{self.AUTH_URL}?client_id={self.client_id}&response_type=code"
        if state:
            url += f"&state={state}"
        return url

    async def exchange_code(self, code: str, redirect_uri: str = "") -> Dict[str, Any]:
        """第二步：用授权码换取访问令牌

        POST /open/api/oauth2/?action=token
        授权码 5 分钟内有效，一次性使用。
        访问令牌 30 天有效（2592000 秒）。
        """
        client = await self._ensure_client()
        data: Dict[str, str] = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
        }
        if redirect_uri or self.redirect_uri:
            data["redirect_uri"] = redirect_uri or self.redirect_uri

        response = await client.post(
            self.API_URL,
            params={"action": "token"},
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        result = response.json()

        if not result.get("success", False):
            code_val = result.get("code", -1)
            msg = result.get("message", ERROR_CODE_MAP.get(code_val, f"OAuth2 错误 [{code_val}]"))
            raise SkBookAPIError(code_val, msg)

        return result.get("data", {})

    async def get_userinfo(self, access_token: str) -> Dict[str, Any]:
        """第三步：获取用户信息

        GET /open/api/oauth2/?action=userinfo
        令牌传递方式（三选一）：
        1. Authorization: Bearer <access_token>
        2. X-Access-Token: <access_token>
        3. ?access_token=<access_token>

        Returns:
            user_id, username, avatar, open_uid, phone
        """
        client = await self._ensure_client()
        response = await client.get(
            self.API_URL,
            params={"action": "userinfo"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        result = response.json()

        if not result.get("success", False):
            code_val = result.get("code", -1)
            msg = result.get("message", ERROR_CODE_MAP.get(code_val, f"OAuth2 错误 [{code_val}]"))
            raise SkBookAPIError(code_val, msg)

        return result.get("data", {})