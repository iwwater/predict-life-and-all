"""Tests for 玄学法器与工具资料库 (divination/data/reference_equipment.py).

覆盖: 塔罗系统 + 签文 + 签筒 + 鲁班尺 + 法器 + 民俗物品
至少 10 项.
"""
from __future__ import annotations

import pytest

from divination.data.reference_equipment import (
    FOLK_ITEMS,
    GUANDI_QIAN,
    GUANYIN_QIAN,
    LUBAN_LUCKY_MM,
    LUBAN_SEGMENTS,
    QIANTONG_SPECS,
    RITUAL_TOOLS,
    TAROT_MEANING_DIFFS,
    TAROT_SYSTEMS,
    count_all_items,
    get_folk_items_by_category,
    get_luban_lucky_segments,
    get_luban_segment_for_mm,
    get_qian_by_category,
    get_qiantong_by_material,
    get_ritual_tools_by_category,
    get_tarot_system,
    get_tarot_system_names,
    search_guandi_qian,
    search_guanyin_qian,
)


# ── 1. 塔罗系统 ────────────────────────────────────────────
def test_tarot_three_systems_exist():
    """韦特/托特/现代 三系统必须存在."""
    assert "waite" in TAROT_SYSTEMS
    assert "thoth" in TAROT_SYSTEMS
    assert "modern" in TAROT_SYSTEMS


def test_tarot_each_has_78_cards():
    """三系统均为 78 张牌."""
    for key, sys in TAROT_SYSTEMS.items():
        assert sys.card_count == 78, f"{key} 牌数 {sys.card_count}"


def test_tarot_meaning_diffs_count():
    """牌义差异 >= 6 张代表性牌."""
    assert len(TAROT_MEANING_DIFFS) >= 6


def test_tarot_major_arcana_22():
    """三系统大阿卡那各 22 张."""
    for key, sys in TAROT_SYSTEMS.items():
        assert len(sys.major_arcana_names) == 22, f"{key} 大牌 {len(sys.major_arcana_names)}"


# ── 2. 签文 ────────────────────────────────────────────────
def test_guanyin_qian_count_100():
    """观音灵签 100 签."""
    assert len(GUANYIN_QIAN) == 100


def test_guandi_qian_count_100():
    """关帝灵签 100 签."""
    assert len(GUANDI_QIAN) == 100


def test_qian_categories_valid():
    """签文分类必须为: 上上/上/中/下/下下."""
    valid = {"上上", "上", "中", "下", "下下"}
    for q in GUANYIN_QIAN:
        assert q.category in valid, f"观音第{q.index}签 分类 {q.category} 非法"
    for q in GUANDI_QIAN:
        assert q.category in valid, f"关帝第{q.index}签 分类 {q.category} 非法"


def test_qian_search():
    """按序号查签."""
    g1 = search_guanyin_qian(1)
    assert g1 is not None
    assert "第一签" in g1.name
    d1 = search_guandi_qian(1)
    assert d1 is not None
    assert "第一签" in d1.name


def test_qian_by_category():
    """按分类筛选."""
    for cat in ["上上", "下下"]:
        items = get_qian_by_category(GUANYIN_QIAN, cat)
        assert len(items) > 0, f"观音签 {cat} 为空"


# ── 3. 签筒法器 ────────────────────────────────────────────
def test_qiantong_specs_count():
    """签筒规格 >= 6 种."""
    assert len(QIANTONG_SPECS) >= 6


def test_qiantong_material_filter():
    """按材料筛选."""
    bamboo = get_qiantong_by_material("竹")
    assert len(bamboo) >= 2
    metal = get_qiantong_by_material("金属")
    assert len(metal) >= 2


# ── 4. 鲁班尺 ──────────────────────────────────────────────
def test_luban_segments_count():
    """鲁班尺段位 >= 16 (两尺)."""
    assert len(LUBAN_SEGMENTS) >= 16


def test_luban_red_black_balance():
    """吉(红)段与凶(黑)段各半."""
    ji = [s for s in LUBAN_SEGMENTS if s.category == "吉"]
    xiong = [s for s in LUBAN_SEGMENTS if s.category == "凶"]
    assert len(ji) >= 8
    assert len(xiong) >= 8


def test_luban_lucky_mm_count():
    """常用吉数 >= 8."""
    assert len(LUBAN_LUCKY_MM) >= 8


def test_luban_segment_lookup():
    """按毫米查段位."""
    seg = get_luban_segment_for_mm(430)
    assert seg is not None
    assert seg.category == "吉"
    assert "财" in seg.name
    # 凶段
    seg2 = get_luban_segment_for_mm(80)
    assert seg2 is not None
    assert seg2.category == "凶"


# ── 5. 法器 ────────────────────────────────────────────────
def test_ritual_tools_count():
    """仪式法器 >= 18 件."""
    assert len(RITUAL_TOOLS) >= 18


def test_ritual_tools_categories():
    """法器分类覆盖: 令牌/法印/法铃/法剑/香炉/金刚杵/念珠."""
    for cat in ["令牌", "法印", "法铃", "法剑", "香炉", "金刚杵", "念珠"]:
        items = get_ritual_tools_by_category(cat)
        assert len(items) > 0, f"{cat} 类法器为空"


# ── 6. 民俗物品 ────────────────────────────────────────────
def test_folk_items_count():
    """民俗物品 >= 12 件."""
    assert len(FOLK_ITEMS) >= 13


def test_folk_items_categories():
    """分类覆盖: 水晶/葫芦/五帝钱."""
    for cat in ["水晶", "葫芦", "五帝钱", "罗盘"]:
        items = get_folk_items_by_category(cat)
        assert len(items) > 0, f"{cat} 类民俗物品为空"


# ── 7. 统计 ────────────────────────────────────────────────
def test_count_all_items():
    """统计函数正确返回各类计数."""
    counts = count_all_items()
    assert counts["tarot_systems"] == 3
    assert counts["guanyin_qian"] == 100
    assert counts["guandi_qian"] == 100
    assert counts["qiantong_specs"] >= 6
    assert counts["luban_segments"] >= 16
    assert counts["ritual_tools"] >= 18
    assert counts["folk_items"] >= 13


def test_dataclass_frozen():
    """资料库 dataclass 为 frozen."""
    from divination.data.reference_equipment import QianDraw, TarotSystemInfo
    t = get_tarot_system("waite")
    assert t is not None
    with pytest.raises(Exception):
        t.name = "test"  # type: ignore
