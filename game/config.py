"""全局配置文件
包含 DeepSeek API 配置、各境界参数、游戏平衡性参数等
"""

# ==================== DeepSeek API 配置 ====================
# 在这里填入你的 DeepSeek API Key
DEEPSEEK_API_KEY = "your-api-key-here"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# ==================== 境界体系配置 ====================
# 8个境界：幼儿园(练气) → 小学(筑基) → 初中(结丹) → 高中(元婴)
#         → 大学(化神) → 硕士(炼虚) → 博士(合体) → 博士后(大乘)
REALMS = [
    {
        "id": 1,
        "name": "练气期",
        "school": "幼儿园",
        "base_lifespan": 100,        # 基础寿命（年）
        "breakthrough_threshold": 100, # 突破所需修为
        "cost_multiplier": 1.0,       # 寿命消耗倍率
        "description": "感气入门，引气入体，初窥修仙门径"
    },
    {
        "id": 2,
        "name": "筑基期",
        "school": "小学",
        "base_lifespan": 200,
        "breakthrough_threshold": 300,
        "cost_multiplier": 1.5,
        "description": "筑就道基，巩固根基，脱胎换骨"
    },
    {
        "id": 3,
        "name": "结丹期",
        "school": "初中",
        "base_lifespan": 500,
        "breakthrough_threshold": 800,
        "cost_multiplier": 2.0,
        "description": "凝结金丹，真元汇聚，实力大增"
    },
    {
        "id": 4,
        "name": "元婴期",
        "school": "高中",
        "base_lifespan": 1000,
        "breakthrough_threshold": 2000,
        "cost_multiplier": 3.0,
        "description": "元婴出窍，神识外放，可御器飞行"
    },
    {
        "id": 5,
        "name": "化神期",
        "school": "大学",
        "base_lifespan": 2000,
        "breakthrough_threshold": 5000,
        "cost_multiplier": 4.0,
        "description": "化神成道，天人感应，领悟法则"
    },
    {
        "id": 6,
        "name": "炼虚期",
        "school": "硕士",
        "base_lifespan": 5000,
        "breakthrough_threshold": 12000,
        "cost_multiplier": 5.0,
        "description": "炼虚合道，虚空造物，神通自生"
    },
    {
        "id": 7,
        "name": "合体期",
        "school": "博士",
        "base_lifespan": 10000,
        "breakthrough_threshold": 30000,
        "cost_multiplier": 6.0,
        "description": "天人合一，身化天地，接近大道"
    },
    {
        "id": 8,
        "name": "大乘期",
        "school": "博士后",
        "base_lifespan": 20000,
        "breakthrough_threshold": 80000,
        "cost_multiplier": 8.0,
        "description": "大乘圆满，飞升在即，超凡入圣"
    }
]

# ==================== 游戏平衡参数 ====================
# 每次行动的基准寿命消耗（年）
BASE_ACTION_COST = 1

# 预设事件的基础修为收益范围
PRESET_EVENT_GAIN_MIN = 5
PRESET_EVENT_GAIN_MAX = 30

# 自定义行动的基准参数
CUSTOM_ACTION_BASE_GAIN = 10
CUSTOM_ACTION_BASE_COST = 2

# 突破失败惩罚：减少当前修为的百分比
BREAKTHROUGH_FAILURE_PENALTY = 0.3

# DeepSeek 超时时间（秒）
DEEPSEEK_TIMEOUT = 15

# ==================== NPC 系统参数 ====================
# NPC名字库（修仙风格）
NPC_SURNAMES = [
    "林", "叶", "苏", "柳", "白", "陆", "沈", "慕容", "上官", "南宫",
    "顾", "楚", "萧", "秦", "洛", "云", "姜", "百里", "东方", "西门"
]
NPC_GIVEN_NAMES_MALE = [
    "无涯", "长空", "逸尘", "清玄", "道然", "玄霄", "天行", "星河",
    "明远", "浩然", "青云", "子墨", "寒霜", "惊鸿", "凌云", "猛", "涛"
]
NPC_GIVEN_NAMES_FEMALE = [
    "如烟", "若雪", "清漪", "灵汐", "婉清", "紫萱", "月瑶", "冰璃",
    "雪见", "晴雪", "嫣然", "梦璃", "云曦", "洛神", "幽兰", "雪莉",
    "梦莉"
]
NPC_TITLES = [
    "散修", "宗门弟子", "长老座下", "执事", "护法",
    "真传弟子", "内门弟子", "外门弟子", "客卿", "隐修"
]

