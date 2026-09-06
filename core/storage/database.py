"""数据库管理 - 基于 aiosqlite"""

import aiosqlite
from typing import Optional, Dict, Any, List
from pathlib import Path
from ..base.logger import logger


class Database:
    """异步 SQLite 数据库管理器"""

    def __init__(self):
        self._conn: Optional[aiosqlite.Connection] = None
        self._db_path: Optional[str] = None

    async def initialize(self, db_path: str) -> None:
        """初始化数据库"""
        self._db_path = db_path
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = await aiosqlite.connect(db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")

        await self._create_tables()
        logger.info(f"数据库已初始化: {db_path}")

    async def _create_tables(self) -> None:
        """创建表结构"""
        # 消息记录
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                community_id TEXT NOT NULL,
                channel_id INTEGER NOT NULL,
                content TEXT,
                sender_id INTEGER,
                created_at TEXT,
                bot_name TEXT,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 机器人配置
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS bot_configs (
                name TEXT PRIMARY KEY,
                token TEXT NOT NULL,
                config TEXT DEFAULT '{}',
                enabled INTEGER DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 会话存储
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)

        # 插件数据
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS plugin_data (
                plugin_name TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                PRIMARY KEY (plugin_name, key)
            )
        """)

        await self._conn.commit()

    async def execute(self, sql: str, params: tuple = ()) -> None:
        """执行 SQL"""
        if not self._conn:
            raise RuntimeError("数据库未初始化")
        await self._conn.execute(sql, params)
        await self._conn.commit()

    async def fetch_one(self, sql: str, params: tuple = ()) -> Optional[Dict]:
        """查询单行"""
        if not self._conn:
            raise RuntimeError("数据库未初始化")
        cursor = await self._conn.execute(sql, params)
        row = await cursor.fetchone()
        await cursor.close()
        if row:
            return dict(row)
        return None

    async def fetch_all(self, sql: str, params: tuple = ()) -> List[Dict]:
        """查询多行"""
        if not self._conn:
            raise RuntimeError("数据库未初始化")
        cursor = await self._conn.execute(sql, params)
        rows = await cursor.fetchall()
        await cursor.close()
        return [dict(row) for row in rows]

    async def insert_message(self, msg: Dict) -> None:
        """插入消息记录"""
        await self.execute("""
            INSERT OR IGNORE INTO messages 
            (message_id, community_id, channel_id, content, sender_id, created_at, bot_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            msg["message_id"], msg.get("community_id", ""),
            msg.get("channel_id", 0), msg.get("content", ""),
            msg.get("sender_id", 0), msg.get("created_at", ""),
            msg.get("bot_name", ""),
        ))

    async def close(self) -> None:
        """关闭数据库"""
        if self._conn:
            await self._conn.close()
            self._conn = None
            logger.info("数据库已关闭")


# 全局数据库实例
db = Database()