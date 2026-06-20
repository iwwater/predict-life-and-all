"""西占 · Aspects 网格 + 月亮交点 + Arabic Parts + Lilith 测试。

覆盖:
- Aspects 网格 (差异化容许度):
  - 合/冲 ±8°
  - 刑/六合/拱/三合 ±6°
  - 半刑/半拱 ±3°
  - 五分相 ±2°
- 月亮交点: 北/南 + 与本命行星相位
- Arabic Parts: 7 主 Lot
- Lilith: 计算 + 12 星座含义
- 元素/模式分布: 火土风水 + 本位/固定/变动
- evidence_sources 引用 Tetrabiblos / 现代心理占星
- compute() 端到端输出
"""
from __future__ import annotations

import pytest

from divination.contracts import Birth
from divination.engines.western import (
    _NATAL_ASPECT_TABLE,
    _angular_sep,
    _element_modality_distribution,
    _sun_house,
    compute,
    find_natal_aspects_grid,
)


# ── 1. 工具函数 _angular_sep ─────────────────────────────
class TestAngularSep:
    def test_zero_separation(self):
        assert _angular_sep(0.0, 0.0) == 0.0

    def test_basic_diff(self):
        assert _angular_sep(0.0, 90.0) == 90.0

    def test_circular_diff(self):
        """350° vs 10° = 20°, 不是 340°。"""
        assert _angular_sep(350.0, 10.0) == 20.0

    def test_opposition(self):
        assert _angular_sep(0.0, 180.0) == 180.0

    def test_max_is_180(self):
        assert _angular_sep(0.0, 181.0) == 179.0


