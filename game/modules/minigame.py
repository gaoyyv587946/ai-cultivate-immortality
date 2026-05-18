"""小游戏模块
提供可扩展的小游戏系统，支持注册新游戏、放弃惩罚机制
"""
import random
from typing import Optional, Callable

from .attributes import ATTR_LABELS

# 游戏注册表
_games: dict[str, dict] = {}
_game_handlers: dict[str, dict] = {}


def register_game(name: str, description: str, category: str = "通用",
                  start_handler: Optional[Callable] = None,
                  action_handler: Optional[Callable] = None):
    """注册一个小游戏"""
    _games[name] = {
        "name": name,
        "description": description,
        "category": category,
    }
    if start_handler or action_handler:
        _game_handlers[name] = {
            "start": start_handler,
            "action": action_handler,
        }


def get_available_games() -> list[dict]:
    return list(_games.values())


def start_game(game_name: str, player) -> Optional[dict]:
    """启动一个小游戏，返回初始游戏状态"""
    handler = _game_handlers.get(game_name)
    if handler and handler["start"]:
        return handler["start"](player)
    return None


def execute_action(game_name: str, player, game_state: dict, action: str) -> dict:
    """执行游戏中的操作"""
    handler = _game_handlers.get(game_name)
    if handler and handler["action"]:
        return handler["action"](player, game_state, action)
    return {"ended": True, "result": "未知操作", "rewards": {}}


# ==================== 放弃惩罚机制 ====================

GIVEUP_PUNISHMENTS = [
    {"type": "cultivation", "label": "修为", "range": (-30, -10)},
    {"type": "intelligence", "label": "智力", "range": (-3, -1)},
    {"type": "stamina", "label": "体力", "range": (-3, -1)},
    {"type": "strength", "label": "力量", "range": (-3, -1)},
    {"type": "spirit", "label": "精神", "range": (-3, -1)},
    {"type": "lifespan", "label": "寿命", "range": (-5, -2)},
    {"type": "spirit_stones", "label": "灵石", "range": (-50, -10)},
]


def apply_giveup_penalty(player) -> dict:
    """应用放弃惩罚，返回惩罚描述"""
    count = random.randint(1, 2)
    selected = random.sample(GIVEUP_PUNISHMENTS, min(count, len(GIVEUP_PUNISHMENTS)))
    parts = []
    for p in selected:
        delta = random.randint(p["range"][0], p["range"][1])
        if p["type"] == "cultivation":
            player.reduce_cultivation(abs(delta))
            parts.append(f"修为 {delta}")
        elif p["type"] == "lifespan":
            player.consume_lifespan(abs(delta))
            parts.append(f"寿命 {delta}年")
        elif p["type"] == "spirit_stones":
            player.add_spirit_stones(delta)
            parts.append(f"灵石 {delta}")
        elif p["type"] in ("intelligence", "stamina", "strength", "spirit"):
            old_val = getattr(player, p["type"])
            from .attributes import modify_attr
            new_val, actual = modify_attr(old_val, delta)
            setattr(player, p["type"], new_val)
            if actual != 0:
                parts.append(f"{p['label']} {actual}")
    return {
        "punishments": parts,
        "description": "，".join(parts) if parts else "无",
    }


# ==================== 内置小游戏 ====================

# --- 1. 灵石猜猜看 ---

def _guess_start(player) -> dict:
    target = random.randint(1, 10)
    return {
        "game": "灵石猜猜看",
        "target": target,
        "attempts": 0,
        "max_attempts": 3,
        "bet": random.randint(5, 20),
        "ended": False,
    }


def _guess_action(player, state: dict, action: str) -> dict:
    if state.get("ended"):
        return {"ended": True, "result": "游戏已结束", "rewards": {}}

    try:
        guess = int(action.strip())
    except ValueError:
        return {"ended": False, "result": "请输入一个数字！", "rewards": {}}

    state["attempts"] += 1
    target = state["target"]
    bet = state["bet"]

    if guess == target:
        reward_ss = bet * 2
        player.add_spirit_stones(reward_ss)
        player.add_cultivation(bet)
        state["ended"] = True
        return {
            "ended": True,
            "result": f"🎉 猜对了！数字就是 {target}！赢得 {reward_ss} 灵石，修为 +{bet}",
            "rewards": {"spirit_stones": reward_ss, "cultivation": bet},
        }
    elif state["attempts"] >= state["max_attempts"]:
        player.add_spirit_stones(-bet)
        state["ended"] = True
        return {
            "ended": True,
            "result": f"😵 三次机会用完了！数字是 {target}，损失 {bet} 灵石",
            "rewards": {"spirit_stones": -bet},
        }
    else:
        hint = "大了" if guess > target else "小了"
        return {
            "ended": False,
            "result": f"❌ 猜{hint}了，还剩 {state['max_attempts'] - state['attempts']} 次机会",
            "rewards": {},
        }


