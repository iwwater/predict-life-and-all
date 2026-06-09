"""Mei Hua Yi Shu with time, number, and external-omen modes."""
from ..contracts import Birth, ChartResult

TRIGRAMS = {
    1: ("乾", (1, 1, 1), "金"),
    2: ("兑", (1, 1, 0), "金"),
    3: ("离", (1, 0, 1), "火"),
    4: ("震", (1, 0, 0), "木"),
    5: ("巽", (0, 1, 1), "木"),
    6: ("坎", (0, 1, 0), "水"),
    7: ("艮", (0, 0, 1), "土"),
    8: ("坤", (0, 0, 0), "土"),
}
SHENG = {("木", "火"), ("火", "土"), ("土", "金"), ("金", "水"), ("水", "木")}
KE = {("木", "土"), ("土", "水"), ("水", "火"), ("火", "金"), ("金", "木")}

TRIGRAM_TABLE = {
    "乾": {"binary": [1, 1, 1], "wuxing": "金", "nature": "天/健"},
    "兑": {"binary": [1, 1, 0], "wuxing": "金", "nature": "泽/悦"},
    "离": {"binary": [1, 0, 1], "wuxing": "火", "nature": "火/明"},
    "震": {"binary": [1, 0, 0], "wuxing": "木", "nature": "雷/动"},
    "巽": {"binary": [0, 1, 1], "wuxing": "木", "nature": "风/入"},
    "坎": {"binary": [0, 1, 0], "wuxing": "水", "nature": "水/陷"},
    "艮": {"binary": [0, 0, 1], "wuxing": "土", "nature": "山/止"},
    "坤": {"binary": [0, 0, 0], "wuxing": "土", "nature": "地/顺"},
}


def _n(n: int, mod: int) -> int:
    return n % mod or mod


def _combine(upper_bits, lower_bits) -> list[int]:
    return list(lower_bits) + list(upper_bits)


def _trigram_from_bits(bits) -> str:
    for name, trigram in [(v[0], v[1]) for v in TRIGRAMS.values()]:
        if tuple(bits) == tuple(trigram):
            return name
    return "乾"


def _hu_gua(lines: list[int]) -> str:
    lower = lines[1:4]
    upper = lines[2:5]
    return _trigram_from_bits(upper) + _trigram_from_bits(lower)


def _relation(ti_wx: str, yong_wx: str) -> str:
    if ti_wx == yong_wx:
        return "比和"
    if (ti_wx, yong_wx) in SHENG:
        return "体生用"
    if (yong_wx, ti_wx) in SHENG:
        return "用生体"
    if (ti_wx, yong_wx) in KE:
        return "体克用"
    if (yong_wx, ti_wx) in KE:
        return "用克体"
    return "平"


def _numbers_for_mode(b: Birth) -> tuple[int, int, int, str]:
    mode = b.mode or "time_qigua"
    if mode == "number_qigua":
        base = abs(int(b.seed if b.seed is not None else sum(ord(c) for c in (b.question or "")) or 1))
        return _n(base, 8), _n(base // 8 + b.day, 8), _n(base + b.month + b.hour, 6), "number_qigua"
    if mode == "external_omen":
        base = sum(ord(c) for c in (b.question or "")) or (b.year + b.month + b.day)
        return _n(base, 8), _n(base + b.hour, 8), _n(base + b.minute, 6), "external_omen"
    # 时辰地支序数: 子=1, 丑=2, ... 亥=12
    hour_branch_num = ((b.hour + 1) // 2) % 12 or 12  # 1-12
    # 年地支数: 梅花易数以地支序数为准 (子=1...亥=12)
    year_branch_num = (b.year % 12) or 12  # 年地支序数 1-12
    return (_n(b.month + b.day + hour_branch_num, 8),
            _n(year_branch_num + b.month + b.day + hour_branch_num, 8),
            _n(b.month + b.day + hour_branch_num, 6),
            "time_qigua")


def compute(b: Birth) -> ChartResult:
    upper_n, lower_n, dong, actual_mode = _numbers_for_mode(b)
    upper_name, upper_bits, upper_wx = TRIGRAMS[upper_n]
    lower_name, lower_bits, lower_wx = TRIGRAMS[lower_n]
    zhu_lines = _combine(upper_bits, lower_bits)
    bian_lines = list(zhu_lines)
    bian_lines[dong - 1] = 1 - bian_lines[dong - 1]
    bian_name = _trigram_from_bits(bian_lines[3:]) + _trigram_from_bits(bian_lines[:3])
    zhu_name = upper_name + lower_name
    hu_name = _hu_gua(zhu_lines)

    if dong <= 3:
        ti_name, ti_wx = upper_name, upper_wx
        yong_name, yong_wx = lower_name, lower_wx
    else:
        ti_name, ti_wx = lower_name, lower_wx
        yong_name, yong_wx = upper_name, upper_wx
    relation = _relation(ti_wx, yong_wx)

    return ChartResult(
        method="meihua",
        school="east",
        engine="self+time-number-omen",
        normalized={"elements": {"metal": 1 if ti_wx == "金" or yong_wx == "金" else 0,
                              "wood": 1 if ti_wx == "木" or yong_wx == "木" else 0,
                              "water": 1 if ti_wx == "水" or yong_wx == "水" else 0,
                              "fire": 1 if ti_wx == "火" or yong_wx == "火" else 0,
                              "earth": 1 if ti_wx == "土" or yong_wx == "土" else 0},
                   "timeline": []},
        raw={
            "mode": actual_mode,
            "subject": b.subject or "decision",
            "rule_version": "v1",
            "zhu_gua": zhu_name,
            "hu_gua": hu_name,
            "bian_gua": bian_name,
            "ti_gua": ti_name,
            "ti_wuxing": ti_wx,
            "yong_gua": yong_name,
            "yong_wuxing": yong_wx,
            "dong_yao": dong,
            "duan": f"体卦 {ti_name}{ti_wx}，用卦 {yong_name}{yong_wx}，关系为 {relation}。",
            "numbers": {"upper": upper_n, "lower": lower_n, "moving": dong},
            "trigram_table": TRIGRAM_TABLE,
            "calculation_basis": {
                "method": "meihua",
                "mode": actual_mode,
                "subject": b.subject or "decision",
                "rule_version": "v1",
                "input_source": "birth (year/month/day/hour/minute) + optional seed/question",
                "rule": "上卦、下卦、动爻按所选起卦模式取数；动爻所在卦为用，另一卦为体。互卦 = 主卦 2-4 爻/3-5 爻。",
                "limits": [
                    "本实现不接互卦变爻、金口诀、纳甲, 仅到体用关系与生克",
                    "动爻来源 priority: 手动起卦 > 数字起卦 > 外应起卦 > 时间起卦",
                    "64 卦全名 = 上下卦组合 (本表 8 卦), 互卦由 2-4 爻/3-5 爻组合",
                ],
            },
        },
    )
