"""Tests for 八宅流年飞星 (bazhai_liunian) + 玄空流年盘 (xuankong_liunian)

文献：
  - 《八宅明镜》(清·箬冠道人) — 八宅
  - 《沈氏玄空学》(清·沈竹礽) — 玄空飞星
  - 《紫白诀》— 年紫白入中算法

Test coverage:
  - 八宅流年: 数据完整性 + 年星计算 + 方位查询 + 命卦交互
  - 玄空流年: 运盘正确性 + 年盘正确性 + 叠合生克 + 运年对比
"""
from __future__ import annotations

import pytest

# ── 八宅流年 imports ──
from divination.data.bazhai_liunian import (
    BAZHAI_LIUNIAN,
    BAZHAI_LIUNIAN_YEARS,
    BazhaiLiunianStar,
    _STAR_NATURE,
    _LUOSHU_FLY_PATH,
    _GUA_DIRECTION,
    _reduce_to_single_digit,
    _compute_annual_center,
    _fly_from_center,
    get_liunian_star,
    get_liunian_star_for_direction,
    get_liunian_range,
)
from divination.engines.bazhai import compute_liunian_stars

# ── 玄空流年 imports ──
from divination.data.xuankong_liunian import (
    XUANKONG_LIUNIAN_8,
    XUANKONG_LIUNIAN_9,
    XUANKONG_LIUNIAN_ALL,
    XuankongLiunianPan,
    PalaceCell,
    _STAR_WUXING as _XK_STAR_WUXING,
    _wuxing_relation,
    _assess_palace,
    _ANNUAL_STAR_DESCRIPTIONS,
    get_liunian_pan,
    get_liunian_by_period,
    get_palace_detail,
)
from divination.engines.xuankong import compute_liunian_pan


# ══════════════════════════════════════════════════════════════
# A. 八宅流年飞星 (8 tests)
# ══════════════════════════════════════════════════════════════
def test_bazhai_data_coverage_30_years():
    """八宅流年应涵盖 30 年。"""
    assert len(BAZHAI_LIUNIAN) == 30
    assert len(BAZHAI_LIUNIAN_YEARS) == 30


def test_bazhai_liunian_star_frozen():
    """BazhaiLiunianStar 应为 frozen dataclass。"""
    e = get_liunian_star(2024)
    assert isinstance(e, BazhaiLiunianStar)
    # frozen: 不可修改
    with pytest.raises(Exception):
        e.year = 2025  # type: ignore


def test_bazhai_annual_center_formula():
    """年紫白入中公式验证。

    2024: 2+0+2+4=8, (11-8)%9=3 → 三碧木
    2025: 2+0+2+5=9, (11-9)%9=2 → 二黑土
    2026: 2+0+2+6=10→1, (11-1)%9=1 → 一白水
    """
    assert _compute_annual_center(2024) == 3
    assert _compute_annual_center(2025) == 2
    assert _compute_annual_center(2026) == 1


def test_bazhai_liunian_star_years_range():
    """数据年份应从 2006 到 2035。"""
    assert min(BAZHAI_LIUNIAN_YEARS) == 2006
    assert max(BAZHAI_LIUNIAN_YEARS) == 2035


def test_bazhai_fly_path_complete():
    """洛书飞泊路径应有 9 宫。"""
    assert len(_LUOSHU_FLY_PATH) == 9
    assert _LUOSHU_FLY_PATH[0] == "中"


def test_bazhai_fly_from_center():
    """飞星: 3入中 → 乾4,兑5,艮6,离7,坎8,坤9,震1,巽2。"""
    result = _fly_from_center(3)
    assert result["中"] == 3
    assert result["乾"] == 4
    assert result["巽"] == 2
    # 验证循环
    assert result["坤"] == 9
    assert result["震"] == 1


def test_bazhai_three_white_2024():
    """2024 年三白星方位。"""
    e = get_liunian_star(2024)
    assert e is not None
    # 三白星 = 1,6,8
    assert len(e.three_white) == 3
    for star_name in e.three_white:
        assert any(s in star_name for s in ["一白", "六白", "八白"])


