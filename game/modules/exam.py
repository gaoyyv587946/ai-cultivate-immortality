"""模拟考试模块
提供AI出题、答题评分功能，支持DeepSeek出题和本地题库回退
"""
import random
import json
from typing import Optional

from .attributes import ATTR_KEYS, ATTR_LABELS, clamp

SCHOOL_TIERS = ["小学", "初中", "高中", "大学", "研究生", "仙界"]

SCHOOL_SUBJECTS = {
    "小学": ["语文", "数学", "英语", "体育", "自然"],
    "初中": ["语文", "数学", "英语", "历史", "体育", "物理"],
    "高中": ["语文", "数学", "英语", "历史", "物理", "化学", "生物"],
    "大学": ["高等数学", "英语", "专业课", "文献阅读", "哲学"],
    "研究生": ["科研方法论", "论文写作", "专业前沿", "学术报告"],
    "仙界": ["天道法则", "仙术理论", "丹药学", "阵法基础", "灵兽驯养"],
}

MOCK_QUESTIONS = {
    "小学": [
        {"q": "请计算：18 + 25 = ？", "hint": "答案是一个两位数", "subject": "数学"},
        {"q": "请默写一句描写春天的古诗。", "hint": "例如：春眠不觉晓，处处闻啼鸟", "subject": "语文"},
        {"q": "\"apple\" 的中文翻译是什么？", "hint": "一种常见的水果", "subject": "英语"},
        {"q": "中国的首都是哪个城市？", "hint": "北京", "subject": "历史"},
        {"q": "跑步时应该用什么部位先着地？", "hint": "脚掌", "subject": "体育"},
    ],
    "初中": [
        {"q": "解一元一次方程：3x + 7 = 22，求 x 的值。", "hint": "x是一个整数", "subject": "数学"},
        {"q": "请简述《出师表》的作者和创作背景。", "hint": "三国时期的著名丞相", "subject": "语文"},
        {"q": "用英语描述一下你的周末计划（不少于30词）。", "hint": "用一般将来时", "subject": "英语"},
        {"q": "第一次鸦片战争爆发于哪一年？", "hint": "19世纪中期", "subject": "历史"},
        {"q": "篮球比赛中，三分线外投篮命中得多少分？", "hint": "3分", "subject": "体育"},
    ],
    "高中": [
        {"q": "已知函数 f(x)=2x²+3x-5，求 f(2) 的值。", "hint": "代入计算即可", "subject": "数学"},
        {"q": "请简要分析《红楼梦》中林黛玉的性格特点。", "hint": "多愁善感、才情出众", "subject": "语文"},
        {"q": "请将以下句子翻译成英文：\"活到老，学到老。\"", "hint": "It is never too old to learn", "subject": "英语"},
        {"q": "第二次世界大战的转折点是什么战役？", "hint": "苏联的一场保卫战", "subject": "历史"},
        {"q": "物体自由落体时，加速度约为多少？", "hint": "9.8", "subject": "物理"},
    ],
    "大学": [
        {"q": "求函数 y = x³ - 6x² + 9x + 1 的极值点。", "hint": "求导后令导数为0", "subject": "高等数学"},
        {"q": "请简述你对\"道可道，非常道\"的理解。", "hint": "道家核心思想", "subject": "哲学"},
        {"q": "TCP/IP协议中，三次握手的作用是什么？", "hint": "建立可靠连接", "subject": "专业课"},
        {"q": "请用英语写一段关于环境保护的短文（不少于50词）。", "hint": "关注碳排放、可持续发展", "subject": "英语"},
    ],
    "研究生": [
        {"q": "请简述你对\"知识图谱\"在自然语言处理中的应用理解。", "hint": "关注实体关系", "subject": "科研方法论"},
        {"q": "论文中引用文献时，应当注意哪些学术规范？", "hint": "避免抄袭", "subject": "论文写作"},
        {"q": "请用英语概括你所在领域的最新研究趋势。", "hint": "关注前沿方向", "subject": "专业前沿"},
    ],
    "仙界": [
        {"q": "天道法则中，\"因果循环\"对修仙者有何影响？", "hint": "善恶终有报", "subject": "天道法则"},
        {"q": "炼制元婴丹需要哪三种主药？", "hint": "千年灵芝、万年人参、龙涎草", "subject": "丹药学"},
        {"q": "请解释\"太极生两仪，两仪生四象\"的含义。", "hint": "道家宇宙观", "subject": "仙术理论"},
    ],
}

