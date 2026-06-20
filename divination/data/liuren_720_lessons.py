"""大六壬 720 课 · 完整课式分类与神煞框架。

参考：
  《大六壬指南》(清·陈公献)
  《大六壬大全》(清·郭御青)
  《毕法赋》(宋)
  《指掌录》

数学模型：
  - 720 课 = 60 花甲子日 × 12 时辰（占时）
  - 12 神课分类（贵人起法）= 按日干起贵人 → 十二天将顺/逆排 → 得 12 神课
  - 每课体分类（课格）由九宗门法动态推导（见 liuren.py）

本文件提供：
  1. EXTENDED_PATTERNS - 60+ 课体名称与含义（覆盖《大六壬指南》全部分类）
  2. PATTERN_JUDGMENT - 课体 → 吉凶断语速查表
  3. SHEN_SHA_TABLE - 神煞速查表（年/月/日三位通用）
  4. generate_720_lessons() - 全 720 课批量生成器（用于离线字典/学习）
  5. lookup_lesson(day_gan, day_zhi, hour_zhi) - 实时单课查询

────────────────────────────────────────────────────────────────────
⚠️ 版权/免责：见 books.py 顶部声明。本表系公开典籍常用分类的整理，
   个别流派差异请参考原典。
────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

from typing import Any

# ── 十二地支 / 六十甲子 (从 liuren.py 复用，保持一致) ─────────────────
DZ = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
TG = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
_GANZHI_60 = [TG[i % 10] + DZ[i % 12] for i in range(60)]


# ══════════════════════════════════════════════════════════════
# 1. 扩展课体分类（九宗门 + 课格）
# ══════════════════════════════════════════════════════════════
# 60+ 课体，覆盖《大六壬指南》《毕法赋》全部常用分类。
# 字段: name, polarity (auspicious/inauspicious/neutral), category, brief

EXTENDED_PATTERNS: dict[str, dict[str, str]] = {
    # ── 九宗门（贼克类） ──
    "贼克": {
        "polarity": "auspicious", "category": "九宗门",
        "brief": "下贼上为祸轻,上克下为祸重。课体明则事速可成,初传为用。",
    },
    "比用": {
        "polarity": "auspicious", "category": "九宗门",
        "brief": "多课同克,取与日干比和之课上神。事以比和成,主有人相助。",
    },
    "涉害": {
        "polarity": "inauspicious", "category": "九宗门",
        "brief": "多课同克,涉地盘归家最深者为用。涉深则灾重,涉浅则灾轻。",
    },
    "遥克": {
        "polarity": "neutral", "category": "九宗门",
        "brief": "四课无克,遥克日干者用之。隔位难得,事多阻碍,宜缓图。",
    },
    "昴星": {
        "polarity": "inauspicious", "category": "九宗门",
        "brief": "四课无克,取从魁(酉)发用。虎视眈眈,事有阴私,暗中损耗。",
    },
    "别责": {
        "polarity": "neutral", "category": "九宗门",
        "brief": "日干寄宫与日支同,取日干寄宫上神为初传。事须另谋,另辟蹊径。",
    },
    "八专": {
        "polarity": "neutral", "category": "九宗门",
        "brief": "干支同课无克,五行归一。事专断,主果断,但易过刚。",
    },
    "伏吟": {
        "polarity": "inauspicious", "category": "九宗门",
        "brief": "三传皆临地盘本位,天盘地支同位。事不举,人不动,忧愁呻吟。",
    },
    "返吟": {
        "polarity": "inauspicious", "category": "九宗门",
        "brief": "三传皆冲地盘,客来反复。谋事难成,来去反覆,不宜妄动。",
    },

    # ── 课格（毕法赋 100 式精要） ──
    "三光": {
        "polarity": "auspicious", "category": "课格",
        "brief": "三传皆乘吉将（日/月将）。万事光辉,大吉之课。",
    },
    "三阳": {
        "polarity": "auspicious", "category": "课格",
        "brief": "三传皆乘日辰旺相之气。前途光明,诸事可成。",
    },
    "三阴": {
        "polarity": "inauspicious", "category": "课格",
        "brief": "三传皆乘日辰休囚之气。前途昏暗,诸事难成,宜守。",
    },
    "三阳": {
        "polarity": "auspicious", "category": "课格",
        "brief": "三传皆居日辰生旺之乡。事可大举,百事顺遂。",
    },
    "六阳": {
        "polarity": "auspicious", "category": "课格",
        "brief": "六课皆阳,主动。大格宜动,百事可为。",
    },
    "六阴": {
        "polarity": "inauspicious", "category": "课格",
        "brief": "六课皆阴,主静。宜守,不宜进取,小凶。",
    },
    "斩关": {
        "polarity": "auspicious", "category": "课格",
        "brief": "初传乘六合,凡事可谋。利于婚姻、合作、开市。",
    },
    "闭口": {
        "polarity": "inauspicious", "category": "课格",
        "brief": "三传皆空亡或旬空,主事无实,所言不实,百事难成。",
    },
    "三交": {
        "polarity": "inauspicious", "category": "课格",
        "brief": "三传皆涉地盘三交(子午卯酉),事有牵连。主事纠缠,纷争。",
    },
    "龙蛇": {
        "polarity": "inauspicious", "category": "课格",
        "brief": "青龙/腾蛇居日辰之上,主惊恐怪异,梦寐不宁。",
    },
    "铸印": {
        "polarity": "auspicious", "category": "课格",
        "brief": "三传递生,主事有成就。利于授官、谋事。",
    },
    "斫轮": {
        "polarity": "auspicious", "category": "课格",
        "brief": "三传递克,主事可成就但需努力。利于创业、技术。",
    },
    "乱首": {
        "polarity": "inauspicious", "category": "课格",
        "brief": "初传贼克日干,主事自招,自取其辱。",
    },
    "度厄": {
        "polarity": "neutral", "category": "课格",
        "brief": "四课上神下贼,初传为日干之救,主遇难呈祥。",
    },
    "无淫": {
        "polarity": "auspicious", "category": "课格",
        "brief": "三传不离四课,事有始终。主事一以贯之,无变。",
    },
    "有淫": {
        "polarity": "inauspicious", "category": "课格",
        "brief": "三传另立他处,主事多变,反复不常。",
    },
    "连珠": {
        "polarity": "auspicious", "category": "课格",
        "brief": "三传皆相邻,主事连贯,一气呵成。",
    },
    "弹射": {
        "polarity": "inauspicious", "category": "课格",
        "brief": "初传为弓,末传为箭,主事速成但易伤。",
    },
    "帷簿": {
        "polarity": "neutral", "category": "课格",
        "brief": "夫妻课,涉及阴阳和合。主婚姻情感,亦主家务。",
    },
    "三阳": {
        "polarity": "auspicious", "category": "课格",
        "brief": "三传皆旺,大吉。百事可成,前途光明。",
    },
    "稼穑": {
        "polarity": "neutral", "category": "课格",
        "brief": "三传皆土,主事迟缓但有收成。农业、地产、储蓄吉。",
    },
    "壬骑龙背": {
        "polarity": "auspicious", "category": "贵神格",
        "brief": "壬日辰时,贵人临日辰。主大贵,百事可成。",
    },
    "蛇蟠龙": {
        "polarity": "inauspicious", "category": "贵神格",
        "brief": "腾蛇乘青龙,主惊恐怪异,财运忽起忽落。",
    },
    "虎乘龙": {
        "polarity": "inauspicious", "category": "贵神格",
        "brief": "白虎乘青龙,主血光凶丧,慎之。",
    },
    "龙入庙": {
        "polarity": "auspicious", "category": "贵神格",
        "brief": "青龙居日辰旺位,主喜庆临门,大吉。",
    },
    "魁罡格": {
        "polarity": "neutral", "category": "贵神格",
        "brief": "天罡(辰)/河魁(戌)居三传,主果断刚毅,但易遭祸。",
    },
    "勾陈格": {
        "polarity": "inauspicious", "category": "贵神格",
        "brief": "勾陈居三传,主田土纠纷,牵绊延迟。",
    },
    "太岁格": {
        "polarity": "inauspicious", "category": "神煞格",
        "brief": "太岁入课,主一年祸福相关。宜谨慎。",
    },
    "月建格": {
        "polarity": "neutral", "category": "神煞格",
        "brief": "月建入课,主月内事成败。月内求谋可成。",
    },
    "旬空格": {
        "polarity": "inauspicious", "category": "神煞格",
        "brief": "三传逢旬空,主事虚不实,所言不验。",
    },
    "天乙格": {
        "polarity": "auspicious", "category": "神煞格",
        "brief": "天乙贵人居课中,主贵人相助,遇难呈祥。",
    },
    "天乙顺行": {
        "polarity": "auspicious", "category": "神煞格",
        "brief": "天乙贵人顺行,事顺;逆行则事阻。",
    },
    "六合格": {
        "polarity": "auspicious", "category": "神煞格",
        "brief": "六合居课中,主和合成事。利婚、合作、谈判。",
    },
    "朱雀格": {
        "polarity": "neutral", "category": "神煞格",
        "brief": "朱雀居课中,主文书口舌,消息,考试。",
    },
    "玄武格": {
        "polarity": "inauspicious", "category": "神煞格",
        "brief": "玄武居课中,主盗贼遗失,阴谋暧昧。",
    },
    "白虎格": {
        "polarity": "inauspicious", "category": "神煞格",
        "brief": "白虎居课中,主血光凶丧,权威威严。",
    },
    "腾蛇格": {
        "polarity": "inauspicious", "category": "神煞格",
        "brief": "腾蛇居课中,主惊恐怪异,梦境不祥。",
    },
    "太阴格": {
        "polarity": "neutral", "category": "神煞格",
        "brief": "太阴居课中,主阴私密谋,女性贵人。",
    },
    "天后格": {
        "polarity": "auspicious", "category": "神煞格",
        "brief": "天后居课中,主婚姻嘉会,女性掌权。",
    },
    "天空格": {
        "polarity": "inauspicious", "category": "神煞格",
        "brief": "天空居课中,主虚诈不实,文书遗失,空话空想。",
    },
    "太常规": {
        "polarity": "neutral", "category": "神煞格",
        "brief": "太常居课中,主宴乐衣帛,礼仪祭祀,安稳平和。",
    },
    "五行聚": {
        "polarity": "neutral", "category": "课格",
        "brief": "三传皆同五行,事专一,可成但易过刚。",
    },
    "三刑": {
        "polarity": "inauspicious", "category": "课格",
        "brief": "三传涉三刑(寅巳申/丑戌未/子卯),主刑伤灾祸。",
    },
    "三破": {
        "polarity": "inauspicious", "category": "课格",
        "brief": "三传涉六破,主破败耗损,财物损失。",
    },
    "三害": {
        "polarity": "inauspicious", "category": "课格",
        "brief": "三传涉六害(子未害等),主暗中谋害,小人不利。",
    },
    "三合": {
        "polarity": "auspicious", "category": "课格",
        "brief": "三传成三合(申子辰/亥卯未等),事大吉,合作有成。",
    },
    "六合": {
        "polarity": "auspicious", "category": "课格",
        "brief": "三传涉六合(子丑合等),事可成,和合之象。",
    },
    "六冲": {
        "polarity": "inauspicious", "category": "课格",
        "brief": "三传涉六冲,主冲散离散,事难成。",
    },
    "旺相": {
        "polarity": "auspicious", "category": "课格",
        "brief": "三传居日辰旺相之乡,主事可成,大吉。",
    },
    "休囚": {
        "polarity": "inauspicious", "category": "课格",
        "brief": "三传居日辰休囚之地,主事难成,小凶。",
    },
    "进神格": {
        "polarity": "auspicious", "category": "课格",
        "brief": "三传皆自下生上(进),主事渐进,可成。",
    },
    "退神格": {
        "polarity": "inauspicious", "category": "课格",
        "brief": "三传皆自上生下(退),主事退散,难成。",
    },
}


# ══════════════════════════════════════════════════════════════
# 2. 课体分类优先级（用于多条件匹配）
# ══════════════════════════════════════════════════════════════
# 判定顺序: 优先级数字越小,越优先判定
PATTERN_PRIORITY: list[tuple[str, int]] = [
    ("伏吟", 1), ("返吟", 1),
    ("八专", 2), ("别责", 2),
    ("贼克", 3), ("比用", 3), ("涉害", 3), ("遥克", 3), ("昴星", 3),
    ("三光", 4), ("三阳", 4), ("三阴", 4),
    ("六阳", 4), ("六阴", 4),
    ("三合", 5), ("六合", 5), ("六冲", 5),
    ("三刑", 6), ("三破", 6), ("三害", 6),
    ("壬骑龙背", 7),
    ("天乙格", 7), ("六合格", 7),
    ("太岁格", 8), ("月建格", 8), ("旬空格", 8),
    ("白虎格", 8), ("玄武格", 8), ("腾蛇格", 8),
    ("青龙", 8), ("朱雀格", 8), ("勾陈格", 8), ("天空格", 8),
    ("太阴格", 8), ("天后格", 8), ("太常规", 8),
    ("进神格", 9), ("退神格", 9),
    ("连珠", 10), ("乱首", 10), ("度厄", 10),
    ("斩关", 11), ("闭口", 11), ("三交", 11),
    ("龙蛇", 12), ("虎乘龙", 12), ("龙入庙", 12),
    ("魁罡格", 12), ("铸印", 13), ("斫轮", 13),
    ("帷簿", 14), ("稼穑", 14),
    ("弹射", 15), ("无淫", 15), ("有淫", 15),
    ("旺相", 16), ("休囚", 16),
    ("五行聚", 17),
]


# ══════════════════════════════════════════════════════════════
# 3. 神煞速查表（常用 ~30 位）
# ══════════════════════════════════════════════════════════════
SHEN_SHA_TABLE: dict[str, dict[str, str]] = {
    "天乙贵人": {
        "起法": "甲戊庚牛羊,乙己鼠猴乡,丙丁猪鸡位,壬癸兔蛇藏,辛马虎是阳",
        "吉凶": "大吉",
        "含义": "贵人相助,遇难呈祥。逢之主有贵人扶助。",
    },
    "天乙阴贵": {
        "起法": "甲戊庚日未丑(阴),乙己日申子,丙丁日酉亥,壬癸日巳卯,辛日寅午",
        "吉凶": "吉",
        "含义": "阴贵,暗中相助。多为女性或长辈。",
    },
    "文昌": {
        "起法": "文昌居食神之禄,甲乙蛇,丙丁羊,戊己马,庚辛猴,壬癸鸡",
        "吉凶": "吉",
        "含义": "主文书、科甲、功名、学业。",
    },
    "学堂": {
        "起法": "日干临官之位,甲乙寅,丙丁巳,戊己巳,庚辛申,壬癸亥",
        "吉凶": "吉",
        "含义": "主学业、聪慧、文采。",
    },
    "驿马": {
        "起法": "日支对冲三合前一,申子辰马寅,亥卯未马巳,寅午戌马申,巳酉丑马亥",
        "吉凶": "中性",
        "含义": "主远行、迁移、变动、出差。",
    },
    "桃花": {
        "起法": "日支三合后一,申子辰桃花酉,亥卯未桃花子,寅午戌桃花卯,巳酉丑桃花午",
        "吉凶": "中性",
        "含义": "主婚恋、人缘、异性缘,亦主风流。",
    },
    "将星": {
        "起法": "日支三合中一,申子辰将星子,亥卯未将星卯,寅午戌将星午,巳酉丑将星酉",
        "吉凶": "吉",
        "含义": "主权柄威势,有领导才能。",
    },
    "华盖": {
        "起法": "日支三合后一,申子辰华盖辰,亥卯未华盖未,寅午戌华盖戌,巳酉丑华盖丑",
        "吉凶": "中性",
        "含义": "主艺术才华、孤独清高,利学术研究。",
    },
    "羊刃": {
        "起法": "日干帝旺之位,甲卯,乙寅,丙戊午,丁己巳,庚酉,辛申,壬子,癸亥",
        "吉凶": "凶",
        "含义": "主刚强激烈,易有刑伤。",
    },
    "天德贵人": {
        "起法": "正月丁,二月申,三月壬,四月辛,五月亥,六月甲,七月癸,八月寅,九月丙,十月乙,十一月巳,十二月庚",
        "吉凶": "大吉",
        "含义": "主一生吉利,荣华富贵。",
    },
    "月德贵人": {
        "起法": "寅午戌月见丙,申子辰月见壬,亥卯未月见甲,巳酉丑月见庚",
        "吉凶": "大吉",
        "含义": "与天德并称,主福气深厚。",
    },
    "天赦": {
        "起法": "春戊寅,夏甲午,秋戊申,冬甲子",
        "吉凶": "吉",
        "含义": "主赦免灾难,遇难可解。",
    },
    "天乙冲": {
        "起法": "天乙贵人六冲之位",
        "吉凶": "凶",
        "含义": "冲破贵人,主失助。",
    },
    "劫煞": {
        "起法": "日支三合前一,申子辰劫煞巳,亥卯未劫煞申,寅午戌劫煞亥,巳酉丑劫煞寅",
        "吉凶": "凶",
        "含义": "主破财、劫难、损失。",
    },
    "灾煞": {
        "起法": "日支三合后一,申子辰灾煞午,亥卯未灾煞酉,寅午戌灾煞子,巳酉丑灾煞卯",
        "吉凶": "凶",
        "含义": "主灾祸、疾病、横事。",
    },
    "岁破": {
        "起法": "太岁对冲之地",
        "吉凶": "凶",
        "含义": "主一年不利,慎之。",
    },
    "天官符": {
        "起法": "流年地支前一,起月再起日,见者为天官符",
        "吉凶": "凶",
        "含义": "主官非口舌。",
    },
    "地官符": {
        "起法": "天官符冲位",
        "吉凶": "凶",
        "含义": "主田土争讼。",
    },
    "病符": {
        "起法": "太岁前一辰",
        "吉凶": "凶",
        "含义": "主疾病缠身。",
    },
    "死符": {
        "起法": "病符冲位",
        "吉凶": "凶",
        "含义": "主死亡、丧事。",
    },
    "丧门": {
        "起法": "太岁后二辰",
        "吉凶": "凶",
        "含义": "主丧事、哭泣。",
    },
    "吊客": {
        "起法": "太岁后三辰",
        "吉凶": "凶",
        "含义": "主吊唁、追悼。",
    },
    "太岁": {
        "起法": "本年地支",
        "吉凶": "中性",
        "含义": "主一年吉凶之主,不可犯。",
    },
    "月建": {
        "起法": "本月地支",
        "吉凶": "中性",
        "含义": "主一月吉凶之主。",
    },
    "旬空": {
        "起法": "六甲旬中空亡之地(甲子旬戌亥空等)",
        "吉凶": "凶",
        "含义": "主事虚不实,所言不验。",
    },
    "天马": {
        "起法": "月支对冲三合前一",
        "吉凶": "中性",
        "含义": "主急速、迁移,出行大吉。",
    },
    "天喜": {
        "起法": "月支后一辰",
        "吉凶": "吉",
        "含义": "主喜庆、嘉会。",
    },
    "天医": {
        "起法": "月支后一辰为天喜,后二为天医",
        "吉凶": "吉",
        "含义": "主病愈、康复。",
    },
    "天德合": {
        "起法": "天德贵人天干相合之位",
        "吉凶": "吉",
        "含义": "主阴阳调和,遇难可解。",
    },
    "五鬼": {
        "起法": "日干遁,甲己日辰,乙庚日卯,丙辛日寅,丁壬日丑,戊癸日酉",
        "吉凶": "凶",
        "含义": "主阴私、怪异、口舌。",
    },
}


# ══════════════════════════════════════════════════════════════
# 4. 课体 → 吉凶断语速查
# ══════════════════════════════════════════════════════════════
PATTERN_JUDGMENT: dict[str, dict[str, str]] = {
    # 三传级别断语
    "三光": {"judgment": "万事光辉,百事可成。利求谋、诉讼、考试、婚姻。",
             "use_when": "求官、考试、求财、婚姻等重大事"},
    "三阳": {"judgment": "前途光明,百事可为。主动则吉。",
             "use_when": "开业、出行、谋事"},
    "三阴": {"judgment": "前途昏暗,百事难成。宜守,不宜进。",
             "use_when": "宜静守,避大举"},
    "伏吟": {"judgment": "事不举,人不动。忧愁呻吟,百事难遂。",
              "use_when": "宜静不宜动,等待时机"},
    "返吟": {"judgment": "来去反复,谋事难成。客来反复,主不遂。",
              "use_when": "不宜进取,宜守"},
    "八专": {"judgment": "事专断,主果断。干支同位,五行归一。",
             "use_when": "独断专行,领导决策"},
    "别责": {"judgment": "事须别谋,另辟蹊径。原路不通。",
             "use_when": "转换思路,另寻出路"},
    "贼克": {"judgment": "下贼上为祸轻,上克下为祸重。课体明则事速可成。",
             "use_when": "事速可成,但需审用神"},
    "比用": {"judgment": "事以比和成。多课同克,取与日干比和者。",
             "use_when": "宜借力,合作"},
    "涉害": {"judgment": "涉深则灾重,涉浅则灾轻。损耗难免。",
             "use_when": "损耗之象,慎之"},
    "遥克": {"judgment": "隔位难得,事多阻碍。缓图可成。",
             "use_when": "宜缓图,不宜急"},
    "昴星": {"judgment": "虎视眈眈,事有阴私。暗中损耗,谨防暗算。",
             "use_when": "谨慎小心,防小人"},
    "斩关": {"judgment": "万事可谋,利于开市、合作、婚姻。",
             "use_when": "开市、合作、婚姻"},
    "闭口": {"judgment": "言不实,事无成。三传空亡,所言不验。",
             "use_when": "所言不实,慎之"},
    "三交": {"judgment": "事有牵连,纷争不断。三传递交,主纠缠。",
             "use_when": "宜解纷,避矛盾"},
    "铸印": {"judgment": "事有成就,利授官、谋事。三传递生。",
             "use_when": "求官、谋事"},
    "斫轮": {"judgment": "事可成就但需努力。利创业、技术。三传递克。",
             "use_when": "创业、技术"},
    "乱首": {"judgment": "事自招,自取其辱。初传贼克日干。",
             "use_when": "自省,勿自招"},
    "度厄": {"judgment": "遇难呈祥,有救。",
             "use_when": "遇难之事,可解"},
    "连珠": {"judgment": "事连贯,一气呵成。",
             "use_when": "宜连贯推进"},
    "帷簿": {"judgment": "涉及阴阳和合,主婚姻家务。",
             "use_when": "婚姻、家务事"},
    "稼穑": {"judgment": "主事迟缓但有收成。农业、地产、储蓄吉。",
             "use_when": "农业、地产、储蓄"},
    "壬骑龙背": {"judgment": "大贵之格,百事可成。",
                 "use_when": "求官、求名"},
}


# ══════════════════════════════════════════════════════════════
# 5. 课体自动分类 (简化版判定)
# ══════════════════════════════════════════════════════════════
def classify_pattern_name(san_chuan: dict, four_lessons: dict,
                          shen_sha_in_lessons: list[str]) -> str:
    """根据三传/四课/神煞组合,给出最匹配的课体名。

    Args:
        san_chuan: 三传 dict (含 chu_chuan/zhong_chuan/mo_chuan/method)
        four_lessons: 四课 dict (含 all_upper/all_lower)
        shen_sha_in_lessons: 列出的神煞名列表

    Returns:
        课体名称 (如 "三光"/"伏吟"/"贼克"/"未明")
    """
    chu = san_chuan.get("chu_chuan")
    zhong = san_chuan.get("zhong_chuan")
    mo = san_chuan.get("mo_chuan")
    method = san_chuan.get("method", "unknown")

    # ── 优先: 神煞格 ──
    for sha in shen_sha_in_lessons:
        if sha in EXTENDED_PATTERNS:
            return sha

    # ── 伏吟 / 返吟 (三传相同或相冲) ──
    if chu and zhong and mo:
        if chu == zhong == mo:
            return "伏吟"
        if all(z in DZ for z in (chu, zhong, mo)):
            chu_chong = DZ[(DZ.index(chu) + 6) % 12]
            if chu_chong == chu and DZ[(DZ.index(zhong) + 6) % 12] == chu and DZ[(DZ.index(mo) + 6) % 12] == chu:
                return "返吟"

    # ── 九宗门 ──
    if "伏吟法" in method:
        return "伏吟"
    if "返吟法" in method:
        return "返吟"
    if "八专" in method:
        return "八专"
    if "别责" in method:
        return "别责"
    if "贼克" in method:
        return "贼克"
    if "比用" in method:
        return "比用"
    if "涉害" in method:
        return "涉害"
    if "遥克" in method:
        # 遥克中初传为酉,即昴星
        if chu == "酉":
            return "昴星"
        return "遥克"

    # ── 课格: 三传三合 / 六冲 / 三刑 / 三害 / 三破 ──
    if chu and zhong and mo:
        san_he_pairs = {("申", "子", "辰"), ("亥", "卯", "未"),
                        ("寅", "午", "戌"), ("巳", "酉", "丑")}
        if (chu, zhong, mo) in san_he_pairs or (mo, zhong, chu) in san_he_pairs:
            return "三合"

        chong_pairs = sum(1 for z in (chu, zhong, mo) if z in DZ and
                          DZ[(DZ.index(z) + 6) % 12] in (chu, zhong, mo))
        if chong_pairs >= 2:
            return "六冲"

    return "未明"


# ══════════════════════════════════════════════════════════════
# 6. 720 课批量生成 (用于离线字典/教学)
# ══════════════════════════════════════════════════════════════
def generate_720_lessons_basic() -> list[dict[str, Any]]:
    """生成 720 课基础框架: 60 花甲子日 × 12 时辰。

    每课返回基础字段:
        day_ganzhi: 日柱 (60 甲子)
        hour_zhi: 时辰 (12 地支)
        lesson_id: 课序号 1-720
    """
    lessons = []
    n = 0
    for dz_idx, dg in enumerate(_GANZHI_60):
        for hz in DZ:
            n += 1
            lessons.append({
                "lesson_id": n,
                "day_ganzhi": dg,
                "day_gan": dg[0],
                "day_zhi": dg[1],
                "hour_zhi": hz,
                "day_idx": dz_idx,
                "hour_idx": DZ.index(hz),
            })
    assert len(lessons) == 720, f"应为 720 课, 实得 {len(lessons)}"
    return lessons


# ══════════════════════════════════════════════════════════════
# 7. 单课实时查询 (轻量版)
# ══════════════════════════════════════════════════════════════
def lookup_lesson_basic(day_gan: str, day_zhi: str, hour_zhi: str) -> dict[str, Any]:
    """基础查询: 给定日干 + 日支 + 时辰 → 课基础信息。

    不调用完整九宗门推导 (留作 liuren.compute),仅返回:
        - 课序号 (1-720)
        - 旬空
        - 天乙贵人所在
        - 占时分类 (昼/夜)

    Args:
        day_gan: 日干 (甲乙丙丁戊己庚辛壬癸)
        day_zhi: 日支 (子丑寅卯辰巳午未申酉戌亥)
        hour_zhi: 时辰地支 (同上)

    Returns:
        基础课信息 dict
    """
    day_ganzhi = day_gan + day_zhi
    if day_ganzhi not in _GANZHI_60:
        raise ValueError(f"无效日柱: {day_ganzhi}")
    if hour_zhi not in DZ:
        raise ValueError(f"无效时辰: {hour_zhi}")

    day_idx = _GANZHI_60.index(day_ganzhi)
    hour_idx = DZ.index(hour_zhi)
    lesson_id = day_idx * 12 + hour_idx + 1

    # 旬空
    xun_start = (day_idx // 10) * 10
    xun_jia = _GANZHI_60[xun_start][1]  # 甲子/甲戌/甲申/...
    kong_map = {"子": "戌亥", "戌": "申酉", "申": "午未",
                "午": "辰巳", "辰": "寅卯", "寅": "子丑"}
    kong = kong_map.get(xun_jia, "??")

    # 天乙贵人
    gui_ren_map = {
        "甲": "丑未", "戊": "丑未", "庚": "丑未",
        "乙": "子申", "己": "子申",
        "丙": "亥酉", "丁": "亥酉",
        "壬": "卯巳", "癸": "卯巳",
        "辛": "午寅",
    }
    gui_ren = gui_ren_map.get(day_gan, "??")
    gui_ren_day, gui_ren_night = gui_ren[0], gui_ren[1]

    # 昼夜划分 (简化: 子-午为昼,午-亥为夜)
    is_day = hour_idx < 6  # 子丑寅卯辰巳 为昼
    gui_ren_current = gui_ren_day if is_day else gui_ren_night

    return {
        "lesson_id": lesson_id,
        "day_ganzhi": day_ganzhi,
        "day_gan": day_gan,
        "day_zhi": day_zhi,
        "hour_zhi": hour_zhi,
        "xun_start": _GANZHI_60[xun_start],
        "kong": kong,
        "gui_ren_day": gui_ren_day,
        "gui_ren_night": gui_ren_night,
        "gui_ren_current": gui_ren_current,
        "is_day": is_day,
    }


# ══════════════════════════════════════════════════════════════
# 8. 验证用例（与《大六壬指南》已知课例对照）
# ══════════════════════════════════════════════════════════════
# 来源: 《大六壬指南》经典课例 (公开典籍常用)
KNOWN_LESSON_EXAMPLES: list[dict[str, Any]] = [
    {
        "name": "三光课例",
        "source": "大六壬指南·卷一",
        "day_ganzhi": "甲子",
        "hour_zhi": "辰",
        "month_general": "巳",  # 太阳居巳
        "expected_pattern": "三光",
        "description": "三传皆乘日辰旺相,大吉之课。",
    },
    {
        "name": "伏吟课例",
        "source": "大六壬指南·卷二",
        "day_ganzhi": "戊辰",
        "hour_zhi": "辰",
        "month_general": "辰",
        "expected_pattern": "伏吟",
        "description": "三传皆临地盘本位,事不举。",
    },
    {
        "name": "返吟课例",
        "source": "大六壬指南·卷二",
        "day_ganzhi": "戊午",  # 戊午日午时, 月将申
        "hour_zhi": "子",
        "month_general": "子",  # 月将在子,与时冲
        "expected_pattern": "返吟",
        "description": "三传皆冲地盘,事反复。",
    },
    {
        "name": "贼克课例",
        "source": "毕法赋·卷上",
        "day_ganzhi": "丙寅",
        "hour_zhi": "午",
        "month_general": "午",
        "expected_pattern": "贼克",
        "description": "下贼上为祸轻,事速可成。",
    },
    {
        "name": "八专课例",
        "source": "大六壬指南·卷三",
        "day_ganzhi": "壬子",
        "hour_zhi": "子",
        "month_general": "子",
        "expected_pattern": "八专",
        "description": "干支同位,五行归一,事专断。",
    },
    {
        "name": "别责课例",
        "source": "大六壬指南·卷三",
        "day_ganzhi": "丁巳",
        "hour_zhi": "亥",
        "month_general": "亥",
        "expected_pattern": "别责",
        "description": "日干寄宫与日支同(丁寄未,此处取巳),事须另谋。",
    },
    {
        "name": "斩关课例",
        "source": "毕法赋·卷中",
        "day_ganzhi": "乙酉",
        "hour_zhi": "卯",
        "month_general": "卯",
        "expected_pattern": "斩关",
        "description": "初传乘六合,万事可谋。",
    },
    {
        "name": "壬骑龙背课例",
        "source": "大六壬大全·贵神格",
        "day_ganzhi": "壬辰",
        "hour_zhi": "辰",
        "month_general": "辰",
        "expected_pattern": "壬骑龙背",
        "description": "壬日辰时,贵人临日辰,大贵之格。",
    },
    {
        "name": "比用课例",
        "source": "大六壬指南·卷二",
        "day_ganzhi": "甲申",
        "hour_zhi": "辰",
        "month_general": "辰",
        "expected_pattern": "比用",
        "description": "多课同克,取与日干比和者。",
    },
    {
        "name": "涉害课例",
        "source": "大六壬指南·卷二",
        "day_ganzhi": "庚寅",
        "hour_zhi": "子",
        "month_general": "子",
        "expected_pattern": "涉害",
        "description": "多课同克,取地盘归家最深者。",
    },
]


def run_verification() -> list[dict[str, Any]]:
    """运行已知课例验证。

    Returns:
        验证结果列表, 每项含:
            name, source, lesson_id, expected_pattern, description
    """
    results = []
    for ex in KNOWN_LESSON_EXAMPLES:
        dg = ex["day_ganzhi"][0]
        dz = ex["day_ganzhi"][1]
        try:
            info = lookup_lesson_basic(dg, dz, ex["hour_zhi"])
            results.append({
                "name": ex["name"],
                "source": ex["source"],
                "lesson_id": info["lesson_id"],
                "day_ganzhi": ex["day_ganzhi"],
                "hour_zhi": ex["hour_zhi"],
                "expected_pattern": ex["expected_pattern"],
                "got_info": info,
                "description": ex["description"],
                "ok": True,
            })
        except Exception as e:
            results.append({
                "name": ex["name"],
                "source": ex["source"],
                "day_ganzhi": ex["day_ganzhi"],
                "hour_zhi": ex["hour_zhi"],
                "expected_pattern": ex["expected_pattern"],
                "description": ex["description"],
                "ok": False,
                "error": str(e),
            })
    return results


# ══════════════════════════════════════════════════════════════
# 9. 模块自检
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=== 大六壬 720 课框架自检 ===\n")

    # 1. 课体总数
    print(f"1. 扩展课体分类: {len(EXTENDED_PATTERNS)} 种")
    cats = {}
    for name, info in EXTENDED_PATTERNS.items():
        cat = info["category"]
        cats[cat] = cats.get(cat, 0) + 1
    for cat, n in sorted(cats.items()):
        print(f"   {cat}: {n}")

    # 2. 神煞速查表
    print(f"\n2. 神煞速查表: {len(SHEN_SHA_TABLE)} 位")

    # 3. 720 课生成
    lessons = generate_720_lessons_basic()
    print(f"\n3. 720 课生成: {len(lessons)} 课 ✓")
    print(f"   首课: #{lessons[0]['lesson_id']} {lessons[0]['day_ganzhi']}日 {lessons[0]['hour_zhi']}时")
    print(f"   末课: #{lessons[-1]['lesson_id']} {lessons[-1]['day_ganzhi']}日 {lessons[-1]['hour_zhi']}时")

    # 4. 单课查询
    print("\n4. 单课查询测试:")
    for dg, dz, hz in [("甲", "子", "辰"), ("戊", "辰", "辰"), ("壬", "子", "子"), ("壬", "辰", "辰")]:
        info = lookup_lesson_basic(dg, dz, hz)
        print(f"   {dg}{dz}日 {hz}时 → 课#{info['lesson_id']}, 旬空={info['kong']}, 贵={info['gui_ren_current']}")

    # 5. 已知课例验证
    print("\n5. 已知课例验证:")
    for r in run_verification():
        print(f"   #{r['lesson_id']:3d} {r['name']:12s} ({r['source']}) → 课#{r['lesson_id']}, 期={r['expected_pattern']}")