# 初遇时关系度范围
NPC_INITIAL_RELATIONSHIP_MIN = -20
NPC_INITIAL_RELATIONSHIP_MAX = 30

# 顶部关系栏最多显示人数
MAX_DISPLAYED_NPCS = 6

# ==================== NPC 交流系统配置 ====================

# 好感度挡位定义
NPC_RELATIONSHIP_TIERS = [
    {"range": (-100, -50), "name": "仇视", "tone": "敌意嘲讽", "address": "你这厮"},
    {"range": (-49, -20), "name": "厌恶", "tone": "冷漠疏离", "address": "阁下"},
    {"range": (-19, 0),   "name": "冷淡", "tone": "敷衍客套", "address": "道友"},
    {"range": (1, 30),    "name": "中立", "tone": "礼貌平淡", "address": "道友"},
    {"range": (31, 60),   "name": "友善", "tone": "温和热情", "address": "贤弟/贤妹"},
    {"range": (61, 80),   "name": "亲近", "tone": "亲密关怀", "address": "挚友"},
    {"range": (81, 100),  "name": "至交", "tone": "无话不谈", "address": "知己"},
]

# 每次NPC交流的基础寿命消耗（年）
NPC_INTERACT_LIFESPAN_COST_MIN = 1
NPC_INTERACT_LIFESPAN_COST_MAX = 4

# NPC交流修为影响范围
NPC_INTERACT_CULTIVATION_GAIN_MIN = -20
NPC_INTERACT_CULTIVATION_GAIN_MAX = 40

# NPC交流特殊效果概率（顿悟/奇遇）
NPC_INTERACT_SPECIAL_CHANCE = 0.08

# 好感度变化范围（根据玩家言行）
NPC_INTERACT_RELATIONSHIP_MIN = -30
NPC_INTERACT_RELATIONSHIP_MAX = 25

# 结婚条件
NPC_MARRY_RELATIONSHIP_MIN = 80
NPC_MARRY_REALM_LEVEL_MIN = 5
NPC_MARRY_SUCCESS_CHANCE_BASE = 0.25
NPC_MARRY_SUCCESS_CHANCE_PER_POINT = 0.007

# ==================== NPC 预设回复库（成人交流降级方案） ====================

NPC_PRESET_REPLIES_ADULT = {
    "亲密": [
        "你轻轻握住对方的手，两人相视一笑，一切尽在不言中。",
        "夜风习习，你们相依而坐，感受着彼此的温度，心中涌起一股暖意。",
        "对方依偎在你肩头，低声说着修炼时遇到的趣事，气氛温馨而融洽。",
        "你们并肩漫步在月色下，偶尔的眼神交汇让彼此心中泛起涟漪。",
    ],
    "暧昧": [
        "对方俏皮地眨了眨眼，略带羞涩地低下了头，脸颊微红。",
        "你靠近了一步，对方没有退让，反而是微微垂下了眼帘，呼吸略显急促。",
        "对方轻轻拉住你的衣袖，声音柔如水：'今晚的月色真美……'",
        "你们的目光在空中相遇，一种难以言说的情愫在两人之间流转。",
    ],
    "含蓄": [
        "对方微微一笑：'修行之路漫漫，能遇到你这样的人，也是一种缘分。'",
        "对方沉吟片刻：'有些话…不必说得太透，你懂，我也懂。'",
        "'你我之间，不需要太多言语。'对方轻声说道，目光中带着温柔。",
    ],
    "拒绝": [
        "对方后退一步，神色严肃：'请自重。你我之间，还是保持距离为好。'",
        "对方冷冷地看了你一眼：'这等轻浮之言，还是不要说了。'",
        "'修行之人，当以大道为重。'对方面无表情地转身离去。",
    ],
    "愤怒": [
        "对方怒目而视：'你再敢放肆，休怪我不念旧情！'",
        "'无耻之徒！'对方手中已经凝聚出一道凌厉的法诀。",
        "对方冷哼一声，眼中寒意如冰：'你若再进一步，便是生死之争。'",
    ]
}

