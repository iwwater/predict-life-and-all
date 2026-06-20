"""Tests for 蓍草变爻辞 (divination/data/shicao_yao_ci.py + divination/engines/shicao.py)

文献：
  - 《周易》本经卦爻辞
  - 《易传》(十翼) 彖传/象传

Test coverage:
  - 数据完整性: 128+ 条目, 30+ 完整录入
  - 查询功能: lookup_changed_yao_ci() + integrate_yao_ci()
  - 内容验证: 爻辞 + 象辞 + 解读的正确性
  - 卦序一致性
"""
from __future__ import annotations

import pytest

from divination.data.shicao_yao_ci import (
    SHICAO_YAO_CI,
    ChangedYaoCi,
    _HEXAGRAM_ORDER,
    _HEXAGRAM_NUM,
    _RAW_YAO_CI,
    lookup_changed_yao_ci,
    lookup_by_hexagram,
    get_all_entries,
    get_complete_count,
    get_total_entries,
)
from divination.engines.shicao import (
    lookup_changed_yao_ci as engine_lookup,
    integrate_yao_ci,
    lookup_by_hexagram as engine_lookup_by_hexagram,
    _line_label,
)


# ══════════════════════════════════════════════════════════════
# 1. 数据完整性
# ══════════════════════════════════════════════════════════════
def test_total_entries_at_least_128():
    """总条目数应 >= 128 (64卦×2状态)。"""
    assert get_total_entries() >= 128


def test_complete_entries_at_least_30():
    """完整录入条目（含 interpretation）应 >= 30。"""
    assert get_complete_count() >= 30


def test_hexagram_order_64():
    """序列表应含 64 卦。"""
    assert len(_HEXAGRAM_ORDER) == 64
    assert _HEXAGRAM_ORDER[0] == "乾"
    assert _HEXAGRAM_ORDER[1] == "坤"
    assert _HEXAGRAM_ORDER[-1] == "未济"


def test_hexagram_numbers_1_to_64():
    """卦序号应 1-64 连续。"""
    nums = set(_HEXAGRAM_NUM.values())
    assert nums == set(range(1, 65))


def test_all_entries_have_required_fields():
    """每个条目应有全部基本字段。"""
    for key, entry in SHICAO_YAO_CI.items():
        assert entry.hexagram_num in range(1, 65), f"{key}: bad hexagram_num"
        assert entry.hexagram_name in _HEXAGRAM_ORDER, f"{key}: unknown name"
        assert entry.line_num in range(1, 7), f"{key}: bad line_num"
        assert isinstance(entry.is_yang_old, bool), f"{key}: bad is_yang_old"
        assert len(entry.yao_ci) > 0, f"{key}: empty yao_ci"
        assert entry.source == "《周易》"


def test_hexagram_names_match_order():
    """所有条目的卦名应在序列表中。"""
    for key, entry in SHICAO_YAO_CI.items():
        assert entry.hexagram_name in _HEXAGRAM_NUM
        assert _HEXAGRAM_NUM[entry.hexagram_name] == entry.hexagram_num


# ══════════════════════════════════════════════════════════════
# 2. 查询功能 — 数据层
# ══════════════════════════════════════════════════════════════
def test_lookup_qian_chu_jiu():
    """乾初九: 潜龙勿用。"""
    e = lookup_changed_yao_ci("乾", 1, True)
    assert e is not None
    assert e.hexagram_name == "乾"
    assert e.line_num == 1
    assert e.is_yang_old is True
    assert "潜龙勿用" in e.yao_ci
    assert len(e.xiang_ci) > 0
    assert len(e.interpretation) > 0


def test_lookup_qian_chu_liu():
    """乾初六(老阴): 同样潜龙勿用, 但解读不同。"""
    e = lookup_changed_yao_ci("乾", 1, False)
    assert e is not None
    assert e.is_yang_old is False
    assert "潜龙勿用" in e.yao_ci
    assert "阴极阳生" in e.interpretation or "老阴" in e.interpretation