_question_id_counter = 0


def _next_qid() -> str:
    global _question_id_counter
    _question_id_counter += 1
    return f"exam_q_{_question_id_counter}"


def get_school_tier(school_name: str) -> str:
    for tier in SCHOOL_TIERS:
        if tier in school_name:
            return tier
    return "小学"


def generate_exam_question(player, user_id: Optional[int] = None) -> dict:
    """生成考试题目，优先使用DeepSeek，回退到本地题库"""
    school_tier = get_school_tier(player.get_school_name() if hasattr(player, 'get_school_name') else str(getattr(player, 'school_name', '小学')))

    question = _try_deepseek_question(player, school_tier, user_id)
    if question:
        return question
    return _mock_question(school_tier)


def _try_deepseek_question(player, school_tier: str, user_id: Optional[int] = None) -> Optional[dict]:
    """尝试用DeepSeek生成题目"""
    try:
        from ..deepseek import DEEPSEEK_API_KEY
        if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "your-api-key-here":
            return None
    except Exception:
        return None

    try:
        import requests
        from ..config import DEEPSEEK_API_KEY as api_key, DEEPSEEK_API_URL, DEEPSEEK_MODEL, DEEPSEEK_TIMEOUT
        from ..database import get_deepseek_call_count, get_user_by_id

        if user_id:
            from ..database import increment_deepseek_calls as _inc
            _inc(user_id)
            user = get_user_by_id(user_id)
            if user:
                user_dict = dict(user)
                limit = user_dict.get("deepseek_daily_limit") or 50
                current = get_deepseek_call_count(user_id)
                if current >= limit:
                    return None

        subjects = SCHOOL_SUBJECTS.get(school_tier, ["语文", "数学"])
        subject = random.choice(subjects)

        system_prompt = f"""你是一个修仙世界中的{school_tier}教师考官。请根据学生的当前阶段（{school_tier}），出一道{subject}题目。
要求：
1. 题目难度适合{school_tier}水平
2. 题目要简洁明了，有实际意义
3. 用JSON格式返回

返回格式：
{{{{
  "q": "题目内容",
  "hint": "提示信息",
  "subject": "{subject}"
}}}}"""

        response = requests.post(
            DEEPSEEK_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请为{school_tier}阶段的修仙者出一道{subject}题目。"}
                ],
                "temperature": 0.7,
                "max_tokens": 300
            },
            timeout=DEEPSEEK_TIMEOUT
        )

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(content[json_start:json_end])
                data["qid"] = _next_qid()
                return data
        return None
    except Exception:
        return None


def _mock_question(school_tier: str) -> dict:
    """从本地题库生成题目"""
    pool = MOCK_QUESTIONS.get(school_tier, MOCK_QUESTIONS["小学"])
    q = random.choice(pool)
    return {
        "qid": _next_qid(),
        "q": q["q"],
        "hint": q["hint"],
        "subject": q["subject"],
    }


def evaluate_exam_answer(player, question: dict, answer: str, user_id: Optional[int] = None) -> dict:
    """评估答案，返回评分和属性变化"""
    evaluation = _try_deepseek_evaluation(player, question, answer, user_id)
    if evaluation:
        return _apply_exam_result(player, evaluation)

    return _mock_evaluation(player, question, answer)


