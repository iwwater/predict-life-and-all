"""《易经》核心：八卦、六十四卦（文王卦序）、京房纳甲、八宫世应。
文献：《周易》本经卦名、《京氏易传》（西汉·京房）纳甲与八宫、纳甲歌诀。
六爻、梅花易数共用此模块。"""

# 八卦：三爻自下而上的阴阳（阳=1 阴=0）-> 卦名/五行
TRIGRAM = {
    (1, 1, 1): ("乾", "金"), (1, 1, 0): ("兑", "金"), (1, 0, 1): ("离", "火"),
    (1, 0, 0): ("震", "木"), (0, 1, 1): ("巽", "木"), (0, 1, 0): ("坎", "水"),
    (0, 0, 1): ("艮", "土"), (0, 0, 0): ("坤", "土"),
}
_NAME2BITS = {v[0]: k for k, v in TRIGRAM.items()}

# 文王六十四卦表：行=上卦 列=下卦，顺序 乾兑离震巽坎艮坤
_ORDER = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]
_TABLE = {
    "乾": ["乾", "履", "同人", "无妄", "姤", "讼", "遯", "否"],
    "兑": ["夬", "兑", "革", "随", "大过", "困", "咸", "萃"],
    "离": ["大有", "睽", "离", "噬嗑", "鼎", "未济", "旅", "晋"],
    "震": ["大壮", "归妹", "丰", "震", "恒", "解", "小过", "豫"],
    "巽": ["小畜", "中孚", "家人", "益", "巽", "涣", "渐", "观"],
    "坎": ["需", "节", "既济", "屯", "井", "坎", "蹇", "比"],
    "艮": ["大畜", "损", "贲", "颐", "蛊", "蒙", "艮", "剥"],
    "坤": ["泰", "临", "明夷", "复", "升", "师", "谦", "坤"],
}

# 京房纳甲——八卦纳地支（内卦下三爻 / 外卦上三爻），自初爻起
_NAZHI = {
    "乾": ["子", "寅", "辰", "午", "申", "戌"],
    "坎": ["寅", "辰", "午", "申", "戌", "子"],
    "艮": ["辰", "午", "申", "戌", "子", "寅"],
    "震": ["子", "寅", "辰", "午", "申", "戌"],
    "巽": ["丑", "亥", "酉", "未", "巳", "卯"],
    "离": ["卯", "丑", "亥", "酉", "未", "巳"],
    "坤": ["未", "巳", "卯", "丑", "亥", "酉"],
    "兑": ["巳", "卯", "丑", "亥", "酉", "未"],
}
_ZHI_WUXING = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
               "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}

# 八宫（京房）——每宫八卦次序：本宫/一世.../归魂；世爻位置随之 6,1,2,3,4,5(游魂4),归魂3
_GONG_WUXING = {"乾": "金", "坎": "水", "艮": "土", "震": "木",
                "巽": "木", "离": "火", "坤": "土", "兑": "金"}


def hexagram_name(lines: list[int]) -> dict:
    """lines: 6 个 0/1，自初爻(下)到上爻。返回卦名+上下卦。"""
    lower = TRIGRAM[tuple(lines[0:3])][0]
    upper = TRIGRAM[tuple(lines[3:6])][0]
    name = _TABLE[upper][_ORDER.index(lower)]
    return {"name": name, "upper": upper, "lower": lower}


def liuqin(gong_wx: str, zhi: str) -> str:
    """六亲：以卦宫五行为'我'，论与爻支五行的生克。"""
    me = gong_wx
    other = _ZHI_WUXING[zhi]
    sheng = {"金": "水", "水": "木", "木": "火", "火": "土", "土": "金"}  # 我生
    ke = {"金": "木", "木": "土", "土": "水", "水": "火", "火": "金"}      # 我克
    if other == me:
        return "兄弟"
    if sheng[me] == other:
        return "子孙"
    if ke[me] == other:
        return "妻财"
    if sheng[other] == me:
        return "父母"
    return "官鬼"  # 克我


def naijia(lines: list[int]) -> list[dict]:
    """给六爻装地支+五行+六亲。"""
    lower = TRIGRAM[tuple(lines[0:3])][0]
    upper = TRIGRAM[tuple(lines[3:6])][0]
    # 本宫五行：以京房八宫之「卦宫」定（曾误用上卦——游魂/归魂等卦六亲会全错）
    name = hexagram_name(lines)["name"]
    gwx = PALACE_INDEX[name]["宫五行"] if name in PALACE_INDEX else _GONG_WUXING[upper]
    zhi_lower = _NAZHI[lower][0:3]   # 内卦取前三
    zhi_upper = _NAZHI[upper][3:6]   # 外卦取后三
    zhis = zhi_lower + zhi_upper
    out = []
    for i, z in enumerate(zhis):
        out.append({"爻": i + 1, "阴阳": "阳" if lines[i] else "阴",
                    "地支": z, "五行": _ZHI_WUXING[z],
                    "六亲": liuqin(gwx, z)})
    return out


# ===== 京房八宫·世应 =====
# 自本宫纯卦的变爻规律：本宫{}世6, 一世{1}世1 ... 五世{1-5}世5, 游魂{1,2,3,5}世4, 归魂{5}世3
_PALACE_PATTERN = [
    (frozenset(), 6), (frozenset({1}), 1), (frozenset({1, 2}), 2),
    (frozenset({1, 2, 3}), 3), (frozenset({1, 2, 3, 4}), 4),
    (frozenset({1, 2, 3, 4, 5}), 5), (frozenset({1, 2, 3, 5}), 4),
    (frozenset({5}), 3),
]
_PURE = {"乾": [1, 1, 1, 1, 1, 1], "兑": [1, 1, 0, 1, 1, 0], "离": [1, 0, 1, 1, 0, 1],
         "震": [1, 0, 0, 1, 0, 0], "巽": [0, 1, 1, 0, 1, 1], "坎": [0, 1, 0, 0, 1, 0],
         "艮": [0, 0, 1, 0, 0, 1], "坤": [0, 0, 0, 0, 0, 0]}

def _build_palace_index():
    idx = {}
    for gong, pure in _PURE.items():
        for changed, shi in _PALACE_PATTERN:
            lines = [(1 - pure[i]) if (i + 1) in changed else pure[i] for i in range(6)]
            name = hexagram_name(lines)["name"]
            idx[name] = {"宫": gong, "宫五行": _GONG_WUXING[gong], "世": shi,
                         "应": (shi + 3 - 1) % 6 + 1}
    return idx

PALACE_INDEX = _build_palace_index()


def palace_shiying(name: str) -> dict:
    return PALACE_INDEX.get(name, {"宫": "?", "世": None, "应": None})
