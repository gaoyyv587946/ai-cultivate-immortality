"""游戏模块注册器
所有子模块在此统一注册，便于后期扩展
"""

from . import attributes
from . import exam
from . import minigame


# 模块注册表：记录所有已注册的模块信息
_registry: dict[str, dict] = {}


def register_module(name: str, description: str, version: str = "1.0"):
    """注册一个模块到系统中"""
    _registry[name] = {
        "name": name,
        "description": description,
        "version": version,
    }


def get_registered_modules() -> list[dict]:
    """获取所有已注册的模块列表"""
    return list(_registry.values())


# 自动注册内置模块
register_module("attributes", "四维属性系统（智力/体力/力量/精神）")
register_module("exam", "模拟考试系统（AI出题+评分）")
register_module("minigame", "小游戏系统（猜数字/灵兽捕捉）")
