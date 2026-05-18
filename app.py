"""Flask Web 应用入口
提供修仙小游戏的Web界面和API接口
"""

import os
import hashlib
import random
from typing import Optional
from flask import Flask, render_template, session, request, jsonify

from game.engine import GameEngine, load_existing_game, create_new_game
from game.database import (
    init_database, create_user, get_user_by_username, get_user_by_id,
    get_npc_event_history, get_npc_by_id, get_conversation_history,
    delete_game_state, delete_user_npcs, set_npc_married,
    set_npc_sworn_brother, get_sworn_brother_npc, get_global_events,
    add_global_event,
    add_relationship_event, is_admin_user, get_all_users,
    update_user_deepseek_limit, change_password, update_last_active,
    get_spirit_stones_ranking
)
from game.npc_generator import get_npcs_for_display
from game.modules.exam import generate_exam_question, evaluate_exam_answer, generate_subject_question, evaluate_subject_answer
from game.modules.minigame import (
    get_available_games, start_game, execute_action, apply_giveup_penalty
)
from game.life_events import get_event_by_id, resolve_event_option
from game.achievements import ACHIEVEMENTS, check_all_achievements
from game.database import get_all_achievements, get_player_achievements

app = Flask(__name__, template_folder="templates", static_folder="static")
# 随机密钥，用于session加密（本地游戏，固定即可）
app.secret_key = "sk-ee323663b0dc44d4ba637aec3829c22b"

# 确保数据库已初始化
init_database()


def get_engine() -> Optional[GameEngine]:
    """从session中获取user_id并加载游戏引擎"""
    user_id = session.get("user_id")
    if not user_id:
        return None
    update_last_active(user_id)
    return load_existing_game(user_id)


def enrich_state(state: dict) -> dict:
    """给游戏状态增加username字段"""
    state["username"] = session.get("username", "")
    return state


# ==================== 页面路由 ====================


@app.route("/")
def index():
    """主游戏页面"""
    user_id = session.get("user_id")
    if not user_id:
        return render_template("game.html", initial_state={"phase": "login"})
    engine = get_engine()
    if not engine:
        return render_template("game.html", initial_state={"phase": "login"})
    state = engine.get_game_state()
    enrich_state(state)
    return render_template("game.html", initial_state=state)


# ==================== 用户认证 API ====================


@app.route("/api/register", methods=["POST"])
def register():
    """用户注册"""
    data = request.get_json()
    username = (data.get("username", "") or "").strip()
    password = data.get("password", "") or ""

    if len(username) < 2 or len(username) > 20:
        return jsonify({"success": False, "message": "用户名长度需在2-20个字符之间"})
    if len(password) < 4:
        return jsonify({"success": False, "message": "密码长度至少4个字符"})

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user_id = create_user(username, password_hash)
    if user_id is None:
        return jsonify({"success": False, "message": "用户名已存在"})

    session["user_id"] = user_id
    session["username"] = username
    engine = create_new_game(user_id)
    state = engine.get_game_state()
    enrich_state(state)
    return jsonify({
        "success": True,
        "message": "注册成功",
        "game_state": state
    })


@app.route("/api/login", methods=["POST"])
def login():
    """用户登录"""
    data = request.get_json()
    username = (data.get("username", "") or "").strip()
    password = data.get("password", "") or ""

    if not username or not password:
        return jsonify({"success": False, "message": "请输入用户名和密码"})

    user = get_user_by_username(username)
    if not user:
        return jsonify({"success": False, "message": "用户名或密码错误"})

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if user["password_hash"] != password_hash:
        return jsonify({"success": False, "message": "用户名或密码错误"})

    session["user_id"] = user["id"]
    session["username"] = username
    # sqlite3.Row 不支持 .get()，用 dict() 转换后再访问
    user_dict = dict(user)
    session["is_admin"] = bool(user_dict.get("is_admin", 0))
    update_last_active(user["id"])
    if user_dict.get("deepseek_calls_today", 0) > 0 and user_dict.get("deepseek_daily_limit"):
        from game.database import reset_deepseek_calls
        reset_deepseek_calls(user["id"])
    engine = load_existing_game(user["id"])
    state = engine.get_game_state()
    enrich_state(state)
    return jsonify({
        "success": True,
        "message": "登录成功",
        "game_state": state
    })