# NPC 口吻模板（根据好感度挡位）
NPC_TONE_TEMPLATES = {
    "仇视": "你{action}，对方{name}眼中闪过一丝杀意，语气冰冷：'{reply}'",
    "厌恶": "{name}皱眉看着你{action}，语气淡漠中带着疏远：'{reply}'",
    "冷淡": "{name}微微点头，客气而不带感情地说：'{reply}'",
    "中立": "{name}以平常态度回应你{action}，语气平和：'{reply}'",
    "友善": "{name}面带笑意地看着你{action}，言语中透着热忱：'{reply}'",
    "亲近": "{name}目光柔和，如同对待至亲般回应你{action}：'{reply}'",
    "至交": "{name}眼中满是信任与温情，毫无保留地对你说：'{reply}'",
}

# ==================== 坏事件系统参数 ====================
BAD_EVENT_PENALTY_CHANCE = 0.3

# ==================== NPC交互类型配置 ====================
NPC_INTERACTION_TYPES = {
    "chat": {
        "name": "交谈",
        "relationship_min": -100,
        "lifespan_cost_range": (1, 4),
        "description": "与NPC进行日常交谈"
    },
    "meet": {
        "name": "见面",
        "relationship_min": -20,
        "lifespan_cost_range": (1, 3),
        "description": "约NPC见面叙旧"
    },
    "date": {
        "name": "约会",
        "relationship_min": 30,
        "lifespan_cost_range": (2, 6),
        "description": "与NPC进行浪漫约会"
    },
    "spar": {
        "name": "切磋",
        "relationship_min": -100,
        "lifespan_cost_range": (1, 5),
        "description": "与NPC进行知识切磋"
    }
}

# ==================== 女NPC攻略系统 ====================
FEMALE_NPC_AFFECTION_TYPES = [
    {
        "type": "学霸型",
        "description": "喜欢勤奋好学的类型，重视修为和学识",
        "gift_preference": "书籍",
        "relationship_bonus_chance": 0.2
    },
    {
        "type": "浪漫型",
        "description": "喜欢浪漫惊喜，重视情感交流",
        "gift_preference": "礼物",
        "relationship_bonus_chance": 0.15
    },
    {
        "type": "实力型",
        "description": "喜欢强者，重视实力和潜力",
        "gift_preference": "修炼资源",
        "relationship_bonus_chance": 0.25
    },
    {
        "type": "温柔型",
        "description": "善解人意，重视陪伴和关怀",
        "gift_preference": "日常用品",
        "relationship_bonus_chance": 0.1
    }
]

NPC_DATE_RELATIONSHIP_MIN = 30
NPC_DATE_LIFESPAN_COST_MIN = 2
NPC_DATE_LIFESPAN_COST_MAX = 6
NPC_MEET_LIFESPAN_COST_MIN = 1
NPC_MEET_LIFESPAN_COST_MAX = 3
NPC_SPAR_RELATIONSHIP_MIN = -100

# ==================== NPC交互拒绝系统 ====================
# 交互被拒绝的基础概率
NPC_INTERACTION_REJECTION_BASE_CHANCE = 0.3
# 被拒绝时好感度减少范围
NPC_REJECTION_RELATIONSHIP_PENALTY_MIN = -5
NPC_REJECTION_RELATIONSHIP_PENALTY_MAX = -1
# 友好交互（见面/约会/切磋）的好感度增益降低系数（0.5表示减半）
NPC_FRIENDLY_INTERACTION_RELATIONSHIP_MULTIPLIER = 0.5
# 友好交互的修为增益降低系数
NPC_FRIENDLY_INTERACTION_CULTIVATION_MULTIPLIER = 0.6

# ==================== 关系等级标签系统 ====================
# 根据好感度值显示的关系标签（覆盖NPC_RELATIONSHIP_TIERS的更精简版本）
# 适用于前端显示NPC的关系等级
NPC_RELATIONSHIP_LABELS = [
    {"range": (-100, -50), "label": "仇人", "css_class": "rel-enemy"},
    {"range": (-49, -20), "label": "厌恶", "css_class": "rel-hate"},
    {"range": (-19, 0),   "label": "冷淡", "css_class": "rel-cold"},
    {"range": (1, 30),    "label": "中立", "css_class": "rel-neutral"},
    {"range": (31, 60),   "label": "朋友", "css_class": "rel-friend"},
    {"range": (61, 80),   "label": "道友", "css_class": "rel-dao"},
    {"range": (81, 100),  "label": "至交", "css_class": "rel-close"},
]
# 当is_married且好感度>=80时，标签显示为"道侣"
NPC_PARTNER_LABEL = "道侣"
NPC_PARTNER_RELATIONSHIP_MIN = 80
NPC_PARTNER_LABEL_CSS = "rel-partner"

