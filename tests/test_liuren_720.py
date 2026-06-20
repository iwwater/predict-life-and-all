"""Tests for 大六壬 720 课框架 (divination/data/liuren_720_lessons.py)

来源：docs/CLASSICAL_SOURCES.md §3 大六壬
对照：《大六壬指南》《大六壬大全》《毕法赋》已知课例
"""
from __future__ import annotations

import pytest

from divination.data.liuren_720_lessons import (
    EXTENDED_PATTERNS,
    KNOWN_LESSON_EXAMPLES,
    PATTERN_JUDGMENT,
    PATTERN_PRIORITY,
    SHEN_SHA_TABLE,
    classify_pattern_name,
    generate_720_lessons_basic,
    lookup_lesson_basic,
    run_verification,
)


# ── 1. 课体分类完整性 ─────────────────────────────────────────
def test_extended_patterns_count():
    """扩展课体至少 30 种（覆盖九宗门+主要课格）。"""
    assert len(EXTENDED_PATTERNS) >= 30, (
        f"扩展课体 {len(EXTENDED_PATTERNS)} 种, 期望 >= 30"
    )


def test_extended_patterns_categories():
    """至少包含 九宗门 / 课格 / 神煞格 / 贵神格 四个分类。"""
    cats = {info["category"] for info in EXTENDED_PATTERNS.values()}
    assert "九宗门" in cats
    assert "课格" in cats
    assert "神煞格" in cats
    assert "贵神格" in cats


def test_extended_patterns_polarity_valid():
    """所有 polarity 必须是 auspicious / inauspicious / neutral 之一。"""
    valid = {"auspicious", "inauspicious", "neutral"}
    for name, info in EXTENDED_PATTERNS.items():
        assert info["polarity"] in valid, f"{name} polarity={info['polarity']!r}"


def test_jiu_zong_men_complete():
    """九宗门全部 9 种必须存在。"""
    required = {"贼克", "比用", "涉害", "遥克", "昴星",
                "伏吟", "返吟", "别责", "八专"}
    missing = required - set(EXTENDED_PATTERNS.keys())
    assert not missing, f"九宗门缺失: {missing}"


# ── 2. 神煞表 ──────────────────────────────────────────────
def test_shen_sha_table_count():
    """神煞表至少 20 位常用神煞。"""
    assert len(SHEN_SHA_TABLE) >= 20, (
        f"神煞 {len(SHEN_SHA_TABLE)} 位, 期望 >= 20"
    )


def test_shen_sha_tian_yi():
    """天乙贵人起法正确: 甲戊庚牛羊（= 丑未）。"""
    sha = SHEN_SHA_TABLE["天乙贵人"]
    # 起法口诀用生肖别名（牛=丑、羊=未），须同时包含
    assert "甲" in sha["起法"] and "牛" in sha["起法"]
    assert "戊" in sha["起法"]
    assert sha["吉凶"] == "大吉"


def test_shen_sha_yi_ma():
    """驿马起法正确: 申子辰马寅。"""
    sha = SHEN_SHA_TABLE["驿马"]
    assert "申" in sha["起法"] and "子" in sha["起法"] and "辰" in sha["起法"]
    assert "寅" in sha["起法"]


# ── 3. 720 课生成器 ─────────────────────────────────────────
def test_generate_720_lessons_count():
    """720 课生成器必须精确返回 720 条。"""
    lessons = generate_720_lessons_basic()
    assert len(lessons) == 720, f"应为 720 课, 实得 {len(lessons)}"


def test_generate_720_first_and_last():
    """首课: 甲子日 子时 (课#1); 末课: 癸亥日 亥时 (课#720)。"""
    lessons = generate_720_lessons_basic()
    assert lessons[0]["day_ganzhi"] == "甲子"
    assert lessons[0]["hour_zhi"] == "子"
    assert lessons[0]["lesson_id"] == 1
    assert lessons[-1]["day_ganzhi"] == "癸亥"
    assert lessons[-1]["hour_zhi"] == "亥"
    assert lessons[-1]["lesson_id"] == 720


def test_generate_720_ganzhi_coverage():
    """720 课覆盖全部 60 花甲子 × 12 时辰（每个日柱 + 每个时辰至少出现一次）。"""
    lessons = generate_720_lessons_basic()
    ganzhi_seen = {l["day_ganzhi"] for l in lessons}
    hours_seen = {l["hour_zhi"] for l in lessons}
    assert len(ganzhi_seen) == 60, f"花甲子覆盖 {len(ganzhi_seen)}, 期望 60"
    assert len(hours_seen) == 12, f"时辰覆盖 {len(hours_seen)}, 期望 12"


