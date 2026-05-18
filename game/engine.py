"""游戏核心引擎模块
负责处理所有游戏逻辑：回合流转、行动执行、突破判定、NPC交互、死亡检测等
"""

import random
from typing import Optional

from .models import Player
from .realms import (
    get_realm_by_level, can_breakthrough, is_max_realm,
    get_breakthrough_threshold, format_realm_info
)
from .events import get_preset_events, get_preset_event_by_name
from .deepseek import call_deepseek
from .story import (
    get_prelude_step, get_prelude_step_count,
    get_breakthrough_story, get_death_scene
)
from .npc_generator import (
    generate_initial_npcs, generate_npcs_for_new_realm,
    generate_event_npc, get_npcs_for_display
)
from .database import (
    update_npc_relationship, add_relationship_event, set_npc_dead,
    set_npc_married, set_npc_relationship_direct,
    get_married_npc, get_alive_npcs, get_npc_by_id, get_npc_by_name,
    save_game_state, load_game_state, is_npc_exists, delete_user_npcs,
    save_conversation, get_conversation_history,
    update_npc_shared_cultivation, get_partner_npc,
    get_sworn_brother_npc, add_global_event, get_user_by_id
)
from .modules.attributes import (
    pick_events_attr_change, modify_attr, ATTR_LABELS
)
from .config import (
    NPC_INTERACTION_REJECTION_BASE_CHANCE,
    NPC_REJECTION_RELATIONSHIP_PENALTY_MIN,
    NPC_REJECTION_RELATIONSHIP_PENALTY_MAX,
    NPC_FRIENDLY_INTERACTION_RELATIONSHIP_MULTIPLIER,
    NPC_FRIENDLY_INTERACTION_CULTIVATION_MULTIPLIER,
    PARTNER_CULTIVATION_SHARE_RATIO,
    PARTNER_NPC_REALM_UPGRADE_THRESHOLD,
    ABSURD_VERDICT_CATEGORIES, REALM_RANDOM_EVENTS,
    SPIRIT_STONES_GAIN_MIN, SPIRIT_STONES_GAIN_MAX,
    SPIRIT_STONES_BONUS_MIN, SPIRIT_STONES_BONUS_MAX
)
from .life_events import get_life_event_for_realm, get_event_by_id, resolve_event_option
from .achievements import check_all_achievements
from .database import init_achievements


