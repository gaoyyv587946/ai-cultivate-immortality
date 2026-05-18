"""SQLite 数据库操作模块
负责用户、NPC、游戏状态的持久化存储
"""

import sqlite3
import os
import json
from typing import Optional, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.db")


def get_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict]:
    """将 sqlite3.Row 安全转换为 dict（避免 .get() 不存在的 AttributeError）

    sqlite3.Row 不支持 .get() 方法，只支持 row["key"] 方括号访问。
    此函数统一做转换，防止 AttributeError 反复出现。
    """
    if row is None:
        return None
    return dict(row)


def init_database():
    """初始化数据库，创建所有必要的表并执行迁移"""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 只删除日志类表（可安全重建），保留用户数据
        cursor.execute("DROP TABLE IF EXISTS npc_conversations")
        cursor.execute("DROP TABLE IF EXISTS relationship_events")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                player_state TEXT NOT NULL,
                turn_count INTEGER DEFAULT 0,
                phase TEXT DEFAULT 'prelude',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS npcs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                title TEXT,
                realm TEXT NOT NULL,
                realm_level INTEGER NOT NULL,
                relationship INTEGER DEFAULT 0,
                first_met_at TEXT NOT NULL,
                first_met_realm_level INTEGER NOT NULL,
                is_alive INTEGER DEFAULT 1,
                backstory TEXT,
                gender TEXT DEFAULT 'male',
                is_married INTEGER DEFAULT 0,
                affection_type TEXT DEFAULT '',
                favorite_gift TEXT DEFAULT '',
                shared_cultivation INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, name)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS npc_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                npc_id INTEGER NOT NULL,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                relationship_change INTEGER DEFAULT 0,
                cultivation_change INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (npc_id) REFERENCES npcs(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS global_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationship_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                npc_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                relationship_change INTEGER NOT NULL,
                player_realm TEXT NOT NULL,
                player_realm_level INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (npc_id) REFERENCES npcs(id) ON DELETE CASCADE
            )
        """)

        # ===== 成就系统表 =====
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                icon TEXT DEFAULT '🏆',
                condition_desc TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, achievement_id)
            )
        """)

        # ===== 数据库迁移：为旧表补充新增列（保留数据） =====
        game_states_migrations = [
            ("intelligence", "INTEGER DEFAULT 50"),
            ("stamina", "INTEGER DEFAULT 50"),
            ("strength", "INTEGER DEFAULT 50"),
            ("spirit", "INTEGER DEFAULT 50"),
        ]
        for col_name, col_type in game_states_migrations:
            try:
                cursor.execute(f"ALTER TABLE game_states ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass

        npcs_migrations = [
            ("shared_cultivation", "INTEGER DEFAULT 0"),
            ("is_sworn_brother", "INTEGER DEFAULT 0"),
        ]
        for col_name, col_type in npcs_migrations:
            try:
                cursor.execute(f"ALTER TABLE npcs ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass

        users_migrations = [
            ("is_admin", "INTEGER DEFAULT 0"),
            ("last_active", "TIMESTAMP"),
            ("deepseek_calls_today", "INTEGER DEFAULT 0"),
            ("deepseek_daily_limit", "INTEGER DEFAULT 50"),
        ]
        for col_name, col_type in users_migrations:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass

        # ===== 游戏状态追踪列迁移 =====
        game_stats_migrations = [
            ("minigame_count", "INTEGER DEFAULT 0"),
            ("exam_count", "INTEGER DEFAULT 0"),
            ("work_earnings", "INTEGER DEFAULT 0"),
            ("npc_encounter_count", "INTEGER DEFAULT 0"),
            ("has_breakthrough", "INTEGER DEFAULT 0"),
        ]
        for col_name, col_type in game_stats_migrations:
            try:
                cursor.execute(f"ALTER TABLE game_states ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass

        # 设置 udaddy 为默认管理员
        cursor.execute("UPDATE users SET is_admin = 1 WHERE username = 'udaddy'")

        conn.commit()
    finally:
        conn.close()


# ==================== 用户系统 ====================


def create_user(username: str, password_hash: str) -> Optional[int]:
    """创建新用户，返回用户ID"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_username(username: str) -> Optional[sqlite3.Row]:
    """根据用户名查询用户"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cursor.fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    """根据ID查询用户"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()
    finally:
        conn.close()


# ==================== 游戏状态持久化 ====================


def save_game_state(user_id: int, player_state: dict):
    """保存玩家游戏状态"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        player_json = json.dumps(player_state, ensure_ascii=False)
        cursor.execute("""
            INSERT INTO game_states (user_id, player_state, turn_count, phase)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                player_state = excluded.player_state,
                turn_count = excluded.turn_count,
                phase = excluded.phase,
                updated_at = CURRENT_TIMESTAMP
        """, (
            user_id,
            player_json,
            player_state.get("turn_count", 0),
            player_state.get("phase", "prelude")
        ))
        conn.commit()
    finally:
        conn.close()


def load_game_state(user_id: int) -> Optional[dict]:
    """加载玩家游戏状态"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT player_state FROM game_states WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return json.loads(row["player_state"])
        return None
    finally:
        conn.close()


def delete_game_state(user_id: int):
    """删除玩家游戏状态（重置游戏）"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM game_states WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


# ==================== NPC 操作 ====================


def add_npc(user_id: int, name: str, title: str, realm: str, realm_level: int,
            first_met_at: str, first_met_realm_level: int,
            relationship: int = 0, backstory: str = "", gender: str = "male",
            affection_type: str = "", favorite_gift: str = "") -> int:
    """添加NPC"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO npcs (user_id, name, title, realm, realm_level, relationship,
                              first_met_at, first_met_realm_level, backstory, gender,
                              affection_type, favorite_gift)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, title, realm, realm_level, relationship,
              first_met_at, first_met_realm_level, backstory, gender,
              affection_type, favorite_gift))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return -1
    finally:
        conn.close()