def _try_deepseek_evaluation(player, question: dict, answer: str, user_id: Optional[int] = None) -> Optional[dict]:
    """尝试用DeepSeek评估答案"""
    try:
        from ..deepseek import DEEPSEEK_API_KEY
        if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "your-api-key-here":
            return None
    except Exception:
        return None

    try:
        import requests
        from ..config import DEEPSEEK_API_KEY as api_key, DEEPSEEK_API_URL, DEEPSEEK_MODEL, DEEPSEEK_TIMEOUT
        from ..database import get_deepseek_call_count, get_user_by_id

        if user_id:
            from ..database import increment_deepseek_calls as _inc
            _inc(user_id)
            user = get_user_by_id(user_id)
            if user:
                user_dict = dict(user)
                limit = user_dict.get("deepseek_daily_limit") or 50
                current = get_deepseek_call_count(user_id)
                if current >= limit:
                    return None

        system_prompt = """你是一个修仙世界中的考官。请评估学生的答案，给出评分和评语。
评分标准：
- 90-100分：回答非常出色，完美切题
- 70-89分：回答良好，基本正确
- 50-69分：回答一般，部分正确
- 30-49分：回答较差，偏离题意
- 0-29分：未作答或完全不相关

用JSON格式返回：
{
  "score": 评分（整数，0-100）,
  "comment": "评语（15-40字，生动有趣，结合修仙风格）"
}"""

        user_message = f"【题目】{question.get('q', '')}\n【提示】{question.get('hint', '')}\n【学生的答案】{answer}"

        response = requests.post(
            DEEPSEEK_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.5,
                "max_tokens": 300
            },
            timeout=DEEPSEEK_TIMEOUT
        )

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(content[json_start:json_end])
        return None
    except Exception:
        return None


def _mock_evaluation(player, question: dict, answer: str) -> dict:
    """本地模拟评估"""
    score = _mock_score(len(answer.strip()))
    if score >= 70:
        comment = random.choice([
            "不错！你的答案颇有见地，仙基扎实！",
            "答得很好，可见你平日用功修炼！",
            "优秀！这份答案让为师甚感欣慰。",
        ])
    elif score >= 40:
        comment = random.choice([
            "马马虎虎，还需继续努力修炼。",
            "答对了一半，回去再好好参悟。",
            "中规中矩，尚有提升空间。",
        ])
    else:
        comment = random.choice([
            "唉，你这答的是啥？回去面壁思过！",
            "太过敷衍！修仙之路岂能如此马虎！",
            "不及格！罚你抄写《道经》一百遍！",
        ])
    return {"score": score, "comment": comment}


def _mock_score(answer_len: int) -> int:
    if answer_len < 2:
        return random.randint(0, 20)
    elif answer_len < 10:
        return random.randint(20, 55)
    elif answer_len < 30:
        return random.randint(40, 75)
    else:
        return random.randint(60, 95)


def _apply_exam_result(player, evaluation: dict) -> dict:
    """根据评估结果应用属性变化"""
    score = evaluation.get("score", 50)
    comment = evaluation.get("comment", "考试结束。")

    cultivation_gain = max(5, int(score * 0.6))
    lifespan_cost = 1

    attr_changes = {}
    if score >= 80:
        attr_changes["intelligence"] = random.randint(2, 4)
        attr_changes["spirit"] = random.randint(1, 3)
    elif score >= 50:
        attr_changes["intelligence"] = random.randint(1, 2)
    else:
        attr_changes["intelligence"] = random.randint(-2, 0)
        attr_changes["spirit"] = random.randint(-2, 0)

    actual_attr_changes = {}
    for attr_key, delta in attr_changes.items():
        old_val = getattr(player, attr_key)
        from .attributes import modify_attr
        new_val, actual = modify_attr(old_val, delta)
        setattr(player, attr_key, new_val)
        if actual != 0:
            actual_attr_changes[attr_key] = actual

    player.add_cultivation(cultivation_gain)
    player.consume_lifespan(lifespan_cost)

    attr_text = "，".join(
        f"{ATTR_LABELS.get(k, k)} {'+' if v > 0 else ''}{v}"
        for k, v in actual_attr_changes.items()
    ) if actual_attr_changes else ""

    return {
        "score": score,
        "comment": comment,
        "cultivation_gain": cultivation_gain,
        "lifespan_cost": lifespan_cost,
        "attr_changes": actual_attr_changes,
        "attr_text": attr_text,
    }


# ==================== 分科出题（语文/数学/英语/历史/地理） ====================

