"""消息解析器"""

import json
from typing import Optional, Dict, Any
from ..base.logger import logger


class MessageParser:
    """消息内容解析器"""

    @staticmethod
    def parse_text(content: str) -> str:
        """解析纯文本（处理格式标记）"""
        # 处理 **加粗**
        # 原样返回，渲染由客户端处理
        return content

    @staticmethod
    def parse_json(content: str) -> Optional[Dict[str, Any]]:
        """尝试解析 JSON 消息"""
        if not content.startswith("{"):
            return None
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def build_text(text: str) -> str:
        """构建纯文本消息 JSON"""
        return json.dumps({"type": "text", "text": text}, ensure_ascii=False)

    @staticmethod
    def build_card(card_data: dict) -> str:
        """构建卡片消息 JSON"""
        card_data["type"] = "card"
        return json.dumps(card_data, ensure_ascii=False)