register_game(
    "灵石猜猜看",
    "庄家心里想了一个1-10的数字，你有3次机会猜中，猜中赢取双倍灵石！",
    category="赌运",
    start_handler=_guess_start,
    action_handler=_guess_action,
)


# --- 2. 灵兽捕捉 ---

BEAST_TYPES = [
    {"name": "疾风狼", "power": 3, "reward": (15, 25)},
    {"name": "火焰雀", "power": 2, "reward": (10, 20)},
    {"name": "玄冰龟", "power": 4, "reward": (20, 35)},
    {"name": "雷霆蟒", "power": 5, "reward": (25, 40)},
    {"name": "幻光蝶", "power": 1, "reward": (5, 15)},
]


def _beast_start(player) -> dict:
    beast = random.choice(BEAST_TYPES)
    return {
        "game": "灵兽捕捉",
        "beast": beast,
        "player_power": random.randint(1, 5),
        "ended": False,
    }


def _beast_action(player, state: dict, action: str) -> dict:
    if state.get("ended"):
        return {"ended": True, "result": "战斗已结束", "rewards": {}}

    beast = state["beast"]
    player_power = state["player_power"]

    action = action.strip()
    if action == "攻击":
        total = player_power + random.randint(1, 3)
        if total >= beast["power"]:
            reward_range = beast["reward"]
            cult_gain = random.randint(reward_range[0], reward_range[1])
            player.add_cultivation(cult_gain)
            state["ended"] = True
            return {
                "ended": True,
                "result": f"⚔️ 你成功击败了【{beast['name']}】！修为 +{cult_gain}",
                "rewards": {"cultivation": cult_gain},
            }
        else:
            damage = random.randint(5, 15)
            player.reduce_cultivation(damage)
            state["ended"] = True
            return {
                "ended": True,
                "result": f"💥 你没能击败【{beast['name']}】，受到反噬，修为 -{damage}",
                "rewards": {"cultivation": -damage},
            }
    elif action == "防御":
        player_power += 1
        state["player_power"] = player_power
        return {
            "ended": False,
            "result": f"🛡️ 你摆出防御姿态，气势提升了！当前战力 {player_power}，灵兽战力 {beast['power']}",
            "rewards": {},
        }
    elif action == "观察":
        return {
            "ended": False,
            "result": f"🔍 你仔细观察【{beast['name']}】，发现它的弱点是 {'速度慢' if beast['power'] > 3 else '防御弱'}，建议全力攻击！",
            "rewards": {},
        }
    else:
        return {
            "ended": False,
            "result": "可用指令：攻击 / 防御 / 观察",
            "rewards": {},
        }


register_game(
    "灵兽捕捉",
    "野外遇到一只灵兽，选择战斗策略来捕捉它！",
    category="战斗",
    start_handler=_beast_start,
    action_handler=_beast_action,
)


# === 3. 诗词接龙 ===

POEM_LINES = [
    ("床前明月光，", "疑是地上霜"),
    ("举头望明月，", "低头思故乡"),
    ("白日依山尽，", "黄河入海流"),
    ("春眠不觉晓，", "处处闻啼鸟"),
    ("好雨知时节，", "当春乃发生"),
    ("离离原上草，", "一岁一枯荣"),
    ("锄禾日当午，", "汗滴禾下土"),
    ("欲穷千里目，", "更上一层楼"),
    ("飞流直下三千尺，", "疑是银河落九天"),
    ("两个黄鹂鸣翠柳，", "一行白鹭上青天"),
]


def _poem_start(player) -> dict:
    first, second = random.choice(POEM_LINES)
    return {
        "game": "诗词接龙",
        "first_half": first,
        "second_half": second,
        "ended": False,
    }


def _poem_action(player, state: dict, action: str) -> dict:
    if state.get("ended"):
        return {"ended": True, "result": "游戏已结束", "rewards": {}}
    action = action.strip()
    if not action:
        return {"ended": False, "result": "请写下你的诗句！", "rewards": {}}

    state["ended"] = True
    cult_gain = random.randint(10, 25)
    player.add_cultivation(cult_gain)
    return {
        "ended": True,
        "result": f"📜 原句是：「{state['first_half']}{state['second_half']}」\n你的接龙：「{state['first_half']}{action}」——颇有文采！修为 +{cult_gain}",
        "rewards": {"cultivation": cult_gain},
    }


register_game(
    "诗词接龙",
    "根据上句诗词，写下你想到的下句，感受诗词之美！",
    category="文学",
    start_handler=_poem_start,
    action_handler=_poem_action,
)


