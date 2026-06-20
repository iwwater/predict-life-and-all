"""中文姓名学 · 三才五格 (San Cai Wu Ge) — 康熙字典笔画数。

文献：
  - 《姓名学大辞典》(现代 · 熊崎氏流派)
  - 《康熙字典》笔画 (清)

五格定义：
  天格 (tiange)  = 姓总笔画 + 1（复姓 = 姓总笔画）
  人格 (renge)   = 姓末字笔画 + 名首字笔画
  地格 (dige)    = 名总笔画 + 1（单字名）或 = 名总笔画
  外格 (waige)   = 总格 - 人格 + 1
  总格 (zongge)  = 姓 + 名 所有笔画之和

三才 (san cai) = 天格 · 人格 · 地格 对应的五行关系
  五行：金 1-2 / 木 3-4 / 水 5-6 / 火 7-8 / 土 9-0
  关系：相生 > 比和 > 相克

⚠️ 注意：
  - "1-2/3-4/5-6/7-8/9-0" 是数 1-10 按尾数映射到五行的简化方案
  - 严格流派（如熊崎氏）使用不同的尾数映射，本表采用最常见方案
"""
from __future__ import annotations

# ══════════════════════════════════════════════════════════════
# 1. 康熙字典笔画数（常用姓 + 名字）
# ══════════════════════════════════════════════════════════════

# ── 常用 100 姓氏 ──
KANGXI_STROKES_SURNAME: dict[str, int] = {
    # 1 画
    "丁": 2, "刁": 3, "卜": 2,
    # 2 画
    "丁": 2, "于": 6, "万": 15, "马": 10, "卞": 4, "尤": 4, "孔": 4,
    # 3 画
    "万": 15, "马": 10, "上官": 11, "卫": 15, "习": 11,
    # 4 画
    "王": 4, "韦": 14, "尤": 4, "尹": 4, "孔": 4, "邓": 19, "木": 4,
    "支": 4, "贝": 7, "牛": 7,
    # 5 画
    "田": 5, "白": 11, "冯": 12, "甘": 5, "古": 5, "史": 5, "石": 5,
    "司": 6, "叶": 15, "丘": 4, "包": 10, "宁": 14, "边": 27,
    # 6 画
    "刘": 15, "朱": 6, "许": 11, "孙": 10, "齐": 14, "邢": 9,
    "毕": 11, "阮": 17, "吕": 6, "华": 14, "关": 16, "伍": 6,
    "乔": 12, "庄": 13, "牟": 14, "伊": 6, "向": 6, "危": 9,
    "成": 7, "邬": 18,
    # 7 画
    "李": 7, "陈": 16, "杨": 13, "张": 11, "何": 7, "周": 8,
    "吴": 7, "徐": 10, "宋": 7, "苏": 22, "汪": 8, "沈": 16,
    "邹": 13, "邵": 12, "庞": 16, "季": 8, "茅": 11, "苟": 8,
    "苑": 11, "官": 14, "郎": 10, "贺": 12, "费": 12, "段": 9,
    # 8 画
    "林": 8, "郑": 19, "罗": 20, "范": 12, "孟": 8, "欧": 15,
    "易": 8, "郁": 29, "卓": 14, "尚": 8, "明": 8, "金": 8,
    "季": 8, "屈": 12, "苗": 11, "苟": 8,
    # 9 画
    "胡": 11, "赵": 14, "高": 10, "钟": 17, "俞": 13, "闻": 14,
    "姚": 9, "姜": 9, "侯": 9, "施": 9, "洪": 10, "宣": 9,
    "段": 9, "柏": 9, "柳": 9, "费": 12, "查": 12, "项": 12,
    # 10 画
    "徐": 10, "郭": 15, "梁": 11, "秦": 10, "袁": 10, "马": 10,
    "钱": 16, "顾": 21, "曹": 11, "唐": 10, "陶": 16, "凌": 10,
    "聂": 18, "贾": 13, "夏": 10, "浦": 11, "晏": 10, "倪": 16,
    "殷": 10, "翁": 12, "栾": 23, "席": 6,
    # 11 画
    "黄": 12, "曹": 11, "崔": 11, "萧": 19, "康": 11, "阎": 16,
    "常": 11, "麻": 11, "商": 11, "戚": 11, "梅": 11, "尉": 8,
    "盛": 12, "龚": 22, "章": 11, "梁": 11, "理": 11,
    # 12 画
    "曾": 12, "谢": 17, "彭": 12, "蒋": 16, "覃": 12, "程": 12,
    "董": 15, "舒": 17, "童": 10, "温": 12, "游": 12, "项": 12,
    "云": 12, "傅": 12, "焦": 12, "储": 14, "韩": 17, "鲁": 15,
    # 13 画
    "赖": 16, "楚": 13, "詹": 13, "蓝": 13, "雷": 13, "蒙": 16,
    "路": 13, "阙": 14, "简": 18, "廉": 13, "裘": 13,
    # 14 画
    "蔡": 17, "谭": 19, "熊": 14, "管": 14, "裴": 14, "缪": 14,
    "漆": 14, "翟": 14, "赫": 14, "榕": 14,
    # 15 画
    "潘": 16, "薛": 19, "黎": 15, "樊": 15, "颜": 18, "滕": 14,
    "墨": 15, "欧阳": 15, "慕容": 15,
    # 16 画
    "燕": 16, "霍": 16, "穆": 16, "戴": 18, "魏": 18, "钱": 16,
    "薄": 16, "融": 16,
    # 17+ 画
    "戴": 18, "鞠": 18, "魏": 18, "瞿": 18, "濮": 17,
    # 18+ 画
    "罗": 20, "谭": 19, "权": 22,
    # 复姓
    "司马": 16, "欧阳": 15, "诸葛": 30, "上官": 11, "东方": 8,
    "皇甫": 14, "尉迟": 12, "公孙": 10,
    # 注：复姓的"总和"由 KANGXI_STROKES_SURNAME 中单字笔画累加得到
    # 司(6) + 马(10) = 16, 欧(15) + 阳(17) = 32, 诸(16) + 葛(15) = 31
    # 建议补充单字笔画：
}


