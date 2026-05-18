"""NPC 随机生成器模块
负责根据玩家当前状态生成合理的NPC，并存入SQLite数据库
"""

import random
from typing import Optional
from .config import (
    NPC_SURNAMES, NPC_GIVEN_NAMES_MALE, NPC_GIVEN_NAMES_FEMALE, NPC_TITLES,
    NPC_INITIAL_RELATIONSHIP_MIN, NPC_INITIAL_RELATIONSHIP_MAX,
    FEMALE_NPC_AFFECTION_TYPES
)
from .database import is_npc_exists, add_npc, get_all_npcs, add_relationship_event
from .realms import get_realm_by_level


def generate_npc_name() -> tuple:
    """生成随机的修仙风格NPC姓名"""
    surname = random.choice(NPC_SURNAMES)
    gender = random.choice(["male", "female"])
    if gender == "male":
        given_name = random.choice(NPC_GIVEN_NAMES_MALE)
    else:
        given_name = random.choice(NPC_GIVEN_NAMES_FEMALE)
    return surname + given_name, gender


def generate_npc_title() -> str:
    """生成随机称号"""
    return random.choice(NPC_TITLES)


def generate_npc_backstory(realm_level: int, relation: str = "偶遇") -> str:
    """根据初见场景生成背景故事"""
    templates = [
        f"在{get_realm_by_level(realm_level)['school']}中{relation}，来历不明，独自修行。",
        f"据说是某个小家族的子弟，在{relation}时与你相识。",
        f"曾在一次{relation}中与你并肩作战，之后便结下了缘分。",
        f"你也不知道他/她的来历，只知道在一次{relation}中偶然相遇。",
        f"看起来是一位经验丰富的修行者，在一次{relation}中你们彼此留下了印象。"
    ]
    return random.choice(templates)


def generate_npcs_for_new_realm(user_id: int, player_realm_level: int, encounter_scene: str = "") -> list:
    """玩家达到新境界时，生成1-3个新NPC，返回新生成NPC的ID列表"""
    count = random.randint(1, 3)
    new_npc_ids = []
    for _ in range(count):
        npc_info = _create_single_npc(user_id, player_realm_level, encounter_scene or "宗门历练")
        if npc_info:
            new_npc_ids.append(npc_info["id"])
    return new_npc_ids


def generate_initial_npcs(user_id: int, player_realm_level: int) -> list:
    """游戏开始时生成2-3个初始NPC"""
    return generate_npcs_for_new_realm(user_id, player_realm_level, "初入修行")


def generate_event_npc(user_id: int, player_realm_level: int, event_description: str) -> Optional[dict]:
    """随机事件中遭遇NPC时调用，生成一个临时NPC"""
    return _create_single_npc(user_id, player_realm_level, event_description)


def _create_single_npc(user_id: int, player_realm_level: int, scene: str) -> Optional[dict]:
    """创建单个NPC的内部方法"""
    for _ in range(50):
        name, gender = generate_npc_name()
        if not is_npc_exists(user_id, name):
            break
    else:
        return None

    npc_level = max(1, min(8, player_realm_level + random.randint(-1, 1)))
    npc_realm_info = get_realm_by_level(npc_level)
    npc_realm = npc_realm_info["name"]
    title = generate_npc_title()
    relationship = random.randint(NPC_INITIAL_RELATIONSHIP_MIN, NPC_INITIAL_RELATIONSHIP_MAX)
    backstory = generate_npc_backstory(player_realm_level, scene)

    player_realm_info = get_realm_by_level(player_realm_level)
    first_met_at = f"{player_realm_info['school']}({player_realm_info['name']})"

    affection_type = ""
    favorite_gift = ""
    if gender == "female":
        affection_config = random.choice(FEMALE_NPC_AFFECTION_TYPES)
        affection_type = affection_config["type"]
        favorite_gift = affection_config["gift_preference"]

    npc_id = add_npc(
        user_id=user_id,
        name=name,
        title=title,
        realm=npc_realm,
        realm_level=npc_level,
        first_met_at=first_met_at,
        first_met_realm_level=player_realm_level,
        relationship=relationship,
        backstory=backstory,
        gender=gender,
        affection_type=affection_type,
        favorite_gift=favorite_gift
    )

    if npc_id < 0:
        return None

    player_realm_name = player_realm_info["name"]
    event_desc = f"你在{player_realm_info['school']}遇到了{name}（{title}），{backstory}"
    add_relationship_event(
        user_id=user_id,
        npc_id=npc_id,
        event_type="相遇",
        description=event_desc,
        relationship_change=relationship,
        player_realm=player_realm_name,
        player_realm_level=player_realm_level
    )

    return {
        "id": npc_id,
        "name": name,
        "title": title,
        "realm": npc_realm,
        "realm_level": npc_level,
        "relationship": relationship,
        "backstory": backstory,
        "gender": gender
    }


def get_npcs_for_display(user_id: int) -> list:
    """获取用于前端展示的NPC列表，按关系度降序排列"""
    npcs = get_all_npcs(user_id)
    result = []
    for npc in npcs:
        if npc["relationship"] > 0:
            symbol = "❤️"
        elif npc["relationship"] < 0:
            symbol = "🔥"
        else:
            symbol = "⚪"
        status = "💀" if not npc["is_alive"] else ""
        married = "💍" if npc["is_married"] else ""
        sworn = "🤝" if npc["is_sworn_brother"] else ""
        result.append({
            "id": npc["id"],
            "name": npc["name"],
            "title": npc["title"],
            "realm": npc["realm"],
            "realm_level": npc["realm_level"],
            "relationship": npc["relationship"],
            "symbol": symbol,
            "is_alive": bool(npc["is_alive"]),
            "status": status,
            "is_married": married,
            "is_sworn_brother": bool(npc["is_sworn_brother"]),
            "backstory": npc["backstory"],
            "gender": npc["gender"],
            "affection_type": npc["affection_type"] if npc["gender"] == "female" and npc["affection_type"] else "",
            "shared_cultivation": npc["shared_cultivation"] if npc["shared_cultivation"] else 0
        })
    return result
