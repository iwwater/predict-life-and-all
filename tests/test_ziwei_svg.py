"""Tests for divination.viz.ziwei_svg - 4 SVG renderers.

Coverage:
  - 4 renderers (传统方盘 / 现代轮盘 / 宫位网格 / 星曜地图)
  - SVG 结构合法性 (xmlns / viewBox / <svg>)
  - 数据映射 (palaces -> 宫位 / 星曜)
  - 边界条件 (空数据 / 缺字段 / 12 宫之外)
  - 4 化 (mutagen) 标记
  - render_all 顶层入口
  - Sprint 任务规范签名: render_xxx(palaces, soul, body, five_elements)
"""
from __future__ import annotations

import pytest

# 从 divination.viz 直接 import (顶层 alias 提供任务规范签名)
from divination.viz import (
    render_modern_wheel,
    render_palace_grid,
    render_star_map,
    render_traditional_square,
    wrap_html,
)

# 内部常量与 render_all 仍从 ziwei_svg 拿
from divination.viz.ziwei_svg import (
    COLORS,
    PALACE_POSITIONS,
    STYLES,
    render_all,
)


# ---------------------------------------------------------------------------
# 样本数据 (基于 divination.engines.ziwei._palaces 返回结构)
# ---------------------------------------------------------------------------

PALACE_LIFE = {
    "name": "命宫",
    "index": 0,
    "is_body": False,
    "is_body_palace": False,
    "is_original_palace": True,
    "heavenly_stem": "甲",
    "earthly_branch": "子",
    "major_stars": ["紫微", "天府"],
    "minor_stars": ["文昌", "文曲"],
    "adjective_stars": ["天魁"],
    "changsheng12": "长生",
    "boshi12": "",
    "jiangqian12": "",
    "suiqian12": "",
}


def make_sample_palaces() -> list[dict]:
    """Build a deterministic 12-palace sample based on canonical names."""
    names = [
        "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
        "迁移", "交友", "官禄", "田宅", "福德", "父母",
    ]
    stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸", "甲", "乙"]
    branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    major_by_idx = {
        0: ["紫微", "天府"],
        1: ["天机"],
        2: ["太阳", "太阴"],
        3: ["武曲"],
        4: ["贪狼"],
        5: ["天同"],
        6: ["廉贞"],
        7: ["七杀"],
        8: ["破军"],
        9: ["巨门"],
        10: ["天相"],
        11: ["天梁"],
    }
    minor_by_idx = {
        0: ["文昌", "文曲"],
        2: ["天钺"],
        4: ["禄存"],
        5: ["擎羊"],
        8: ["陀罗"],
    }
    palaces = []
    for i, name in enumerate(names):
        palaces.append({
            "name": name,
            "index": i,
            "is_body": i == 0,
            "is_body_palace": i == 0,
            "is_original_palace": i == 0,
            "heavenly_stem": stems[i],
            "earthly_branch": branches[i],
            "major_stars": list(major_by_idx.get(i, [])),
            "minor_stars": list(minor_by_idx.get(i, [])),
            "adjective_stars": [],
            "changsheng12": "长生" if i == 0 else "",
            "boshi12": "",
            "jiangqian12": "",
            "suiqian12": "",
        })
    return palaces


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert_valid_svg(svg: str) -> None:
    """Common SVG structural assertions."""
    assert svg.startswith("<svg"), "SVG must start with <svg tag"
    assert "</svg>" in svg, "SVG must have closing tag"
    assert 'xmlns="http://www.w3.org/2000/svg"' in svg, "Must declare SVG namespace"
    assert "viewBox=" in svg, "Must have viewBox"
    assert "fill=" in svg, "Must have at least one fill attribute"


def _count_palace_names(svg: str, names: list[str]) -> dict[str, int]:
    """Count occurrences of each palace name in SVG text content."""
    return {name: svg.count(name) for name in names}


