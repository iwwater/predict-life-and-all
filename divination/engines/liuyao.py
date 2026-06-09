"""Liu Yao with manual coin, number, and time casting modes."""
import hashlib
import random

from lunar_python import Solar

from ..contracts import Birth, ChartResult

TRIGRAM_BITS = {
    "乾": (1, 1, 1), "兑": (1, 1, 0), "离": (1, 0, 1), "震": (1, 0, 0),
    "巽": (0, 1, 1), "坎": (0, 1, 0), "艮": (0, 0, 1), "坤": (0, 0, 0),
}
HEX_BY_TRIGRAM = {
    ("乾", "乾"): "乾为天", ("坤", "坤"): "坤为地", ("坎", "震"): "水雷屯", ("艮", "坎"): "山水蒙",
    ("坎", "乾"): "水天需", ("乾", "坎"): "天水讼", ("坤", "坎"): "地水师", ("坎", "坤"): "水地比",
    ("巽", "乾"): "风天小畜", ("乾", "兑"): "天泽履", ("坤", "乾"): "地天泰", ("乾", "坤"): "天地否",
    ("乾", "离"): "天火同人", ("离", "乾"): "火天大有", ("坤", "艮"): "地山谦", ("震", "坤"): "雷地豫",
    ("兑", "震"): "泽雷随", ("艮", "巽"): "山风蛊", ("坤", "兑"): "地泽临", ("巽", "坤"): "风地观",
    ("离", "震"): "火雷噬嗑", ("艮", "离"): "山火贲", ("艮", "坤"): "山地剥", ("坤", "震"): "地雷复",
    ("乾", "震"): "天雷无妄", ("艮", "乾"): "山天大畜", ("艮", "震"): "山雷颐", ("兑", "巽"): "泽风大过",
    ("坎", "坎"): "坎为水", ("离", "离"): "离为火", ("兑", "艮"): "泽山咸", ("震", "巽"): "雷风恒",
    ("乾", "艮"): "天山遁", ("震", "乾"): "雷天大壮", ("离", "坤"): "火地晋", ("坤", "离"): "地火明夷",
    ("巽", "离"): "风火家人", ("离", "兑"): "火泽睽", ("坎", "艮"): "水山蹇", ("震", "坎"): "雷水解",
    ("艮", "兑"): "山泽损", ("巽", "震"): "风雷益", ("兑", "乾"): "泽天夬", ("乾", "巽"): "天风姤",
    ("兑", "坤"): "泽地萃", ("坤", "巽"): "地风升", ("兑", "坎"): "泽水困", ("坎", "巽"): "水风井",
    ("兑", "离"): "泽火革", ("离", "巽"): "火风鼎", ("震", "震"): "震为雷", ("艮", "艮"): "艮为山",
    ("巽", "艮"): "风山渐", ("震", "兑"): "雷泽归妹", ("震", "离"): "雷火丰", ("离", "艮"): "火山旅",
    ("巽", "巽"): "巽为风", ("兑", "兑"): "兑为泽", ("巽", "坎"): "风水涣", ("坎", "兑"): "水泽节",
    ("巽", "兑"): "风泽中孚", ("震", "艮"): "雷山小过", ("坎", "离"): "水火既济", ("离", "坎"): "火水未济",
}
NAJIA = {
    "乾": ["子水", "寅木", "辰土", "午火", "申金", "戌土"],
    "坤": ["未土", "巳火", "卯木", "丑土", "亥水", "酉金"],
    "震": ["子水", "寅木", "辰土", "午火", "申金", "戌土"],
    "巽": ["丑土", "亥水", "酉金", "未土", "巳火", "卯木"],
    "坎": ["寅木", "辰土", "午火", "申金", "戌土", "子水"],
    "离": ["卯木", "丑土", "亥水", "酉金", "未土", "巳火"],
    "艮": ["辰土", "午火", "申金", "戌土", "子水", "寅木"],
    "兑": ["巳火", "卯木", "丑土", "亥水", "酉金", "未土"],
}
LIUSHEN = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]
LIUSHEN_START = {"甲": 0, "乙": 0, "丙": 1, "丁": 1, "戊": 2, "己": 2, "庚": 3, "辛": 3, "壬": 4, "癸": 4}
SUBJECT_USING_GOD = {
    "career": "官鬼",
    "wealth": "妻财",
    "relationship": "妻财/官鬼",
    "lost_item": "父母/妻财",
    "decision": "世应与动爻",
}


