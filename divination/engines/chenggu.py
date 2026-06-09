"""Yuan Tiangang bone weight using traditional lookup tables."""
from lunar_python import Solar

from ..contracts import Birth, ChartResult

YEAR_WEIGHT = [
    12, 9, 6, 7, 12, 5, 9, 8, 7, 8, 15, 6,
    16, 15, 7, 8, 16, 8, 19, 12, 6, 8, 7, 5,
    15, 9, 16, 8, 8, 19, 12, 6, 8, 7, 5, 15,
    9, 16, 8, 8, 19, 12, 6, 8, 7, 5, 15, 9,
    16, 8, 8, 19, 12, 6, 8, 7, 5, 15, 9, 16,
]
MONTH_WEIGHT = [6, 7, 18, 9, 5, 16, 9, 15, 18, 8, 9, 5]
DAY_WEIGHT = [
    5, 10, 8, 15, 16, 15, 8, 16, 8, 16,
    9, 17, 8, 17, 10, 8, 9, 18, 5, 15,
    10, 9, 8, 9, 15, 18, 7, 8, 16, 6,
]
HOUR_WEIGHT = {
    "子": 16, "丑": 6, "寅": 7, "卯": 10, "辰": 9, "巳": 16,
    "午": 10, "未": 8, "申": 8, "酉": 9, "戌": 6, "亥": 6,
}


def _jiazi_index(gz: str) -> int:
    stems = "甲乙丙丁戊己庚辛壬癸"
    branches = "子丑寅卯辰巳午未申酉戌亥"
    for i in range(60):
        if stems[i % 10] == gz[0] and branches[i % 12] == gz[1]:
            return i
    return 0


def _piyu(qian: int) -> str:
    if qian < 30:
        return "骨重较轻，传统批语多主早年劳碌，宜重后天修为。"
    if qian < 40:
        return "中平之格，传统批语多主先难后易，靠积累见成。"
    if qian < 50:
        return "中上之格，传统批语多主衣食渐丰，晚景较稳。"
    if qian < 60:
        return "较厚之格，传统批语多主福分可得，但忌骄满。"
    return "骨重厚重，传统批语多主格局较高，仍须结合八字细看。"


def compute(b: Birth) -> ChartResult:
    solar = Solar.fromYmdHms(b.year, b.month, b.day, b.hour, b.minute, 0)
    lunar = solar.getLunar()
    year_gz = lunar.getYearInGanZhiByLiChun()
    year_idx = _jiazi_index(year_gz)
    month = lunar.getMonth()
    day = lunar.getDay()
    hour_zhi = lunar.getTimeZhi()

    y_qian = YEAR_WEIGHT[year_idx]
    m_qian = MONTH_WEIGHT[month - 1]
    d_qian = DAY_WEIGHT[day - 1]
    h_qian = HOUR_WEIGHT.get(hour_zhi, 0)
    total_qian = y_qian + m_qian + d_qian + h_qian
    total_liang = round(total_qian / 10, 1)

    return ChartResult(
        method="chenggu",
        school="east",
        engine="self+traditional-table",
        normalized={"elements": {}, "timeline": [], "note": "称骨不直接映射五行元素, 以骨重总量(l量)为归一化指标"},
        raw={
            "mode": "traditional_weight",
            "subject": b.subject or "self_life",
            "rule_version": "v1",
            "year_qian": y_qian,
            "month_qian": m_qian,
            "day_qian": d_qian,
            "hour_qian": h_qian,
            "total_liang": total_liang,
            "total_qian": total_qian,
            "piyu": _piyu(total_qian),
            "ganzhi": {"year": year_gz, "month": lunar.getMonthInGanZhi(), "day": lunar.getDayInGanZhi(), "hour": lunar.getTimeInGanZhi()},
            "calculation_basis": {
                "method": "chenggu",
                "mode": "traditional_weight",
                "calendar_source": "lunar-python",
                "rule_version": "v1",
                "rule": "Yuan Tiangang bone-weight year/month/day/hour lookup tables, qian as integer tenths of liang",
                "note": "称骨是传统歌诀表，不替代八字格局取用。",
                "limits": [
                    "仅提供骨重总览, 不解读具体命造格局",
                    "年柱用立春分界, 月柱用农历月, 日柱用农历日, 时柱用地支",
                    "骨重解释为传统歌诀批语, 非定量模型",
                ],
            },
        },
    )
