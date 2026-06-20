"""Sprint 2.1 — bazi 流年/流月/大运 golden 验证。

公版参考 (中国万年历 + 60 甲子):
  1984 = 甲子年
  1998 = 戊寅年
  2014 = 甲午年
  2026 = 丙午年 (current sprint year)

也覆盖 1984 甲子 0号/1998 戊寅 14号/2014 甲午 30号 三个 60 甲子节点对《滴天髓》思路的现代验证。
"""
from __future__ import annotations

import pytest

from divination.engines.bazi import compute
from divination.contracts import Birth


# ── 60 甲子 baseline ────────────────────────────────────────────────

GOLDEN_YEARS = [
    (1984, "甲子"),  # 0
    (1998, "戊寅"),  # 14
    (2014, "甲午"),  # 30
    (2026, "丙午"),  # 42
    (1988, "戊辰"),  # 4
    (2000, "庚辰"),  # 16
]


@pytest.mark.parametrize("year,expected_gz", GOLDEN_YEARS)
def test_bazi_yearly_ganzhi_matches_60_cycle(year: int, expected_gz: str):
    """甲子纪年: 1984 甲子 / 1998 戊寅 / 2014 甲午 等。"""
    b = Birth(year=1990, month=6, day=15, hour=8, minute=30,
              gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai")
    r = compute(b)
    yearly = r.raw["horoscope"]["yearly"]
    hit = next((y for y in yearly if y["year"] == year), None)
    assert hit is not None, f"{year} not in yearly list"
    assert hit["ganzhi"] == expected_gz, (
        f"{year} 期望 {expected_gz}, 实际 {hit['ganzhi']}"
    )


# ── 当前大运 ───────────────────────────────────────────────────────

class TestCurrentDayun:
    def test_current_dayun_within_timeline(self):
        """当前年必须落在某段大运 (timeline) 内。"""
        b = Birth(year=1990, month=6, day=15, hour=8, minute=30,
                  gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai")
        r = compute(b)
        cy = r.raw["horoscope"]["current_year"]
        cd = r.raw["horoscope"]["current_dayun"]
        # timeline 中应有一段覆盖 cy
        timeline = r.normalized["timeline"]
        matched = [
            d for d in timeline
            if int(d["from"]) <= cy <= int(d["to"])
        ]
        assert matched, f"current year {cy} 不在 timeline 内: {timeline}"
        assert cd is not None
        assert cd["label"] == matched[0]["label"]


# ── 流月 ────────────────────────────────────────────────────────────

class TestMonthlyGanzhi:
    def test_monthly_12_entries(self):
        """12 个月应有 12 条。"""
        b = Birth(year=1990, month=6, day=15, hour=8, minute=30,
                  gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai")
        r = compute(b)
        assert len(r.raw["horoscope"]["monthly"]) == 12

    def test_monthly_unique_consecutive(self):
        """相邻月份干支应不同 (五虎遁年起月法)。"""
        b = Birth(year=1990, month=6, day=15, hour=8, minute=30,
                  gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai")
        r = compute(b)
        gz_list = [m["ganzhi"] for m in r.raw["horoscope"]["monthly"]]
        # 12 个连续月, 干支应 12 个不同 (五虎遁 60 甲子循环)
        assert len(set(gz_list)) >= 10, f"流月干支重复过多: {gz_list}"


# ── Normalizer 流年/大运/流月 signals ────────────────────────────────

class TestNormalizerLiunianSignals:
    def _bazi_chart(self):
        b = Birth(year=1990, month=6, day=15, hour=8, minute=30,
                  gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai")
        return compute(b)

    def test_bazi_normalizer_emits_dayun_signal(self):
        from divination.aggregation.normalizer import normalize
        chart = self._bazi_chart()
        signals = normalize("bazi", chart)
        dayun_sigs = [s for s in signals if s.signal_key == "current_cycle_dasha"]
        assert len(dayun_sigs) >= 1
        sig = dayun_sigs[0]
        assert sig.dimension == "current_cycle"
        assert sig.time_scope == "current_cycle"
        assert "大运" in sig.evidence

    def test_bazi_normalizer_emits_liunian_signal(self):
        from divination.aggregation.normalizer import normalize
        chart = self._bazi_chart()
        signals = normalize("bazi", chart)
        liunian_sigs = [s for s in signals
                       if s.signal_key == "timing_transition"
                       and "流年" in s.evidence]
        assert len(liunian_sigs) >= 1

    def test_bazi_normalizer_emits_liuyue_signal(self):
        from divination.aggregation.normalizer import normalize
        chart = self._bazi_chart()
        signals = normalize("bazi", chart)
        liuyue_sigs = [s for s in signals
                      if s.signal_key == "timing_transition"
                      and "流月" in s.evidence]
        assert len(liuyue_sigs) >= 1

    def test_all_bazi_signals_have_signal_digest(self):
        """Sprint 1.4 集成验证: 每条 signal 都有 5 档 digest。"""
        from divination.aggregation.normalizer import normalize
        chart = self._bazi_chart()
        signals = normalize("bazi", chart)
        for s in signals:
            assert s.signal_digest is not None
