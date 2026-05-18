"""DeepSeek API 集成模块
负责与 DeepSeek API 进行通信，处理自定义行动的判定和随机事件的生成
"""

import json
import requests
from typing import Optional
from .config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL, DEEPSEEK_TIMEOUT


def check_deepseek_limit(user_id: int) -> bool:
    """检查用户DeepSeek调用是否达到上限
    返回 True 表示限制未达上限（可以调API），False 表示已达上限（需回退到mock）
    """
    from .database import get_deepseek_call_count, get_user_by_id
    user = get_user_by_id(user_id)
    if not user:
        return True
    user_dict = dict(user)
    limit = user_dict.get("deepseek_daily_limit") or 50
    current = get_deepseek_call_count(user_id)
    return current < limit


def increment_deepseek_calls(user_id: int):
    """增加用户DeepSeek调用计数"""
    from .database import increment_deepseek_calls as _inc
    _inc(user_id)


def _build_system_prompt(player_realm_name: str, player_school: str,
                         realm_description: str, nearby_npcs_info: str = "",
                         player_good_evil: int = 0, player_dao_heart: int = 50,
                         player_spirit_stones: int = 0) -> str:
    """
    构造发送给 DeepSeek 的系统提示词
    指导 DeepSeek 以天道法则判定系统的角色进行回应
    """
    good_evil_label = "善良" if player_good_evil > 0 else ("邪恶" if player_good_evil < 0 else "中立")
    prompt = f"""你是一个修仙世界的天道法则判定系统。你的职责是根据玩家的行动，判定其在当前境界下的合理性，并返回结构化的结果。

【当前玩家状态】
境界：{player_realm_name}（{player_school}）
境界描述：{realm_description}
善恶度：{player_good_evil}（{good_evil_label}）
道心值：{player_dao_heart}/100
灵石：{player_spirit_stones}

【判定规则】
1. 行动必须符合当前境界的能力范围：
   - 练气期（幼儿园）：只能进行基础感气、简单锻体、基础草药认知等活动
   - 筑基期（小学）：可以筑造道基、基础炼丹、简单法术切磋
   - 结丹期（初中）：可以凝聚金丹、御器初学、探索小型秘境
   - 元婴期（高中）：可以元婴出窍、御器飞行、中级炼器
   - 化神期（大学）：可以参悟法则、开坛讲道、斩妖除魔
   - 炼虚期（硕士）：可以撕裂虚空、炼制法宝、收徒传道
   - 合体期（博士）：可以天人合一、创造小世界、推演天道
   - 大乘期（博士后）：可以炼制仙器、感悟天劫、飞升准备

2. 不合理行动的判定标准：
   - 低境界做高境界的事（如练气期想炼丹）→ 判定为不合理
   - 违背修仙常识（如想一夜成仙）→ 判定为不合理
   - 过于离谱的行为（如想毁灭世界）→ 判定为不合理，给予严厉惩罚
   - 合理范围内的创新行为 → 可以接受，但收益适当降低

3. 奖励和消耗规律：
   - 合理的修炼行动：修为+5~30，寿命消耗1~3年
   - 合理的冒险行动：修为+10~50，寿命消耗2~5年
   - 合理的社交行动：修为+3~15，寿命消耗0~2年
   - 不合理的行动：修为减少10~50，寿命额外消耗5~20年，或直接导致死亡
   - 太离谱的行动可以直接判定玩家死亡（走火入魔、天谴等）

4. NPC互动规则（如果有NPC信息）：
   - 正面互动（帮助、赠送、合作）→ 关系度+5~30
   - 负面互动（攻击、抢夺、欺骗）→ 关系度-10~50
   - 如果NPC境界高于玩家，负面行为可能带来严重后果

5. 善恶度影响：
   - 行善（帮助他人、慷慨捐赠）→ 善恶度+1~10
   - 作恶（抢夺、欺骗、伤害无辜）→ 善恶度-1~10
   - 善恶度越高，天降机缘概率越大，NPC初始好感度越高
   - 善恶度过低（<-50）：正道NPC会主动疏远你，魔道事件概率增加
   - 善恶度过高（>50）：魔道NPC可能敌视你，但正道NPC更亲近

6. 道心值影响：
   - 坚定道心（坚持原则、克服诱惑）→ 道心值+1~5
   - 动摇道心（违背本心、随波逐流）→ 道心值-1~5
   - 道心值越高，突破成功率越高，修炼效率越高
   - 道心值越低（<30），走火入魔概率大幅增加
   - 道心值为0时，修仙之路彻底断绝，修为不再增长

7. 灵石收益：
   - 修炼/工作可获得灵石，数量1~5
   - 特殊奇遇可获得额外灵石5~20
   - 购买丹药、法宝、情报等需消耗灵石
   - 灵石为负数代表欠债状态

{_build_npc_prompt_section(nearby_npcs_info)}

【返回格式】
你必须严格按以下JSON格式返回，不要包含其他任何内容：
{{
  "reasonable": true 或 false,
  "description": "一段30-100字的生动剧情描述，描述行动的过程和结果",
  "lifespan_cost": 消耗的寿命年数（整数，>=0）,
  "cultivation_gain": 获得的修为值（整数，可为负数表示修为减少）,
  "good_evil_change": 善恶度变化值（整数，默认0，范围-10~10）,
  "dao_heart_change": 道心值变化值（整数，默认0，范围-5~5）,
  "spirit_stones_change": 灵石变化值（整数，默认0，范围-20~20）,
  "special_effect": "无" 或 "受伤" 或 "奇遇" 或 "顿悟" 或 "走火入魔",
  "is_death": false,
  "death_reason": "如果is_death为true，填写死亡原因",
  "npc_interaction": {{
    "npc_name": "涉及的NPC名称",
    "relationship_change": 关系变化值（整数）
  }}
}}
"""
    return prompt