def test_lookup_qian_jiu_wu():
    """乾九五: 飞龙在天。"""
    e = lookup_changed_yao_ci("乾", 5, True)
    assert e is not None
    assert "飞龙在天" in e.yao_ci
    assert "利见大人" in e.yao_ci


def test_lookup_qian_shang_jiu():
    """乾上九: 亢龙有悔。"""
    e = lookup_changed_yao_ci("乾", 6, True)
    assert e is not None
    assert "亢龙有悔" in e.yao_ci


def test_lookup_kun_liu_wu():
    """坤六五: 黄裳元吉。"""
    e = lookup_changed_yao_ci("坤", 5, True)
    assert e is not None
    assert "黄裳" in e.yao_ci


def test_lookup_kun_shang_liu():
    """坤上六: 龙战于野。"""
    e = lookup_changed_yao_ci("坤", 6, True)
    assert e is not None
    assert "龙战于野" in e.yao_ci


def test_lookup_nonexistent():
    """查询不存在的条目应返回 None。"""
    assert lookup_changed_yao_ci("不存在的卦", 1, True) is None


# ══════════════════════════════════════════════════════════════
# 3. 查询功能 — 引擎层
# ══════════════════════════════════════════════════════════════
def test_engine_lookup_returns_dict():
    """引擎层查询应返回 dict (非 dataclass)。"""
    r = engine_lookup("乾", 1, True)
    assert isinstance(r, dict)
    assert r["hexagram_name"] == "乾"
    assert r["line_num"] == 1
    assert r["change_type"] == "老阳(9)→阴"
    assert len(r["yao_ci"]) > 0


def test_engine_lookup_yin():
    """老阴查询: change_type 应为'老阴(6)→阳'。"""
    r = engine_lookup("坤", 1, False)
    assert r is not None
    assert r["change_type"] == "老阴(6)→阳"


def test_engine_lookup_none():
    """引擎层查询不存在条目返回 None。"""
    assert engine_lookup("不存在的卦", 1, True) is None


def test_line_label():
    """爻位标签: 1→初, 2→二, ..., 6→上。"""
    assert _line_label(1) == "初"
    assert _line_label(2) == "二"
    assert _line_label(5) == "五"
    assert _line_label(6) == "上"


# ══════════════════════════════════════════════════════════════
# 4. integrate_yao_ci 集成
# ══════════════════════════════════════════════════════════════
def test_integrate_no_moving_lines():
    """无动爻时应提示以本卦卦辞为断。"""
    lines = [
        {"position": i + 1, "line_value": 7, "moving": False, "yang": 1}
        for i in range(6)
    ]
    r = integrate_yao_ci("乾", lines)
    assert r["moving_lines_count"] == 0
    assert "无动爻" in r["summary"]


def test_integrate_one_moving_line():
    """一爻动应以本爻辞为断。"""
    lines = [
        {"position": 1, "line_value": 9, "moving": True, "yang": 1},
        {"position": 2, "line_value": 7, "moving": False, "yang": 1},
        {"position": 3, "line_value": 8, "moving": False, "yang": 0},
        {"position": 4, "line_value": 8, "moving": False, "yang": 0},
        {"position": 5, "line_value": 7, "moving": False, "yang": 1},
        {"position": 6, "line_value": 8, "moving": False, "yang": 0},
    ]
    r = integrate_yao_ci("乾", lines)
    assert r["moving_lines_count"] == 1
    assert "一爻动" in r["summary"]


def test_integrate_two_moving_lines():
    """二爻动应合断。"""
    lines = [
        {"position": 1, "line_value": 9, "moving": True, "yang": 1},
        {"position": 2, "line_value": 7, "moving": False, "yang": 1},
        {"position": 3, "line_value": 8, "moving": False, "yang": 0},
        {"position": 4, "line_value": 6, "moving": True, "yang": 0},
        {"position": 5, "line_value": 7, "moving": False, "yang": 1},
        {"position": 6, "line_value": 8, "moving": False, "yang": 0},
    ]
    r = integrate_yao_ci("乾", lines)
    assert r["moving_lines_count"] == 2
    assert "二爻动" in r["summary"]


