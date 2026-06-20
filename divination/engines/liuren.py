"""大六壬 (Da Liu Ren) — 三式之首, 天地盘 + 四课三传。

实现:
- 天地盘: 地盘固定 12 地支, 天盘月将加时
- 月将: 基于 24 节气的中气 (太阳过宫)
- 四课: 日干支与地盘交互生成四课
- 三传: 九宗门法 (简化贼克/比用/涉害/遥克/昴星/伏吟/返吟/别责/八专)
- 十二天将: 贵人顺逆排布
- 遁干/旬空/五行生克

参考: 《大六壬大全》《六壬断案》《六壬指南》
"""

from datetime import date, datetime

from ..contracts import Birth, ChartResult

# ═══════════════════════════════════════════════════════════════
# 1. 基础常量
# ═══════════════════════════════════════════════════════════════
# 十二地支
DZ = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 十天干
TG = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 地支五行
DZ_WX = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
         "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}

# 天干五行
TG_WX = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
         "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}

# 五行生克
_WX_OVERCOME = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 十二天将 (贵人体系)
_GENERALS = ["贵人", "腾蛇", "朱雀", "六合", "勾陈", "青龙", "天空", "白虎", "太常", "玄武", "太阴", "天后"]
_GENERAL_WX = {
    "贵人": "土", "腾蛇": "火", "朱雀": "火", "六合": "木", "勾陈": "土", "青龙": "木",
    "天空": "土", "白虎": "金", "太常": "土", "玄武": "水", "太阴": "金", "天后": "水",
}
_GENERAL_MEANING = {
    "贵人": "贵人来助、上司/长辈、官运、名誉",
    "腾蛇": "惊恐怪异、虚浮不实、火烛之灾、梦境",
    "朱雀": "文书口舌、消息传递、考试、是非",
    "六合": "婚姻和合、中介媒介、合作契约",
    "勾陈": "争斗迟滞、田土纠纷、牵连牵绊",
    "青龙": "喜庆财运、升迁之兆、贵人途中的吉神",
    "天空": "虚诈不实、空话空想、文书遗失",
    "白虎": "凶丧血光、权威威严、疾病手术",
    "太常": "宴乐衣帛、礼仪祭祀、安稳平和",
    "玄武": "盗贼遗失、暧昧不明、水厄",
    "太阴": "阴私密谋、女性贵人、暗中相助",
    "天后": "婚姻嘉会、女性掌权、恩泽庇护",
}

# 月将 (中气后太阳所在宫位)
# 月将名: 登明亥 河魁戌 从魁酉 传送申 小吉未 胜光午 太乙巳 天罡辰 太冲卯 功曹寅 大吉丑 神后子
_MONTH_GENERAL_NAMES = {
    "亥": "登明", "戌": "河魁", "酉": "从魁", "申": "传送",
    "未": "小吉", "午": "胜光", "巳": "太乙", "辰": "天罡",
    "卯": "太冲", "寅": "功曹", "丑": "大吉", "子": "神后",
}

# 月将表: (公历月日范围) → 月将地支
# 基于 24 节气中气: 雨水→亥, 春分→戌, 谷雨→酉, 小满→申, 夏至→未, 大暑→午, 处暑→巳, 秋分→辰, 霜降→卯, 小雪→寅, 冬至→丑, 大寒→子
_SOLAR_TERM_GENERAL = [
    (1, 20, "子"),   # 大寒 → 神后
    (2, 19, "亥"),   # 雨水 → 登明
    (3, 21, "戌"),   # 春分 → 河魁
    (4, 20, "酉"),   # 谷雨 → 从魁
    (5, 21, "申"),   # 小满 → 传送
    (6, 21, "未"),   # 夏至 → 小吉
    (7, 22, "午"),   # 大暑 → 胜光
    (8, 23, "巳"),   # 处暑 → 太乙
    (9, 23, "辰"),   # 秋分 → 天罡
    (10, 23, "卯"),  # 霜降 → 太冲
    (11, 22, "寅"),  # 小雪 → 功曹
    (12, 22, "丑"),  # 冬至 → 大吉
]