def _build_npc_prompt_section(nearby_npcs_info: str) -> str:
    """构建NPC相关提示部分"""
    if not nearby_npcs_info:
        return ""
    return f"""
【附近相关NPC】
{nearby_npcs_info}
如果玩家的行动涉及这些NPC，请根据关系度给出合理的互动结果。
"""


def _build_user_message(action_text: str, event_context: str = "") -> str:
    """构造用户消息"""
    if event_context:
        return f"【事件背景】{event_context}\n\n【玩家的行动】{action_text}"
    return f"【玩家的行动】{action_text}"


def call_deepseek(action_text: str, player_realm_name: str,
                  player_school: str, realm_description: str,
                  nearby_npcs_info: str = "",
                  event_context: str = "",
                  user_id: int = None,
                  player_good_evil: int = 0, player_dao_heart: int = 50,
                  player_spirit_stones: int = 0) -> Optional[dict]:
    """
    调用 DeepSeek API 判定玩家行动
    返回解析后的JSON字典，失败时返回None

    参数:
        action_text: 玩家的行动描述
        player_realm_name: 玩家当前境界名称
        player_school: 玩家当前学校名称
        realm_description: 境界描述
        nearby_npcs_info: 附近NPC信息（可选）
        event_context: 事件背景描述（可选）
        user_id: 用户ID（用于检测调用上限）
        player_good_evil: 当前善恶度
        player_dao_heart: 当前道心值
        player_spirit_stones: 当前灵石数量
    """
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "your-api-key-here":
        return _get_mock_result(action_text, player_realm_name)

    if user_id:
        increment_deepseek_calls(user_id)
        if not check_deepseek_limit(user_id):
            return _get_mock_result(action_text, player_realm_name)

    try:
        system_prompt = _build_system_prompt(
            player_realm_name, player_school, realm_description, nearby_npcs_info,
            player_good_evil, player_dao_heart, player_spirit_stones
        )
        user_message = _build_user_message(action_text, event_context)

        response = requests.post(
            DEEPSEEK_API_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.8,
                "max_tokens": 500
            },
            timeout=DEEPSEEK_TIMEOUT
        )

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            # 提取JSON部分（防止DeepSeek返回了额外文本）
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
            return None
        else:
            # API调用失败时使用本地模拟
            return _get_mock_result(action_text, player_realm_name)

    except Exception:
        # 异常时使用本地模拟
        return _get_mock_result(action_text, player_realm_name)


