"""PluginManager - 插件管理器，支持热重载"""

import os
import sys
import importlib
import asyncio
from typing import Dict, Optional, List, Callable, Any
from pathlib import Path
from ..base.logger import logger
from ..base.config import config
from .context import PluginContext
from ..message.event import MessageEvent


class PluginInfo:
    """插件信息"""

    def __init__(self, name: str, module, instance, handlers: list):
        self.name = name
        self.module = module
        self.instance = instance
        self.handlers = handlers  # [(handler_func, metadata), ...]


class PluginManager:
    """插件管理器"""

    def __init__(self):
        self._plugins: Dict[str, PluginInfo] = {}
        self._plugin_dirs: List[Path] = []

    @property
    def plugins(self) -> Dict[str, PluginInfo]:
        return self._plugins

    def get_plugin_dirs(self) -> List[Path]:
        """获取插件目录列表"""
        if not self._plugin_dirs:
            # 默认插件目录
            base_dir = Path.cwd() / "plugins"
            if base_dir.exists():
                self._plugin_dirs.append(base_dir)

            # 系统插件目录
            sys_dir = base_dir / "system"
            if sys_dir.exists():
                self._plugin_dirs.append(sys_dir)
        return self._plugin_dirs

    async def load_plugins(self) -> None:
        """加载所有插件"""
        plugin_dirs = self.get_plugin_dirs()
        for plugin_dir in plugin_dirs:
            await self._load_plugins_from_dir(plugin_dir)

    async def _load_plugins_from_dir(self, plugin_dir: Path) -> None:
        """从目录加载插件"""
        if not plugin_dir.exists():
            return

        for item in plugin_dir.iterdir():
            if item.is_dir() and (item / "main.py").exists():
                await self._load_plugin(item.name, str(item / "main.py"))
            elif item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
                await self._load_plugin(item.stem, str(item))

    async def _load_plugin(self, name: str, file_path: str) -> None:
        """加载单个插件"""
        if name in self._plugins:
            logger.debug(f"插件 [{name}] 已加载，跳过")
            return

        try:
            # 将插件目录加入 sys.path
            file_path_obj = Path(file_path)
            plugin_dir = str(file_path_obj.parent)
            if plugin_dir not in sys.path:
                sys.path.insert(0, plugin_dir)

            # 动态导入
            spec = importlib.util.spec_from_file_location(f"plugin_{name}", file_path)
            if not spec or not spec.loader:
                logger.error(f"插件 [{name}] 加载失败: 无法创建 spec")
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找插件实例
            plugin_instance = None
            handlers = []

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type):
                    # 检查是否是插件类（有 _skbook_handlers 或继承 PluginBase）
                    if hasattr(attr, "_skbook_handlers"):
                        instance = attr()
                        instance.ctx = PluginContext(name)
                        plugin_instance = instance
                        for handler_meta in getattr(attr, "_skbook_handlers", []):
                            handler_func = getattr(instance, handler_meta.get("name", ""), None)
                            if handler_func:
                                handlers.append((handler_func, handler_meta))
                    elif hasattr(attr, "_is_skbook_plugin"):
                        instance = attr()
                        instance.ctx = PluginContext(name)
                        plugin_instance = instance

            if plugin_instance is None:
                # 查找所有顶层函数 handler
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if callable(attr) and hasattr(attr, "_skbook_handlers"):
                        for handler_meta in getattr(attr, "_skbook_handlers"):
                            handlers.append((attr, handler_meta))

            if not plugin_instance and not handlers:
                logger.warning(f"插件 [{name}] 未找到有效的插件类或处理器")
                return

            pi = PluginInfo(name, module, plugin_instance, handlers)
            self._plugins[name] = pi

            # 调用插件 on_load
            if plugin_instance and hasattr(plugin_instance, "on_load"):
                await plugin_instance.on_load()

            logger.info(f"插件 [{name}] 已加载 ({len(handlers)} 个处理器)")

        except Exception as e:
            logger.error(f"插件 [{name}] 加载失败: {e}", exc_info=True)

    async def unload_plugin(self, name: str) -> bool:
        """卸载插件"""
        pi = self._plugins.pop(name, None)
        if not pi:
            return False

        try:
            if pi.instance and hasattr(pi.instance, "on_unload"):
                await pi.instance.on_unload()
            logger.info(f"插件 [{name}] 已卸载")
            return True
        except Exception as e:
            logger.error(f"插件 [{name}] 卸载失败: {e}")
            return False

    async def reload_plugin(self, name: str) -> bool:
        """重载插件"""
        await self.unload_plugin(name)
        # 移除模块缓存
        for key in list(sys.modules.keys()):
            if key.startswith(f"plugin_{name}"):
                del sys.modules[key]
        # 重新加载
        for plugin_dir in self.get_plugin_dirs():
            main_file = plugin_dir / f"{name}.py"
            dir_main = plugin_dir / name / "main.py"
            if main_file.exists():
                await self._load_plugin(name, str(main_file))
                return True
            elif dir_main.exists():
                await self._load_plugin(name, str(dir_main))
                return True
        return False

    async def dispatch(self, event: MessageEvent) -> None:
        """分发消息事件到插件"""
        for pi in list(self._plugins.values()):
            for handler_func, meta in pi.handlers:
                try:
                    handler_type = meta.get("type", "message")

                    if handler_type == "command":
                        # 命令匹配
                        cmd_name = meta.get("name", "")
                        aliases = meta.get("aliases", [])
                        if event.is_command and (
                            event.command_name == cmd_name or
                            event.command_name in aliases
                        ):
                            await handler_func(event)

                    elif handler_type == "message":
                        # 消息匹配
                        pattern = meta.get("pattern")
                        if pattern and pattern.search(event.content):
                            await handler_func(event)
                        elif meta.get("matcher") and meta["matcher"](event):
                            await handler_func(event)

                    elif handler_type == "event":
                        # 事件匹配（暂未实现具体事件类型）
                        pass

                except Exception as e:
                    logger.error(f"插件处理器错误 ({pi.name}): {e}")

    def get_plugin_list(self) -> List[dict]:
        """获取插件列表（用于 Web 面板）"""
        result = []
        for name, pi in self._plugins.items():
            result.append({
                "name": name,
                "handlers": len(pi.handlers),
                "has_instance": pi.instance is not None,
            })
        return result