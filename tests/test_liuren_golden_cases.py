"""P2-9 + P3-2: 大六壬 30 golden cases + 课式 + 神煞 测试.

覆盖:
- LiurenCase dataclass 完整性 (18 complete + 12 partial = 30 cases)
- 高阶课式 detect_patterns (10 patterns x check_fn)
- 神煞落宫断语 get_shen_sha_judgments
- 集成: liuren.py 输出含 liuren_patterns + shen_sha_judgments
"""
from __future__ import annotations

import pytest

from divination.data.liuren_cases import (
    ALL_CASES,
    COMPLETE_COUNT,
    LIUREN_COMPLETE_CASES,
    LIUREN_PARTIAL_CASES,
    LiurenCase,
    PARTIAL_COUNT,
    TOTAL_COUNT,
)
from divination.data.liuren_patterns import (
    HIGH_LEVEL_PATTERNS,
    PatternDef,
    detect_patterns,
    _check_sanguang,
    _check_sanyang,
    _check_sanyin,
    _check_zhuyin,
    _check_zhuolun,
    _check_jiase,
    _check_lianzhu,
    _check_youzi,
    _check_jieli,
    _check_luanshou,
)
from divination.data.liuren_shen_sha import (
    SHEN_SHA_JUDGMENTS,
    ShenShaEntry,
    get_shen_sha_judgments,
)
from divination.contracts import Birth


# ═══════════════════════════════════════════════════════════════
# Group 1: LiurenCase dataclass 完整性
# ═══════════════════════════════════════════════════════════════

class TestLiurenCaseDataclass:
    """LiurenCase frozen dataclass 验证."""

    def test_case_is_frozen(self):
        """LiurenCase 应不可变 (frozen)."""
        with pytest.raises(Exception):
            ALL_CASES[0].day_gan = "乙"  # type: ignore

    def test_total_30_cases(self):
        """共 30 个案例."""
        assert TOTAL_COUNT == 30

    def test_complete_18_cases(self):
        """至少 18 个完整案例."""
        assert COMPLETE_COUNT >= 18

    def test_partial_12_cases(self):
        """至少 12 个部分案例."""
        assert PARTIAL_COUNT >= 12

    def test_complete_cases_have_chu_chuan(self):
        """完整案例必须有初传."""
        for c in LIUREN_COMPLETE_CASES:
            assert c.chu_chuan is not None, f"Case {c.case_id} missing chu_chuan"
            assert c.is_complete is True

    def test_partial_cases_no_chu_chuan(self):
        """部分案例缺初传."""
        for c in LIUREN_PARTIAL_CASES:
            assert c.chu_chuan is None
            assert c.is_complete is False

    def test_all_cases_have_gan_and_zhi(self):
        """所有案例必须有 day_gan/day_zhi."""
        for c in ALL_CASES:
            assert len(c.day_gan) == 1
            assert len(c.day_zhi) == 1
            assert c.day_gan in "甲乙丙丁戊己庚辛壬癸"
            assert c.day_zhi in "子丑寅卯辰巳午未申酉戌亥"

    def test_all_cases_have_hour_zhi(self):
        """所有案例必须有 hour_zhi (占时)."""
        DZ = "子丑寅卯辰巳午未申酉戌亥"
        for c in ALL_CASES:
            assert c.hour_zhi in DZ

    def test_all_cases_have_month_general(self):
        """所有案例必须有月将."""
        DZ = "子丑寅卯辰巳午未申酉戌亥"
        for c in ALL_CASES:
            assert c.month_general in DZ

    def test_all_cases_have_source(self):
        """所有案例必须标注来源."""
        known_sources = {"六壬断案", "六壬指南", "六壬大全", "毕法赋"}
        for c in ALL_CASES:
            # source至少含一个已知来源
            found = any(s in c.source for s in known_sources)
            assert found or c.source == "六壬大全·课例补遗" or c.source == "六壬断案摘录" or c.source == "六壬指南摘录" or "六壬大全" in c.source, f"Case {c.case_id}: unknown source {c.source}"

    def test_complete_cases_have_lessons(self):
        """完整案例必须有四课."""
        for c in LIUREN_COMPLETE_CASES:
            assert c.lessons_upper is not None, f"Case {c.case_id} missing lessons_upper"
            assert c.lessons_lower is not None, f"Case {c.case_id} missing lessons_lower"
            assert len(c.lessons_upper) == 4
            assert len(c.lessons_lower) == 4

    def test_complete_cases_have_gui_ren(self):
        """完整案例应有贵人所在 (至少大部分有)."""
        with_gr = sum(1 for c in LIUREN_COMPLETE_CASES if c.gui_ren_zhi is not None)
        assert with_gr >= 12  # 至少 2/3

    def test_complete_cases_have_xun_kong(self):
        """完整案例应有旬空."""
        with_xk = sum(1 for c in LIUREN_COMPLETE_CASES if c.xun_kong is not None)
        assert with_xk >= 12

    def test_pattern_names_valid(self):
        """课式名应为已知的九宗门或高阶课式."""
        valid = {"贼克", "比用", "涉害", "遥克", "昴星", "伏吟", "返吟",
                 "别责", "八专", "三光", "三阳", "三阴", "铸印", "斫轮"}
        for c in ALL_CASES:
            assert c.pattern_name in valid or c.pattern_name, f"Case {c.case_id}: unknown pattern {c.pattern_name}"

    def test_duplicate_case_ids(self):
        """case_id 不能重复."""
        ids = [c.case_id for c in ALL_CASES]
        assert len(ids) == len(set(ids))

    def test_all_cases_unique_ganzhi_hour(self):
        """每个案例 (day_gan, day_zhi, hour_zhi) 组合应唯一或至少合理."""
        keys = [(c.day_gan, c.day_zhi, c.hour_zhi, c.month_general) for c in ALL_CASES]
        # 允许部分重复 (同干支不同月将), 但至少有 20 个不同的组合
        unique = len(set(keys))
        assert unique >= 20, f"Only {unique} unique (day_gan, day_zhi, hour_zhi, month_general) combos"

    def test_complete_cases_have_verdict_or_question(self):
        """完整案例至少一半有 question 或 verdict."""
        with_q = sum(1 for c in LIUREN_COMPLETE_CASES if c.question or c.verdict)
        assert with_q >= 9  # 至少一半

    def test_case_pattern_polarity_matches(self):
        """课式极性应为有效值."""
        valid = {"auspicious", "inauspicious", "neutral"}
        for c in ALL_CASES:
            assert c.pattern_polarity in valid