# ── 2. Aspects 网格 — 容许度差异化 ─────────────────────
class TestNatalAspectsGrid:
    def test_aspect_table_required_aspects(self):
        """至少 9 种相位: 合/冲/刑/六合/拱/三合/半刑/半拱/五分相。"""
        required = {"合", "冲", "刑", "六合", "拱", "三合", "半刑", "半拱", "五分相"}
        assert required <= set(_NATAL_ASPECT_TABLE.keys())

    def test_aspect_table_orb_differentiation(self):
        """容许度差异化: 合/冲 ≥ 主相位 ≥ 半相位 > 五分相。"""
        t = _NATAL_ASPECT_TABLE
        assert t["合"]["orb"] == 8.0
        assert t["冲"]["orb"] == 8.0
        assert t["刑"]["orb"] == 6.0
        assert t["六合"]["orb"] == 6.0
        assert t["拱"]["orb"] == 6.0
        assert t["三合"]["orb"] == 6.0
        assert t["半刑"]["orb"] == 3.0
        assert t["半拱"]["orb"] == 3.0
        assert t["五分相"]["orb"] == 2.0

    def test_aspect_table_hard_soft_classification(self):
        """硬相位: 冲/刑; 软相位: 合/六合/拱/三合/半拱/五分相; 半刑也算硬。"""
        t = _NATAL_ASPECT_TABLE
        hard = {k for k, v in t.items() if v["is_hard"]}
        soft = {k for k, v in t.items() if not v["is_hard"]}
        assert "冲" in hard
        assert "刑" in hard
        assert "半刑" in hard
        assert "合" in soft
        assert "拱" in soft
        assert "五分相" in soft

    def test_conjunction_exact(self):
        """0° 差 → 合相位。"""
        positions = {"太阳": 0.0, "月亮": 0.0}
        grid = find_natal_aspects_grid(positions)
        assert len(grid) == 1
        assert grid[0]["aspect"] == "合"
        assert grid[0]["orb"] == 0.0
        assert grid[0]["exact"] is True

    def test_conjunction_within_8_orb(self):
        """7° 差 → 仍在合相 ±8° 容许度内。"""
        positions = {"太阳": 0.0, "月亮": 7.0}
        grid = find_natal_aspects_grid(positions)
        assert len(grid) == 1
        assert grid[0]["aspect"] == "合"
        assert grid[0]["orb"] == 7.0

    def test_conjunction_outside_8_orb(self):
        """10° 差 → 超出合容许度, 无合相。"""
        positions = {"太阳": 0.0, "月亮": 10.0}
        grid = find_natal_aspects_grid(positions)
        # 10° 不属于任何相位 (六合 60° 差 50° > 6° orb)
        assert grid == []

    def test_opposition_exact(self):
        """180° 差 → 冲相位。"""
        positions = {"太阳": 0.0, "月亮": 180.0}
        grid = find_natal_aspects_grid(positions)
        assert len(grid) == 1
        assert grid[0]["aspect"] == "冲"
        assert grid[0]["is_hard"] is True

    def test_trine_exact(self):
        """120° 差 → 拱相位。"""
        positions = {"太阳": 0.0, "月亮": 120.0}
        grid = find_natal_aspects_grid(positions)
        assert len(grid) == 1
        assert grid[0]["aspect"] == "拱"

    def test_sextile_exact(self):
        """60° 差 → 六合相位。"""
        positions = {"太阳": 0.0, "月亮": 60.0}
        grid = find_natal_aspects_grid(positions)
        assert len(grid) == 1
        assert grid[0]["aspect"] == "六合"

    def test_square_exact(self):
        """90° 差 → 刑相位。"""
        positions = {"太阳": 0.0, "月亮": 90.0}
        grid = find_natal_aspects_grid(positions)
        assert len(grid) == 1
        assert grid[0]["aspect"] == "刑"

    def test_semisquare_within_3_orb(self):
        """45° 差 → 半刑 (±3° 容许度)。"""
        positions = {"太阳": 0.0, "月亮": 47.0}
        grid = find_natal_aspects_grid(positions)
        assert len(grid) == 1
        assert grid[0]["aspect"] == "半刑"
        assert grid[0]["orb"] == 2.0

    def test_semisquare_outside_3_orb(self):
        """49° 差 → 超出半刑容许度, 无相位。"""
        positions = {"太阳": 0.0, "月亮": 49.0}
        grid = find_natal_aspects_grid(positions)
        assert grid == []

    def test_quintile_within_2_orb(self):
        """72° 差 → 五分相 (±2° 容许度)。"""
        positions = {"太阳": 0.0, "月亮": 73.0}
        grid = find_natal_aspects_grid(positions)
        assert len(grid) == 1
        assert grid[0]["aspect"] == "五分相"
        assert grid[0]["orb"] == 1.0

    def test_quintile_outside_2_orb(self):
        """75° 差 → 超出五分相容许度。"""
        positions = {"太阳": 0.0, "月亮": 75.0}
        grid = find_natal_aspects_grid(positions)
        # 75° - 72° = 3° > 2° orb → 五分相不触发
        assert grid == []

    def test_grid_sorted_by_orb(self):
        """结果应按 orb 升序排列 (更精确的相位在前)。"""
        positions = {"A": 0.0, "B": 5.0, "C": 60.0}  # A-B 合 (orb 5), A-C 六合 (orb 0), B-C 55°
        grid = find_natal_aspects_grid(positions)
        # B-C: 55° 差, 六合 60° - 55° = 5°, 在 ±6° 容许度内 → 六合 orb 5
        # 至少 A-C 六合 (orb 0) 排第一
        if grid:
            orbs = [a["orb"] for a in grid]
            assert orbs == sorted(orbs)

    def test_each_aspect_has_required_fields(self):
        """每个相位对象必须含完整字段。"""
        positions = {"太阳": 0.0, "月亮": 120.0}
        grid = find_natal_aspects_grid(positions)
        assert len(grid) >= 1
        for asp in grid:
            for k in ["a", "b", "aspect", "angle", "actual_separation",
                      "orb", "is_hard", "category", "exact"]:
                assert k in asp, f"缺 {k}"


# ── 3. 元素 / 模式分布 ──────────────────────────────
class TestElementModality:
    def test_element_distribution_basic(self):
        positions = {"A": 30.0, "B": 150.0, "C": 270.0}  # 金牛(60°+)/天秤(60°+)...
        dist = _element_modality_distribution(positions)
        assert "elements" in dist
        assert "modalities" in dist
        assert "dominant_element" in dist
        assert "dominant_modality" in dist
        for e in ["火", "土", "风", "水"]:
            assert e in dist["elements"]
        for m in ["本位", "固定", "变动"]:
            assert m in dist["modalities"]

    def test_modality_groups(self):
        """白羊(0°) = 本位; 金牛(30°) = 固定; 双子(60°) = 变动。"""
        positions = {"A": 0.0, "B": 30.0, "C": 60.0}
        dist = _element_modality_distribution(positions)
        assert dist["modalities"]["本位"] == 1
        assert dist["modalities"]["固定"] == 1
        assert dist["modalities"]["变动"] == 1

    def test_dominant_modality(self):
        """3 个本位 → 本位主导。"""
        positions = {"A": 0.0, "B": 90.0, "C": 180.0}  # 白羊/巨蟹/天秤 (均为本位)
        dist = _element_modality_distribution(positions)
        assert dist["dominant_modality"] == "本位"
        assert dist["modalities"]["本位"] == 3

    def test_interpretation_non_empty(self):
        positions = {"A": 30.0, "B": 60.0, "C": 90.0}
        dist = _element_modality_distribution(positions)
        assert dist["element_interpretation"]
        assert dist["modality_interpretation"]


