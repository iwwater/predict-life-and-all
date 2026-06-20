"""八宅流年飞星数据 —— 年度紫白飞星入中及各方位飞星分布。

文献：
  - 《八宅明镜》(清·箬冠道人) — 八宅本命卦 + 游年星
  - 《紫白诀》— 年紫白飞星入中算法
  - 《沈氏玄空学》(清·沈竹礽) — 年飞星流年盘

年紫白算法：
  取公历年各位数之和 → 反复加至个位数 n
  年紫白入中星 = (11 - n) % 9, 若 0 则为 9
  然后按洛书轨迹顺飞九宫（中→乾→兑→艮→离→坎→坤→震→巽）

方位吉凶（八宅视角）：
  流年飞星与宅命卦交互：星生宅命/比和为吉，星克宅命为凶
  年星 1(白水)/6(白金)/8(白土) 为三吉星
  年星 2(黑土)/3(碧木)/5(黄土)/7(赤金) 为凶星
  年星 4(绿木)/9(紫火) 为中性偏吉
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ══════════════════════════════════════════════════════════════
# 1. 洛书飞泊路径（后天八卦顺序，中宫起）
# ══════════════════════════════════════════════════════════════
_LUOSHU_FLY_PATH: list[str] = ["中", "乾", "兑", "艮", "离", "坎", "坤", "震", "巽"]

# 卦名 ↔ 方位映射
_GUA_DIRECTION: dict[str, str] = {
    "乾": "西北", "兑": "西", "艮": "东北", "离": "南",
    "坎": "北", "坤": "西南", "震": "东", "巽": "东南", "中": "中宫",
}

# 年星吉凶等级
_STAR_NATURE: dict[int, dict] = {
    1: {"name": "一白水", "element": "水", "auspicious": True, "domain": "桃花/人缘/文昌"},
    2: {"name": "二黑土", "element": "土", "auspicious": False, "domain": "病符/健康"},
    3: {"name": "三碧木", "element": "木", "auspicious": False, "domain": "是非/官非/口舌"},
    4: {"name": "四绿木", "element": "木", "auspicious": True, "domain": "文昌/学业/名誉"},
    5: {"name": "五黄土", "element": "土", "auspicious": False, "domain": "灾煞/大凶/破财"},
    6: {"name": "六白金", "element": "金", "auspicious": True, "domain": "权贵/偏财/升迁"},
    7: {"name": "七赤金", "element": "金", "auspicious": False, "domain": "破军/盗贼/口舌"},
    8: {"name": "八白土", "element": "土", "auspicious": True, "domain": "正财/田宅/置业"},
    9: {"name": "九紫火", "element": "火", "auspicious": True, "domain": "喜事/姻缘/贵人"},
}


def _reduce_to_single_digit(n: int) -> int:
    """将整数各位相加，反复直到个位数。"""
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def _compute_annual_center(year: int) -> int:
    """计算年紫白入中星数 (1-9)。"""
    n = _reduce_to_single_digit(year)
    center = (11 - n) % 9
    return center if center != 0 else 9


def _fly_from_center(center: int) -> dict[str, int]:
    """以 center 星入中宫，顺飞九宫。返回 {卦名: 星数}。"""
    result: dict[str, int] = {}
    star = center
    for gua in _LUOSHU_FLY_PATH:
        result[gua] = star
        star = star % 9 + 1  # 顺飞: 递增
    return result


# ══════════════════════════════════════════════════════════════
# 2. 数据结构
# ══════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class BazhaiLiunianStar:
    """单一年度的八宅流年飞星数据。

    Attributes:
        year: 公历年份
        center_star: 入中星数 (1-9)
        center_star_name: 入中星名称
        palace_stars: {卦名: 星数} 九宫飞星分布
        direction_stars: {方位: 星数} 以方位名索引
        auspicious_directions: 该年吉方列表
        inauspicious_directions: 该年凶方列表
        three_white: 三白星所在方位 (1/6/8)
    """
    year: int
    center_star: int
    center_star_name: str
    palace_stars: dict[str, int] = field(default_factory=dict)
    direction_stars: dict[str, int] = field(default_factory=dict)
    auspicious_directions: list[str] = field(default_factory=list)
    inauspicious_directions: list[str] = field(default_factory=list)
    three_white: dict[str, int] = field(default_factory=dict)  # {star_name: direction}


def _build_year_entry(year: int) -> BazhaiLiunianStar:
    """构建单一年份的流年飞星条目。"""
    center = _compute_annual_center(year)
    palace_stars = _fly_from_center(center)
    direction_stars = {_GUA_DIRECTION[gua]: star for gua, star in palace_stars.items()}

    auspicious = []
    inauspicious = []
    for gua, star in palace_stars.items():
        direction = _GUA_DIRECTION[gua]
        nature = _STAR_NATURE.get(star, {})
        if nature.get("auspicious", True):
            auspicious.append(direction)
        else:
            inauspicious.append(direction)

    three_white = {}
    for gua, star in palace_stars.items():
        if star in (1, 6, 8):
            three_white[_STAR_NATURE[star]["name"]] = _GUA_DIRECTION[gua]

    return BazhaiLiunianStar(
        year=year,
        center_star=center,
        center_star_name=_STAR_NATURE[center]["name"],
        palace_stars=dict(palace_stars),
        direction_stars=dict(direction_stars),
        auspicious_directions=list(auspicious),
        inauspicious_directions=list(inauspicious),
        three_white=dict(three_white),
    )


# ══════════════════════════════════════════════════════════════
# 3. 三十年流年飞星数据 (2006–2035)
# ══════════════════════════════════════════════════════════════
# 年份范围说明：覆盖 2006–2035 共 30 年，涵盖八运末 + 九运初
BAZHAI_LIUNIAN_YEARS: list[int] = list(range(2006, 2036))

BAZHAI_LIUNIAN: dict[int, BazhaiLiunianStar] = {
    year: _build_year_entry(year) for year in BAZHAI_LIUNIAN_YEARS
}


# ══════════════════════════════════════════════════════════════
# 4. 查询函数
# ══════════════════════════════════════════════════════════════
def get_liunian_star(year: int) -> BazhaiLiunianStar | None:
    """查询指定年份的流年飞星数据。"""
    return BAZHAI_LIUNIAN.get(year)


def get_liunian_star_for_direction(year: int, direction: str) -> dict | None:
    """查询某年某方位的流年飞星 (含吉凶和星性)。"""
    entry = BAZHAI_LIUNIAN.get(year)
    if entry is None:
        return None
    star = entry.direction_stars.get(direction)
    if star is None:
        return None
    nature = _STAR_NATURE.get(star, {})
    return {
        "year": year,
        "direction": direction,
        "star": star,
        "star_name": nature.get("name", f"星{star}"),
        "element": nature.get("element", "?"),
        "auspicious": nature.get("auspicious", True),
        "domain": nature.get("domain", ""),
    }


def get_liunian_range(
    start_year: int | None = None, end_year: int | None = None
) -> dict[int, BazhaiLiunianStar]:
    """获取某年份区间的流年数据。若不指定则返回全部 30 年。"""
    if start_year is None and end_year is None:
        return dict(BAZHAI_LIUNIAN)
    start = start_year or min(BAZHAI_LIUNIAN.keys())
    end = end_year or max(BAZHAI_LIUNIAN.keys())
    return {y: e for y, e in BAZHAI_LIUNIAN.items() if start <= y <= end}
