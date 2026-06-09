"""Xuan Kong Flying Star using period, 24 mountains, and Luo Shu flight."""
from ..contracts import Birth, ChartResult

SANSHAN = ["壬", "子", "癸", "丑", "艮", "寅", "甲", "卯", "乙", "辰", "巽", "巳", "丙", "午", "丁", "未", "坤", "申", "庚", "酉", "辛", "戌", "乾", "亥"]
SAN_TO_GUA = {
    "壬": "坎", "子": "坎", "癸": "坎",
    "丑": "艮", "艮": "艮", "寅": "艮",
    "甲": "震", "卯": "震", "乙": "震",
    "辰": "巽", "巽": "巽", "巳": "巽",
    "丙": "离", "午": "离", "丁": "离",
    "未": "坤", "坤": "坤", "申": "坤",
    "庚": "兑", "酉": "兑", "辛": "兑",
    "戌": "乾", "乾": "乾", "亥": "乾",
}
GONG_NUM = {1: "坎", 2: "坤", 3: "震", 4: "巽", 5: "中", 6: "乾", 7: "兑", 8: "艮", 9: "离"}
GUA_GONG_NUM = {"坎": 1, "坤": 2, "震": 3, "巽": 4, "中": 5, "乾": 6, "兑": 7, "艮": 8, "离": 9}
LUO_ORDER = [5, 6, 7, 8, 9, 1, 2, 3, 4]

# 洛书数五行: 用于飞星旺衰计算
NUM_WUXING = {1: "水", 2: "土", 3: "木", 4: "木", 5: "土", 6: "金", 7: "金", 8: "土", 9: "火"}

# 五行生克链
_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def _period(year: int) -> tuple[int, str]:
    if 1864 <= year <= 1883: return 1, "上元"
    if 1884 <= year <= 1903: return 2, "上元"
    if 1904 <= year <= 1923: return 3, "上元"
    if 1924 <= year <= 1943: return 4, "中元"
    if 1944 <= year <= 1963: return 5, "中元"
    if 1964 <= year <= 1983: return 6, "中元"
    if 1984 <= year <= 2003: return 7, "下元"
    if 2004 <= year <= 2023: return 8, "下元"
    if 2024 <= year <= 2043: return 9, "下元"
    base = 1864
    idx = ((year - base) // 20) % 9 + 1
    yuan = "上元" if idx <= 3 else "中元" if idx <= 6 else "下元"
    return idx, yuan


def _fly(start: int, reverse: bool = False) -> dict[str, int]:
    values = {}
    seq = list(reversed(LUO_ORDER)) if reverse else LUO_ORDER
    for offset, palace in enumerate(seq):
        values[GONG_NUM[palace]] = ((start + offset - 1) % 9) + 1
    return values


def _facing(sitting: str) -> str:
    if sitting not in SANSHAN:
        sitting = "子"
    return SANSHAN[(SANSHAN.index(sitting) + 12) % 24]


def _reverse_for_san(san: str) -> bool:
    # First mountain of each trigram runs forward, middle/last reverse; recorded as the adopted rule.
    idx = SANSHAN.index(san)
    return idx % 3 != 0


def star_timeliness(star_num: int, period_num: int) -> str:
    """Determine flying star timeliness relative to the current period.
    Returns: 旺/生/退/死/煞/平"""
    if star_num == period_num:
        return "旺"
    sw = NUM_WUXING.get(star_num, "")
    pw = NUM_WUXING.get(period_num, "")
    if not sw or not pw:
        return "平"
    if _SHENG.get(sw) == pw:
        return "生"   # star generates the period — fresh energy
    if _SHENG.get(pw) == sw:
        return "退"   # period generates star — retreating energy
    if _KE.get(sw) == pw:
        return "死"   # star overcomes period — dead energy
    if _KE.get(pw) == sw:
        return "煞"   # period overcomes star — killing energy
    return "平"


def compute(b: Birth) -> ChartResult:
    year = int(b.construction_year or b.year)
    period_num, yuan = (int(b.period), "指定元") if b.period else _period(year)
    sitting_san = b.sitting if b.sitting in SANSHAN else "子"
    facing_san = _facing(sitting_san)
    sitting_gua = SAN_TO_GUA[sitting_san]
    facing_gua = SAN_TO_GUA[facing_san]

    yun_stars = _fly(period_num)
    mountain_start = GUA_GONG_NUM.get(sitting_gua, period_num)
    facing_start = GUA_GONG_NUM.get(facing_gua, period_num)
    mountain_stars = _fly(mountain_start, reverse=_reverse_for_san(sitting_san))
    facing_stars = _fly(facing_start, reverse=_reverse_for_san(facing_san))
    grid = {}
    for gua in GONG_NUM.values():
        yun = yun_stars[gua]
        shan = mountain_stars[gua]
        xiang = facing_stars[gua]
        grid[gua] = {
            "运": yun, "山": shan, "向": xiang,
            "运_旺衰": star_timeliness(yun, period_num),
            "山_旺衰": star_timeliness(shan, period_num),
            "向_旺衰": star_timeliness(xiang, period_num),
        }

    if grid[sitting_gua]["山"] == period_num and grid[facing_gua]["向"] == period_num:
        pattern = "旺山旺向"
    elif grid[facing_gua]["向"] == period_num:
        pattern = "双星到向"
    elif grid[sitting_gua]["山"] == period_num:
        pattern = "双星到坐"
    else:
        pattern = "上山下水"

    return ChartResult(
        method="xuankong",
        school="east",
        engine="self+luoshu",
        normalized={"elements": {}, "timeline": [], "note": "玄空飞星以运山向三盘飞星为指标, 不直接做五行计数"},
        raw={
            "mode": "residential_xuankong",
            "subject": b.subject or "home_fengshui",
            "rule_version": "v1",
            "period": f"{yuan}{period_num}运",
            "period_number": period_num,
            "construction_year": year,
            "sitting": sitting_san,
            "facing": facing_san,
            "sitting_gua": sitting_gua,
            "facing_gua": facing_gua,
            "grid": grid,
            "pattern": pattern,
            "mid_court": period_num,
            "star_timeliness": {
                "period_wuxing": NUM_WUXING.get(period_num, ""),
                "legend": {"旺": "当运大吉", "生": "生气吉", "退": "退气平", "死": "死气凶", "煞": "煞气大凶", "平": "中和"},
            },
            "ti_gua_reserved": {"enabled": False, "note": "替卦预留位, 下一版本补入"},
            "sitting_valid": sitting_san in SANSHAN,
            "facing_valid": facing_san in SANSHAN,
            "calculation_basis": {
                "method": "xuankong",
                "mode": "residential_xuankong",
                "rule_version": "v1",
                "input_source": "construction_year + sitting (24山合法) + optional period override",
                "period_rule": "三元九运，每运20年，默认用建造/入伙年；可用 period 覆盖。",
                "sitting_rule": "24山坐山，向山取对宫相差12山。",
                "flight_rule": "洛书飞布；运星从当运入中顺飞；山星从坐山卦洛书数入中、向星从向首卦洛书数入中，依三山阴阳定顺逆。旺衰按五星生克定旺生退死煞。",
                "limits": [
                    "24山合法输入, 不合法默认回退子山",
                    "替卦预留位, 当前不启用",
                    "山盘/向盘/运盘 均为同一元局派生的稳定快照, 不做环境形峦判断",
                ],
            },
        },
    )
