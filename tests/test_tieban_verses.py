"""Tests for 铁板神数条文数据库 (divination/data/tieban_verses.py)

来源：docs/CLASSICAL_SOURCES.md §5 铁板神数
覆盖：条文完整性 + 考刻分（父母生肖校验）
"""
from __future__ import annotations

import pytest

from divination.data.tieban_verses import (
    CHA_KE_FEN_MAP,
    TAIXUAN_NUM,
    TIANGAN_NUM,
    TIEBAN_VERSES,
    VERSE_SET_COUNT,
    YANG_ZHI,
    ZODIAC_NUM,
    compute_cha_ke_fen,
    get_category_names,
    get_total_verse_count,
    get_verse_count,
    lookup_verse_set_by_cha_ke,
)


# ── 1. 基础完整性 ──────────────────────────────────────────
def test_verse_set_count_at_least_8():
    """至少 8 个条文集 (1000-1799 + 1800-...)。"""
    assert len(TIEBAN_VERSES) >= 8


def test_total_verse_count_at_least_150():
    """总条文数 >= 150（扩展目标）。"""
    n = get_total_verse_count()
    assert n >= 150, f"当前 {n} 条, 期望 >= 150"


def test_categories_at_least_10():
    """分类数 >= 10（覆盖核心生活维度）。"""
    cats = get_category_names()
    assert len(cats) >= 10, f"当前 {len(cats)} 类, 期望 >= 10"


def test_core_categories_present():
    """核心 7 分类必须存在。"""
    required = {"父母", "兄弟", "夫妻", "子女", "财运", "官禄", "寿命"}
    cats = set(get_category_names())
    missing = required - cats
    assert not missing, f"核心分类缺失: {missing}"


def test_new_categories_present():
    """新增 6 分类必须存在。"""
    required = {"疾病", "出行", "流年", "田宅", "人际", "大运"}
    cats = set(get_category_names())
    missing = required - cats
    assert not missing, f"新增分类缺失: {missing}"


# ── 2. 条文编号与校验和 ────────────────────────────────────
def test_each_category_has_verses():
    """每个分类至少 8 条条文。"""
    for cat in get_category_names():
        n = get_verse_count().get(cat, 0)
        assert n >= 8, f"{cat}: 仅 {n} 条"


def test_verse_numbers_unique_within_category():
    """同一分类内, 条文编号必须唯一。"""
    for range_key, data in TIEBAN_VERSES.items():
        for cat, verses in data.get("categories", {}).items():
            numbers = [v["number"] for v in verses]
            assert len(set(numbers)) == len(numbers), (
                f"{range_key}/{cat}: 编号重复 {numbers}"
            )


def test_verse_numbers_sequential():
    """同一分类内, 条文编号从 1 开始连续。"""
    for range_key, data in TIEBAN_VERSES.items():
        for cat, verses in data.get("categories", {}).items():
            numbers = sorted(v["number"] for v in verses)
            if numbers:
                assert numbers[0] == 1, f"{range_key}/{cat}: 首编号={numbers[0]}"
                for i in range(1, len(numbers)):
                    assert numbers[i] == numbers[i - 1] + 1, (
                        f"{range_key}/{cat}: 跳号 {numbers[i - 1]}→{numbers[i]}"
                    )


def test_verse_checksum_range():
    """checksum 必须在 100-999 范围（3 位数）。"""
    for range_key, data in TIEBAN_VERSES.items():
        for cat, verses in data.get("categories", {}).items():
            for v in verses:
                cs = v["checksum"]
                assert 100 <= cs <= 999, f"{range_key}/{cat}/#{v['number']}: checksum={cs}"


def test_verse_text_not_empty():
    """所有条文必须有非空文本。"""
    for range_key, data in TIEBAN_VERSES.items():
        for cat, verses in data.get("categories", {}).items():
            for v in verses:
                assert v["text"] and len(v["text"]) > 5, (
                    f"{range_key}/{cat}/#{v['number']}: 文本过短"
                )


# ── 3. 父母生肖校验（考刻分） ─────────────────────────────
def test_zodiac_all_twelve():
    """生肖表必须包含全部 12 生肖。"""
    assert len(ZODIAC_NUM) == 12
    required = {"鼠", "牛", "虎", "兔", "龙", "蛇",
                "马", "羊", "猴", "鸡", "狗", "猪"}
    assert set(ZODIAC_NUM.keys()) == required