def get_npc_by_name(user_id: int, name: str) -> Optional[sqlite3.Row]:
    """根据名字和用户ID查询NPC"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM npcs WHERE user_id = ? AND name = ?",
            (user_id, name)
        )
        return cursor.fetchone()
    finally:
        conn.close()


def get_npc_by_id(npc_id: int) -> Optional[sqlite3.Row]:
    """根据ID查询NPC"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM npcs WHERE id = ?", (npc_id,))
        return cursor.fetchone()
    finally:
        conn.close()


def update_npc_relationship(npc_id: int, change: int):
    """更新NPC关系度"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE npcs
            SET relationship = MAX(-100, MIN(100, relationship + ?)),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (change, npc_id))
        conn.commit()
    finally:
        conn.close()


def set_npc_relationship_direct(npc_id: int, value: int):
    """直接设置NPC关系度"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        clamped = max(-100, min(100, value))
        cursor.execute("""
            UPDATE npcs
            SET relationship = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (clamped, npc_id))
        conn.commit()
    finally:
        conn.close()


def update_npc_realm(npc_id: int, new_realm: str, new_level: int):
    """更新NPC境界"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE npcs
            SET realm = ?, realm_level = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_realm, new_level, npc_id))
        conn.commit()
    finally:
        conn.close()


def set_npc_dead(npc_id: int):
    """标记NPC死亡"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE npcs
            SET is_alive = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (npc_id,))
        conn.commit()
    finally:
        conn.close()


def set_npc_married(npc_id: int, married: bool = True):
    """设置NPC婚姻状态"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE npcs
            SET is_married = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (1 if married else 0, npc_id))
        conn.commit()
    finally:
        conn.close()


def set_npc_sworn_brother(npc_id: int, sworn: bool = True):
    """设置NPC结拜状态"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE npcs
            SET is_sworn_brother = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (1 if sworn else 0, npc_id))
        conn.commit()
    finally:
        conn.close()


def get_sworn_brother_npc(user_id: int) -> Optional[sqlite3.Row]:
    """获取用户当前结拜兄弟NPC"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM npcs
            WHERE user_id = ? AND is_sworn_brother = 1 AND is_alive = 1
            LIMIT 1
        """, (user_id,))
        return cursor.fetchone()
    finally:
        conn.close()


def add_relationship_event(user_id: int, npc_id: int, event_type: str, description: str,
                           relationship_change: int, player_realm: str,
                           player_realm_level: int):
    """添加关系事件日志"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO relationship_events
                (user_id, npc_id, event_type, description, relationship_change,
                 player_realm, player_realm_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, npc_id, event_type, description, relationship_change,
              player_realm, player_realm_level))
        conn.commit()
    finally:
        conn.close()


def add_global_event(username: str, event_type: str, description: str):
    """添加全局事件（突破、结交道侣等），保留最近200条"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO global_events (username, event_type, description)
            VALUES (?, ?, ?)
        """, (username, event_type, description))
        cursor.execute("""
            DELETE FROM global_events WHERE id NOT IN (
                SELECT id FROM global_events ORDER BY id DESC LIMIT 200
            )
        """)
        conn.commit()
    finally:
        conn.close()


