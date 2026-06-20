"""Tests for 三才五格姓名学 (divination/data/numerology_xingming.py)

来源：docs/CLASSICAL_SOURCES.md §6 数字命理 / 姓名学
文献：《姓名学大辞典》《康熙字典》笔画
"""
from __future__ import annotations

import pytest

from divination.data.numerology_xingming import (
    KANGXI_STROKES_ALL,
    KANGXI_STROKES_GIVEN,
    KANGXI_STROKES_SURNAME,
    NUMBER_TO_WUXING,
    OVERCOMES,
    GENERATES,
    SHULI_JIXIONG,
    compute_wuge,
    get_stroke,
    num_to_wuxing,
    wuxing_relationship,
)


# ── 1. 笔画表完整性 ─────────────────────────────────────
def test_surname_table_not_empty():
    """姓氏笔画表至少 50 个常见姓。"""
    assert len(KANGXI_STROKES_SURNAME) >= 50


def test_given_table_not_empty():
    """名用字笔画表至少 50 个。"""
    assert len(KANGXI_STROKES_GIVEN) >= 50


def test_common_surnames_present():
    """常见姓氏必须存在。"""
    common = {"李", "王", "张", "刘", "陈", "杨", "黄", "周", "吴", "徐"}
    missing = common - set(KANGXI_STROKES_SURNAME.keys())
    assert not missing, f"常见姓氏缺失: {missing}"


def test_common_given_present():
    """常见名用字必须存在。"""
    common = {"梓", "宇", "子", "轩", "涵", "思", "雨", "欣", "嘉", "慧"}
    missing = common - set(KANGXI_STROKES_GIVEN.keys())
    assert not missing, f"常见名用字缺失: {missing}"


def test_stroke_counts_valid():
    """所有笔画数必须在 1-40 范围（康熙字典最大 ~40 画）。"""
    for char, n in KANGXI_STROKES_ALL.items():
        assert 1 <= n <= 40, f"{char}: 笔画={n}"


def test_known_correct_strokes():
    """验证经典字的笔画数（与康熙字典一致）。"""
    assert KANGXI_STROKES_SURNAME["李"] == 7
    assert KANGXI_STROKES_SURNAME["王"] == 4
    assert KANGXI_STROKES_SURNAME["陈"] == 16
    assert KANGXI_STROKES_GIVEN["梓"] == 11
    assert KANGXI_STROKES_GIVEN["宇"] == 6
    assert KANGXI_STROKES_GIVEN["子"] == 3


# ── 2. 数→五行映射 ──────────────────────────────────────
def test_num_to_wuxing_all_ten():
    """1-10 全部映射到五行。"""
    for i in range(1, 11):
        wx = num_to_wuxing(i)
        assert wx in {"金", "木", "水", "火", "土"}, f"{i} → {wx}"


def test_num_to_wuxing_mapping():
    """关键映射: 1=木, 3=火, 5=土, 7=金, 9=水。"""
    assert num_to_wuxing(1) == "木"
    assert num_to_wuxing(3) == "火"
    assert num_to_wuxing(5) == "土"
    assert num_to_wuxing(7) == "金"
    assert num_to_wuxing(9) == "水"


def test_num_to_wuxing_last_digit():
    """11 → 木（1 尾数）, 25 → 土（5 尾数）, 38 → 金（8 尾数）。"""
    assert num_to_wuxing(11) == "木"
    assert num_to_wuxing(25) == "土"
    assert num_to_wuxing(38) == "金"


def test_num_to_wuxing_zero():
    """10/20/30 → 水（10 视为水）。"""
    assert num_to_wuxing(10) == "水"
    assert num_to_wuxing(20) == "水"
    assert num_to_wuxing(30) == "水"


# ── 3. 五行关系 ────────────────────────────────────────
def test_wuxing_generate():
    """木生火, 火生土, 土生金, 金生水, 水生木。"""
    assert GENERATES["木"] == "火"
    assert GENERATES["火"] == "土"
    assert GENERATES["土"] == "金"
    assert GENERATES["金"] == "水"
    assert GENERATES["水"] == "木"


def test_wuxing_overcome():
    """木克土, 土克水, 水克火, 火克金, 金克木。"""
    assert OVERCOMES["木"] == "土"
    assert OVERCOMES["土"] == "水"
    assert OVERCOMES["水"] == "火"
    assert OVERCOMES["火"] == "金"
    assert OVERCOMES["金"] == "木"


def test_relationship_self():
    """相同五行 = 比和。"""
    assert wuxing_relationship("木", "木") == "比和"
    assert wuxing_relationship("金", "金") == "比和"


def test_relationship_generate():
    """木生火 → A生B（甲对乙）。"""
    assert wuxing_relationship("木", "火") == "生"
    assert wuxing_relationship("火", "土") == "生"


def test_relationship_overcome():
    """木克土 → A克B。"""
    assert wuxing_relationship("木", "土") == "克"
    assert wuxing_relationship("水", "火") == "克"


def test_relationship_reversed():
    """水生木 = '生'(水生木); 土被木克 = '被克'。"""
    # 水对木的关系: 水生木 → 水主动生木 → 关系是 '生'
    assert wuxing_relationship("水", "木") == "生"
    # 木克土: 土被动被克 → 关系是 '被克'
    assert wuxing_relationship("土", "木") == "被克"