def _get_mock_result(action_text: str, realm_name: str) -> dict:
    """
    当API不可用时的本地模拟判定
    基于关键词进行简单的合理/不合理判断
    """
    action_lower = action_text.lower()

    # 不合理行为的检测关键词
    unreasonable_keywords = [
        "毁灭", "屠", "杀光", "灭世", "无敌", "成仙", "飞升",
        "destroy", "kill all", "god mode"
    ]
    is_unreasonable = any(kw in action_text for kw in unreasonable_keywords)

    if is_unreasonable:
        return {
            "reasonable": False,
            "description": f"天道感应到你的狂妄之言，降下天雷惩戒！以你{realm_name}的境界，竟敢口出狂言，实属不智。",
            "lifespan_cost": 20,
            "cultivation_gain": -30,
            "good_evil_change": -5,
            "dao_heart_change": -3,
            "spirit_stones_change": 0,
            "special_effect": "走火入魔",
            "is_death": False,
            "death_reason": "",
            "npc_interaction": None
        }

    # 合理的行动
    import random
    gain = random.randint(5, 25)
    cost = random.randint(1, 3)
    ge_change = random.randint(-2, 3)
    dh_change = random.randint(-1, 2)
    ss_change = random.randint(1, 5)
    effects = ["无", "无", "无", "奇遇", "顿悟"]
    effect = random.choice(effects)
    if effect == "奇遇":
        gain += 20
        ss_change += random.randint(5, 15)
    elif effect == "顿悟":
        gain *= 2
        dh_change += 2

    return {
        "reasonable": True,
        "description": f"你{action_text}。天地灵气随之涌动，你的修为略有精进。",
        "lifespan_cost": cost,
        "cultivation_gain": gain,
        "good_evil_change": ge_change,
        "dao_heart_change": dh_change,
        "spirit_stones_change": ss_change,
        "special_effect": effect,
        "is_death": False,
        "death_reason": "",
        "npc_interaction": None
    }


def _get_relationship_tier_name(relationship: int) -> str:
    """根据好感度值返回对应的挡位名称"""
    from .config import NPC_RELATIONSHIP_TIERS
    for tier in NPC_RELATIONSHIP_TIERS:
        low, high = tier["range"]
        if low <= relationship <= high:
            return tier["name"]
    return "中立"


def _format_conversation_history(history: list, max_exchanges: int = 15) -> str:
    """将对话历史格式化为文本"""
    if not history:
        return ""
    lines = []
    count = 0
    for msg in history[-max_exchanges * 2:]:
        sender = "玩家" if msg["sender"] == "player" else msg["npc_name"] if "npc_name" in msg else "对方"
        lines.append(f"{sender}: {msg['content']}")
        count += 1
    return "\n".join(lines)


def _get_preset_adult_reply(relationship: int, tier_name: str) -> dict:
    """根据好感度获取预设的成人内容回复"""
    import random
    from .config import NPC_PRESET_REPLIES_ADULT

    if relationship >= 61:
        category = "亲密"
    elif relationship >= 31:
        category = "暧昧"
    elif relationship >= 1:
        category = "含蓄"
    elif relationship >= -20:
        category = "拒绝"
    else:
        category = "愤怒"

    replies = NPC_PRESET_REPLIES_ADULT.get(category, NPC_PRESET_REPLIES_ADULT["拒绝"])
    reply = random.choice(replies)

    # 好感度变化
    if category == "亲密":
        rel_change = random.randint(0, 5)
    elif category == "暧昧":
        rel_change = random.randint(-2, 3)
    elif category == "含蓄":
        rel_change = random.randint(-5, 0)
    elif category == "拒绝":
        rel_change = random.randint(-10, -3)
    else:
        rel_change = random.randint(-20, -10)

    return {
        "reply": reply,
        "relationship_change": rel_change,
        "cultivation_change": 0,
        "special_effect": "无",
        "is_adult": True,
        "tone_category": category
    }