# ==================== 道侣系统配置 ====================
# 道侣经验共享比例（玩家获得修为的百分比共享给道侣）
PARTNER_CULTIVATION_SHARE_RATIO = 0.3
# 道侣NPC每累积多少共享修为可提升1级境界
PARTNER_NPC_REALM_UPGRADE_THRESHOLD = 500
# 结为道侣时增加的好感度
PARTNER_BECOME_RELATIONSHIP_BONUS = 20
# 结拜共享修为比例（玩家获得修为的百分比共享给结拜兄弟）
SWORN_BROTHER_SHARE_RATIO = 0.5

# 修行时NPC主动搭讪概率
NPC_ENCOUNTER_CHANCE = 0.15

# DeepSeek API 每日调用上限（后台管理）
DEEPSEEK_DAILY_LIMIT_DEFAULT = 50

# ==================== 职业路线配置 ====================
# 化神期（大学/等级5）后可选路线
CAREER_BREAKPOINT_REALM_LEVEL = 5
CAREER_CHOICE_REALM_NAME = "化神"

# 随机公司名称列表
COMPANY_NAMES = [
    "天衍科技有限公司", "碧落生物科技", "紫霄金融集团",
    "昆仑人工智能", "太虚区块链研究", "鸿蒙互联网",
    "混元生物医药", "太极数据分析", "两仪软件工程",
    "七星控股集团", "八卦传媒文化", "九宫建筑设计",
    "十方咨询公司", "万象物流集团", "无极环保科技"
]

# 上班路线可选活动（对应上班族的日常）
WORK_EVENTS = [
    {"name": "开晨会", "description": "参加部门晨会，汇报工作进展。",
     "cultivation_range": (3, 8), "lifespan_cost": 1,
     "npc_interact_chance": 0.2, "npc_scene": "公司晨会"},
    {"name": "写周报", "description": "整理一周工作，编写周报。",
     "cultivation_range": (5, 12), "lifespan_cost": 1,
     "npc_interact_chance": 0.1, "npc_scene": "工位上"},
    {"name": "项目攻坚", "description": "加班加点攻克项目难点。",
     "cultivation_range": (10, 20), "lifespan_cost": 2,
     "npc_interact_chance": 0.25, "npc_scene": "项目会议室"},
    {"name": "部门团建", "description": "参加公司团建活动，放松身心。",
     "cultivation_range": (2, 6), "lifespan_cost": 0,
     "npc_interact_chance": 0.35, "npc_scene": "团建现场"},
    {"name": "摸鱼", "description": "偷偷摸鱼，看看摸鱼网站。",
     "cultivation_range": (0, 3), "lifespan_cost": 0,
     "npc_interact_chance": 0.15, "npc_scene": "茶水间",
     "is_bad": True, "penalty_range": (-10, -3)},
    {"name": "汇报工作", "description": "向领导汇报近期工作成果。",
     "cultivation_range": (4, 10), "lifespan_cost": 1,
     "npc_interact_chance": 0.2, "npc_scene": "领导办公室"}
]