SUBJECT_MOCK_QUESTIONS = {
    ("小学", "语文"): [
        {"q": "请默写《静夜思》的前两句（床前明月光，疑是地上霜）。", "correct_answer": "床前明月光，疑是地上霜", "topic": "古诗默写"},
        {"q": "“春眠不觉晓，处处闻啼鸟”出自哪首诗？作者是谁？", "correct_answer": "春晓，孟浩然", "topic": "古诗常识"},
        {"q": "请写出三个带有“日”字的汉字。", "correct_answer": "明、晴、星", "topic": "汉字识记"},
        {"q": "“举头望明月”的下一句是什么？", "correct_answer": "低头思故乡", "topic": "古诗接龙"},
        {"q": "请写出一个ABB式的词语（如：红彤彤）。", "correct_answer": "绿油油", "topic": "词语积累"},
    ],
    ("小学", "数学"): [
        {"q": "25 + 38 = ？请直接给出答案。", "correct_answer": "63", "topic": "加法运算"},
        {"q": "100 - 45 = ？请直接给出答案。", "correct_answer": "55", "topic": "减法运算"},
        {"q": "小明有12个苹果，吃了5个，还剩几个？", "correct_answer": "7个", "topic": "应用题"},
        {"q": "6 × 7 = ？请直接给出答案。", "correct_answer": "42", "topic": "乘法口诀"},
        {"q": "把15平均分成3份，每份是多少？", "correct_answer": "5", "topic": "平均分"},
    ],
    ("小学", "英语"): [
        {"q": "\"apple\" 的中文翻译是什么？", "correct_answer": "苹果", "topic": "单词翻译"},
        {"q": "用英语说“你好”。", "correct_answer": "hello", "topic": "日常用语"},
        {"q": "\"猫\" 的英文单词是什么？", "correct_answer": "cat", "topic": "动物单词"},
        {"q": "英语字母表中共有多少个字母？", "correct_answer": "26个", "topic": "字母常识"},
        {"q": "\"红色\" 用英语怎么说？", "correct_answer": "red", "topic": "颜色单词"},
    ],
    ("小学", "历史"): [
        {"q": "中国的首都是哪个城市？", "correct_answer": "北京", "topic": "首都常识"},
        {"q": "中国古代四大发明是什么？", "correct_answer": "造纸术、印刷术、火药、指南针", "topic": "四大发明"},
        {"q": "孔子是哪个学派的创始人？", "correct_answer": "儒家", "topic": "古代思想"},
        {"q": "我国现任国家主席是谁？（2020年代）", "correct_answer": "习近平", "topic": "现代中国"},
        {"q": "长城最早修建于哪个朝代？", "correct_answer": "秦朝", "topic": "古代建筑"},
    ],
    ("小学", "地理"): [
        {"q": "世界上最大的洋是什么？", "correct_answer": "太平洋", "topic": "海洋常识"},
        {"q": "中国的母亲河——黄河，最终流入哪个海？", "correct_answer": "渤海", "topic": "中国河流"},
        {"q": "地球有几大洲？", "correct_answer": "七大洲", "topic": "大洲常识"},
        {"q": "太阳从哪个方向升起？", "correct_answer": "东方", "topic": "自然常识"},
        {"q": "我国面积最大的省级行政区是哪个？", "correct_answer": "新疆", "topic": "中国地理"},
    ],
    ("初中", "语文"): [
        {"q": "《出师表》的作者是谁？他是哪个朝代的？", "correct_answer": "诸葛亮，三国时期", "topic": "文言文常识"},
        {"q": "“长风破浪会有时”的下一句是什么？", "correct_answer": "直挂云帆济沧海", "topic": "古诗名句"},
        {"q": "请简要说明“比喻”这种修辞手法的特点。", "correct_answer": "用类似的事物来打比方", "topic": "修辞手法"},
        {"q": "《水浒传》的作者是谁？", "correct_answer": "施耐庵", "topic": "名著常识"},
        {"q": "“但愿人长久，千里共婵娟”出自谁的哪首词？", "correct_answer": "苏轼的《水调歌头》", "topic": "宋词赏析"},
    ],
    ("初中", "数学"): [
        {"q": "解方程：2x + 5 = 15，x = ？", "correct_answer": "5", "topic": "一元一次方程"},
        {"q": "一个直角三角形的两条直角边分别为3和4，斜边是多少？", "correct_answer": "5", "topic": "勾股定理"},
        {"q": "(-3) + (-7) = ？", "correct_answer": "-10", "topic": "有理数运算"},
        {"q": "已知圆的半径为5，求圆的面积（π取3.14）。", "correct_answer": "78.5", "topic": "圆的面积"},
        {"q": "数据 2,4,6,8,10 的平均数是多少？", "correct_answer": "6", "topic": "统计初步"},
    ],
    ("初中", "英语"): [
        {"q": "用英语翻译“我是一名学生”。", "correct_answer": "I am a student", "topic": "简单翻译"},
        {"q": "“go”的过去式是什么？", "correct_answer": "went", "topic": "动词时态"},
        {"q": "请写出“美丽的”的英文单词。", "correct_answer": "beautiful", "topic": "形容词"},
        {"q": "“What time is it?” 的中文意思是什么？", "correct_answer": "几点了", "topic": "日常对话"},
        {"q": "请写出“图书馆”的英文单词。", "correct_answer": "library", "topic": "名词积累"},
    ],
    ("初中", "历史"): [
        {"q": "第一次鸦片战争爆发于哪一年？", "correct_answer": "1840年", "topic": "近代史开端"},
        {"q": "戊戌变法的主要领导人是谁？", "correct_answer": "康有为、梁启超", "topic": "维新运动"},
        {"q": "辛亥革命发生在哪一年？", "correct_answer": "1911年", "topic": "民主革命"},
        {"q": "《南京条约》是中国近代史上第一个不平等条约吗？", "correct_answer": "是", "topic": "条约常识"},
        {"q": "红军长征途中召开的具有转折意义的会议是什么？", "correct_answer": "遵义会议", "topic": "革命史"},
    ],
    ("初中", "地理"): [
        {"q": "世界上面积最大的国家是？", "correct_answer": "俄罗斯", "topic": "国家地理"},
        {"q": "赤道的周长大约是多少公里？", "correct_answer": "约4万公里", "topic": "地球知识"},
        {"q": "秦岭—淮河一线大致是哪两个温度带的分界线？", "correct_answer": "暖温带和亚热带", "topic": "中国地理"},
        {"q": "长江干流流经多少个省级行政区？", "correct_answer": "11个", "topic": "中国河流"},
        {"q": "亚洲与非洲的分界线是什么？", "correct_answer": "苏伊士运河", "topic": "大洲分界"},
    ],
    ("高中", "语文"): [
        {"q": "《红楼梦》中“黛玉葬花”体现了林黛玉怎样的性格特征？", "correct_answer": "多愁善感、孤傲清高", "topic": "名著人物分析"},
        {"q": "“落霞与孤鹜齐飞，秋水共长天一色”出自哪篇古文？", "correct_answer": "《滕王阁序》", "topic": "古文名句"},
        {"q": "请简述苏轼词作的艺术特色。", "correct_answer": "豪放洒脱、意境开阔", "topic": "宋词艺术"},
        {"q": "鲁迅的《狂人日记》是中国第一部什么体式的白话小说？", "correct_answer": "现代白话小说", "topic": "现代文学"},
        {"q": "“无边落木萧萧下，不尽长江滚滚来”的作者是谁？", "correct_answer": "杜甫", "topic": "唐诗赏析"},
    ],
    ("高中", "数学"): [
        {"q": "求函数 f(x)=x²-4x+3 的对称轴方程。", "correct_answer": "x=2", "topic": "二次函数"},
        {"q": "sin²30° + cos²30° = ？", "correct_answer": "1", "topic": "三角恒等式"},
        {"q": "等差数列 3, 7, 11, 15, ... 的第10项是多少？", "correct_answer": "39", "topic": "数列"},
        {"q": "已知向量 a=(1,2)，b=(3,4)，求 a·b。", "correct_answer": "11", "topic": "向量运算"},
        {"q": "圆心在(0,0)半径为1的圆的标准方程是什么？", "correct_answer": "x²+y²=1", "topic": "解析几何"},
    ],
    ("高中", "英语"): [
        {"q": "请将以下句子改为被动语态：\"He wrote a letter.\"", "correct_answer": "A letter was written by him", "topic": "被动语态"},
        {"q": "“environment”的中文意思是什么？", "correct_answer": "环境", "topic": "高频词汇"},
        {"q": "用英语表达“我本来打算去，但太忙了”。", "correct_answer": "I had intended to go, but was too busy", "topic": "虚拟语气"},
        {"q": "“not only...but also...”连接两个主语时，谓语动词遵循什么原则？", "correct_answer": "就近原则", "topic": "语法结构"},
        {"q": "请写出“university”的冠词用法（a/an）。", "correct_answer": "a university", "topic": "冠词用法"},
    ],
    ("高中", "历史"): [
        {"q": "第一次世界大战爆发的导火索是什么？", "correct_answer": "萨拉热窝事件", "topic": "世界史"},
        {"q": "文艺复兴运动最早兴起于哪个国家？", "correct_answer": "意大利", "topic": "欧洲文化史"},
        {"q": "明治维新的核心口号是什么？", "correct_answer": "富国强兵", "topic": "日本近代史"},
        {"q": "1929-1933年经济大危机首先爆发于哪个国家？", "correct_answer": "美国", "topic": "世界经济史"},
        {"q": "中国加入世界贸易组织（WTO）是在哪一年？", "correct_answer": "2001年", "topic": "当代中国"},
    ],
    ("高中", "地理"): [
        {"q": "地球内部圈层从外到内依次是什么？", "correct_answer": "地壳、地幔、地核", "topic": "地球圈层"},
        {"q": "影响气候的主要因素有哪些？", "correct_answer": "纬度、海陆位置、地形", "topic": "气候因素"},
        {"q": "我国南水北调工程主要解决什么问题？", "correct_answer": "水资源分布不均", "topic": "资源调配"},
        {"q": "板块构造学说中，喜马拉雅山脉是如何形成的？", "correct_answer": "印度洋板块与亚欧板块碰撞", "topic": "板块运动"},
        {"q": "城市化过程中可能出现哪些环境问题？", "correct_answer": "热岛效应、污染", "topic": "城市地理"},
    ],
}


