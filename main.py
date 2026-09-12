#!/usr/bin/env python3
"""SkBookBot - SkBook 开放平台机器人框架"""

import asyncio
import sys
import os
from pathlib import Path

# 将项目根目录加入 sys.path
sys.path.insert(0, str(Path(__file__).parent))

from core.base.config import config
from core.base.logger import logger
from core.application import Application


async def main():
    """主入口"""
    print("""
    ╔══════════════════════════════════════╗
    ║         SkBookBot v1.0.0             ║
    ║   SkBook 开放平台机器人框架           ║
    ╚══════════════════════════════════════╝
    """)

    # 加载框架配置
    settings_path = Path(__file__).parent / "config" / "settings.yaml"
    if settings_path.exists():
        config.load_settings(str(settings_path))
        logger.info("已加载 settings.yaml")
    else:
        # 使用默认配置（首次运行自动创建）
        config.set("server.host", "0.0.0.0")
        config.set("server.port", 5200)
        config.set("web.admin_password", "admin123")
        config.set("logging.level", "INFO")
        config.set("database.path", "./data/skbookbot.db")
        logger.info("使用默认配置")

    # 加载机器人配置
    bot_path = Path(__file__).parent / "config" / "bot.yaml"
    if bot_path.exists():
        config.load_bot_config(str(bot_path))
        logger.info("已加载 bot.yaml")

    # 初始化日志
    log_level = config.get("logging.level", "INFO")
    log_file = config.get("logging.file", "")
    logger.setup(log_level, log_file)

    # 创建应用
    app = Application()
    await app.initialize()

    # 运行
    try:
        await app.start()
    except KeyboardInterrupt:
        pass
    finally:
        await app.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        sys.exit(1)