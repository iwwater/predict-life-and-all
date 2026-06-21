"""Tests for 铁板神数 深化 (divination/engines/tieban.py)

深化项 (Sprint 3.x):
1. 太玄数公式精校 (阳支取阳数, 阴支取阴数)
2. 纳音五行计算
3. 考刻分深化 (分金 60 编号)
4. 多条文集流派支持 (邵雍本/铁冠道人本)
5. 条文匹配度评分 (关键词加权)
6. 综合解读
7. evidence_sources
"""
from __future__ import annotations

import pytest

from divination.contracts import Birth
from divination.engines import tieban
from divination.engines.tieban import (
    EVIDENCE_SOURCES,
    LINEAGES,
    LINEAGE_NAMES,
    LINEAGE_OFFSET,
    NAYIN_BY_GANZHI,
    NAYIN_TABLE,
    NAYIN_WUXING,
    _build_interpretation,
    _compute_base_number,
    _compute_fen_jin,
    _compute_ke_fen,
    _compute_ke_fen_with_fen_jin,
    _encode_branches,
    _encode_stems,
    _four_pillars,
    _lookup_verses,
    _nayin_summary,
    _nayin_wuxing_for_pillar,
    _verse_relevance,
    compute,
)


# ── 1. 太玄数公式精校 ─────────────────────────────────────
def test_taixuan_yang_zhi_yang_num():
    """阳支 (子寅辰午申戌) 取阳数 (pair[0])."""
    b = Birth(year=1990, month=5, day=15, hour=23, minute=0)  # 子时
    solar = tieban._solar_from_birth(b)
    pillars = _four_pillars(solar)
    br = _encode_branches(pillars)
    # 验证: 子时为子(阳支, 取阳数 1)
    if "子" in {br[k]["zhi"] for k in br}:
        zi_branch = next(b for b in br.values() if b["zhi"] == "子")
        assert zi_branch["num"] == 1


def test_taixuan_yin_zhi_yin_num():
    """阴支 (丑卯巳未酉亥) 取阴数 (pair[1])."""
    # 丑时 (1-3 时)
    b = Birth(year=1990, month=5, day=15, hour=1, minute=0)
    solar = tieban._solar_from_birth(b)
    pillars = _four_pillars(solar)
    br = _encode_branches(pillars)
    # 丑为阴支, 应取阴数 10
    if "丑" in {br[k]["zhi"] for k in br}:
        chou_branch = next(b for b in br.values() if b["zhi"] == "丑")
        assert chou_branch["num"] == 10


def test_taixuan_all_12_zhi_mapped():
    """所有 12 地支都应能正确映射阳/阴数."""
    for zhi in "子丑寅卯辰巳午未申酉戌亥":
        from divination.data.tieban_verses import TAIXUAN_NUM, YANG_ZHI
        pair = TAIXUAN_NUM[zhi]
        expected = pair[0] if zhi in YANG_ZHI else pair[1]
        # 模拟编码
        fake_pillars = {"year": "甲" + zhi}
        br = _encode_branches(fake_pillars)
        assert br["year"]["num"] == expected


# ── 2. 纳音五行计算 ─────────────────────────────────────
def test_nayin_table_complete():
    """六十甲子纳音表必须完整 (60 项)."""
    assert len(NAYIN_TABLE) == 60
    assert len(NAYIN_BY_GANZHI) == 60


def test_nayin_known_pairs():
    """检验几个经典纳音对."""
    # 甲子乙丑海中金
    assert NAYIN_BY_GANZHI["甲子"] == "海中金"
    assert NAYIN_BY_GANZHI["乙丑"] == "海中金"
    # 丙寅丁卯炉中火
    assert NAYIN_BY_GANZHI["丙寅"] == "炉中火"
    assert NAYIN_BY_GANZHI["丁卯"] == "炉中火"
    # 戊辰己巳大林木
    assert NAYIN_BY_GANZHI["戊辰"] == "大林木"
    assert NAYIN_BY_GANZHI["己巳"] == "大林木"


def test_nayin_wuxing_classical():
    """纳音五行对照传统说法."""
    assert NAYIN_WUXING["海中金"] == "金"
    assert NAYIN_WUXING["炉中火"] == "火"
    assert NAYIN_WUXING["大林木"] == "木"
    assert NAYIN_WUXING["路旁土"] == "土"
    assert NAYIN_WUXING["涧下水"] == "水"


def test_nayin_for_pillar_helper():
    """_nayin_wuxing_for_pillar 单柱助手."""
    r = _nayin_wuxing_for_pillar("甲子")
    assert r["ganzhi"] == "甲子"
    assert r["纳音"] == "海中金"
    assert r["纳音五行"] == "金"


def test_nayin_summary_returns_4_pillars():
    """_nayin_summary 返回四柱纳音."""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=0)
    solar = tieban._solar_from_birth(b)
    pillars = _four_pillars(solar)
    summary = _nayin_summary(pillars)
    assert set(summary.keys()) == {"year", "month", "day", "hour"}
    for k, v in summary.items():
        assert "纳音" in v
        assert "纳音五行" in v