def get_school_tier_for_subject(player) -> str:
    school_name = player.get_school_name() if hasattr(player, 'get_school_name') else getattr(player, 'school_name', '小学')
    for tier in SCHOOL_TIERS:
        if tier in school_name:
            return tier
    return "小学"


def generate_subject_question(player, subject: str, user_id: Optional[int] = None) -> dict:
    """生成指定科目的题目，AI优先，本地题库回退"""
    school_tier = get_school_tier_for_subject(player)
    question = _try_deepseek_subject_question(player, school_tier, subject, user_id)
    if question:
        return question
    return _mock_subject_question(school_tier, subject)


def _try_deepseek_subject_question(player, school_tier: str, subject: str, user_id: Optional[int] = None) -> Optional[dict]:
    try:
        from ..deepseek import DEEPSEEK_API_KEY
        if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "your-api-key-here":
            return None
    except Exception:
        return None

    try:
        import requests
        from ..config import DEEPSEEK_API_KEY as api_key, DEEPSEEK_API_URL, DEEPSEEK_MODEL, DEEPSEEK_TIMEOUT
        from ..database import get_deepseek_call_count

        if user_id:
            from ..database import increment_deepseek_calls as _inc
            _inc(user_id)
            user_row = None
            from ..database import get_user_by_id
            user_row = get_user_by_id(user_id)
            if user_row:
                user_dict = dict(user_row)
                limit = user_dict.get("deepseek_daily_limit") or 50
                current = get_deepseek_call_count(user_id)
                if current >= limit:
                    return None

        system_prompt = f"""你是一个{school_tier}{subject}教师。请出一道{school_tier}水平的{subject}题目。
要求：
1. 题目难度适合{school_tier}水平
2. 题目简洁明了，附有标准答案
3. 用JSON格式返回

返回格式：
{{{{
  "q": "题目内容",
  "correct_answer": "标准答案",
  "topic": "本题知识点"
}}}}"""

        response = requests.post(
            DEEPSEEK_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请为{school_tier}阶段的学生出一道{subject}题目。"}
                ],
                "temperature": 0.7,
                "max_tokens": 300
            },
            timeout=DEEPSEEK_TIMEOUT
        )

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(content[json_start:json_end])
                data["qid"] = _next_qid()
                return data
        return None
    except Exception:
        return None


