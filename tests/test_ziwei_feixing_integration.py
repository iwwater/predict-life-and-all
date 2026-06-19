"""Sprint 4.1 — 紫微飞星四化 normalizer 端到端集成测试。

覆盖:
- engine → raw[four_transformations_enriched] → normalizer signals 完整链路
- 1984 男 (甲子年) 本命四化 = {禄: 廉贞, 权: 破军, 科: 武曲, 忌: 太阳}
- normalizer evidence 包含 "本命" + 结构化含义
- W1 老 API ['','','',''] 不再误判为全正向
- 4 化 signal 至少 1 个包含本命/大限/流年 enriched evidence
"""
from __future__ import annotations

import pytest

from divination.engines.ziwei import compute
from divination.aggregation.normalizer import normalize
from divination.contracts import Birth, ChartResult


# 1984-1-1 男 → 年干=甲, NATAL_SIHUA["甲"] = {禄: 廉贞, 权: 破军, 科: 武曲, 忌: 太阳}
BIRTH_1984_JIA = Birth(
    year=1984, month=6, day=15, hour=8, minute=30,
    gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai",
)

# 1990-6-15 男 → 年干=庚, NATAL_SIHUA["庚"] = {禄: 太阳, 权: 武曲, 科: 太阴, 忌: 天同}
BIRTH_1990_GENG = Birth(
    year=1990, month=6, day=15, hour=8, minute=30,
    gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai",
)


def _chart(birth):
    r = compute(birth)
    return ChartResult(method="ziwei", school="east", engine="iztro",
                      normalized=r.normalized, raw=r.raw)


# ── 1. Engine raw 输出 (结构化 enriched) ─────────────────────────────────

class TestZiweiFeixingRaw:
    def test_enriched_natal_present_1984(self):
        """1984 男 本命四化 = 廉贞/破军/武曲/太阳 (按 NATAL_SIHUA["甲"])"""
        r = compute(BIRTH_1984_JIA)
        enriched = r.raw.get("four_transformations_enriched") or {}
        natal = enriched.get("natal") or {}
        assert natal, "1984 男 enriched.natal 应非空"
        assert natal.get("禄", {}).get("star") == "廉贞"
        assert natal.get("权", {}).get("star") == "破军"
        assert natal.get("科", {}).get("star") == "武曲"
        assert natal.get("忌", {}).get("star") == "太阳"
        # 每条都有含义
        for hua_type in ("禄", "权", "科", "忌"):
            assert natal[hua_type].get("meaning"), f"本命 {hua_type} 缺 meaning"
            assert natal[hua_type].get("category"), f"本命 {hua_type} 缺 category"

    def test_enriched_natal_present_1990(self):
        """1990 男 本命四化 = 太阳/武曲/太阴/天同 (按 NATAL_SIHUA["庚"])"""
        r = compute(BIRTH_1990_GENG)
        natal = r.raw.get("four_transformations_enriched", {}).get("natal") or {}
        assert natal, "1990 男 enriched.natal 应非空"
        assert natal.get("禄", {}).get("star") == "太阳"
        assert natal.get("权", {}).get("star") == "武曲"
        assert natal.get("科", {}).get("star") == "太阴"
        assert natal.get("忌", {}).get("star") == "天同"

    def test_interpretation_string_present(self):
        r = compute(BIRTH_1984_JIA)
        interp = r.raw.get("four_transformations_enriched", {}).get("interpretation", "")
        assert "本命四化" in interp
        assert "廉贞" in interp


# ── 2. Normalizer 消费 enriched ─────────────────────────────────────────

