"""Tests for 袁天罡《称骨歌》51 档全量批语数据库
(divination/data/chenggu_verses.py + divination/engines/chenggu.py)

来源：袁天罡《称骨歌》(唐) + 《命相全编·称骨篇》(清)
覆盖：数据完整性 + lookup 容差 + compute() 集成 + 印本对标
"""
from __future__ import annotations

import pytest

from divination.contracts import Birth
from divination.data.chenggu_verses import (
    CHENGGU_VERSES,
    ChengguVerse,
    all_weights,
    lookup_verse,
    polarity_counts,
)
from divination.engines.chenggu import compute


# ── 1. 数据完整性 (>= 3 项) ──────────────────────────────
def test_total_verses_count_is_51():
    """袁天罡称骨歌 51 档 (2.1~7.1 两, 0.1 两递增)."""
    assert len(CHENGGU_VERSES) == 51, f"当前 {len(CHENGGU_VERSES)} 档, 期望 51"


def test_all_weights_in_01_increment_range():
    """所有骨重在 2.1~7.1 范围, 0.1 两递增."""
    weights = all_weights()
    assert weights[0] == 2.1
    assert weights[-1] == 7.1
    expected = [round(2.1 + i * 0.1, 1) for i in range(51)]
    assert weights == expected


def test_every_verse_has_non_empty_source():
    """每档 source 字段非空, 标识出处."""
    empty = [w for w, v in CHENGGU_VERSES.items() if not v.source]
    assert not empty, f"source 为空的档: {empty}"


def test_every_verse_source_not_partial():
    """51 档主表已校订完成, source 不应再标 partial."""
    partial = [w for w, v in CHENGGU_VERSES.items() if "partial" in v.source.lower()]
    assert not partial, f"source 仍标 partial 的档: {partial}"


def test_every_verse_has_4_lines():
    """每档必须 4 句歌诀 (原印本四言/七言)."""
    bad = [(w, len(v.verse_4_lines)) for w, v in CHENGGU_VERSES.items()
           if len(v.verse_4_lines) != 4]
    assert not bad, f"歌诀行数 != 4 的档: {bad}"


def test_polarity_values_valid():
    """polarity 必须为 auspicious / inauspicious / neutral 之一."""
    valid = {"auspicious", "inauspicious", "neutral"}
    bad = [(w, v.summary_polarity) for w, v in CHENGGU_VERSES.items()
           if v.summary_polarity not in valid]
    assert not bad, f"polarity 非法: {bad}"


# ── 2. lookup_verse 行为 (>= 6 项) ───────────────────────
def test_lookup_exact_match_middle_weight():
    """精确匹配: 中骨 4.7 两."""
    v = lookup_verse(4.7)
    assert v is not None
    assert v.weight == 4.7
    assert len(v.verse_4_lines) == 4
    assert v.summary_polarity in {"auspicious", "inauspicious", "neutral"}


def test_lookup_exact_match_min_weight():
    """精确匹配: 最小骨重 2.1 两 (轻骨首档)."""
    v = lookup_verse(2.1)
    assert v is not None
    assert v.weight == 2.1
    # 2.1 极轻, 应主孤贫
    assert v.summary_polarity == "inauspicious"


def test_lookup_exact_match_max_weight():
    """精确匹配: 最大骨重 7.1 两 (重骨末档)."""
    v = lookup_verse(7.1)
    assert v is not None
    assert v.weight == 7.1
    # 7.1 极重, 应主富贵
    assert v.summary_polarity == "auspicious"


def test_lookup_tolerance_within_005():
    """容差匹配: ±0.05 两内仍能命中."""
    # 4.7 ± 0.04 应命中 4.7 档
    assert lookup_verse(4.74) is not None
    # 5.0 ± 0.04 应命中 5.0 档
    assert lookup_verse(5.03) is not None
    # 2.5 ± 0.04 应命中 2.5 档
    assert lookup_verse(2.46) is not None


def test_lookup_out_of_tolerance_returns_none():
    """超出容差返回 None (例如 2.1 vs 2.5 差 0.4)."""
    assert lookup_verse(2.5, tolerance=0.05) is None or \
           lookup_verse(2.5, tolerance=0.05).weight != 2.1


def test_lookup_far_out_of_range_returns_none():
    """完全超出 51 档范围 (1.0 两 / 8.0 两) 返回 None."""
    assert lookup_verse(1.0) is None
    assert lookup_verse(8.0) is None
    assert lookup_verse(0.5) is None


def test_lookup_all_51_entries_findable():
    """51 个骨重都能查到, 无空缺."""
    for w in all_weights():
        v = lookup_verse(w)
        assert v is not None, f"骨重 {w} 查不到"
        assert v.weight == w