def _mock_subject_question(school_tier: str, subject: str) -> dict:
    pool = SUBJECT_MOCK_QUESTIONS.get((school_tier, subject))
    if not pool:
        pool = SUBJECT_MOCK_QUESTIONS.get(("小学", subject), SUBJECT_MOCK_QUESTIONS.get(("小学", "语文")))
        if not pool:
            pool = [{"q": "请简述你的学习心得。", "correct_answer": "勤奋", "topic": "综合"}]
    q = random.choice(pool)
    return {
        "qid": _next_qid(),
        "q": q["q"],
        "correct_answer": q["correct_answer"],
        "topic": q.get("topic", subject),
    }


def evaluate_subject_answer(player, question: dict, answer: str, user_id: Optional[int] = None) -> dict:
    """评估科目答案，AI判断正确/错误"""
    evaluation = _try_deepseek_subject_judge(question, answer, user_id)
    if evaluation:
        return _apply_subject_result(player, evaluation)

    return _mock_subject_judge(player, question, answer)


def _try_deepseek_subject_judge(question: dict, answer: str, user_id: Optional[int] = None) -> Optional[dict]:
    try:
        from ..deepseek import DEEPSEEK_API_KEY
        if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "your-api-key-here":
            return None
    except Exception:
        return None

    try:
        import requests
        from ..config import DEEPSEEK_API_KEY as api_key, DEEPSEEK_API_URL, DEEPSEEK_MODEL, DEEPSEEK_TIMEOUT
        from ..database import get_deepseek_call_count

        if user_id:
            from ..database import increment_deepseek_calls as _inc
            _inc(user_id)
            user_row = None
            from ..database import get_user_by_id
            user_row = get_user_by_id(user_id)
            if user_row:
                user_dict = dict(user_row)
                limit = user_dict.get("deepseek_daily_limit") or 50
                current = get_deepseek_call_count(user_id)
                if current >= limit:
                    return None

        system_prompt = """你是严格但公正的老师，请判断学生的答案是否正确。
返回格式（JSON）：
{
  "correct": true/false,
  "comment": "10-30字评语，生动有趣",
  "reference_answer": "标准参考答案"
}"""

        user_message = f"【题目】{question.get('q', '')}\n【标准答案参考】{question.get('correct_answer', '')}\n【学生答案】{answer}"

        response = requests.post(
            DEEPSEEK_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.3,
                "max_tokens": 300
            },
            timeout=DEEPSEEK_TIMEOUT
        )

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(content[json_start:json_end])
        return None
    except Exception:
        return None