# === 4. 炼丹小试 ===

PILL_INGREDIENTS = {
    "千年灵芝": {"cost": 10, "power": 3},
    "万年人参": {"cost": 15, "power": 4},
    "龙涎草": {"cost": 5, "power": 2},
    "凤凰羽": {"cost": 20, "power": 5},
    "冰晶花": {"cost": 8, "power": 2},
    "星辰砂": {"cost": 12, "power": 3},
}


def _pill_start(player) -> dict:
    return {
        "game": "炼丹小试",
        "selected": [],
        "max_select": 3,
        "ended": False,
        "result_text": "",
    }


def _pill_action(player, state: dict, action: str) -> dict:
    if state.get("ended"):
        return {"ended": True, "result": "炼丹已结束", "rewards": {}}

    action = action.strip()

    if action == "开炉" or action == "confirm":
        selected = state.get("selected", [])
        if len(selected) < 2:
            return {"ended": False, "result": "至少选2种材料才能开炉炼丹！", "rewards": {}}

        total_power = sum(PILL_INGREDIENTS[ing]["power"] for ing in selected)
        total_cost = sum(PILL_INGREDIENTS[ing]["cost"] for ing in selected)

        if player.spirit_stones < total_cost:
            state["ended"] = True
            return {
                "ended": True,
                "result": f"灵石不足（需要 {total_cost} 灵石），炼丹失败！",
                "rewards": {},
            }

        player.add_spirit_stones(-total_cost)
        success = total_power >= 8
        if success:
            cult_gain = total_power * 5 + random.randint(5, 15)
            player.add_cultivation(cult_gain)
            state["ended"] = True
            return {
                "ended": True,
                "result": f"✨ 炼丹成功！用{'、'.join(selected)}炼出宝丹，修为 +{cult_gain}（花费 {total_cost} 灵石）",
                "rewards": {"cultivation": cult_gain, "spirit_stones": -total_cost},
            }
        else:
            state["ended"] = True
            return {
                "ended": True,
                "result": f"💥 炼丹失败！{'、'.join(selected)}的药力不足（{total_power}），材料化为灰烬！损失 {total_cost} 灵石",
                "rewards": {"spirit_stones": -total_cost},
            }

    if action in PILL_INGREDIENTS:
        selected = state.get("selected", [])
        if action in selected:
            return {"ended": False, "result": f"{action} 已经选过了，换一种吧。", "rewards": {}}
        if len(selected) >= state["max_select"]:
            return {"ended": False, "result": f"最多选{state['max_select']}种材料，已选：{'、'.join(selected)}", "rewards": {}}
        selected.append(action)
        state["selected"] = selected
        cost = PILL_INGREDIENTS[action]["cost"]
        if len(selected) >= state["max_select"]:
            return {"ended": False, "result": f"已选：{'、'.join(selected)}，可以开炉了！", "rewards": {}}
        return {
            "ended": False,
            "result": f"已选：{'、'.join(selected)}（花费 {cost} 灵石），继续选或开炉！",
            "rewards": {},
        }

    return {
        "ended": False,
        "result": "可选材料：" + "、".join(PILL_INGREDIENTS.keys()) + "。选好后输入「开炉」",
        "rewards": {},
    }


register_game(
    "炼丹小试",
    "选择 2-3 种天材地宝炼制丹药，药力够强才能成功！",
    category="生产",
    start_handler=_pill_start,
    action_handler=_pill_action,
)


# === 5. 秘境碎石 ===

MINE_GEMS = [
    {"name": "灵石碎片", "value": (5, 15), "chance": 40},
    {"name": "下品灵石", "value": (15, 30), "chance": 25},
    {"name": "中品灵石", "value": (30, 50), "chance": 15},
    {"name": "上品灵石", "value": (50, 80), "chance": 8},
    {"name": "极品灵石", "value": (80, 150), "chance": 4},
    {"name": "💀 陷阱", "value": (-30, -10), "chance": 8},
]


def _mine_start(player) -> dict:
    return {
        "game": "秘境碎石",
        "swings": 0,
        "max_swings": 5,
        "total_gain": 0,
        "mines": [],
        "remaining": 5,
        "ended": False,
    }