# ==================== 荒诞法则判词系统 ====================
# 每次突破时根据玩家行为倾向触发个性化判词
# 分类词库：学习型、摸鱼型、社交型、打工型、道心型、通用型
ABSURD_VERDICT_CATEGORIES = {
    "studious": {
        "label": "📖 卷王",
        "verdicts": [
            "天道法则第{}条：天道大数据监测显示，该修士学习时长已超越99%同龄人 —— 封号'卷王'，建议适度休息。",
            "天道法则第{}条：该修士的学习笔记可绕地球三圈，天道特批'学霸专属'休息室一间。",
            "天道法则第{}条：经检测，该修士的头发数量与修为成反比 —— 强者的代价，秃了也变强了。",
            "天道法则第{}条：天道发现该修士边吃泡面边看书，特授予'时间管理大师'称号，胃病概率+50%。",
            "天道法则第{}条：该修士的专注力突破天际，天道建议将其列入'修仙界非物质文化遗产'保护名单。",
            "天道法则第{}条：天道观察到该修士连做梦都在修炼，决定授予'卷心菜'勋章 —— 卷王中的卷王。",
            "天道法则第{}条：图书馆管理员实名举报该修士'长期霸占自习区'，天道回应：强者为尊，合理合法。",
            "天道法则第{}条：天道检测到该修士的咖啡消耗量已达'工业化'级别，建议与咖啡品牌联名代言。",
        ]
    },
    "slacker": {
        "label": "🦥 咸鱼",
        "verdicts": [
            "天道法则第{}条：天道检测到该修士的躺平时长已达修仙界平均水平 —— 继续躺，天道给你盖被子。",
            "天道法则第{}条：该修士的座右铭是'能坐着绝不站着，能躺着绝不坐着' —— 天道表示这很养生。",
            "天道法则第{}条：摸鱼一时爽，一直摸鱼一直爽 —— 天道认证的'修仙界摸鱼王'。",
            "天道法则第{}条：天道发现该修士的修炼效率在截止日期前会暴涨300% —— 这就是Deadline是第一生产力。",
            "天道法则第{}条：该修士将'摆烂'修炼到了极致，天道决定授予'咸鱼大圆满'境界称号。",
            "天道法则第{}条：天道统计显示该修士的'马上开始'次数已突破四位数 —— 但从未真正开始过。",
            "天道法则第{}条：该修士领悟了'无为而治'的真谛 —— 实际上就是懒，但天道无法反驳。",
        ]
    },
    "social": {
        "label": "💞 海王",
        "verdicts": [
            "天道法则第{}条：该修士的社交圈可绕地球一圈 —— 天道友情提示：道心比人脉更重要。",
            "天道法则第{}条：天道监测到该修士的情话库存堪比修仙界图书馆 —— 渣男/渣女鉴定完毕。",
            "天道法则第{}条：该修士同时与多位NPC保持暧昧关系 —— 天道提醒：海王渡劫时雷劫威力+100%。",
            "天道法则第{}条：该修士的好感度管理技能已点满 —— 天道建议转行做'修仙界情感导师'。",
            "天道法则第{}条：天道发现该修士微信好友数量已超过宗门总人数 —— 社牛症晚期，无法医治。",
            "天道法则第{}条：该修士的约会日程排到了明年 —— 天道疑问：什么时候修炼？",
            "天道法则第{}条：天道检测到该修士正在同时与多位NPC聊天 —— 时间管理能力令天道叹服。",
        ]
    },
    "worker": {
        "label": "💰 财迷",
        "verdicts": [
            "天道法则第{}条：该修士的灵石储备可买下半个修仙界 —— 但天道提醒：生不带来，死不带去。",
            "天道法则第{}条：天道检测到该修士把修炼时间用在了搞钱上 —— 资本家的思维已深入骨髓。",
            "天道法则第{}条：该修士的赚钱速度让天道都眼红 —— 天道决定对其征收'修仙所得税'。",
            "天道法则第{}条：天道发现该修士的存钱罐里连下品灵石都舍不得花 —— 葛朗台转世实锤。",
            "天道法则第{}条：该修士的副业收入已超过主业 —— 天道建议：要不改行吧？",
            "天道法则第{}条：天道征信系统显示该修士信用评级为SSS —— 因为太有钱了根本不需要贷款。",
        ]
    },
    "dao_xin": {
        "label": "🧘 道痴",
        "verdicts": [
            "天道法则第{}条：该修士的道心之坚，可令天道动容 —— 修仙界楷模，特此表彰。",
            "天道法则第{}条：天道检测到该修士做选择时永远选'道心'选项 —— 这就是传说中的圣人？",
            "天道法则第{}条：该修士的功德值已突破天际 —— 天道决定对其开放'VIP渡劫通道'。",
            "天道法则第{}条：天道发现该修士多次做出符合道心的选择 —— 善哉善哉，功德无量。",
        ]
    },
    "general": {
        "label": "⚖️ 天道",
        "verdicts": [
            "天道法则第{}条：熬夜修仙者，猝死概率+100%，但修为增速+50% —— 等价交换，童叟无欺。",
            "天道法则第{}条：在厕所突破者，有30%概率领悟'屎'之道，攻击附带臭味效果。",
            "天道法则第{}条：上课偷看修仙小说者，视力-1，想象力+10，期末考时走火入魔概率+80%。",
            "天道法则第{}条：凡是发誓'再玩手机就剁手'的修士，第二天都会领悟'千手观音'神通。",
            "天道法则第{}条：被导师骂一次，道心-5；反怼回去，道心+10 —— 但论文盲审可能被卡。",
            "天道法则第{}条：修仙界最新研究显示，每摸鱼1小时，实际修为增速反而提升20% —— 这叫'松弛有道'。",
            "天道法则第{}条：食堂大妈的手抖程度与你的修为成反比 —— 境界越高，打菜越多。",
            "天道法则第{}条：考试时用'仙力'作弊被抓者，一律没收手机并处以'重修大礼包'一份。",
            "天道法则第{}条：图书馆占座超过2小时不出现者，将遭受'天打雷劈'诅咒，雷劫难度+10%。",
            "天道法则第{}条：修仙界新规：凡在朋友圈发'闭关修炼'定位者，实际都在刷短视频，扣除功德+10。",
            "天道法则第{}条：深夜点外卖者，将吸引'饿鬼道'生物，建议搭配老干妈提升防御力。",
            "天道法则第{}条：CPDD者天打雷劈，但若找到真爱的道侣，双修速度+200%。",
            "天道法则第{}条：在修仙群里发'已阅'不发表情包者，人际关系-10，社恐指数+20。",
            "天道法则第{}条：凡使用'论文代写'服务者，天道将降下'查重天劫'，重复率超过80%则原地爆炸。",
            "天道法则第{}条：修仙界劳动法规定：996福报修士每月可领取'过劳死'保险一份。",
            "天道法则第{}条：在B站学习修仙功法者，弹幕护体+30%，但专注度-50% —— 俗称'氛围组修行法'。",
            "天道法则第{}条：喝奶茶加珍珠者，灵力转换效率+15%，但每次突破需多消耗20%修为 —— 糖分陷阱。",
            "天道法则第{}条：凡称自己'佛系修仙'者，实际都在偷偷内卷 —— 天道已识破此伪装，功德-5。",
            "天道法则第{}条：失恋后的修士修炼速度+50%，但走火入魔概率+50% —— 情劫双刃剑。",
            "天道法则第{}条：天道征信系统上线：欠灵石不还者，将无法使用'御剑飞行'等交通功能。",
        ]
    }
}