def test_cha_ke_fen_range():
    """考刻分必须在 0-11 范围。"""
    for fz in ZODIAC_NUM:
        for mz in ZODIAC_NUM:
            ck = compute_cha_ke_fen(fz, mz)
            assert 0 <= ck <= 11, f"父{fz}母{mz} → 考刻分={ck}"


def test_cha_ke_fen_determinism():
    """同一对父母生肖必须始终返回同一考刻分。"""
    ck1 = compute_cha_ke_fen("虎", "兔")
    ck2 = compute_cha_ke_fen("虎", "兔")
    assert ck1 == ck2


def test_cha_ke_fen_symmetry():
    """父 X + 母 Y = 父 Y + 母 X（对称性）。"""
    pairs = [("鼠", "牛"), ("虎", "蛇"), ("马", "羊"), ("猴", "鸡")]
    for f, m in pairs:
        ck_fm = compute_cha_ke_fen(f, m)
        ck_mf = compute_cha_ke_fen(m, f)
        assert ck_fm == ck_mf, f"{f}+{m} ({ck_fm}) != {m}+{f} ({ck_mf})"


def test_cha_ke_map_complete():
    """CHA_KE_FEN_MAP 必须覆盖 0-11 全部考刻分。"""
    for i in range(12):
        assert i in CHA_KE_FEN_MAP, f"考刻分 {i} 缺失映射"


def test_lookup_by_cha_ke_valid():
    """合法生肖组合必须返回完整结果。"""
    result = lookup_verse_set_by_cha_ke("虎", "兔")
    assert "cha_ke" in result
    assert "range" in result
    assert "verse_set" in result
    assert "categories" in result
    assert "desc" in result
    assert result["cha_ke"] == 7  # 3 + 4 = 7


def test_lookup_by_cha_ke_invalid_father():
    """非法父生肖应返回 error 字段。"""
    result = lookup_verse_set_by_cha_ke("xyz", "牛")
    assert "error" in result
    assert "父生肖" in result["error"]


def test_lookup_by_cha_ke_invalid_mother():
    """非法母生肖应返回 error 字段。"""
    result = lookup_verse_set_by_cha_ke("牛", "xyz")
    assert "error" in result
    assert "母生肖" in result["error"]


def test_lookup_by_cha_ke_returns_real_verses():
    """考刻分查找必须返回实际的条文（非空 categories）。"""
    for fz in ["鼠", "虎", "龙"]:
        for mz in ["牛", "兔", "蛇"]:
            result = lookup_verse_set_by_cha_ke(fz, mz)
            cats = result.get("categories", {})
            total = sum(len(v) for v in cats.values())
            assert total > 0, f"父{fz}母{mz} → 无条文"


# ── 4. 太玄数 / 天干数 ────────────────────────────────────
def test_tiangan_num_complete():
    """天干表必须含甲-癸 全部 10 天干。"""
    assert len(TIANGAN_NUM) == 10
    assert set(TIANGAN_NUM.keys()) == {"甲", "乙", "丙", "丁", "戊",
                                        "己", "庚", "辛", "壬", "癸"}


def test_taixuan_num_complete():
    """太玄数表必须覆盖 12 地支, 每个为 (阳数, 阴数) 二元组。"""
    required = {"子", "丑", "寅", "卯", "辰", "巳",
                "午", "未", "申", "酉", "戌", "亥"}
    assert set(TAIXUAN_NUM.keys()) == required
    for zhi, (yang, yin) in TAIXUAN_NUM.items():
        assert 1 <= yang <= 10, f"{zhi} 阳数={yang}"
        assert 1 <= yin <= 10, f"{zhi} 阴数={yin}"


def test_yang_zhi_six():
    """阳支必须为 6 个。"""
    assert len(YANG_ZHI) == 6
    expected = {"子", "寅", "辰", "午", "申", "戌"}
    assert YANG_ZHI == expected


# ── 5. 统计 ────────────────────────────────────────────────
def test_verse_count_distribution():
    """分类统计函数必须返回所有分类。"""
    counts = get_verse_count()
    cats = get_category_names()
    assert set(counts.keys()) == set(cats)


def test_total_count_consistent():
    """总条文数 = 各分类之和。"""
    counts = get_verse_count()
    assert sum(counts.values()) == get_total_verse_count()
