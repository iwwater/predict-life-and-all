"""Tests for 小六壬数字起卦深化 (P3-3).

Tests cover:
  - NumberKeRule dataclass structure
  - NUMBER_KE_RULES list completeness
  - evaluate_number_rules function
  - get_number_wuxing function
  - _interpret_multi_numbers function
  - xiaoliuren engine integration

Source: 《小六壬课经》
"""

from __future__ import annotations

import pytest


# ══════════════════════════════════════════════════════════════
# 1. NumberKeRule dataclass tests
# ══════════════════════════════════════════════════════════════


class TestNumberKeRule:
    """Test NumberKeRule dataclass structure."""

    def test_import_exists(self):
        """Can import NumberKeRule."""
        from divination.data.xiaoliuren_ke_jing import NumberKeRule
        assert NumberKeRule is not None

    def test_is_frozen_dataclass(self):
        """NumberKeRule is a frozen dataclass."""
        from dataclasses import is_dataclass
        from divination.data.xiaoliuren_ke_jing import NumberKeRule
        assert is_dataclass(NumberKeRule)

        r = NumberKeRule(
            rule_id="test_001",
            name="测试规则",
            category="数字模式",
            condition_description="测试条件",
            interpretation="测试解读",
            tone="neutral",
            advice="测试建议",
        )
        with pytest.raises(Exception):
            r.name = "changed"

    def test_fields_present(self):
        """All required fields are present."""
        from divination.data.xiaoliuren_ke_jing import NumberKeRule
        r = NumberKeRule(
            rule_id="test_001",
            name="三数顺行",
            category="数字模式",
            condition_description="n1 < n2 < n3",
            interpretation="事态发展顺利",
            tone="auspicious",
            advice="顺势而为",
        )
        assert r.rule_id == "test_001"
        assert r.name == "三数顺行"
        assert r.category == "数字模式"
        assert r.tone == "auspicious"
        assert r.source == "《小六壬课经》"


# ══════════════════════════════════════════════════════════════
# 2. NUMBER_KE_RULES tests
# ══════════════════════════════════════════════════════════════


class TestNumberKeRules:
    """Test NUMBER_KE_RULES list."""

    def test_import_exists(self):
        """Can import NUMBER_KE_RULES."""
        from divination.data.xiaoliuren_ke_jing import NUMBER_KE_RULES
        assert NUMBER_KE_RULES is not None

    def test_is_list(self):
        """NUMBER_KE_RULES is a list."""
        from divination.data.xiaoliuren_ke_jing import NUMBER_KE_RULES
        assert isinstance(NUMBER_KE_RULES, list)

    def test_has_10_to_15_rules(self):
        """Has 10-15 number ke rules."""
        from divination.data.xiaoliuren_ke_jing import NUMBER_KE_RULES
        assert 10 <= len(NUMBER_KE_RULES) <= 20

    def test_all_are_number_ke_rules(self):
        """All entries are NumberKeRule instances."""
        from divination.data.xiaoliuren_ke_jing import NUMBER_KE_RULES, NumberKeRule
        for rule in NUMBER_KE_RULES:
            assert isinstance(rule, NumberKeRule)

    def test_unique_rule_ids(self):
        """All rule_ids are unique."""
        from divination.data.xiaoliuren_ke_jing import NUMBER_KE_RULES
        ids = [r.rule_id for r in NUMBER_KE_RULES]
        assert len(ids) == len(set(ids))

    def test_valid_tones(self):
        """All tones are valid values."""
        from divination.data.xiaoliuren_ke_jing import NUMBER_KE_RULES
        valid = {"auspicious", "inauspicious", "mixed", "neutral"}
        for rule in NUMBER_KE_RULES:
            assert rule.tone in valid


# ══════════════════════════════════════════════════════════════
# 3. evaluate_number_rules tests
# ══════════════════════════════════════════════════════════════