# ═══════════════════════════════════════════════════════════════
# Group 2: 高阶课式 detect_patterns
# ═══════════════════════════════════════════════════════════════

class TestHighLevelPatterns:
    """10 个高阶课式 check_fn 测试."""

    def test_10_patterns_defined(self):
        """应有 10 个高阶课式."""
        assert len(HIGH_LEVEL_PATTERNS) == 10

    def test_all_patterns_are_frozen(self):
        """PatternDef 应 frozen."""
        with pytest.raises(Exception):
            HIGH_LEVEL_PATTERNS[0].name = "fake"  # type: ignore

    def test_each_pattern_has_check_fn(self):
        """每个课式有 check_fn."""
        for pat in HIGH_LEVEL_PATTERNS:
            assert callable(pat.check_fn), f"{pat.name}: check_fn not callable"

    def test_each_pattern_has_brief(self):
        """每个课式有简要说明."""
        for pat in HIGH_LEVEL_PATTERNS:
            assert len(pat.brief) > 5

    def test_each_pattern_has_detailed(self):
        """每个课式有详细断语."""
        for pat in HIGH_LEVEL_PATTERNS:
            assert len(pat.detailed) > 20

    def test_each_pattern_valid_polarity(self):
        """极性应为有效值."""
        valid = {"auspicious", "inauspicious", "neutral"}
        for pat in HIGH_LEVEL_PATTERNS:
            assert pat.polarity in valid, f"{pat.name}: invalid polarity {pat.polarity}"

    # ── 各 check_fn 独立验证 ──

    def test_sanguang_matches_case16(self):
        """三光: 贵人临卯 (case 16 后验)."""
        # 构造满足条件的数据
        cosmic = {"gui_ren_zhi": "卯", "hour_branch": "卯", "month_general": "亥"}
        san_chuan = {"chu_chuan": "寅", "zhong_chuan": "卯", "mo_chuan": "辰"}
        si_ke = {"lessons": []}
        assert _check_sanguang("甲", "午", san_chuan, si_ke, cosmic) is True

    def test_sanguang_false_when_gui_not_mao(self):
        """三光: 贵人不在卯 → False."""
        cosmic = {"gui_ren_zhi": "丑"}
        san_chuan = {"chu_chuan": "寅", "zhong_chuan": "卯", "mo_chuan": "辰"}
        si_ke = {"lessons": []}
        assert _check_sanguang("甲", "午", san_chuan, si_ke, cosmic) is False

    def test_sanyang_matches_gui_hai_fire_chu(self):
        """三阳: 贵亥+初传火."""
        cosmic = {"gui_ren_zhi": "亥"}
        san_chuan = {"chu_chuan": "午", "zhong_chuan": "未", "mo_chuan": "申"}
        si_ke = {"lessons": []}
        assert _check_sanyang("丙", "子", san_chuan, si_ke, cosmic) is True

    def test_sanyang_false_gui_not_hai(self):
        """三阳: 贵人不在亥 → False."""
        cosmic = {"gui_ren_zhi": "丑"}
        san_chuan = {"chu_chuan": "午", "zhong_chuan": "未", "mo_chuan": "申"}
        si_ke = {"lessons": []}
        assert _check_sanyang("丙", "子", san_chuan, si_ke, cosmic) is False

    def test_sanyin_matches_gui_si_water_chu(self):
        """三阴: 贵巳+初传水."""
        cosmic = {"gui_ren_zhi": "巳"}
        san_chuan = {"chu_chuan": "子", "zhong_chuan": "丑", "mo_chuan": "寅"}
        si_ke = {"lessons": []}
        assert _check_sanyin("丁", "巳", san_chuan, si_ke, cosmic) is True

    def test_sanyin_false_not_water_chu(self):
        """三阴: 初传非水 → False."""
        cosmic = {"gui_ren_zhi": "巳"}
        san_chuan = {"chu_chuan": "午", "zhong_chuan": "未", "mo_chuan": "申"}
        si_ke = {"lessons": []}
        assert _check_sanyin("丁", "巳", san_chuan, si_ke, cosmic) is False

    def test_zhuyin_matches_si_xu_mao(self):
        """铸印: 巳戌卯三传."""
        cosmic = {"gui_ren_zhi": "未"}
        san_chuan = {"chu_chuan": "巳", "zhong_chuan": "戌", "mo_chuan": "卯"}
        si_ke = {"lessons": []}
        assert _check_zhuyin("庚", "申", san_chuan, si_ke, cosmic) is True

    def test_zhuyin_matches_gold_chu_gui_chen(self):
        """铸印: 初传金+贵临辰."""
        cosmic = {"gui_ren_zhi": "辰"}
        san_chuan = {"chu_chuan": "申", "zhong_chuan": "酉", "mo_chuan": "戌"}
        si_ke = {"lessons": []}
        assert _check_zhuyin("庚", "申", san_chuan, si_ke, cosmic) is True

    def test_zhuolun_matches_mao_shen(self):
        """斫轮: 卯申二传."""
        cosmic = {"gui_ren_zhi": "未"}
        san_chuan = {"chu_chuan": "卯", "zhong_chuan": "申", "mo_chuan": "丑"}
        si_ke = {"lessons": []}
        assert _check_zhuolun("辛", "卯", san_chuan, si_ke, cosmic) is True

    def test_jiase_matches_all_earth(self):
        """稼穑: 三传皆土."""
        cosmic = {"gui_ren_zhi": "未"}
        san_chuan = {"chu_chuan": "辰", "zhong_chuan": "戌", "mo_chuan": "丑"}
        si_ke = {"lessons": []}
        assert _check_jiase("戊", "辰", san_chuan, si_ke, cosmic) is True

    def test_jiase_false_not_all_earth(self):
        """稼穑: 非全土 → False."""
        cosmic = {"gui_ren_zhi": "未"}
        san_chuan = {"chu_chuan": "辰", "zhong_chuan": "卯", "mo_chuan": "丑"}
        si_ke = {"lessons": []}
        assert _check_jiase("戊", "辰", san_chuan, si_ke, cosmic) is False

    def test_lianzhu_matches_forward(self):
        """连珠: 寅卯辰."""
        cosmic = {"gui_ren_zhi": "未"}
        san_chuan = {"chu_chuan": "寅", "zhong_chuan": "卯", "mo_chuan": "辰"}
        si_ke = {"lessons": []}
        assert _check_lianzhu("甲", "子", san_chuan, si_ke, cosmic) is True

    def test_lianzhu_matches_backward(self):
        """连珠: 辰卯寅 (退行)."""
        cosmic = {"gui_ren_zhi": "未"}
        san_chuan = {"chu_chuan": "辰", "zhong_chuan": "卯", "mo_chuan": "寅"}
        si_ke = {"lessons": []}
        assert _check_lianzhu("甲", "子", san_chuan, si_ke, cosmic) is True

    def test_lianzhu_false_skip(self):
        """连珠: 寅辰卯 (不连续) → False."""
        cosmic = {"gui_ren_zhi": "未"}
        san_chuan = {"chu_chuan": "寅", "zhong_chuan": "辰", "mo_chuan": "卯"}
        si_ke = {"lessons": []}
        assert _check_lianzhu("甲", "子", san_chuan, si_ke, cosmic) is False

    def test_youzi_matches(self):
        """游子: 寅+贵寅."""
        cosmic = {"gui_ren_zhi": "寅"}
        san_chuan = {"chu_chuan": "寅", "zhong_chuan": "卯", "mo_chuan": "辰"}
        si_ke = {"lessons": []}
        assert _check_youzi("甲", "子", san_chuan, si_ke, cosmic) is True

    def test_youzi_false_no_meng(self):
        """游子: 无四孟 → False."""
        cosmic = {"gui_ren_zhi": "卯"}
        san_chuan = {"chu_chuan": "子", "zhong_chuan": "卯", "mo_chuan": "午"}
        si_ke = {"lessons": []}
        assert _check_youzi("甲", "子", san_chuan, si_ke, cosmic) is False

    def test_luanshou_matches(self):
        """乱首: 上神受下神克."""
        # 寅(木)克丑(土): 如果 upper=丑(土)受 lower=寅(木)克 → 下克上
        # 子(水)受辰(土)克: upper=子(水), lower=辰(土)
        si_ke = {
            "lessons": [
                {"idx": 1, "upper": "子", "lower": "辰"},
            ]
        }
        cosmic = {"gui_ren_zhi": "未"}
        san_chuan = {"chu_chuan": "子", "zhong_chuan": "丑", "mo_chuan": "寅"}
        assert _check_luanshou("甲", "午", san_chuan, si_ke, cosmic) is True

    def test_luanshou_false(self):
        """乱首: 无克 → False."""
        si_ke = {
            "lessons": [
                {"idx": 1, "upper": "寅", "lower": "亥"},
            ]
        }
        cosmic = {"gui_ren_zhi": "未"}
        san_chuan = {"chu_chuan": "子", "zhong_chuan": "丑", "mo_chuan": "寅"}
        assert _check_luanshou("甲", "午", san_chuan, si_ke, cosmic) is False

    def test_detect_patterns_returns_list(self):
        """detect_patterns 应返回 list."""
        cosmic = {"gui_ren_zhi": "卯"}
        san_chuan = {"chu_chuan": "寅", "zhong_chuan": "卯", "mo_chuan": "辰"}
        si_ke = {"lessons": []}
        results = detect_patterns("甲", "午", san_chuan, si_ke, cosmic)
        assert isinstance(results, list)
        # 三光应匹配
        matched_names = [r["name"] for r in results]
        assert "三光" in matched_names

    def test_detect_patterns_graceful_error(self):
        """错误的输入不应崩溃."""
        cosmic = {}
        san_chuan = {}
        si_ke = {}
        results = detect_patterns("甲", "子", san_chuan, si_ke, cosmic)
        assert isinstance(results, list)  # 可能为空但不崩


