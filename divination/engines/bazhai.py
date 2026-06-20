"""八宅风水（命卦+八游年方位吉凶+流年飞星）—— 文献：《八宅明镜》《紫白诀》。"""
from ..contracts import Birth, ChartResult
from ..data.bazhai_liunian import (
    BAZHAI_LIUNIAN,
    BazhaiLiunianStar,
    _STAR_NATURE,
    get_liunian_star,
    get_liunian_star_for_direction,
    get_liunian_range,
)
from ..fengshui import bazhai as _bazhai

# 八宅本命卦 → 命宅方位映射
_BAZHAI_BY_GUA: dict[str, str] = {
    "坎": "北", "离": "南", "震": "东", "巽": "东南",
    "乾": "西北", "坤": "西南", "艮": "东北", "兑": "西",
}


def compute(b: Birth) -> ChartResult:
    r = _bazhai(b.year, b.gender)
    return ChartResult(method="bazhai", school="east", engine="self(八宅明镜)",
                       normalized={"elements": {}, "timeline": []}, raw=r)


# ═══════════════════════════════════════════════════════════════
# 流年飞星
# ═══════════════════════════════════════════════════════════════
def compute_liunian_stars(year: int) -> dict:
    """计算指定年份的八宅流年飞星，返回与命宅卦交互的结果。

    数据驱动：查预计算的 BAZHAI_LIUNIAN 表。
    纯函数：同一输入永远同一输出。

    Args:
        year: 公历年份 (2006-2035)

    Returns:
        dict with:
          - year: 年份
          - center_star: 入中星
          - direction_stars: {方位: 星数}
          - star_details: {星数: 星性}
          - auspicious_directions: 吉方列表
          - inauspicious_directions: 凶方列表
          - three_white: 三白星方位
          - bazhai_interactions: 与八宅命卦的交互
    """
    entry = get_liunian_star(year)
    if entry is None:
        return {"error": f"年份 {year} 超出数据范围 (2006-2035)", "year": year}

    # 星性详情
    star_details = {s: dict(_STAR_NATURE.get(s, {})) for s in range(1, 10)}

    # 八宅交互：各命卦与各方位流年星的关系
    bazhai_interactions = _compute_bazhai_liunian_interactions(entry)

    return {
        "year": year,
        "center_star": entry.center_star,
        "center_star_name": entry.center_star_name,
        "direction_stars": entry.direction_stars,
        "palace_stars": entry.palace_stars,
        "star_details": star_details,
        "auspicious_directions": entry.auspicious_directions,
        "inauspicious_directions": entry.inauspicious_directions,
        "three_white": entry.three_white,
        "bazhai_interactions": bazhai_interactions,
    }


def _compute_bazhai_liunian_interactions(entry: BazhaiLiunianStar) -> dict:
    """计算各八宅本命卦与流年飞星的交互吉凶。

    规则 (数据驱动):
      - 流年星吉 + 宅命方吉 = 叠吉 (大吉)
      - 流年星凶 + 宅命方凶 = 叠凶 (大凶)
      - 流年星吉 + 宅命方凶 = 吉凶相抵
      - 流年星凶 + 宅命方吉 = 凶煞犯吉
      - 流年星五行生宅命方 → 生入吉
      - 流年星五行克宅命方 → 克入凶
    """
    # 八宅八方游年星吉凶 (来自 bazhai)
    _GUA_JIXIONG: dict[str, dict[str, str]] = {
        "坎": {"坎": "吉", "离": "吉", "震": "吉", "巽": "吉", "乾": "凶", "坤": "凶", "兑": "凶", "艮": "凶"},
        "离": {"离": "吉", "坎": "吉", "巽": "吉", "震": "吉", "坤": "凶", "乾": "凶", "艮": "凶", "兑": "凶"},
        "震": {"震": "吉", "巽": "吉", "坎": "吉", "离": "吉", "兑": "凶", "艮": "凶", "乾": "凶", "坤": "凶"},
        "巽": {"巽": "吉", "震": "吉", "离": "吉", "坎": "吉", "艮": "凶", "兑": "凶", "坤": "凶", "乾": "凶"},
        "乾": {"乾": "吉", "兑": "吉", "艮": "吉", "坤": "吉", "巽": "凶", "坎": "凶", "震": "凶", "离": "凶"},
        "坤": {"坤": "吉", "艮": "吉", "兑": "吉", "乾": "吉", "坎": "凶", "离": "凶", "巽": "凶", "震": "凶"},
        "艮": {"艮": "吉", "坤": "吉", "乾": "吉", "兑": "吉", "离": "凶", "震": "凶", "巽": "凶", "坎": "凶"},
        "兑": {"兑": "吉", "乾": "吉", "坤": "吉", "艮": "吉", "震": "凶", "巽": "凶", "离": "凶", "坎": "凶"},
    }

    _GUA_TO_DIRECTION: dict[str, str] = {
        "坎": "北", "离": "南", "震": "东", "巽": "东南",
        "乾": "西北", "坤": "西南", "艮": "东北", "兑": "西",
    }

    _DIRECTION_TO_GUA: dict[str, str] = {v: k for k, v in _GUA_TO_DIRECTION.items()}

    result: dict[str, list[dict]] = {}
    for ming_gua, gua_ji_map in _GUA_JIXIONG.items():
        interactions: list[dict] = []
        for gua, jixiong in gua_ji_map.items():
            direction = _GUA_TO_DIRECTION.get(gua, gua)
            star = entry.palace_stars.get(gua)
            if star is None:
                continue
            nature = _STAR_NATURE.get(star, {})
            star_auspicious = nature.get("auspicious", True)
            # 叠合判断
            if jixiong == "吉" and star_auspicious:
                combined = "叠吉"
            elif jixiong == "凶" and not star_auspicious:
                combined = "叠凶"
            elif jixiong == "吉" and not star_auspicious:
                combined = "凶犯吉方"
            else:
                combined = "吉制凶方"

            interactions.append({
                "direction": direction,
                "gua": gua,
                "star": star,
                "star_name": nature.get("name", f"星{star}"),
                "star_auspicious": star_auspicious,
                "bazhai_auspicious": jixiong == "吉",
                "combined": combined,
            })
        result[ming_gua] = interactions
    return result