@app.route("/api/logout", methods=["POST"])
def logout():
    """用户登出"""
    session.clear()
    return jsonify({"success": True, "message": "已登出"})


@app.route("/api/check_session", methods=["GET"])
def check_session():
    """检查当前会话状态"""
    user_id = session.get("user_id")
    username = session.get("username")
    if user_id and username:
        is_admin = session.get("is_admin", False)
        return jsonify({
            "logged_in": True,
            "user_id": user_id,
            "username": username,
            "is_admin": is_admin
        })
    return jsonify({"logged_in": False})


# ==================== API 路由 ====================


# ==================== 排行榜 API ====================

@app.route("/api/ranking/spirit_stones", methods=["GET"])
def spirit_stones_ranking():
    """获取灵石排行榜"""
    ranking = get_spirit_stones_ranking(20)
    return jsonify({"ranking": ranking})


# ==================== 境界随机事件 API ====================

@app.route("/api/action/realm_event", methods=["POST"])
def realm_event_choice():
    """处理境界随机事件的选择"""
    data = request.get_json()
    event_name = data.get("event_name", "")
    choice_index = data.get("choice_index", 0)
    engine = get_engine()
    if not engine:
        return jsonify({"error": "未登录"}), 401
    result = engine._apply_realm_event_choice(event_name, choice_index)
    if "game_state" in result:
        enrich_state(result["game_state"])
    return jsonify(result)


# ==================== 管理后台 API（密码管理） ====================

@app.route("/api/admin/change_password", methods=["POST"])
def admin_change_password():
    """管理员修改用户密码"""
    if not session.get("is_admin"):
        return jsonify({"error": "无权限"}), 403
    data = request.get_json()
    target_user_id = data.get("user_id")
    new_password = data.get("new_password", "")
    if not target_user_id or len(new_password) < 4:
        return jsonify({"error": "参数不完整或密码长度不足"}), 400
    new_hash = hashlib.sha256(new_password.encode()).hexdigest()
    if change_password(target_user_id, new_hash):
        return jsonify({"success": True, "message": "密码已重置"})
    return jsonify({"error": "密码重置失败"}), 500


@app.route("/admin")
def admin_page():
    """管理后台页面"""
    if not session.get("is_admin"):
        return render_template("game.html")
    from game.config import DEEPSEEK_DAILY_LIMIT_DEFAULT
    return render_template("admin.html",
                           username=session.get("username"),
                           default_limit=DEEPSEEK_DAILY_LIMIT_DEFAULT)


@app.route("/api/admin/users", methods=["GET"])
def admin_get_users():
    """获取所有用户列表（仅管理员）"""
    if not session.get("is_admin"):
        return jsonify({"error": "无权限"}), 403
    users = get_all_users()
    from datetime import datetime
    now = datetime.utcnow()
    for u in users:
        if u.get("last_active"):
            try:
                last = datetime.fromisoformat(u["last_active"].rstrip("Z"))
                diff = (now - last).total_seconds()
                u["is_online"] = diff < 300
                u["online_minutes"] = round(diff / 60, 1) if not u["is_online"] else 0
            except Exception:
                u["is_online"] = False
                u["online_minutes"] = 0
        else:
            u["is_online"] = False
            u["online_minutes"] = 0
    try:
        return jsonify(users)
    except TypeError:
        import json
        safe_json = json.dumps(users, ensure_ascii=False, default=str)
        return app.response_class(safe_json, mimetype="application/json")