# ── 常用 80 名字用字 ──
KANGXI_STROKES_GIVEN: dict[str, int] = {
    "梓": 11, "宇": 6, "子": 3, "轩": 10, "涵": 12, "思": 9,
    "雨": 8, "欣": 8, "嘉": 14, "俊": 9, "志": 7, "慧": 15,
    "婷": 12, "静": 16, "雪": 11, "诗": 13, "语": 14, "乐": 15,
    "晨": 11, "阳": 17, "明": 8, "天": 4, "龙": 16, "凤": 12,
    "鹏": 19, "飞": 9, "海": 11, "林": 8, "涛": 18, "波": 9,
    "燕": 16, "红": 9, "丽": 19, "艳": 24, "君": 7, "华": 14,
    "伟": 11, "强": 11, "磊": 15, "鑫": 24, "杰": 12, "浩": 11,
    "清": 12, "润": 16, "泽": 17, "玉": 5, "玲": 10, "瑶": 15,
    "瑞": 14, "琪": 13, "颖": 16, "聪": 17, "明": 8, "昭": 9,
    "晓": 16, "晔": 14, "晗": 11, "昊": 8, "旭": 6, "辉": 15,
    "豪": 14, "雄": 12, "涛": 18, "亮": 9, "康": 11, "健": 11,
    "雯": 12, "霏": 16, "露": 21, "薇": 19, "蓉": 16, "芳": 7,
    "兰": 23, "萍": 14, "莲": 13, "娟": 10, "婷": 12, "媛": 13,
    "宁": 14, "安": 6, "平": 5, "和": 8, "顺": 12, "达": 12,
}


# ── 复合表（姓氏+名用字统一查找）──
def _build_combined_table() -> dict[str, int]:
    combined: dict[str, int] = {}
    combined.update(KANGXI_STROKES_SURNAME)
    combined.update(KANGXI_STROKES_GIVEN)
    return combined


