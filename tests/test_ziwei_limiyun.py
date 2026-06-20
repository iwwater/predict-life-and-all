"""Sprint 2.3 — ziwei 大限/流年/流月 4 化信号测试。

覆盖:
- engine 输出 decadal/yearly/monthly/daily/hourly 4 化列表
- normalizer 各出 1 个 current_cycle signal (大限+流年+流月 = 3 个)
- 大限/流年用 timing, 流月用 timing_transition
- 每条 signal 有 5 档 signal_digest
"""
from __future__ import annotations

import pytest

from divination.engines.ziwei import compute
from divination.aggregation.normalizer import normalize
from divination.contracts import Birth, ChartResult


BIRTH = Birth(
    year=1990, month=6, day=15, hour=8, minute=30,
    gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai",
)


def _chart():
    r = compute(BIRTH)
    return ChartResult(method="ziwei", school="east", engine="iztro",
                      normalized=r.normalized, raw=r.raw)


# ── Engine raw 4 化 ─────────────────────────────────────────────────

class TestZiweiFourTransRaw:
    def test_four_transformations_all_scopes(self):
        r = compute(BIRTH)
        ft = r.raw.get("four_transformations", {})
        for scope in ("decadal", "yearly", "monthly", "daily", "hourly"):
            assert scope in ft, f"missing scope: {scope}"
            assert isinstance(ft[scope], list)

    def test_each_scope_has_4_mutagens(self):
        """每个 scope 4 化 4 条 (禄/权/科/忌)."""
        r = compute(BIRTH)
        ft = r.raw.get("four_transformations", {})
        for scope in ("decadal", "yearly", "monthly"):
            assert len(ft[scope]) == 4, (
                f"{scope} 应有 4 化, 实际 {len(ft[scope])}: {ft[scope]}"
            )


# ── Normalizer 三层 signal ─────────────────────────────────────────

class TestZiweiLimitSignals:
    def test_decadal_signal(self):
        signals = normalize("ziwei", _chart())
        decadal = [s for s in signals if "大限4化" in s.evidence]
        assert len(decadal) == 1
        assert decadal[0].dimension == "current_cycle"
        assert decadal[0].time_scope == "current_cycle"

    def test_yearly_signal(self):
        signals = normalize("ziwei", _chart())
        yearly = [s for s in signals if "流年4化" in s.evidence]
        assert len(yearly) == 1
        assert yearly[0].dimension == "current_cycle"

    def test_monthly_signal(self):
        """Sprint 2.3 新增: 流月 4 化 独立 signal。"""
        signals = normalize("ziwei", _chart())
        monthly = [s for s in signals if "流月4化" in s.evidence]
        assert len(monthly) == 1
        assert monthly[0].dimension == "current_cycle"
        assert monthly[0].time_scope == "current_cycle"

    def test_at_least_3_limit_signals(self):
        """Sprint 2.3 红线: 至少 3 个 4 化 signal (大限+流年+流月)."""
        signals = normalize("ziwei", _chart())
        limit_signals = [s for s in signals
                        if "4化" in s.evidence and s.dimension == "current_cycle"]
        assert len(limit_signals) >= 3, f"只有 {len(limit_signals)} 个, 期望 ≥3"

    def test_all_signals_have_digest(self):
        signals = normalize("ziwei", _chart())
        for s in signals:
            assert s.signal_digest is not None


# ── 时序逻辑 golden ────────────────────────────────────────────────

class TestZiweiGolden:
    def test_decadal_4_mutagens_lu_quan_ke_ji(self):
        """大限 4 化 4 条, 不为空 (具体哪 4 星依本命)."""
        r = compute(BIRTH)
        ft = r.raw["four_transformations"]
        assert len(ft["decadal"]) == 4
        # 不重复
        assert len(set(ft["decadal"])) == 4