def _mock_subject_judge(player, question: dict, answer: str) -> dict:
    answer = answer.strip()
    correct_ref = question.get("correct_answer", "").strip()
    if not correct_ref:
        correct = len(answer) >= 3
        comment = "回答得不错！" if correct else "请认真作答！"
        return {"correct": correct, "comment": comment, "reference_answer": correct_ref}

    clean_ans = answer.replace(" ", "").replace("，", ",").replace("。", ".")
    clean_ref = correct_ref.replace(" ", "").replace("，", ",").replace("。", ".")
    correct = clean_ans in clean_ref or clean_ref in clean_ans or len(set(clean_ans) & set(clean_ref)) > max(len(clean_ref)*0.5, 2)
    if correct:
        comment = random.choice(["回答正确！看来你学得很扎实！", "完全正确，继续加油！", "没错，根基很稳！"])
    else:
        comment = random.choice(["答错了，再想想？", "不太对哦，回去复习一下吧。", "错误，正确答案是：" + correct_ref])
    return {"correct": correct, "comment": comment, "reference_answer": correct_ref}


def _apply_subject_result(player, evaluation: dict) -> dict:
    correct = evaluation.get("correct", False)
    comment = evaluation.get("comment", "")
    reference_answer = evaluation.get("reference_answer", "")

    if correct:
        cultivation_gain = random.randint(15, 35)
        player.add_cultivation(cultivation_gain)
        attr_boost = random.choice(["intelligence", "spirit"])
        old_val = getattr(player, attr_boost)
        from .attributes import modify_attr
        new_val, actual = modify_attr(old_val, 1)
        setattr(player, attr_boost, new_val)
        return {
            "correct": True,
            "comment": comment,
            "cultivation_gain": cultivation_gain,
            "attr_boost": attr_boost,
            "attr_text": f"{ATTR_LABELS.get(attr_boost, attr_boost)}+1" if actual != 0 else "",
            "reference_answer": reference_answer,
        }
    else:
        cultivation_gain = random.randint(2, 6)
        player.add_cultivation(cultivation_gain)
        return {
            "correct": False,
            "comment": comment,
            "cultivation_gain": cultivation_gain,
            "attr_boost": None,
            "attr_text": "",
            "reference_answer": reference_answer,
        }
