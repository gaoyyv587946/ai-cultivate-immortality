"""成就系统模块
定义所有成就及其检查逻辑
"""
from .database import unlock_achievement, get_player_achievements


ACHIEVEMENTS = [
    {
        "id": "intelligence_master",
        "name": "智力超群",
        "title": "小天才",
        "description": "智力达到70以上，聪明过人",
        "icon": "🧠",
        "condition_desc": "智力 ≥ 70"
    },
    {
        "id": "stamina_master",
        "name": "体力超群",
        "title": "壮汉",
        "description": "体力达到70以上，身强体壮",
        "icon": "💪",
        "condition_desc": "体力 ≥ 70"
    },
    {
        "id": "strength_master",
        "name": "力量超群",
        "title": "大力士",
        "description": "力量达到70以上，力大无穷",
        "icon": "⚔️",
        "condition_desc": "力量 ≥ 70"
    },
    {
        "id": "spirit_master",
        "name": "精神超群",
        "title": "智者",
        "description": "精神达到70以上，意志坚定",
        "icon": "✨",
        "condition_desc": "精神 ≥ 70"
    },
    {
        "id": "harem_king",
        "name": "妻妾成群",
        "title": "风流倜傥",
        "description": "与2位以上NPC结为道侣",
        "icon": "👨‍👩‍👧‍👧",
        "condition_desc": "道侣 ≥ 2位"
    },
    {
        "id": "social_butterfly",
        "name": "好友遍布",
        "title": "社交达人",
        "description": "5位以上NPC好感度不低于40",
        "icon": "🤝",
        "condition_desc": "5位NPC好感度 ≥ 40"
    },
    {
        "id": "inner_volume",
        "name": "卷王",
        "title": "内卷之王",
        "description": "累计完成300回合修炼",
        "icon": "📚",
        "condition_desc": "回合数 ≥ 300"
    },
    {
        "id": "worker_bee",
        "name": "打工仔",
        "title": "社畜",
        "description": "打工累计赚取1000灵石",
        "icon": "💼",
        "condition_desc": "打工收入 ≥ 1000灵石"
    },
    {
        "id": "game_master",
        "name": "游戏之王",
        "title": "游戏大师",
        "description": "完成10次小游戏挑战",
        "icon": "🎮",
        "condition_desc": "完成小游戏 ≥ 10次"
    },
    {
        "id": "bookworm",
        "name": "博览群书",
        "title": "学霸",
        "description": "完成10次考试",
        "icon": "📖",
        "condition_desc": "完成考试 ≥ 10次"
    },
    {
        "id": "saint",
        "name": "大善人",
        "title": "活佛转世",
        "description": "善恶度达到80以上，乐善好施",
        "icon": "😇",
        "condition_desc": "善恶度 ≥ 80"
    },
    {
        "id": "villain",
        "name": "大恶人",
        "title": "魔头降世",
        "description": "善恶度达到-80以下，无恶不作",
        "icon": "😈",
        "condition_desc": "善恶度 ≤ -80"
    },
    {
        "id": "firm_heart",
        "name": "道心坚定",
        "title": "佛系青年",
        "description": "道心值达到80以上，坚定不移",
        "icon": "🧘",
        "condition_desc": "道心值 ≥ 80"
    },
    {
        "id": "broken_heart",
        "name": "道心破碎",
        "title": "摆烂达人",
        "description": "道心值跌破15，彻底摆烂",
        "icon": "💔",
        "condition_desc": "道心值 ≤ 15"
    },
    {
        "id": "rich_man",
        "name": "灵石大亨",
        "title": "灵石首富",
        "description": "拥有3000以上灵石",
        "icon": "🤑",
        "condition_desc": "灵石 ≥ 3000"
    },
    {
        "id": "long_life",
        "name": "寿比南山",
        "title": "老不死",
        "description": "剩余寿命达到3000年以上",
        "icon": "🐢",
        "condition_desc": "剩余寿命 ≥ 3000年"
    },
    {
        "id": "cultivation_maniac",
        "name": "修炼狂魔",
        "title": "修炼疯子",
        "description": "修为达到10000点",
        "icon": "🔥",
        "condition_desc": "修为 ≥ 10000"
    },
    {
        "id": "breakthrough_champion",
        "name": "突破达人",
        "title": "飞升预备役",
        "description": "达到合体期（博士）以上",
        "icon": "🚀",
        "condition_desc": "境界 ≥ 合体期"
    },
    {
        "id": "heartthrob",
        "name": "万人迷",
        "title": "芳心纵火犯",
        "description": "3位以上NPC好感度不低于60",
        "icon": "🌸",
        "condition_desc": "3位NPC好感度 ≥ 60"
    },
    {
        "id": "all_rounder",
        "name": "均衡发展",
        "title": "六边形战士",
        "description": "四维属性全部达到60以上",
        "icon": "⚖️",
        "condition_desc": "全部属性 ≥ 60"
    },
    {
        "id": "first_step",
        "name": "初出茅庐",
        "title": "修仙萌新",
        "description": "完成第一次境界突破",
        "icon": "🌱",
        "condition_desc": "完成首次突破"
    },
    {
        "id": "obsessive",
        "name": "偏执狂",
        "title": "一条道走到黑",
        "description": "任意单一属性达到95",
        "icon": "🎯",
        "condition_desc": "任意属性 ≥ 95"
    },
    {
        "id": "social_anxiety",
        "name": "社交恐惧症",
        "title": "透明人",
        "description": "从未触发过NPC搭讪",
        "icon": "🙈",
        "condition_desc": "NPC搭讪次数 = 0"
    },
    {
        "id": "loyal_lover",
        "name": "情种",
        "title": "专一痴情",
        "description": "与一位NPC好感度达到80以上",
        "icon": "💕",
        "condition_desc": "单NPC好感度 ≥ 80"
    },
    {
        "id": "debtor",
        "name": "负债累累",
        "title": "穷光蛋",
        "description": "灵石欠债达到-50以下",
        "icon": "💸",
        "condition_desc": "灵石 ≤ -50"
    },
]