def get_global_events(limit: int = 50) -> list:
    """获取全局事件列表"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM global_events ORDER BY id DESC LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_top_npcs(user_id: int, limit: int = 6) -> list:
    """获取用户关系度最高的NPC列表"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM npcs
            WHERE user_id = ? AND is_alive = 1
            ORDER BY ABS(relationship) DESC, relationship DESC
            LIMIT ?
        """, (user_id, limit))
        return cursor.fetchall()
    finally:
        conn.close()


def get_all_npcs(user_id: int) -> list:
    """获取用户所有NPC"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM npcs
            WHERE user_id = ?
            ORDER BY ABS(relationship) DESC, relationship DESC
        """, (user_id,))
        return cursor.fetchall()
    finally:
        conn.close()


def get_alive_npcs(user_id: int) -> list:
    """获取用户所有存活NPC"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM npcs
            WHERE user_id = ? AND is_alive = 1
            ORDER BY ABS(relationship) DESC, relationship DESC
        """, (user_id,))
        return cursor.fetchall()
    finally:
        conn.close()


def get_married_npc(user_id: int) -> Optional[sqlite3.Row]:
    """获取用户已婚NPC（道侣）"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM npcs
            WHERE user_id = ? AND is_married = 1 AND is_alive = 1
            LIMIT 1
        """, (user_id,))
        return cursor.fetchone()
    finally:
        conn.close()


def get_npc_event_history(user_id: int, npc_id: int, limit: int = 20) -> list:
    """获取NPC关系事件历史"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM relationship_events
            WHERE user_id = ? AND npc_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, npc_id, limit))
        return cursor.fetchall()
    finally:
        conn.close()


def is_npc_exists(user_id: int, name: str) -> bool:
    """检查NPC是否存在"""
    return get_npc_by_name(user_id, name) is not None


def get_npc_count(user_id: int) -> int:
    """获取用户NPC总数"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM npcs WHERE user_id = ?", (user_id,))
        return cursor.fetchone()[0]
    finally:
        conn.close()


def delete_user_npcs(user_id: int):
    """删除用户所有NPC和相关事件"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM npc_conversations WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM relationship_events WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM npcs WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


def save_conversation(user_id: int, npc_id: int, sender: str, content: str,
                      relationship_change: int = 0, cultivation_change: int = 0):
    """保存一条NPC对话记录"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO npc_conversations
                (user_id, npc_id, sender, content, relationship_change, cultivation_change)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, npc_id, sender, content, relationship_change, cultivation_change))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_conversation_history(user_id: int, npc_id: int, limit: int = 20) -> list:
    """获取NPC对话历史（最新在前）"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM npc_conversations
            WHERE user_id = ? AND npc_id = ?
            ORDER BY created_at ASC
            LIMIT ?
        """, (user_id, npc_id, limit))
        return cursor.fetchall()
    finally:
        conn.close()


def delete_npc_conversations(user_id: int, npc_id: int = None):
    """删除NPC对话记录，如果指定npc_id则只删除该NPC的"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if npc_id:
            cursor.execute("""
                DELETE FROM npc_conversations WHERE user_id = ? AND npc_id = ?
            """, (user_id, npc_id))
        else:
            cursor.execute("DELETE FROM npc_conversations WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


def update_npc_shared_cultivation(npc_id: int, amount: int) -> int:
    """增加NPC共享修为，返回累计共享修为"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE npcs
            SET shared_cultivation = shared_cultivation + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (amount, npc_id))
        conn.commit()
        cursor.execute("SELECT shared_cultivation FROM npcs WHERE id = ?", (npc_id,))
        row = cursor.fetchone()
        return row["shared_cultivation"] if row else 0
    finally:
        conn.close()


def get_npc_shared_cultivation(npc_id: int) -> int:
    """获取NPC当前累积的共享修为"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT shared_cultivation FROM npcs WHERE id = ?", (npc_id,))
        row = cursor.fetchone()
        return row["shared_cultivation"] if row else 0
    finally:
        conn.close()


def get_partner_npc(user_id: int):
    """获取用户当前道侣NPC（已婚且存活）"""
    return get_married_npc(user_id)


# ==================== 后台管理 ====================


def _ensure_json_safe(obj):
    """递归确保对象中的所有值都是 JSON 可序列化的基本类型"""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _ensure_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_ensure_json_safe(v) for v in obj]
    return str(obj)


def get_all_users() -> list:
    """获取所有用户及其最新游戏状态"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.username, u.is_admin, u.created_at, u.last_active,
                   u.deepseek_calls_today, u.deepseek_daily_limit,
                   gs.player_state, gs.turn_count
            FROM users u
            LEFT JOIN game_states gs ON gs.user_id = u.id
            ORDER BY u.id
        """)
        rows = cursor.fetchall()
        result = []
        for row in rows:
            user = dict(row)
            user["deepseek_calls_today"] = user.get("deepseek_calls_today") or 0
            user["deepseek_daily_limit"] = user.get("deepseek_daily_limit") or 0
            user["is_admin"] = user.get("is_admin", 0) or 0
            user["turn_count"] = user.get("turn_count") or 0
            if user.get("player_state"):
                import json
                ps = json.loads(user["player_state"])
                user["realm_level"] = ps.get("realm_level", 1)
                user["realm_name"] = ps.get("realm_name", "未知")
                user["is_alive"] = ps.get("is_alive", True)
            else:
                user["realm_level"] = None
                user["realm_name"] = "未开始"
                user["is_alive"] = None
            del user["player_state"]
            result.append(user)
        return _ensure_json_safe(result)
    finally:
        conn.close()