class GameEngine:
    """游戏核心引擎，管理一个玩家实例的所有游戏逻辑"""

    def __init__(self, player: Player, user_id: int):
        self.player = player
        self.user_id = user_id

    # ==================== 持久化 ====================

    def save(self):
        """保存当前游戏状态到数据库"""
        save_game_state(self.user_id, self.player.to_dict())

    # ==================== 序章阶段 ====================

    def handle_prelude_choice(self, choice_index: int) -> dict:
        """处理序章阶段的选择"""
        prelude_step = get_prelude_step(self.player.prelude_step)
        if not prelude_step:
            return self._start_cultivation_phase()

        next_step = prelude_step["choices"][choice_index]["next"]
        if next_step == -1 or next_step >= get_prelude_step_count():
            return self._start_cultivation_phase()

        self.player.prelude_step = next_step
        next_prelude = get_prelude_step(next_step)
        self.save()
        return {
            "phase": self.player.phase,
            "prelude_step": next_prelude,
            "player": self.player.to_dict(),
            "npcs": get_npcs_for_display(self.user_id)
        }

    def _start_cultivation_phase(self) -> dict:
        """从序章过渡到修仙阶段"""
        self.player.phase = Player.PHASE_CULTIVATION
        self.player.add_log("🌄 你重生了！在这个修仙世界，一切都将重新开始。")
        self.player.add_log(f"🎒 你进入了{self.player.get_school_name()}，开始了你的修行之路。")

        new_npcs = generate_initial_npcs(self.user_id, self.player.realm_level)
        if new_npcs:
            self.player.add_log(f"👥 你结识了{len(new_npcs)}位新朋友。")

        self.save()
        return {
            "phase": self.player.phase,
            "player": self.player.to_dict(),
            "events": get_preset_events(self.player.realm_level),
            "npcs": get_npcs_for_display(self.user_id)
        }

    # ==================== 预设事件执行 ====================

    def execute_preset_event(self, event_name: str) -> dict:
        """执行预设事件"""
        if self.player.phase != Player.PHASE_CULTIVATION:
            return self._error_result("当前阶段无法执行此操作")

        if self.player.career_path == "上班":
            from .config import WORK_EVENTS
            event = next((e for e in WORK_EVENTS if e["name"] == event_name), None)
        else:
            event = get_preset_event_by_name(self.player.realm_level, event_name)
        if not event:
            return self._error_result(f"未知事件：{event_name}")

        self.player.advance_turn()

        is_bad_event = event.get("is_bad", False)

        base_ss = random.randint(SPIRIT_STONES_GAIN_MIN, SPIRIT_STONES_GAIN_MAX)
        ge_change = random.randint(-1, 2)
        dh_change = random.randint(-1, 1)

        if is_bad_event:
            gain = random.randint(event["cultivation_range"][0], event["cultivation_range"][1])
            cost = event["lifespan_cost"]
            extra_cost = random.randint(1, 3)
            total_cost = cost + extra_cost
            actual_cost = self.player.consume_lifespan(total_cost)
            self.player.add_cultivation(gain)

            self.player.add_spirit_stones(base_ss)
            self.player.add_good_evil(ge_change)
            self.player.add_dao_heart(dh_change)

            penalty_message = ""
            if random.random() < 0.3:
                penalty_range = event.get("penalty_range", (-20, -5))
                penalty = random.randint(penalty_range[0], penalty_range[1])
                self.player.reduce_cultivation(abs(penalty))
                penalty_message = f"\n⚠️ 坏事败露！受到惩罚，修为 {penalty}"

            outcome_message = (
                f"🔸 {event['description']}\n"
                f"修为 +{gain}，寿命 -{actual_cost}年，灵石 +{base_ss}"
                f"{penalty_message}"
            )
        else:
            gain = random.randint(event["cultivation_range"][0], event["cultivation_range"][1])
            cost = event["lifespan_cost"]
            actual_cost = self.player.consume_lifespan(cost)
            self.player.add_cultivation(gain)

            self.player.add_spirit_stones(base_ss)
            self.player.add_good_evil(ge_change)
            self.player.add_dao_heart(dh_change)

            outcome_message = (
                f"🔸 {event['description']}\n"
                f"修为 +{gain}，寿命 -{actual_cost}年，灵石 +{base_ss}"
            )

        # ---- 四维属性变化（好事件增加，坏事件减少） ----
        attr_changes = pick_events_attr_change(is_bad_event)
        attr_parts = []
        for attr_key, delta in attr_changes.items():
            old_val = getattr(self.player, attr_key)
            new_val, actual = modify_attr(old_val, delta)
            setattr(self.player, attr_key, new_val)
            if actual != 0:
                attr_parts.append(f"{ATTR_LABELS.get(attr_key, attr_key)} {'+' if actual > 0 else ''}{actual}")
        if attr_parts:
            outcome_message += "\n" + "，".join(attr_parts)

        self.player.add_log(outcome_message)

        npc_interact_chance = event["npc_interact_chance"]
        if is_bad_event:
            npc_interact_chance = min(0.9, npc_interact_chance * 1.5)

        npc_interaction = None
        if random.random() < npc_interact_chance:
            npc_interaction = self._try_npc_interaction(event["npc_scene"])

        random_event = None
        if random.random() < 0.1:
            random_event = self._trigger_random_event()

        realm_random_event = None
        realm_random_event = self._trigger_realm_random_event()

        from .config import NPC_ENCOUNTER_CHANCE
        npc_encounter = None
        if random.random() < NPC_ENCOUNTER_CHANCE:
            npc_encounter = self._trigger_proactive_encounter()
            if npc_encounter:
                self.player.npc_encounter_count += 1

        breakthrough_result = None
        if can_breakthrough(self.player.realm_level, self.player.cultivation):
            if (self.player.realm_level == 5
                    and self.player.career_path is None):
                breakthrough_result = {"need_career_choice": True}
            else:
                breakthrough_result = self._perform_breakthrough()

        # 道侣修为共享
        partner_share = self._share_cultivation_with_partner(gain)

        death_result = self._check_death()
        self.save()

        new_achievements = self._check_achievements()
        life_event = self._trigger_life_event()

        if self.player.career_path == "上班":
            from .config import WORK_EVENTS
            next_events = WORK_EVENTS
        else:
            next_events = get_preset_events(self.player.realm_level)

        return {
            "phase": self.player.phase,
            "player": self.player.to_dict(),
            "events": next_events,
            "npcs": get_npcs_for_display(self.user_id),
            "result": {
                "event": event["name"],
                "description": event["description"],
                "gain": gain,
                "cost": actual_cost
            },
            "npc_interaction": npc_interaction,
            "random_event": random_event,
            "realm_random_event": realm_random_event,
            "npc_encounter": npc_encounter,
            "breakthrough": breakthrough_result,
            "death": death_result,
            "partner_share": partner_share,
            "new_achievements": new_achievements,
            "life_event": life_event
        }

    # ==================== 自定义行动 ====================

    def execute_custom_action(self, action_text: str) -> dict:
        """执行玩家自定义行动"""
        if self.player.phase != Player.PHASE_CULTIVATION:
            return self._error_result("当前阶段无法执行此操作")

        if not action_text or len(action_text.strip()) == 0:
            return self._error_result("请输入你的行动")

        self.player.advance_turn()
        nearby_npcs = get_npcs_for_display(self.user_id)
        nearby_npcs_info = self._format_npcs_for_prompt(nearby_npcs[:3])

        player_realm = self.player.get_realm()
        deepseek_result = call_deepseek(
            action_text=action_text.strip(),
            player_realm_name=player_realm["name"],
            player_school=player_realm["school"],
            realm_description=player_realm["description"],
            nearby_npcs_info=nearby_npcs_info,
            event_context=f"这是第{self.player.turn_count}回合，玩家在{player_realm['school']}中行动。",
            user_id=self.user_id,
            player_good_evil=self.player.good_evil,
            player_dao_heart=self.player.dao_heart,
            player_spirit_stones=self.player.spirit_stones
        )

        if deepseek_result is None:
            return self._error_result("天道感应出错，请稍后再试。")

        return self._apply_deepseek_result(deepseek_result, action_text.strip())

    def _apply_deepseek_result(self, result: dict, action_text: str) -> dict:
        """应用DeepSeek的判定结果到游戏状态"""
        description = result.get("description", "你进行了一次行动。")
        lifespan_cost = result.get("lifespan_cost", 1)
        cultivation_gain = result.get("cultivation_gain", 0)
        special_effect = result.get("special_effect", "无")
        is_death = result.get("is_death", False)
        death_reason = result.get("death_reason", "")
        npc_interaction_data = result.get("npc_interaction")
        good_evil_change = result.get("good_evil_change", 0)
        dao_heart_change = result.get("dao_heart_change", 0)
        spirit_stones_change = result.get("spirit_stones_change", 0)

        if lifespan_cost > 0:
            actual_cost = self.player.consume_lifespan(lifespan_cost)

        if cultivation_gain > 0:
            self.player.add_cultivation(cultivation_gain)
        elif cultivation_gain < 0:
            self.player.reduce_cultivation(abs(cultivation_gain))

        if good_evil_change != 0:
            self.player.add_good_evil(good_evil_change)

        if dao_heart_change != 0:
            self.player.add_dao_heart(dao_heart_change)

        if spirit_stones_change != 0:
            self.player.add_spirit_stones(spirit_stones_change)

        special_message = ""
        if special_effect == "受伤":
            injury_cost = random.randint(10, 30)
            self.player.consume_lifespan(injury_cost)
            special_message = f"\n⚠️ 你受伤了，额外消耗{injury_cost}年寿命！"
        elif special_effect == "奇遇":
            bonus = random.randint(50, 200)
            self.player.add_cultivation(bonus)
            special_message = f"\n✨ 天降奇遇！额外获得{bonus}点修为！"
        elif special_effect == "顿悟":
            bonus = cultivation_gain
            self.player.add_cultivation(bonus)
            special_message = f"\n🌟 你顿悟了！修为收益翻倍，额外获得{bonus}点修为！"
        elif special_effect == "走火入魔":
            penalty = int(self.player.cultivation * random.uniform(0.3, 0.5))
            self.player.reduce_cultivation(penalty)
            self.player.consume_lifespan(20)
            special_message = f"\n💢 你走火入魔！修为减少{penalty}点，消耗20年寿命！"

        if is_death or not self.player.is_alive:
            death_type = "走火入魔" if "走火" in death_reason else "意外"
            self.player.force_death(death_reason or get_death_scene(death_type))
            self.save()
            return {
                "phase": self.player.phase,
                "player": self.player.to_dict(),
                "npcs": get_npcs_for_display(self.user_id),
                "death": {
                    "is_dead": True,
                    "type": death_type,
                    "scene": get_death_scene(death_type)
                }
            }

        npc_interaction = None
        if npc_interaction_data and "npc_name" in npc_interaction_data:
            npc_interaction = self._handle_npc_interaction_from_deepseek(
                npc_interaction_data["npc_name"],
                npc_interaction_data.get("relationship_change", 0)
            )

        log_message = f"🔸 {description}{special_message}"
        if cultivation_gain != 0:
            log_message += f"\n修为 {'+' if cultivation_gain > 0 else ''}{cultivation_gain}"
        if lifespan_cost > 0:
            log_message += f"，寿命 -{lifespan_cost}年"
        if good_evil_change != 0:
            log_message += f"，善恶 {'+' if good_evil_change > 0 else ''}{good_evil_change}"
        if dao_heart_change != 0:
            log_message += f"，道心 {'+' if dao_heart_change > 0 else ''}{dao_heart_change}"
        if spirit_stones_change != 0:
            log_message += f"，灵石 {'+' if spirit_stones_change > 0 else ''}{spirit_stones_change}"
        self.player.add_log(log_message)

        # 道侣修为共享（仅共享正向修为）
        partner_share = None
        if cultivation_gain > 0:
            partner_share = self._share_cultivation_with_partner(cultivation_gain)

        breakthrough_result = None
        if can_breakthrough(self.player.realm_level, self.player.cultivation):
            breakthrough_result = self._perform_breakthrough()

        death_result = self._check_death()
        self.save()

        new_achievements = self._check_achievements()
        life_event = self._trigger_life_event()

        return {
            "phase": self.player.phase,
            "player": self.player.to_dict(),
            "events": get_preset_events(self.player.realm_level),
            "npcs": get_npcs_for_display(self.user_id),
            "result": {
                "description": description,
                "gain": cultivation_gain,
                "cost": lifespan_cost,
                "special_effect": special_effect,
                "special_message": special_message,
                "good_evil_change": good_evil_change,
                "dao_heart_change": dao_heart_change,
                "spirit_stones_change": spirit_stones_change
            },
            "npc_interaction": npc_interaction,
            "breakthrough": breakthrough_result,
            "death": death_result,
            "partner_share": partner_share,
            "realm_random_event": self._trigger_realm_random_event(),
            "new_achievements": new_achievements,
            "life_event": life_event
        }

    # ==================== 突破系统 ====================

    def _perform_breakthrough(self) -> dict:
        """执行突破逻辑"""
        result = self.player.try_breakthrough()
        story = get_breakthrough_story(self.player.realm_level - 1, result["success"])

        verdict = self._get_absurd_verdict()
        if verdict and result["success"]:
            self.player.add_log(f"⚡ {result['message']}\n📜 天道显现法则：{verdict}")
        else:
            self.player.add_log(f"⚡ {result['message']}")

        npc_ids = []
        if result["success"] and self.player.realm_level <= 8:
            self.player.has_breakthrough = True
            npc_ids = generate_npcs_for_new_realm(self.user_id, self.player.realm_level)
            if npc_ids:
                self.player.add_log(f"👥 进入新的境界，你结识了新朋友。")
            # 记录全局事件
            user = get_user_by_id(self.user_id)
            if user:
                username = user["username"]
                add_global_event(username, "突破",
                    f"{username}成功突破至【{result['new_realm']}】！")

        return {
            "success": result["success"],
            "old_realm": result["old_realm"],
            "new_realm": result["new_realm"],
            "message": result["message"],
            "story": story,
            "new_npc_ids": npc_ids,
            "is_flyup": result["new_realm"] == "飞升",
            "verdict": verdict if result.get("success") else None
        }

    def choose_career(self, path: str) -> dict:
        """选择职业路线（化神/大学后）"""
        from .config import COMPANY_NAMES
        if self.player.realm_level != 5 or self.player.career_path is not None:
            return {"success": False, "message": "当前无法选择职业路线"}

        if path == "飞升":
            self.player.career_path = "飞升"
            self.player.add_log("📚 你决定继续深造，考研飞升！")
            return {
                "success": True,
                "path": "飞升",
                "message": "你选择了飞升路线，继续读研深造！"
            }
        elif path == "上班":
            self.player.career_path = "上班"
            self.player.company_name = random.choice(COMPANY_NAMES)
            self.player.add_log(f"💼 你决定进入{self.player.company_name}工作。")
            return {
                "success": True,
                "path": "上班",
                "company_name": self.player.company_name,
                "message": f"你选择了上班路线，进入{self.player.company_name}工作！"
            }
        return {"success": False, "message": f"未知路线：{path}"}

    # ==================== NPC互动系统 ====================

    def _try_npc_interaction(self, scene: str) -> Optional[dict]:
        """尝试随机NPC互动"""
        npcs = get_npcs_for_display(self.user_id)
        alive_npcs = [n for n in npcs if n["is_alive"]]

        if not alive_npcs:
            if random.random() < 0.3:
                new_npc = generate_event_npc(self.user_id, self.player.realm_level, scene)
                if new_npc:
                    return {
                        "type": "new_npc",
                        "npc": new_npc,
                        "message": f"你遇到了{new_npc['name']}（{new_npc['title']}）"
                    }
            return None

        npc = random.choice(alive_npcs)
        change = random.randint(-10, 20)
        update_npc_relationship(npc["id"], change)

        if change > 0:
            event_type = "相助"
            msg = f"你与{npc['name']}在{scene}中相处愉快，关系升温{change}点。"
        elif change == 0:
            event_type = "相遇"
            msg = f"你在{scene}遇到了{npc['name']}，彼此点头示意。"
        else:
            event_type = "冲突"
            msg = f"你在{scene}与{npc['name']}发生了一些不愉快，关系下降了{abs(change)}点。"

        add_relationship_event(
            user_id=self.user_id,
            npc_id=npc["id"],
            event_type=event_type,
            description=msg,
            relationship_change=change,
            player_realm=self.player.get_realm_name(),
            player_realm_level=self.player.realm_level
        )

        self.player.add_log(f"👤 {msg}")
        return {
            "type": "interaction",
            "npc": npc,
            "change": change,
            "message": msg
        }

    def _trigger_proactive_encounter(self) -> Optional[dict]:
        """随机触发NPC主动搭讪，中断当前自动修行"""
        npcs = get_npcs_for_display(self.user_id)
        alive_npcs = [n for n in npcs if n["is_alive"] and not n["is_married"]]
        if not alive_npcs:
            return None

        npc = random.choice(alive_npcs)
        name = npc["name"]

        encounter_lines = [
            f"{name}向你走来，微笑道：『道友近来可好？』",
            f"{name}远远喊住你：『喂，好久不见！』",
            f"{name}拍了拍你的肩膀：『在忙什么呢？』",
            f"{name}好奇地看着你：『道友修为又有精进啊！』",
            f"{name}凑过来小声说：『听说最近有大事要发生...』",
            f"{name}笑着对你说：『一起交流一下修行心得吧！』",
        ]
        line = random.choice(encounter_lines)

        self.player.add_log(f"💬 {line}")
        return {
            "type": "proactive_encounter",
            "npc_id": npc["id"],
            "npc_name": name,
            "npc_title": npc.get("title", ""),
            "npc_realm": npc.get("realm", ""),
            "npc_relationship": npc.get("relationship", 0),
            "opening_line": line
        }

    def _handle_npc_interaction_from_deepseek(self, npc_name: str,
                                               relationship_change: int) -> Optional[dict]:
        """处理DeepSeek返回的NPC互动结果"""
        npc = get_npc_by_name(self.user_id, npc_name)
        if npc:
            update_npc_relationship(npc["id"], relationship_change)
            event_type = "相助" if relationship_change > 0 else "冲突"
            msg = f"与{npc_name}的关系发生了变化（{relationship_change:+d}）。"
            add_relationship_event(
                user_id=self.user_id,
                npc_id=npc["id"],
                event_type=event_type,
                description=msg,
                relationship_change=relationship_change,
                player_realm=self.player.get_realm_name(),
                player_realm_level=self.player.realm_level
            )
            self.player.add_log(f"👤 {msg}")
            return {
                "type": "deepseek_interaction",
                "npc_name": npc_name,
                "change": relationship_change,
                "message": msg
            }
        else:
            new_npc = generate_event_npc(self.user_id, self.player.realm_level, f"与{npc_name}相遇")
            if new_npc:
                update_npc_relationship(new_npc["id"], max(-20, min(20, relationship_change)))
                msg = f"你遇到了{new_npc['name']}，{new_npc['backstory']}"
                self.player.add_log(f"👤 {msg}")
                return {
                    "type": "new_npc_from_deepseek",
                    "npc": new_npc,
                    "change": relationship_change,
                    "message": msg
                }
            return None

    # ==================== 主动NPC交互系统 ====================

    def interact_with_npc(self, npc_id: int, message: str) -> dict:
        """主动与NPC进行对话交流"""
        npc = get_npc_by_id(npc_id)
        if not npc:
            return {"success": False, "type": "interact", "message": "找不到该NPC。"}
        # 统一转为 dict，避免 sqlite3.Row 不支持 .get() 的 AttributeError
        npc = dict(npc)

        if not npc["is_alive"]:
            return {"success": False, "type": "interact", "message": f"{npc['name']}已不在人世。"}

        player_message = message.strip()
        if not player_message:
            return {"success": False, "type": "interact", "message": "你想说些什么呢？"}

        # 获取对话历史
        history_rows = get_conversation_history(self.user_id, npc_id, 50)
        conversation_history = [
            {
                "sender": row["sender"],
                "content": row["content"],
                "npc_name": npc["name"]
            }
            for row in history_rows
        ]

        # 调用DeepSeek进行NPC交互（含成人内容检测）
        from .deepseek import call_npc_interaction
        interaction_result = call_npc_interaction(
            npc_name=npc["name"],
            npc_title=npc["title"] or "",
            npc_realm=npc["realm"],
            npc_realm_level=npc["realm_level"],
            npc_relationship=npc["relationship"],
            npc_gender=npc["gender"],
            npc_backstory=npc["backstory"] or "",
            player_realm_name=self.player.get_realm_name(),
            player_school=self.player.get_school_name(),
            player_realm_level=self.player.realm_level,
            player_name=self.player.name,
            player_career_path=self.player.career_path or "",
            player_message=player_message,
            conversation_history=conversation_history,
            user_id=self.user_id,
            is_married=bool(npc["is_married"]),
            is_sworn_brother=bool(npc.get("is_sworn_brother", False))
        )

        reply = interaction_result.get("reply", "……")
        relationship_change = interaction_result.get("relationship_change", 0)
        cultivation_change = interaction_result.get("cultivation_change", 0)
        special_effect = interaction_result.get("special_effect", "无")
        is_adult = interaction_result.get("is_adult", False)

        # 应用好感度变化
        if relationship_change != 0:
            update_npc_relationship(npc["id"], relationship_change)

        # 获取口吻挡位名称，构建完整剧情描述
        from .deepseek import _get_relationship_tier_name
        tier_name = _get_relationship_tier_name(npc["relationship"] + relationship_change)
        from .config import NPC_TONE_TEMPLATES
        tone_template = NPC_TONE_TEMPLATES.get(tier_name, "{name}对你说：'{reply}'")

        # 构建带口吻的场景描述
        action_desc = f"对{npc['name']}说：「{player_message}」"
        tone_description = tone_template.format(
            action=action_desc,
            name=npc["name"],
            reply=reply
        )

        # 应用修为变化
        cultivation_desc = ""
        if cultivation_change > 0:
            self.player.add_cultivation(cultivation_change)
            cultivation_desc = f"修为+{cultivation_change}"
        elif cultivation_change < 0:
            self.player.reduce_cultivation(abs(cultivation_change))
            cultivation_desc = f"修为{cultivation_change}"

        # 特殊效果
        special_desc = ""
        if special_effect == "顿悟":
            bonus = random.randint(20, 80)
            self.player.add_cultivation(bonus)
            special_desc = f"\n🌟 你从对话中顿悟了！额外获得{bonus}点修为！"
        elif special_effect == "机缘":
            bonus = random.randint(30, 100)
            self.player.add_cultivation(bonus)
            special_desc = f"\n✨ 这次交流带来了意外的机缘！修为+{bonus}！"
        elif special_effect == "指点":
            bonus = random.randint(10, 40)
            self.player.add_cultivation(bonus)
            special_desc = f"\n📖 {npc['name']}的指点让你受益匪浅！修为+{bonus}！"

        # 随机消耗寿命（每次交流消耗1-4年）
        lifespan_cost = random.randint(1, 4)
        self.player.consume_lifespan(lifespan_cost)

        # 保存对话记录到数据库
        save_conversation(
            user_id=self.user_id,
            npc_id=npc["id"],
            sender="player",
            content=player_message,
            relationship_change=0,
            cultivation_change=0
        )
        save_conversation(
            user_id=self.user_id,
            npc_id=npc["id"],
            sender="npc",
            content=reply,
            relationship_change=relationship_change,
            cultivation_change=cultivation_change
        )

        # 记录关系变化事件
        if relationship_change != 0:
            event_type = "好感上升" if relationship_change > 0 else "好感下降"
            add_relationship_event(
                user_id=self.user_id,
                npc_id=npc["id"],
                event_type=event_type,
                description=f"对话交流：{reply[:30]}…",
                relationship_change=relationship_change,
                player_realm=self.player.get_realm_name(),
                player_realm_level=self.player.realm_level
            )

        # 构建日志
        log_parts = [f"💬 与{npc['name']}交谈"]
        if relationship_change != 0:
            log_parts.append(f"好感{relationship_change:+d}")
        if cultivation_change != 0:
            log_parts.append(cultivation_desc)
        if lifespan_cost > 0:
            log_parts.append(f"寿命-{lifespan_cost}")
        self.player.add_log(f"{'，'.join(log_parts)}{special_desc}")

        # 检查死亡
        death_result = None
        if not self.player.is_alive:
            death_type = "寿终"
            death_result = {
                "is_dead": True,
                "type": death_type,
                "scene": f"岁月无情，你与{npc['name']}的这次交谈耗尽了最后的时光……"
            }

        # 尝试触发结婚（好感度≥80且未婚）
        marriage_offer = None
        married_npc = get_married_npc(self.user_id)
        new_relationship = npc["relationship"] + relationship_change
        if (new_relationship >= 80
                and not npc["is_married"]
                and not married_npc
                and self.player.realm_level >= 5):
            # 对方主动表白/玩家可以求婚
            marriage_chance = 0.25 + new_relationship * 0.007
            if random.random() < marriage_chance:
                set_npc_married(npc["id"], True)
                # 设置玩家道侣相关状态
                marriage_offer = {
                    "success": True,
                    "npc_name": npc["name"],
                    "message": f"💍 经过这次交流，你与{npc['name']}心意相通，结为道侣！"
                }
                self.player.add_log(f"💍 与{npc['name']}结为道侣！")
            elif random.random() < 0.1:
                # 低概率对方主动求婚
                marriage_offer = {
                    "success": True,
                    "auto_propose": True,
                    "npc_name": npc["name"],
                    "message": f"💍 {npc['name']}突然握住你的手，眼含深情道：「我们结为道侣吧…」"
                }
                # 需要前端确认
                marriage_offer["pending"] = True

        self.save()
        return {
            "success": True,
            "type": "interact",
            "npc_id": npc["id"],
            "npc_name": npc["name"],
            "player_message": player_message,
            "reply": reply,
            "tone_description": tone_description,
            "relationship_change": relationship_change,
            "cultivation_change": cultivation_change,
            "lifespan_cost": lifespan_cost,
            "special_effect": special_effect,
            "special_desc": special_desc,
            "is_adult": is_adult,
            "marriage_offer": marriage_offer,
            "death": death_result,
            "game_state": self.get_game_state()
        }

    def confirm_marriage(self, npc_id: int) -> dict:
        """确认结婚（对方主动求婚时）"""
        npc = get_npc_by_id(npc_id)
        if not npc:
            return {"success": False, "message": "找不到该NPC。"}

        if npc["is_married"]:
            return {"success": False, "message": f"{npc['name']}已有道侣。"}

        if get_married_npc(self.user_id):
            return {"success": False, "message": "你已有道侣。"}

        set_npc_married(npc_id, True)
        msg = f"💍 你与{npc['name']}正式结为道侣，从此携手共赴大道！"
        self.player.add_log(f"💍 {msg}")
        self.save()
        return {"success": True, "message": msg, "game_state": self.get_game_state()}

    # ==================== 新增NPC交互类型：见面/约会/切磋 ====================

    def meet_npc(self, npc_id: int) -> dict:
        """与NPC见面"""
        npc = get_npc_by_id(npc_id)
        if not npc:
            return {"success": False, "type": "meet", "message": "找不到该NPC。"}
        if not npc["is_alive"]:
            return {"success": False, "type": "meet", "message": f"{npc['name']}已不在人世。"}
        if npc["relationship"] < -20:
            return {"success": False, "type": "meet", "message": f"{npc['name']}不愿与你见面（关系度需≥-20，当前{npc['relationship']}）。"}

        # 拒绝判定
        if random.random() < NPC_INTERACTION_REJECTION_BASE_CHANCE:
            penalty = random.randint(NPC_REJECTION_RELATIONSHIP_PENALTY_MIN, NPC_REJECTION_RELATIONSHIP_PENALTY_MAX)
            update_npc_relationship(npc["id"], penalty)
            msg = f"{npc['name']}婉拒了你的见面请求，关系{penalty:+d}"
            self.player.add_log(f"🤝 {msg}")
            add_relationship_event(
                user_id=self.user_id, npc_id=npc["id"], event_type="拒绝",
                description=f"被{npc['name']}拒绝见面", relationship_change=penalty,
                player_realm=self.player.get_realm_name(), player_realm_level=self.player.realm_level
            )
            self.save()
            return {
                "success": False, "type": "meet", "npc_name": npc["name"],
                "rejected": True, "relationship_change": penalty,
                "message": msg, "game_state": self.get_game_state()
            }

        lifespan_cost = random.randint(1, 3)
        cultivation_gain = max(1, int(random.randint(5, 15) * NPC_FRIENDLY_INTERACTION_CULTIVATION_MULTIPLIER))
        relationship_change = max(1, int(random.randint(1, 5) * NPC_FRIENDLY_INTERACTION_RELATIONSHIP_MULTIPLIER))

        self.player.consume_lifespan(lifespan_cost)
        self.player.add_cultivation(cultivation_gain)
        update_npc_relationship(npc["id"], relationship_change)

        msg = f"你与{npc['name']}见了一面，相谈甚欢。修为+{cultivation_gain}，好感{relationship_change:+d}，寿命-{lifespan_cost}年"
        self.player.add_log(f"🤝 {msg}")
        add_relationship_event(
            user_id=self.user_id, npc_id=npc["id"], event_type="见面",
            description=f"与{npc['name']}见面叙旧", relationship_change=relationship_change,
            player_realm=self.player.get_realm_name(), player_realm_level=self.player.realm_level
        )

        partner_share = self._share_cultivation_with_partner(cultivation_gain)
        self.save()
        return {
            "success": True, "type": "meet", "npc_name": npc["name"],
            "cultivation_change": cultivation_gain, "relationship_change": relationship_change,
            "lifespan_cost": lifespan_cost, "message": msg,
            "partner_share": partner_share,
            "game_state": self.get_game_state()
        }

    def date_npc(self, npc_id: int) -> dict:
        """与NPC约会（仅限女性NPC）"""
        npc = get_npc_by_id(npc_id)
        if not npc:
            return {"success": False, "type": "date", "message": "找不到该NPC。"}
        if not npc["is_alive"]:
            return {"success": False, "type": "date", "message": f"{npc['name']}已不在人世。"}
        if npc["gender"] != "female":
            return {"success": False, "type": "date", "message": f"{npc['name']}是男性，无法约会。"}
        if npc["relationship"] < 30:
            return {"success": False, "type": "date", "message": f"{npc['name']}和你还不够熟悉（关系度需≥30，当前{npc['relationship']}）。"}

        # 拒绝判定
        if random.random() < NPC_INTERACTION_REJECTION_BASE_CHANCE:
            penalty = random.randint(NPC_REJECTION_RELATIONSHIP_PENALTY_MIN, NPC_REJECTION_RELATIONSHIP_PENALTY_MAX)
            update_npc_relationship(npc["id"], penalty)
            msg = f"{npc['name']}婉拒了你的约会邀请，关系{penalty:+d}"
            self.player.add_log(f"🌹 {msg}")
            add_relationship_event(
                user_id=self.user_id, npc_id=npc["id"], event_type="拒绝",
                description=f"被{npc['name']}拒绝约会", relationship_change=penalty,
                player_realm=self.player.get_realm_name(), player_realm_level=self.player.realm_level
            )
            self.save()
            return {
                "success": False, "type": "date", "npc_name": npc["name"],
                "rejected": True, "relationship_change": penalty,
                "message": msg, "game_state": self.get_game_state()
            }

        lifespan_cost = random.randint(2, 6)
        cultivation_gain = max(1, int(random.randint(10, 30) * NPC_FRIENDLY_INTERACTION_CULTIVATION_MULTIPLIER))
        relationship_change = max(1, int(random.randint(3, 10) * NPC_FRIENDLY_INTERACTION_RELATIONSHIP_MULTIPLIER))

        self.player.consume_lifespan(lifespan_cost)
        self.player.add_cultivation(cultivation_gain)
        update_npc_relationship(npc["id"], relationship_change)

        romance_message = ""
        if npc["gender"] == "female" and npc["affection_type"]:
            bonus_relation = random.randint(1, 5)
            update_npc_relationship(npc["id"], bonus_relation)
            relationship_change += bonus_relation
            romance_message = f"\n💕 {npc['name']}（{npc['affection_type']}）对你更加倾心了！好感额外+{bonus_relation}"

        msg = f"你与{npc['name']}度过了一段愉快的约会时光。修为+{cultivation_gain}，好感{relationship_change:+d}，寿命-{lifespan_cost}年{romance_message}"
        self.player.add_log(f"🌹 {msg}")
        add_relationship_event(
            user_id=self.user_id, npc_id=npc["id"], event_type="约会",
            description=f"与{npc['name']}浪漫约会", relationship_change=relationship_change,
            player_realm=self.player.get_realm_name(), player_realm_level=self.player.realm_level
        )

        partner_share = self._share_cultivation_with_partner(cultivation_gain)
        self.save()
        return {
            "success": True, "type": "date", "npc_name": npc["name"],
            "cultivation_change": cultivation_gain, "relationship_change": relationship_change,
            "lifespan_cost": lifespan_cost, "message": msg,
            "romance_message": romance_message,
            "partner_share": partner_share,
            "game_state": self.get_game_state()
        }

    def spar_with_npc(self, npc_id: int) -> dict:
        """与NPC切磋"""
        npc = get_npc_by_id(npc_id)
        if not npc:
            return {"success": False, "type": "spar", "message": "找不到该NPC。"}
        if not npc["is_alive"]:
            return {"success": False, "type": "spar", "message": f"{npc['name']}已不在人世。"}

        # 拒绝判定
        if random.random() < NPC_INTERACTION_REJECTION_BASE_CHANCE:
            penalty = random.randint(NPC_REJECTION_RELATIONSHIP_PENALTY_MIN, NPC_REJECTION_RELATIONSHIP_PENALTY_MAX)
            update_npc_relationship(npc["id"], penalty)
            msg = f"{npc['name']}拒绝了你的切磋请求，关系{penalty:+d}"
            self.player.add_log(f"⚔️ {msg}")
            add_relationship_event(
                user_id=self.user_id, npc_id=npc["id"], event_type="拒绝",
                description=f"被{npc['name']}拒绝切磋", relationship_change=penalty,
                player_realm=self.player.get_realm_name(), player_realm_level=self.player.realm_level
            )
            self.save()
            return {
                "success": False, "type": "spar", "npc_name": npc["name"],
                "rejected": True, "relationship_change": penalty,
                "message": msg, "game_state": self.get_game_state()
            }

        lifespan_cost = random.randint(1, 5)
        self.player.consume_lifespan(lifespan_cost)

        player_power = self.player.realm_level * 100 + self.player.cultivation
        npc_power = npc["realm_level"] * 100 + 50

        power_diff = player_power - npc_power
        roll = random.random()

        if power_diff > 200 or (power_diff > 0 and roll < 0.6):
            cultivation_gain = max(1, int(random.randint(20, 50) * NPC_FRIENDLY_INTERACTION_CULTIVATION_MULTIPLIER))
            relationship_change = max(1, int(random.randint(2, 8) * NPC_FRIENDLY_INTERACTION_RELATIONSHIP_MULTIPLIER))
            result_text = "你凭借扎实的学识胜过了对方！"
        elif power_diff < -200 or (power_diff < 0 and roll < 0.6):
            cultivation_gain = max(1, int(random.randint(5, 15) * NPC_FRIENDLY_INTERACTION_CULTIVATION_MULTIPLIER))
            relationship_change = max(0, int(random.randint(0, 3) * NPC_FRIENDLY_INTERACTION_RELATIONSHIP_MULTIPLIER))
            result_text = "你虽败犹荣，从对方身上学到了不少。"
        else:
            cultivation_gain = max(1, int(random.randint(10, 20) * NPC_FRIENDLY_INTERACTION_CULTIVATION_MULTIPLIER))
            relationship_change = max(1, int(random.randint(1, 5) * NPC_FRIENDLY_INTERACTION_RELATIONSHIP_MULTIPLIER))
            result_text = "你们旗鼓相当，互相切磋获益良多。"

        self.player.add_cultivation(cultivation_gain)
        update_npc_relationship(npc["id"], relationship_change)

        msg = f"你与{npc['name']}进行了一场知识切磋。{result_text} 修为+{cultivation_gain}，好感{relationship_change:+d}，寿命-{lifespan_cost}年"
        self.player.add_log(f"⚔️ {msg}")
        add_relationship_event(
            user_id=self.user_id, npc_id=npc["id"], event_type="切磋",
            description=f"与{npc['name']}切磋论道", relationship_change=relationship_change,
            player_realm=self.player.get_realm_name(), player_realm_level=self.player.realm_level
        )

        partner_share = self._share_cultivation_with_partner(cultivation_gain)
        self.save()
        return {
            "success": True, "type": "spar", "npc_name": npc["name"],
            "cultivation_change": cultivation_gain, "relationship_change": relationship_change,
            "lifespan_cost": lifespan_cost, "result_text": result_text, "message": msg,
            "partner_share": partner_share,
            "game_state": self.get_game_state()
        }

    # ==================== 仇视系统（NPC刺杀等） ====================

    def check_hostile_npc_events(self) -> Optional[dict]:
        """检查是否有仇视NPC触发敌对事件"""
        alive_npcs = get_alive_npcs(self.user_id)
        hostile_npcs = [n for n in alive_npcs if n["relationship"] <= -50]

        if not hostile_npcs or random.random() > 0.15:
            return None

        npc = random.choice(hostile_npcs)
        event_roll = random.random()

        if event_roll < 0.3:
            loss = random.randint(20, 60)
            self.player.reduce_cultivation(loss)
            cost = random.randint(5, 15)
            self.player.consume_lifespan(cost)
            msg = (f"🗡️ {npc['name']}对你怀恨在心，暗中下手偷袭！"
                   f"你损失了{loss}点修为，{cost}年寿命。")
            add_relationship_event(
                user_id=self.user_id,
                npc_id=npc["id"],
                event_type="刺杀",
                description=f"刺杀玩家：修为-{loss}，寿命-{cost}",
                relationship_change=-10,
                player_realm=self.player.get_realm_name(),
                player_realm_level=self.player.realm_level
            )
            self.player.add_log(f"💥 {msg}")
            return {"type": "hostile_attack", "npc": dict(npc), "message": msg}

        elif event_roll < 0.6:
            set_npc_dead(npc["id"])
            msg = (f"☠️ {npc['name']}因修行急功近利走火入魔，已身死道消。"
                   f"你少了一个仇敌。")
            self.player.add_log(f"💀 {msg}")
            return {"type": "hostile_died", "npc": dict(npc), "message": msg}
        else:
            revelation = random.randint(10, 30)
            self.player.add_cultivation(revelation)
            msg = (f"👁️ 你发现{npc['name']}在暗中谋划对你不利，"
                   f"提前防范并从中领悟到了{revelation}点修为。")
            self.player.add_log(f"🔍 {msg}")
            return {"type": "hostile_foiled", "npc": dict(npc), "message": msg}

    # ==================== 好友系统（NPC援助等） ====================

    def check_friendly_npc_events(self) -> Optional[dict]:
        """检查是否有友好NPC触发正面事件"""
        alive_npcs = get_alive_npcs(self.user_id)
        friendly_npcs = [n for n in alive_npcs if n["relationship"] >= 50]

        if not friendly_npcs or random.random() > 0.12:
            return None

        npc = random.choice(friendly_npcs)
        event_roll = random.random()

        if event_roll < 0.4:
            gift = random.randint(30, 100)
            self.player.add_cultivation(gift)
            msg = f"🎁 {npc['name']}送来了一份修炼资源！你获得了{gift}点修为。"
            add_relationship_event(
                user_id=self.user_id,
                npc_id=npc["id"],
                event_type="赠礼",
                description=f"赠送修炼资源：修为+{gift}",
                relationship_change=5,
                player_realm=self.player.get_realm_name(),
                player_realm_level=self.player.realm_level
            )
            self.player.add_log(f"🎁 {msg}")
            return {"type": "friendly_gift", "npc": dict(npc), "message": msg}

        elif event_roll < 0.7:
            heal = random.randint(10, 40)
            self.player.remaining_lifespan = min(
                self.player.max_lifespan,
                self.player.remaining_lifespan + heal
            )
            msg = f"💊 {npc['name']}送来了一枚延寿丹！你的寿命增加了{heal}年。"
            self.player.add_log(f"💊 {msg}")
            return {"type": "friendly_heal", "npc": dict(npc), "message": msg}
        else:
            insight = random.randint(20, 50)
            self.player.add_cultivation(insight)
            msg = (f"📖 {npc['name']}与你论道切磋，你从中获得了{insight}点修为感悟。")
            self.player.add_log(f"📖 {msg}")
            return {"type": "friendly_insight", "npc": dict(npc), "message": msg}

    # ==================== 结婚系统 ====================

    def try_marry_npc(self, npc_id: int) -> dict:
        """向NPC求婚"""
        npc = get_npc_by_id(npc_id)
        if not npc:
            return {"success": False, "message": "找不到该NPC。"}

        if npc["is_alive"] == 0:
            return {"success": False, "message": f"{npc['name']}已不在人世。"}

        if npc["is_married"]:
            return {"success": False, "message": f"{npc['name']}已有道侣。"}

        if get_married_npc(self.user_id):
            return {"success": False, "message": "你已有道侣，不可再婚。"}

        if self.player.realm_level < 5:
            return {"success": False, "message": "你修为尚浅（未到大学/化神期），不宜谈论婚嫁。"}

        relationship = npc["relationship"]
        if relationship < 60:
            return {"success": False, "message": f"你和{npc['name']}的关系还不够深厚（需要≥60，当前{relationship}）。"}

        success_chance = min(0.9, 0.3 + relationship * 0.006)
        if random.random() < success_chance:
            set_npc_married(npc_id, True)
            add_relationship_event(
                user_id=self.user_id,
                npc_id=npc_id,
                event_type="结婚",
                description=f"你与{npc['name']}喜结连理，成为道侣！",
                relationship_change=20,
                player_realm=self.player.get_realm_name(),
                player_realm_level=self.player.realm_level
            )
            self.player.add_log(f"💍 你与{npc['name']}结为道侣！双修可增加修为收益。")
            return {"success": True, "npc_name": npc["name"], "message": f"你与{npc['name']}喜结连理，从此携手共修大道！"}
        else:
            set_npc_relationship_direct(npc_id, relationship - 10)
            msg = f"{npc['name']}婉拒了你的求婚，关系略微下降。"
            self.player.add_log(f"💔 {msg}")
            return {"success": False, "message": msg}

    def apply_marriage_bonus(self, gain: int) -> int:
        """如果已婚，双修加成"""
        spouse = get_married_npc(self.user_id)
        if spouse and spouse["is_alive"]:
            bonus = int(gain * 0.15)
            return bonus
        return 0

    def _share_cultivation_with_partner(self, gain: int) -> Optional[dict]:
        """将修为共享给道侣和结拜兄弟NPC，并检查其境界提升"""
        from .config import PARTNER_CULTIVATION_SHARE_RATIO, SWORN_BROTHER_SHARE_RATIO, \
            PARTNER_NPC_REALM_UPGRADE_THRESHOLD
        from .database import get_partner_npc, get_sworn_brother_npc, update_npc_shared_cultivation, \
            update_npc_realm
        from .realms import get_realm_by_level, is_max_realm

        results = []

        # 1. 道侣修为共享
        partner = get_partner_npc(self.user_id)
        if partner:
            shared = int(gain * PARTNER_CULTIVATION_SHARE_RATIO)
            if shared > 0:
                total_shared = update_npc_shared_cultivation(partner["id"], shared)
                realm_upgraded = False
                new_level = partner["realm_level"]
                new_realm_name = partner["realm"]
                upgrade_count = (total_shared // PARTNER_NPC_REALM_UPGRADE_THRESHOLD) - \
                                ((total_shared - shared) // PARTNER_NPC_REALM_UPGRADE_THRESHOLD)
                if upgrade_count > 0:
                    for _ in range(upgrade_count):
                        if is_max_realm(new_level):
                            break
                        new_level += 1
                    if new_level > partner["realm_level"]:
                        new_realm_info = get_realm_by_level(new_level)
                        new_realm_name = new_realm_info["name"]
                        update_npc_realm(partner["id"], new_realm_name, new_level)
                        realm_upgraded = True
                msg = f"道侣{partner['name']}获得{shared}点共享修为"
                if realm_upgraded:
                    msg += f"，境界提升至【{new_realm_name}】"
                results.append({
                    "type": "partner",
                    "npc_name": partner["name"],
                    "shared_cultivation": shared,
                    "total_shared": total_shared,
                    "realm_upgraded": realm_upgraded,
                    "new_realm": new_realm_name if realm_upgraded else None,
                    "new_level": new_level if realm_upgraded else None,
                    "message": msg
                })

        # 2. 结拜兄弟修为共享
        sworn_brother = get_sworn_brother_npc(self.user_id)
        if sworn_brother:
            shared = int(gain * SWORN_BROTHER_SHARE_RATIO)
            if shared > 0:
                total_shared = update_npc_shared_cultivation(sworn_brother["id"], shared)
                realm_upgraded = False
                new_level = sworn_brother["realm_level"]
                new_realm_name = sworn_brother["realm"]
                upgrade_count = (total_shared // PARTNER_NPC_REALM_UPGRADE_THRESHOLD) - \
                                ((total_shared - shared) // PARTNER_NPC_REALM_UPGRADE_THRESHOLD)
                if upgrade_count > 0:
                    for _ in range(upgrade_count):
                        if is_max_realm(new_level):
                            break
                        new_level += 1
                    if new_level > sworn_brother["realm_level"]:
                        new_realm_info = get_realm_by_level(new_level)
                        new_realm_name = new_realm_info["name"]
                        update_npc_realm(sworn_brother["id"], new_realm_name, new_level)
                        realm_upgraded = True
                msg = f"结拜兄弟{sworn_brother['name']}获得{shared}点共享修为"
                if realm_upgraded:
                    msg += f"，境界提升至【{new_realm_name}】"
                results.append({
                    "type": "sworn_brother",
                    "npc_name": sworn_brother["name"],
                    "shared_cultivation": shared,
                    "total_shared": total_shared,
                    "realm_upgraded": realm_upgraded,
                    "new_realm": new_realm_name if realm_upgraded else None,
                    "new_level": new_level if realm_upgraded else None,
                    "message": msg
                })

        if not results:
            return None
        # 向后兼容：返回第一个结果，同时包含完整列表（使用副本避免环形引用）
        first = results[0]
        result = dict(first)
        result["all_shared"] = [dict(r) for r in results]
        return result

    @staticmethod
    def get_relationship_label(relationship: int, is_married: bool = False,
                                is_sworn_brother: bool = False) -> dict:
        """根据好感度获取关系等级标签"""
        from .config import NPC_RELATIONSHIP_LABELS, NPC_PARTNER_LABEL, \
            NPC_PARTNER_RELATIONSHIP_MIN, NPC_PARTNER_LABEL_CSS
        if is_married and relationship >= NPC_PARTNER_RELATIONSHIP_MIN:
            return {"label": NPC_PARTNER_LABEL, "css_class": NPC_PARTNER_LABEL_CSS}
        if is_sworn_brother and relationship >= NPC_PARTNER_RELATIONSHIP_MIN:
            return {"label": "结拜兄弟", "css_class": "rel-partner"}
        for tier in NPC_RELATIONSHIP_LABELS:
            low, high = tier["range"]
            if low <= relationship <= high:
                return {"label": tier["label"], "css_class": tier["css_class"]}
        return {"label": "中立", "css_class": "rel-neutral"}

    # ==================== 随机事件 ====================

    def _trigger_random_event(self) -> dict:
        """触发一个随机事件"""
        event_type = random.choice(["奇遇", "灾难", "机缘", "访客"])

        if event_type == "奇遇":
            npc = generate_event_npc(self.user_id, self.player.realm_level, "机缘偶遇")
            bonus = random.randint(20, 80)
            self.player.add_cultivation(bonus)
            msg = f"🌈 机缘巧合！你获得了一场意外的机缘，修为增加{bonus}点。"
            if npc:
                msg += f" 你在此次机缘中遇到了{npc['name']}。"
        elif event_type == "灾难":
            loss = random.randint(10, 40)
            self.player.reduce_cultivation(loss)
            cost = random.randint(2, 8)
            self.player.consume_lifespan(cost)
            msg = f"🌪️ 突遭变故！你损失了{loss}点修为，消耗了{cost}年寿命。"
        elif event_type == "机缘":
            gain = random.randint(30, 100)
            self.player.add_cultivation(gain)
            msg = f"🎁 天降机缘！你发现了一处前辈洞府，获得{gain}点修为。"
        else:
            npc = generate_event_npc(self.user_id, self.player.realm_level, "登门拜访")
            if npc:
                msg = f"🚪 有客来访！{npc['name']}（{npc['title']}）前来拜访你。"
            else:
                msg = "🚪 有客来访，但对方似乎只是路过。"

        self.player.add_log(f"🎲 {msg}")
        icon_map = {"奇遇": "🌈", "灾难": "🌪️", "机缘": "🎁", "访客": "🚪"}
        return {
            "type": event_type,
            "icon": icon_map.get(event_type, "📜"),
            "title": event_type,
            "message": msg,
            "description": msg
        }

    # ==================== 境界随机事件 ====================

    def _trigger_realm_random_event(self) -> Optional[dict]:
        """触发当前境界的随机事件（含预设选项）"""
        events = REALM_RANDOM_EVENTS.get(self.player.realm_level)
        if not events or random.random() > 0.25:
            return None

        event = random.choice(events)
        return {
            "type": "realm_random_event",
            "event_name": event["name"],
            "event_description": event["description"],
            "choices": event["choices"]
        }

    def _apply_realm_event_choice(self, event_name: str, choice_index: int) -> dict:
        """应用境界随机事件的选择结果"""
        events = REALM_RANDOM_EVENTS.get(self.player.realm_level)
        if not events:
            return {"success": False, "message": "找不到对应事件"}

        event = next((e for e in events if e["name"] == event_name), None)
        if not event or choice_index >= len(event["choices"]):
            return {"success": False, "message": "无效的选择"}

        choice = event["choices"][choice_index]
        cultivation_gain = choice.get("cultivation", 0)
        good_evil_change = choice.get("good_evil", 0)
        dao_heart_change = choice.get("dao_heart", 0)
        spirit_stones_change = choice.get("spirit_stones", 0)

        self.player.advance_turn()

        if cultivation_gain > 0:
            self.player.add_cultivation(cultivation_gain)
        elif cultivation_gain < 0:
            self.player.reduce_cultivation(abs(cultivation_gain))

        if good_evil_change != 0:
            self.player.add_good_evil(good_evil_change)

        if dao_heart_change != 0:
            self.player.add_dao_heart(dao_heart_change)

        if spirit_stones_change != 0:
            self.player.add_spirit_stones(spirit_stones_change)

        lifespan_cost = 1
        self.player.consume_lifespan(lifespan_cost)

        log_parts = [f"🎲 {event['description']} → {choice['text']}"]
        if cultivation_gain != 0:
            log_parts.append(f"修为 {'+' if cultivation_gain > 0 else ''}{cultivation_gain}")
        if good_evil_change != 0:
            log_parts.append(f"善恶 {'+' if good_evil_change > 0 else ''}{good_evil_change}")
        if dao_heart_change != 0:
            log_parts.append(f"道心 {'+' if dao_heart_change > 0 else ''}{dao_heart_change}")
        if spirit_stones_change != 0:
            log_parts.append(f"灵石 {'+' if spirit_stones_change > 0 else ''}{spirit_stones_change}")
        log_parts.append(f"寿命 -{lifespan_cost}年")
        self.player.add_log("，".join(log_parts))

        breakthrough_result = None
        if can_breakthrough(self.player.realm_level, self.player.cultivation):
            breakthrough_result = self._perform_breakthrough()

        death_result = self._check_death()
        self.save()

        return {
            "success": True,
            "event_name": event_name,
            "choice_text": choice["text"],
            "cultivation_gain": cultivation_gain,
            "good_evil_change": good_evil_change,
            "dao_heart_change": dao_heart_change,
            "spirit_stones_change": spirit_stones_change,
            "lifespan_cost": lifespan_cost,
            "breakthrough": breakthrough_result,
            "death": death_result,
            "game_state": self.get_game_state()
        }

    # ==================== 荒诞法则判词 ====================

    def _analyze_player_behavior(self) -> str:
        """分析玩家近期日志，判定行为倾向类别"""
        keywords = {
            "studious": ["学习", "上课", "读书", "刷题", "深造", "考研", "论文", "图书馆", "复习"],
            "slacker": ["摸鱼", "短视频", "摆烂", "发呆", "睡觉", "躺平", "偷懒"],
            "social": ["约会", "情书", "早恋", "社交", "联谊", "情书", "告白"],
            "worker": ["灵石", "打零工", "炒股", "兼职", "打工", "赚钱", "理财"],
            "dao_xin": ["道心", "功德", "善念", "悟道"],
        }
        scores = {cat: 0 for cat in keywords}
        recent_logs = self.player.logs[-80:] if len(self.player.logs) > 80 else self.player.logs
        for log in recent_logs:
            msg = log.message if hasattr(log, "message") else str(log)
            for cat, kw_list in keywords.items():
                if any(kw in msg for kw in kw_list):
                    scores[cat] += 1
        best = max(scores, key=scores.get)
        return best if scores[best] >= 3 else "general"

    def _get_absurd_verdict(self) -> Optional[str]:
        """根据玩家行为倾向生成个性化突破判词"""
        if not ABSURD_VERDICT_CATEGORIES:
            return None
        category = self._analyze_player_behavior()
        cat_data = ABSURD_VERDICT_CATEGORIES.get(category, ABSURD_VERDICT_CATEGORIES["general"])
        verdicts = cat_data["verdicts"]
        label = cat_data["label"]
        index = random.randint(0, len(verdicts) - 1)
        rule_number = random.randint(1, 999)
        verdict_text = verdicts[index].format(rule_number)
        return f"【{label}】{verdict_text}"

    # ==================== 死亡检测 ====================

    def _check_death(self) -> Optional[dict]:
        """检测玩家是否死亡"""
        if not self.player.is_alive:
            if self.player.realm_level >= 8 and self.player.phase == Player.PHASE_ENDED:
                if self.player.cultivation >= get_breakthrough_threshold(8):
                    return {
                        "is_dead": False,
                        "is_flyup": True,
                        "scene": get_death_scene("飞升")
                    }
            return {
                "is_dead": True,
                "type": "寿尽",
                "scene": get_death_scene("寿尽")
            }
        return None

    # ==================== 成就系统 ====================

    def _check_achievements(self) -> list:
        """检查所有成就，返回新解锁的成就列表"""
        init_achievements()
        npcs = get_npcs_for_display(self.user_id)
        new_achievements = check_all_achievements(self.player, self.user_id, npcs)
        for ach in new_achievements:
            self.player.add_log(f"🏆 解锁成就【{ach['name']}】- {ach['title']}")
            self.player.add_log(f"   {ach['description']}")
        return new_achievements

    # ==================== 生活事件系统 ====================

    def _trigger_life_event(self) -> Optional[dict]:
        """触发生活随机事件（小学后触发）"""
        if self.player.realm_level < 2:
            return None
        available = get_life_event_for_realm(self.player.realm_level)
        if not available:
            return None
        event = random.choice(available)
        return {
            "type": "life_event",
            "event": event,
            "message": f"【{event['name']}】{event['description']}"
        }

    # ==================== 工具方法 ====================

    def _error_result(self, message: str) -> dict:
        """返回错误结果"""
        self.player.add_log(f"❌ {message}")
        return {
            "phase": self.player.phase,
            "player": self.player.to_dict(),
            "error": message,
            "npcs": get_npcs_for_display(self.user_id)
        }

    def _format_npcs_for_prompt(self, npcs: list) -> str:
        """将NPC信息格式化为DeepSeek可读的文本"""
        if not npcs:
            return ""
        lines = []
        for npc in npcs:
            relation_label = "友善" if npc["relationship"] > 20 else "中立" if npc["relationship"] >= -10 else "敌对"
            married_label = "（道侣）" if npc.get("married") else ""
            lines.append(f"- {npc['name']}{married_label}（{npc['realm']}，关系度{npc['relationship']}，{relation_label}）")
        return "\n".join(lines)

    def get_game_state(self) -> dict:
        """获取完整的游戏状态"""
        state = {
            "phase": self.player.phase,
            "player": self.player.to_dict(),
            "npcs": get_npcs_for_display(self.user_id)
        }

        if self.player.phase == Player.PHASE_PRELUDE:
            prelude = get_prelude_step(self.player.prelude_step)
            state["prelude_step"] = prelude

        if self.player.phase == Player.PHASE_CULTIVATION:
            if self.player.career_path == "上班":
                from .config import WORK_EVENTS
                state["events"] = WORK_EVENTS
            else:
                state["events"] = get_preset_events(self.player.realm_level)

        return state


def create_new_game(user_id: int) -> GameEngine:
    """创建一个新游戏实例"""
    player = Player("道友")
    engine = GameEngine(player, user_id)
    engine.save()
    return engine


def load_existing_game(user_id: int) -> Optional[GameEngine]:
    """从数据库加载已有的游戏"""
    state = load_game_state(user_id)
    if not state:
        return create_new_game(user_id)

    player = Player(state.get("name", "道友"))
    player.realm_level = state.get("realm_level", 1)
    player.cultivation = state.get("cultivation", 0)
    player.max_lifespan = state.get("max_lifespan", 100)
    player.remaining_lifespan = state.get("remaining_lifespan", 100)
    player.is_alive = state.get("is_alive", True)
    player.phase = state.get("phase", Player.PHASE_PRELUDE)
    player.turn_count = state.get("turn_count", 0)
    player.prelude_step = state.get("prelude_step", 0)
    player.logs = state.get("logs", [])
    player.career_path = state.get("career_path")
    player.company_name = state.get("company_name")
    player.good_evil = state.get("good_evil", 0)
    player.dao_heart = state.get("dao_heart", 50)
    player.spirit_stones = state.get("spirit_stones", 0)

    # 加载四维属性（兼容旧存档）
    from .modules.attributes import ATTR_DEFAULT
    player.intelligence = state.get("intelligence", ATTR_DEFAULT)
    player.stamina = state.get("stamina", ATTR_DEFAULT)
    player.strength = state.get("strength", ATTR_DEFAULT)
    player.spirit = state.get("spirit", ATTR_DEFAULT)

    # 加载成就追踪统计
    player.minigame_count = state.get("minigame_count", 0)
    player.exam_count = state.get("exam_count", 0)
    player.work_earnings = state.get("work_earnings", 0)
    player.npc_encounter_count = state.get("npc_encounter_count", 0)
    player.has_breakthrough = state.get("has_breakthrough", False)
    player.achievements = state.get("achievements", [])

    return GameEngine(player, user_id)