def test_bazhai_direction_query_2024():
    """按方位查询 2024 年飞星。"""
    r = get_liunian_star_for_direction(2024, "南")
    assert r is not None
    assert "star" in r
    assert "auspicious" in r
    assert r["year"] == 2024
    assert r["direction"] == "南"


def test_bazhai_liunian_range_filter():
    """年份区间过滤: 2020-2025 应有 6 年。"""
    subset = get_liunian_range(2020, 2025)
    assert len(subset) == 6
    assert 2020 in subset
    assert 2025 in subset


def test_bazhai_star_nature_completeness():
    """九星性质表应有 1-9 星。"""
    assert len(_STAR_NATURE) == 9
    for i in range(1, 10):
        assert i in _STAR_NATURE
        assert "name" in _STAR_NATURE[i]
        assert "element" in _STAR_NATURE[i]
        assert "auspicious" in _STAR_NATURE[i]


def test_bazhai_direction_mapping():
    """卦→方位映射应覆盖 9 宫。"""
    assert len(_GUA_DIRECTION) == 9
    assert _GUA_DIRECTION["坎"] == "北"
    assert _GUA_DIRECTION["离"] == "南"
    assert _GUA_DIRECTION["中"] == "中宫"


def test_bazhai_compute_liunian_stars_2024():
    """compute_liunian_stars(2024) 应返回完整结构。"""
    r = compute_liunian_stars(2024)
    assert r["year"] == 2024
    assert r["center_star"] == 3
    assert len(r["direction_stars"]) == 9
    assert len(r["bazhai_interactions"]) == 8  # 8 命卦
    # 每个命卦有 8 方向交互
    for gua in ["坎", "离", "震", "巽", "乾", "坤", "艮", "兑"]:
        assert gua in r["bazhai_interactions"]
        assert len(r["bazhai_interactions"][gua]) == 8


def test_bazhai_compute_liunian_stars_out_of_range():
    """超出范围的年份应返回 error。"""
    r = compute_liunian_stars(1990)
    assert "error" in r


# ══════════════════════════════════════════════════════════════
# B. 玄空流年盘 (12 tests)
# ══════════════════════════════════════════════════════════════
def test_xuankong_data_coverage_30_each():
    """八运和九运应各有 30 年数据。"""
    assert len(XUANKONG_LIUNIAN_8) == 30
    assert len(XUANKONG_LIUNIAN_9) == 30
    assert len(XUANKONG_LIUNIAN_ALL) == 60


def test_xuankong_8_yun_start_year():
    """八运数据应始于 2006。"""
    assert min(XUANKONG_LIUNIAN_8.keys()) == 2006


def test_xuankong_9_yun_start_year():
    """九运数据应始于 2024。"""
    assert min(XUANKONG_LIUNIAN_9.keys()) == 2024


def test_xuankong_pan_frozen():
    """XuankongLiunianPan 和 PalaceCell 应为 frozen dataclass。"""
    pan = get_liunian_pan(2024, 9)
    assert pan is not None
    with pytest.raises(Exception):
        pan.year = 2025  # type: ignore


def test_xuankong_annual_center_2024_2025():
    """年紫白入中验证: 2024→3, 2025→2。"""
    pan24 = get_liunian_pan(2024, 9)
    pan25 = get_liunian_pan(2025, 9)
    assert pan24 is not None
    assert pan25 is not None
    assert pan24.annual_center == 3
    assert pan25.annual_center == 2


def test_xuankong_yun_pan_period_9():
    """九运运盘: period=9 入中顺飞 → 中9→乾1→兑2→艮3→离4→坎5→坤6→震7→巽8。"""
    pan = get_liunian_pan(2024, 9)
    assert pan is not None
    assert pan.yun_pan["中"] == 9
    assert pan.yun_pan["乾"] == 1
    assert pan.yun_pan["离"] == 4


def test_xuankong_yun_pan_period_8():
    """八运运盘: period=8 入中顺飞。"""
    pan = get_liunian_pan(2006, 8)
    assert pan is not None
    assert pan.yun_pan["中"] == 8
    assert pan.yun_pan["乾"] == 9


