"""鉴权模块 - 机器人 Token 与 OAuth2 管理"""

from typing import Optional, Dict
from ..base.logger import logger


class BotAuth:
    """机器人鉴权管理"""

    def __init__(self, token: str = ""):
        self._token = token

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, value: str) -> None:
        self._token = value

    def is_authenticated(self) -> bool:
        """检查是否已配置 Token"""
        return bool(self._token) and len(self._token) > 0


class OAuth2Auth:
    """OAuth2 鉴权管理器"""

    def __init__(self):
        self._client_id: str = ""
        self._client_secret: str = ""
        self._redirect_uri: str = ""
        self._access_token: Optional[str] = None
        self._user_info: Optional[Dict] = None

    def configure(self, client_id: str, client_secret: str,
                  redirect_uri: str = "") -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    @property
    def client_id(self) -> str:
        return self._client_id

    @property
    def is_configured(self) -> bool:
        return bool(self._client_id) and bool(self._client_secret)

    @property
    def access_token(self) -> Optional[str]:
        return self._access_token

    @access_token.setter
    def access_token(self, value: str) -> None:
        self._access_token = value

    @property
    def user_info(self) -> Optional[Dict]:
        return self._user_info

    @user_info.setter
    def user_info(self, value: Dict) -> None:
        self._user_info = value