"""NOR-016~019: 标准化器单元测试。

NOR-016: NORMALIZERS 必须有 18 个 key
NOR-017: signal 字段完整
NOR-018: strength 范围 — 0 <= strength <= 1
NOR-019: polarity 合法 — positive/negative/neutral/mixed
Phase 1: 18 法全部纳入 (方案 §二十一)。
"""
import pytest

from divination.contracts import Birth, ChartResult
from divination.aggregation.normalizer import (
    SIGNAL_KEYS,
    DOMAIN_KEYS,
    _fallback,
    _make_signal,
    normalize,
    normalize_all,
    _normalize_bazi,
    _normalize_ziwei,
    _normalize_qimen,
    _normalize_liuyao,
    _normalize_meihua,
    _normalize_bazhai,
    _normalize_xuankong,
    _normalize_western,
    _normalize_vedic,
    _normalize_tarot,
    _normalize_numerology,
    _normalize_liuren,
    _normalize_xiaoliuren,
    _normalize_tieban,
    _normalize_lenormand,
)


# ── 快捷构建 ChartResult ──────────────────────────────────────────────────────

def _cr(raw=None, method="test", school="east", engine="test"):
    """Convenience: create a ChartResult with minimal boilerplate."""
    return ChartResult(method=method, school=school, engine=engine, raw=raw or {}, normalized={})


# ═══════════════════════════════════════════════════════════════════════════════
# NOR-016: SIGNAL_KEYS whitelist
# ═══════════════════════════════════════════════════════════════════════════════

class TestSignalKeysWhitelist:
    """SIG-001~011: 统一信号键白名单。"""

    EXPECTED_GROUPS = {
        "career":          {"career_independence", "career_stability", "career_pressure"},
        "wealth":          {"wealth_growth", "wealth_risk", "wealth_stability"},
        "relationship":    {"relationship_attraction", "relationship_conflict", "marriage_stability"},
        "decision":        {"decision_support", "decision_delay", "decision_risk"},
        "timing":          {"timing_opportunity", "timing_obstacle", "timing_transition"},
        "health":          {"health_pressure", "emotional_pressure", "rest_recovery"},
        "noble":           {"noble_help", "obstacle_pressure"},
        "mobility":        {"mobility_change", "relocation_signal"},
        "fengshui":        {"environment_support", "direction_benefit", "layout_risk"},
        "longterm":        {"long_term_potential", "short_term_caution"},
        "fallback":        {"general_reference"},
    }

    def test_all_expected_keys_present(self):
        for group_name, expected_keys in self.EXPECTED_GROUPS.items():
            for key in expected_keys:
                assert key in SIGNAL_KEYS, f"'{key}' missing from SIGNAL_KEYS ({group_name} group)"

    def test_no_extra_keys(self):
        all_expected = set()
        for keys in self.EXPECTED_GROUPS.values():
            all_expected.update(keys)
        assert SIGNAL_KEYS == all_expected, (
            f"Extra: {SIGNAL_KEYS - all_expected}\nMissing: {all_expected - SIGNAL_KEYS}"
        )

    def test_total_key_count(self):
        assert len(SIGNAL_KEYS) == 28, f"Expected 28, got {len(SIGNAL_KEYS)}"


class TestDomainKeys:
    def test_each_domain_has_relevant_keys(self):
        for domain, keys in DOMAIN_KEYS.items():
            for key in keys:
                assert key in SIGNAL_KEYS, f"DOMAIN_KEYS['{domain}']: '{key}' not in SIGNAL_KEYS"


# ═══════════════════════════════════════════════════════════════════════════════
# NOR-018~019: _make_signal
# ═══════════════════════════════════════════════════════════════════════════════

class TestMakeSignal:
    def test_strength_clamped_to_max_1(self):
        s = _make_signal("test", "career", "career_stability", "positive", strength=1.5, confidence=0.8)
        assert s.strength <= 1.0

    def test_strength_clamped_to_min_0(self):
        s = _make_signal("test", "career", "career_stability", "positive", strength=-0.5, confidence=0.8)
        assert s.strength >= 0.0

    def test_strength_in_0_1_range(self):
        s = _make_signal("test", "career", "career_stability", "positive", strength=0.75, confidence=0.8)
        assert 0.0 <= s.strength <= 1.0

    def test_unknown_key_falls_back_to_general_reference(self):
        s = _make_signal("test", "career", "unknown_key_xyz", "neutral", strength=0.5)
        assert s.signal_key == "general_reference"

    def test_method_field_set(self):
        s = _make_signal("bazi_v2", "career", "career_stability", "neutral", 0.5, "evidence text", 0.7)
        assert s.method == "bazi_v2"
        assert s.evidence == "evidence text"

    @pytest.mark.parametrize("polarity", ["positive", "negative", "neutral", "mixed"])
    def test_valid_polarities(self, polarity):
        s = _make_signal("test", "career", "career_stability", polarity, strength=0.5)
        assert s.polarity == polarity