@app.route("/api/admin/set_deepseek_limit", methods=["POST"])
def admin_set_deepseek_limit():
    """设置用户DeepSeek调用上限（仅管理员）"""
    if not session.get("is_admin"):
        return jsonify({"error": "无权限"}), 403
    data = request.get_json()
    user_id = data.get("user_id")
    new_limit = data.get("limit")
    if not user_id or new_limit is None:
        return jsonify({"error": "参数不完整"}), 400
    if update_user_deepseek_limit(user_id, int(new_limit)):
        return jsonify({"success": True, "message": "已更新"})
    return jsonify({"error": "更新失败"}), 500


@app.route("/api/admin/clear_all_data", methods=["POST"])
def admin_clear_all_data():
    """一键清理所有用户游戏数据（仅管理员）"""
    if not session.get("is_admin"):
        return jsonify({"error": "无权限"}), 403
    from game.database import clear_all_user_data
    result = clear_all_user_data()
    if result.get("success"):
        return jsonify({"success": True, "message": "所有用户数据已清除"})
    else:
        return jsonify({"error": result.get("message", "清除失败")}), 500


@app.route("/api/global_events", methods=["GET"])
def global_events():
    """获取全局事件列表"""
    events = get_global_events(30)
    return jsonify(events)


@app.route("/api/start", methods=["POST"])
def new_game():
    """开始新游戏（重置当前用户的游戏进度）"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "未登录"}), 401
    delete_user_npcs(user_id)
    delete_game_state(user_id)
    engine = create_new_game(user_id)
    state = engine.get_game_state()
    enrich_state(state)
    return jsonify(state)


@app.route("/api/state", methods=["GET"])
def get_state():
    """获取当前游戏状态"""
    engine = get_engine()
    if not engine:
        return jsonify({"error": "未登录"}), 401
    state = engine.get_game_state()
    enrich_state(state)
    return jsonify(state)


@app.route("/api/prelude", methods=["POST"])
def prelude_choice():
    """处理序章选择"""
    data = request.get_json()
    choice_index = data.get("choice_index", 0)
    engine = get_engine()
    if not engine:
        return jsonify({"error": "未登录"}), 401
    result = engine.handle_prelude_choice(choice_index)
    engine.save()
    enrich_state(result)
    return jsonify(result)


@app.route("/api/action/preset", methods=["POST"])
def preset_action():
    """执行预设事件"""
    data = request.get_json()
    event_name = data.get("event_name", "")
    engine = get_engine()
    if not engine:
        return jsonify({"error": "未登录"}), 401
    result = engine.execute_preset_event(event_name)
    engine.save()
    enrich_state(result)
    if result.get("realm_random_event"):
        username = session.get("username", "匿名")
        event_desc = result["realm_random_event"].get("event_description", "")
        short_desc = (event_desc[:30] + "...") if len(event_desc) > 30 else event_desc
        add_global_event(username, "奇遇", f"{username}触发奇遇：{short_desc}")
    if result.get("npc_encounter"):
        username = session.get("username", "匿名")
        add_global_event(username, "邂逅", f"{username}遭遇NPC邂逅！")
    return jsonify(result)


@app.route("/api/career/choose", methods=["POST"])
def career_choose():
    """选择职业路线（化神/大学后）"""
    engine = get_engine()
    if not engine:
        return jsonify({"error": "未登录"}), 401
    data = request.get_json()
    path = data.get("path", "")
    if path not in ("飞升", "上班"):
        return jsonify({"error": "无效的路线选择"}), 400
    result = engine.choose_career(path)
    if not result["success"]:
        return jsonify(result), 400
    engine.save()
    state = enrich_state(engine.get_game_state())
    return jsonify({"success": True, "career_result": result, "game_state": state})


@app.route("/api/action/custom", methods=["POST"])
def custom_action():
    """执行自定义行动（调用DeepSeek）"""
    data = request.get_json()
    action_text = data.get("action_text", "")
    engine = get_engine()
    if not engine:
        return jsonify({"error": "未登录"}), 401
    result = engine.execute_custom_action(action_text)
    engine.save()
    enrich_state(result)
    return jsonify(result)


@app.route("/api/exam/start", methods=["POST"])
def exam_start():
    """开始模拟考试：生成题目"""
    engine = get_engine()
    if not engine:
        return jsonify({"error": "未登录"}), 401
    question = generate_exam_question(engine.player, session.get("user_id"))
    return jsonify({"success": True, "question": question})


@app.route("/api/exam/submit", methods=["POST"])
def exam_submit():
    """提交考试答案：评分并应用结果"""
    engine = get_engine()
    if not engine:
        return jsonify({"error": "未登录"}), 401
    data = request.get_json()
    question = data.get("question")
    answer = (data.get("answer") or "").strip()
    if not question or not answer:
        return jsonify({"error": "参数不完整"}), 400
    result = evaluate_exam_answer(engine.player, question, answer, session.get("user_id"))
    engine.player.exam_count += 1
    engine.player.add_log(
        f"📝 模拟考试：{result['comment']}（得分：{result['score']}分，修为 +{result['cultivation_gain']}）"
        + (f"，{result['attr_text']}" if result.get("attr_text") else "")
    )
    engine.save()
    state = engine.get_game_state()
    enrich_state(state)
    return jsonify({"success": True, "result": result, "game_state": state})


@app.route("/api/exam/subject", methods=["POST"])
def exam_subject():
    """开始科目学习：根据科目生成题目"""
    engine = get_engine()
    if not engine:
        return jsonify({"error": "未登录"}), 401
    data = request.get_json()
    subject = data.get("subject")
    if not subject:
        return jsonify({"error": "参数不完整"}), 400
    question = generate_subject_question(engine.player, subject, session.get("user_id"))
    return jsonify({"success": True, "question": question})


@app.route("/api/exam/subject_judge", methods=["POST"])
def exam_subject_judge():
    """提交科目答案：AI判断对错并应用结果"""
    engine = get_engine()
    if not engine:
        return jsonify({"error": "未登录"}), 401
    data = request.get_json()
    question = data.get("question")
    answer = (data.get("answer") or "").strip()
    if not question or not answer:
        return jsonify({"error": "参数不完整"}), 400
    result = evaluate_subject_answer(engine.player, question, answer, session.get("user_id"))
    engine.player.exam_count += 1
    correct_text = "✅ 回答正确！" if result["correct"] else "❌ 回答错误"
    log_msg = (
        f"📖 {result.get('subject', '科目')}学习：{correct_text}"
        f"（修为 +{result['cultivation_gain']}）"
        + (f"，{result['attr_text']}" if result.get("attr_text") else "")
    )
    engine.player.add_log(log_msg)
    random_event = None
    if random.random() < 0.1:
        random_event = engine._trigger_random_event()
    engine.save()
    state = engine.get_game_state()
    enrich_state(state)
    return jsonify({"success": True, "result": result, "game_state": state, "random_event": random_event})


@app.route("/api/minigame/list", methods=["GET"])
def minigame_list():
    return jsonify({"games": get_available_games()})


@app.route("/api/minigame/start", methods=["POST"])
def minigame_start():
    engine = get_engine()
    if not engine:
        return jsonify({"error": "未登录"}), 401
    data = request.get_json()
    game_name = data.get("game_name")
    if not game_name:
        return jsonify({"error": "参数不完整"}), 400
    state = start_game(game_name, engine.player)
    if state is None:
        return jsonify({"error": "游戏不存在"}), 404
    return jsonify({"success": True, "game_state_v2": state})


@app.route("/api/minigame/action", methods=["POST"])
def minigame_action():
    engine = get_engine()
    if not engine:
        return jsonify({"error": "未登录"}), 401
    data = request.get_json()
    game_name = data.get("game_name")
    game_state_v2 = data.get("game_state_v2")
    action = data.get("action", "")
    if not game_name or not game_state_v2:
        return jsonify({"error": "参数不完整"}), 400
    result = execute_action(game_name, engine.player, game_state_v2, action)
    if result.get("ended"):
        engine.player.minigame_count += 1
    engine.save()
    state = engine.get_game_state()
    enrich_state(state)
    return jsonify({"success": True, "result": result, "game_state": state, "game_state_v2": game_state_v2})


@app.route("/api/minigame/giveup", methods=["POST"])
def minigame_giveup():
    engine = get_engine()
    if not engine:
        return jsonify({"error": "未登录"}), 401
    penalty = apply_giveup_penalty(engine.player)
    engine.player.add_log(f"🏳️ 放弃游戏，受到惩罚：{penalty['description']}")
    engine.save()
    state = engine.get_game_state()
    enrich_state(state)
    return jsonify({"success": True, "penalty": penalty, "game_state": state})


@app.route("/api/npcs", methods=["GET"])
def get_npcs():
    """获取当前用户的所有NPC列表"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"npcs": []})
    npcs = get_npcs_for_display(user_id)
    return jsonify({"npcs": npcs})


