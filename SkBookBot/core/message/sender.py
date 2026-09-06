"""消息发送器"""

from typing import Optional
from ..base.logger import logger
from ..network.api_client import SkBookAPIClient


class MessageSender:
    """SkBook 消息发送器"""

    def __init__(self, api: SkBookAPIClient):
        self._api = api

    async def send_channel(self, community_id: str, channel_id: int,
                           content: str) -> bool:
        """发送频道消息"""
        try:
            await self._api.send_channel_message(community_id, channel_id, content)
            return True
        except Exception as e:
            logger.error(f"发送频道消息失败: {e}")
            return False

    async def send_dm(self, community_id: str, user_id: int,
                      content: str) -> bool:
        """发送私信"""
        try:
            await self._api.send_dm_message(community_id, user_id, content)
            return True
        except Exception as e:
            logger.error(f"发送私信失败: {e}")
            return False

    async def send_card(self, community_id: str, channel_id: int,
                        card_json: str) -> bool:
        """发送卡片消息"""
        return await self.send_channel(community_id, channel_id, card_json)