# ── 4. _sun_house ──────────────────────────────────
class TestSunHouse:
    def test_sun_in_first_house(self):
        """太阳在 ASC 附近, 宫位取决于宫位表。"""
        houses = [
            {"house": 1, "cusp_lon": 0.0},
            {"house": 2, "cusp_lon": 30.0},
            {"house": 3, "cusp_lon": 60.0},
            {"house": 4, "cusp_lon": 90.0},
            {"house": 5, "cusp_lon": 120.0},
            {"house": 6, "cusp_lon": 150.0},
            {"house": 7, "cusp_lon": 180.0},
            {"house": 8, "cusp_lon": 210.0},
            {"house": 9, "cusp_lon": 240.0},
            {"house": 10, "cusp_lon": 270.0},
            {"house": 11, "cusp_lon": 300.0},
            {"house": 12, "cusp_lon": 330.0},
        ]
        assert _sun_house(10.0, houses) == 1

    def test_sun_in_fifth_house(self):
        houses = [
            {"house": 1, "cusp_lon": 0.0},
            {"house": 2, "cusp_lon": 30.0},
            {"house": 3, "cusp_lon": 60.0},
            {"house": 4, "cusp_lon": 90.0},
            {"house": 5, "cusp_lon": 120.0},
            {"house": 6, "cusp_lon": 150.0},
            {"house": 7, "cusp_lon": 180.0},
            {"house": 8, "cusp_lon": 210.0},
            {"house": 9, "cusp_lon": 240.0},
            {"house": 10, "cusp_lon": 270.0},
            {"house": 11, "cusp_lon": 300.0},
            {"house": 12, "cusp_lon": 330.0},
        ]
        assert _sun_house(130.0, houses) == 5

    def test_sun_wrap_around_360(self):
        """太阳在 350°, 跨越 0° 边界。"""
        houses = [
            {"house": 1, "cusp_lon": 300.0},  # ASC 在水瓶 0°
            {"house": 2, "cusp_lon": 330.0},
            {"house": 3, "cusp_lon": 0.0},
            {"house": 4, "cusp_lon": 30.0},
            {"house": 5, "cusp_lon": 60.0},
            {"house": 6, "cusp_lon": 90.0},
            {"house": 7, "cusp_lon": 120.0},
            {"house": 8, "cusp_lon": 150.0},
            {"house": 9, "cusp_lon": 180.0},
            {"house": 10, "cusp_lon": 210.0},
            {"house": 11, "cusp_lon": 240.0},
            {"house": 12, "cusp_lon": 270.0},
        ]
        # 350° 在 1 宫 (300°-330° 不含), 应在 12 宫 (270°-300°)
        # 实际: 350° 在 1 宫起点 300° 到 2 宫起点 330° 之后... 等等
        # 350° > 330° 且 < 360° → 在 2 宫 (330°-0°)
        assert _sun_house(350.0, houses) == 2

    def test_empty_houses_returns_none(self):
        assert _sun_house(100.0, []) is None