def _trigram_from_lines(lines3: list[int]) -> str:
    for name, bits in TRIGRAM_BITS.items():
        if tuple(lines3) == bits:
            return name
    return "乾"


def _hex_name(lines: list[int]) -> tuple[str, str, str]:
    lower = _trigram_from_lines(lines[:3])
    upper = _trigram_from_lines(lines[3:])
    return HEX_BY_TRIGRAM.get((upper, lower), f"{upper}{lower}卦"), upper, lower


def _coin_lines(tosses) -> tuple[list[int], list[int], str]:
    if tosses and len(tosses) >= 6:
        values = [int(x) for x in tosses[:6]]
        if all(v in (6, 7, 8, 9) for v in values):
            lines = [1 if v in (7, 9) else 0 for v in values]
            moving = [i + 1 for i, v in enumerate(values) if v in (6, 9)]
            return lines, moving, "manual_coin"
        lines = [1 if v else 0 for v in values]
        return lines, [], "manual_binary"
    return [], [], ""


def _time_lines(b: Birth) -> tuple[list[int], list[int], str]:
    nums = [b.year, b.month, b.day, b.hour, b.minute]
    seed = "-".join(map(str, nums)) + "-" + (b.question or "")
    rng = random.Random(hashlib.sha256(seed.encode("utf-8")).hexdigest())
    yao_values = [rng.choice([6, 7, 8, 9]) for _ in range(6)]
    lines = [1 if v in (7, 9) else 0 for v in yao_values]
    moving = [i + 1 for i, v in enumerate(yao_values) if v in (6, 9)]
    return lines, moving or [((b.hour + b.day) % 6) + 1], "time_qigua"


def _number_lines(b: Birth) -> tuple[list[int], list[int], str]:
    seed = str(b.seed if b.seed is not None else b.question or f"{b.year}{b.month}{b.day}{b.hour}")
    rng = random.Random(seed)
    yao_values = [rng.choice([6, 7, 8, 9]) for _ in range(6)]
    lines = [1 if v in (7, 9) else 0 for v in yao_values]
    moving = [i + 1 for i, v in enumerate(yao_values) if v in (6, 9)]
    return lines, moving or [rng.randint(1, 6)], "number_qigua"


# 天干五行映射
_TG_WX = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
          "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}

# 五行生克关系: 克我者为官鬼, 我克者为妻财, 生我者为父母, 我生者为子孙, 同我者为兄弟
_WX_RELATION = {
    # (self_wx, other_wx) -> 六亲
    # 我克 = 妻财, 克我 = 官鬼, 生我 = 父母, 我生 = 子孙, 同 = 兄弟
}
def _derive_liu_qin(day_gan: str, najia: list[str]) -> list[str]:
    """根据日干五行与各爻纳音五行的关系推导六亲。

    关系规则 (以日干为我):
    - 同我: 兄弟
    - 我生: 子孙
    - 我克: 妻财
    - 生我: 父母
    - 克我: 官鬼
    """
    day_wx = _TG_WX.get(day_gan, "土")
    out = []
    for item in najia:
        if not item:
            out.append("兄弟")
            continue
        line_wx = item[-1]  # 纳音最后一个字是五行: 木/火/土/金/水
        # 简化五行字符映射
        wx_map = {"木": "木", "火": "火", "土": "土", "金": "金", "水": "水"}
        line_wx = wx_map.get(line_wx, "土")

        if line_wx == day_wx:
            out.append("兄弟")
        elif (day_wx, line_wx) in WX_SHENG:
            out.append("子孙")  # 我生
        elif (line_wx, day_wx) in WX_SHENG:
            out.append("父母")  # 生我
        elif (day_wx, line_wx) in WX_KE:
            out.append("妻财")  # 我克
        elif (line_wx, day_wx) in WX_KE:
            out.append("官鬼")  # 克我
        else:
            out.append("兄弟")
    return out


# 五行生克关系集
WX_SHENG = {("木", "火"), ("火", "土"), ("土", "金"), ("金", "水"), ("水", "木")}
WX_KE = {("木", "土"), ("土", "水"), ("水", "火"), ("火", "金"), ("金", "木")}


def _count_najia_elements(najia: list[str]) -> dict:
    """从纳音统计六爻五行分布。"""
    elem = {"metal": 0, "wood": 0, "water": 0, "fire": 0, "earth": 0}
    wx_key = {"金": "metal", "木": "wood", "水": "water", "火": "fire", "土": "earth"}
    for item in najia:
        if item and item[-1] in wx_key:
            elem[wx_key[item[-1]]] += 1
    return elem