# ==================== 各境界随机事件配置 ====================
# 每个境界在修行时有概率触发对应的随机事件
REALM_RANDOM_EVENTS = {
    1: [  # 练气期（幼儿园）
        {"name": "抢零食", "description": "同桌抢了你的辣条！", "choices": [
            {"text": "抢回来！(武力对抗)", "cultivation": 5, "good_evil": -3, "dao_heart": -2, "spirit_stones": 0},
            {"text": "分享给TA", "cultivation": 2, "good_evil": 5, "dao_heart": 3, "spirit_stones": 0},
            {"text": "告老师", "cultivation": 0, "good_evil": -1, "dao_heart": -5, "spirit_stones": 0},
        ]},
        {"name": "午睡被查", "description": "午睡时间被老师抓到你没睡！", "choices": [
            {"text": "装睡", "cultivation": 1, "good_evil": 0, "dao_heart": -3, "spirit_stones": 0},
            {"text": "承认错误", "cultivation": 2, "good_evil": 3, "dao_heart": 5, "spirit_stones": 0},
        ]},
    ],
    2: [  # 筑基期（小学）
        {"name": "抄作业风波", "description": "有同学想抄你的作业！", "choices": [
            {"text": "借TA抄(积累人脉)", "cultivation": -5, "good_evil": 2, "dao_heart": -3, "spirit_stones": 5},
            {"text": "拒绝并教TA做题", "cultivation": 8, "good_evil": 5, "dao_heart": 5, "spirit_stones": 0},
            {"text": "告发TA", "cultivation": 1, "good_evil": -2, "dao_heart": 2, "spirit_stones": 0},
        ]},
    ],
    3: [  # 结丹期（初中）
        {"name": "考试作弊疑云", "description": "你发现旁边的同学在作弊，老师似乎没发现。", "choices": [
            {"text": "举报作弊", "cultivation": 2, "good_evil": 5, "dao_heart": 5, "spirit_stones": 0},
            {"text": "无视", "cultivation": 3, "good_evil": -2, "dao_heart": -3, "spirit_stones": 0},
            {"text": "勒索TA保密费", "cultivation": 0, "good_evil": -8, "dao_heart": -5, "spirit_stones": 20},
        ]},
    ],
    4: [  # 元婴期（高中）
        {"name": "选科抉择", "description": "文理分科/选科在即，你感到迷茫。", "choices": [
            {"text": "选擅长的科目", "cultivation": 10, "good_evil": 0, "dao_heart": 3, "spirit_stones": 0},
            {"text": "选喜欢的科目", "cultivation": 8, "good_evil": 0, "dao_heart": 5, "spirit_stones": 0},
            {"text": "随大流", "cultivation": 3, "good_evil": 0, "dao_heart": -5, "spirit_stones": 0},
        ]},
        {"name": "早恋风波", "description": "有人给你递了一封情书！", "choices": [
            {"text": "接受并交往", "cultivation": -3, "good_evil": 0, "dao_heart": -8, "spirit_stones": 0},
            {"text": "婉拒并专注学习", "cultivation": 8, "good_evil": 2, "dao_heart": 5, "spirit_stones": 0},
            {"text": "把情书交给老师", "cultivation": 1, "good_evil": -5, "dao_heart": -3, "spirit_stones": 0},
        ]},
    ],
    5: [  # 化神期（大学）
        {"name": "小组作业", "description": "小组作业遇到划水的队友！", "choices": [
            {"text": "一个人扛下所有", "cultivation": 12, "good_evil": 3, "dao_heart": 3, "spirit_stones": 0},
            {"text": "据理力争分配任务", "cultivation": 8, "good_evil": 0, "dao_heart": 5, "spirit_stones": 0},
            {"text": "一起摆烂", "cultivation": -5, "good_evil": -3, "dao_heart": -8, "spirit_stones": 0},
        ]},
        {"name": "社团活动", "description": "社团邀请你参加周末的联谊活动。", "choices": [
            {"text": "积极参加社交", "cultivation": 3, "good_evil": 2, "dao_heart": 3, "spirit_stones": 5},
            {"text": "拒绝并去图书馆", "cultivation": 10, "good_evil": 0, "dao_heart": 3, "spirit_stones": 0},
            {"text": "在活动中摸鱼", "cultivation": 1, "good_evil": -1, "dao_heart": -3, "spirit_stones": 0},
        ]},
    ],
    6: [  # 炼虚期（硕士）
        {"name": "导师约谈", "description": "导师约你谈话，表情严肃。", "choices": [
            {"text": "如实汇报进展", "cultivation": 10, "good_evil": 3, "dao_heart": 5, "spirit_stones": 0},
            {"text": "画大饼糊弄", "cultivation": 3, "good_evil": -5, "dao_heart": -5, "spirit_stones": 0},
            {"text": "申请换导师", "cultivation": -10, "good_evil": -3, "dao_heart": -10, "spirit_stones": 0},
        ]},
    ],
    7: [  # 合体期（博士）
        {"name": "论文盲审", "description": "论文盲审结果回来了！", "choices": [
            {"text": "认真修改", "cultivation": 15, "good_evil": 2, "dao_heart": 5, "spirit_stones": 10},
            {"text": "跟审稿人battle", "cultivation": 5, "good_evil": 0, "dao_heart": 3, "spirit_stones": 0},
            {"text": "摆烂延期", "cultivation": -15, "good_evil": -3, "dao_heart": -10, "spirit_stones": -10},
        ]},
    ],
    8: [  # 大乘期（博士后）
        {"name": "学术会议", "description": "国际学术会议邀请你做报告。", "choices": [
            {"text": "精心准备展示", "cultivation": 20, "good_evil": 3, "dao_heart": 5, "spirit_stones": 20},
            {"text": "随便讲讲", "cultivation": 5, "good_evil": 0, "dao_heart": -3, "spirit_stones": 5},
            {"text": "鸽了不去", "cultivation": -5, "good_evil": -3, "dao_heart": -5, "spirit_stones": -5},
        ]},
    ],
}

# ==================== 灵石系统配置 ====================
# 每次修行基础灵石收益范围
SPIRIT_STONES_GAIN_MIN = 1
SPIRIT_STONES_GAIN_MAX = 5
# 特殊事件额外灵石奖励范围
SPIRIT_STONES_BONUS_MIN = 5
SPIRIT_STONES_BONUS_MAX = 20
# 排行榜最多显示人数
RANKING_MAX_DISPLAY = 20
