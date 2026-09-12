"""PluginManager - 插件管理器，支持热重载"""

import os
import sys
import importlib.util
import asyncio
from typing import Dict, Optional, List, Callable, Any, Tuple
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
        """获取插件目录列表

        只扫描 plugins/ 根目录，其下的子目录 / .py 文件均作为独立插件加载。
        plugins/system/ 作为 system 子目录会自动发现，无需额外添加。
        """
        if not self._plugin_dirs:
            base_dir = Path.cwd() / "plugins"
            if base_dir.exists():
                self._plugin_dirs.append(base_dir)
        return self._plugin_dirs

    async def load_plugins(self) -> None:
        """加载所有插件"""
        plugin_dirs = self.get_plugin_dirs()
        for plugin_dir in plugin_dirs:
            await self._load_plugins_from_dir(plugin_dir)

    async def _load_plugins_from_dir(self, plugin_dir: Path) -> None:
        """从目录加载插件

        - 子目录含 main.py → 以目录名作为插件名
        - 独立 .py 文件（非 __init__） → 以文件名（不含后缀）作为插件名
        """
        if not plugin_dir.exists():
            return

        for item in sorted(plugin_dir.iterdir()):
            if item.is_dir() and (item / "main.py").exists():
                await self._load_plugin(item.name, str(item / "main.py"))
            elif item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
                await self._load_plugin(item.stem, str(item))

    async def _load_plugin(self, name: str, file_path: str) -> None:
        """加载单个插件"""
        if name in self._plugins:
            logger.debug("插件 [%s] 已加载，跳过", name)
            return

        try:
            # 将插件所在目录加入 sys.path（支持相对导入）
            file_path_obj = Path(file_path)
            plugin_dir = str(file_path_obj.parent)
            if plugin_dir not in sys.path:
                sys.path.insert(0, plugin_dir)

            # 动态导入模块
            spec = importlib.util.spec_from_file_location(f"plugin_{name}", file_path)
            if not spec or not spec.loader:
                logger.error("插件 [%s] 加载失败: 无法创建 spec", name)
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找所有顶层函数 / 类上的处理器
            handlers: List[Tuple[Callable, dict]] = []
            plugin_instance = None

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if not callable(attr):
                    continue

                # 检查是否是被装饰的函数（有 _skbook_handlers）
                if hasattr(attr, "_skbook_handlers"):
                    for handler_meta in getattr(attr, "_skbook_handlers"):
                        handlers.append((attr, handler_meta))

                # 检查是否是插件类（有 _skbook_handlers 类属性或 _is_skbook_plugin）
                if isinstance(attr, type) and hasattr(attr, "_skbook_handlers"):
                    try:
                        instance = attr()
                        instance.ctx = PluginContext(name)
                        plugin_instance = instance
                        # 从类属性中解析类方法处理器
                        for handler_meta in getattr(attr, "_skbook_handlers", []):
                            handler_func = getattr(instance, handler_meta.get("name", ""), None)
                            if handler_func:
                                handlers.append((handler_func, handler_meta))
                    except Exception as e:
                        logger.debug("插件 [%s] 类实例化失败: %s", name, e)

                if isinstance(attr, type) and hasattr(attr, "_is_skbook_plugin"):
                    try:
                        instance = attr()
                        instance.ctx = PluginContext(name)
                        plugin_instance = instance
                    except Exception as e:
                        logger.debug("插件 [%s] 类实例化失败: %s", name, e)

            if not handlers:
                logger.warning("插件 [%s] 未找到有效的命令或消息处理器", name)
                return

            pi = PluginInfo(name, module, plugin_instance, handlers)
            self._plugins[name] = pi

            # 调用插件 on_load 生命周期
            if plugin_instance and hasattr(plugin_instance, "on_load"):
                try:
                    await plugin_instance.on_load()
                except Exception as e:
                    logger.error("插件 [%s] on_load 错误: %s", name, e)

            logger.info("插件 [%s] 已加载 (%d 个处理器)",
                        name, len(handlers))

        except Exception as e:
            logger.error("插件 [%s] 加载失败: %s", name, e, exc_info=True)

    async def unload_plugin(self, name: str) -> bool:
        """卸载插件"""
        pi = self._plugins.pop(name, None)
        if not pi:
            return False

        try:
            if pi.instance and hasattr(pi.instance, "on_unload"):
                await pi.instance.on_unload()
            logger.info("插件 [%s] 已卸载", name)
            return True
        except Exception as e:
            logger.error("插件 [%s] 卸载失败: %s", name, e)
            return False

    async def reload_plugin(self, name: str) -> bool:
        """重载插件"""
        await self.unload_plugin(name)

        # 清除模块缓存
        for key in list(sys.modules.keys()):
            if key.startswith(f"plugin_{name}"):
                del sys.modules[key]

        # 重新搜索并加载
        for plugin_dir in self.get_plugin_dirs():
            # 检查独立文件: plugins/<name>.py
            main_file = plugin_dir / f"{name}.py"
            if main_file.exists():
                await self._load_plugin(name, str(main_file))
                return name in self._plugins

            # 检查目录: plugins/<name>/main.py
            dir_main = plugin_dir / name / "main.py"
            if dir_main.exists():
                await self._load_plugin(name, str(dir_main))
                return name in self._plugins

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
                        # 消息模式匹配
                        pattern = meta.get("pattern")
                        if pattern and pattern.search(event.content):
                            await handler_func(event)
                        elif meta.get("matcher") and meta["matcher"](event):
                            await handler_func(event)

                    elif handler_type == "event":
                        # 事件匹配（预留）
                        pass

                except Exception as e:
                    logger.error("插件 [%s] 处理器错误: %s", pi.name, e)

    def get_plugin_list(self) -> List[dict]:
        """获取插件列表（用于 Web 面板）"""
        result = []
        for name, pi in self._plugins.items():
            handler_list = []
            for handler_func, meta in pi.handlers:
                item: dict = {
                    "type": meta.get("type", "message"),
                }
                if meta.get("type") == "command":
                    item["command"] = meta.get("name", "")
                    item["aliases"] = meta.get("aliases", [])
                elif meta.get("type") == "message":
                    pattern = meta.get("pattern")
                    item["pattern"] = (
                        str(pattern.pattern) if hasattr(pattern, "pattern")
                        else str(pattern) if pattern else ""
                    )
                handler_list.append(item)

            result.append({
                "name": name,
                "handlers": len(pi.handlers),
                "handler_list": handler_list,
                "has_instance": pi.instance is not None,
            })
        return result