def test_xuankong_9_palaces_complete():
    """九宫必须全部在场。"""
    pan = get_liunian_pan(2024, 9)
    assert pan is not None
    expected_gua = {"中", "乾", "兑", "艮", "离", "坎", "坤", "震", "巽"}
    assert set(pan.palaces.keys()) == expected_gua


def test_xuankong_palace_cell_has_all_fields():
    """PalaceCell 应含全部字段。"""
    pan = get_liunian_pan(2024, 9)
    assert pan is not None
    cell = pan.palaces["离"]
    assert cell.gua == "离"
    assert cell.direction == "南"
    assert cell.yun_star in range(1, 10)
    assert cell.annual_star in range(1, 10)
    assert cell.yun_wx in ("金", "木", "水", "火", "土")
    assert cell.annual_wx in ("金", "木", "水", "火", "土")
    assert cell.assessment in ("生入吉", "比和旺", "生出泄", "克入煞", "克出制", "平")


def test_xuankong_get_palace_detail():
    """get_palace_detail 应返回正确的 PalaceCell。"""
    cell = get_palace_detail(2024, 9, "坎")
    assert cell is not None
    assert cell.gua == "坎"
    assert cell.direction == "北"


def test_xuankong_wuxing_relation():
    """五行生克关系验证。"""
    # 6=金 1=水: 金生水 → 运生年=生入
    assert _wuxing_relation(6, 1) == "生入"
    # 3=木 2=土: 木克土 → 运克年=克出
    assert _wuxing_relation(3, 2) == "克出"
    # 2=土 5=土: 比和
    assert _wuxing_relation(2, 5) == "比和"
    # 1=水 6=金: 金生水 → 年生运=生出
    assert _wuxing_relation(1, 6) == "生出"
    # 2=土 3=木: 木克土 → 年克运=克入
    assert _wuxing_relation(2, 3) == "克入"


def test_xuankong_wuxing_distribution_2024():
    """2024九运的五行分布应合理。"""
    r = compute_liunian_pan(2024, 9)
    wxa = r["wuxing_analysis"]
    assert sum(wxa["yun_wuxing_distribution"].values()) == 9  # 9宫
    assert sum(wxa["annual_wuxing_distribution"].values()) == 9


def test_xuankong_lookup_missing_data():
    """查询无数据的 (year, period) 应返回 None。"""
    assert get_liunian_pan(1990, 8) is None
    assert get_liunian_pan(2024, 5) is None


def test_xuankong_compute_liunian_pan_2024():
    """compute_liunian_pan(2024, 9) 应返回完整结构。"""
    r = compute_liunian_pan(2024, 9)
    assert "error" not in r
    assert r["year"] == 2024
    assert r["period"] == 9
    assert len(r["palaces"]) == 9
    assert len(r["auspicious_palaces"]) >= 0
    assert len(r["inauspicious_palaces"]) >= 0
    assert "summary" in r
    assert r["annual_center_nature"] != ""


def test_xuankong_liunian_by_period():
    """按运查询: 八运30年, 九运30年。"""
    d8 = get_liunian_by_period(8)
    d9 = get_liunian_by_period(9)
    assert len(d8) == 30
    assert len(d9) == 30
    # 无数据的运
    assert get_liunian_by_period(5) == {}


def test_xuankong_summary_consistency():
    """每个流年盘的 summary 应非空。"""
    for year in [2024, 2025, 2026, 2030, 2040]:
        pan = get_liunian_pan(year, 9 if year >= 2024 else 8)
        if pan:
            assert pan.summary, f"Year {year} has empty summary"


def test_xuankong_star_wuxing_completeness():
    """星→五行映射应覆盖 1-9。"""
    assert len(_XK_STAR_WUXING) == 9
    for i in range(1, 10):
        assert i in _XK_STAR_WUXING
        assert _XK_STAR_WUXING[i] in ("金", "木", "水", "火", "土")


def test_xuankong_annual_star_descriptions():
    """九星入中描述应覆盖 1-9。"""
    assert len(_ANNUAL_STAR_DESCRIPTIONS) == 9
    for i in range(1, 10):
        assert i in _ANNUAL_STAR_DESCRIPTIONS
        assert len(_ANNUAL_STAR_DESCRIPTIONS[i]) > 0
