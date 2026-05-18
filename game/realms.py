"""境界体系模块
定义8大修炼境界及其相关的工具函数
"""

from typing import Optional
from .config import REALMS


def get_realm_by_id(realm_id: int) -> Optional[dict]:
    """
    根据ID获取境界信息
    ID范围: 1(练气) ~ 8(大乘)
    """
    for realm in REALMS:
        if realm["id"] == realm_id:
            return realm
    return None


def get_realm_by_level(realm_level: int) -> Optional[dict]:
    """根据等级(1-8)获取境界信息，同 get_realm_by_id"""
    return get_realm_by_id(realm_level)


def get_realm_by_name(name: str) -> Optional[dict]:
    """根据境界名称获取境界信息"""
    for realm in REALMS:
        if realm["name"] == name:
            return realm
    return None


def get_realm_by_school(school: str) -> Optional[dict]:
    """根据学校名称获取境界信息"""
    for realm in REALMS:
        if realm["school"] == school:
            return realm
    return None


def get_max_realm_level() -> int:
    """获取最高境界等级（大乘期=8）"""
    return len(REALMS)


def is_max_realm(realm_level: int) -> bool:
    """判断是否已达到最高境界"""
    return realm_level >= get_max_realm_level()


def can_breakthrough(current_realm_level: int, current_cultivation: int) -> bool:
    """
    判断是否可以突破到下一境界
    条件：修为达到或超过当前境界的突破阈值
    """
    if is_max_realm(current_realm_level):
        return False
    realm = get_realm_by_level(current_realm_level)
    return current_cultivation >= realm["breakthrough_threshold"]


def calculate_lifespan(realm_level: int) -> int:
    """
    计算指定境界的基础寿命
    寿命随境界提升而增加
    """
    realm = get_realm_by_level(realm_level)
    return realm["base_lifespan"]


def get_realm_name(realm_level: int) -> str:
    """获取境界名称"""
    realm = get_realm_by_level(realm_level)
    return realm["name"] if realm else "未知"


def get_school_name(realm_level: int) -> str:
    """获取对应的学校名称"""
    realm = get_realm_by_level(realm_level)
    return realm["school"] if realm else "未知"


def get_realm_description(realm_level: int) -> str:
    """获取境界描述"""
    realm = get_realm_by_level(realm_level)
    return realm["description"] if realm else ""


def get_cost_multiplier(realm_level: int) -> float:
    """获取当前境界的寿命消耗倍率"""
    realm = get_realm_by_level(realm_level)
    return realm["cost_multiplier"] if realm else 1.0


def get_breakthrough_threshold(realm_level: int) -> int:
    """获取突破到下一境界所需的修为阈值"""
    if is_max_realm(realm_level):
        return float("inf")
    realm = get_realm_by_level(realm_level)
    return realm["breakthrough_threshold"]


def format_realm_info(realm_level: int) -> str:
    """格式化输出境界信息"""
    realm = get_realm_by_level(realm_level)
    if not realm:
        return "未知境界"
    return f"{realm['school']}({realm['name']})"