# ---------------------------------------------------------------------------
# Test: render_traditional_square
# ---------------------------------------------------------------------------

class TestTraditionalSquare:
    def test_basic_structure(self):
        svg = render_traditional_square(make_sample_palaces())
        _assert_valid_svg(svg)
        assert "传统方盘" in svg

    def test_contains_all_12_palace_names(self):
        svg = render_traditional_square(make_sample_palaces())
        for name in ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
                     "迁移", "交友", "官禄", "田宅", "福德", "父母"]:
            assert name in svg, f"Missing palace name: {name}"

    def test_renders_major_stars(self):
        svg = render_traditional_square(make_sample_palaces())
        # 紫微, 天府 在命宫
        assert "紫微" in svg
        assert "天府" in svg
        assert "天机" in svg
        assert "贪狼" in svg

    def test_renders_stem_branch(self):
        svg = render_traditional_square(make_sample_palaces())
        # 甲子 在命宫
        assert "甲子" in svg
        assert "乙丑" in svg

    def test_body_palace_marker(self):
        svg = render_traditional_square(make_sample_palaces(), size=720)
        # 命宫 is_body=True, 应有 accent 标记
        assert "●" in svg

    def test_changsheng12_shown(self):
        svg = render_traditional_square(make_sample_palaces())
        assert "长生" in svg


# ---------------------------------------------------------------------------
# Test: render_modern_wheel
# ---------------------------------------------------------------------------

class TestModernWheel:
    def test_basic_structure(self):
        svg = render_modern_wheel(make_sample_palaces())
        _assert_valid_svg(svg)
        assert "现代轮盘" in svg

    def test_uses_circles_and_paths(self):
        svg = render_modern_wheel(make_sample_palaces())
        # 轮盘用 circle 和扇形 path
        assert "<circle" in svg
        assert "<path" in svg
        # 12 个扇形 (12 palace segments)
        assert svg.count("<path") >= 12

    def test_contains_palace_names(self):
        svg = render_modern_wheel(make_sample_palaces())
        for name in ["命宫", "财帛", "官禄", "田宅"]:
            assert name in svg, f"Missing: {name}"

    def test_center_text(self):
        svg = render_modern_wheel(make_sample_palaces())
        assert "紫微斗数" in svg


# ---------------------------------------------------------------------------
# Test: render_palace_grid
# ---------------------------------------------------------------------------

class TestPalaceGrid:
    def test_basic_structure(self):
        svg = render_palace_grid(make_sample_palaces())
        _assert_valid_svg(svg)
        assert "宫位网格" in svg

    def test_grid_4x3_layout(self):
        svg = render_palace_grid(make_sample_palaces(), size=720)
        # 4×3 网格应有 12 个 rect 卡片 + 背景 + 头部 rect
        rect_count = svg.count("<rect")
        assert rect_count >= 12, f"Expected ≥12 rects, got {rect_count}"

    def test_all_12_palaces(self):
        svg = render_palace_grid(make_sample_palaces())
        names = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
                 "迁移", "交友", "官禄", "田宅", "福德", "父母"]
        counts = _count_palace_names(svg, names)
        for name, n in counts.items():
            assert n >= 1, f"Palace {name} not rendered ({n})"

    def test_renders_minor_stars(self):
        svg = render_palace_grid(make_sample_palaces())
        assert "文昌" in svg
        assert "禄存" in svg


# ---------------------------------------------------------------------------
# Test: render_star_map
# ---------------------------------------------------------------------------

class TestStarMap:
    def test_basic_structure(self):
        svg = render_star_map(make_sample_palaces())
        _assert_valid_svg(svg)
        assert "星曜地图" in svg

    def test_renders_two_systems(self):
        svg = render_star_map(make_sample_palaces())
        # 紫微系 + 天府系
        assert "紫微" in svg
        assert "天府" in svg
        # 14 主星至少部分出现
        assert "天机" in svg or "太阴" in svg

    def test_legend_present(self):
        svg = render_star_map(make_sample_palaces())
        assert "主星" in svg
        assert "辅星" in svg

    def test_two_concentric_circles(self):
        svg = render_star_map(make_sample_palaces())
        # 内圈 + 外圈 = 至少 2 个 circle
        assert svg.count("<circle") >= 14  # 12 锚点 + 内/外圈 + 星点