def _mine_action(player, state: dict, action: str) -> dict:
    if state.get("ended"):
        return {"ended": True, "result": "挖矿已结束", "rewards": {}}

    if state["swings"] >= state["max_swings"]:
        state["ended"] = True
        return {
            "ended": True,
            "result": f"次数用完了！共挖到 {state['total_gain']} 灵石",
            "rewards": {"spirit_stones": state["total_gain"]},
        }

    state["swings"] += 1
    remaining = state["max_swings"] - state["swings"]
    state["remaining"] = remaining

    roll = random.randint(1, 100)
    cumulative = 0
    chosen = None
    for gem in MINE_GEMS:
        cumulative += gem["chance"]
        if roll <= cumulative:
            chosen = gem
            break
    if not chosen:
        chosen = MINE_GEMS[0]

    value = random.randint(chosen["value"][0], chosen["value"][1])
    label = f"{chosen['name']} +{value}" if value >= 0 else f"{chosen['name']} {value}"
    state.setdefault("mines", []).append(label)

    if chosen["name"] == "💀 陷阱":
        player.add_spirit_stones(value)
        state["total_gain"] += value
        return {
            "ended": False,
            "result": f"💥 踩到陷阱！损失 {abs(value)} 灵石（剩余 {remaining} 次）",
            "rewards": {"spirit_stones": value},
        }
    else:
        player.add_spirit_stones(value)
        state["total_gain"] += value
        if remaining > 0:
            return {
                "ended": False,
                "result": f"⛏️ 挖到{chosen['name']}！+{value} 灵石（剩余 {remaining} 次）",
                "rewards": {"spirit_stones": value},
            }
        else:
            state["ended"] = True
            return {
                "ended": True,
                "result": f"⛏️ 最后一次挖到{chosen['name']}！+{value} 灵石。总共收获 {state['total_gain']} 灵石",
                "rewards": {"spirit_stones": value},
            }


register_game(
    "秘境碎石",
    "深入秘境挖掘灵石，挖5次，出宝还是踩坑全看运气！",
    category="探险",
    start_handler=_mine_start,
    action_handler=_mine_action,
)


# === 6. 奇遇骰子 ===

DICE_EVENTS = [
    {"roll": 1, "name": "天降横财", "desc": "你捡到一个小袋子，里面有些许灵石。", "ss": (10, 25)},
    {"roll": 2, "name": "灵泉沐浴", "desc": "你发现一处灵泉，浸泡后神清气爽！", "cult": (15, 30)},
    {"roll": 3, "name": "仙人指路", "desc": "一位神秘仙人指点你修行法门。", "intel": (1, 2), "cult": (10, 20)},
    {"roll": 4, "name": "妖兽袭击", "desc": "你被妖兽袭击，奋力搏斗后逃脱。", "stamina": (-2, -1), "ss": (-15, -5)},
    {"roll": 5, "name": "古卷参悟", "desc": "你发现一卷上古秘籍，参悟后修为大进！", "spirit": (1, 3), "cult": (25, 45)},
    {"roll": 6, "name": "天道赐福", "desc": "天道感应到你的诚心，降下福泽！", "cult": (30, 50), "ss": (20, 40)},
]


def _dice_start(player) -> dict:
    return {
        "game": "奇遇骰子",
        "rolled": False,
        "ended": False,
    }


def _dice_action(player, state: dict, action: str) -> dict:
    if state.get("ended"):
        return {"ended": True, "result": "奇遇已结束", "rewards": {}}
    if state.get("rolled"):
        return {"ended": True, "result": "你已经掷过骰子了", "rewards": {}}

    state["rolled"] = True
    state["ended"] = True
    roll = random.randint(1, 6)
    event = DICE_EVENTS[roll - 1]

    rewards = {}
    parts = [f"🎲 掷出 {roll} 点：{event['name']}！", event["desc"]]

    if "ss" in event:
        val = random.randint(event["ss"][0], event["ss"][1])
        player.add_spirit_stones(val)
        rewards["spirit_stones"] = val
        parts.append(f"灵石 {'+' if val >= 0 else ''}{val}")

    if "cult" in event:
        val = random.randint(event["cult"][0], event["cult"][1])
        player.add_cultivation(val)
        rewards["cultivation"] = val
        parts.append(f"修为 +{val}")

    for attr_key in ("intel", "stamina", "spirit"):
        if attr_key in event:
            from .attributes import modify_attr as _modattr
            val = random.randint(event[attr_key][0], event[attr_key][1])
            pkey = {"intel": "intelligence", "stamina": "stamina", "spirit": "spirit"}[attr_key]
            old = getattr(player, pkey)
            newv, actual = _modattr(old, val)
            setattr(player, pkey, newv)
            if actual != 0:
                from .attributes import ATTR_LABELS as _LABELS
                parts.append(f"{_LABELS.get(pkey, pkey)} {'+' if actual > 0 else ''}{actual}")

    player.consume_lifespan(1)
    parts.append("寿命 -1")
    return {"ended": True, "result": "\n".join(parts), "rewards": rewards}


register_game(
    "奇遇骰子",
    "掷出命运的骰子（1-6），随机触发各种奇遇！",
    category="命运",
    start_handler=_dice_start,
    action_handler=_dice_action,
)
