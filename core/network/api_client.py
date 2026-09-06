"""SkBook 开放平台 API 客户端"""

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


class SkBookAPIClient:
    """SkBook 开放平台 API 客户端"""

    def __init__(self, token: str = ""):
        self._token = token
        self._base_url = API_BASE_URL
        self._client: Optional[httpx.AsyncClient] = None

    async def ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, value: str) -> None:
        self._token = value

    def _build_url(self, endpoint: str) -> str:
        """构建带 token 的 URL"""
        url = urljoin(self._base_url, endpoint)
        if self._token:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}token={self._token}"
        return url

    async def _request(self, method: str, endpoint: str,
                       params: Dict = None, data: Dict = None,
                       headers: Dict = None) -> Dict:
        """发送 HTTP 请求"""
        client = await self.ensure_client()
        url = self._build_url(endpoint)

        request_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if headers:
            request_headers.update(headers)

        try:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=request_headers
            )
            result = response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP 请求失败: {e}")
            raise SkBookAPIError(50000, f"网络错误: {e}")
        except ValueError as e:
            logger.error(f"JSON 解析失败: {e}")
            raise SkBookAPIError(50000, f"响应解析错误: {e}")

        if not result.get("success", False):
            code = result.get("code", -1)
            msg = result.get("message", "未知错误")
            raise SkBookAPIError(code, msg)

        return result

    async def get_channels(self, community_id: str) -> List[Dict]:
        """获取社区频道列表"""
        result = await self._request("GET", "get_channels/",
                                     params={"community_id": community_id})
        return result.get("data", {}).get("channels", [])

    async def get_messages(self, community_id: str, channel_id: int,
                           limit: int = 20, message_id: int = None) -> Dict:
        """获取频道消息"""
        params = {
            "community_id": community_id,
            "channel_id": channel_id,
            "limit": min(limit, 100),
        }
        if message_id:
            params["message_id"] = message_id
        result = await self._request("GET", "get_messages/", params=params)
        return result.get("data", {})

    async def get_all_messages(self, limit: int = 20,
                               message_id: int = None) -> Dict:
        """获取所有社区的消息"""
        params = {"limit": min(limit, 100)}
        if message_id:
            params["message_id"] = message_id
        result = await self._request("GET", "get_all_messages/", params=params)
        return result.get("data", {})

    async def send_channel_message(self, community_id: str, channel_id: int,
                                   content: str) -> Dict:
        """发送频道消息"""
        result = await self._request("POST", "send_channel_message/", data={
            "community_id": community_id,
            "channel_id": str(channel_id),
            "content": content,
        })
        return result.get("data", {})

    async def send_dm_message(self, community_id: str, user_id: int,
                              content: str) -> Dict:
        """发送私信消息"""
        result = await self._request("POST", "send_dm_message/", data={
            "community_id": community_id,
            "user_id": str(user_id),
            "content": content,
        })
        return result.get("data", {})

    async def mute_user(self, community_id: str, user_id: int,
                        duration: int, reason: str = "") -> Dict:
        """禁言用户"""
        data = {
            "community_id": community_id,
            "user_id": str(user_id),
            "duration": str(duration),
        }
        if reason:
            data["reason"] = reason
        result = await self._request("POST", "mute_user/", data=data)
        return result.get("data", {})

    async def kick_member(self, community_id: str, user_id: int,
                          add_blacklist: bool = False,
                          clear_messages: bool = False) -> Dict:
        """移除用户"""
        data = {
            "community_id": community_id,
            "user_id": str(user_id),
            "add_blacklist": "true" if add_blacklist else "false",
            "clear_messages": "true" if clear_messages else "false",
        }
        result = await self._request("POST", "kick_member/", data=data)
        return result.get("data", {})

    async def close(self) -> None:
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None


class OAuth2Client:
    """SkBook OAuth2.0 客户端"""

    AUTH_URL = "https://skbook.sk26.cn/open/oauth_authorize.php"
    TOKEN_URL = "https://skbook.sk26.cn/open/api/oauth2/"
    USERINFO_URL = "https://skbook.sk26.cn/open/api/oauth2/"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = ""):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._client: Optional[httpx.AsyncClient] = None

    def get_authorize_url(self, state: str = "") -> str:
        """获取 OAuth2 授权页面 URL"""
        url = f"{self.AUTH_URL}?client_id={self.client_id}&response_type=code"
        if state:
            url += f"&state={state}"
        return url

    async def exchange_code(self, code: str, redirect_uri: str = "") -> Dict:
        """用授权码换取访问令牌"""
        client = httpx.AsyncClient(timeout=30.0)
        try:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "authorization_code",
                "code": code,
            }
            if redirect_uri or self.redirect_uri:
                data["redirect_uri"] = redirect_uri or self.redirect_uri

            response = await client.post(self.TOKEN_URL, params={"action": "token"}, data=data)
            result = response.json()
        finally:
            await client.aclose()

        if not result.get("success", False):
            code = result.get("code", -1)
            msg = result.get("message", "未知错误")
            raise SkBookAPIError(code, msg)

        return result.get("data", {})

    async def get_userinfo(self, access_token: str) -> Dict:
        """获取用户信息"""
        client = httpx.AsyncClient(timeout=30.0)
        try:
            response = await client.get(
                self.USERINFO_URL,
                params={"action": "userinfo"},
                headers={"Authorization": f"Bearer {access_token}"}
            )
            result = response.json()
        finally:
            await client.aclose()

        if not result.get("success", False):
            code = result.get("code", -1)
            msg = result.get("message", "未知错误")
            raise SkBookAPIError(code, msg)

        return result.get("data", {})