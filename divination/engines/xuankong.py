"""玄空飞星排盘 —— 文献：《沈氏玄空学》。需 period(运 1-9) + sitting(坐山)。
用法：compute(birth, period=8, sitting='子')；运缺省按建造/起造年推。

流年盘：compute_liunian_pan(year, period) — 查预计算表。
"""
from ..contracts import Birth, ChartResult
from ..data.xuankong_liunian import (
    XUANKONG_LIUNIAN_8,
    XUANKONG_LIUNIAN_9,
    XUANKONG_LIUNIAN_ALL,
    XuankongLiunianPan,
    PalaceCell,
    _STAR_WUXING as _XK_STAR_WUXING,
    get_liunian_pan,
    get_liunian_by_period,
    get_palace_detail,
)
from ..fengshui import san_yuan_jiu_yun, xuankong as _xk


def compute(b: Birth, period: int | None = None, sitting: str = "子",
            facing_deg: float | None = None) -> ChartResult:
    period = getattr(b, "period", None) or period
    sitting = getattr(b, "sitting", None) or sitting
    construction_year = getattr(b, "construction_year", None)
    if period is None:
        period = san_yuan_jiu_yun(construction_year or b.year)["运"]
    r = _xk(period, sitting)
    # 兼向替卦检测
    r["tixing"] = None
    if facing_deg is not None:
        try:
            from ..data.xuankong_jian_xiang import should_use_jian_xiang, apply_jian_xiang_tixing, find_jian_shan
            if should_use_jian_xiang(facing_deg, sitting):
                jian = find_jian_shan(facing_deg, sitting)
                if jian:
                    tixing = apply_jian_xiang_tixing(sitting, jian)
                    if tixing:
                        r["tixing"] = {"original_shan": sitting, "jian_shan": jian,
                                        "tixing_shan": tixing, "is_jian_xiang": True}
        except ImportError:
            pass
    return ChartResult(method="xuankong", school="east", engine="self(沈氏玄空)",
                       normalized={"elements": {}, "timeline": []}, raw=r)


# ═══════════════════════════════════════════════════════════════
# 流年盘
# ═══════════════════════════════════════════════════════════════
def compute_liunian_pan(year: int, period: int) -> dict:
    """计算指定年份和运数的玄空流年盘。

    数据驱动：查预计算的 XUANKONG_LIUNIAN_ALL 表。
    纯函数：同一 (year, period) 永远同一输出。

    Args:
        year: 公历年份 (8运: 2006-2035; 9运: 2024-2053)
        period: 运数 (8 or 9)

    Returns:
        dict with:
          - year, period, annual_center
          - yun_pan: 运盘 {卦: 星}
          - annual_pan: 年盘 {卦: 星}
          - palaces: 九宫叠合详情 {卦: PalaceCell}
          - auspicious_palaces: 吉宫列表
          - inauspicious_palaces: 凶宫列表
          - summary: 流年总评
          - wuxing_analysis: 五行生克分析
    """
    pan = get_liunian_pan(year, period)
    if pan is None:
        return {
            "error": f"无数据: year={year}, period={period} (8运:2006-2035, 9运:2024-2053)",
            "year": year,
            "period": period,
        }

    # 五行生克深层分析
    wuxing_analysis = _compute_liunian_wuxing_analysis(pan)

    return {
        "year": year,
        "period": period,
        "annual_center": pan.annual_center,
        "annual_center_nature": pan.annual_center_nature,
        "yun_pan": pan.yun_pan,
        "annual_pan": pan.annual_pan,
        "palaces": {
            gua: {
                "gua": cell.gua,
                "direction": cell.direction,
                "yun_star": cell.yun_star,
                "annual_star": cell.annual_star,
                "yun_wx": cell.yun_wx,
                "annual_wx": cell.annual_wx,
                "yun_annual_relation": cell.yun_annual_relation,
                "annual_yun_relation": cell.annual_yun_relation,
                "assessment": cell.assessment,
            }
            for gua, cell in pan.palaces.items()
        },
        "auspicious_palaces": pan.auspicious_palaces,
        "inauspicious_palaces": pan.inauspicious_palaces,
        "summary": pan.summary,
        "wuxing_analysis": wuxing_analysis,
    }


def _compute_liunian_wuxing_analysis(pan: XuankongLiunianPan) -> dict:
    """基于流年盘计算五行全面分析（数据驱动）。"""
    # 统计各五行出现频次（运星 + 年星）
    yun_wx_count: dict[str, int] = {}
    annual_wx_count: dict[str, int] = {}
    for cell in pan.palaces.values():
        yun_wx_count[cell.yun_wx] = yun_wx_count.get(cell.yun_wx, 0) + 1
        annual_wx_count[cell.annual_wx] = annual_wx_count.get(cell.annual_wx, 0) + 1

    # 生克关系统计
    relation_counts: dict[str, int] = {}
    for cell in pan.palaces.values():
        rel = cell.annual_yun_relation
        relation_counts[rel] = relation_counts.get(rel, 0) + 1

    # 最旺五行
    dominant_yun = max(yun_wx_count, key=yun_wx_count.get) if yun_wx_count else "土"
    dominant_annual = max(annual_wx_count, key=annual_wx_count.get) if annual_wx_count else "土"

    # 吉凶比例
    ausp_count = len(pan.auspicious_palaces)
    inausp_count = len(pan.inauspicious_palaces)

    return {
        "yun_wuxing_distribution": yun_wx_count,
        "annual_wuxing_distribution": annual_wx_count,
        "dominant_yun_wuxing": dominant_yun,
        "dominant_annual_wuxing": dominant_annual,
        "relation_distribution": relation_counts,
        "auspicious_ratio": f"{ausp_count}/{ausp_count + inausp_count + 1}",
        "star_wuxing_lookup": {s: w for s, w in _XK_STAR_WUXING.items()},
    }

