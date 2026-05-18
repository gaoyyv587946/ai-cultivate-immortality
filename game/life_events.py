"""生活随机事件模块
小学（筑基期）后触发的日常生活事件，包含属性对抗选项和自定义行动支持
"""
import random

LIFE_EVENTS = [
    {
        "id": "bully_block",
        "name": "校霸堵门",
        "description": "放学后，校霸带了几个人把你堵在门口，嚣张地说：'新来的，交保护费了吗？'周围同学纷纷避开，没人敢管。",
        "min_realm_level": 2,
        "icon": "👊",
        "npc_generated": True,
        "npc_attrs": {
            "strength_range": (30, 70),
            "stamina_range": (30, 60),
            "name_prefix": "恶霸"
        },
        "options": [
            {
                "text": "正面硬刚 - 用力量说话",
                "attr": "strength",
                "success": {"log": "你一拳打在校霸脸上，他踉跄后退，带着小弟灰溜溜地跑了！", "rewards": {"good_evil": 5, "strength": 2}},
                "fail": {"log": "你被校霸按在地上摩擦，丢尽了脸面。", "rewards": {"strength": 1, "remaining_lifespan": -10}}
            },
            {
                "text": "智取 - 用计谋吓退他们",
                "attr": "intelligence",
                "success": {"log": "你大声说'老师来了！'趁他们回头时撒腿就跑，还顺便记下了他们的把柄。", "rewards": {"intelligence": 2, "spirit_stones": 10}},
                "fail": {"log": "你的小把戏被识破，被嘲笑了一番。", "rewards": {"dao_heart": -5}}
            },
            {
                "text": "硬抗 - 凭体力硬撑",
                "attr": "stamina",
                "success": {"log": "你咬紧牙关硬扛了一顿揍，校霸打累了觉得没意思就走了。虽然身上疼，但你感觉自己变强了。", "rewards": {"stamina": 3, "remaining_lifespan": -5}},
                "fail": {"log": "你直接被揍晕了过去，醒来时已经在医务室了。", "rewards": {"remaining_lifespan": -20, "spirit_stones": -10}}
            }
        ]
    },
    {
        "id": "found_wallet",
        "name": "捡到钱包",
        "description": "在路上你发现了一个鼓鼓的钱包，打开一看里面有不少灵石和一张身份牌。失主一定很着急。",
        "min_realm_level": 2,
        "icon": "👛",
        "npc_generated": False,
        "options": [
            {
                "text": "拾金不昧 - 按照身份牌找到失主",
                "attr": "good_evil",
                "success": {"log": "你把钱包还给失主，对方感激涕零，非要请你吃饭还给了你一些灵石作为谢礼。", "rewards": {"good_evil": 10, "spirit_stones": 30, "dao_heart": 3}},
                "fail": {"log": "你费了好大劲找到失主，结果对方不但不感谢还说你偷了他的钱包，真是好心没好报。", "rewards": {"good_evil": 5, "dao_heart": -3}}
            },
            {
                "text": "据为己有 - 反正没人看见",
                "attr": "good_evil",
                "success": {"log": "你悄悄把灵石收好，心里美滋滋的。虽然有点愧疚，但白捡的灵石真香！", "rewards": {"spirit_stones": 60, "good_evil": -10}},
                "fail": {"log": "你刚把灵石装进口袋，就有巡逻的人注意到了你，赶紧把钱包扔了假装路过。", "rewards": {"good_evil": -3, "spirit_stones": 5, "dao_heart": -2}}
            },
            {
                "text": "交给老师/长辈处理",
                "attr": "intelligence",
                "success": {"log": "你把钱包交给长辈处理，对方夸你诚实懂事，还奖励了你。", "rewards": {"good_evil": 8, "spirit_stones": 20, "intelligence": 1}},
                "fail": {"log": "长辈处理时被其他人冒领了，你感觉很憋屈。", "rewards": {"dao_heart": -3}}
            }
        ]
    },
    {
        "id": "stand_up",
        "name": "见义勇为",
        "description": "你看到几个高年级学生在欺负一个低年级的同学，把他推倒在地还抢他的东西。周围人都在围观但没人敢管。",
        "min_realm_level": 2,
        "icon": "🦸",
        "npc_generated": False,
        "options": [
            {
                "text": "挺身而出 - 用武力制止",
                "attr": "strength",
                "success": {"log": "你冲上前去三拳两脚打跑了高年级生，被欺负的小同学对你崇拜不已！", "rewards": {"good_evil": 15, "strength": 2, "dao_heart": 5}},
                "fail": {"log": "你冲上去但打不过对方，反而一起被揍了。不过你保护弱者的勇气赢得了大家的尊重。", "rewards": {"good_evil": 8, "remaining_lifespan": -15, "dao_heart": 3}}
            },
            {
                "text": "机智解围 - 想办法引开他们",
                "attr": "intelligence",
                "success": {"log": "你大喊'教导主任来了！'趁高年级生慌乱时拉着小同学就跑，成功解围！", "rewards": {"good_evil": 10, "intelligence": 2, "spirit_stones": 15}},
                "fail": {"log": "你的计谋被识破了，高年级生连你一起盯上了。", "rewards": {"good_evil": 3, "dao_heart": -2}}
            },
            {
                "text": "悄悄去叫老师",
                "attr": "intelligence",
                "success": {"log": "你悄悄跑到办公室叫来了老师，高年级生被当场抓获，得到了应有的惩罚。", "rewards": {"good_evil": 12, "intelligence": 1, "spirit_stones": 10}},
                "fail": {"log": "老师不在办公室，等你回来时人已经散了。", "rewards": {"good_evil": 3}}
            }
        ]
    },
    {
        "id": "mysterious_stall",
        "name": "神秘摊位",
        "description": "路边有个白胡子老头摆了个摊位，上面写着'缘法一道，童叟无欺'。他笑眯眯地朝你招手：'小友，来试试手气？'",
        "min_realm_level": 2,
        "icon": "🔮",
        "npc_generated": False,
        "options": [
            {
                "text": "花灵石买一卦 - 看看运气",
                "attr": "intelligence",
                "success": {"log": "老头看了你的卦象，啧啧称奇：'小友根骨不凡，前途不可限量！'他送了你一颗灵丹，服下后精神大振。", "rewards": {"spirit": 3, "spirit_stones": -20, "cultivation": 100}},
                "fail": {"log": "老头说了一堆云里雾里的话，你花了灵石啥也没听懂。", "rewards": {"spirit_stones": -20, "dao_heart": -2}}
            },
            {
                "text": "求取修炼心得",
                "attr": "spirit",
                "success": {"log": "老头见你诚心向道，传了你几句修炼口诀，你感觉修为有所精进。", "rewards": {"cultivation": 200, "spirit": 1, "dao_heart": 3}},
                "fail": {"log": "老头摇摇头：'心不诚则不灵'，不再理你了。", "rewards": {"dao_heart": -3}}
            },
            {
                "text": "直接走人 - 不理会",
                "attr": "good_evil",
                "success": {"log": "你礼貌地摆摆手离开了，老头在你身后喊：'有缘再见！'", "rewards": {"spirit_stones": 10}},
                "fail": {"log": "你白了一眼就走了，老头在后面嘀咕：'现在的年轻人啊。'", "rewards": {"good_evil": -2}}
            }
        ]
    },
    {
        "id": "exam_cheat",
        "name": "考试作弊",
        "description": "期末考试前，一个同学鬼鬼祟祟地找到你：'哥们儿，帮我传个答案，这是报酬！'他掏出一袋灵石在你面前晃了晃。",
        "min_realm_level": 3,
        "icon": "📝",
        "npc_generated": False,
        "options": [
            {
                "text": "严词拒绝 - 做人要正直",
                "attr": "good_evil",
                "success": {"log": "你义正言辞地拒绝了，对方讪讪离开。考试时你发现他就在你后面，但你已经表明立场，问心无愧。", "rewards": {"good_evil": 8, "dao_heart": 5, "intelligence": 1}},
                "fail": {"log": "你拒绝了他，但他在背后到处说你坏话。", "rewards": {"good_evil": 5, "dao_heart": -2}}
            },
            {
                "text": "答应帮忙 - 赚一笔",
                "attr": "intelligence",
                "success": {"log": "你巧妙地用暗号传了答案，神不知鬼不觉地赚了一袋灵石。", "rewards": {"spirit_stones": 80, "good_evil": -10, "intelligence": 1}},
                "fail": {"log": "你传答案时被监考老师发现了，两人都被抓了个正着！", "rewards": {"good_evil": -15, "spirit_stones": -30, "dao_heart": -5}}
            },
            {
                "text": "假装答应然后举报",
                "attr": "intelligence",
                "success": {"log": "你假装答应，转头就告诉了老师。老师当场抓住他，表扬了你的正直。", "rewards": {"good_evil": 10, "spirit_stones": 30, "intelligence": 2}},
                "fail": {"log": "你的小动作被人发现，两边都不讨好。", "rewards": {"good_evil": -3, "dao_heart": -5}}
            }
        ]
    },
    {
        "id": "beggar_encounter",
        "name": "路遇乞丐",
        "description": "路边蜷缩着一个衣衫褴褛的老乞丐，面前放着一个破碗，用颤抖的声音说：'行行好吧，几天没吃饭了……'",
        "min_realm_level": 2,
        "icon": "🥣",
        "npc_generated": False,
        "options": [
            {
                "text": "慷慨解囊 - 给一些灵石",
                "attr": "good_evil",
                "success": {"log": "你往碗里放了一些灵石，老乞丐感激地连连道谢。你心里暖暖的，好人自有好报。", "rewards": {"good_evil": 10, "dao_heart": 3, "spirit_stones": -20}},
                "fail": {"log": "你刚掏出灵石，旁边突然冲出几个乞丐把你围住要钱。你赶紧把钱收好跑了。", "rewards": {"good_evil": 3, "spirit_stones": -5}}
            },
            {
                "text": "买些吃的给他",
                "attr": "intelligence",
                "success": {"log": "你去买了热腾腾的包子和粥递给老乞丐。他眼眶湿润地说：'好人有好报啊！'你注意到他手上有一个古朴的戒指……他悄悄塞给了你。", "rewards": {"good_evil": 12, "spirit_stones": -15, "cultivation": 80}},
                "fail": {"log": "等你买完吃的回来，老乞丐已经不见了。", "rewards": {"good_evil": 5, "spirit_stones": -10}}
            },
            {
                "text": "视而不见 - 多一事不如少一事",
                "attr": "good_evil",
                "success": {"log": "你低头快步走过，假装没看见。心里有点过意不去，但也省了麻烦。", "rewards": {"good_evil": -3}},
                "fail": {"log": "你走开后回头看了一眼，发现老乞丐正用一种说不清道不明的眼神看着你。", "rewards": {"good_evil": -5, "dao_heart": -2}}
            }
        ]
    },
    {
        "id": "emergency_rescue",
        "name": "江湖救急",
        "description": "你听到路边草丛中有微弱的呻吟声，走过去一看，有个人受伤倒在地上，面色苍白，似乎伤得不轻。",
        "min_realm_level": 2,
        "icon": "🚑",
        "npc_generated": False,
        "options": [
            {
                "text": "运功疗伤 - 用灵力帮助",
                "attr": "spirit",
                "success": {"log": "你运功为伤者疗伤，他缓过气来感激地说：'多谢救命之恩！'他送了你一本修炼心得作为谢礼。", "rewards": {"spirit": 2, "cultivation": 150, "good_evil": 10, "dao_heart": 3}},
                "fail": {"log": "你修为不够，强行运功导致气血翻涌，自己也受了内伤。", "rewards": {"spirit": -2, "remaining_lifespan": -20, "good_evil": 5}}
            },
            {
                "text": "背去找大夫 - 体力活",
                "attr": "stamina",
                "success": {"log": "你咬牙把伤者背到了医馆，累得满头大汗但救了一条人命。大夫说你来得及时，再晚就危险了。", "rewards": {"stamina": 2, "good_evil": 12, "spirit_stones": 20}},
                "fail": {"log": "你背到一半就体力不支，两人一起摔在地上，伤者伤得更重了。", "rewards": {"remaining_lifespan": -15, "good_evil": -3}}
            },
            {
                "text": "帮忙呼叫救援",
                "attr": "intelligence",
                "success": {"log": "你迅速找到路人帮忙，一起把伤者送到了医馆。伤者虽未当面道谢，但你做了该做的事。", "rewards": {"good_evil": 8, "intelligence": 1, "dao_heart": 2}},
                "fail": {"log": "你喊破了喉咙也没人帮忙，回来时伤者已经昏迷了。", "rewards": {"good_evil": 3}}
            }
        ]
    },
    {
        "id": "lottery_win",
        "name": "天降横财",
        "description": "你随手买的一张刮刮乐竟然中奖了！面值还不小，你激动得手都在抖。不过有道声音在心里问：这笔钱该怎么用？",
        "min_realm_level": 3,
        "icon": "🎰",
        "npc_generated": False,
        "options": [
            {
                "text": "存起来修炼用 - 合理规划",
                "attr": "intelligence",
                "success": {"log": "你冷静地把灵石存好，规划用于修炼资源。克制欲望也是一种修行。", "rewards": {"spirit_stones": 120, "intelligence": 1, "dao_heart": 3}},
                "fail": {"log": "你准备存起来时不小心被人偷了部分，损失惨重。", "rewards": {"spirit_stones": 40, "dao_heart": -3}}
            },
            {
                "text": "大肆挥霍 - 及时行乐",
                "attr": "spirit",
                "success": {"log": "你请朋友们胡吃海喝了一顿，大家都夸你仗义！灵石虽花了不少但收获了快乐和友谊。", "rewards": {"spirit_stones": -60, "good_evil": 5, "stamina": 1}},
                "fail": {"log": "你挥霍无度引起了坏人注意，被人盯上了。", "rewards": {"spirit_stones": -80, "remaining_lifespan": -10}}
            },
            {
                "text": "捐给需要的人",
                "attr": "good_evil",
                "success": {"log": "你把大部分灵石捐给了书院资助贫困学生，你的善举感动了很多人，书院特意表彰了你。", "rewards": {"spirit_stones": -80, "good_evil": 20, "dao_heart": 5, "cultivation": 100}},
                "fail": {"log": "你捐的钱被中间人贪了一部分，没能完全到需要的人手中。", "rewards": {"spirit_stones": -40, "good_evil": 8, "dao_heart": -2}}
            }
        ]
    },
    {
        "id": "campus_rumor",
        "name": "校园传闻",
        "description": "课间你听到有人在背后传你的谣言，说你考试作弊还走后门。周围同学对你指指点点，窃窃私语。",
        "min_realm_level": 2,
        "icon": "🗣️",
        "npc_generated": False,
        "options": [
            {
                "text": "当面质问 - 用气势压回去",
                "attr": "strength",
                "success": {"log": "你走到造谣者面前，冷冷地盯着他。他被你的气势震慑住了，灰溜溜地承认是瞎说的。", "rewards": {"strength": 1, "dao_heart": 3, "good_evil": 3}},
                "fail": {"log": "你冲过去质问反而被他倒打一耙，说你恼羞成怒，谣言反而传得更凶了。", "rewards": {"dao_heart": -5, "good_evil": -3}}
            },
            {
                "text": "用实力证明 - 下次考试见真章",
                "attr": "intelligence",
                "success": {"log": "你没有辩解，而是在下次考试中考了全班第一。成绩是最好的反击，谣言不攻自破。", "rewards": {"intelligence": 2, "cultivation": 80, "dao_heart": 5}},
                "fail": {"log": "你太在意这件事导致发挥失常，考砸了，谣言反而被坐实了。", "rewards": {"intelligence": -2, "dao_heart": -5}}
            },
            {
                "text": "置之不理 - 清者自清",
                "attr": "spirit",
                "success": {"log": "你心态平和地该干嘛干嘛，过了一段时间大家发现谣言不攻自破，反而觉得你大度。", "rewards": {"spirit": 2, "dao_heart": 5, "good_evil": 5}},
                "fail": {"log": "你表面不在意，心里却一直憋着气，影响了修炼状态。", "rewards": {"dao_heart": -3, "cultivation": -30}}
            }
        ]
    },
    {
        "id": "secret_entrance",
        "name": "秘境入口",
        "description": "你在后山闲逛时无意中发现了一个隐蔽的山洞，洞口有微弱的光芒闪烁，似乎是一个未被发现的秘境入口！",
        "min_realm_level": 3,
        "icon": "🏔️",
        "npc_generated": False,
        "options": [
            {
                "text": "独自探索 - 富贵险中求",
                "attr": "strength",
                "success": {"log": "你小心翼翼地进入秘境，在里面发现了不少天材地宝，修为大增！", "rewards": {"cultivation": 300, "spirit_stones": 100, "strength": 2}},
                "fail": {"log": "你刚进入就触发了机关，被弹了出来，灰头土脸还受了伤。", "rewards": {"remaining_lifespan": -25, "spirit_stones": -20}}
            },
            {
                "text": "先探虚实 - 用灵力感知",
                "attr": "spirit",
                "success": {"log": "你盘腿坐下，用灵力感知洞内情况，发现了一处隐蔽的灵石矿脉！安全采集了不少灵石。", "rewards": {"spirit": 2, "spirit_stones": 150, "cultivation": 100}},
                "fail": {"log": "你感知到洞内有一股强大的气息，赶紧退了出来，什么都没捞着。", "rewards": {"dao_heart": -2}}
            },
            {
                "text": "做个标记找帮手",
                "attr": "intelligence",
                "success": {"log": "你机智地做好标记，回去找了几个可靠的同伴一起来探索，大家合力收获颇丰！", "rewards": {"intelligence": 2, "spirit_stones": 80, "cultivation": 150, "good_evil": 5}},
                "fail": {"log": "等你带人回来时，秘境已经被别人发现了，里面的宝贝被洗劫一空。", "rewards": {"dao_heart": -5, "intelligence": -1}}
            }
        ]
    },
    {
        "id": "rescue_beauty",
        "name": "英雄救美",
        "description": "你听到巷子里传来争吵声，走过去看到几个地痞正在纠缠一个年轻女子，女子脸色煞白，不断后退。",
        "min_realm_level": 3,
        "icon": "💝",
        "npc_generated": False,
        "options": [
            {
                "text": "武力驱赶 - 用拳头说话",
                "attr": "strength",
                "success": {"log": "你冲上前去三下五除二把地痞打跑了。女子感激不尽，原来她是某大家族的千金，执意要报答你。", "rewards": {"strength": 2, "good_evil": 15, "spirit_stones": 80, "dao_heart": 5}},
                "fail": {"log": "你打不过几个地痞，反而被打了一顿。好在动静大了引来了巡逻，地痞跑了。", "rewards": {"remaining_lifespan": -20, "good_evil": 8}}
            },
            {
                "text": "智取 - 假装巡逻队来了",
                "attr": "intelligence",
                "success": {"log": "你大声喊道：'队长！这边有情况！'地痞们以为巡逻队来了，慌忙逃窜。女子破涕为笑。", "rewards": {"intelligence": 2, "good_evil": 10, "spirit_stones": 40}},
                "fail": {"log": "你的把戏被识破了，地痞们恼羞成怒连你一起打。", "rewards": {"remaining_lifespan": -15, "good_evil": 5}}
            },
            {
                "text": "好言相劝 - 尝试讲道理",
                "attr": "spirit",
                "success": {"log": "你走上前冷静地跟地痞讲道理，你的气场让地痞觉得你不是一般人，骂骂咧咧地走了。", "rewards": {"spirit": 2, "good_evil": 8, "dao_heart": 3}},
                "fail": {"log": "地痞根本不吃这套，反而嘲笑你多管闲事。", "rewards": {"dao_heart": -3, "good_evil": 3}}
            }
        ]
    },
    {
        "id": "business_opportunity",
        "name": "商业机会",
        "description": "一个看起来精明的商人找到你：'我发现了一个商机，缺个合伙人。你出点灵石，我出力，利润五五分成，干不干？'",
        "min_realm_level": 4,
        "icon": "💼",
        "npc_generated": False,
        "options": [
            {
                "text": "投资合作 - 赌一把",
                "attr": "intelligence",
                "success": {"log": "你仔细研究了商人的计划，发现确实可行。果然，一个月后你获得了丰厚的回报！", "rewards": {"spirit_stones": 200, "intelligence": 2, "spirit_stones": -50}},
                "fail": {"log": "商人卷款跑路了！你血本无归，气得几天没睡好觉。", "rewards": {"spirit_stones": -80, "dao_heart": -5, "intelligence": -1}}
            },
            {
                "text": "杀价入股 - 只出小钱试试水",
                "attr": "intelligence",
                "success": {"log": "你精打细算只投了一小笔，结果生意还真成了，虽然赚得不多但稳赚不赔。", "rewards": {"spirit_stones": 60, "intelligence": 1, "spirit_stones": -20}},
                "fail": {"log": "生意没做成，好在你投得少，损失不大。", "rewards": {"spirit_stones": -20}}
            },
            {
                "text": "拒绝 - 天下没有免费的午餐",
                "attr": "spirit",
                "success": {"log": "你婉拒了商人的邀请。后来听说那人的生意出了事，你暗自庆幸自己的判断。", "rewards": {"dao_heart": 3, "spirit": 1}},
                "fail": {"log": "你拒绝了之后发现那生意其实很赚钱，错过了一个好机会。", "rewards": {"dao_heart": -3}}
            }
        ]
    },
    {
        "id": "lost_child",
        "name": "迷路小孩",
        "description": "你看到一个五六岁的小女孩坐在路边哭，鼻涕眼泪糊了一脸：'呜呜……我找不到妈妈了……'",
        "min_realm_level": 2,
        "icon": "👶",
        "npc_generated": False,
        "options": [
            {
                "text": "耐心安慰并帮忙找家长",
                "attr": "spirit",
                "success": {"log": "你蹲下来轻声安慰小女孩，带她去管理处广播寻人。很快一位焦急的母亲冲了过来，抱着孩子哭了一场，对你千恩万谢。", "rewards": {"good_evil": 15, "spirit": 2, "dao_heart": 5, "spirit_stones": 20}},
                "fail": {"log": "你越安慰小女孩哭得越厉害，引来路人用怀疑的眼光看你，你只好赶紧离开了。", "rewards": {"dao_heart": -2}}
            },
            {
                "text": "带她去附近店铺问询",
                "attr": "intelligence",
                "success": {"log": "你带小女孩去了最近的店铺，老板娘认识她家，很快帮忙联系上了家人。", "rewards": {"good_evil": 10, "intelligence": 1, "spirit_stones": 10}},
                "fail": {"log": "店铺老板也不认识，你带着孩子转来转去，最后只好送去了治安处。", "rewards": {"good_evil": 5, "remaining_lifespan": -10}}
            }
        ]
    },
    {
        "id": "traffic_accident",
        "name": "目睹车祸",
        "description": "街上突然传来一声巨响，一辆疾驰的马车撞翻了一个摊位，摊主倒在地上痛苦地呻吟，周围一片混乱。",
        "min_realm_level": 2,
        "icon": "🚗",
        "npc_generated": False,
        "options": [
            {
                "text": "冲上去救人 - 救人要紧",
                "attr": "stamina",
                "success": {"log": "你快速冲过去把摊主从危险区域拖出来，做了简单的止血处理。医馆的人赶到时说你处理得很及时。", "rewards": {"good_evil": 12, "stamina": 2, "spirit_stones": 25, "dao_heart": 3}},
                "fail": {"log": "你冲过去但力气不够，没能把压在摊位下的人拽出来，反而自己也受伤了。", "rewards": {"remaining_lifespan": -15, "good_evil": 5}}
            },
            {
                "text": "维护秩序 - 组织大家帮忙",
                "attr": "intelligence",
                "success": {"log": "你大声指挥围观群众帮忙抬起摊位、疏导交通，大家在你的组织下有条不紊地进行救援。", "rewards": {"intelligence": 2, "good_evil": 10, "spirit_stones": 15}},
                "fail": {"log": "没人听你的指挥，场面更加混乱了。", "rewards": {"intelligence": -1}}
            }
        ]
    },
    {
        "id": "neighbor_noise",
        "name": "邻里纠纷",
        "description": "你的邻居每天半夜都在大声喧哗，严重影响你修炼。你好言相劝几次都没用，今晚又开始了。",
        "min_realm_level": 2,
        "icon": "🏠",
        "npc_generated": False,
        "options": [
            {
                "text": "强硬上门 - 武力警告",
                "attr": "strength",
                "success": {"log": "你一脚踹开邻居的门，强大的气场让对方瞬间怂了，连连保证再也不吵了。", "rewards": {"strength": 1, "dao_heart": 3, "good_evil": -3}},
                "fail": {"log": "邻居一家子人高马大，你反而被轰了出来，丢尽了脸。", "rewards": {"strength": -1, "dao_heart": -5}}
            },
            {
                "text": "以理服人 - 动之以情",
                "attr": "intelligence",
                "success": {"log": "你心平气和地跟邻居谈了谈，才知道他家中有急事。你帮了他一把，他感激不尽，之后再也没有吵闹过。", "rewards": {"intelligence": 2, "good_evil": 8, "dao_heart": 3}},
                "fail": {"log": "邻居根本不讲理，反而说你多管闲事。", "rewards": {"dao_heart": -3}}
            },
            {
                "text": "忍了 - 修炼心境",
                "attr": "spirit",
                "success": {"log": "你静下心来在嘈杂中修炼，反而锤炼了自己的心志，精神更加坚韧了。", "rewards": {"spirit": 3, "dao_heart": 5, "cultivation": 50}},
                "fail": {"log": "你越想静心越烦躁，差点走火入魔。", "rewards": {"spirit": -2, "dao_heart": -5, "cultivation": -30}}
            }
        ]
    },
    {
        "id": "pet_adoption",
        "name": "捡到小动物",
        "description": "路边有一只瑟瑟发抖的小奶狗/小灵兽，看起来刚出生不久，被遗弃在纸箱里，用湿漉漉的大眼睛看着你。",
        "min_realm_level": 2,
        "icon": "🐾",
        "npc_generated": False,
        "options": [
            {
                "text": "带回去养 - 有缘相遇",
                "attr": "good_evil",
                "success": {"log": "你小心翼翼地把小家伙抱回去，悉心照料。它长大后竟然是一只珍稀灵兽，帮你找到了不少天材地宝！", "rewards": {"good_evil": 10, "spirit_stones": 80, "cultivation": 100, "dao_heart": 5}},
                "fail": {"log": "你带回去养了三天，小家伙把你的住处搞得一团糟，你只好送人了。", "rewards": {"good_evil": 5, "spirit_stones": -20}}
            },
            {
                "text": "送到灵兽店",
                "attr": "good_evil",
                "success": {"log": "你把小灵兽送到灵兽店，店主认出这是一只稀有品种，给了你一笔报酬。", "rewards": {"good_evil": 5, "spirit_stones": 50}},
                "fail": {"log": "灵兽店老板说这只是普通土狗，不值钱。你只好把它留在那里。", "rewards": {"good_evil": 3, "spirit_stones": 5}}
            }
        ]
    },
    {
        "id": "classmate_borrow",
        "name": "同学借钱",
        "description": "一个平时不太熟的同学找到你，说家里出了急事急需灵石周转，问你借100灵石，承诺一个月后还。",
        "min_realm_level": 2,
        "icon": "💰",
        "npc_generated": False,
        "options": [
            {
                "text": "慷慨借出 - 助人为乐",
                "attr": "good_evil",
                "success": {"log": "你毫不犹豫地借给了他。一个月后，他不仅如数归还，还多给了20灵石利息，从此成了好朋友。", "rewards": {"spirit_stones": 120, "good_evil": 10, "dao_heart": 3}},
                "fail": {"log": "你借给他之后他就消失了，再也找不到人了。", "rewards": {"spirit_stones": -100, "dao_heart": -5}}
            },
            {
                "text": "只借一半 - 留个心眼",
                "attr": "intelligence",
                "success": {"log": "你借了一半给他，说手头也紧。后来他确实还了钱，虽然少赚了点但保住了本金。", "rewards": {"spirit_stones": -50, "intelligence": 1, "good_evil": 5}},
                "fail": {"log": "你借了一半给他，结果他还是没还，不过损失倒是不大。", "rewards": {"spirit_stones": -50, "dao_heart": -2}}
            },
            {
                "text": "婉拒 - 不熟不借",
                "attr": "intelligence",
                "success": {"log": "你委婉地拒绝了。后来听说他在外面借了很多人的钱跑路了，你庆幸自己没上当。", "rewards": {"intelligence": 2}},
                "fail": {"log": "你拒绝后他在同学圈里说你小气，不过你并不在意。", "rewards": {"good_evil": -3}}
            }
        ]
    },
    {
        "id": "public_speech",
        "name": "被迫演讲",
        "description": "老师突然点名让你上台分享修炼心得！你毫无准备，全班几十双眼睛齐刷刷盯着你，教室里鸦雀无声。",
        "min_realm_level": 3,
        "icon": "🎤",
        "npc_generated": False,
        "options": [
            {
                "text": "硬着头皮上 - 即兴发挥",
                "attr": "spirit",
                "success": {"log": "你深吸一口气，开始讲自己的修炼体会。虽然磕磕绊绊，但真情实感打动了大家，赢得了热烈掌声！", "rewards": {"spirit": 3, "cultivation": 80, "dao_heart": 3}},
                "fail": {"log": "你站在台上大脑一片空白，憋了半天说了句'我还没准备好'就跑了下去，全班哄堂大笑。", "rewards": {"spirit": -2, "dao_heart": -5}}
            },
            {
                "text": "用段子化解 - 幽默救场",
                "attr": "intelligence",
                "success": {"log": "你上台先讲了个修炼笑话，全班笑得前仰后合，气氛轻松了之后你从容地分享了自己的心得。", "rewards": {"intelligence": 2, "cultivation": 60, "good_evil": 5}},
                "fail": {"log": "你讲的冷笑话没人笑，场面一度十分尴尬。", "rewards": {"dao_heart": -3}}
            }
        ]
    },
    {
        "id": "sports_meet",
        "name": "修仙运动会",
        "description": "书院举办了一年一度的修仙运动会！有长跑（体力）、举重（力量）、灵力比拼（精神）、阵法解谜（智力）等多个项目，你可以选择一个参加。",
        "min_realm_level": 3,
        "icon": "🏅",
        "npc_generated": False,
        "options": [
            {
                "text": "参加长跑 - 体力比拼",
                "attr": "stamina",
                "success": {"log": "你在长跑项目中一骑绝尘，轻松夺冠！全场为你欢呼，你获得了'飞毛腿'称号和灵石奖励。", "rewards": {"stamina": 3, "spirit_stones": 80, "cultivation": 100, "good_evil": 5}},
                "fail": {"log": "你跑到一半岔气了，最后几名收场，好不丢人。", "rewards": {"stamina": -1, "remaining_lifespan": -10}}
            },
            {
                "text": "参加举重 - 力量比拼",
                "attr": "strength",
                "success": {"log": "你力拔山兮气盖世，举起了全场最重的灵石鼎！台下惊呼不断。", "rewards": {"strength": 3, "spirit_stones": 80, "cultivation": 100, "good_evil": 5}},
                "fail": {"log": "你憋红了脸也没举起来，还被鼎压到了脚。", "rewards": {"strength": -1, "remaining_lifespan": -15}}
            },
            {
                "text": "参加灵力比拼 - 精神比拼",
                "attr": "spirit",
                "success": {"log": "你以强大的精神力碾压所有对手，让全场感受到了你的威压！", "rewards": {"spirit": 3, "spirit_stones": 80, "cultivation": 100, "good_evil": 5}},
                "fail": {"log": "你灵力不够稳定，比拼中反噬了自己。", "rewards": {"spirit": -2, "remaining_lifespan": -10}}
            },
            {
                "text": "参加阵法解谜 - 智力比拼",
                "attr": "intelligence",
                "success": {"log": "你轻松破解了所有阵法谜题，以绝对优势夺冠！围观的同学都看呆了。", "rewards": {"intelligence": 3, "spirit_stones": 80, "cultivation": 100, "good_evil": 5}},
                "fail": {"log": "你在迷阵里绕来绕去出不来，最后超时出局。", "rewards": {"intelligence": -1}}
            }
        ]
    },
    {
        "id": "rain_storm",
        "name": "暴雨被困",
        "description": "放学时突然下起了暴雨，你没带伞，被困在教学楼门口。雨越下越大，天也快黑了。",
        "min_realm_level": 2,
        "icon": "🌧️",
        "npc_generated": False,
        "options": [
            {
                "text": "冒雨冲回去 - 拼速度",
                "attr": "stamina",
                "success": {"log": "你把外套顶在头上，撒腿就跑。虽然淋成了落汤鸡，但你发现雨中奔跑竟然让体力有所增长。", "rewards": {"stamina": 2, "remaining_lifespan": -5}},
                "fail": {"log": "雨太大路太滑，你摔了一跤，浑身泥泞地回到家。", "rewards": {"remaining_lifespan": -15, "stamina": -1}}
            },
            {
                "text": "运功避雨 - 用灵力撑开屏障",
                "attr": "spirit",
                "success": {"log": "你运起灵力在头顶形成一个屏障，虽然消耗不小但滴水未沾地回到了住处。", "rewards": {"spirit": 2, "cultivation": -30}},
                "fail": {"log": "你灵力不够，屏障只撑了一会儿就破了，反而消耗了大量灵力。", "rewards": {"spirit": -2, "cultivation": -50}}
            },
            {
                "text": "等雨停 - 顺便修炼",
                "attr": "intelligence",
                "success": {"log": "你索性在屋檐下盘腿修炼起来。雨停后你不仅没淋湿，修为还有所精进。", "rewards": {"cultivation": 80, "intelligence": 1, "dao_heart": 3}},
                "fail": {"log": "你等着等着睡着了，最后被巡逻的人叫醒，雨已经停了但你也错过了晚饭。", "rewards": {"remaining_lifespan": -5}}
            }
        ]
    },
    {
        "id": "street_performer",
        "name": "街头卖艺",
        "description": "街上有一个杂耍班子在表演，围观的人很多。班主看到你气质不凡，邀请你露一手：'小兄弟，上来展示展示，赏钱五五分！'",
        "min_realm_level": 2,
        "icon": "🎪",
        "npc_generated": False,
        "options": [
            {
                "text": "展示武力 - 碎石表演",
                "attr": "strength",
                "success": {"log": "你一拳砸碎了一块大石头，围观群众喝彩连连，灵石像雨点般扔来！", "rewards": {"strength": 2, "spirit_stones": 70, "good_evil": 3}},
                "fail": {"log": "你一拳下去石头纹丝不动，你的手反而肿了起来，观众一片嘘声。", "rewards": {"remaining_lifespan": -10, "spirit_stones": -10}}
            },
            {
                "text": "展示灵力 - 隔空取物",
                "attr": "spirit",
                "success": {"log": "你施展灵力凭空摄物，观众惊为天人！班主连连称赞，分了你不少灵石。", "rewards": {"spirit": 2, "spirit_stones": 70, "good_evil": 3}},
                "fail": {"log": "你灵力失控，把摊子掀翻了，班主追着你赔钱。", "rewards": {"spirit_stones": -40, "good_evil": -5}}
            },
            {
                "text": "表演变戏法 - 用聪明才智",
                "attr": "intelligence",
                "success": {"log": "你表演了几个精彩的魔术手法，观众看得目瞪口呆，掌声雷动！", "rewards": {"intelligence": 2, "spirit_stones": 60, "good_evil": 3}},
                "fail": {"log": "你的手法被一个小孩当场拆穿，尴尬得想找个地缝钻进去。", "rewards": {"spirit_stones": -15, "dao_heart": -3}}
            }
        ]
    },
    {
        "id": "help_stranger",
        "name": "问路老者",
        "description": "一位白发苍苍的老者拦住你：'年轻人，请问去城东的灵药铺怎么走？'他看起来有些糊涂，手里拿着一张破旧的地图。",
        "min_realm_level": 2,
        "icon": "🗺️",
        "npc_generated": False,
        "options": [
            {
                "text": "详细指路并送他过去",
                "attr": "good_evil",
                "success": {"log": "你耐心地扶着老者找到了灵药铺。老者感激之下送你一张古老的丹方，据说价值不菲！", "rewards": {"good_evil": 10, "spirit_stones": 50, "cultivation": 100}},
                "fail": {"log": "你带老者绕了半天也没找到地方，老者气得用拐杖敲你。", "rewards": {"good_evil": 3, "remaining_lifespan": -5}}
            },
            {
                "text": "看地图帮他规划路线",
                "attr": "intelligence",
                "success": {"log": "你仔细研究了地图，给老者画了一条清晰的路线图。老者连连点头：'后生可畏啊！'", "rewards": {"intelligence": 2, "dao_heart": 2, "spirit_stones": 20}},
                "fail": {"log": "你看反了地图，指了个完全相反的方向。", "rewards": {"intelligence": -2, "good_evil": -3}}
            }
        ]
    },
]