def compute(b: Birth) -> ChartResult:
    requested_mode = b.mode or "time_qigua"
    subject = b.subject or "decision"
    lines, moving, actual_mode = _coin_lines(b.tosses)
    if not lines:
        if requested_mode == "number_qigua":
            lines, moving, actual_mode = _number_lines(b)
        else:
            lines, moving, actual_mode = _time_lines(b)

    ben_name, upper, lower = _hex_name(lines)
    bian_lines = list(lines)
    for pos in moving:
        bian_lines[pos - 1] = 1 - bian_lines[pos - 1]
    bian_name, bian_upper, bian_lower = _hex_name(bian_lines)

    solar = Solar.fromYmdHms(b.year, b.month, b.day, b.hour, b.minute, 0)
    lunar = solar.getLunar()
    day_gz = lunar.getDayInGanZhi()
    hour_gz = lunar.getTimeInGanZhi()
    start_idx = LIUSHEN_START.get(day_gz[0], 0)
    liu_shen = [LIUSHEN[(start_idx + i) % 6] for i in range(6)]
    najia = NAJIA.get(lower, [""] * 3)[:3] + NAJIA.get(upper, [""] * 6)[3:]
    liu_qin = _derive_liu_qin(day_gz[0], najia)
    # 针对特定主题的用神覆盖提示
    using_god_hint = SUBJECT_USING_GOD.get(subject, "世应与动爻")
    if subject in {"career", "wealth", "relationship"}:
        idx = 2  # 第三爻(索引2)通常为世爻位置
        # 用神覆盖仅作为解读参考, 不更改实际六亲推导结果
        using_god_hint = f"{using_god_hint} (六亲参考: 第{idx+1}爻为{liu_qin[idx]})"
    shi_yao = 3 if subject in {"decision", "career"} else 1
    ying_yao = ((shi_yao + 2) % 6) + 1

    return ChartResult(
        method="liuyao",
        school="east",
        engine="self+iching",
        normalized={"elements": _count_najia_elements(najia), "timeline": []},
        raw={
            "mode": actual_mode,
            "subject": subject,
            "rule_version": "v1",
            "ben_gua": ben_name,
            "bian_gua": bian_name if bian_name != ben_name else None,
            "upper_trigram": upper,
            "lower_trigram": lower,
            "changed_upper_trigram": bian_upper,
            "changed_lower_trigram": bian_lower,
            "dong_yao": moving,
            "shi_yao": shi_yao,
            "ying_yao": ying_yao,
            "using_god": using_god_hint,
            "using_god_basis": {
                "career": "以官鬼为用神,看动爻/世应",
                "wealth": "以妻财为用神,看动爻/世应",
                "relationship": "以妻财 (男问感情) / 官鬼 (女问感情) 为用神",
                "lost_item": "以父母 (失物为印) 或妻财 (失财) 为用神",
                "decision": "看世爻、应爻、动爻之生克制化",
            }.get(subject, "以世爻、应爻、动爻为参考"),
            "liu_qin": liu_qin,
            "liu_shen": liu_shen,
            "hex_lines": [{"pos": i + 1, "yang": bool(lines[i]), "gan_zhi": najia[i] if i < len(najia) else ""} for i in range(6)],
            "gua_ci": f"{ben_name}，{actual_mode} 起卦，按 {subject} 取用神。",
            "day_gz": day_gz,
            "hour_gz": hour_gz,
            "tosses": b.tosses or lines,
            "calculation_basis": {
                "method": "liuyao",
                "mode": actual_mode,
                "subject": subject,
                "rule_version": "v1",
                "priority": "manual coin tosses > number qigua > time qigua",
                "using_god_rule": SUBJECT_USING_GOD.get(subject, "世爻、应爻、动爻合参"),
                "input_source": "birth (year/month/day/hour/minute) + manual tosses (optional) + question (optional)",
                "limits": [
                    "卦位 64 卦以八卦上下组合为骨,纳甲/世应/六亲/六神在六爻本位置入表",
                    "用神按主题选: 事业选官鬼、财运选妻财、感情选官鬼/妻财、失物选父母/妻财",
                    "手动铜钱三枚爻面 (6/7/8/9) 优先级最高; 无 tosses 才走数字/时间起卦",
                    "本实现不纳入卦气/卦象详析, 只到卦名 + 动爻 + 用神 + 世应层",
                ],
            },
        },
    )