@app.route("/api/npc/<int:npc_id>", methods=["GET"])
def get_npc_detail(npc_id: int):
    """获取NPC详细信息及互动历史"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "未登录"}), 401
    npc = get_npc_by_id(npc_id)
    if not npc:
        return jsonify({"error": "NPC不存在"}), 404
    if npc["user_id"] != user_id:
        return jsonify({"error": "无权访问"}), 403
    history = get_npc_event_history(user_id, npc_id)
    return jsonify({
        "npc": dict(npc),
        "history": [dict(e) for e in history]
    })


@app.route("/api/npc/<int:npc_id>/conversations", methods=["GET"])
def get_npc_conversations(npc_id: int):
    """获取NPC对话历史"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "未登录"}), 401
    npc = get_npc_by_id(npc_id)
    if not npc:
        return jsonify({"error": "NPC不存在"}), 404
    if npc["user_id"] != user_id:
        return jsonify({"error": "无权访问"}), 403
    conversations = get_conversation_history(user_id, npc_id, 50)
    return jsonify({
        "conversations": [dict(c) for c in conversations]
    })


@app.route("/api/npc/<int:npc_id>/interact", methods=["POST"])
def interact_npc(npc_id: int):
    """与NPC主动交流"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    npc = get_npc_by_id(npc_id)
    if not npc:
        return jsonify({"error": "NPC不存在"}), 404
    if npc["user_id"] != user_id:
        return jsonify({"error": "无权访问"}), 403

    data = request.get_json()
    message = data.get("message", "")
    if not message.strip():
        return jsonify({"success": False, "message": "请输入要说的话"})

    engine = get_engine()
    if not engine:
        return jsonify({"error": "游戏尚未开始"}), 400

    result = engine.interact_with_npc(npc_id, message)
    if "game_state" in result:
        enrich_state(result["game_state"])
    return jsonify(result)


@app.route("/api/npc/<int:npc_id>/marry", methods=["POST"])
def marry_npc(npc_id: int):
    """与NPC结婚（对方主动求婚后的确认）"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    engine = get_engine()
    if not engine:
        return jsonify({"error": "游戏尚未开始"}), 400

    result = engine.confirm_marriage(npc_id)
    if "game_state" in result:
        enrich_state(result["game_state"])
    return jsonify(result)


