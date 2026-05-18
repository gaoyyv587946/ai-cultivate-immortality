"""四维属性系统模块
管理智力(intelligence)、体力(stamina)、力量(strength)、精神(spirit)四种属性
"""

import random

# 属性名称常量
ATTR_KEYS = ["intelligence", "stamina", "strength", "spirit"]

ATTR_LABELS = {
    "intelligence": "智力",
    "stamina": "体力",
    "strength": "力量",
    "spirit": "精神",
}

ATTR_DEFAULT = 50
ATTR_MIN = 0
ATTR_MAX = 100


def clamp(value: int) -> int:
    """将属性值限制在合法范围内"""
    return max(ATTR_MIN, min(ATTR_MAX, value))


def modify_attr(current: int, delta: int) -> tuple[int, int]:
    """修改属性值，返回 (新值, 实际变化量)"""
    new_val = clamp(current + delta)
    actual_change = new_val - current
    return new_val, actual_change


def get_random_attr() -> str:
    """随机选择一个属性key"""
    return random.choice(ATTR_KEYS)


def pick_events_attr_change(is_bad: bool = False) -> dict[str, int]:
    """为事件随机生成属性变化
    好事件：1~3个随机属性 +1~+3
    坏事件：1~2个随机属性 -1~-3
    返回 { attribute_key: delta, ... }
    """
    changes: dict[str, int] = {}
    if is_bad:
        count = random.randint(1, 2)
        for _ in range(count):
            attr = get_random_attr()
            delta = random.randint(-3, -1)
            if attr in changes:
                changes[attr] += delta
            else:
                changes[attr] = delta
    else:
        count = random.randint(1, 3)
        for _ in range(count):
            attr = get_random_attr()
            delta = random.randint(1, 3)
            if attr in changes:
                changes[attr] += delta
            else:
                changes[attr] = delta
    return changes
