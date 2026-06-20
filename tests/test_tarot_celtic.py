"""塔罗 · 凯尔特十字 (Celtic Cross) 深度解读测试。

覆盖:
- 凯尔特十字牌阵位置含义表 (10 个位置)
- 位置关系矩阵 (8 对关键关系)
- 宫廷牌 16 种人格画像
- 元素分布 (水/火/风/土)
- 综合解读 (中心十字 + 权杖柱 + 最终结果)
- evidence_sources 引用
- compute() 端到端输出
"""
from __future__ import annotations

import pytest

from divination.contracts import Birth
from divination.engines.tarot import (
    SPREADS,
    _COURT,
    _COURT_PROFILES,
    _build_deck,
    _build_position_meanings,
    _compose_celtic_narrative,
    _compute_relationships,
    _court_profile,
    _element_distribution,
    get_celtic_position_meanings,
    get_celtic_relationships,
    get_court_profiles,
    compute,
)


# ── 1. 凯尔特十字牌阵基础 ─────────────────────────────────
class TestCelticSpread:
    def test_celtic_spread_exists(self):
        assert "celtic" in SPREADS
        spread = SPREADS["celtic"]
        assert spread["名称"] == "凯尔特十字"
        assert len(spread["positions"]) == 10

    def test_celtic_10_positions(self):
        """10 个位置: 现状、阻碍、潜意识根源、近过去、可能未来、近期发展、自我态度、外在环境、希望与恐惧、最终结果。"""
        spread = SPREADS["celtic"]
        expected = ["现状", "阻碍", "潜意识根源", "近过去", "可能未来",
                    "近期发展", "自我态度", "外在环境", "希望与恐惧", "最终结果"]
        assert spread["positions"] == expected

    def test_celtic_has_guide_and_fit(self):
        spread = SPREADS["celtic"]
        assert spread["fit"]
        assert spread["guide"]
        # guide 应提及中心十字与权杖柱
        assert "中心十字" in spread["guide"]
        assert "权杖柱" in spread["guide"]


# ── 2. 位置含义表 (10 个) ─────────────────────────────────
class TestPositionMeanings:
    def test_celtic_position_meanings_public(self):
        meanings = get_celtic_position_meanings()
        assert len(meanings) == 10

    def test_each_position_has_required_fields(self):
        meanings = get_celtic_position_meanings()
        for pos in ["现状", "阻碍", "潜意识根源", "近过去", "可能未来",
                    "近期发展", "自我态度", "外在环境", "希望与恐惧", "最终结果"]:
            assert pos in meanings, f"缺失位置 {pos}"
            m = meanings[pos]
            for field in ["核心提问", "读法", "落点"]:
                assert field in m, f"{pos} 缺 {field}"
                assert len(m[field]) > 5, f"{pos}.{field} 过短"

    def test_final_result_position_special(self):
        """第10张「最终结果」位置含义必须强调综合判读。"""
        meanings = get_celtic_position_meanings()
        final = meanings["最终结果"]
        assert "综合" in final["读法"] or "综合" in final["落点"]


# ── 3. 位置关系矩阵 (8 对) ─────────────────────────────────
class TestPositionRelationships:
    def test_relationships_public_count(self):
        rels = get_celtic_relationships()
        assert len(rels) == 8

    def test_relationship_required_fields(self):
        rels = get_celtic_relationships()
        for r in rels:
            assert "pair" in r and len(r["pair"]) == 2
            assert "relation" in r
            assert "meaning" in r
            assert "权重" in r
            assert r["权重"] in {"高", "中", "低"}

    def test_key_relationship_pairs(self):
        """必须有 (现状, 阻碍) 横轴张力 与 (潜意识根源, 可能未来) 纵轴轨迹。"""
        rels = get_celtic_relationships()
        pair_set = {tuple(r["pair"]) for r in rels}
        # 注意: pair 是 (a, b) 但顺序不重要, 检查子集
        pair_normalized = {tuple(sorted(p)) for p in pair_set}
        assert tuple(sorted(("现状", "阻碍"))) in pair_normalized
        assert tuple(sorted(("潜意识根源", "可能未来"))) in pair_normalized
        assert tuple(sorted(("可能未来", "希望与恐惧"))) in pair_normalized
        assert tuple(sorted(("可能未来", "最终结果"))) in pair_normalized

    def test_relationship_computation(self):
        """_compute_relationships 必须返回与 drawn 对应的卡片信息。"""
        from divination.engines.tarot import _build_deck
        deck = _build_deck()
        # 模拟 10 张牌 (选前 10)
        drawn = []
        positions = SPREADS["celtic"]["positions"]
        for i, pos in enumerate(positions):
            card = dict(deck[i])
            card["位置"] = pos
            card["方位"] = "正位"
            card["牌义"] = card["正位"]
            drawn.append(card)
        rels = _compute_relationships("celtic", drawn)
        assert len(rels) == 8
        for r in rels:
            assert "cards" in r
            assert "position_indices" in r
            assert "is_major_arcana_pair" in r
            assert "same_element" in r
            assert "tension_signal" in r