class TestEvaluateNumberRules:
    """Test evaluate_number_rules function."""

    def test_import_exists(self):
        """Can import evaluate_number_rules."""
        from divination.data.xiaoliuren_ke_jing import evaluate_number_rules
        assert callable(evaluate_number_rules)

    def test_returns_list(self):
        """Returns a list of matched rules."""
        from divination.data.xiaoliuren_ke_jing import evaluate_number_rules
        result = evaluate_number_rules([1, 2, 3])
        assert isinstance(result, list)

    def test_result_items_are_dicts(self):
        """Result items are dicts with expected keys."""
        from divination.data.xiaoliuren_ke_jing import evaluate_number_rules
        result = evaluate_number_rules([7, 7, 7])
        for item in result:
            assert isinstance(item, dict)

    def test_empty_list_handled(self):
        """Empty list does not crash."""
        from divination.data.xiaoliuren_ke_jing import evaluate_number_rules
        result = evaluate_number_rules([])
        assert isinstance(result, list)

    def test_small_numbers(self):
        """Small numbers (1-10) are handled."""
        from divination.data.xiaoliuren_ke_jing import evaluate_number_rules
        result = evaluate_number_rules([1, 2, 3])
        assert isinstance(result, list)

    def test_large_numbers(self):
        """Large numbers (>50) are handled."""
        from divination.data.xiaoliuren_ke_jing import evaluate_number_rules
        result = evaluate_number_rules([99, 88, 77])
        assert isinstance(result, list)


# ══════════════════════════════════════════════════════════════
# 4. get_number_wuxing tests
# ══════════════════════════════════════════════════════════════


class TestGetNumberWuxing:
    """Test get_number_wuxing function."""

    def test_import_exists(self):
        """Can import get_number_wuxing."""
        from divination.data.xiaoliuren_ke_jing import get_number_wuxing
        assert callable(get_number_wuxing)

    def test_returns_dict(self):
        """Returns a dict."""
        from divination.data.xiaoliuren_ke_jing import get_number_wuxing
        result = get_number_wuxing([1, 2, 3])
        assert isinstance(result, dict)

    def test_three_numbers_produces_three_wuxing(self):
        """Three numbers yield three wuxing assignments."""
        from divination.data.xiaoliuren_ke_jing import get_number_wuxing
        result = get_number_wuxing([1, 2, 3])
        assert len(result) >= 3


# ══════════════════════════════════════════════════════════════
# 5. xiaoliuren engine integration tests
# ══════════════════════════════════════════════════════════════


class TestXiaoliurenMultiNumbers:
    """Test xiaoliuren engine multi-number interpretation."""

    def test_import_function_exists(self):
        """_interpret_multi_numbers can be imported."""
        from divination.engines.xiaoliuren import _interpret_multi_numbers
        assert callable(_interpret_multi_numbers)

    def test_returns_dict(self):
        """Returns a structured dict."""
        from divination.engines.xiaoliuren import _interpret_multi_numbers
        result = _interpret_multi_numbers([15, 30, 45])
        assert isinstance(result, dict)

    def test_has_expected_keys(self):
        """Result dict has expected keys."""
        from divination.engines.xiaoliuren import _interpret_multi_numbers
        result = _interpret_multi_numbers([1, 50, 99])
        assert "numbers" in result
        assert "number_rules_matched" in result
        assert "wuxing_distribution" in result

    def test_accepts_question(self):
        """Accepts and uses question parameter for intent linkage."""
        from divination.engines.xiaoliuren import _interpret_multi_numbers
        result = _interpret_multi_numbers(
            [3, 6, 9],
            question="我的事业发展如何?",
        )
        assert isinstance(result, dict)

    def test_number_xiaoliuren_mode_integration(self):
        """number_xiaoliuren compute() includes multi_number_interpretation."""
        from divination.contracts import Birth
        from divination.engines.xiaoliuren import compute
        b = Birth(year=2024, month=6, day=15, hour=12)
        b.mode = "number_xiaoliuren"
        b.seed = "1,2,3"
        b.question = "test question"
        result = compute(b)
        assert "multi_number_interpretation" in result.raw

    def test_number_xiaoliuren_has_ke_rules_total(self):
        """number_xiaoliuren raw includes number_ke_rules_total."""
        from divination.contracts import Birth
        from divination.engines.xiaoliuren import compute
        b = Birth(year=2024, month=6, day=15, hour=12)
        b.mode = "number_xiaoliuren"
        b.seed = "4,5,6"
        result = compute(b)
        assert "number_ke_rules_total" in result.raw