# ── 4. 数理吉凶表 ──────────────────────────────────────
def test_shuli_covers_1_to_81():
    """数理吉凶表覆盖 1-81 全部。"""
    missing = set(range(1, 82)) - set(SHULI_JIXIONG.keys())
    assert not missing, f"数理缺失: {sorted(missing)}"


def test_shuli_luck_valid_values():
    """吉凶判定只能是 大吉/吉/半吉/凶 之一。"""
    valid = {"大吉", "吉", "半吉", "凶"}
    for n, info in SHULI_JIXIONG.items():
        assert info["luck"] in valid, f"{n}: luck={info['luck']!r}"


def test_shuli_meaning_not_empty():
    """每条数理必须有非空 meaning。"""
    for n, info in SHULI_JIXIONG.items():
        assert info.get("meaning") and len(info["meaning"]) >= 4, (
            f"{n}: meaning={info.get('meaning')!r}"
        )


def test_shuli_classical_known():
    """已知经典数理: 1=大吉, 33=大吉（旭日升天）。"""
    assert SHULI_JIXIONG[1]["luck"] == "大吉"
    assert SHULI_JIXIONG[33]["luck"] == "大吉"
    assert "旭日" in SHULI_JIXIONG[33]["meaning"]


# ── 5. 笔画查询 ────────────────────────────────────────
def test_get_stroke_known():
    """查询已知字笔画。"""
    assert get_stroke("李") == 7
    assert get_stroke("王") == 4
    assert get_stroke("梓") == 11


def test_get_stroke_unknown_fallback():
    """未知字应走 fallback（不崩溃, 返回 1-30 之间的值）。"""
    n = get_stroke("龘")  # 极复杂字
    assert 1 <= n <= 30


# ── 6. 三才五格计算 ────────────────────────────────────
def test_wuge_li_zi_han():
    """李梓涵（姓氏 7+1=8, 单字名梓 11）。"""
    r = compute_wuge("李", "梓涵")
    # 天格 = 7 + 1 = 8
    assert r["tiange"]["num"] == 8
    # 人格 = 7 + 11 = 18
    assert r["renge"]["num"] == 18
    # 地格 = 11 + 12 = 23 (梓 11 + 涵 12)
    assert r["dige"]["num"] == 23
    # 总格 = 7 + 11 + 12 = 30
    assert r["zongge"]["num"] == 30
    # 必须有综合判断
    assert r["overall"] in {"吉", "半吉", "凶"}


def test_wuge_single_char_name():
    """单字名 + 单字姓: 陈静 (陈 16, 静 16)。"""
    r = compute_wuge("陈", "静")
    # 天格 = 16 + 1 = 17
    assert r["tiange"]["num"] == 17
    # 人格 = 16 + 16 = 32
    assert r["renge"]["num"] == 32
    # 地格 = 16 + 1 = 17 (单字名)
    assert r["dige"]["num"] == 17
    # 总格 = 16 + 16 = 32
    assert r["zongge"]["num"] == 32


def test_wuge_compound_surname():
    """复姓: 司马晓晗（司马 6+10=16, 晓 16, 晗 11）。"""
    r = compute_wuge("司马", "晓晗")
    # 天格 = 司+马 = 6+10 = 16 (复姓用总笔画)
    assert r["tiange"]["num"] == 16
    # 人格 = 马 + 晓 = 10 + 16 = 26
    assert r["renge"]["num"] == 26
    # 地格 = 晓 + 晗 = 16 + 11 = 27
    assert r["dige"]["num"] == 27
    # 总格 = 16 + 27 = 43
    assert r["zongge"]["num"] == 43


def test_wuge_san_cai_present():
    """三才五格必须含 san_cai 字段。"""
    r = compute_wuge("王", "宇轩")
    sc = r["san_cai"]
    assert "tian_wx" in sc
    assert "ren_wx" in sc
    assert "di_wx" in sc
    assert "tian_ren_rel" in sc
    assert "ren_di_rel" in sc
    assert all(wx in {"金", "木", "水", "火", "土"} for wx in [sc["tian_wx"], sc["ren_wx"], sc["di_wx"]])


def test_wuge_empty_surname():
    """空姓应返回 error。"""
    r = compute_wuge("", "梓涵")
    assert "error" in r


def test_wuge_empty_given_name():
    """空名应返回 error。"""
    r = compute_wuge("李", "")
    assert "error" in r


def test_wuge_all_luck_in_valid():
    """综合判断只能是 吉/半吉/凶 之一。"""
    r = compute_wuge("李", "梓涵")
    assert r["overall"] in {"吉", "半吉", "凶"}


def test_wuge_individual_luck_in_valid():
    """五格各自的 luck 必须是 大吉/吉/半吉/凶。"""
    r = compute_wuge("李", "梓涵")
    valid = {"大吉", "吉", "半吉", "凶"}
    for key in ["tiange", "renge", "dige", "waige", "zongge"]:
        assert r[key]["luck"] in valid, f"{key}: luck={r[key]['luck']!r}"
