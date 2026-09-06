"""应用上下文 - 全局单例持有者"""

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..application import Application


class AppContext:
    """应用上下文，持有全局 Application 实例"""

    _instance: Optional["AppContext"] = None
    _app: Optional["Application"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def app(self) -> Optional["Application"]:
        return self._app

    @app.setter
    def app(self, value: "Application") -> None:
        self._app = value

    @classmethod
    def get_app(cls) -> Optional["Application"]:
        """获取全局 Application 实例"""
        instance = cls()
        return instance._app


# 快捷函数
def get_app():
    return AppContext.get_app()