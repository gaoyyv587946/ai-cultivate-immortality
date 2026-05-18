"""数据模型模块
定义玩家类 Player 及游戏状态管理
"""

import random
from .config import REALMS
from .realms import get_realm_by_level, get_max_realm_level, calculate_lifespan, format_realm_info


class Player:
    """玩家类，管理玩家的所有状态数据"""

    # 游戏阶段常量
    PHASE_PRELUDE = "prelude"       # 前世凡人生涯
    PHASE_CULTIVATION = "cultivation"  # 修仙之旅
    PHASE_ENDED = "ended"           # 游戏结束

    def __init__(self, name: str = "玩家"):
        self.name = name

        # ---- 修仙状态 ----
        self.realm_level = 1                  # 当前境界等级 1-8
        self.cultivation = 0                  # 当前修为值
        self.max_lifespan = calculate_lifespan(1)  # 最大寿命
        self.remaining_lifespan = self.max_lifespan  # 剩余寿命
        self.is_alive = True

        # ---- 游戏阶段 ----
        self.phase = self.PHASE_PRELUDE
        self.turn_count = 0                    # 回合计数

        # ---- 前世状态（叙事用） ----
        self.prelude_step = 0                  # 前世的叙事进度

        # ---- 职业路线（化神/大学后） ----
        self.career_path = None                # None/"飞升"/"上班"
        self.company_name = None               # 上班时的公司名称

        # ---- 善恶度 & 道心值 ----
        self.good_evil = 0                     # 善恶度 (-100~100)，正为善，负为恶
        self.dao_heart = 50                    # 道心值 (0~100)，初始50

        # ---- 四维属性（智力/体力/力量/精神，范围 0~100，初始 50） ----
        self.intelligence = 50
        self.stamina = 50
        self.strength = 50
        self.spirit = 50

        # ---- 灵石 ----
        self.spirit_stones = 0                 # 灵石数量

        # ---- 成就追踪统计 ----
        self.minigame_count = 0                # 完成小游戏次数
        self.exam_count = 0                    # 完成考试次数
        self.work_earnings = 0                 # 打工总收入（灵石）
        self.npc_encounter_count = 0            # 遭遇NPC搭讪次数
        self.has_breakthrough = False           # 是否已突破至少一次
        self.achievements = []                 # 已解锁成就ID列表

        # ---- 日志 ----
        self.logs = []                         # 事件日志列表
        self._add_log("你的故事即将开始...")

    def get_realm(self) -> dict:
        """获取当前境界信息"""
        return get_realm_by_level(self.realm_level)

    def get_realm_name(self) -> str:
        """获取当前境界名称"""
        return self.get_realm()["name"]

    def get_school_name(self) -> str:
        """获取当前学校名称"""
        return self.get_realm()["school"]

    def get_realm_info(self) -> str:
        """获取格式化境界信息"""
        return format_realm_info(self.realm_level)

    def get_cultivation_progress(self) -> float:
        """获取修为突破进度（百分比，0-100）"""
        threshold = self.get_realm()["breakthrough_threshold"]
        return min(100, round(self.cultivation / threshold * 100, 1))

    def get_cost_multiplier(self) -> float:
        """获取寿命消耗倍率"""
        return self.get_realm()["cost_multiplier"]

    def add_cultivation(self, amount: int) -> int:
        """增加修为，返回实际增加的数值"""
        actual = max(0, amount)
        self.cultivation += actual
        return actual

    def add_good_evil(self, amount: int) -> int:
        """增减善恶度，范围限制在 -100~100，返回实际变化值"""
        clamped = max(-100, min(100, amount))
        self.good_evil = max(-100, min(100, self.good_evil + clamped))
        return clamped

    def add_dao_heart(self, amount: int) -> int:
        """增减道心值，范围 0~100，返回实际变化值"""
        old = self.dao_heart
        self.dao_heart = max(0, min(100, self.dao_heart + amount))
        return self.dao_heart - old

    def add_spirit_stones(self, amount: int) -> int:
        """增减灵石，返回实际变化值（灵石可为负表示欠债）"""
        self.spirit_stones += amount
        return amount

    def reduce_cultivation(self, amount: int) -> int:
        """减少修为（如走火入魔），修为不低于0"""
        actual = min(self.cultivation, max(0, amount))
        self.cultivation -= actual
        return actual

    def consume_lifespan(self, years: int) -> int:
        """
        消耗寿命，考虑境界倍率
        返回实际消耗的寿命值；若寿命耗尽则标记死亡
        """
        multiplier = self.get_cost_multiplier()
        actual_cost = max(1, int(years * multiplier))
        self.remaining_lifespan -= actual_cost
        if self.remaining_lifespan <= 0:
            self.remaining_lifespan = 0
            self.is_alive = False
            self.phase = self.PHASE_ENDED
        return actual_cost

    def try_breakthrough(self) -> dict:
        """
        尝试突破到下一境界
        返回突破结果字典：
        {
            "success": bool,
            "old_realm": str,
            "new_realm": str,
            "message": str
        }
        """
        old_realm = self.get_realm_info()
        current_realm = self.get_realm()

        # 已到最高境界
        if self.realm_level >= get_max_realm_level():
            if self.cultivation >= current_realm["breakthrough_threshold"]:
                self.phase = self.PHASE_ENDED
                return {
                    "success": True,
                    "old_realm": old_realm,
                    "new_realm": "飞升",
                    "message": "大乘圆满，功德具足，你感觉天地间一股伟力降下，接引你飞升仙界！"
                }
            return {"success": False, "message": "你已是最强境界，还需继续积累。"}

        # 修为不够
        if self.cultivation < current_realm["breakthrough_threshold"]:
            return {"success": False, "message": "修为不足以突破，还需继续修炼。"}

        # 突破判定：当前境界越高，突破越难
        base_chance = 0.9 - (self.realm_level - 1) * 0.08
        success_chance = max(0.3, base_chance)
        success = random.random() < success_chance

        if success:
            self.realm_level += 1
            new_realm = self.get_realm()
            # 突破后重新计算寿命
            new_max_lifespan = calculate_lifespan(self.realm_level)
            lifespan_gain = new_max_lifespan - calculate_lifespan(self.realm_level - 1)
            self.max_lifespan = new_max_lifespan
            self.remaining_lifespan += lifespan_gain
            return {
                "success": True,
                "old_realm": old_realm,
                "new_realm": self.get_realm_info(),
                "message": f"你成功突破至{self.get_realm_info()}！寿命增加了{lifespan_gain}年！"
            }
        else:
            # 突破失败，扣除部分修为
            penalty = int(self.cultivation * 0.3)
            self.cultivation -= penalty
            return {
                "success": False,
                "old_realm": old_realm,
                "new_realm": old_realm,
                "message": f"突破失败！修为倒退，损失了{penalty}点修为。"
            }

    def _add_log(self, message: str):
        """添加事件日志"""
        self.logs.append({"turn": self.turn_count, "message": message})

    def add_log(self, message: str):
        """公开的日志添加接口"""
        self._add_log(message)

    def get_logs(self, limit: int = 20) -> list:
        """获取最近的事件日志"""
        return self.logs[-limit:]

    def advance_turn(self):
        """推进一个回合"""
        self.turn_count += 1

    def to_dict(self) -> dict:
        """
        将玩家状态序列化为字典（用于传给前端）
        """
        realm = self.get_realm()
        return {
            "name": self.name,
            "phase": self.phase,
            "prelude_step": self.prelude_step,
            "realm_level": self.realm_level,
            "realm_name": realm["name"],
            "school_name": realm["school"],
            "realm_description": realm["description"],
            "cultivation": self.cultivation,
            "breakthrough_threshold": realm["breakthrough_threshold"],
            "progress": self.get_cultivation_progress(),
            "max_lifespan": self.max_lifespan,
            "remaining_lifespan": self.remaining_lifespan,
            "is_alive": self.is_alive,
            "turn_count": self.turn_count,
            "career_path": self.career_path,
            "company_name": self.company_name,
            "good_evil": self.good_evil,
            "dao_heart": self.dao_heart,
            "intelligence": self.intelligence,
            "stamina": self.stamina,
            "strength": self.strength,
            "spirit": self.spirit,
            "spirit_stones": self.spirit_stones,
            "minigame_count": self.minigame_count,
            "exam_count": self.exam_count,
            "work_earnings": self.work_earnings,
            "npc_encounter_count": self.npc_encounter_count,
            "has_breakthrough": self.has_breakthrough,
            "achievements": self.achievements,
            "logs": self.get_logs(30)
        }

    def force_death(self, reason: str):
        """强制玩家死亡（意外暴毙）"""
        self.is_alive = False
        self.phase = self.PHASE_ENDED
        self._add_log(f"☠️ {reason}")