def get_life_event_for_realm(realm_level: int) -> list:
    """获取当前境界可触发的所有生活事件"""
    return [e for e in LIFE_EVENTS if realm_level >= e["min_realm_level"]]


def get_event_by_id(event_id: str):
    """根据ID获取事件"""
    for e in LIFE_EVENTS:
        if e["id"] == event_id:
            return e
    return None


_CHOICE_COMMENTS = {
    "校霸堵门": {
        "正面硬刚": {"success": "好家伙，这一拳下去校霸的脸都歪了！建议改行当拳击手。", "fail": "emmm...被按在地上摩擦的样子，像极了被猫踩的蟑螂。"},
        "智取": {"success": "智商碾压！你这脑子不去参加最强大脑真是屈才了。", "fail": "计划通...了个寂寞。下次还是直接跑吧。"},
        "硬抗": {"success": "铁打的汉子！建议去工地干活，肯定是一把好手。", "fail": "直接被揍晕可还行？你怕不是来搞笑的吧。"},
    },
    "捡到钱包": {
        "拾金不昧": {"success": "活雷锋啊！这年头捡到钱还能还的，不是萌新就是圣人。", "fail": "好心没好报？这剧情连狗血剧都不敢这么写！"},
        "据为己有": {"success": "啧啧啧，白嫖的灵石真香是吧？小心晚上睡不着觉哦。", "fail": "刚想占便宜就被发现，这运气也是没谁了！"},
        "交给老师/长辈处理": {"success": "乖宝宝行为！老师给你发朵小红花。", "fail": "交上去都能被冒领？你这运气绝了！"},
    },
    "见义勇为": {
        "挺身而出": {"success": "侠肝义胆！建议去演武侠片，绝对男主角。", "fail": "虽然被揍了，但姿势很帅！虽败犹荣。"},
        "机智解围": {"success": "这波操作秀翻全场！脑子是个好东西，你不仅有还很好用。", "fail": "计谋被识破的瞬间，空气突然安静..."},
        "悄悄去叫老师": {"success": "借刀杀人，啊不，借师救人之计用得妙！", "fail": "老师不在办公室？这剧情我熟，恐怖片经典桥段！"},
    },
    "神秘摊位": {
        "花灵石买一卦": {"success": "老头说得玄乎其玄，你听得一脸崇拜——是不是被忽悠了？", "fail": "花了钱啥也没听懂，妥妥的交了智商税。"},
        "求取修炼心得": {"success": "老头传了你几句口诀，你感觉打开了新世界的大门！", "fail": "老头摇摇头——孩子，你根骨不行啊。"},
        "直接走人": {"success": "机智地躲过了消费陷阱，今天省了一个亿！", "fail": "走了还在背后被说，这老头怕不是个话痨。"},
    },
    "考试作弊": {
        "严词拒绝": {"success": "正气凛然！建议去当纪委，绝对是反腐先锋。", "fail": "拒绝了还被说你坏话？这年头好人难做啊。"},
        "答应帮忙": {"success": "完美操作！你有做间谍的天赋，建议报考国安局。", "fail": "被抓住了吧！考场如战场，翻车是常态。"},
        "假装答应然后举报": {"success": "这波碟中谍玩得溜！奥斯卡欠你一个小金人。", "fail": "玩脱了吧！下次还是简单点，套路别太深。"},
    },
    "路遇乞丐": {
        "慷慨解囊": {"success": "善心大发！建议多捐点，积德改命。", "fail": "刚掏钱就被围住？这怕不是丐帮团建现场。"},
        "买些吃的给他": {"success": "不是直接给钱而是买吃的，看来你是个暖心的聪明人！", "fail": "买个饭回来人就不见了？这剧情我熟，老江湖了。"},
        "视而不见": {"success": "省钱小能手！虽然良心有点痛。", "fail": "回头发现乞丐在看你——那眼神仿佛在说：我记住你了。"},
    },
    "江湖救急": {
        "运功疗伤": {"success": "运功救人，仙侠小说主角就是你！", "fail": "修为不够逞强救人？你这是救人还是自杀啊喂！"},
        "背去找大夫": {"success": "这条命是你救的！以后他就是你的人了。", "fail": "背到一半两人一起摔了——这画面太美我不敢看。"},
        "帮忙呼叫救援": {"success": "救人讲究方法，你是理智型选手！", "fail": "喊破喉咙也没人来...等等，这句台词怎么这么耳熟？"},
    },
    "天降横财": {
        "存起来修炼用": {"success": "理财小能手！你是修仙界的巴菲特。", "fail": "存钱都能被偷？你这运气不去买彩票可惜了。"},
        "大肆挥霍": {"success": "土豪气质暴露无遗！全场喊大佬。", "fail": "挥霍无度被盯上？你这是行走的ATM机啊。"},
        "捐给需要的人": {"success": "善举感动天地！书院欠你一面锦旗。", "fail": "捐钱都被中间人贪了？这世道太险恶了。"},
    },
    "校园传闻": {
        "当面质问": {"success": "气场全开！你这一瞪眼，造谣者直接怂了。", "fail": "质问反被倒打一耙？你这嘴皮子功夫还得练练。"},
        "用实力证明": {"success": "实力打脸！这才是最高级的反击。", "fail": "考砸了谣言反而被坐实？这下跳进黄河也洗不清了。"},
        "置之不理": {"success": "心态满分！有大佬风范，不在乎凡夫俗子的议论。", "fail": "表面不在意心里憋着气？兄dei，你这样容易走火入魔的。"},
    },
    "秘境入口": {
        "独自探索": {"success": "富贵险中求！你是天选之人，秘境都为你敞开。", "fail": "刚进去就被弹出来？秘境表示：你不配。"},
        "先探虚实": {"success": "稳扎稳打，你是修仙界的稳健派代表！", "fail": "感知到强大气息就退出来？苟，也是一种生存智慧。"},
        "做个标记找帮手": {"success": "团队合作意识满分！建议去考公务员，组织能力强。", "fail": "带人回来发现被洗劫一空？这秘境有毒！"},
    },
    "英雄救美": {
        "武力驱赶": {"success": "英雄救美！接下来是不是要以身相许了？", "fail": "打不过还被一起揍...这就是传说中的患难与共？"},
        "智取": {"success": "智商在线！巡逻队来得正是时候，你是导演吧？", "fail": "把戏被识破还被一起打？这剧本拿错了！"},
        "好言相劝": {"success": "以理服人！你的气场连地痞都怕。", "fail": "地痞根本不吃这套——看来你长得不够凶。"},
    },
    "商业机会": {
        "投资合作": {"success": "投资天才！恭喜你解锁了商业大亨成就。", "fail": "卷款跑路了？经典韭菜案例加一。"},
        "杀价入股": {"success": "精打细算！你是修仙界的葛朗台。", "fail": "投得少亏得少，你是懂得风险控制的。"},
        "拒绝": {"success": "谨慎是美德！你成功避开了所有坑。", "fail": "错过了一个亿！这感觉比亏钱还难受。"},
    },
    "迷路小孩": {
        "耐心安慰并帮忙找家长": {"success": "暖心大哥哥/大姐姐！家长给你发好人卡。", "fail": "安慰反把孩子越弄越哭？你这是哄孩子还是吓孩子呢。"},
        "带她去附近店铺问询": {"success": "机智！店铺老板娘果然是万能的情报站。", "fail": "转了一大圈最后还是送治安处了——今天的步数达标了！"},
    },
    "目睹车祸": {
        "冲上去救人": {"success": "见义勇为好青年！医馆都夸你处理得好。", "fail": "力气不够反而自己受伤了...好心办坏事典型教材。"},
        "维护秩序": {"success": "组织能力MAX！你天生就是当领导的料。", "fail": "没人听你的指挥？这届群众不行啊。"},
    },
    "邻里纠纷": {
        "强硬上门": {"success": "霸气侧漏！邻居被你吓得瑟瑟发抖。", "fail": "被轰出来了？这一家子人比你想象中能打。"},
        "以理服人": {"success": "和谐社会的楷模！建议去当居委会主任。", "fail": "讲道理没用？有时候拳头比道理好用。"},
        "忍了": {"success": "忍一时风平浪静！心境突破指日可待。", "fail": "忍到差点走火入魔？兄弟，别憋出病来。"},
    },
    "捡到小动物": {
        "带回去养": {"success": "捡到宝了！这运气建议去买彩票。", "fail": "养了三天就搞破坏？这怕不是二哈转世。"},
        "送到灵兽店": {"success": "不仅捡到宝还赚了一笔！人生赢家。", "fail": "老板说只是土狗？emmm...你高兴就好。"},
    },
    "同学借钱": {
        "慷慨借出": {"success": "识人精准！不仅收回本金还有利息，你是放贷天才。", "fail": "借钱后人就消失了？经典剧情，你的钱大概率是捐了。"},
        "只借一半": {"success": "留了一手！你是懂得风险管理的人才。", "fail": "借一半还是跑了？下次建议借十分之一。"},
        "婉拒": {"success": "火眼金睛！你预判了对方的预判。", "fail": "被说小气？走自己的路让别人说去吧。"},
    },
    "被迫演讲": {
        "硬着头皮上": {"success": "真情实感最打动人！你不去参加脱口秀可惜了。", "fail": "大脑一片空白？社死现场经典重现！"},
        "用段子化解": {"success": "幽默感MAX！全场被你圈粉。", "fail": "冷笑话没人笑...这尴尬程度突破天际了。"},
    },
    "修仙运动会": {
        "参加长跑": {"success": "飞毛腿！你是修仙界的博尔特。", "fail": "岔气了？建议下次跑慢点，装装样子也行。"},
        "参加举重": {"success": "大力士！建议去参加世界大力士比赛。", "fail": "被鼎压到脚？这画面有点好笑是怎么回事。"},
        "参加灵力比拼": {"success": "精神碾压！你这精神力不去练读心术可惜了。", "fail": "反噬自己？装逼失败典型案例。"},
        "参加阵法解谜": {"success": "智勇双全！你是修仙界的爱因斯坦。", "fail": "在迷阵里绕不出来？路痴属性暴露了。"},
    },
    "暴雨被困": {
        "冒雨冲回去": {"success": "速度与激情！你是雨中奔跑的王者。", "fail": "淋成落汤鸡？建议下次带伞，修仙者也要看天气预报。"},
        "运功避雨": {"success": "帅气逼人！用灵力撑伞，这操作我给满分。", "fail": "灵力不够淋成狗？下次记得带伞才是正道。"},
    },
}