# ── 3. 考刻分 + 分金深化 ─────────────────────────────────
def test_ke_fen_basic():
    """基本刻分: 0-14 分 → 1 刻 0-14 分."""
    r = _compute_ke_fen(0)
    assert r["ke"] == 1
    assert r["fen"] == 0
    r = _compute_ke_fen(14)
    assert r["ke"] == 1
    assert r["fen"] == 14
    r = _compute_ke_fen(15)
    assert r["ke"] == 2
    assert r["fen"] == 0


def test_fen_jin_60_range():
    """分金编号 0-59 全覆盖 (60 分金)."""
    for ke in (1, 2, 3, 4):
        for fen in range(15):
            r = _compute_fen_jin(ke, fen)
            assert 0 <= r["分金编号"] <= 59
            assert r["校验"] is True


def test_fen_jin_4_ke_15_fen_each():
    """4 刻 × 15 分 = 60 分金, 编号连续."""
    expected_id = 0
    for ke in (1, 2, 3, 4):
        for fen in range(15):
            r = _compute_fen_jin(ke, fen)
            assert r["分金编号"] == expected_id
            expected_id += 1
    assert expected_id == 60


def test_ke_fen_with_fen_jin():
    """考刻分深化: 刻 + 分 + 分金 完整编码."""
    r = _compute_ke_fen_with_fen_jin(30)  # 30//15=2 → 2 刻, 30%15=0 → 0 分
    assert r["ke"] == 3  # 30//15+1=3
    assert r["fen"] == 0
    assert "分金" in r
    assert r["分金"]["分金编号"] == 30  # (3-1)*15 + 0


# ── 4. 多条文集流派支持 ─────────────────────────────────
def test_lineage_offset_differs():
    """两个流派的偏移必须不同."""
    assert LINEAGE_OFFSET["shaoyong"] != LINEAGE_OFFSET["tieguan"]


def test_lineage_names_present():
    """两个流派必须有名称."""
    assert "邵雍本" in LINEAGE_NAMES["shaoyong"]
    assert "铁冠道人本" in LINEAGE_NAMES["tieguan"]


def test_lookup_different_lineages_different_sets():
    """同一基数, 不同流派的条文集可能不同."""
    from divination.data.tieban_verses import TIEBAN_VERSES
    range_keys = list(TIEBAN_VERSES.keys())
    n = len(range_keys)
    base_num = 1000
    shaoyong_idx = (base_num + LINEAGE_OFFSET["shaoyong"]) % n
    tieguan_idx = (base_num + LINEAGE_OFFSET["tieguan"]) % n
    # 因为偏移 100, 不同流派的索引通常不同
    assert shaoyong_idx != tieguan_idx


def test_compute_shaoyong_lineage():
    """compute 支持 shaoyong 流派."""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=0)
    r = compute(b, lineage="shaoyong")
    assert r.raw["lineage"] == "shaoyong"
    assert "邵雍" in r.raw["lineage_name"]


def test_compute_tieguan_lineage():
    """compute 支持 tieguan 流派."""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=0)
    r = compute(b, lineage="tieguan")
    assert r.raw["lineage"] == "tieguan"
    assert "铁冠道人" in r.raw["lineage_name"]


def test_compute_lineages_map_to_different_verse_ranges():
    """同一出生信息在不同流派下应映射到不同条文范围。"""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=0)
    shaoyong = compute(b, lineage="shaoyong")
    tieguan = compute(b, lineage="tieguan")
    assert shaoyong.raw["verse_result"]["verse_set_range"] != tieguan.raw["verse_result"]["verse_set_range"]


def test_compute_invalid_lineage_raises():
    """不支持的流派应 raise ValueError."""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=0)
    with pytest.raises(ValueError, match="lineage"):
        compute(b, lineage="unknown")


# ── 5. 条文匹配度评分 ─────────────────────────────────────
def test_relevance_base_score():
    """基础分 (无关键词命中) 应为 0.5."""
    fake_verse = {"text": "通用条文", "checksum": 300}
    score = _verse_relevance(fake_verse, "财运", [])
    assert 0.5 <= score <= 0.6


def test_relevance_keywords_boost():
    """关键词命中数越高, 评分越高."""
    v1 = {"text": "财运", "checksum": 300}
    v2 = {"text": "财源广进, 财运亨通, 进财", "checksum": 400}
    s1 = _verse_relevance(v1, "财运", [])
    s2 = _verse_relevance(v2, "财运", [])
    assert s2 > s1


def test_relevance_user_question_boost():
    """用户问题关键词能进一步加权."""
    v = {"text": "婚姻美满, 夫唱妇随, 鸾凤和鸣", "checksum": 300}
    s_no_q = _verse_relevance(v, "夫妻", [])
    s_with_q = _verse_relevance(v, "夫妻", ["婚", "夫"])
    assert s_with_q > s_no_q