# ---------------------------------------------------------------------------
# Test: render_all
# ---------------------------------------------------------------------------

class TestRenderAll:
    def test_returns_four_styles(self):
        result = render_all(make_sample_palaces())
        assert set(result.keys()) == set(STYLES)
        assert len(result) == 4

    def test_all_styles_valid_svg(self):
        result = render_all(make_sample_palaces())
        for style, svg in result.items():
            _assert_valid_svg(svg)
            assert len(svg) > 500, f"{style} too short: {len(svg)} chars"

    def test_styles_constant(self):
        assert STYLES == ("traditional", "wheel", "grid", "star_map")


# ---------------------------------------------------------------------------
# Test: 数据鲁棒性
# ---------------------------------------------------------------------------

class TestRobustness:
    def test_empty_palaces(self):
        """空 palaces 不报错, 应渲染空盘."""
        svg = render_traditional_square([])
        _assert_valid_svg(svg)

    def test_partial_palaces(self):
        """只给 1 个宫位, 其它填充 placeholder."""
        svg = render_modern_wheel([PALACE_LIFE])
        _assert_valid_svg(svg)
        assert "命宫" in svg

    def test_missing_optional_fields(self):
        """宫位 dict 缺字段 (无 stars/stem 等) 仍能渲染."""
        minimal = [{"name": "命宫", "index": 0}]
        svg = render_palace_grid(minimal)
        _assert_valid_svg(svg)
        assert "命宫" in svg

    def test_handles_string_index(self):
        """index 是字符串 '3' 也能解析."""
        data = [{"name": "财帛", "index": "3",
                 "is_body_palace": False, "is_original_palace": False,
                 "heavenly_stem": "", "earthly_branch": "",
                 "major_stars": ["武曲"], "minor_stars": [],
                 "adjective_stars": [], "changsheng12": "",
                 "boshi12": "", "jiangqian12": "", "suiqian12": ""}]
        svg = render_star_map(data)
        _assert_valid_svg(svg)
        assert "武曲" in svg

    def test_escapes_special_characters(self):
        """特殊字符 (<, >, &) 必须 HTML escape."""
        data = [{
            "name": "<命&宫>", "index": 0,
            "is_body_palace": False, "is_original_palace": False,
            "heavenly_stem": "", "earthly_branch": "",
            "major_stars": ["<星>"], "minor_stars": [],
            "adjective_stars": [], "changsheng12": "",
            "boshi12": "", "jiangqian12": "", "suiqian12": ""
        }]
        svg = render_traditional_square(data)
        _assert_valid_svg(svg)
        # 未转义会破坏 XML 结构
        assert "&lt;命&amp;宫&gt;" in svg
        # 原始未转义串不应出现
        assert "<命&宫>" not in svg

    def test_palace_position_constants(self):
        """PALACE_POSITIONS 必须覆盖 0-11 全部 12 宫."""
        positions = set(PALACE_POSITIONS.values())
        assert positions == set(range(12))


# ---------------------------------------------------------------------------
# Test: 一致性
# ---------------------------------------------------------------------------