def _build_npc_interaction_prompt(
    npc_name: str, npc_title: str, npc_realm: str, npc_realm_level: int,
    npc_relationship: int, npc_gender: str, npc_backstory: str,
    player_realm_name: str, player_school: str, player_realm_level: int,
    player_name: str, player_career_path: str,
    conversation_history_text: str,
    is_married: bool = False, is_sworn_brother: bool = False
) -> str:
    """构建NPC交流系统提示词"""
    tier_name = _get_relationship_tier_name(npc_relationship)
    gender_prompt = "他是一个" if npc_gender == "male" else "她是一个"

    realm_diff = npc_realm_level - player_realm_level
    if realm_diff > 2:
        power_relation = "修为远高于你，态度中可以带有居高临下的俯视感"
    elif realm_diff > 0:
        power_relation = "修为略高于你，态度中带有一点前辈的优越感"
    elif realm_diff == 0:
        power_relation = "修为与你相当，以平等的态度对待你"
    elif realm_diff >= -2:
        power_relation = "修为略低于你，态度中带有一点敬意"
    else:
        power_relation = "修为远低于你，语气中带有敬畏"

    backstory_info = npc_backstory if npc_backstory else "暂无特别背景"

    player_role = f"{player_school}的{player_realm_name}"
    if player_career_path == "飞升":
        player_role = f"{player_school}的{player_realm_name}（选择继续深造考研飞升）"
    elif player_career_path == "上班":
        player_role = f"{player_school}的{player_realm_name}（选择进入修仙界职场上班）"

    history_section = ""
    if conversation_history_text:
        history_section = f"""
【历史对话上下文（最近的对话记录）】
{conversation_history_text}
请注意：NPC的记忆和历史对话上下文中保持一致性，不要前后矛盾。
"""

    # 特殊关系描述
    special_relation_note = ""
    if is_married:
        special_relation_note = f"""
【特殊关系：道侣】
{npc_name}是你的道侣（妻子/丈夫），你们已经正式结为双修伴侣，感情深厚。
作为你的道侣，{npc_name}对你的说话口吻应该是亲昵、温柔的，如同夫妻一般。
{npc_name}会关心你的修炼进展、身体状况，会和你分享修炼心得，也会在你遇到困难时全力支持你。
当{npc_name}与你交谈时，应当以伴侣的身份回应，语气亲昵，可以称呼你为"夫君"（若{npc_name}为女性）或"娘子"（若{npc_name}为男性）。
已经结为道侣，不再需要判断是否愿意结为道侣（want_be_partner始终为false）。
"""
    elif is_sworn_brother:
        special_relation_note = f"""
【特殊关系：结拜兄弟】
{npc_name}是你的结拜兄弟，你们已经正式结拜，肝胆相照、情同手足。
作为你的结拜兄弟，{npc_name}对你说话的口吻应该是兄弟般的豪爽、真诚。
{npc_name}会关心你的修炼进展，会和你分享修炼资源，也会在你遇到困难时两肋插刀。
当{npc_name}与你交谈时，应当以兄弟的身份回应，语气真诚豪爽，可以称呼你为"兄弟"或"贤弟"。
"""

    prompt = f"""你正在扮演一个修仙世界中的NPC角色。请根据以下角色设定进行回复。

【NPC基本信息】
名称：{npc_name}
称号：{npc_title}
境界：{npc_realm}（等级{npc_realm_level}）
性别：{'男' if npc_gender == 'male' else '女'}
背景故事：{backstory_info}

【NPC与玩家的关系】
当前好感度：{npc_relationship}（{tier_name}阶段）
{gender_prompt}修为与你的差距：{power_relation}
{special_relation_note}
【玩家信息】
名称：{player_name}
身份：{player_role}

【好感度对应的说话风格】
- 仇视(-100~-50)：冷嘲热讽，充满敌意和杀意
- 厌恶(-49~-20)：冷漠疏离，懒得理会
- 冷淡(-19~0)：敷衍客套，保持距离
- 中立(1~30)：礼貌礼貌，公式化交流
- 友善(31~60)：温和热情，愿意分享
- 亲近(61~80)：亲密关怀，像朋友一样
- 至交(81~100)：无话不谈，完全信任

{history_section}
【回复规则】
1. 你必须完全以{npc_name}的身份和口吻回复，不要跳出角色
2. 回复长度控制在20-80字之间
3. 根据好感度调整态度和语气
4. 如果玩家行为不当（无礼、轻浮、攻击性等），好感度会下降
5. 如果玩家表现友善、尊重或帮助，好感度会上升
6. 注意修为差距：修为高者对修为低者可以傲慢，修为低者对修为高者应当尊敬
7. 如果玩家涉及成人内容，请根据好感度做出合理回应（亲密阶段可以暧昧回应，低好感度则会愤怒拒绝）
8. 保持角色性格一致性
9. 记住玩家是一个穿越/重生到修仙世界的人，以{player_name}的身份在这个世界修行

【道侣意愿判定规则】
- 如果已有特殊关系（道侣/结拜），则不需要再判断道侣意愿
- 当好感度达到80以上（至交阶段），且对方（玩家）行为友善、表现出深厚情谊时，
  你（NPC）可能会在心中产生与对方结为道侣（双修伴侣）的意愿
- 道侣意愿必须是NPC发自内心的想法，而不是玩家主动询问的结果
- 不要主动在回复中告知玩家你想成为道侣，只是内心有这种意愿
- 如果玩家明确表白或求婚，你可以根据好感度做出合理回应
  - 好感度≥80且关系良好：愿意成为道侣（want_be_partner=true）
  - 好感度<80：委婉拒绝或表示需要更多时间

【返回格式】
你必须严格按以下JSON格式返回，不要包含其他任何内容：
{{
  "reply": "NPC的回复内容（20-80字，以NPC的第一人称口吻）",
  "relationship_change": 好感度变化值（整数，范围-20到20）,
  "cultivation_change": 玩家修为变化（整数，范围-10到30，普通对话为0，悟道论道可增加）,
  "special_effect": "无" 或 "顿悟" 或 "指点" 或 "机缘",
  "is_adult": true或false（是否涉及成人/暧昧内容）,
  "want_be_partner": true或false（NPC是否内心愿意与玩家结为道侣，默认false）
}}
"""
    return prompt