def test_relevance_score_range():
    """评分必须限定在 [0, 1] 范围."""
    v = {"text": "财源广进, 婚姻美满, 官星明亮, 寿元绵长", "checksum": 400}
    s = _verse_relevance(v, "财运", ["财", "婚", "官", "寿"])
    assert 0.0 <= s <= 1.0


def test_lookup_verses_sorted_by_relevance():
    """lookup 返回的条文必须按相关度降序."""
    r = _lookup_verses(1050, question_keywords=["财", "婚姻"], top_n=5)
    verses = r["matched_verses"]
    if len(verses) >= 2:
        scores = [v["relevance"] for v in verses]
        assert scores == sorted(scores, reverse=True)


def test_lookup_verses_with_zodiac_filter():
    """父母生肖校验过滤后, 仍有命中条文 (相关性计算)."""
    r = _lookup_verses(1050, father_zodiac="虎", mother_zodiac="兔",
                       question_keywords=["婚"], top_n=3)
    assert "verification" in r
    assert r["verification"]["father_zodiac"] == "虎"


# ── 6. 综合解读 ───────────────────────────────────────────
def test_interpretation_includes_5_sections():
    """综合解读必须包含 5 大段: 流派/编码/纳音/刻分/条文."""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=0)
    r = compute(b)
    interp = r.raw["interpretation"]
    for kw in ("铁板神数", "四柱编码", "太玄数", "纳音", "考刻分", "条文"):
        assert kw in interp


def test_interpretation_includes_nayin():
    """综合解读必须包含纳音五行."""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=0)
    r = compute(b)
    interp = r.raw["interpretation"]
    # 纳音格式: "年纳音=海中金(金)"
    assert "纳音=" in interp


def test_interpretation_with_question_keywords():
    """综合解读应包含用户关键词."""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=0)
    r = compute(b, question_keywords=["财", "婚"])
    interp = r.raw["interpretation"]
    assert "用户关键词" in interp
    assert "财" in interp
    assert "婚" in interp


# ── 7. evidence_sources ──────────────────────────────────
def test_evidence_sources_classical():
    """evidence_sources 必须引用铁板神数经典文献."""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=0)
    r = compute(b)
    sources = r.raw["evidence_sources"]
    assert any("铁板神数" in s for s in sources)
    assert any("纳音" in s or "渊海子平" in s or "三命通会" in s for s in sources)


def test_evidence_sources_two_lineages():
    """evidence_sources 应涵盖两大流派."""
    assert any("邵雍" in s for s in EVIDENCE_SOURCES)
    assert any("铁冠道人" in s for s in EVIDENCE_SOURCES)


# ── 8. 兼容性 + 编码完整性 ──────────────────────────────
def test_compute_default_keeps_backward_compat():
    """compute 默认参数保留旧 API 行为."""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=30)
    r = compute(b)
    assert r.method == "tieban"
    raw = r.raw
    assert raw["rule_version"] == "v2"
    assert "encoding" in raw
    assert "stems" in raw["encoding"]
    assert "branches" in raw["encoding"]
    assert "four_pillars" in raw


def test_compute_via_explicit_args():
    """父母生肖通过 compute() 显式参数传入 (旧 API 也支持)."""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=0)
    # 旧版用 getattr(b, "father_zodiac", "") 默认 ""; 新版显式参数优先级更高
    r = compute(b, father_zodiac="虎", mother_zodiac="兔")
    assert r.raw["verse_result"]["verification"]["father_zodiac"] == "虎"
    assert r.raw["verse_result"]["verification"]["mother_zodiac"] == "兔"


def test_compute_backward_compat_no_args():
    """compute(b) 不传任何额外参数仍能工作 (向后兼容)."""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=0)
    r = compute(b)
    assert r.method == "tieban"
    # 不传父母生肖 → verification.father_zodiac 为 None
    assert r.raw["verse_result"]["verification"]["father_zodiac"] is None


def test_nayin_in_compute_output():
    """compute raw 必须包含纳音五行."""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=0)
    r = compute(b)
    assert "nayin" in r.raw
    assert set(r.raw["nayin"].keys()) == {"year", "month", "day", "hour"}


def test_fen_jin_in_compute_output():
    """compute raw 的 ke_fen 必须包含分金."""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=30)
    r = compute(b)
    assert "分金" in r.raw["ke_fen"]
    assert "分金编号" in r.raw["ke_fen"]["分金"]


def test_lineages_constant():
    """LINEAGES 必须包含两个流派."""
    assert "shaoyong" in LINEAGES
    assert "tieguan" in LINEAGES
    assert len(LINEAGES) >= 2


def test_top_n_limits_returned_verses():
    """top_n 参数限制返回条文数."""
    r = _lookup_verses(1050, top_n=2)
    assert len(r["matched_verses"]) <= 2
