"""SkBook 开放平台 API 客户端"""

import asyncio
import httpx
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

from ..base.logger import logger

API_BASE_URL = "https://skbook.sk26.cn/open/api/"


class SkBookAPIError(Exception):
    """SkBook API 调用异常"""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


# 错误码映射
ERROR_CODES = {
    40001: "参数缺失或格式错误",
    40002: "社区不存在",
    40003: "频道不存在",
    40004: "用户不存在",
    40101: "TOKEN / 凭证缺失或无效",
    40102: "访问令牌无效",
    40103: "访问令牌已过期",
    40104: "令牌对应的用户不存在",
    40201: "OAuth2 授权码无效",
    40202: "OAuth2 授权码已被使用",
    40203: "OAuth2 授权码已过期",
    40204: "redirect_uri 与授权/配置不一致",
    40301: "机器人未添加到该社区",
    40302: "无对应社区权限 / 应用未开启OAuth2",
    40303: "机器人未获得发送消息授权",
    40304: "频道不在机器人的授权范围内",
    40305: "机器人未获得获取消息授权",
    40400: "未知接口或请求方式",
    50000: "服务器内部错误",
}


class SkBookAPIClient:
    """SkBook 开放平台 API 客户端

    按 API 文档封装所有 Open API 接口。
    token 始终通过 URL 查询参数传递。
    """

    def __init__(self, token: str = ""):
        self._token = token
        self._base_url = API_BASE_URL
        self._client: Optional[httpx.AsyncClient] = None
        self._max_retries = 3
        self._retry_delay = 1.0  # 秒

    async def ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                follow_redirects=False,
            )
        return self._client

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, value: str) -> None:
        self._token = value

    def _build_url(self, endpoint: str) -> str:
        """构建带 token 的请求 URL

        API 文档规定：token 通过 URL 查询参数传递。
        GET / POST 均支持 ?token=<TOKEN>
        """
        url = urljoin(self._base_url, endpoint)
        if self._token:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}token={self._token}"
        return url

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        data: Dict = None,
    ) -> Dict:
        """发送 HTTP 请求，带重试"""
        last_error = None

        for attempt in range(1, self._max_retries + 1):
            try:
                return await self._do_request(method, endpoint, params, data)
            except SkBookAPIError:
                # API 返回的业务错误直接抛出，不重试
                raise
            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as e:
                last_error = e
                if attempt < self._max_retries:
                    wait = self._retry_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"API 请求 [{endpoint}] 第 {attempt} 次失败: {e}，"
                        f"{wait:.1f}s 后重试..."
                    )
                    await asyncio.sleep(wait)
                else:
                    logger.error(
                        f"API 请求 [{endpoint}] 重试 {self._max_retries} 次均失败: {e}"
                    )
            except Exception as e:
                last_error = e
                logger.error(f"API 请求 [{endpoint}] 未知错误: {e}")
                raise SkBookAPIError(50000, f"请求异常: {e}")

        raise SkBookAPIError(50000, f"连接失败: {last_error}")

    async def _do_request(
        self, method: str, endpoint: str,
        params: Dict = None, data: Dict = None,
    ) -> Dict:
        """执行单次 HTTP 请求"""
        client = await self.ensure_client()
        url = self._build_url(endpoint)

        # Content-Type: 仅 POST 请求设置 form-urlencoded
        headers = {}
        if method.upper() == "POST":
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        response = await client.request(
            method=method.upper(),
            url=url,
            params=params,
            data=data,
            headers=headers,
        )

        try:
            result = response.json()
        except ValueError as e:
            body_preview = response.text[:200]
            raise SkBookAPIError(
                50000,
                f"响应不是合法 JSON: {e} | 响应内容: {body_preview}"
            )

        if not result.get("success", False):
            code = result.get("code", -1)
            msg = result.get("message", ERROR_CODES.get(code, "未知错误"))
            raise SkBookAPIError(code, msg)

        return result

    # ---- Open API 接口实现 ----

    async def get_channels(self, community_id: str) -> List[Dict]:
        """获取社区频道列表

        GET /open/api/get_channels/
        需要机器人已添加到该社区。
        """
        result = await self._request(
            "GET", "get_channels/",
            params={"community_id": community_id},
        )
        return result.get("data", {}).get("channels", [])

    async def get_messages(
        self, community_id: str, channel_id: int,
        limit: int = 20, message_id: int = None,
    ) -> Dict:
        """获取频道消息

        GET /open/api/get_messages/
        默认返回最新消息；携带 message_id 返回该消息之后的消息。
        """
        params = {
            "community_id": community_id,
            "channel_id": str(channel_id),
            "limit": str(min(limit, 100)),
        }
        if message_id is not None:
            params["message_id"] = str(message_id)

        result = await self._request("GET", "get_messages/", params=params)
        return result.get("data", {})

    async def get_all_messages(self, limit: int = 20, message_id: int = None) -> Dict:
        """获取所有社区的消息

        GET /open/api/get_all_messages/
        需要联系管理员授权（后台添加机器人ID到白名单）。
        """
        params = {"limit": str(min(limit, 100))}
        if message_id is not None:
            params["message_id"] = str(message_id)

        result = await self._request("GET", "get_all_messages/", params=params)
        return result.get("data", {})

    async def send_channel_message(
        self, community_id: str, channel_id: int, content: str,
    ) -> Dict:
        """发送社区频道消息

        POST /open/api/send_channel_message/
        需要管理员授权 + 机器人有「查看与发言权限」。
        content 支持 JSON 字符串（纯文本 / 卡片消息）。
        """
        result = await self._request(
            "POST", "send_channel_message/",
            data={
                "community_id": community_id,
                "channel_id": str(channel_id),
                "content": content,
            },
        )
        return result.get("data", {})

    async def send_dm_message(
        self, community_id: str, user_id: int, content: str,
    ) -> Dict:
        """发送私信消息

        POST /open/api/send_dm_message/
        需要管理员授权；目标用户必须是该社区成员。
        """
        result = await self._request(
            "POST", "send_dm_message/",
            data={
                "community_id": community_id,
                "user_id": str(user_id),
                "content": content,
            },
        )
        return result.get("data", {})

    async def mute_user(
        self, community_id: str, user_id: int,
        duration: int, reason: str = "",
    ) -> Dict:
        """禁言用户

        POST /open/api/mute_user/
        需要机器人有「社区禁言」权限。
        """
        data = {
            "community_id": community_id,
            "user_id": str(user_id),
            "duration": str(duration),
        }
        if reason:
            data["reason"] = reason
        result = await self._request("POST", "mute_user/", data=data)
        return result.get("data", {})

    async def kick_member(
        self, community_id: str, user_id: int,
        add_blacklist: bool = False, clear_messages: bool = False,
    ) -> Dict:
        """移除用户

        POST /open/api/kick_member/
        需要机器人有「移除和拉黑成员」权限。
        """
        result = await self._request(
            "POST", "kick_member/",
            data={
                "community_id": community_id,
                "user_id": str(user_id),
                "add_blacklist": "true" if add_blacklist else "false",
                "clear_messages": "true" if clear_messages else "false",
            },
        )
        return result.get("data", {})

    async def close(self) -> None:
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None