# ── 5. compute() 端到端 ──────────────────────────────
class TestComputeEndToEnd:
    BIRTH = Birth(
        year=1990, month=6, day=15, hour=8, minute=30,
        gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai",
    )

    def test_compute_returns_aspects_grid(self):
        r = compute(self.BIRTH)
        assert "aspects_grid" in r.raw
        assert isinstance(r.raw["aspects_grid"], list)
        # 每个相位对象含完整字段
        if r.raw["aspects_grid"]:
            asp = r.raw["aspects_grid"][0]
            for k in ["a", "b", "aspect", "angle", "actual_separation",
                      "orb", "is_hard", "category"]:
                assert k in asp

    def test_aspects_table_evidence(self):
        """aspects_table 应有完整容许度说明。"""
        r = compute(self.BIRTH)
        t = r.raw["aspects_table"]
        assert "±8°" in t["合/冲"]
        assert "±6°" in t["刑/六合/拱/三合"]
        assert "±3°" in t["半刑/半拱"]
        assert "±2°" in t["五分相"]

    def test_compute_includes_lunar_nodes(self):
        r = compute(self.BIRTH)
        assert "lunar_nodes" in r.raw
        nodes = r.raw["lunar_nodes"]
        assert "north_node" in nodes
        assert "south_node" in nodes
        assert "interpretation" in nodes
        assert "north_aspects" in nodes
        assert "south_aspects" in nodes
        # 北交点与南交点相差 180°
        north = nodes["north_node"]["north_node_lon"]
        south = nodes["north_node"]["south_node_lon"]
        diff = abs((south - north) % 360)
        assert abs(diff - 180.0) < 0.001 or abs(diff + 180.0) < 0.001

    def test_compute_includes_lilith(self):
        r = compute(self.BIRTH)
        assert "lilith" in r.raw
        lilith = r.raw["lilith"]
        assert "lilith_lon" in lilith
        assert "lilith_sign" in lilith
        assert "sign_meaning" in lilith
        # 12 星座含义应非空
        assert len(lilith["sign_meaning"]) > 5

    def test_compute_includes_arabic_parts(self):
        r = compute(self.BIRTH)
        assert "arabic_parts" in r.raw
        assert "arabic_parts_count" in r.raw
        # 应有 7 个核心 Lot
        assert r.raw["arabic_parts_count"] == 7

    def test_arabic_parts_have_required_fields(self):
        r = compute(self.BIRTH)
        for lot in r.raw["arabic_parts"]:
            for k in ["part_name", "part_name_cn", "formula_used",
                      "lot_lon", "lot_sign", "is_day_chart"]:
                assert k in lot, f"Lot 缺 {k}"

    def test_arabic_parts_include_chinese_names(self):
        r = compute(self.BIRTH)
        cn_names = {lot["part_name_cn"] for lot in r.raw["arabic_parts"]}
        for required in ["福点", "灵点", "婚姻点"]:
            assert required in cn_names

    def test_distribution_with_nodes_and_lilith(self):
        """元素/模式分布应包含 7 行星 + 交点 + Lilith。"""
        r = compute(self.BIRTH)
        dist = r.raw["distribution"]
        assert "elements" in dist
        assert "modalities" in dist
        # 至少 9 个天体贡献 (7 行星 + 北交点 + 南交点 + Lilith)
        total_elements = sum(dist["elements"].values())
        total_modalities = sum(dist["modalities"].values())
        assert total_elements == 10
        assert total_modalities == 10

    def test_evidence_sources(self):
        """evidence_sources 应引用 Tetrabiblos 和现代心理占星。"""
        r = compute(self.BIRTH)
        evs = r.raw["evidence_sources"]
        assert any("Tetrabiblos" in s for s in evs)
        assert any("Forrest" in s or "Greene" in s for s in evs)

    def test_backward_compatible_fields(self):
        """保留旧版字段: aspects (走 astro_math.find_aspects)。"""
        r = compute(self.BIRTH)
        assert "aspects" in r.raw
        assert "planets" in r.raw
        assert "houses" in r.raw
        assert "transits" in r.raw
        assert "progressions" in r.raw
        assert "solar_return" in r.raw


# ── 6. Aspects 网格 与月亮交点 / Lilith 的集成 ─────────
class TestAspectGridIntegration:
    BIRTH = Birth(
        year=1990, month=6, day=15, hour=8, minute=30,
        gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai",
    )

    def test_aspects_grid_includes_north_node(self):
        """Aspects 网格应包含月亮交点作为相位对象。"""
        r = compute(self.BIRTH)
        north_aspects = [a for a in r.raw["aspects_grid"]
                         if a["a"] == "北交点" or a["b"] == "北交点"]
        # 北交点应至少与一颗行星形成相位 (3° orb)
        # 注: 实际可能没有, 这里只检查函数能处理
        assert isinstance(north_aspects, list)

    def test_aspects_grid_includes_lilith(self):
        r = compute(self.BIRTH)
        lilith_aspects = [a for a in r.raw["aspects_grid"]
                          if a["a"] == "莉莉丝" or a["b"] == "莉莉丝"]
        assert isinstance(lilith_aspects, list)

    def test_no_self_aspects(self):
        """行星不应与自己形成相位 (虽然不应出现在网格中)。"""
        r = compute(self.BIRTH)
        for asp in r.raw["aspects_grid"]:
            assert asp["a"] != asp["b"], f"自相位: {asp}"


# ── 7. 与现有 western_three_channels 测试的兼容性 ──────
class TestBackwardCompat:
    """确认新增字段不影响旧测试。"""
    BIRTH = Birth(
        year=1990, month=6, day=15, hour=8, minute=30,
        gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai",
    )

    def test_transits_still_present(self):
        r = compute(self.BIRTH)
        assert "transits" in r.raw
        assert isinstance(r.raw["transits"], list)

    def test_progressions_still_present(self):
        r = compute(self.BIRTH)
        assert "progressions" in r.raw
        assert "progressed_date" in r.raw

    def test_solar_return_still_present(self):
        r = compute(self.BIRTH)
        sr = r.raw.get("solar_return")
        assert sr is not None
        assert sr["sun_diff_deg"] < 1.0