def _get_mock_npc_reply(npc_name: str, npc_relationship: int) -> dict:
    """API不可用时的NPC回复模拟"""
    import random
    tier_name = _get_relationship_tier_name(npc_relationship)

    mock_replies = {
        "仇视": ["哼，你还有脸出现在我面前？", "滚远点，否则休怪我无情！", "看见你就觉得恶心。"],
        "厌恶": ["有什么事？没事别来烦我。", "……不愿与你多言。", "你走吧，我不想和你说话。"],
        "冷淡": ["道友有何贵干？", "嗯，知道了。", "如果没有别的事，我先走了。"],
        "中立": ["道友有什么事可以直说。", "嗯，我在听，你继续。", "原来如此，道友请便。"],
        "友善": ["哈哈，你来得正好！", "你我之间不必客气。", "能见到你真是太好了！"],
        "亲近": ["你来了？我正想找你呢。", "有你在我就放心了。", "最近修炼可还顺利？有什么需要帮忙的吗？"],
        "至交": ["你我之间何须多言？", "你的事就是我的事。", "能遇到你这样的知己，此生无憾。"]
    }

    replies = mock_replies.get(tier_name, mock_replies["中立"])
    reply = random.choice(replies)

    # 好感度变化
    rel_change = random.randint(-2, 5)
    cult_change = random.randint(0, 5)

    effects = ["无", "无", "无", "指点"]
    effect = random.choice(effects)

    # 高好感度时小概率产生道侣意愿
    want_partner = False
    if npc_relationship >= 80 and random.random() < 0.05:
        want_partner = True

    return {
        "reply": reply,
        "relationship_change": rel_change,
        "cultivation_change": cult_change,
        "special_effect": effect,
        "is_adult": False,
        "want_be_partner": want_partner
    }