@app.route("/api/npc/<int:npc_id>/become_partner", methods=["POST"])
def become_partner(npc_id: int):
    """与NPC结为道侣（100%成功）"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    npc = get_npc_by_id(npc_id)
    if not npc:
        return jsonify({"error": "NPC不存在"}), 404
    if npc["user_id"] != user_id:
        return jsonify({"error": "无权访问"}), 403
    if not npc["is_alive"]:
        return jsonify({"error": f"{npc['name']}已不在人世"}), 400
    if npc["gender"] != "female":
        return jsonify({"error": f"{npc['name']}是男性，无法结为道侣"}), 400
    if npc["is_married"]:
        return jsonify({"error": f"{npc['name']}已是他人道侣"}), 400

    from game.config import NPC_PARTNER_RELATIONSHIP_MIN, PARTNER_BECOME_RELATIONSHIP_BONUS
    if npc["relationship"] < NPC_PARTNER_RELATIONSHIP_MIN:
        return jsonify({"error": f"好感度不足，需≥{NPC_PARTNER_RELATIONSHIP_MIN}"}), 400

    engine = get_engine()
    if not engine:
        return jsonify({"error": "游戏尚未开始"}), 400

    set_npc_married(npc_id)
    engine.player.add_log(f"💞 你与{npc['name']}结为道侣，从此双宿双飞！")
    add_relationship_event(
        user_id=user_id, npc_id=npc_id, event_type="结为道侣",
        description=f"与{npc['name']}正式结为道侣",
        relationship_change=PARTNER_BECOME_RELATIONSHIP_BONUS + 20,
        player_realm=engine.player.get_realm_name(),
        player_realm_level=engine.player.realm_level
    )
    username = session.get("username", "")
    add_global_event(username, "结为道侣",
        f"💞 {username}与{npc['name']}结为道侣！")

    engine.save()
    return jsonify({
        "success": True,
        "message": f"你与{npc['name']}正式结为道侣！",
        "game_state": enrich_state(engine.get_game_state())
    })


@app.route("/api/npc/<int:npc_id>/become_sworn_brother", methods=["POST"])
def become_sworn_brother(npc_id: int):
    """与男性NPC结为结拜兄弟（100%成功）"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    npc = get_npc_by_id(npc_id)
    if not npc:
        return jsonify({"error": "NPC不存在"}), 404
    if npc["user_id"] != user_id:
        return jsonify({"error": "无权访问"}), 403
    if not npc["is_alive"]:
        return jsonify({"error": f"{npc['name']}已不在人世"}), 400
    if npc["gender"] != "male":
        return jsonify({"error": "只有男性角色可以结拜"}), 400
    if npc["is_sworn_brother"]:
        return jsonify({"error": f"你已与{npc['name']}结拜"}), 400

    from game.config import NPC_PARTNER_RELATIONSHIP_MIN, PARTNER_BECOME_RELATIONSHIP_BONUS
    if npc["relationship"] < NPC_PARTNER_RELATIONSHIP_MIN:
        return jsonify({"error": f"好感度不足，需≥{NPC_PARTNER_RELATIONSHIP_MIN}"}), 400

    engine = get_engine()
    if not engine:
        return jsonify({"error": "游戏尚未开始"}), 400

    set_npc_sworn_brother(npc_id)
    engine.player.add_log(f"🤝 你与{npc['name']}结为兄弟，从此肝胆相照！")
    add_relationship_event(
        user_id=user_id, npc_id=npc_id, event_type="结拜",
        description=f"与{npc['name']}正式结为兄弟",
        relationship_change=PARTNER_BECOME_RELATIONSHIP_BONUS + 20,
        player_realm=engine.player.get_realm_name(),
        player_realm_level=engine.player.realm_level
    )
    username = session.get("username", "")
    add_global_event(username, "结拜",
        f"🤝 {username}与{npc['name']}结为兄弟！")

    engine.save()
    return jsonify({
        "success": True,
        "message": f"你与{npc['name']}正式结为兄弟！从此共享修为，肝胆相照！",
        "game_state": enrich_state(engine.get_game_state())
    })