def update_user_deepseek_limit(user_id: int, new_limit: int) -> bool:
    """更新用户每日DeepSeek调用上限"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET deepseek_daily_limit = ? WHERE id = ?",
            (new_limit, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def update_last_active(user_id: int):
    """更新用户最后活跃时间"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id,)
        )
        conn.commit()
    finally:
        conn.close()


# ==================== 成就系统 ====================


def init_achievements():
    """初始化成就定义（确保数据库中已有成就数据）"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM achievements")
        if cursor.fetchone()[0] > 0:
            return
        from .achievements import ACHIEVEMENTS
        for ach in ACHIEVEMENTS:
            cursor.execute("""
                INSERT OR IGNORE INTO achievements (id, name, title, description, icon, condition_desc)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ach["id"], ach["name"], ach["title"], ach["description"], ach.get("icon", "🏆"), ach["condition_desc"]))
        conn.commit()
    finally:
        conn.close()


def get_all_achievements() -> list:
    """获取所有成就定义"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM achievements ORDER BY id")
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_player_achievements(user_id: int) -> list:
    """获取玩家已解锁的成就ID列表"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pa.achievement_id, pa.unlocked_at, a.name, a.title, a.description, a.icon, a.condition_desc
            FROM player_achievements pa
            JOIN achievements a ON a.id = pa.achievement_id
            WHERE pa.user_id = ?
            ORDER BY pa.unlocked_at
        """, (user_id,))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def unlock_achievement(user_id: int, achievement_id: str) -> bool:
    """解锁玩家成就，返回是否新解锁"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO player_achievements (user_id, achievement_id)
            VALUES (?, ?)
        """, (user_id, achievement_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def change_password(user_id: int, new_password_hash: str) -> bool:
    """修改用户密码"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (new_password_hash, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_deepseek_call_count(user_id: int) -> int:
    """获取用户今日DeepSeek调用次数"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT deepseek_calls_today FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        return row["deepseek_calls_today"] if row else 0
    finally:
        conn.close()


def increment_deepseek_calls(user_id: int) -> int:
    """DeepSeek调用次数+1，返回当前次数"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET deepseek_calls_today = deepseek_calls_today + 1 WHERE id = ?",
            (user_id,)
        )
        conn.commit()
        cursor.execute("SELECT deepseek_calls_today FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return row["deepseek_calls_today"] if row else 0
    finally:
        conn.close()


def reset_deepseek_calls(user_id: int):
    """重置用户DeepSeek调用计数"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET deepseek_calls_today = 0 WHERE id = ?",
            (user_id,)
        )
        conn.commit()
    finally:
        conn.close()


def is_admin_user(user_id: int) -> bool:
    """检查用户是否为管理员"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return bool(row and row["is_admin"])
    finally:
        conn.close()


def get_spirit_stones_ranking(limit: int = 20) -> list:
    """获取灵石排行榜（按灵石数量降序排列）"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.username, gs.player_state
            FROM users u
            INNER JOIN game_states gs ON gs.user_id = u.id
            ORDER BY gs.updated_at DESC
        """)
        rows = cursor.fetchall()
        ranking = []
        for row in rows:
            try:
                ps = json.loads(row["player_state"])
                stones = ps.get("spirit_stones", 0)
                realm_name = ps.get("realm_name", "未知")
                ranking.append({
                    "user_id": row["id"],
                    "username": row["username"],
                    "spirit_stones": stones,
                    "realm_name": realm_name
                })
            except (json.JSONDecodeError, TypeError):
                continue
        ranking.sort(key=lambda x: x["spirit_stones"], reverse=True)
        return _ensure_json_safe(ranking[:limit])
    finally:
        conn.close()


def clear_all_user_data():
    """一键清理所有用户游戏数据（保留用户账号）"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM game_states")
        cursor.execute("DELETE FROM npcs")
        cursor.execute("DELETE FROM npc_conversations")
        cursor.execute("DELETE FROM relationship_events")
        cursor.execute("DELETE FROM global_events")
        conn.commit()
        return {"success": True, "message": "所有用户数据已清除"}
    except Exception as e:
        return {"success": False, "message": f"清除失败：{str(e)}"}
    finally:
        conn.close()