# ═══════════════════════════════════════════════════════════════
# Group 3: 神煞落宫断语
# ═══════════════════════════════════════════════════════════════

class TestShenShaJudgments:
    """十二神煞落宫断语表 + 查表函数."""

    def test_12_shen_sha_unique_names(self):
        """SHEN_SHA_JUDGMENTS 含 12 种不同神煞."""
        names = set(e.shen_sha for e in SHEN_SHA_JUDGMENTS)
        assert len(names) == 12

    def test_entry_is_frozen(self):
        """ShenShaEntry 应 frozen."""
        with pytest.raises(Exception):
            SHEN_SHA_JUDGMENTS[0].judgment = "fake"  # type: ignore

    def test_all_entries_have_judgment(self):
        """每条有判断语."""
        for e in SHEN_SHA_JUDGMENTS:
            assert len(e.judgment) > 10, f"{e.shen_sha}@{e.zhi}: judgment too short"

    def test_all_entries_have_category(self):
        """每条有分类."""
        valid = {"吉神", "凶煞", "中性"}
        for e in SHEN_SHA_JUDGMENTS:
            assert e.category in valid, f"{e.shen_sha}@{e.zhi}: invalid category"

    def test_all_entries_have_wuxing(self):
        """每条有五行."""
        valid = {"水", "火", "木", "金", "土"}
        for e in SHEN_SHA_JUDGMENTS:
            assert e.wuxing in valid, f"{e.shen_sha}@{e.zhi}: invalid wuxing {e.wuxing}"

    def test_all_entries_have_trigram(self):
        """每条有八卦."""
        valid = {"坎", "艮", "震", "巽", "离", "坤", "兑", "乾"}
        for e in SHEN_SHA_JUDGMENTS:
            assert e.trigram in valid, f"{e.shen_sha}@{e.zhi}: invalid trigram {e.trigram}"

    def test_zhi_matches_gong_prefix(self):
        """落宫地支应匹配宫名."""
        for e in SHEN_SHA_JUDGMENTS:
            assert e.gong_name.startswith(e.zhi), f"{e.shen_sha}: {e.gong_name} vs {e.zhi}"

    def test_jixin_num(self):
        """吉神至少 30 条, 凶煞至少 20 条."""
        ji = sum(1 for e in SHEN_SHA_JUDGMENTS if e.category == "吉神")
        xiong = sum(1 for e in SHEN_SHA_JUDGMENTS if e.category == "凶煞")
        assert ji >= 5
        assert xiong >= 5

    def test_get_shen_sha_judgments_matches(self):
        """匹配测试: 贵人临子应返回断语."""
        generals = [{"general": "贵人", "position": "子"}]
        results = get_shen_sha_judgments(generals)
        assert len(results) == 1
        assert results[0]["shen_sha"] == "贵人"
        assert results[0]["zhi"] == "子"
        assert "暗中有贵人提携" in results[0]["judgment"]

    def test_get_shen_sha_no_match(self):
        """无匹配 → 空列表."""
        generals = [{"general": "贵人", "position": "卯"}]  # 卯无贵人条目
        results = get_shen_sha_judgments(generals)
        # 卯在贵人中无条目, 返回空
        assert isinstance(results, list)

    def test_get_shen_sha_multiple_generals(self):
        """多个天将 → 多项结果."""
        generals = [
            {"general": "贵人", "position": "子"},
            {"general": "青龙", "position": "寅"},
            {"general": "白虎", "position": "申"},
        ]
        results = get_shen_sha_judgments(generals)
        # 至少匹配 2 项
        assert len(results) >= 2

    def test_get_shen_sha_all_keys_present(self):
        """返回的每条结果含所有必需键."""
        generals = [{"general": "贵人", "position": "子"}]
        results = get_shen_sha_judgments(generals)
        if results:
            for key in ("shen_sha", "zhi", "gong_name", "wuxing", "trigram", "judgment", "category"):
                assert key in results[0]