def test_integrate_entries_have_required_fields():
    """集成结果每条目应有完整字段。"""
    lines = [
        {"position": 1, "line_value": 9, "moving": True, "yang": 1},
        {"position": 2, "line_value": 7, "moving": False, "yang": 1},
        {"position": 3, "line_value": 8, "moving": False, "yang": 0},
        {"position": 4, "line_value": 6, "moving": True, "yang": 0},
        {"position": 5, "line_value": 7, "moving": False, "yang": 1},
        {"position": 6, "line_value": 8, "moving": False, "yang": 0},
    ]
    r = integrate_yao_ci("乾", lines)
    for entry in r["yao_ci_entries"]:
        assert "hexagram_name" in entry
        assert "line_num" in entry
        assert "change_type" in entry
        assert "yao_ci" in entry
        assert "source" in entry


def test_integrate_db_stats():
    """集成结果应包含数据库统计。"""
    lines = [
        {"position": 1, "line_value": 9, "moving": True, "yang": 1},
        {"position": 2, "line_value": 8, "moving": False, "yang": 0},
        {"position": 3, "line_value": 8, "moving": False, "yang": 0},
        {"position": 4, "line_value": 8, "moving": False, "yang": 0},
        {"position": 5, "line_value": 8, "moving": False, "yang": 0},
        {"position": 6, "line_value": 8, "moving": False, "yang": 0},
    ]
    r = integrate_yao_ci("乾", lines)
    assert r["yao_ci_total_db"] >= 128
    assert r["yao_ci_complete_db"] >= 30



# ══════════════════════════════════════════════════════════════
# 5. lookup_by_hexagram
# ══════════════════════════════════════════════════════════════
def test_lookup_by_hexagram_qian():
    """乾卦应有 12 条 (6爻×2状态)。"""
    entries = lookup_by_hexagram("乾")
    assert len(entries) == 12


def test_engine_lookup_by_hexagram_returns_dicts():
    """引擎层 lookup_by_hexagram 返回 dict 列表。"""
    entries = engine_lookup_by_hexagram("乾")
    assert isinstance(entries, list)
    assert len(entries) == 12
    for e in entries:
        assert isinstance(e, dict)
        assert "line_label" in e
        assert "change_type" in e


# ══════════════════════════════════════════════════════════════
# 6. 卦序一致性
# ══════════════════════════════════════════════════════════════
def test_hexagram_names_unique():
    """64卦名应唯一。"""
    assert len(_HEXAGRAM_ORDER) == len(set(_HEXAGRAM_ORDER))


def test_hexagram_num_reverse_lookup():
    """卦名→序号→卦名应闭环。"""
    for name, num in _HEXAGRAM_NUM.items():
        assert _HEXAGRAM_ORDER[num - 1] == name


# ══════════════════════════════════════════════════════════════
# 7. 动爻数据覆盖 (乾/坤 六爻完整, 其余部分)
# ══════════════════════════════════════════════════════════════
def test_qian_all_six_lines_present():
    """乾卦 6 爻 × 2 状态 = 12 条全部应有数据。"""
    for line_num in range(1, 7):
        for is_yang in (True, False):
            e = lookup_changed_yao_ci("乾", line_num, is_yang)
            assert e is not None, f"乾 line={line_num} yang={is_yang} missing"


def test_kun_all_six_lines_present():
    """坤卦 6 爻 × 2 状态 = 12 条全部应有数据。"""
    for line_num in range(1, 7):
        for is_yang in (True, False):
            e = lookup_changed_yao_ci("坤", line_num, is_yang)
            assert e is not None, f"坤 line={line_num} yang={is_yang} missing"


def test_changed_yao_ci_frozen():
    """ChangedYaoCi 应为 frozen dataclass。"""
    e = lookup_changed_yao_ci("乾", 1, True)
    assert e is not None
    with pytest.raises(Exception):
        e.yao_ci = "modified"  # type: ignore