# ── 4. 宫廷牌 16 种画像 ─────────────────────────────────
class TestCourtProfiles:
    def test_court_profiles_public_16(self):
        profiles = get_court_profiles()
        assert len(profiles) == 16

    def test_court_profiles_required_keys(self):
        """16 张 = 4 阶 × 4 花色。"""
        profiles = get_court_profiles()
        expected = []
        for suit in ["权杖", "圣杯", "宝剑", "钱币"]:
            for court in ["侍从", "骑士", "王后", "国王"]:
                expected.append(f"{suit}{court}")
        for k in expected:
            assert k in profiles, f"缺 {k}"
            assert len(profiles[k]) > 10

    def test_court_constant_set(self):
        assert _COURT == {"侍从", "骑士", "王后", "国王"}

    def test_court_profile_extraction(self):
        """模拟一张圣杯王后的提取。"""
        from divination.engines.tarot import _build_deck
        deck = _build_deck()
        # 找到 圣杯王后
        queen = next(c for c in deck if c["牌"] == "圣杯王后")
        assert queen["阶"] == "王后"
        # profile 应有画像
        assert queen["牌"] in _COURT_PROFILES


# ── 5. 元素分布 ──────────────────────────────────────
class TestElementDistribution:
    def test_element_distribution_keys(self):
        from divination.engines.tarot import _build_deck
        deck = _build_deck()
        drawn = []
        positions = ["现状", "阻碍", "潜意识根源", "近过去", "可能未来"]
        for i, pos in enumerate(positions):
            card = dict(deck[i])
            card["位置"] = pos
            card["方位"] = "正位"
            card["牌义"] = card["正位"]
            drawn.append(card)
        info = _element_distribution(drawn)
        assert "元素计数" in info
        assert "花色计数" in info
        assert "主导元素" in info
        # 5 张小牌 (假设前 5 都是小牌, 因为大阿卡纳排前 22 张)
        # 实际 deck 中索引 0-21 是大阿卡纳, 22+ 是小牌
        # 因此 _element_distribution(drawn with deck[0..4]) 都是大阿卡纳 → 元素为空
        # 但函数应不崩溃
        for e in ["火", "土", "风", "水"]:
            assert e in info["元素计数"]

    def test_element_distribution_with_minor_only(self):
        """选 5 张小牌测试元素分布。"""
        from divination.engines.tarot import _build_deck
        deck = _build_deck()
        # deck[22..] 是小牌
        drawn = [dict(deck[22 + i]) for i in range(8)]
        for i, c in enumerate(drawn):
            c["位置"] = f"P{i}"
            c["方位"] = "正位"
            c["牌义"] = c["正位"]
        info = _element_distribution(drawn)
        total = sum(info["元素计数"].values())
        assert total == 8
        # 主导元素应为某一种
        assert info["主导元素"] in {"火", "土", "风", "水"}
        # 提示应有内容
        assert info["提示"] is not None


# ── 6. 综合解读 (中心十字 + 权杖柱) ─────────────────────
class TestCompositeNarrative:
    def test_narrative_has_required_fields(self):
        from divination.engines.tarot import _build_deck
        deck = _build_deck()
        drawn = []
        positions = SPREADS["celtic"]["positions"]
        for i, pos in enumerate(positions):
            card = dict(deck[i])
            card["位置"] = pos
            card["方位"] = "正位" if i % 2 == 0 else "逆位"
            card["牌义"] = card["逆位"] if i % 2 else card["正位"]
            drawn.append(card)
        analysis = {"元素分布": {"主导元素": "火", "主导主题": "行动"}}
        narrative = _compose_celtic_narrative(drawn, analysis)
        for field in ["中心十字牌数", "权杖柱牌数", "最终结果牌",
                      "最终结果方位", "综合文本", "读牌顺序建议"]:
            assert field in narrative, f"缺 {field}"
        # 综合文本应非空
        assert len(narrative["综合文本"]) > 10
        # 读牌顺序建议应是 4 步
        assert len(narrative["读牌顺序建议"]) == 4

    def test_narrative_includes_element_theme(self):
        from divination.engines.tarot import _build_deck
        deck = _build_deck()
        drawn = []
        for i, pos in enumerate(SPREADS["celtic"]["positions"]):
            card = dict(deck[i])
            card["位置"] = pos
            card["方位"] = "正位"
            card["牌义"] = card["正位"]
            drawn.append(card)
        analysis = {"元素分布": {"主导元素": "水", "主导主题": "情感·关系·直觉"}}
        narrative = _compose_celtic_narrative(drawn, analysis)
        assert "情感" in narrative["综合文本"] or "关系" in narrative["综合文本"]