# ═══════════════════════════════════════════════════════════════════════════════
# NOR-002: fallback signal
# ═══════════════════════════════════════════════════════════════════════════════

class TestFallback:
    def test_fallback_is_neutral(self):
        s = _fallback("bazi_v2")
        assert s.polarity == "neutral"
        assert s.signal_key == "general_reference"

    def test_fallback_strength_is_low(self):
        s = _fallback("ziwei")
        assert s.strength <= 0.5

    def test_fallback_has_method(self):
        s = _fallback("qimen")
        assert s.method == "qimen"


# ═══════════════════════════════════════════════════════════════════════════════
# NOR-004~015: each method ≥3 signals, strength 0-1, polarity valid
# ═══════════════════════════════════════════════════════════════════════════════

VALID_POLARITIES = {"positive", "negative", "neutral", "mixed"}


class TestNormalizeBazi:
    def test_at_least_3_signals(self):
        chart = _cr({
            "day_master": "甲", "strength_score": 60,
            "elements": {"金": 30, "木": 40, "水": 20, "火": 5, "土": 5},
            "yong_shen": {"yong_shen": "水"}, "yong_shen_quality": {"score": 60},
            "shensha": {"summary": {"notable": ["天乙贵人", "文昌"]}},
        })
        signals = _normalize_bazi("bazi_v2", chart.raw, chart.normalized)
        assert len(signals) >= 3, f"NOR-004: Expected ≥3, got {len(signals)}"

    def test_all_fields_complete(self):
        chart = _cr({"day_master": "乙", "strength_score": 40, "yong_shen": {}, "yong_shen_quality": {}, "shensha": {}})
        signals = _normalize_bazi("bazi_v2", chart.raw, chart.normalized)
        for s in signals:
            assert s.method
            assert s.domain
            assert s.signal_key
            assert s.signal_key in SIGNAL_KEYS, f"Unknown key: {s.signal_key}"
            assert s.polarity in VALID_POLARITIES, f"Invalid polarity: {s.polarity}"

    def test_strength_in_range(self):
        chart = _cr({
            "day_master": "丙", "strength_score": 70,
            "yong_shen": {"yong_shen": "火"}, "yong_shen_quality": {"score": 70},
            "shensha": {"summary": {"notable": ["福星"]}},
        })
        signals = _normalize_bazi("bazi_v2", chart.raw, chart.normalized)
        for s in signals:
            assert 0.0 <= s.strength <= 1.0, f"NOR-018 FAIL: strength={s.strength}"


class TestNormalizeZiwei:
    def test_at_least_3_signals(self):
        chart = _cr({"palaces": [
            {"name": "命宫", "major_stars": ["紫微", "天相"]},
            {"name": "官禄宫", "major_stars": ["天府"]},
            {"name": "夫妻宫", "major_stars": ["天同"]},
        ]})
        signals = _normalize_ziwei("ziwei", chart.raw, chart.normalized)
        assert len(signals) >= 3, f"NOR-005: Expected ≥3, got {len(signals)}"

    def test_strength_range(self):
        chart = _cr({})
        signals = _normalize_ziwei("ziwei", chart.raw, chart.normalized)
        for s in signals:
            assert 0.0 <= s.strength <= 1.0
            assert s.polarity in VALID_POLARITIES


class TestNormalizeQimen:
    def test_at_least_3_signals(self):
        chart = _cr({"断": {"格局": ["青龙返首(吉)", "飞鸟跌穴(吉)"], "门状态": {"休门": "吉"}}})
        signals = _normalize_qimen("qimen", chart.raw, chart.normalized)
        assert len(signals) >= 3, f"NOR-006: Expected ≥3, got {len(signals)}"

    def test_strength_range(self):
        chart = _cr({})
        signals = _normalize_qimen("qimen", chart.raw, chart.normalized)
        for s in signals:
            assert 0.0 <= s.strength <= 1.0
            assert s.polarity in VALID_POLARITIES