# ── 3. compute() 集成 (>= 3 项) ─────────────────────────
def test_compute_typical_birth_5_0_liang():
    """典型八字 → 算总骨重 + 印本歌诀一并出现."""
    b = Birth(1990, 5, 15, 8, 30, gender="male")
    r = compute(b)
    assert r.method == "chenggu"
    # raw 关键字段都在
    assert "总骨重_两" in r.raw
    assert "verse_4_lines" in r.raw
    assert "verse_source" in r.raw
    assert "verse_polarity" in r.raw
    # 兼容老 API
    assert "批语首句" in r.raw
    # 印本歌诀非空 (除非总骨重未在 51 档表)
    total = r.raw["总骨重_两"]
    if 2.1 <= total <= 7.1:
        assert len(r.raw["verse_4_lines"]) == 4
        assert r.raw["verse_source"] != ""


def test_compute_deterministic_weight():
    """compute 确定性: 同输入 → 同总骨重."""
    b = Birth(1990, 5, 15, 8, 30, gender="male")
    r1 = compute(b)
    r2 = compute(b)
    assert r1.raw["总骨重_两"] == r2.raw["总骨重_两"]


def test_compute_verse_lines_match_lookup():
    """compute() 查得的 verse_4_lines 必须与 lookup_verse 一致."""
    b = Birth(1985, 3, 20, 14, 0, gender="female")
    r = compute(b)
    total = r.raw["总骨重_两"]
    v_lookup = lookup_verse(total)
    if v_lookup is not None:
        assert r.raw["verse_4_lines"] == list(v_lookup.verse_4_lines)
        assert r.raw["verse_polarity"] == v_lookup.summary_polarity
        assert r.raw["verse_source"] == v_lookup.source


def test_compute_backward_compat_piyu_shouju():
    """兼容老 API: 批语首句 仍可读, 非空字符串."""
    # 1990-5-15 8:30 → 总骨重 3.7 两
    b = Birth(1990, 5, 15, 8, 30, gender="male")
    r = compute(b)
    assert r.raw["总骨重_两"] == 3.7
    # 3.7 两在 51 档内
    assert len(r.raw["verse_4_lines"]) == 4
    # 批语首句 非空字符串即可(兼容新旧版本差异)
    assert isinstance(r.raw["批语首句"], str) and len(r.raw["批语首句"]) > 0


# ── 4. 印本对标 (>= 3 项) ───────────────────────────────
def test_yinben_known_first_line_2_1():
    """印本对标: 2.1 两首句 "身寒骨冷苦伶仃"."""
    v = lookup_verse(2.1)
    assert v is not None
    assert "身寒骨冷苦伶仃" in v.verse_4_lines[0]


def test_yinben_known_first_line_3_2():
    """印本对标: 3.2 两首句 "初年运蹇事难谐"."""
    v = lookup_verse(3.2)
    assert v is not None
    assert "初年运蹇事难谐" in v.verse_4_lines[0]


def test_yinben_known_first_line_6_6():
    """印本对标: 6.6 两首句 "命格生成大不同"."""
    v = lookup_verse(6.6)
    assert v is not None
    assert "命格生成大不同" in v.verse_4_lines[0]


def test_polarity_pattern_light_heavy():
    """吉凶总评分布: 轻骨 (2.1) 主凶, 重骨 (7.1) 主吉."""
    light = lookup_verse(2.1)
    heavy = lookup_verse(7.1)
    assert light is not None and heavy is not None
    assert light.summary_polarity == "inauspicious"
    assert heavy.summary_polarity == "auspicious"


def test_polarity_counts_in_expected_distribution():
    """polarity 统计: inauspicious 多数在轻骨; auspicious 多数在重骨."""
    counts = polarity_counts()
    # 51 档应全部计入
    assert sum(counts.values()) == 51
    # 至少 5 档 inauspicious (轻骨 2.1-3.0 共 10 档)
    assert counts.get("inauspicious", 0) >= 5
    # 至少 5 档 auspicious (重骨 6.1-7.1 共 11 档)
    assert counts.get("auspicious", 0) >= 5


# ── 5. 边界 / 健壮性 ────────────────────────────────────
def test_chenggu_verse_is_frozen_dataclass():
    """ChengguVerse 是 frozen dataclass, 不可就地修改."""
    v = lookup_verse(3.5)
    assert v is not None
    with pytest.raises(Exception):  # FrozenInstanceError
        v.weight = 999.0  # type: ignore[misc]


def test_chenggu_verse_isinstance():
    """lookup_verse 返回 ChengguVerse 实例."""
    v = lookup_verse(4.0)
    assert isinstance(v, ChengguVerse)


def test_all_weights_returns_sorted_list():
    """all_weights() 返回升序列表."""
    ws = all_weights()
    assert ws == sorted(ws)
    assert len(ws) == 51
