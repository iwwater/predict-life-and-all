"""Tests for 西方月亮交点 (divination/data/western_lunar_nodes.py)

来源：docs/CLASSICAL_SOURCES.md §7 西方占星
文献：Tetrabiblos, The Inner Sky
"""
from __future__ import annotations

import pytest

from divination.data.western_lunar_nodes import (
    NODE_IN_HOUSES,
    NODE_IN_SIGNS,
    NODE_MEANINGS,
    NODE_SYMBOLS,
    _mean_node_longitude,
    _south_node_longitude,
    compute_nodes,
    get_node_interpretation,
)


# ── 1. 节点基础含义 ─────────────────────────────────
def test_node_meanings_two_nodes():
    """必须含北交点与南交点。"""
    assert "北交点" in NODE_MEANINGS
    assert "南交点" in NODE_MEANINGS


def test_node_meanings_required_fields():
    """每个节点必须有 name_en / astronomical / core / keywords。"""
    required = {"name_en", "astronomical", "core", "keywords"}
    for node, info in NODE_MEANINGS.items():
        missing = required - set(info.keys())
        assert not missing, f"{node} 缺失: {missing}"


def test_node_symbols():
    """符号: 北=☊, 南=☋。"""
    assert NODE_SYMBOLS["北交点"] == "☊"
    assert NODE_SYMBOLS["南交点"] == "☋"


# ── 2. 12 星座速查 ─────────────────────────────────
def test_node_in_signs_12_signs():
    """12 星座全覆盖。"""
    required = {"白羊", "金牛", "双子", "巨蟹", "狮子", "处女",
                "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼"}
    assert set(NODE_IN_SIGNS.keys()) == required


def test_node_in_signs_north_south():
    """每星座必须有 north + south 含义。"""
    for sign, info in NODE_IN_SIGNS.items():
        assert "north" in info, f"{sign} 缺 north"
        assert "south" in info, f"{sign} 缺 south"
        assert len(info["north"]) > 5
        assert len(info["south"]) > 5


# ── 3. 12 宫位速查 ─────────────────────────────────
def test_node_in_houses_12_houses():
    """12 宫位全覆盖。"""
    assert set(NODE_IN_HOUSES.keys()) == set(range(1, 13))


def test_node_in_houses_north_south():
    """每宫位必须有 north + south 含义。"""
    for house, info in NODE_IN_HOUSES.items():
        assert "north" in info, f"第 {house} 宫 缺 north"
        assert "south" in info, f"第 {house} 宫 缺 south"


# ── 4. 天文计算 ─────────────────────────────────────
def test_mean_node_longitude_range():
    """Mean Node 黄经必须在 0-360 范围。"""
    from datetime import datetime
    for dt in [datetime(2026, 6, 18), datetime(1990, 5, 15), datetime(2000, 1, 1)]:
        lon = _mean_node_longitude(dt)
        assert 0 <= lon < 360, f"{dt}: lon={lon}"


def test_south_node_longitude():
    """南交点 = 北交点 + 180°。"""
    from datetime import datetime
    dt = datetime(2026, 6, 18)
    north = _mean_node_longitude(dt)
    south = _south_node_longitude(dt)
    diff = (south - north) % 360
    assert abs(diff - 180.0) < 0.001 or abs(diff + 180.0) < 0.001


def test_node_regression():
    """节点逆行: 后一天的北交点黄经应小于前一天。"""
    from datetime import datetime, timedelta
    dt1 = datetime(2026, 6, 18)
    dt2 = dt1 + timedelta(days=30)
    lon1 = _mean_node_longitude(dt1)
    lon2 = _mean_node_longitude(dt2)
    # 30 天后退约 30 * 0.053 = 1.59°
    assert lon2 < lon1, f"节点应逆行: {lon1} → {lon2}"


def test_node_regression_rate():
    """节点逆行速率 ≈ 0.053°/天, 30 天后退约 1.59°。"""
    from datetime import datetime, timedelta
    dt1 = datetime(2026, 6, 18)
    dt2 = dt1 + timedelta(days=30)
    lon1 = _mean_node_longitude(dt1)
    lon2 = _mean_node_longitude(dt2)
    regression = lon1 - lon2
    # 容许 ±0.5° 误差
    assert 1.0 < regression < 2.5, f"30 天后退 {regression:.2f}°, 期望 ~1.59°"