KANGXI_STROKES_ALL = _build_combined_table()


# ══════════════════════════════════════════════════════════════
# 2. 数 → 五行 映射（数 1-10 按尾数）
# ══════════════════════════════════════════════════════════════
NUMBER_TO_WUXING: dict[int, str] = {
    1: "木", 2: "木",
    3: "火", 4: "火",
    5: "土", 6: "土",
    7: "金", 8: "金",
    9: "水", 10: "水",
}


def num_to_wuxing(n: int) -> str:
    """数字 → 五行（按尾数 1-10 → 五行）。"""
    last_digit = n % 10
    if last_digit == 0:
        return "水"  # 10 算水
    return NUMBER_TO_WUXING[last_digit]


# ══════════════════════════════════════════════════════════════
# 3. 五行关系
# ══════════════════════════════════════════════════════════════
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
OVERCOMES = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def wuxing_relationship(a: str, b: str) -> str:
    """A 对 B 的五行关系: '生'(a生b) / '被生' / '克'(a克b) / '被克' / '比和'。"""
    if a == b:
        return "比和"
    if GENERATES.get(a) == b:
        return "生"  # A 生 B
    if GENERATES.get(b) == a:
        return "被生"
    if OVERCOMES.get(a) == b:
        return "克"  # A 克 B
    if OVERCOMES.get(b) == a:
        return "被克"
    return "未知"