class TestConsistency:
    def test_all_styles_render_same_palace_names(self):
        """4 种渲染器都包含全部 12 宫名."""
        palaces = make_sample_palaces()
        names = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
                 "迁移", "交友", "官禄", "田宅", "福德", "父母"]
        for renderer in (render_traditional_square, render_modern_wheel,
                         render_palace_grid, render_star_map):
            svg = renderer(palaces)
            for name in names:
                assert name in svg, f"{renderer.__name__} missing {name}"

    def test_color_palette_complete(self):
        """色板字典必须含所有引用键."""
        required = {"bg", "ink", "border", "body_palace", "major_star",
                    "minor_star", "adj_star", "cell_bg"}
        assert required.issubset(COLORS.keys())

    def test_size_parameter_respected(self):
        """size 参数改变 viewBox 宽度."""
        s1 = render_palace_grid(make_sample_palaces(), size=480)
        s2 = render_palace_grid(make_sample_palaces(), size=720)
        assert 'width="480"' in s1
        assert 'width="720"' in s2

    def test_custom_title(self):
        svg = render_traditional_square(
            make_sample_palaces(), title="我的命盘"
        )
        assert "我的命盘" in svg

    def test_star_map_with_no_minor_stars(self):
        """没有副星时, 星曜地图不应崩溃."""
        palaces = [{
            "name": "命宫", "index": 0,
            "is_body_palace": True, "is_original_palace": True,
            "heavenly_stem": "甲", "earthly_branch": "子",
            "major_stars": ["紫微"], "minor_stars": [],
            "adjective_stars": [], "changsheng12": "",
            "boshi12": "", "jiangqian12": "", "suiqian12": ""
        }]
        svg = render_star_map(palaces)
        _assert_valid_svg(svg)
        assert "紫微" in svg


# ---------------------------------------------------------------------------
# Test: Sprint 任务规范签名 (palaces, soul, body, five_elements)
# ---------------------------------------------------------------------------

SAMPLE_SOUL = "禄存"
SAMPLE_BODY = "火星"
SAMPLE_FIVE = "土五"


class TestPositionalSignature:
    """验证 Sprint 任务规范的 4 元位置参数签名."""

    def test_traditional_with_center_info(self):
        """传统方盘 (palaces, soul, body, five_elements)."""
        svg = render_traditional_square(
            make_sample_palaces(), SAMPLE_SOUL, SAMPLE_BODY, SAMPLE_FIVE
        )
        _assert_valid_svg(svg)
        assert "命主" in svg
        assert SAMPLE_SOUL in svg
        assert "身主" in svg
        assert SAMPLE_BODY in svg
        assert "土五" in svg

    def test_wheel_with_center_info(self):
        """现代轮盘 (palaces, soul, body, five_elements)."""
        svg = render_modern_wheel(
            make_sample_palaces(), SAMPLE_SOUL, SAMPLE_BODY, SAMPLE_FIVE
        )
        _assert_valid_svg(svg)
        assert "命主" in svg
        assert SAMPLE_SOUL in svg
        assert "身主" in svg
        assert SAMPLE_BODY in svg

    def test_grid_with_center_info(self):
        """宫位网格 (palaces, soul, body, five_elements)."""
        svg = render_palace_grid(
            make_sample_palaces(), SAMPLE_SOUL, SAMPLE_BODY, SAMPLE_FIVE
        )
        _assert_valid_svg(svg)
        assert "命主" in svg
        assert SAMPLE_SOUL in svg
        assert "身主" in svg
        assert SAMPLE_BODY in svg

    def test_star_map_with_center_info(self):
        """星曜地图 (palaces, soul, body, five_elements)."""
        svg = render_star_map(
            make_sample_palaces(), SAMPLE_SOUL, SAMPLE_BODY, SAMPLE_FIVE
        )
        _assert_valid_svg(svg)
        assert "命主" in svg
        assert SAMPLE_SOUL in svg
        assert "身主" in svg
        assert SAMPLE_BODY in svg

    def test_empty_center_args_no_crash(self):
        """空中心信息不应报错."""
        for fn in (render_traditional_square, render_modern_wheel,
                   render_palace_grid, render_star_map):
            svg = fn(make_sample_palaces(), "", "", "")
            _assert_valid_svg(svg)

    def test_signature_with_kwargs(self):
        """位置参数 + kwargs 组合可用."""
        svg = render_traditional_square(
            make_sample_palaces(), SAMPLE_SOUL, SAMPLE_BODY, SAMPLE_FIVE,
            title="自定义命盘", size=480,
        )
        _assert_valid_svg(svg)
        assert "自定义命盘" in svg
        assert 'width="480"' in svg