def check_achievement(achievement_id: str, player, user_id: int, npcs: list) -> bool:
    """检查单个成就条件是否满足"""
    ach_map = {a["id"]: a for a in ACHIEVEMENTS}
    ach = ach_map.get(achievement_id)
    if not ach:
        return False

    if achievement_id == "intelligence_master":
        return player.intelligence >= 70
    elif achievement_id == "stamina_master":
        return player.stamina >= 70
    elif achievement_id == "strength_master":
        return player.strength >= 70
    elif achievement_id == "spirit_master":
        return player.spirit >= 70
    elif achievement_id == "harem_king":
        married_count = sum(1 for npc in npcs if npc.get("is_married"))
        return married_count >= 2
    elif achievement_id == "social_butterfly":
        count = sum(1 for npc in npcs if npc.get("relationship", 0) >= 40)
        return count >= 5
    elif achievement_id == "inner_volume":
        return player.turn_count >= 300
    elif achievement_id == "worker_bee":
        return player.work_earnings >= 1000
    elif achievement_id == "game_master":
        return player.minigame_count >= 10
    elif achievement_id == "bookworm":
        return player.exam_count >= 10
    elif achievement_id == "saint":
        return player.good_evil >= 80
    elif achievement_id == "villain":
        return player.good_evil <= -80
    elif achievement_id == "firm_heart":
        return player.dao_heart >= 80
    elif achievement_id == "broken_heart":
        return player.dao_heart <= 15
    elif achievement_id == "rich_man":
        return player.spirit_stones >= 3000
    elif achievement_id == "long_life":
        return player.remaining_lifespan >= 3000
    elif achievement_id == "cultivation_maniac":
        return player.cultivation >= 10000
    elif achievement_id == "breakthrough_champion":
        return player.realm_level >= 7
    elif achievement_id == "heartthrob":
        count = sum(1 for npc in npcs if npc.get("relationship", 0) >= 60)
        return count >= 3
    elif achievement_id == "all_rounder":
        return (player.intelligence >= 60 and player.stamina >= 60
                and player.strength >= 60 and player.spirit >= 60)
    elif achievement_id == "first_step":
        return player.has_breakthrough
    elif achievement_id == "obsessive":
        return (player.intelligence >= 95 or player.stamina >= 95
                or player.strength >= 95 or player.spirit >= 95)
    elif achievement_id == "social_anxiety":
        return player.npc_encounter_count == 0 and player.turn_count >= 50
    elif achievement_id == "loyal_lover":
        return any(npc.get("relationship", 0) >= 80 for npc in npcs)
    elif achievement_id == "debtor":
        return player.spirit_stones <= -50

    return False


def check_all_achievements(player, user_id: int, npcs: list) -> list:
    """检查所有成就，返回新解锁的成就列表"""
    unlocked_ids = {a["achievement_id"] for a in get_player_achievements(user_id)}
    new_achievements = []
    for ach in ACHIEVEMENTS:
        if ach["id"] in unlocked_ids:
            continue
        if check_achievement(ach["id"], player, user_id, npcs):
            if unlock_achievement(user_id, ach["id"]):
                player.achievements.append(ach["id"])
                new_achievements.append(ach)
    return new_achievements