def get_choice_comment(event_name, option_text, success):
    """根据事件和选择返回搞怪评价"""
    event_comments = _CHOICE_COMMENTS.get(event_name, {})
    # Try to match option_text prefix
    matched_key = None
    for key in event_comments:
        if option_text.startswith(key):
            matched_key = key
            break
    if matched_key:
        return event_comments[matched_key].get("success" if success else "fail", "")
    # Fallback generic comments
    if success:
        return random.choice(["这波操作很可以！", "完美！今天运气爆棚。", "大佬就是大佬！", "这波不亏！"])
    else:
        return random.choice(["翻车了？下次继续努力。", "emmm...这就很尴尬了。", "看来今天不适合出门。", "失败是成功之母...才怪。"])


def resolve_event_option(event, option_index: int, player, npcs: list) -> dict:
    """处理事件选择的固定选项，返回结果"""
    options = event.get("options", [])
    if option_index < 0 or option_index >= len(options):
        return {"log": "无效的选择。", "rewards": {}}

    option = options[option_index]
    attr = option["attr"]
    attr_value = getattr(player, attr, 0)

    # 随机校霸事件需要对抗
    if event.get("npc_generated") and event.get("npc_attrs"):
        npc_attrs = event["npc_attrs"]
        npc_value = random.randint(npc_attrs["strength_range"][0] if "strength" in npc_attrs else 30,
                                    npc_attrs["strength_range"][1] if "strength" in npc_attrs else 60)
        if attr == "strength":
            npc_value = random.randint(npc_attrs["strength_range"][0], npc_attrs["strength_range"][1])
        elif attr == "intelligence":
            npc_value = random.randint(20, 50)
        elif attr == "stamina":
            npc_value = random.randint(npc_attrs["stamina_range"][0], npc_attrs["stamina_range"][1])
        elif attr == "spirit":
            npc_value = random.randint(20, 50)
        success = attr_value >= npc_value
    else:
        # 普通事件，比较属性值
        threshold = 40 if attr == "good_evil" else 35
        # 用属性值+随机波动决定成败
        roll = random.randint(-10, 10)
        success = (attr_value + roll) >= threshold

    result_key = "success" if success else "fail"
    result = option[result_key]

    # 应用奖励
    rewards = result.get("rewards", {})
    for key, value in rewards.items():
        if hasattr(player, key):
            current = getattr(player, key)
            setattr(player, key, current + value)

    comment = get_choice_comment(event.get("name", ""), option.get("text", ""), success)

    return {
        "log": result.get("log", ""),
        "success": success,
        "rewards": rewards,
        "comment": comment
    }
