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

    # 加载环境变量
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        config.load_env(str(env_path))
        logger.info("已加载 .env 文件")

    # 加载框架配置
    settings_path = Path(__file__).parent / "config" / "settings.yaml"
    if settings_path.exists():
        config.load_settings(str(settings_path))
        logger.info("已加载 settings.yaml")
        # 环境变量可以覆盖部分配置（如端口、日志级别），但不覆盖密码
        config.set("server.host", os.environ.get("WEB_HOST", config.get("server.host", "0.0.0.0")))
        config.set("server.port", int(os.environ.get("WEB_PORT", str(config.get("server.port", 5200)))))
        config.set("logging.level", os.environ.get("LOG_LEVEL", config.get("logging.level", "INFO")))
    else:
        # 使用默认配置
        config.set("server.host", os.environ.get("WEB_HOST", "0.0.0.0"))
        config.set("server.port", int(os.environ.get("WEB_PORT", "5200")))
        config.set("web.admin_password", os.environ.get("WEB_ADMIN_PASSWORD", "admin123"))
        config.set("logging.level", os.environ.get("LOG_LEVEL", "INFO"))
        config.set("database.path", os.environ.get("DATA_DIR", "./data") + "/skbookbot.db")
        config.set("oauth2.client_id", os.environ.get("OAUTH2_CLIENT_ID", ""))
        config.set("oauth2.client_secret", os.environ.get("OAUTH2_CLIENT_SECRET", ""))
        config.set("oauth2.redirect_uri", os.environ.get("OAUTH2_REDIRECT_URI", ""))
        logger.info("使用环境变量配置")

    # 加载机器人配置
    bot_path = Path(__file__).parent / "config" / "bot.yaml"
    if bot_path.exists():
        config.load_bot_config(str(bot_path))
        logger.info("已加载 bot.yaml")
    else:
        # 尝试从环境变量加载默认机器人
        bot_token = os.environ.get("BOT_TOKEN", "")
        if bot_token:
            config.set("bots", [{
                "name": "default",
                "token": bot_token,
                "enabled": True,
                "communities": [],
                "poll_interval": 3,
                "command_prefix": "/",
            }])
            logger.info("从环境变量加载默认机器人")

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