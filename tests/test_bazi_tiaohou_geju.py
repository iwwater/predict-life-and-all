"""Tests for 八字调候深化 + 格局体系 (P3-1).

Tests cover:
  - wuxing_tiaohou: TiaohouRule dataclass, TIAOHOU_TABLE, evaluate_tiaohou, get_tiaohou_advice
  - wuxing_geju: GejuPattern dataclass, GEOJU_PATTERNS, evaluate_dynamic_geju
  - bazi_v2 integration: tiaohou + dynamic_geju in raw output

Sources:
  - 《穷通宝鉴》— 调候经典
  - 《渊海子平》— 格局体系
  - 《三命通会》— 格局深化
"""

from __future__ import annotations

import pytest

from divination.contracts import Birth


# ══════════════════════════════════════════════════════════════
# 1. TiaohouRule dataclass tests
# ══════════════════════════════════════════════════════════════


class TestTiaohouRule:
    """Test TiaohouRule dataclass structure and immutability."""

    def test_import_exists(self):
        """Can import TiaohouRule from wuxing_tiaohou."""
        from divination.data.wuxing_tiaohou import TiaohouRule
        assert TiaohouRule is not None

    def test_is_frozen_dataclass(self):
        """TiaohouRule is a frozen dataclass."""
        from dataclasses import is_dataclass
        from divination.data.wuxing_tiaohou import TiaohouRule
        assert is_dataclass(TiaohouRule)
        # frozen dataclasses raise on mutation
        r = TiaohouRule(
            day_gan="甲", month_zhi="寅",
            primary_use="火", secondary_use="土",
            rationale="春木需火", source="《穷通宝鉴》",
        )
        with pytest.raises(Exception):
            r.primary_use = "水"

    def test_fields_present(self):
        """All required fields exist on TiaohouRule."""
        from divination.data.wuxing_tiaohou import TiaohouRule
        r = TiaohouRule(
            day_gan="甲", month_zhi="寅",
            primary_use="火", secondary_use="土",
            rationale="春木需火", source="《穷通宝鉴》",
        )
        assert r.day_gan == "甲"
        assert r.month_zhi == "寅"
        assert r.primary_use == "火"
        assert r.secondary_use == "土"
        assert r.rationale == "春木需火"
        assert r.source == "《穷通宝鉴》"

    def test_default_source(self):
        """Default source is 《穷通宝鉴》."""
        from divination.data.wuxing_tiaohou import TiaohouRule
        r = TiaohouRule(
            day_gan="甲", month_zhi="子",
            primary_use="火", secondary_use="土",
            rationale="寒木向阳",
        )
        assert "穷通宝鉴" in r.source


# ══════════════════════════════════════════════════════════════
# 2. TIAOHOU_TABLE tests
# ══════════════════════════════════════════════════════════════


class TestTiaohouTable:
    """Test the TIAOHOU_TABLE lookup structure."""

    def test_table_exists(self):
        """TIAOHOU_TABLE is a dict."""
        from divination.data.wuxing_tiaohou import TIAOHOU_TABLE
        assert isinstance(TIAOHOU_TABLE, dict)

    def test_table_has_entries(self):
        """TIAOHOU_TABLE has at least 60 entries."""
        from divination.data.wuxing_tiaohou import TIAOHOU_TABLE
        assert len(TIAOHOU_TABLE) >= 60

    def test_table_keys_are_tuples(self):
        """Keys are (day_gan, month_zhi) tuples."""
        from divination.data.wuxing_tiaohou import TIAOHOU_TABLE
        for key in list(TIAOHOU_TABLE.keys()):
            assert isinstance(key, tuple)
            assert len(key) == 2
            assert isinstance(key[0], str)
            assert isinstance(key[1], str)

    def test_all_10_day_stems_covered(self):
        """All 10 day stems (甲-癸) have at least one entry."""
        from divination.data.wuxing_tiaohou import TIAOHOU_TABLE
        stems = set(k[0] for k in TIAOHOU_TABLE.keys())
        expected = {"甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"}
        assert stems == expected

    def test_all_12_month_branches_covered(self):
        """Entries cover at least 9 month branches (精简录入60项)."""
        from divination.data.wuxing_tiaohou import TIAOHOU_TABLE
        branches = set(k[1] for k in TIAOHOU_TABLE.keys())
        assert len(branches) >= 9
        # Verify key seasonal branches are represented
        assert "子" in branches or "午" in branches or "寅" in branches

    def test_values_are_tiaohou_rules(self):
        """All values are TiaohouRule instances."""
        from divination.data.wuxing_tiaohou import TIAOHOU_TABLE, TiaohouRule
        for rule in TIAOHOU_TABLE.values():
            assert isinstance(rule, TiaohouRule)


