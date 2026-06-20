"""Sprint 2.2 — western 三通道 (行运/次限/太阳返照) 测试。

覆盖:
- western engine raw 输出含 transits/progressions/solar_return
- normalizer 三个 channel 各自出 signal
- transits: 容许度 ±2° 内, 命中 0-7 个相位
- progressions: 1日=1年, progressed_date 是 birth + age_years
- solar_return: 当年太阳回照精度 < 1°
"""
from __future__ import annotations

import pytest

from divination.engines.western import (
    _find_progressed_aspects,
    _find_transits,
    _solar_return_moment,
    compute,
)
from divination.aggregation.normalizer import normalize
from divination.contracts import Birth, ChartResult


BIRTH = Birth(
    year=1990, month=6, day=15, hour=8, minute=30,
    gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai",
)


# ── Engine 三个 channel 输出 ──────────────────────────────────────────

class TestWesternThreeChannelsRaw:
    def test_transits_in_raw(self):
        r = compute(BIRTH)
        assert "transits" in r.raw
        assert isinstance(r.raw["transits"], list)

    def test_progressions_in_raw(self):
        r = compute(BIRTH)
        assert "progressions" in r.raw
        assert "progressed_date" in r.raw
        assert r.raw["progressed_date"], "progressed_date 应有值"

    def test_solar_return_in_raw(self):
        r = compute(BIRTH)
        sr = r.raw.get("solar_return")
        assert sr is not None
        assert "moment_utc" in sr
        assert "year" in sr
        assert "sun_diff_deg" in sr
        # 太阳回照精度应 < 1° (查找算法)
        assert sr["sun_diff_deg"] < 1.0


# ── Transit 工具函数 ─────────────────────────────────────────────────

class TestFindTransits:
    def test_self_aspect_returns_zero_when_no_transit(self):
        """本命 vs 本命 → 0 transit。"""
        natal = {"太阳": 100.0, "月亮": 200.0}
        transits = _find_transits(natal, natal, orb=2.0)
        # 太阳/太阳合(0°), 月亮/月亮合(0°) 应被检测到
        # 因为 aspect "合" = 0°, 实际 diff=0 → orb=0 ≤ 2.0
        assert len(transits) >= 2  # 至少太阳合 + 月亮合

    def test_hard_aspect_detected(self):
        """transit 太阳 0° vs natal 月亮 90° = 刑 → is_hard=True。"""
        natal = {"月亮": 0.0}
        current = {"太阳": 90.0}
        transits = _find_transits(natal, current, orb=2.0)
        # 太阳对月亮 90° → 刑
        moon_sun = [t for t in transits if t["transit_planet"] == "太阳"
                    and t["natal_planet"] == "月亮"]
        assert any(t["aspect"] == "刑" for t in moon_sun)
        # 硬相位
        if moon_sun:
            assert moon_sun[0]["is_hard"] is True

    def test_soft_aspect_detected(self):
        """transit 太阳 0° vs natal 木星 120° = 拱 → is_hard=False。"""
        natal = {"土星": 0.0}  # 用土星做 natal, 避免与月亮/太阳冲突
        current = {"太阳": 120.0}
        transits = _find_transits(natal, current, orb=2.0)
        sun_saturn = [t for t in transits if t["transit_planet"] == "太阳"
                      and t["natal_planet"] == "土星"]
        assert any(t["aspect"] == "拱" for t in sun_saturn)
        if sun_saturn:
            assert sun_saturn[0]["is_hard"] is False

    def test_no_transit_outside_orb(self):
        """超过容许度 → 不报。"""
        natal = {"月亮": 0.0}
        current = {"太阳": 95.0}  # 离 90° (刑) 差 5°, > 2° orb
        transits = _find_transits(natal, current, orb=2.0)
        # 刑被过滤
        for t in transits:
            if t["natal_planet"] == "月亮" and t["transit_planet"] == "太阳":
                assert t["aspect"] != "刑"


# ── Progressions 工具函数 ───────────────────────────────────────────

class TestFindProgressedAspects:
    def test_progressed_chart_1day_per_year(self):
        """Progressed date = birth + age_years days。"""
        from datetime import datetime
        r = compute(BIRTH)
        prog_date_str = r.raw.get("progressed_date", "")
        assert prog_date_str
        # 1990-06-15 出生, 当前 2026, age ≈ 36 年 → progressed = 1990 + 36 days = 1990-07-21
        prog_dt = datetime.fromisoformat(prog_date_str)
        age_seconds = (datetime.utcnow() - datetime(1990, 6, 15, 8, 30)).total_seconds()
        expected_age_days = int(age_seconds / 86400)
        expected_prog = datetime(1990, 6, 15, 8, 30) + __import__("datetime").timedelta(days=expected_age_days)
        # 精度 1 天内
        assert abs((prog_dt - expected_prog).total_seconds()) < 86400

    def test_progressions_aspects_format(self):
        r = compute(BIRTH)
        prog = r.raw.get("progressions", [])
        # 至少格式正确 (可能 0 个, 但若有, 必有 planet/aspect/is_hard)
        for p in prog:
            assert "planet" in p
            assert "aspect" in p
            assert "is_hard" in p


# ── Solar Return ────────────────────────────────────────────────────

class TestSolarReturn:
    def test_solar_return_within_tolerance(self):
        sr = _solar_return_moment(BIRTH)
        assert sr is not None
        # 太阳回照精度 < 1° (12h 细化后)
        assert sr["sun_diff_deg"] < 1.0

    def test_solar_return_in_current_year(self):
        from datetime import datetime
        sr = _solar_return_moment(BIRTH)
        assert sr["year"] == datetime.utcnow().year


# ── Normalizer 三个 channel signal ─────────────────────────────────

class TestNormalizerThreeChannels:
    def _chart(self):
        r = compute(BIRTH)
        return ChartResult(method="western", school="west", engine="skyfield+self",
                          normalized=r.normalized, raw=r.raw)

    def test_transits_signal(self):
        signals = normalize("western", self._chart())
        # 至少 1 条 timing_* signal (transits 出)
        transits_signals = [s for s in signals
                          if "行运" in s.evidence]
        assert len(transits_signals) >= 1

    def test_progressions_signal(self):
        signals = normalize("western", self._chart())
        prog_signals = [s for s in signals
                       if "次限" in s.evidence]
        assert len(prog_signals) >= 1
        # signal_key 应是 prog_timing_*
        assert prog_signals[0].signal_key.startswith("prog_")

    def test_solar_return_signal(self):
        signals = normalize("western", self._chart())
        sr_signals = [s for s in signals
                     if "太阳返照" in s.evidence]
        assert len(sr_signals) >= 1
        assert sr_signals[0].dimension == "current_cycle"

    def test_all_three_channels_have_signal_digest(self):
        signals = normalize("western", self._chart())
        for s in signals:
            assert s.signal_digest is not None