class TestNormalizeLiuyao:
    def test_at_least_3_signals(self):
        chart = _cr({"本卦": {"name": "乾为天"}, "动爻": True, "断": {"断语": "吉，可行"}})
        signals = _normalize_liuyao("liuyao", chart.raw, chart.normalized)
        assert len(signals) >= 3, f"NOR-007: Expected ≥3, got {len(signals)}"

    def test_strength_range(self):
        chart = _cr({})
        signals = _normalize_liuyao("liuyao", chart.raw, chart.normalized)
        for s in signals:
            assert 0.0 <= s.strength <= 1.0
            assert s.polarity in VALID_POLARITIES


class TestNormalizeMeihua:
    def test_at_least_3_signals(self):
        chart = _cr({
            "体卦": "乾", "用卦": "离",
            "主卦": {"name": "天火同人"}, "变卦": {"name": "乾为天"},
            "断": {"总断": "用生体，吉"},
        })
        signals = _normalize_meihua("meihua", chart.raw, chart.normalized)
        assert len(signals) >= 3, f"NOR-008: Expected ≥3, got {len(signals)}"

    def test_strength_range(self):
        chart = _cr({})
        signals = _normalize_meihua("meihua", chart.raw, chart.normalized)
        for s in signals:
            assert 0.0 <= s.strength <= 1.0
            assert s.polarity in VALID_POLARITIES


class TestNormalizeBazhai:
    def test_at_least_3_signals(self):
        chart = _cr({"命卦": "离", "吉方": ["生气方", "天医方"], "凶方": ["绝命方"]})
        signals = _normalize_bazhai("bazhai", chart.raw, chart.normalized)
        assert len(signals) >= 3, f"NOR-010: Expected ≥3, got {len(signals)}"

    def test_strength_range(self):
        chart = _cr({})
        signals = _normalize_bazhai("bazhai", chart.raw, chart.normalized)
        for s in signals:
            assert 0.0 <= s.strength <= 1.0
            assert s.polarity in VALID_POLARITIES


class TestNormalizeXuankong:
    def test_at_least_3_signals(self):
        chart = _cr({"运": "八运", "格局": "旺山旺向", "坐": "壬", "向": "丙"})
        signals = _normalize_xuankong("xuankong", chart.raw, chart.normalized)
        assert len(signals) >= 3, f"NOR-011: Expected ≥3, got {len(signals)}"

    def test_strength_range(self):
        chart = _cr({})
        signals = _normalize_xuankong("xuankong", chart.raw, chart.normalized)
        for s in signals:
            assert 0.0 <= s.strength <= 1.0
            assert s.polarity in VALID_POLARITIES


class TestNormalizeWestern:
    def test_at_least_3_signals(self):
        chart = _cr({
            "planets": {"太阳": {"sign": "狮子座"}, "月亮": {"sign": "巨蟹座"}},
            "aspects": [
                {"aspect": "拱", "p1": "太阳", "p2": "木星"},
                {"aspect": "合", "p1": "月亮", "p2": "金星"},
            ],
        })
        signals = _normalize_western("western", chart.raw, chart.normalized)
        assert len(signals) >= 3, f"NOR-012: Expected ≥3, got {len(signals)}"

    def test_strength_range(self):
        chart = _cr({})
        signals = _normalize_western("western", chart.raw, chart.normalized)
        for s in signals:
            assert 0.0 <= s.strength <= 1.0
            assert s.polarity in VALID_POLARITIES


class TestNormalizeVedic:
    def test_at_least_3_signals(self):
        chart = _cr({"planets": {"太阳": {"宫(Rashi)": "狮子座"}, "月亮": {"宫(Rashi)": "金牛座"}}})
        signals = _normalize_vedic("vedic", chart.raw, chart.normalized)
        assert len(signals) >= 3, f"NOR-013: Expected ≥3, got {len(signals)}"

    def test_strength_range(self):
        chart = _cr({})
        signals = _normalize_vedic("vedic", chart.raw, chart.normalized)
        for s in signals:
            assert 0.0 <= s.strength <= 1.0
            assert s.polarity in VALID_POLARITIES