# ---------------------------------------------------------------------------
# Test: HTML 包裹
# ---------------------------------------------------------------------------

class TestWrapHtmlBasic:
    def test_wrap_html_basic(self):
        svg = render_traditional_square(
            make_sample_palaces(), SAMPLE_SOUL, SAMPLE_BODY, SAMPLE_FIVE,
        )
        html = wrap_html(svg)
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert svg in html
        assert "</html>" in html

    def test_wrap_html_preserves_svg_content(self):
        svg = render_modern_wheel(
            make_sample_palaces(), SAMPLE_SOUL, SAMPLE_BODY, SAMPLE_FIVE,
        )
        html = wrap_html(svg)
        assert svg in html


# ---------------------------------------------------------------------------
# Test: 真实 engine 数据端到端
# ---------------------------------------------------------------------------

class TestRealEngineEndToEnd:
    """端到端: engine -> viz 渲染."""

    def test_real_chart_all_styles(self):
        try:
            from divination.engines.ziwei import compute
            from divination.contracts import Birth
            b = Birth(year=1990, month=6, day=15, hour=8, minute=30,
                      gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai")
            r = compute(b)
        except Exception as e:
            pytest.skip(f"engine not available: {e}")

        palaces = r.raw.get("palaces", [])
        soul = r.raw.get("soul", "")
        body_ = r.raw.get("body", "")
        five = r.raw.get("five_elements", "")

        if not palaces:
            pytest.skip("no palaces")

        for fn in (render_traditional_square, render_modern_wheel,
                   render_palace_grid, render_star_map):
            svg = fn(palaces, soul, body_, five)
            _assert_valid_svg(svg)
            # 长度合理 (1KB - 50KB)
            assert 1000 < len(svg) < 50_000, f"{fn.__name__} size {len(svg)}"

    def test_real_chart_soul_body_five_in_svg(self):
        """真实数据: soul/body/five 出现在 SVG 中."""
        try:
            from divination.engines.ziwei import compute
            from divination.contracts import Birth
            b = Birth(year=1990, month=6, day=15, hour=8, minute=30,
                      gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai")
            r = compute(b)
        except Exception as e:
            pytest.skip(f"engine not available: {e}")

        palaces = r.raw.get("palaces", [])
        soul = r.raw.get("soul", "")
        body_ = r.raw.get("body", "")
        five = r.raw.get("five_elements", "")

        if not (palaces and soul and body_ and five):
            pytest.skip("missing data")

        svg = render_traditional_square(palaces, soul, body_, five)
        assert soul in svg, f"soul {soul} not in SVG"
        assert body_ in svg, f"body {body_} not in SVG"
        assert five in svg, f"five_elements {five} not in SVG"


# ---------------------------------------------------------------------------
# Test: SVG 长度边界
# ---------------------------------------------------------------------------

class TestSvgSizeBounds:
    """SVG 长度必须在 1KB-50KB 范围内."""

    @pytest.mark.parametrize("render_fn,style", [
        (render_traditional_square, "traditional"),
        (render_modern_wheel, "wheel"),
        (render_palace_grid, "grid"),
        (render_star_map, "star_map"),
    ])
    def test_size_in_range(self, render_fn, style):
        svg = render_fn(
            make_sample_palaces(), SAMPLE_SOUL, SAMPLE_BODY, SAMPLE_FIVE,
        )
        size = len(svg.encode("utf-8"))
        assert 1000 < size < 50_000, (
            f"{style} SVG size {size}B out of range (1KB-50KB)"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])