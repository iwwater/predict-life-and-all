"""Tests for 紫微飞星四化深度解读 (divination/engines/ziwei.py 中的 _enrich_four_transformations)

来源：docs/CLASSICAL_SOURCES.md §2 紫微斗数
文献：《飞星紫微斗数全书》《紫微斗数全书》
"""
from __future__ import annotations

import pytest

from divination.engines.ziwei import _enrich_four_transformations


# ── 1. 本命四化 ───────────────────────────────────
def test_natal_sihua_jia_year():
    """甲年生人: 廉贞禄/破军权/武曲科/太阳忌。"""
    r = _enrich_four_transformations({}, year_gan="甲")
    assert r["natal"]["禄"]["star"] == "廉贞"
    assert r["natal"]["权"]["star"] == "破军"
    assert r["natal"]["科"]["star"] == "武曲"
    assert r["natal"]["忌"]["star"] == "太阳"


def test_natal_sihua_yi_year():
    """乙年生人: 天机禄/天梁权/紫微科/太阴忌。"""
    r = _enrich_four_transformations({}, year_gan="乙")
    assert r["natal"]["禄"]["star"] == "天机"
    assert r["natal"]["权"]["star"] == "天梁"
    assert r["natal"]["科"]["star"] == "紫微"
    assert r["natal"]["忌"]["star"] == "太阴"


def test_natal_sihua_all_ten_gans():
    """10 天干本命四化全覆盖。"""
    expected = {
        "甲": ("廉贞", "破军", "武曲", "太阳"),
        "乙": ("天机", "天梁", "紫微", "太阴"),
        "丙": ("天同", "天机", "文昌", "廉贞"),
        "丁": ("太阴", "天同", "天机", "巨门"),
        "戊": ("贪狼", "太阴", "右弼", "天机"),
        "己": ("武曲", "贪狼", "天梁", "文曲"),
        "庚": ("太阳", "武曲", "太阴", "天同"),
        "辛": ("巨门", "太阳", "文曲", "文昌"),
        "壬": ("天梁", "紫微", "左辅", "武曲"),
        "癸": ("破军", "巨门", "太阴", "贪狼"),
    }
    for gan, (lu, quan, ke, ji) in expected.items():
        r = _enrich_four_transformations({}, year_gan=gan)
        assert r["natal"]["禄"]["star"] == lu, f"甲={gan}: 禄 expected {lu}"
        assert r["natal"]["权"]["star"] == quan
        assert r["natal"]["科"]["star"] == ke
        assert r["natal"]["忌"]["star"] == ji


# ── 2. 大限 / 流年四化解析 ──────────────────────────
def test_decadal_parse_format_a():
    """格式: "贪狼化禄"。"""
    r = _enrich_four_transformations({"decadal": ["贪狼化禄"]})
    assert r["current_decadal"]["化禄"]["star"] == "贪狼"
    assert "交际财" in r["current_decadal"]["化禄"]["meaning"]


def test_decadal_parse_format_b():
    """格式: "化禄贪狼"（倒装）。"""
    r = _enrich_four_transformations({"decadal": ["化禄贪狼"]})
    assert r["current_decadal"]["化禄"]["star"] == "贪狼"


def test_yearly_parse_multiple():
    """多四化解析。"""
    r = _enrich_four_transformations({
        "yearly": ["紫微化权", "天机化科"],
    })
    assert "化权" in r["current_yearly"]
    assert r["current_yearly"]["化权"]["star"] == "紫微"
    assert "化科" in r["current_yearly"]
    assert r["current_yearly"]["化科"]["star"] == "天机"


def test_decadal_parse_empty():
    """空大限四化。"""
    r = _enrich_four_transformations({"decadal": []})
    assert r["current_decadal"] == {}


def test_decadal_parse_invalid():
    """无效字符串应跳过。"""
    r = _enrich_four_transformations({"decadal": ["随便", "无效"]})
    assert r["current_decadal"] == {}


# ── 3. 综合解读 ──────────────────────────────────
def test_interpretation_combined():
    """综合解读包含本命+大限+流年。"""
    r = _enrich_four_transformations(
        {"decadal": ["贪狼化禄"], "yearly": ["紫微化权"]},
        year_gan="甲"
    )
    interp = r["interpretation"]
    assert "本命四化" in interp
    assert "甲" or "廉贞" in interp  # 甲年本命
    assert "大限" in interp
    assert "流年" in interp


def test_interpretation_only_natal():
    """仅本命四化时, 解读只含本命。"""
    r = _enrich_four_transformations({}, year_gan="甲")
    assert "本命四化" in r["interpretation"]
    assert "大限" not in r["interpretation"]
    assert "流年" not in r["interpretation"]


def test_interpretation_empty():
    """无数据时解读为空。"""
    r = _enrich_four_transformations({}, year_gan=None)
    assert r["interpretation"] == "暂无四化数据"


# ── 4. evidence_sources ──────────────────────────
def test_evidence_sources_included():
    """返回必须含证据来源。"""
    r = _enrich_four_transformations({}, year_gan="甲")
    assert "evidence_sources" in r
    assert len(r["evidence_sources"]) >= 2
    assert any("飞星" in src for src in r["evidence_sources"])


# ── 5. Return 字段完整性 ──────────────────────────
def test_full_result_has_all_keys():
    """完整返回应含所有必需字段。"""
    r = _enrich_four_transformations(
        {"decadal": ["贪狼化禄"], "yearly": ["紫微化权"]},
        year_gan="甲",
    )
    required = {"natal", "current_decadal", "current_yearly",
                "interpretation", "evidence_sources"}
    assert required <= set(r.keys())