class OAuth2Client:
    """SkBook OAuth2.0 客户端

    使用 CLIENT ID / CLIENT SECRET。
    经过完整 OAuth2.0 流程后可获取用户信息。
    """

    AUTH_URL = "https://skbook.sk26.cn/open/oauth_authorize.php"
    API_URL = "https://skbook.sk26.cn/open/api/oauth2/"

    # 错误码映射
    ERROR_CODES = {
        40101: "TOKEN / 凭证缺失或无效",
        40102: "访问令牌无效",
        40103: "访问令牌已过期",
        40104: "令牌对应的用户不存在",
        40201: "OAuth2 授权码无效",
        40202: "OAuth2 授权码已被使用",
        40203: "OAuth2 授权码已过期",
        40204: "redirect_uri 与授权/配置不一致",
    }

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = ""):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._client: Optional[httpx.AsyncClient] = None

    async def ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0, follow_redirects=False)
        return self._client

    def get_authorize_url(self, state: str = "") -> str:
        """第一步：生成用户授权页面 URL

        用户确认后跳转回回调地址，携带 code 和 state。
        """
        url = f"{self.AUTH_URL}?client_id={self.client_id}&response_type=code"
        if state:
            url += f"&state={state}"
        return url

    async def exchange_code(self, code: str, redirect_uri: str = "") -> Dict:
        """第二步：用授权码换取访问令牌

        POST /open/api/oauth2/?action=token
        """
        client = await self.ensure_client()
        data = {
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
            msg = result.get(
                "message",
                self.ERROR_CODES.get(code_val, f"OAuth2 错误 [{code_val}]"),
            )
            raise SkBookAPIError(code_val, msg)

        return result.get("data", {})

    async def get_userinfo(self, access_token: str) -> Dict:
        """第三步：获取用户信息

        GET /open/api/oauth2/?action=userinfo
        令牌传递：Authorization: Bearer <token> 或 X-Access-Token: <token>
        """
        client = await self.ensure_client()
        response = await client.get(
            self.API_URL,
            params={"action": "userinfo"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        result = response.json()

        if not result.get("success", False):
            code_val = result.get("code", -1)
            msg = result.get(
                "message",
                self.ERROR_CODES.get(code_val, f"OAuth2 错误 [{code_val}]"),
            )
            raise SkBookAPIError(code_val, msg)

        return result.get("data", {})

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None