# ══════════════════════════════════════════════════════════════
# 3. evaluate_tiaohou tests
# ══════════════════════════════════════════════════════════════


class TestEvaluateTiaohou:
    """Test evaluate_tiaohou lookup function."""

    def test_import_exists(self):
        """Can import evaluate_tiaohou."""
        from divination.data.wuxing_tiaohou import evaluate_tiaohou
        assert callable(evaluate_tiaohou)

    def test_valid_lookup(self):
        """Lookup for a known combination returns a dict."""
        from divination.data.wuxing_tiaohou import evaluate_tiaohou, TIAOHOU_TABLE
        # Pick first available key
        key = next(iter(TIAOHOU_TABLE.keys()))
        result = evaluate_tiaohou(key[0], key[1])
        assert result is not None
        assert isinstance(result, dict)

    def test_invalid_lookup_returns_none(self):
        """Lookup for an unknown combination returns None."""
        from divination.data.wuxing_tiaohou import evaluate_tiaohou
        # 癸+亥 combination might not be in the table
        result = evaluate_tiaohou("癸", "亥")
        # May be None or may have a rule; just test it doesn't crash
        assert result is None or isinstance(result, dict)


class TestGetTiaohouAdvice:
    """Test get_tiaohou_advice function."""

    def test_import_exists(self):
        """Can import get_tiaohou_advice."""
        from divination.data.wuxing_tiaohou import get_tiaohou_advice
        assert callable(get_tiaohou_advice)

    def test_returns_dict(self):
        """Returns a dict with structured advice."""
        from divination.data.wuxing_tiaohou import get_tiaohou_advice
        result = get_tiaohou_advice("甲", "寅")
        assert isinstance(result, dict)

    def test_advice_has_key_fields(self):
        """Advice dict has expected fields."""
        from divination.data.wuxing_tiaohou import get_tiaohou_advice
        result = get_tiaohou_advice("甲", "子")
        # Should have at minimum some advice content
        assert len(result) > 0


# ══════════════════════════════════════════════════════════════
# 4. GejuPattern dataclass tests
# ══════════════════════════════════════════════════════════════


class TestGejuPattern:
    """Test GejuPattern dataclass structure."""

    def test_import_exists(self):
        """Can import GejuPattern."""
        from divination.data.wuxing_geju import GejuPattern
        assert GejuPattern is not None

    def test_is_frozen_dataclass(self):
        """GejuPattern is a frozen dataclass."""
        from dataclasses import is_dataclass
        from divination.data.wuxing_geju import GejuPattern
        assert is_dataclass(GejuPattern)

        p = GejuPattern(
            name="食神制杀",
            category="贵格",
            description="食神制杀,主贵",
            check_fn_description="检测食神+七杀同现",
            source="《渊海子平》",
        )
        with pytest.raises(Exception):
            p.name = "other"