@app.route("/api/npc/<int:npc_id>/meet", methods=["POST"])
def meet_npc(npc_id: int):
    """与NPC见面"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    engine = get_engine()
    if not engine:
        return jsonify({"error": "游戏尚未开始"}), 400

    result = engine.meet_npc(npc_id)
    if "game_state" in result:
        enrich_state(result["game_state"])
    return jsonify(result)


@app.route("/api/npc/<int:npc_id>/date", methods=["POST"])
def date_npc(npc_id: int):
    """与NPC约会"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    engine = get_engine()
    if not engine:
        return jsonify({"error": "游戏尚未开始"}), 400

    result = engine.date_npc(npc_id)
    if "game_state" in result:
        enrich_state(result["game_state"])
    return jsonify(result)


@app.route("/api/npc/<int:npc_id>/spar", methods=["POST"])
def spar_npc(npc_id: int):
    """与NPC切磋"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    engine = get_engine()
    if not engine:
        return jsonify({"error": "游戏尚未开始"}), 400

    result = engine.spar_with_npc(npc_id)
    if "game_state" in result:
        enrich_state(result["game_state"])
    return jsonify(result)


# ==================== 生活事件系统 ====================


@app.route("/api/life_event/choice", methods=["POST"])
def life_event_choice():
    """处理生活随机事件选择"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    engine = get_engine()
    if not engine:
        return jsonify({"error": "游戏尚未开始"}), 400

    data = request.get_json()
    event_id = data.get("event_id")
    option_index = data.get("option_index")
    custom_action = data.get("custom_action", "")

    event = get_event_by_id(event_id)
    if not event:
        return jsonify({"success": False, "error": "事件不存在"}), 404

    npcs = get_npcs_for_display(engine.user_id)

    if custom_action and option_index == -1:
        from .game.deepseek import get_deepseek_response
        prompt = f"玩家在'{event['name']}'事件中决定：{custom_action}。请以天道法则判定结果，用一句话描述。"
        ai_result = get_deepseek_response(prompt)
        result = {
            "log": ai_result,
            "success": True,
            "rewards": {}
        }
    elif option_index >= 0:
        result = resolve_event_option(event, option_index, engine.player, npcs)
    else:
        return jsonify({"success": False, "error": "无效的选择"}), 400

    engine.save()

    new_achievements = engine._check_achievements()
    life_event = engine._trigger_life_event()

    return jsonify({
        "success": True,
        "result": result,
        "player": engine.player.to_dict(),
        "new_achievements": new_achievements,
        "life_event": life_event
    })


