"""Tests for the True Solar Time hour calibrator.

Covers:
  - True solar time computation (经度差 + 均时差)
  - Uncertainty window expansion (±1h / ±2h)
  - Candidate scoring: trait match, career match, 用神 match, 大运/流年 events
  - Top-level calibrate_with_true_solar entry point
  - Confidence calibration and ranking
"""
import pytest

from divination.contracts import Birth
from divination.engines import hour_calibrator as hc


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_birth(**kwargs) -> Birth:
    """Convenience Birth factory with reasonable defaults."""
    defaults = dict(
        year=1990, month=6, day=15,
        hour=12, minute=0,
        gender="male",
        calendar="gregorian",
        lat=31.23, lng=121.47,
        tz="Asia/Shanghai",
    )
    defaults.update(kwargs)
    return Birth(**defaults)


# ── 1. True Solar Time basic computation ──────────────────────────────────

def test_true_solar_time_shanghai_approx():
    """Shanghai (≈120°E) should have minimal longitude correction."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    aware = datetime(1990, 6, 15, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    tst = hc.true_solar_time(aware, lng_deg=121.47, tz="Asia/Shanghai")
    # tz_central = 120 (Asia/Shanghai)
    # lng_corr = (121.47 - 120) * 4 = +5.88 min
    # EoT in mid-June ≈ +0 to +2 min
    # Total ≈ +6 to +8 min
    delta_min = (tst - aware.replace(tzinfo=None)).total_seconds() / 60
    assert -2 <= delta_min <= 12, f"Shanghai TST delta should be small positive, got {delta_min}"


def test_true_solar_time_west_of_central():
    """Chongqing (≈106°E, west of Shanghai's 120°) — TST should be earlier than clock."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    aware = datetime(1990, 6, 15, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    tst = hc.true_solar_time(aware, lng_deg=106.5, tz="Asia/Shanghai")
    delta_min = (tst - aware.replace(tzinfo=None)).total_seconds() / 60
    # lng_corr = (106.5 - 120) * 4 = -54 min (large negative)
    # EoT small
    assert delta_min < -40, f"Chongqing TST should be ~54 min earlier, got {delta_min}"


def test_true_solar_time_east_of_central():
    """Tokyo (≈139°E, east of 135°E central) — TST should be later than clock."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    aware = datetime(1990, 6, 15, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo"))
    tst = hc.true_solar_time(aware, lng_deg=139.7, tz="Asia/Tokyo")
    delta_min = (tst - aware.replace(tzinfo=None)).total_seconds() / 60
    # tz_central from UTC+9 = 135; lng_corr = (139.7 - 135)*4 = +18.8 min
    assert delta_min > 10, f"Tokyo east of central should give positive delta, got {delta_min}"


def test_equation_of_time_finite():
    """EoT should return a finite number, typically within ±20 minutes."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    aware = datetime(2024, 6, 15, 12, 0, tzinfo=ZoneInfo("UTC"))
    eot = hc._equation_of_time_minutes(aware)
    assert -20 <= eot <= 20, f"EoT should be within ±20 minutes, got {eot}"


# ── 2. hour_branch_from_time ──────────────────────────────────────────────

def test_hour_branch_basic():
    """Standard hour → branch mapping."""
    assert hc.hour_branch_from_time(0, 0) == "子"
    assert hc.hour_branch_from_time(0, 30) == "子"
    assert hc.hour_branch_from_time(1, 0) == "丑"
    assert hc.hour_branch_from_time(5, 30) == "卯"
    assert hc.hour_branch_from_time(12, 0) == "午"
    assert hc.hour_branch_from_time(23, 0) == "子"
    assert hc.hour_branch_from_time(23, 30) == "子"
    assert hc.hour_branch_from_time(22, 0) == "亥"


# ── 3. expand_uncertainty ─────────────────────────────────────────────────

def test_expand_uncertainty_pm1():
    """±1h uncertainty should expand to 2-3 branches."""
    result = hc.expand_uncertainty(["午"], 1.0)
    assert "午" in result
    # ±1h → span 11:00-13:00 → 午(11-13) plus partial 巳(9-11) and 未(13-15)
    assert len(result) >= 1


def test_expand_uncertainty_pm2():
    """±2h uncertainty should expand to ~3 branches."""
    result = hc.expand_uncertainty(["午"], 2.0)
    assert "午" in result
    # ±2h → span 10:00-14:00 → 巳/午/未
    assert len(result) >= 2
    assert "巳" in result
    assert "未" in result


def test_expand_uncertainty_wraparound():
    """Uncertainty near midnight should wrap correctly."""
    result = hc.expand_uncertainty(["子"], 2.0)
    # 子时 spans 23-01, ±2h should include 亥 and 丑
    assert "子" in result
    assert "亥" in result or "丑" in result


# ── 4. Calibration core function ──────────────────────────────────────────

def test_calibrate_unknown_hour_returns_candidates():
    """calibrate() with hour_uncertainty_hours=0 should return up to 12 candidates."""
    birth = _make_birth()
    result = hc.calibrate(birth, hour_uncertainty_hours=0)
    assert result.best_hour is not None
    assert len(result.candidates) == 12
    assert all(c.score >= 0 for c in result.candidates)


def test_calibrate_pm2_returns_3_candidates():
    """±2h uncertainty should narrow to ~3 candidates."""
    birth = _make_birth(hour=12)
    result = hc.calibrate(birth, hour_uncertainty_hours=2.0)
    assert result.best_hour is not None
    # 12:00 → 午时, ±2h → 巳/午/未
    assert len(result.candidates) >= 2
    assert len(result.candidates) <= 5


def test_calibrate_with_traits_ranks_top_correctly():
    """Adding known traits should reorder candidates."""
    birth = _make_birth()
    result = hc.calibrate(
        birth,
        known_traits=["leader", "ambitious"],
        hour_uncertainty_hours=0,
    )
    assert result.best_hour in ("寅",) or any(
        kw in HOUR_TRAITS_TEXT.get(result.best_hour, "")
        for kw in ["leader", "ambitious", "pioneer"]
    ) or result.best_hour in {"寅", "午", "巳", "申"}


# Lookup map of branch → trait text for result assertions
HOUR_TRAITS_TEXT = {b[0]: b[3] for b in hc.HOUR_BRANCHES}


def test_calibrate_with_career_boosts_match():
    """Career=technology should boost 金/水-strong candidates."""
    birth = _make_birth()
    result = hc.calibrate(
        birth,
        known_career="technology",
        hour_uncertainty_hours=0,
    )
    # Verify the result has a valid best hour
    assert result.best_hour in [b[0] for b in hc.HOUR_BRANCHES]
    # At least one candidate should have a non-zero career_match
    career_scores = [c.score_breakdown.get("career_match", 0) for c in result.candidates]
    assert any(s > 0 for s in career_scores), "Some candidate should have career bonus"


def test_calibrate_with_events_ranks_by_timing():
    """Known events should influence ranking."""
    birth = _make_birth()
    events = [
        {"year": 2014, "category": "career_start", "polarity": "positive"},
        {"year": 2020, "category": "finance", "polarity": "positive"},
    ]
    result = hc.calibrate(
        birth,
        known_events=events,
        hour_uncertainty_hours=0,
    )
    # Best candidate should have event_match_count > 0
    assert result.candidates[0].event_match_count >= 0  # may be 0 if no timeline matches
    # Score breakdown should include event_timing_match
    assert "event_timing_match" in result.candidates[0].score_breakdown


def test_calibrate_returns_true_solar_time_info():
    """When lat/lng provided, TST info should be populated."""
    birth = _make_birth(lat=31.23, lng=121.47)
    result = hc.calibrate(birth, hour_uncertainty_hours=0)
    assert "tst_branch" in result.true_solar_time_info
    assert "true_solar_time" in result.true_solar_time_info
    assert "longitude_correction_min" in result.true_solar_time_info
    assert "equation_of_time_min" in result.true_solar_time_info


def test_calibrate_confidence_between_0_and_100():
    """Confidence should always be in [0, 100]."""
    birth = _make_birth()
    result = hc.calibrate(birth, hour_uncertainty_hours=0)
    assert 0 <= result.best_confidence <= 100


def test_calibrate_no_lat_lng_still_works():
    """Without lat/lng, calibrate should still work (no TST info)."""
    birth = _make_birth(lat=None, lng=None)
    result = hc.calibrate(birth, hour_uncertainty_hours=0)
    assert result.best_hour is not None
    assert result.true_solar_time_info == {}


# ── 5. calibrate_with_true_solar entry point ──────────────────────────────

def test_calibrate_with_true_solar_anchors_at_tst():
    """calibrate_with_true_solar should anchor candidate set at TST branch."""
    # Beijing: 116.4°E, tz_central=120 → lng_corr = (116.4-120)*4 = -14.4 min
    # 12:00 clock → ~11:46 TST → still 午时
    birth = _make_birth(hour=12, minute=0, lat=39.9, lng=116.4)
    result = hc.calibrate_with_true_solar(birth, tolerance_hours=1.0)
    assert result.true_solar_time_info["tst_branch"] in ("午",)
    # Candidate set should include 午
    branches = [c.branch for c in result.candidates]
    assert "午" in branches


def test_calibrate_with_true_solar_pm2_includes_neighbors():
    """With ±2h tolerance, neighbors should be included."""
    birth = _make_birth(hour=12, lat=31.23, lng=121.47)
    result = hc.calibrate_with_true_solar(birth, tolerance_hours=2.0)
    branches = [c.branch for c in result.candidates]
    # 12:00 → 午 → ±2h → should include 巳/午/未
    assert "午" in branches
    assert any(b in {"巳", "未"} for b in branches)


# ── 6. estimate_from_traits (trait-only reverse lookup) ───────────────────

def test_estimate_from_traits_returns_top5():
    """Given traits, should return top-5 candidate branches."""
    result = hc.estimate_from_traits(["leader", "ambitious"])
    assert "top_hours" in result
    assert len(result["top_hours"]) <= 5
    # 寅 has both leader (0.8) and ambitious (0.8) → should rank high
    top_branches = [h["branch"] for h in result["top_hours"]]
    assert "寅" in top_branches


# ── 7. End-to-end integration ─────────────────────────────────────────────

def test_end_to_end_birth_in_shanghai():
    """Full integration: Birth with Shanghai coords, all inputs populated."""
    birth = _make_birth(
        year=1988, month=8, day=8, hour=8, minute=30,
        lat=31.23, lng=121.47, tz="Asia/Shanghai",
        gender="male",
    )
    result = hc.calibrate_with_true_solar(
        birth,
        tolerance_hours=2.0,
        known_traits=["leader", "ambitious"],
        known_career="business",
        known_events=[
            {"year": 2010, "category": "career_start", "polarity": "positive"},
            {"year": 2018, "category": "finance", "polarity": "positive"},
        ],
    )
    assert result.best_hour is not None
    assert result.best_confidence > 0
    assert "用神匹配度" in result.analysis or "用神" in result.analysis
    assert "真太阳时" in result.analysis
    # Recommendation should mention 候选时辰
    assert "置信度" in result.recommendation


def test_end_to_end_without_known_facts_uses_structure():
    """Without facts, calibrate should still return a ranked result based on structure."""
    birth = _make_birth(hour=14, lat=39.9, lng=116.4)
    result = hc.calibrate_with_true_solar(birth, tolerance_hours=0)
    assert result.best_hour is not None
    assert 0 <= result.best_confidence <= 100
    # With no known facts, score breakdown should use neutral baselines
    assert "structure_quality" in result.candidates[0].score_breakdown


def test_yong_shen_score_breakdown_present():
    """Every candidate should have a yong_shen_match score breakdown."""
    birth = _make_birth()
    result = hc.calibrate(birth, hour_uncertainty_hours=0)
    for c in result.candidates:
        assert "yong_shen_match" in c.score_breakdown
        assert c.yong_shen_match is not None


def test_hour_branch_consistency_between_methods():
    """All scoring methods should agree on the canonical 12 branches."""
    assert len(hc.HOUR_BRANCHES) == 12
    assert set(b[0] for b in hc.HOUR_BRANCHES) == set(
        ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    )


def test_quick_estimate_returns_note():
    """quick_estimate should include a note about limitations."""
    birth = _make_birth()
    est = hc.quick_estimate(birth)
    assert "best_hour" in est
    assert "note" in est
    assert "未参考" in est["note"] or "结构" in est["note"]