# ── 4. 单课查询 ────────────────────────────────────────────
def test_lookup_jia_zi_chen():
    """甲子日 辰时 → 课#5（甲子日排第 1 柱, 辰时为第 5 个时辰）。"""
    info = lookup_lesson_basic("甲", "子", "辰")
    assert info["lesson_id"] == 5
    assert info["day_ganzhi"] == "甲子"
    assert info["kong"] == "戌亥"  # 甲子旬戌亥空


def test_lookup_wu_chen_chen():
    """戊辰日 辰时 → 课#53, 旬空=戌亥（戊辰在甲戌旬）。"""
    info = lookup_lesson_basic("戊", "辰", "辰")
    assert info["lesson_id"] == 53
    assert info["kong"] == "戌亥"


def test_lookup_ren_zi_zi():
    """壬子日 子时 → 课#577, 旬空=寅卯（壬子在甲寅旬）。"""
    info = lookup_lesson_basic("壬", "子", "子")
    assert info["lesson_id"] == 577
    assert info["kong"] == "寅卯"


def test_lookup_gui_ren():
    """甲日辰时（昼）→ 贵人=丑；子时（夜）→ 贵人=未。"""
    info_day = lookup_lesson_basic("甲", "子", "辰")  # 辰时 = 昼
    assert info_day["gui_ren_current"] == "丑"
    info_night = lookup_lesson_basic("甲", "子", "未")  # 未时 = 夜
    assert info_night["gui_ren_current"] == "未"


def test_lookup_invalid_day():
    """非法日柱应抛 ValueError。"""
    with pytest.raises(ValueError, match="无效日柱"):
        lookup_lesson_basic("X", "Y", "子")


def test_lookup_invalid_hour():
    """非法时辰应抛 ValueError。"""
    with pytest.raises(ValueError, match="无效时辰"):
        lookup_lesson_basic("甲", "子", "X")


# ── 5. 已知课例（来自《大六壬指南》《毕法赋》） ──────────────
def test_known_examples_count():
    """已知课例至少 8 例（覆盖九宗门主要 + 课格主要）。"""
    assert len(KNOWN_LESSON_EXAMPLES) >= 8


def test_run_verification_all_ok():
    """所有已知课例验证通过（lookup 不抛错）。"""
    results = run_verification()
    for r in results:
        assert r["ok"], f"{r['name']}: {r.get('error')}"
        assert "lesson_id" in r
        assert r["lesson_id"] >= 1 and r["lesson_id"] <= 720


def test_known_examples_unique_lessons():
    """已知课例的课序号唯一。"""
    results = run_verification()
    ids = [r["lesson_id"] for r in results if r["ok"]]
    assert len(set(ids)) == len(ids), f"重复课号: {ids}"


# ── 6. 课体自动分类 ────────────────────────────────────────
def test_classify_fuyin():
    """三传相同 → 伏吟。"""
    san_chuan = {"chu_chuan": "辰", "zhong_chuan": "辰", "mo_chuan": "辰", "method": "未知"}
    four_lessons = {"all_upper": ["辰"], "all_lower": ["辰"]}
    pattern = classify_pattern_name(san_chuan, four_lessons, [])
    assert pattern == "伏吟"


def test_classify_ba_zhuan():
    """method 含"八专" → 八专。"""
    san_chuan = {"chu_chuan": "子", "zhong_chuan": "丑", "mo_chuan": "寅", "method": "八专法"}
    pattern = classify_pattern_name(san_chuan, {"all_upper": [], "all_lower": []}, [])
    assert pattern == "八专"


def test_classify_shensha_priority():
    """神煞格优先级高于九宗门（当两者同时存在）。"""
    san_chuan = {"chu_chuan": "酉", "zhong_chuan": "辰", "mo_chuan": "巳",
                 "method": "贼克法"}
    pattern = classify_pattern_name(san_chuan, {"all_upper": [], "all_lower": []},
                                    ["天乙格"])
    assert pattern == "天乙格"


# ── 7. 速查表（PATTERN_JUDGMENT） ───────────────────────────
def test_judgment_table_contains_main():
    """速查表包含主要课格。"""
    required = ["三光", "三阳", "三阴", "伏吟", "返吟", "贼克", "比用"]
    missing = [k for k in required if k not in PATTERN_JUDGMENT]
    assert not missing, f"速查表缺失: {missing}"


# ── 8. 优先级表 ─────────────────────────────────────────────
def test_priority_table_no_duplicates():
    """优先级表无重复名。"""
    names = [name for name, _ in PATTERN_PRIORITY]
    duplicates = [n for n in names if names.count(n) > 1]
    assert not duplicates, f"优先级表重复: {set(duplicates)}"