# ══════════════════════════════════════════════════════════════
# 4. 数理吉凶（1-81）
# ══════════════════════════════════════════════════════════════
# 1-81 数理吉凶简表（标准熊崎氏流派 + 现代综合）
SHULI_JIXIONG: dict[int, dict[str, str]] = {
    # ── 大吉 ──
    1: {"luck": "大吉", "meaning": "首领之数,出类拔萃,权威显达。"},
    3: {"luck": "大吉", "meaning": "吉祥之数,进取如意,大业成就。"},
    5: {"luck": "大吉", "meaning": "阴阳和合,福禄长寿,大业成就。"},
    7: {"luck": "吉", "meaning": "刚毅果断,权威显达,但易孤独。"},
    8: {"luck": "大吉", "meaning": "坚刚之数,意志坚定,成功发达。"},
    11: {"luck": "大吉", "meaning": "旱苗逢雨,挽回家运,亦可成功。"},
    13: {"luck": "大吉", "meaning": "智略超群,博学多艺,但易孤独。"},
    15: {"luck": "大吉", "meaning": "福寿之数,温和雅量,大业成就。"},
    16: {"luck": "大吉", "meaning": "化凶为吉之数,厚重余庆。"},
    17: {"luck": "半吉", "meaning": "刚毅之数,突破万难,权威显达。"},
    18: {"luck": "半吉", "meaning": "铁镜重磨,有志竟成。"},
    21: {"luck": "大吉", "meaning": "明月光照,独立权威,大业成就。"},
    23: {"luck": "大吉", "meaning": "旭日东升,发育期长,大业成就。"},
    24: {"luck": "大吉", "meaning": "金钱丰盈,家门余庆。"},
    25: {"luck": "半吉", "meaning": "资性英敏,温和雅量,但性刚。"},
    29: {"luck": "半吉", "meaning": "智谋兼备,欲望过盛,易遭失败。"},
    31: {"luck": "大吉", "meaning": "智勇兼备,大业成就。"},
    32: {"luck": "大吉", "meaning": "侥幸之数,常陷逆境。"},
    33: {"luck": "大吉", "meaning": "旭日升天,鸾凤相会,大业成就。"},
    35: {"luck": "大吉", "meaning": "温和平静,温恭和顺。"},
    37: {"luck": "大吉", "meaning": "独立权威,大业成就。"},
    39: {"luck": "半吉", "meaning": "富贵之数,虽多阻碍,终成大业。"},
    41: {"luck": "大吉", "meaning": "天资聪颖,德望兼备,大业成就。"},
    45: {"luck": "大吉", "meaning": "万物滋生,大业成就。"},
    47: {"luck": "大吉", "meaning": "德望兼备,大业成就。"},
    48: {"luck": "大吉", "meaning": "智谋兼备,德望兼备。"},
    52: {"luck": "大吉", "meaning": "先见之明,理想实现。"},
    57: {"luck": "半吉", "meaning": "寒雪青松,大志大业。"},
    63: {"luck": "大吉", "meaning": "万物归成,繁荣发达。"},
    65: {"luck": "大吉", "meaning": "富贵长寿,大业成就。"},
    67: {"luck": "大吉", "meaning": "财源旺发,大业成就。"},
    68: {"luck": "大吉", "meaning": "顺风扬帆,大业成就。"},
    81: {"luck": "大吉", "meaning": "万物归成,大业成就。"},

    # ── 半吉 ──
    2: {"luck": "凶", "meaning": "混沌未定,分离破败,万事挫折。"},
    4: {"luck": "凶", "meaning": "坎坷凶变,万事挫折,多灾多难。"},
    6: {"luck": "半吉", "meaning": "安稳余庆,福禄长寿。"},
    9: {"luck": "凶", "meaning": "穷困之数,吉凶参半。"},
    10: {"luck": "凶", "meaning": "万事终局,暗淡不兴。"},
    12: {"luck": "凶", "meaning": "薄弱之数,谋事难成。"},
    14: {"luck": "凶", "meaning": "沦落天涯,失意烦闷。"},
    19: {"luck": "凶", "meaning": "多难之数,成败难定。"},
    20: {"luck": "凶", "meaning": "凶星暗藏,终成废人。"},
    22: {"luck": "凶", "meaning": "秋草逢霜,忧愁病苦。"},
    26: {"luck": "凶", "meaning": "波澜起伏,凶变不断。"},
    27: {"luck": "凶", "meaning": "欲望太大,多成多败。"},
    28: {"luck": "凶", "meaning": "凶祸相离,难逃凶运。"},
    30: {"luck": "半吉", "meaning": "吉凶参半,沉浮不定。"},
    34: {"luck": "凶", "meaning": "破家之数,大凶。"},
    36: {"luck": "半吉", "meaning": "波澜重叠,沉浮万变。"},
    38: {"luck": "半吉", "meaning": "薄幸之数,成败难定。"},
    40: {"luck": "半吉", "meaning": "退安之数,谨慎保身。"},
    42: {"luck": "半吉", "meaning": "寒蝉凄风,博识多能。"},
    43: {"luck": "凶", "meaning": "散财之数,多灾多难。"},
    44: {"luck": "凶", "meaning": "愁闷之数,难成大业。"},
    46: {"luck": "凶", "meaning": "坎坷之数,多愁多病。"},
    49: {"luck": "凶", "meaning": "凶变之数,进退两难。"},
    50: {"luck": "半吉", "meaning": "成败之数,小吉。"},
    51: {"luck": "半吉", "meaning": "盛衰交加,半吉半凶。"},
    53: {"luck": "凶", "meaning": "忧愁之数,多成多败。"},
    54: {"luck": "凶", "meaning": "多难之数,石上开花。"},
    55: {"luck": "凶", "meaning": "多难之数,外祥内苦。"},
    56: {"luck": "凶", "meaning": "凶变之数,进退两难。"},
    58: {"luck": "半吉", "meaning": "晚耕之数,先难后成。"},
    59: {"luck": "凶", "meaning": "寒蝉凄风,难成大业。"},
    60: {"luck": "凶", "meaning": "无定之数,暗昧不吉。"},
    61: {"luck": "半吉", "meaning": "名利双收,谨慎保身。"},
    62: {"luck": "凶", "meaning": "衰微之数,多灾多难。"},
    64: {"luck": "凶", "meaning": "骨肉分离,多灾多难。"},
    66: {"luck": "凶", "meaning": "凶变之数,万事挫折。"},
    69: {"luck": "凶", "meaning": "动不如静,多灾多难。"},
    70: {"luck": "凶", "meaning": "残春之数,多灾多难。"},
    71: {"luck": "半吉", "meaning": "万物收成,大吉之末转吉。"},
    72: {"luck": "半吉", "meaning": "先甘后苦,小吉。"},
    73: {"luck": "半吉", "meaning": "旭日初升,小吉。"},
    74: {"luck": "凶", "meaning": "残花落叶,多灾多难。"},
    75: {"luck": "半吉", "meaning": "守安之数,小吉。"},
    76: {"luck": "凶", "meaning": "离散之数,多灾多难。"},
    77: {"luck": "半吉", "meaning": "先苦后甘,小吉。"},
    78: {"luck": "半吉", "meaning": "福祸参半,小吉。"},
    79: {"luck": "半吉", "meaning": "先难后成,小吉。"},
    80: {"luck": "凶", "meaning": "凶变之数,多灾多难。"},
}