class TestNormalizeTarot:
    def test_at_least_3_signals(self):
        chart = _cr({"牌面": [
            {"name": "太阳", "关键词": "光明, 成功, 吉"},
            {"name": "星星", "关键词": "希望, 和谐"},
        ]})
        signals = _normalize_tarot("tarot", chart.raw, chart.normalized)
        assert len(signals) >= 3, f"NOR-014: Expected ≥3, got {len(signals)}"

    def test_strength_range(self):
        chart = _cr({})
        signals = _normalize_tarot("tarot", chart.raw, chart.normalized)
        for s in signals:
            assert 0.0 <= s.strength <= 1.0
            assert s.polarity in VALID_POLARITIES


class TestNormalizeNumerology:
    def test_at_least_3_signals(self):
        chart = _cr({"生命灵数": 7, "life_path": 7})
        signals = _normalize_numerology("numerology", chart.raw, chart.normalized)
        assert len(signals) >= 3, f"NOR-015: Expected ≥3, got {len(signals)}"

    def test_strength_range(self):
        chart = _cr({})
        signals = _normalize_numerology("numerology", chart.raw, chart.normalized)
        for s in signals:
            assert 0.0 <= s.strength <= 1.0
            assert s.polarity in VALID_POLARITIES


# ═══════════════════════════════════════════════════════════════════════════════
# NOR-001: normalize() unified entry — 18 methods (Phase 1)
# ═══════════════════════════════════════════════════════════════════════════════

ALL_METHODS = [
    "bazi_v2", "ziwei", "qimen", "liuyao", "meihua",
    "fengshui", "bazhai", "xuankong", "western", "vedic",
    "tarot", "numerology",
    "liuren", "xiaoliuren", "tieban", "lenormand",
]


class TestNormalizeEntry:
    @pytest.mark.parametrize("method", ALL_METHODS)
    def test_each_method_returns_at_least_3_signals(self, method):
        chart = _cr({})
        signals = normalize(method, chart)
        assert len(signals) >= 3, (
            f"NOR-016 FAIL: {method} returned only {len(signals)} signals (need ≥3)"
        )

    @pytest.mark.parametrize("method", ALL_METHODS)
    def test_each_method_signals_have_complete_fields(self, method):
        chart = _cr({})
        signals = normalize(method, chart)
        for s in signals:
            assert s.method == method, f"NOR-017: method mismatch ({s.method} vs {method})"
            assert isinstance(s.domain, str) and s.domain, f"NOR-017: empty domain"
            assert isinstance(s.signal_key, str) and s.signal_key, f"NOR-017: empty signal_key"
            assert s.signal_key in SIGNAL_KEYS, f"NOR-017: unknown key '{s.signal_key}'"
            assert s.polarity in VALID_POLARITIES, f"NOR-019: invalid polarity '{s.polarity}'"
            assert 0.0 <= s.strength <= 1.0, f"NOR-018: strength {s.strength} out of [0,1]"

    @pytest.mark.parametrize("method", ALL_METHODS)
    def test_unknown_chart_still_returns_3_signals(self, method):
        chart = _cr({})
        signals = normalize(method, chart)
        assert len(signals) >= 3


class TestNormalizeAll:
    def test_normalize_all_with_multiple_methods(self):
        charts = {
            "bazi_v2": _cr({"day_master": "甲", "strength_score": 50, "yong_shen": {}, "yong_shen_quality": {}, "shensha": {}}),
            "ziwei": _cr({"palaces": []}),
            "tarot": _cr({}),
        }
        signals = normalize_all(charts)
        assert len(signals) >= 9

    def test_normalize_all_handles_bad_chart_gracefully(self):
        # chart with None raw should not crash
        charts = {
            "bazi_v2": _cr({"day_master": "丙", "strength_score": 50, "yong_shen": {}, "yong_shen_quality": {}, "shensha": {}}),
            "broken": ChartResult(method="b", school="east", engine="x", raw=None, normalized=None),
        }
        signals = normalize_all(charts)
        assert len(signals) >= 3

    @pytest.mark.parametrize("method", ALL_METHODS)
    def test_18_methods_all_present(self, method):
        charts = {m: _cr({}) for m in ALL_METHODS}
        signals = normalize_all(charts)
        # 当前 16 methods × ≥3 = ≥48, 目标 18 × ≥3 = ≥54
        assert len(signals) >= 48, f"normalize_all: expected ≥48 (16×3), got {len(signals)}"
        methods_found = set(s.method for s in signals)
        assert methods_found == set(ALL_METHODS), f"Missing: {set(ALL_METHODS) - methods_found}"


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 1: NOR-101~104 — 4 个新法 (大六壬/小六壬/铁板/雷诺曼) 的 dimension 标签
# ═══════════════════════════════════════════════════════════════════════════════