# ==================== 成就系统 ====================


@app.route("/api/achievements", methods=["GET"])
def list_achievements():
    """获取所有成就定义及玩家解锁情况"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    engine = get_engine()
    if engine:
        npcs = get_npcs_for_display(engine.user_id)
        new_achievements = check_all_achievements(engine.player, engine.user_id, npcs)
    else:
        new_achievements = []

    all_achievements = get_all_achievements()
    player_achievements = get_player_achievements(user_id)
    unlocked_ids = {a["achievement_id"] for a in player_achievements}

    achievements_list = []
    for ach in all_achievements:
        achievements_list.append({
            "id": ach["id"],
            "name": ach["name"],
            "title": ach["title"],
            "description": ach["description"],
            "icon": ach["icon"],
            "condition_desc": ach["condition_desc"],
            "unlocked": ach["id"] in unlocked_ids,
            "unlocked_at": next(
                (a["unlocked_at"] for a in player_achievements if a["achievement_id"] == ach["id"]),
                None
            )
        })

    return jsonify({
        "achievements": achievements_list,
        "total": len(achievements_list),
        "unlocked_count": len(unlocked_ids),
        "new_achievements": new_achievements
    })


@app.route("/api/deepseek_config", methods=["POST"])
def update_deepseek_config():
    """更新DeepSeek API配置"""
    data = request.get_json()
    api_key = data.get("api_key", "")
    if api_key:
        from game.config import DEEPSEEK_API_KEY
        # 运行时更新API Key（仅本次会话有效）
        import game.config as config
        config.DEEPSEEK_API_KEY = api_key
        return jsonify({"success": True, "message": "API Key已更新"})
    return jsonify({"success": False, "message": "请输入有效的API Key"})


# ==================== 启动入口 ====================

if __name__ == "__main__":
    print("=" * 50)
    print("  修仙之路 - 重生穿越文字冒险游戏")
    print("=" * 50)
    print("  启动服务器...")
    print("  请在浏览器中打开: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host="127.0.0.1", port=5000)