def _get_month_general(month: int, day: int) -> str:
    """根据公历月日返回月将地支.

    24节气中气表(月份-起始日-月将): 1/20→子, 2/19→亥, 3/21→戌, ...
    直接用 sorted 列表+顺序遍历, 避免跨月索引。
    """
    candidates = sorted(_SOLAR_TERM_GENERAL, key=lambda x: (x[0], x[1]))
    # 找到最后一个 (m,d) <= (month, day) 的项
    best = "子"  # fallback
    for m, d, general in candidates:
        if (month, day) >= (m, d):
            best = general
        else:
            break
    return best


def _get_hour_branch(hour: int) -> str:
    """时辰 → 地支 (23-1=子, 1-3=丑, ...)"""
    return DZ[((hour + 1) // 2) % 12]


# 贵人起法: 日干决定贵人所在, 昼夜分顺逆
# 甲戊庚牛羊(丑未), 乙己鼠猴(子申), 丙丁猪鸡(亥酉), 壬癸兔蛇(卯巳), 辛马虎(午寅)
_GUI_REN_TABLE = {
    "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
    "乙": ("子", "申"), "己": ("子", "申"),
    "丙": ("亥", "酉"), "丁": ("亥", "酉"),
    "壬": ("卯", "巳"), "癸": ("卯", "巳"),
    "辛": ("午", "寅"),
}


def _get_gui_ren(day_gan: str, is_day: bool = True) -> str:
    """日干 → 贵人所在支。昼贵在前, 夜贵在后。"""
    pair = _GUI_REN_TABLE.get(day_gan, ("丑", "未"))
    return pair[0] if is_day else pair[1]


# ═══════════════════════════════════════════════════════════════
# 2. 天地盘构建
# ═══════════════════════════════════════════════════════════════
def _build_cosmic_board(hour_branch: str, month_general: str) -> dict:
    """构建天地盘。

    地盘: 固定 12 宫 (子丑寅卯辰巳午未申酉戌亥)
    天盘: 月将 + 占时 → 月将加在地盘占时宫上, 顺排十二将
    """
    # 地盘固定
    earth_board = {i: dz for i, dz in enumerate(DZ)}  # 0=子, 1=丑, ...

    # 天盘: 月将从占时宫开始顺排
    general_idx = DZ.index(month_general)  # 月将是哪个地支
    hour_idx = DZ.index(hour_branch)       # 占时是哪个地支

    # 天盘[i] = DZ[(general_idx - hour_idx + i) % 12]
    heaven_board = {}
    for i in range(12):
        heaven_board[i] = DZ[(general_idx - hour_idx + i) % 12]

    return {
        "earth_board": earth_board,
        "heaven_board": heaven_board,
        "month_general": month_general,
        "month_general_name": _MONTH_GENERAL_NAMES.get(month_general, "?"),
        "hour_branch": hour_branch,
    }


# ═══════════════════════════════════════════════════════════════
# 3. 四课 (4 Lessons)
# ═══════════════════════════════════════════════════════════════
def _build_four_lessons(day_gan: str, day_zhi: str, heaven_board: dict, earth_board: dict) -> dict:
    """从日干支 + 天地盘构建四课。

    第一课: 日干寄宫 → 天盘支 → 地盘支
    第二课: 地盘支 → 天盘支 → 地盘支
    第三课: 日支 → 天盘支 → 地盘支
    第四课: 地盘支 → 天盘支 → 地盘支

    天干寄宫: 甲寄寅, 乙寄辰, 丙戊寄巳, 丁己寄未, 庚寄申, 辛寄戌, 壬寄亥, 癸寄丑
    """
    gan_ji_gong = {"甲": "寅", "乙": "辰", "丙": "巳", "丁": "未", "戊": "巳",
                   "己": "未", "庚": "申", "辛": "戌", "壬": "亥", "癸": "丑"}

    # 第一课
    gan_gong = gan_ji_gong.get(day_gan, "寅")  # 日干寄宫
    gan_gong_idx = DZ.index(gan_gong)
    tian1 = heaven_board[gan_gong_idx]  # 天盘支
    tian1_idx = DZ.index(tian1)
    di1 = earth_board[tian1_idx]  # 下神

    # 第二课 (第一课的下神继续)
    di1_idx = DZ.index(di1)
    tian2 = heaven_board[di1_idx]
    tian2_idx = DZ.index(tian2)
    di2 = earth_board[tian2_idx]

    # 第三课 (日支)
    zhi_idx = DZ.index(day_zhi)
    tian3 = heaven_board[zhi_idx]
    tian3_idx = DZ.index(tian3)
    di3 = earth_board[tian3_idx]

    # 第四课
    di3_idx = DZ.index(di3)
    tian4 = heaven_board[di3_idx]
    tian4_idx = DZ.index(tian4)
    di4 = earth_board[tian4_idx]

    return {
        "lessons": [
            {"idx": 1, "upper": gan_gong, "lower": tian1, "upper_label": f"日干{day_gan}寄{gan_gong}", "lower_label": f"天盘{tian1}"},
            {"idx": 2, "upper": tian1, "lower": di1, "upper_label": "上神", "lower_label": f"地盘{di1}"},
            {"idx": 3, "upper": day_zhi, "lower": tian3, "upper_label": f"日支{day_zhi}", "lower_label": f"天盘{tian3}"},
            {"idx": 4, "upper": tian3, "lower": di3, "upper_label": "上神", "lower_label": f"地盘{di3}"},
        ],
        "all_upper": [gan_gong, tian1, day_zhi, tian3],
        "all_lower": [tian1, di1, tian3, di3],
        "day_gan": day_gan,
        "day_zhi": day_zhi,
    }


# ═══════════════════════════════════════════════════════════════
# 4.0 课式判定 (Pattern Detection, Phase 3)
# ═══════════════════════════════════════════════════════════════
# 吉凶分类:
# - auspicious: 贼克(下克上, 客来克我, 事速成) / 比用(用神比和, 大事可成)
# - inauspicious: 返吟(来去反复) / 伏吟(事不动) / 涉害(下贼上, 主忧)
# - neutral: 遥克(隔位, 难成) / 昴星(事有阻) / 别责(事须另谋) / 八专(刚断)

_PATTERNS = {
    "贼克": "下贼上为祸轻, 上克下为祸重。课体明则事速可成。",
    "比用": "多课同克, 取与日干比和之课上神。事以比和成。",
    "涉害": "多课同克, 涉地盘归家最深者为用, 涉深则灾重。",
    "遥克": "四课无克, 遥克日干者用之, 隔位难得, 事多阻碍。",
    "昴星": "四课无克, 取从魁(酉)发用, 虎视眈眈, 事有阴私。",
    "伏吟": "三传皆临地盘本位, 天盘地支同位, 事不举, 人不动。",
    "返吟": "三传皆冲地盘, 客来反复, 谋事难成。",
    "别责": "八专课, 干支同位, 取日干寄宫上神为初传, 事须别图。",
    "八专": "干支同课无克, 五行归一, 事专断。",
}

_PATTERN_POLARITY = {
    "贼克": "auspicious",  # 课体明, 但用神需审
    "比用": "auspicious",  # 比和成
    "涉害": "inauspicious",  # 涉深则灾
    "遥克": "neutral",
    "昴星": "inauspicious",  # 虎视眈眈
    "伏吟": "inauspicious",  # 事不动
    "返吟": "inauspicious",  # 来去反复
    "别责": "neutral",  # 另谋
    "八专": "neutral",  # 刚断
    "三光": "auspicious",
    "三阳": "auspicious",
    "三阴": "inauspicious",
    "三阳": "auspicious",
    "稼穑": "neutral",
}


def _judge_pattern(
    san_chuan: dict,
    si_ke: dict,
    day_gan: str,
    day_zhi: str,
    cosmic_board: dict,
) -> dict:
    """判定课式 (Pattern Detection, 9 宗门简化)。

    优先级: 伏吟/返吟 > 贼克 > 比用 > 涉害 > 遥克 > 昴星 > 别责/八专
    """
    chu = san_chuan.get("chu_chuan", "")
    zhong = san_chuan.get("zhong_chuan", "")
    mo = san_chuan.get("mo_chuan", "")

    # 1. 伏吟: 三传 = 地盘 (天盘与地盘同)
    earth = cosmic_board.get("earth_board", {})
    heaven = cosmic_board.get("heaven_board", {})
    if chu and zhong and mo:
        # 伏吟: chu = earth[chu_idx]  (即该地支的"地盘"位置)
        chu_idx = DZ.index(chu) if chu in DZ else -1
        if chu_idx >= 0 and earth.get(chu_idx) == chu and zhong == chu and mo == chu:
            return {"name": "伏吟", "explanation": _PATTERNS["伏吟"],
                    "type": _PATTERN_POLARITY["伏吟"], "method": "伏吟法"}

    # 2. 返吟: 三传 = 地盘对冲
    if chu and zhong and mo and all(z in DZ for z in (chu, zhong, mo)):
        chu_chong = DZ[(DZ.index(chu) + 6) % 12]
        zhong_chong = DZ[(DZ.index(zhong) + 6) % 12]
        mo_chong = DZ[(DZ.index(mo) + 6) % 12]
        if chu_chong == chu and zhong_chong == chu and mo_chong == chu:
            # 简单判断: 三传都冲自身
            if all(DZ[(DZ.index(z) + 6) % 12] in DZ for z in (chu, zhong, mo)):
                return {"name": "返吟", "explanation": _PATTERNS["返吟"],
                        "type": _PATTERN_POLARITY["返吟"], "method": "返吟法"}

    # 3. 八专: 日干与日支同五行且同课 (如 壬子 癸丑)
    gan_wx = TG_WX.get(day_gan, "")
    zhi_wx = DZ_WX.get(day_zhi, "")
    if gan_wx == zhi_wx and day_gan in ("壬", "癸") and day_zhi in ("子", "丑"):
        return {"name": "八专", "explanation": _PATTERNS["八专"],
                "type": _PATTERN_POLARITY["八专"], "method": "八专法"}

    # 4. 别责: 日干寄宫与日支同支
    gan_ji_gong = {"甲": "寅", "乙": "辰", "丙": "巳", "丁": "未", "戊": "巳",
                   "己": "未", "庚": "申", "辛": "戌", "壬": "亥", "癸": "丑"}
    if gan_ji_gong.get(day_gan) == day_zhi:
        return {"name": "别责", "explanation": _PATTERNS["别责"],
                "type": _PATTERN_POLARITY["别责"], "method": "别责法"}

    # 5. 贼克 / 比用 / 涉害: 看四课克关系 (san_chuan.method 已被 _derive_three_transmissions 判定)
    method = san_chuan.get("method", "unknown")
    if "贼克" in method:
        return {"name": "贼克", "explanation": _PATTERNS["贼克"],
                "type": _PATTERN_POLARITY["贼克"], "method": "贼克法"}
    if "比用" in method:
        return {"name": "比用", "explanation": _PATTERNS["比用"],
                "type": _PATTERN_POLARITY["比用"], "method": "比用法"}
    if "涉害" in method:
        return {"name": "涉害", "explanation": _PATTERNS["涉害"],
                "type": _PATTERN_POLARITY["涉害"], "method": "涉害法"}

    # 6. 遥克 / 昴星
    if "遥克" in method:
        # 昴星优先: 若初传 = 酉
        if chu == "酉":
            return {"name": "昴星", "explanation": _PATTERNS["昴星"],
                    "type": _PATTERN_POLARITY["昴星"], "method": "昴星法"}
        return {"name": "遥克", "explanation": _PATTERNS["遥克"],
                "type": _PATTERN_POLARITY["遥克"], "method": "遥克法"}

    # 7. 兜底
    return {"name": "未明", "explanation": "课式未能判定 (简化九宗门法)",
            "type": "neutral", "method": method}


# ═══════════════════════════════════════════════════════════════
# 4. 三传 (3 Transmissions) — 九宗门简化版
# ═══════════════════════════════════════════════════════════════
def _derive_three_transmissions(lessons_data: dict) -> dict:
    """从四课推导三传(初传、中传、末传)。

    简化实现支持最常见的几种课式:
    - 贼克 (下克上/上克下)
    - 比用
    - 涉害
    - 遥克
    - 伏吟/返吟
    """
    lessons = lessons_data["lessons"]
    all_upper = lessons_data["all_upper"]
    all_lower = lessons_data["all_lower"]

    # 检查克的关系
    overcomes = []  # (lesson_idx, type)  type="下克上" or "上克下"
    for i, (up, lo) in enumerate(zip(all_upper, all_lower)):
        up_wx = DZ_WX.get(up, "")
        lo_wx = DZ_WX.get(lo, "")
        if _WX_OVERCOME.get(lo_wx) == up_wx:
            overcomes.append((i, "下克上"))
        elif _WX_OVERCOME.get(up_wx) == lo_wx:
            overcomes.append((i, "上克下"))

    transmission_method = "unknown"
    chu_chuan = zhong_chuan = mo_chuan = None

    if overcomes:
        if len(overcomes) == 1:
            # 仅一课有克 → 贼克法
            transmission_method = "贼克法"
            lesson_idx = overcomes[0][0]
            chu_chuan = all_upper[lesson_idx]
        else:
            # 多课有克 → 比用法: 取与日干五行相同的上神
            day_gan = lessons_data["day_gan"]
            day_gan_wx = TG_WX.get(day_gan, "")
            matched = [(i, all_upper[i]) for i, _ in overcomes
                       if DZ_WX.get(all_upper[i], "") == day_gan_wx]
            if matched:
                transmission_method = "比用法"
                lesson_idx, chu_chuan = matched[0]
            else:
                # 涉害法: 取地盘克方最多(涉害最深)者
                # 简化实现: 统计各地支在overcomes中出现的次数, 最多的为初传
                from collections import Counter
                zhi_counts = Counter()
                for i, kt in overcomes:
                    # 下克上: lo克up → 初传取lo(地盘); 上克下: 初传取up
                    if kt == "下克上":
                        zhi_counts[all_lower[i]] += 1
                    else:
                        zhi_counts[all_upper[i]] += 1
                chu_chuan = zhi_counts.most_common(1)[0][0]
                transmission_method = "涉害法"
    else:
        # 无克 → 遥克法 (简化: 取日干寄宫上神)
        transmission_method = "遥克法"
        gan_ji_gong = {"甲": "寅", "乙": "辰", "丙": "巳", "丁": "未", "戊": "巳",
                       "己": "未", "庚": "申", "辛": "戌", "壬": "亥", "癸": "丑"}
        gan_ji = gan_ji_gong.get(lessons_data["day_gan"], "寅")
        chu_chuan = gan_ji  # 遥克简化: 初传=日干寄宫

    # 中传和末传: 从初传在天盘上的位置开始, 依次取下一宫的天盘支
    chu_idx = DZ.index(chu_chuan) if chu_chuan else 0
    zhong_chuan = DZ[(chu_idx + 1) % 12]
    mo_chuan = DZ[(chu_idx + 2) % 12]

    # 检查是否有重复 (伏吟/返吟特征)
    has_fuyin = (chu_chuan == zhong_chuan == mo_chuan)

    return {
        "method": transmission_method,
        "chu_chuan": chu_chuan,  # 初传
        "zhong_chuan": zhong_chuan,  # 中传
        "mo_chuan": mo_chuan,  # 末传
        "chu_wx": DZ_WX.get(chu_chuan, "?"),
        "zhong_wx": DZ_WX.get(zhong_chuan, "?"),
        "mo_wx": DZ_WX.get(mo_chuan, "?"),
        "has_fuyin": has_fuyin,
    }


# ═══════════════════════════════════════════════════════════════
# 5. 十二天将排布
# ═══════════════════════════════════════════════════════════════
def _arrange_generals(gui_ren_zhi: str, day_gan: str, is_day: bool,
                      heaven_board: dict) -> list[dict]:
    """十二天将的排布: 贵人所在 → 顺/逆排。

    贵人顺逆规则: 贵人所在支若在亥~辰(子丑寅卯辰巳的前半),则顺排;若在巳~戌,则逆排。
    简化: 用地支序号判断。
    """
    gui_idx = DZ.index(gui_ren_zhi)
    # 贵人在亥子丑寅卯辰 → 顺排; 在巳午未申酉戌 → 逆排
    shun_pai = gui_idx in (0, 1, 2, 3, 4, 5, 6)  # 子丑寅卯辰巳午 → 顺

    generals = []
    for i in range(12):
        if shun_pai:
            tian_idx = (gui_idx - i) % 12  # 贵人起, 顺排: 贵人→腾蛇→朱雀...
        else:
            tian_idx = (gui_idx + i) % 12  # 贵人起, 逆排
        tian_zhi = heaven_board[tian_idx]
        generals.append({
            "general": _GENERALS[i],
            "general_wx": _GENERAL_WX[_GENERALS[i]],
            "general_meaning": _GENERAL_MEANING[_GENERALS[i]],
            "tian_pan_zhi": tian_zhi,
            "zhi_wx": DZ_WX.get(tian_zhi, "?"),
            "position": DZ[tian_idx],
        })

    return generals


# ═══════════════════════════════════════════════════════════════
# 6. 旬空计算
# ═══════════════════════════════════════════════════════════════
def _xun_kong(day_gan: str, day_zhi: str) -> str:
    """日干支 → 旬空(哪两个地支空亡)。

    六甲旬: 甲子旬戌亥空, 甲戌旬申酉空, 甲申旬午未空, 甲午旬辰巳空,
            甲辰旬寅卯空, 甲寅旬子丑空。
    """
    kong_map = {"子": ("戌", "亥"), "戌": ("申", "酉"), "申": ("午", "未"),
                "午": ("辰", "巳"), "辰": ("寅", "卯"), "寅": ("子", "丑")}

    # 构建 60 干支表
    ganzhi_60 = [TG[i % 10] + DZ[i % 12] for i in range(60)]

    day_ganzhi = day_gan + day_zhi
    day_60_idx = ganzhi_60.index(day_ganzhi) if day_ganzhi in ganzhi_60 else 0

    # 找所在旬首(甲日)
    xun_start_idx = (day_60_idx // 10) * 10
    xun_jia_zhi = ganzhi_60[xun_start_idx][1]  # 甲X的X
    kong1, kong2 = kong_map.get(xun_jia_zhi, ("?", "?"))
    return f"{kong1}{kong2}"


# ═══════════════════════════════════════════════════════════════
# 7. 主排盘函数
# ═══════════════════════════════════════════════════════════════
def compute(b: Birth) -> ChartResult:
    """大六壬排盘。

    输入: birth (用于取年月日时)
    输出: 天盘、地盘、四课、三传、十二天将、旬空
    """
    now = datetime(b.year, b.month, b.day, b.hour, b.minute)

    # 1. 占时 (divination hour)
    hour_branch = _get_hour_branch(now.hour)

    # 2. 月将 (month general)
    month_general = _get_month_general(now.month, now.day)

    # 3. 天地盘
    board = _build_cosmic_board(hour_branch, month_general)

    # 4. 日干支 — 通过 lunar-python 获取日柱
    try:
        from lunar_python import Solar
        sol = Solar.fromYmdHms(b.year, b.month, b.day, b.hour, b.minute, 0)
        lun = sol.getLunar()
        day_ganzhi = lun.getDayInGanZhi()
        day_gan = day_ganzhi[0] if len(day_ganzhi) >= 1 else "甲"
        day_zhi = day_ganzhi[1] if len(day_ganzhi) >= 2 else "子"
    except Exception:
        # fallback: 基于日期简化推算
        day_gan = TG[(b.year + b.month + b.day) % 10]
        day_zhi = DZ[(b.year + b.month + b.day) % 12]

    # 5. 四课
    four_lessons = _build_four_lessons(day_gan, day_zhi, board["heaven_board"], board["earth_board"])

    # 6. 三传
    three_trans = _derive_three_transmissions(four_lessons)

    # 7. 贵人 / 十二天将
    is_day = 6 <= now.hour < 18
    gui_ren_zhi = _get_gui_ren(day_gan, is_day)
    generals = _arrange_generals(gui_ren_zhi, day_gan, is_day, board["heaven_board"])

    # 8. 旬空
    xun_kong_str = _xun_kong(day_gan, day_zhi)

    # 9. 高阶课式检测 (P2-9: 查表, 不堆 if-elif)
    try:
        from ..data.liuren_patterns import detect_patterns as _detect_hl_patterns
        cosmic_data = {
            "gui_ren_zhi": gui_ren_zhi,
            "hour_branch": hour_branch,
            "month_general": month_general,
        }
        hl_patterns = _detect_hl_patterns(day_gan, day_zhi, three_trans, four_lessons, cosmic_data)
    except Exception:
        hl_patterns = []

    # 10. 神煞落宫断语 (P3-2: 查表)
    try:
        from ..data.liuren_shen_sha import get_shen_sha_judgments
        shen_sha_judgments = get_shen_sha_judgments(generals)
    except Exception:
        shen_sha_judgments = []

    # 构建解读提示
    reading_hints = {
        "overall": _build_overall_hint(board, four_lessons, three_trans, day_gan),
    }

    return ChartResult(
        method="liuren",
        school="east",
        engine="self+liuren-board+four-lessons+three-transmissions",
        normalized={"elements": _count_liuren_elements(day_gan, day_zhi, three_trans), "timeline": []},
        raw={
            "computed_at": date.today().isoformat(),
            "divination_time": {
                "datetime": now.strftime("%Y-%m-%d %H:%M"),
                "hour_branch": hour_branch,
                "month_general": month_general,
                "month_general_name": _MONTH_GENERAL_NAMES.get(month_general, "?"),
                "is_day": is_day,
            },
            "day_gan": day_gan,
            "day_zhi": day_zhi,
            "day_ganzhi": day_gan + day_zhi,
            "cosmic_board": {
                "sky_pan": {f"宫{i}({DZ[i]})": board["heaven_board"][i] for i in range(12)},
                "earth_pan": {f"宫{i}({DZ[i]})": board["earth_board"][i] for i in range(12)},
            },
            "four_lessons": four_lessons["lessons"],
            "three_transmissions": three_trans,
            "pattern": _judge_pattern(three_trans, four_lessons, day_gan, day_zhi, board),
            "liuren_patterns": hl_patterns,        # P2-9: 高阶课式 (三光/铸印/斫轮等)
            "shen_sha_judgments": shen_sha_judgments,  # P3-2: 十二神煞落宫断语
            "twelve_generals": generals,
            "gui_ren_zhi": gui_ren_zhi,
            "xun_kong": xun_kong_str,
            "reading_hints": reading_hints,
            "rule_version": "v1",
            "calculation_basis": {
                "method": "da_liu_ren",
                "system": "天地盘 + 四课三传 + 十二天将",
                "school": "三式之首",
                "rule_version": "v1",
                "limits": [
                    "三传推导使用简化九宗门法, 未实现全部课式变体",
                    "日干支来自八字排盘或简化推算",
                    "遁干、神煞体系待完善",
                    "长生十二宫、禄马等高级特性未展开",
                ],
            },
        },
    )


def _count_liuren_elements(day_gan: str, day_zhi: str, three_trans: dict) -> dict:
    """从日干支和三传统计五行分布。"""
    elem = {"metal": 0, "wood": 0, "water": 0, "fire": 0, "earth": 0}
    wx_key = {"金": "metal", "木": "wood", "水": "water", "火": "fire", "土": "earth"}
    # 日干五行
    gan_wx = TG_WX.get(day_gan, "")
    if gan_wx in wx_key:
        elem[wx_key[gan_wx]] += 1
    # 日支五行
    zhi_wx = DZ_WX.get(day_zhi, "")
    if zhi_wx in wx_key:
        elem[wx_key[zhi_wx]] += 1
    # 三传五行
    for key in ("chu_wx", "zhong_wx", "mo_wx"):
        wx = three_trans.get(key, "")
        if wx in wx_key:
            elem[wx_key[wx]] += 1
    return elem


def _build_overall_hint(board: dict, four_lessons: dict,
                        three_trans: dict, day_gan: str) -> str:
    """生成简单的课式总结。"""
    parts = []
    parts.append(f"月将{board['month_general_name']}({board['month_general']})加时{board['hour_branch']}")
    parts.append(f"日干{day_gan}")
    parts.append(f"课式: {three_trans['method']}")
    parts.append(f"三传: {three_trans['chu_chuan']}→{three_trans['zhong_chuan']}→{three_trans['mo_chuan']}")
    return "; ".join(parts)