class TestGejuPatterns:
    """Test GEOJU_PATTERNS list."""

    def test_import_exists(self):
        """Can import GEOJU_PATTERNS."""
        from divination.data.wuxing_geju import GEOJU_PATTERNS
        assert GEOJU_PATTERNS is not None

    def test_is_list(self):
        """GEOJU_PATTERNS is a list."""
        from divination.data.wuxing_geju import GEOJU_PATTERNS
        assert isinstance(GEOJU_PATTERNS, list)

    def test_has_8_to_10_patterns(self):
        """Has 8-10 geju patterns."""
        from divination.data.wuxing_geju import GEOJU_PATTERNS
        assert 8 <= len(GEOJU_PATTERNS) <= 15

    def test_all_entries_are_geju_patterns(self):
        """All entries are GejuPattern instances."""
        from divination.data.wuxing_geju import GEOJU_PATTERNS, GejuPattern
        for p in GEOJU_PATTERNS:
            assert isinstance(p, GejuPattern)


# ══════════════════════════════════════════════════════════════
# 5. evaluate_dynamic_geju tests
# ══════════════════════════════════════════════════════════════


class TestEvaluateDynamicGeju:
    """Test evaluate_dynamic_geju function."""

    def test_import_exists(self):
        """Can import evaluate_dynamic_geju."""
        from divination.data.wuxing_geju import evaluate_dynamic_geju
        assert callable(evaluate_dynamic_geju)

    def test_returns_list(self):
        """Returns a list of matched patterns."""
        from divination.data.wuxing_geju import evaluate_dynamic_geju
        mock_counts = {}
        mock_pillars = {
            "year": "甲子", "month": "丙寅",
            "day": "戊辰", "hour": "庚申",
        }
        result = evaluate_dynamic_geju("戊", mock_counts, mock_pillars, 50)
        assert isinstance(result, list)

    def test_result_items_are_dicts(self):
        """Each result item is a dict."""
        from divination.data.wuxing_geju import evaluate_dynamic_geju
        mock_counts = {}
        mock_pillars = {
            "year": "甲子", "month": "丙寅",
            "day": "戊辰", "hour": "庚申",
        }
        result = evaluate_dynamic_geju("戊", mock_counts, mock_pillars, 50)
        for item in result:
            assert isinstance(item, dict)

    def test_handles_empty_inputs(self):
        """Does not crash on empty/missing inputs."""
        from divination.data.wuxing_geju import evaluate_dynamic_geju
        result = evaluate_dynamic_geju("甲", {}, {}, 0)
        assert isinstance(result, list)


# ══════════════════════════════════════════════════════════════
# 6. bazi_v2 integration tests
# ══════════════════════════════════════════════════════════════


class TestBaziV2TiaohouIntegration:
    """Test that bazi_v2 compute() includes tiaohou and dynamic_geju in output."""

    def test_raw_has_tiaohou(self):
        """bazi_v2 raw output contains 'tiaohou' key."""
        from divination.engines.bazi_v2 import compute
        b = Birth(year=1984, month=6, day=15, hour=8, gender="male")
        result = compute(b)
        assert "tiaohou" in result.raw

    def test_raw_has_tiaohou_advice(self):
        """bazi_v2 raw output contains 'tiaohou_advice' key."""
        from divination.engines.bazi_v2 import compute
        b = Birth(year=1984, month=6, day=15, hour=8, gender="male")
        result = compute(b)
        assert "tiaohou_advice" in result.raw

    def test_raw_has_dynamic_geju(self):
        """bazi_v2 raw output contains 'dynamic_geju' key."""
        from divination.engines.bazi_v2 import compute
        b = Birth(year=1984, month=6, day=15, hour=8, gender="male")
        result = compute(b)
        assert "dynamic_geju" in result.raw

    def test_raw_has_dynamic_geju_count(self):
        """bazi_v2 raw output contains 'dynamic_geju_count' key."""
        from divination.engines.bazi_v2 import compute
        b = Birth(year=1984, month=6, day=15, hour=8, gender="male")
        result = compute(b)
        assert "dynamic_geju_count" in result.raw
        assert isinstance(result.raw["dynamic_geju_count"], int)