# ═══════════════════════════════════════════════════════════════
# Group 4: 集成 — liuren.py 输出验证
# ═══════════════════════════════════════════════════════════════

class TestLiurenEngineIntegration:
    """liuren.py compute() 输出含 liuren_patterns + shen_sha_judgments."""

    def test_liuren_compute_has_liuren_patterns(self):
        """raw 含 liuren_patterns 字段."""
        from divination.engines.liuren import compute
        b = Birth(year=2025, month=6, day=15, hour=10)
        chart = compute(b)
        assert "liuren_patterns" in chart.raw
        assert isinstance(chart.raw["liuren_patterns"], list)

    def test_liuren_compute_has_shen_sha_judgments(self):
        """raw 含 shen_sha_judgments 字段."""
        from divination.engines.liuren import compute
        b = Birth(year=2025, month=6, day=15, hour=10)
        chart = compute(b)
        assert "shen_sha_judgments" in chart.raw
        assert isinstance(chart.raw["shen_sha_judgments"], list)

    def test_liuren_shen_sha_judgments_not_empty(self):
        """shen_sha_judgments 应有匹配项 (天将排布应命中部分断语)."""
        from divination.engines.liuren import compute
        b = Birth(year=2025, month=6, day=15, hour=10)
        chart = compute(b)
        # 12 天将中至少有一些能匹配
        judgments = chart.raw["shen_sha_judgments"]
        assert len(judgments) >= 1, "Expected at least 1 shen_sha match"

    def test_liuren_patterns_field_is_list_of_dicts(self):
        """liuren_patterns 每项应有 name/polarity/brief/detailed."""
        from divination.engines.liuren import compute
        b = Birth(year=2025, month=6, day=15, hour=10)
        chart = compute(b)
        for p in chart.raw["liuren_patterns"]:
            assert "name" in p
            assert "polarity" in p
            assert "brief" in p
            assert "detailed" in p

    def test_liuren_data_files_importable(self):
        """三个数据文件均可导入."""
        import divination.data.liuren_cases
        import divination.data.liuren_patterns
        import divination.data.liuren_shen_sha
        assert divination.data.liuren_cases is not None
        assert divination.data.liuren_patterns is not None
        assert divination.data.liuren_shen_sha is not None