# ── 7. _analyze 集成 (凯尔特 vs 其他牌阵) ─────────────────
class TestAnalyzeIntegration:
    def test_celtic_analysis_has_extra_fields(self):
        """凯尔特十字分析应包含位置含义 + 关系矩阵 + 综合解读。"""
        from divination.engines.tarot import _analyze, _build_deck
        deck = _build_deck()
        drawn = []
        for i, pos in enumerate(SPREADS["celtic"]["positions"]):
            card = dict(deck[i])
            card["位置"] = pos
            card["方位"] = "正位"
            card["牌义"] = card["正位"]
            drawn.append(card)
        a = _analyze(drawn, spread="celtic")
        assert "位置含义" in a
        assert "位置关系" in a
        assert "综合解读" in a
        assert "evidence_sources" in a
        # 位置含义应有 10 个
        assert len(a["位置含义"]) == 10
        # evidence_sources 应含 RWS
        evs = a["evidence_sources"]
        assert any("RWS" in s for s in evs)

    def test_non_celtic_analysis_basic(self):
        """非凯尔特牌阵 → 基础分析字段 + 简化 evidence。"""
        from divination.engines.tarot import _analyze, _build_deck
        deck = _build_deck()
        drawn = []
        for i, pos in enumerate(SPREADS["three"]["positions"]):
            card = dict(deck[i])
            card["位置"] = pos
            card["方位"] = "正位"
            card["牌义"] = card["正位"]
            drawn.append(card)
        a = _analyze(drawn, spread="three")
        assert "元素分布" in a
        assert "宫廷画像" in a
        assert "整体提示" in a
        # 不应有 位置关系 (凯尔特专属)
        assert "位置关系" not in a


# ── 8. compute() 端到端 ─────────────────────────────────
class TestComputeEndToEnd:
    def test_compute_celtic_full(self):
        b = Birth(year=1990, month=6, day=15, hour=12, minute=0,
                  gender="unspecified", lat=None, lng=None, tz="Asia/Shanghai")
        r = compute(b, spread="celtic", seed=42)
        assert r.method == "tarot"
        assert "牌组分析" in r.raw
        analysis = r.raw["牌组分析"]
        # 10 张牌
        assert len(r.raw["牌面"]) == 10
        # 凯尔特专属字段
        assert "位置含义" in analysis
        assert "位置关系" in analysis
        assert "综合解读" in analysis
        # evidence
        assert "evidence_sources" in analysis

    def test_compute_celtic_deterministic_with_seed(self):
        b = Birth(year=1990, month=6, day=15, hour=12, minute=0)
        r1 = compute(b, spread="celtic", seed=42)
        r2 = compute(b, spread="celtic", seed=42)
        cards1 = [(c["牌"], c["方位"]) for c in r1.raw["牌面"]]
        cards2 = [(c["牌"], c["方位"]) for c in r2.raw["牌面"]]
        assert cards1 == cards2

    def test_compute_celtic_via_alias(self):
        """别名 'celtic_cross' 应映射到 'celtic'。"""
        b = Birth(year=1990, month=6, day=15, hour=12, minute=0)
        r = compute(b, spread="celtic_cross", seed=42)
        assert r.raw["牌阵"] == "celtic"
        assert len(r.raw["牌面"]) == 10

    def test_compute_three_spread_unchanged(self):
        """普通三张牌阵 → 不应有凯尔特专属字段。"""
        b = Birth(year=1990, month=6, day=15, hour=12, minute=0)
        r = compute(b, spread="three", seed=42)
        assert "牌组分析" in r.raw
        assert "位置关系" not in r.raw["牌组分析"]


# ── 9. _build_position_meanings 通用 ─────────────────────
class TestBuildPositionMeanings:
    def test_three_spread_positions(self):
        meanings = _build_position_meanings("three")
        assert len(meanings) == 3
        for pos in ["过去", "现在", "未来"]:
            assert pos in meanings
            assert "index" in meanings[pos]
            assert "落点" in meanings[pos]

    def test_unknown_spread_falls_back(self):
        """未知牌阵名 → 不崩溃, 用通用读法。"""
        meanings = _build_position_meanings("nonexistent_spread")
        assert isinstance(meanings, dict)