def call_npc_interaction(
    npc_name: str, npc_title: str, npc_realm: str, npc_realm_level: int,
    npc_relationship: int, npc_gender: str, npc_backstory: str,
    player_realm_name: str, player_school: str, player_realm_level: int,
    player_name: str, player_career_path: str,
    player_message: str, conversation_history: list = None,
    user_id: int = None,
    is_married: bool = False, is_sworn_brother: bool = False
) -> dict:
    """
    调用DeepSeek进行NPC交流互动

    参数:
        npc_name: NPC名称
        npc_title: NPC称号
        npc_realm: NPC境界名称
        npc_realm_level: NPC境界等级
        npc_relationship: 当前好感度
        npc_gender: NPC性别
        npc_backstory: NPC背景故事
        player_realm_name: 玩家境界名称
        player_school: 玩家学校名称
        player_realm_level: 玩家境界等级
        player_name: 玩家名称
        player_career_path: 玩家职业路线（None/"飞升"/"上班"）
        player_message: 玩家发送的消息
        conversation_history: 历史对话记录列表
        user_id: 用户ID（用于检测调用上限）
        is_married: 是否与玩家结为道侣
        is_sworn_brother: 是否与玩家结为兄弟

    返回:
        dict: {reply, relationship_change, cultivation_change, special_effect, is_adult}
    """
    # 检测是否涉及成人/暧昧内容（关键词匹配）
    adult_keywords = ["双修", "合欢", "洞房", "鱼水之欢", "云雨", "共枕", "侍寝",
                      "make love", "sleep together", "床", "抱紧", "亲亲", "吻"]
    is_adult_content = any(kw in player_message for kw in adult_keywords)

    if is_adult_content:
        return _get_preset_adult_reply(npc_relationship, _get_relationship_tier_name(npc_relationship))

    # 格式化对话历史
    history_text = _format_conversation_history(conversation_history) if conversation_history else ""

    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "your-api-key-here":
        return _get_mock_npc_reply(npc_name, npc_relationship)

    if user_id:
        increment_deepseek_calls(user_id)
        if not check_deepseek_limit(user_id):
            return _get_mock_npc_reply(npc_name, npc_relationship)

    try:
        system_prompt = _build_npc_interaction_prompt(
            npc_name, npc_title, npc_realm, npc_realm_level,
            npc_relationship, npc_gender, npc_backstory,
            player_realm_name, player_school, player_realm_level,
            player_name, player_career_path,
            history_text,
            is_married=is_married, is_sworn_brother=is_sworn_brother
        )

        response = requests.post(
            DEEPSEEK_API_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"你对{npc_name}说：{player_message}"}
                ],
                "temperature": 0.85,
                "max_tokens": 400
            },
            timeout=DEEPSEEK_TIMEOUT
        )

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                parsed = json.loads(json_str)
                parsed["is_adult"] = parsed.get("is_adult", False)
                parsed["want_be_partner"] = parsed.get("want_be_partner", False)
                return parsed
            return _get_mock_npc_reply(npc_name, npc_relationship)
        else:
            return _get_mock_npc_reply(npc_name, npc_relationship)

    except Exception:
        return _get_mock_npc_reply(npc_name, npc_relationship)