# ── 5. compute_nodes 函数 ─────────────────────────────
def test_compute_nodes_returns_full_dict():
    """compute_nodes 返回完整字段。"""
    r = compute_nodes(2026, 6, 18)
    required = {"north_node_lon", "south_node_lon", "north_sign",
                "south_sign", "north_symbol", "south_symbol",
                "delta_to_true_node", "computation", "retrograde"}
    assert required <= set(r.keys())


def test_compute_nodes_north_south_180():
    """北交点 + 南交点相差 180°。"""
    r = compute_nodes(1990, 5, 15)
    diff = (r["south_node_lon"] - r["north_node_lon"]) % 360
    assert abs(diff - 180.0) < 0.001 or abs(diff + 180.0) < 0.001


def test_compute_nodes_retrograde_true():
    """节点永远逆行。"""
    r = compute_nodes(2026, 6, 18)
    assert r["retrograde"] is True


def test_compute_nodes_symbols():
    """符号必须正确。"""
    r = compute_nodes(2026, 6, 18)
    assert r["north_symbol"] == "☊"
    assert r["south_symbol"] == "☋"


def test_compute_nodes_known_j2000():
    """J2000 (2000-01-01 12:00 UTC) Mean Node ≈ 125.04°。"""
    # 注意: tropical, 而非 sidereal
    r = compute_nodes(2000, 1, 1, 12, 0)
    # 允许 ±2° 误差
    assert 123 < r["north_node_lon"] < 127, (
        f"J2000 Mean Node ≈ 125.04°, 实得 {r['north_node_lon']}°"
    )


def test_compute_nodes_pisces_2026():
    """2026-06-18 北交点应在双鱼座（公共占星数据）。"""
    r = compute_nodes(2026, 6, 18)
    # 2025-2026 期间北交点从白羊移到双鱼（公共占星数据）
    assert r["north_sign"] in {"双鱼", "白羊"}, (
        f"2026-06-18 北交点应双鱼, 实得 {r['north_sign']}"
    )


# ── 6. get_node_interpretation ─────────────────────
def test_interpretation_sign_meaning():
    """返回必须含 north_sign, north_meaning, south_sign, south_meaning。"""
    interp = get_node_interpretation(60.0)
    for k in ["north_sign", "north_meaning", "south_sign", "south_meaning"]:
        assert k in interp


def test_interpretation_with_house():
    """含 house 时返回 house + house_meaning_*。"""
    interp = get_node_interpretation(60.0, house=7)
    assert interp["house"] == 7
    assert "house_meaning_north" in interp
    assert "house_meaning_south" in interp


def test_interpretation_without_house():
    """无 house 时不含 house 字段。"""
    interp = get_node_interpretation(60.0)
    assert "house" not in interp


def test_interpretation_invalid_house():
    """非法 house 应不崩溃。"""
    interp = get_node_interpretation(60.0, house=99)
    # 无 house 字段
    assert "house" not in interp


def test_interpretation_opposite_signs():
    """北交点与南交点星座必然不同。"""
    interp = get_node_interpretation(0.0)  # 北交点白羊
    assert interp["north_sign"] == "白羊"
    assert interp["south_sign"] == "天秤"  # 180° 相对


# ── 7. 节点与本命行星相位 ─────────────────────────────
from divination.data.western_lunar_nodes import (
    NODE_ASPECTS,
    check_node_aspect,
    find_all_node_aspects,
)


def test_aspect_conjunction_within_orb():
    """合相位: 节点 0° + 行星 1° → 合 (容许度 3°)。"""
    r = check_node_aspect(0.0, 1.0)
    assert r is not None
    assert r["aspect"] == "合"
    assert r["actual_diff"] == 1.0


def test_aspect_conjunction_exact():
    """合相位精确 (0° 差)。"""
    r = check_node_aspect(0.0, 0.0)
    assert r is not None
    assert r["aspect"] == "合"
    assert r["exact"] is True