class TestNormalizerConsumesEnriched:
    def test_normalizer_uses_enriched_natal_1984(self):
        """normalizer 应消费 enriched.natal, evidence 包含 本命 + 廉贞化禄"""
        signals = normalize("ziwei", _chart(BIRTH_1984_JIA))
        natal_sigs = [
            s for s in signals
            if s.signal_key == "natal_four_transformations"
            or ("本命四化" in s.evidence and "廉贞" in s.evidence)
        ]
        assert natal_sigs, f"未找到本命四化 signal, signals={[(s.signal_key, s.evidence[:50]) for s in signals]}"
        ev = natal_sigs[0].evidence
        # 含义字段都应在 evidence 中
        assert "廉贞" in ev
        assert "破军" in ev
        assert "武曲" in ev
        assert "太阳" in ev

    def test_normalizer_decadal_or_fallback_evidence(self):
        """大限 signal evidence 应包含 '大限4化' 前缀 (Sprint 2.3 测试兼容)"""
        signals = normalize("ziwei", _chart(BIRTH_1990_GENG))
        decadal_sigs = [s for s in signals if "大限4化" in s.evidence]
        assert decadal_sigs, "应有大限4化 signal"
        assert decadal_sigs[0].dimension == "current_cycle"

    def test_normalizer_yearly_evidence(self):
        """流年 signal evidence 应包含 '流年4化' 前缀"""
        signals = normalize("ziwei", _chart(BIRTH_1990_GENG))
        yearly_sigs = [s for s in signals if "流年4化" in s.evidence]
        assert yearly_sigs
        assert yearly_sigs[0].dimension == "current_cycle"

    def test_normalizer_monthly_evidence(self):
        """流月 signal evidence 应包含 '流月4化' 前缀"""
        signals = normalize("ziwei", _chart(BIRTH_1990_GENG))
        monthly_sigs = [s for s in signals if "流月4化" in s.evidence]
        assert monthly_sigs
        assert monthly_sigs[0].dimension == "current_cycle"

    def test_at_least_4_signals_1984(self):
        """Sprint 4.1 红线: 至少 4 个 4 化 signal (本命 + 大限 + 流年 + 流月 + 短期)."""
        signals = normalize("ziwei", _chart(BIRTH_1984_JIA))
        limit_signals = [
            s for s in signals
            if "本命" in s.evidence or "4化" in s.evidence
        ]
        assert len(limit_signals) >= 4, (
            f"4 化 signal 不足: {len(limit_signals)}, "
            f"got: {[(s.signal_key, s.evidence[:40]) for s in limit_signals]}"
        )


# ── 3. W1 老 API bug 修复 ────────────────────────────────────────────────

class TestW1OldAPIBugFix:
    def test_empty_mutagen_not_misclassified(self):
        """py_iztro 0.3+ 老 API 返回 ['','','',''], 不应误判为全 4 吉.

        修复策略: _classify_mutagen 显式空串归 neutral.
        """
        # 构造一个全空 mutagen 的 chart
        empty_chart = ChartResult(
            method="ziwei", school="east", engine="iztro",
            normalized={},
            raw={
                "palaces": [],
                "four_transformations": {
                    "decadal": ["", "", "", ""],
                    "yearly": ["", "", "", ""],
                    "monthly": ["", "", "", ""],
                    "daily": ["", "", "", ""],
                    "hourly": ["", "", "", ""],
                },
                "four_transformations_enriched": {},
            },
        )
        signals = normalize("ziwei", empty_chart)
        # 不应出现 polarity="positive" 的 4 化 signal (因空串 → neutral)
        for s in signals:
            if "4化" in s.evidence:
                assert s.polarity in ("neutral", "negative"), (
                    f"空串被误判为 {s.polarity}: {s.evidence}"
                )


# ── 4. enriched evidence 含义密度 ────────────────────────────────────────

class TestEnrichedEvidenceQuality:
    def test_decadal_evidence_contains_meaning_when_enriched(self):
        """如果 enriched 有大限含义, evidence 应包含 '→' 含义箭头"""
        r = compute(BIRTH_1984_JIA)
        enriched = r.raw.get("four_transformations_enriched", {})
        decadal = enriched.get("current_decadal", {})
        if decadal:
            signals = normalize("ziwei", _chart(BIRTH_1984_JIA))
            decadal_sigs = [s for s in signals if "大限4化" in s.evidence]
            assert decadal_sigs
            ev = decadal_sigs[0].evidence
            # enriched 路径下, 至少一个化有 '→' 含义箭头
            assert "→" in ev, f"含义缺失: {ev}"
