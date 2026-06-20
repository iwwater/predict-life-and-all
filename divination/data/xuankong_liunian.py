"""玄空流年盘数据 —— 八运/九运各 30 年的玄空飞星流年盘。

文献：
  - 《沈氏玄空学》(清·沈竹礽) — 年飞星流年 + 运星交互
  - 《紫白诀》— 年紫白入中 + 月紫白
  - 《玄空秘旨》— 流年飞星与运盘生克

核心概念：
  - 玄空流年 = 运盘（permanent） + 年盘（annual）叠合
  - 运盘：以当运星入中顺飞（如山向盘）
  - 年盘：以年紫白星入中顺飞
  - 两盘叠合看各宫：运星与年星生克定吉凶
  - 年星克运星为"煞"，运星生年星为"生入吉"，年星生运星为"生出泄"
  - 年星与运星同宫比和为"旺"

数据结构：
  每个流年条目包含：年份、运数、年紫白入中星、九宫叠合数据（运星/年星/生克关系）
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ══════════════════════════════════════════════════════════════
# 1. 洛书飞泊路径 + 五行生克基础
# ══════════════════════════════════════════════════════════════
_LUOSHU_FLY_PATH: list[str] = ["中", "乾", "兑", "艮", "离", "坎", "坤", "震", "巽"]

# 卦名 → 方位
_GUA_DIRECTION: dict[str, str] = {
    "乾": "西北", "兑": "西", "艮": "东北", "离": "南",
    "坎": "北", "坤": "西南", "震": "东", "巽": "东南", "中": "中宫",
}

# 后天卦序数 → 卦名
_NUM_TO_GUA: dict[int, str] = {
    1: "坎", 2: "坤", 3: "震", 4: "巽", 5: "中",
    6: "乾", 7: "兑", 8: "艮", 9: "离",
}

# 星 → 五行
_STAR_WUXING: dict[int, str] = {
    1: "水", 2: "土", 3: "木", 4: "木", 5: "土",
    6: "金", 7: "金", 8: "土", 9: "火",
}

# 五行生克关系
_WUXING_SHENG: dict[str, str] = {
    "金": "水", "水": "木", "木": "火", "火": "土", "土": "金",
}
_WUXING_KE: dict[str, str] = {
    "金": "木", "木": "土", "土": "水", "水": "火", "火": "金",
}


def _wuxing_relation(a_star: int, b_star: int) -> str:
    """返回 a 星对 b 星的五行关系（以星数查五行后比对）。

    Args:
        a_star: 星数 1-9 (代表运星)
        b_star: 星数 1-9 (代表年星)

    Returns:
        关系描述: 生入(a生b)/克出(a克b)/比和/生出(b生a)/克入(b克a)
    """
    a_wx = _STAR_WUXING.get(a_star, "土")
    b_wx = _STAR_WUXING.get(b_star, "土")
    if a_wx == b_wx:
        return "比和"
    if _WUXING_SHENG.get(a_wx) == b_wx:
        return "生入"  # a 生 b → 运生年为"泄"
    if _WUXING_KE.get(a_wx) == b_wx:
        return "克出"  # a 克 b → 运克年为"制"
    if _WUXING_SHENG.get(b_wx) == a_wx:
        return "生出"  # b 生 a → 年生运为"生入吉"
    if _WUXING_KE.get(b_wx) == a_wx:
        return "克入"  # b 克 a → 年克运为"煞"
    return "未知"


def _reduce_to_single_digit(n: int) -> int:
    """各位相加至个位数。"""
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def _compute_annual_center(year: int) -> int:
    """年紫白入中星 (1-9)。"""
    n = _reduce_to_single_digit(year)
    center = (11 - n) % 9
    return center if center != 0 else 9


def _fly_from_center(center: int, forward: bool = True) -> dict[str, int]:
    """从 center 入中飞泊九宫。forward=True 顺飞, False 逆飞。"""
    result: dict[str, int] = {}
    star = center
    step = 1 if forward else -1
    for gua in _LUOSHU_FLY_PATH:
        result[gua] = (star - 1) % 9 + 1
        star = (star - 1 + step) % 9 + 1
    return result


# ══════════════════════════════════════════════════════════════
# 2. 九宫位数据类
# ══════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class PalaceCell:
    """单宫飞星数据。"""
    gua: str                      # 卦名
    direction: str                # 方位
    yun_star: int                 # 运星
    annual_star: int              # 年星
    yun_wx: str                   # 运星五行
    annual_wx: str                # 年星五行
    yun_annual_relation: str      # 运星对年星: 生入/克出/比和/生出/克入
    annual_yun_relation: str      # 年星对运星: 生入(吉)/克入(煞)/比和/生出/克出
    assessment: str               # 吉凶判断


def _assess_palace(yun_star: int, annual_star: int) -> str:
    """判断某宫流年吉凶。

    年星生运星 = 生入吉; 年星与运星比和 = 旺; 运星生年星 = 泄;
    年星克运星 = 煞凶; 运星克年星 = 制平。
    """
    yw = _STAR_WUXING.get(yun_star, "土")
    aw = _STAR_WUXING.get(annual_star, "土")
    # 年星对运星
    if _WUXING_SHENG.get(aw) == yw:
        relation = "生入吉"
    elif aw == yw:
        relation = "比和旺"
    elif _WUXING_SHENG.get(yw) == aw:
        relation = "生出泄"
    elif _WUXING_KE.get(aw) == yw:
        relation = "克入煞"
    elif _WUXING_KE.get(yw) == aw:
        relation = "克出制"
    else:
        relation = "平"
    return relation


# ══════════════════════════════════════════════════════════════
# 3. 流年盘数据类
# ══════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class XuankongLiunianPan:
    """单个年份的玄空流年盘。

    Attributes:
        year: 公历年份
        period: 运数 (1-9)
        annual_center: 年紫白入中星
        yun_pan: {卦名: 运星} 运盘
        annual_pan: {卦名: 年星} 年盘
        palaces: {卦名: PalaceCell} 九宫叠合详情
        annual_center_nature: 年星性质描述
        auspicious_palaces: 该年吉宫列表
        inauspicious_palaces: 该年凶宫列表
        summary: 流年总评
    """
    year: int
    period: int
    annual_center: int
    yun_pan: dict[str, int] = field(default_factory=dict)
    annual_pan: dict[str, int] = field(default_factory=dict)
    palaces: dict[str, PalaceCell] = field(default_factory=dict)
    annual_center_nature: str = ""
    auspicious_palaces: list[str] = field(default_factory=list)
    inauspicious_palaces: list[str] = field(default_factory=list)
    summary: str = ""


# 年星性质描述
_ANNUAL_STAR_DESCRIPTIONS: dict[int, str] = {
    1: "一白水入中 — 人缘桃花旺，利文昌学业",
    2: "二黑土入中 — 防病符健康，宜静不宜动",
    3: "三碧木入中 — 是非口舌多，防官非争执",
    4: "四绿木入中 — 文昌星照，利考试升学",
    5: "五黄土入中 — 大煞入中，宜化解不宜动土",
    6: "六白金入中 — 权贵当令，利升迁偏财",
    7: "七赤金入中 — 破军当值，防盗贼口舌",
    8: "八白土入中 — 正财临宫，利置业投资",
    9: "九紫火入中 — 喜庆星临，利姻缘贵人",
}


def _build_liunian_pan(year: int, period: int) -> XuankongLiunianPan:
    """构建单一年份的玄空流年盘。

    算法：
      1. 运盘：当运星入中顺飞
      2. 年盘：年紫白入中顺飞
      3. 叠合：各宫运星 vs 年星 → 五行生克 → 吉凶判断
    """
    annual_center = _compute_annual_center(year)

    # 运盘: period 入中顺飞
    yun_pan = _fly_from_center(period, forward=True)
    # 年盘: 年紫白入中顺飞
    annual_pan = _fly_from_center(annual_center, forward=True)

    palaces: dict[str, PalaceCell] = {}
    auspicious_palaces: list[str] = []
    inauspicious_palaces: list[str] = []

    for gua in _LUOSHU_FLY_PATH:
        yun_star = yun_pan[gua]
        annual_star = annual_pan[gua]
        yun_wx = _STAR_WUXING.get(yun_star, "土")
        annual_wx = _STAR_WUXING.get(annual_star, "土")
        yun_annual_rel = _wuxing_relation(yun_star, annual_star)
        annual_yun_rel = _wuxing_relation(annual_star, yun_star)
        assessment = _assess_palace(yun_star, annual_star)

        direction = _GUA_DIRECTION.get(gua, gua)
        cell = PalaceCell(
            gua=gua,
            direction=direction,
            yun_star=yun_star,
            annual_star=annual_star,
            yun_wx=yun_wx,
            annual_wx=annual_wx,
            yun_annual_relation=yun_annual_rel,
            annual_yun_relation=annual_yun_rel,
            assessment=assessment,
        )
        palaces[gua] = cell

        if assessment in ("生入吉", "比和旺"):
            auspicious_palaces.append(f"{direction}({gua})")
        elif assessment in ("克入煞",):
            inauspicious_palaces.append(f"{direction}({gua})")

    # 流年总评
    center_cell = palaces["中"]
    ausp_count = len(auspicious_palaces)
    inausp_count = len(inauspicious_palaces)
    if ausp_count >= 5:
        tone = "流年大吉"
    elif inausp_count >= 4:
        tone = "流年多阻"
    elif ausp_count >= 3:
        tone = "流年平顺偏吉"
    else:
        tone = "流年平淡"

    summary_parts = [
        f"{year}年{period}运 {_ANNUAL_STAR_DESCRIPTIONS.get(annual_center, '')}",
        f"吉宫{ausp_count}处, 凶宫{inausp_count}处, {tone}",
    ]

    return XuankongLiunianPan(
        year=year,
        period=period,
        annual_center=annual_center,
        yun_pan=yun_pan,
        annual_pan=annual_pan,
        palaces=palaces,
        annual_center_nature=_ANNUAL_STAR_DESCRIPTIONS.get(annual_center, ""),
        auspicious_palaces=list(auspicious_palaces),
        inauspicious_palaces=list(inauspicious_palaces),
        summary="; ".join(summary_parts),
    )


# ══════════════════════════════════════════════════════════════
# 4. 八运/九运各 30 年流年盘数据
# ══════════════════════════════════════════════════════════════
# 八运: 2004–2023, 数据覆盖 2006–2035 (含跨运年份)
# 九运: 2024–2043, 数据覆盖 2024–2053

_PERIOD_8_YEARS: list[int] = list(range(2006, 2036))   # 30 年
_PERIOD_9_YEARS: list[int] = list(range(2024, 2054))   # 30 年

XUANKONG_LIUNIAN_8: dict[int, XuankongLiunianPan] = {
    year: _build_liunian_pan(year, 8) for year in _PERIOD_8_YEARS
}

XUANKONG_LIUNIAN_9: dict[int, XuankongLiunianPan] = {
    year: _build_liunian_pan(year, 9) for year in _PERIOD_9_YEARS
}

# 合并字典便于全量查询
XUANKONG_LIUNIAN_ALL: dict[tuple[int, int], XuankongLiunianPan] = {
    **{(year, 8): pan for year, pan in XUANKONG_LIUNIAN_8.items()},
    **{(year, 9): pan for year, pan in XUANKONG_LIUNIAN_9.items()},
}


# ══════════════════════════════════════════════════════════════
# 5. 查询函数
# ══════════════════════════════════════════════════════════════
def get_liunian_pan(year: int, period: int) -> XuankongLiunianPan | None:
    """查询指定年份和运数的玄空流年盘。"""
    return XUANKONG_LIUNIAN_ALL.get((year, period))


def get_liunian_by_period(period: int) -> dict[int, XuankongLiunianPan]:
    """获取某运全部 30 年流年盘。"""
    if period == 8:
        return dict(XUANKONG_LIUNIAN_8)
    elif period == 9:
        return dict(XUANKONG_LIUNIAN_9)
    return {}


def get_palace_detail(year: int, period: int, gua: str) -> PalaceCell | None:
    """查询某年某运某宫的详细飞星数据。"""
    pan = get_liunian_pan(year, period)
    if pan is None:
        return None
    return pan.palaces.get(gua)