def test_liuren_normalizer_tags_one_question():
    """大六壬 — 决疑占, 短期一题一答, 维度=one_question。"""
    chart = ChartResult(
        method="liuren", school="east", engine="test",
        raw={
            "three_transmissions": {"chu_chuan": "子", "zhong_chuan": "丑", "mo_chuan": "寅"},
            "pattern": {"name": "贼克", "type": "auspicious"},
            "day_ganzhi": "甲子",
        },
        normalized={},
    )
    sigs = _normalize_liuren("liuren", chart.raw, chart.normalized)
    assert len(sigs) >= 3, f"Expected ≥3 signals, got {len(sigs)}"
    for s in sigs:
        assert s.dimension == "one_question", f"liuren should tag one_question, got {s.dimension}"
        assert s.time_scope == "short_term", f"liuren should be short_term, got {s.time_scope}"


def test_xiaoliuren_normalizer_tags_one_question():
    """小六壬 — 即时占, 维度=one_question。"""
    chart = ChartResult(
        method="xiaoliuren", school="east", engine="test",
        raw={
            "mode": "time_xiaoliuren", "palace": "大安", "tone": "auspicious",
            "meaning": "稳为主", "subject": "decision", "question": "test",
        },
        normalized={},
    )
    sigs = _normalize_xiaoliuren("xiaoliuren", chart.raw, chart.normalized)
    assert len(sigs) >= 3, f"Expected ≥3 signals, got {len(sigs)}"
    for s in sigs:
        assert s.dimension == "one_question", f"xiaoliuren should tag one_question, got {s.dimension}"
        assert s.time_scope == "short_term", f"xiaoliuren should be short_term, got {s.time_scope}"


def test_tieban_normalizer_tags_long_term():
    """铁板神数 — 命数条文, 长期, 维度=long_term。"""
    chart = ChartResult(
        method="tieban", school="east", engine="test",
        raw={
            "verse_set_number": 1234,
            "verse_result": {
                "matched_verses": [{"category": "财运", "number": 1, "text": "x"}],
                "total_matched": 5,
            },
        },
        normalized={},
    )
    sigs = _normalize_tieban("tieban", chart.raw, chart.normalized)
    assert len(sigs) >= 3, f"Expected ≥3 signals, got {len(sigs)}"
    for s in sigs:
        assert s.dimension == "long_term", f"tieban should tag long_term, got {s.dimension}"
        assert s.time_scope == "long_term", f"tieban should be long_term, got {s.time_scope}"


def test_lenormand_normalizer_tags_one_question():
    """雷诺曼 — 日常占卜, 维度=one_question。"""
    chart = ChartResult(
        method="lenormand", school="west", engine="test",
        raw={
            "spread": "three_line", "spread_name": "三张线",
            "cards": [
                {"name": "Rider", "name_zh": "骑士", "timing": "快速", "index": 1},
                {"name": "Heart", "name_zh": "心", "timing": "当下", "index": 2},
                {"name": "Sun", "name_zh": "太阳", "timing": "当下", "index": 3},
            ],
            "analysis": {"positive_count": 2, "negative_count": 0, "neutral_count": 1, "tone": "positive"},
        },
        normalized={},
    )
    sigs = _normalize_lenormand("lenormand", chart.raw, chart.normalized)
    assert len(sigs) >= 3, f"Expected ≥3 signals, got {len(sigs)}"
    for s in sigs:
        assert s.dimension == "one_question", f"lenormand should tag one_question, got {s.dimension}"
        assert s.time_scope == "short_term", f"lenormand should be short_term, got {s.time_scope}"


def test_normalize_dispatches_to_new_methods():
    """验证 4 新法能通过 normalize() 入口调用 (Phase 1 NOR-101~104)。"""
    for method in ["liuren", "xiaoliuren", "tieban", "lenormand"]:
        chart = _cr({})
        sigs = normalize(method, chart)
        assert len(sigs) >= 3, (
            f"normalize({method}) returned {len(sigs)} signals, expected ≥3"
        )