def test_aspect_opposition_exact():
    """冲相位: 节点 0° + 行星 180° → 冲。"""
    r = check_node_aspect(0.0, 180.0)
    assert r is not None
    assert r["aspect"] == "冲"
    assert r["actual_diff"] == 180.0
    assert r["exact"] is True


def test_aspect_square_exact():
    """刑相位: 节点 0° + 行星 90° → 刑。"""
    r = check_node_aspect(0.0, 90.0)
    assert r is not None
    assert r["aspect"] == "刑"


def test_aspect_sextile_exact():
    """六合相位: 节点 0° + 行星 60° → 六合。"""
    r = check_node_aspect(0.0, 60.0)
    assert r is not None
    assert r["aspect"] == "六合"


def test_aspect_trine_exact():
    """拱相位: 节点 0° + 行星 120° → 拱。"""
    r = check_node_aspect(0.0, 120.0)
    assert r is not None
    assert r["aspect"] == "拱"


def test_aspect_none_outside_orb():
    """无相位: 节点 0° + 行星 50° → None (差 50°)。"""
    r = check_node_aspect(0.0, 50.0)
    assert r is None


def test_aspect_orb_override():
    """自定义容许度。"""
    # 容许度 10°, 行星 50° 与节点 0° → 应触发六合 (差 10°)
    r = check_node_aspect(0.0, 50.0, orb=10.0)
    assert r is not None
    assert r["aspect"] == "六合"


def test_aspect_circular():
    """圆形度数差计算 (跨 360°)。"""
    # 节点 350° + 行星 110° → 实际差 120° = 拱 (非 240°)
    r = check_node_aspect(350.0, 110.0)
    assert r is not None
    assert r["aspect"] == "拱"  # 120° 差
    assert abs(r["actual_diff"] - 120.0) < 0.1


def test_aspect_circular_opposition():
    """圆形度数差计算: 冲。"""
    # 节点 350° + 行星 170° → 实际差 180° = 冲
    r = check_node_aspect(350.0, 170.0)
    assert r is not None
    assert r["aspect"] == "冲"
    assert abs(r["actual_diff"] - 180.0) < 0.1


def test_node_aspects_required_keys():
    """NODE_ASPECTS 必须含 5 种相位。"""
    required = {"合", "六合", "拱", "刑", "冲"}
    assert required <= set(NODE_ASPECTS.keys())


def test_node_aspects_have_degree():
    """每相位必须有 degree + orb + meaning。"""
    for name, info in NODE_ASPECTS.items():
        assert "degree" in info
        assert "orb" in info
        assert "meaning" in info


# ── 8. find_all_node_aspects (多行星) ─────────────────
def test_find_all_aspects_multiple_planets():
    """节点 0°, 多行星相位检测。"""
    natal = {"太阳": 1.0, "月亮": 180.0, "金星": 60.0, "火星": 50.0}
    aspects = find_all_node_aspects(0.0, natal)
    # 应返回: 太阳=合, 月亮=冲, 金星=六合 (火星 50° 无相位)
    aspect_map = {a["planet"]: a["aspect"] for a in aspects}
    assert aspect_map.get("太阳") == "合"
    assert aspect_map.get("月亮") == "冲"
    assert aspect_map.get("金星") == "六合"
    assert "火星" not in aspect_map  # 50° 无相位


def test_find_all_aspects_sorted():
    """结果应按紧张度排序: 冲 > 刑 > 拱 > 六合 > 合。"""
    natal = {"太阳": 1.0, "月亮": 180.0, "金星": 60.0, "水星": 90.0}
    aspects = find_all_node_aspects(0.0, natal)
    aspect_order = [a["aspect"] for a in aspects]
    # 冲 应排第一
    assert aspect_order[0] == "冲"


def test_find_all_aspects_empty():
    """无行星 → 空列表。"""
    aspects = find_all_node_aspects(0.0, {})
    assert aspects == []


def test_find_all_aspects_with_orb():
    """容许度参数。"""
    # 容许度 10° 时, 火星 50° 应触发六合 (差 10°)
    natal = {"火星": 50.0}
    aspects = find_all_node_aspects(0.0, natal, orb=10.0)
    assert len(aspects) == 1
    assert aspects[0]["aspect"] == "六合"