# ══════════════════════════════════════════════════════════════
# 5. 笔画查询与 fallback
# ══════════════════════════════════════════════════════════════
def get_stroke(char: str) -> int:
    """查询单字康熙字典笔画数。

    优先查 KANGXI_STROKES_ALL,未命中时按 unicode 笔画数粗略估算 (fallback)。
    """
    if char in KANGXI_STROKES_ALL:
        return KANGXI_STROKES_ALL[char]
    # Fallback: 用 unicodedata 估算（粗略）
    return _fallback_stroke_count(char)


def _fallback_stroke_count(char: str) -> int:
    """Fallback: 当字不在表中,使用粗略笔画数估算。

    简化策略:
        - CJK 基本区 0x4E00-0x9FFF: 按码点偏移 +1 作为笔画（粗略）
        - 其他: 1 画
    """
    code = ord(char)
    if 0x4E00 <= code <= 0x9FFF:
        # 极粗略估算: 不准确,建议补表
        return ((code - 0x4E00) % 30) + 1
    return 1


# ══════════════════════════════════════════════════════════════
# 6. 三才五格计算
# ══════════════════════════════════════════════════════════════
def compute_wuge(surname: str, given_name: str) -> dict:
    """计算三才五格。

    Args:
        surname: 姓氏 (1-2 字)
        given_name: 名 (1-2 字)

    Returns:
        {
            "surname": str,
            "given_name": str,
            "tiange": {num, wuxing, luck},
            "renge":  {num, wuxing, luck},
            "dige":   {num, wuxing, luck},
            "waige":  {num, wuxing, luck},
            "zongge": {num, wuxing, luck},
            "san_cai": {tian_wx, ren_wx, di_wx, relationship},
            "overall": "吉/半吉/凶"
        }
    """
    surname_chars = list(surname)
    given_chars = list(given_name)

    if not surname_chars or not given_chars:
        return {"error": "姓或名为空"}

    # 笔画数
    surname_strokes = [get_stroke(c) for c in surname_chars]
    given_strokes = [get_stroke(c) for c in given_chars]

    # 天格
    if len(surname_chars) == 1:
        tiange_num = surname_strokes[0] + 1
    else:  # 复姓
        tiange_num = sum(surname_strokes)

    # 人格
    renge_num = surname_strokes[-1] + given_strokes[0]

    # 地格
    if len(given_chars) == 1:
        dige_num = given_strokes[0] + 1
    else:
        dige_num = sum(given_strokes)

    # 总格
    zongge_num = sum(surname_strokes) + sum(given_strokes)

    # 外格 = 总格 - 人格 + 1 (若为单字名, 外格 = 总格 - 人格 + 1 之后取绝对值)
    waige_num = abs(zongge_num - renge_num + 1) if len(given_chars) > 1 else abs(zongge_num - renge_num - 1)

    # 各格五行 + 数理吉凶
    def gr(num: int) -> dict:
        return {
            "num": num,
            "wuxing": num_to_wuxing(num),
            "luck": SHULI_JIXIONG.get(num, {}).get("luck", "?"),
            "meaning": SHULI_JIXIONG.get(num, {}).get("meaning", ""),
        }

    tiange = gr(tiange_num)
    renge = gr(renge_num)
    dige = gr(dige_num)
    waige = gr(waige_num)
    zongge = gr(zongge_num)

    # 三才 (天 → 人 → 地) 关系链
    tian_ren = wuxing_relationship(tiange["wuxing"], renge["wuxing"])
    ren_di = wuxing_relationship(renge["wuxing"], dige["wuxing"])

    # 综合判断: 天人吉 + 人地吉 = 吉; 一吉一凶 = 半吉; 都凶 = 凶
    luck_scores = {"大吉": 3, "吉": 2, "半吉": 1, "凶": 0, "?": 1}
    avg_score = (luck_scores.get(tiange["luck"], 1) +
                 luck_scores.get(renge["luck"], 1) +
                 luck_scores.get(dige["luck"], 1)) / 3
    if avg_score >= 2:
        overall = "吉"
    elif avg_score >= 1:
        overall = "半吉"
    else:
        overall = "凶"

    return {
        "surname": surname,
        "given_name": given_name,
        "tiange": tiange,
        "renge": renge,
        "dige": dige,
        "waige": waige,
        "zongge": zongge,
        "san_cai": {
            "tian_wx": tiange["wuxing"],
            "ren_wx": renge["wuxing"],
            "di_wx": dige["wuxing"],
            "tian_ren_rel": tian_ren,
            "ren_di_rel": ren_di,
        },
        "overall": overall,
    }


# ══════════════════════════════════════════════════════════════
# 7. 自检
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=== 三才五格姓名学 自检 ===\n")

    # 1. 笔画数表
    print(f"1. 姓氏笔画表: {len(KANGXI_STROKES_SURNAME)} 个常见姓")
    print(f"2. 名用字笔画表: {len(KANGXI_STROKES_GIVEN)} 个常见名用字")
    print(f"3. 组合表: {len(KANGXI_STROKES_ALL)} 字")

    # 2. 数理吉凶覆盖
    n_luck = sum(1 for v in SHULI_JIXIONG.values() if v["luck"] == "大吉")
    n_half = sum(1 for v in SHULI_JIXIONG.values() if v["luck"] == "半吉")
    n_xi = sum(1 for v in SHULI_JIXIONG.values() if v["luck"] == "凶")
    print(f"\n4. 数理吉凶: {len(SHULI_JIXIONG)} 类 → 大吉={n_luck}, 半吉={n_half}, 凶={n_xi}")

    # 3. 计算示例
    print("\n5. 三才五格示例:")
    for s, g in [("李", "梓涵"), ("王", "宇轩"), ("陈", "静"), ("张", "嘉慧"),
                  ("司马", "晓晗"), ("欧阳", "子涵")]:
        result = compute_wuge(s, g)
        if "error" not in result:
            print(f"\n   {s}{g}:")
            print(f"     天格: {result['tiange']['num']:2d} ({result['tiange']['wuxing']}, {result['tiange']['luck']})")
            print(f"     人格: {result['renge']['num']:2d} ({result['renge']['wuxing']}, {result['renge']['luck']})")
            print(f"     地格: {result['dige']['num']:2d} ({result['dige']['wuxing']}, {result['dige']['luck']})")
            print(f"     外格: {result['waige']['num']:2d} ({result['waige']['wuxing']}, {result['waige']['luck']})")
            print(f"     总格: {result['zongge']['num']:2d} ({result['zongge']['wuxing']}, {result['zongge']['luck']})")
            print(f"     三才: {result['san_cai']['tian_wx']} → {result['san_cai']['ren_wx']} → {result['san_cai']['di_wx']} (天人:{result['san_cai']['tian_ren_rel']}, 人地:{result['san_cai']['ren_di_rel']})")
            print(f"     综合: {result['overall']}")
