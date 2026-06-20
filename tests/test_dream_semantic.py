"""Tests for 解梦语义向量 (engines/dream.py v2 + data/dream_synonyms.py)

深化验证:
  - 同义词扩展匹配 (权重 0.5)
  - 组合梦境解读 (龙 + 水 = 龙入水)
  - 情绪识别 (吉凶倾向)
  - Top-N 多维匹配 + 类别分布
  - evidence_sources 引用《周公解梦》《梦占逸旨》《梦溪笔谈》

文献: 《周公解梦》《梦占逸旨》《梦溪笔谈》《说文解字》
"""
from __future__ import annotations

import pytest

from divination.contracts import Birth
from divination.data.dream_synonyms import (
    COMBO_INTERPRETATIONS,
    LUCK_KEYWORDS,
    SYNONYM_GROUPS,
    all_variants,
    detect_emotion,
    find_combo,
    get_canonical,
    get_synonyms,
)
from divination.engines.dream import (
    _extract_keywords,
    _score_entry,
    compute,
    get_corpus_stats,
    interpret_dream,
    lookup_symbol,
)


# ══════════════════════════════════════════════════════════════
# 1. 同义词基础 (synonyms)
# ══════════════════════════════════════════════════════════════
def test_synonym_groups_at_least_50():
    """至少 50 组同义词。"""
    assert len(SYNONYM_GROUPS) >= 50


def test_synonym_groups_total_variants_at_least_150():
    """所有变体总数至少 150 (每组平均 ≥ 3)。"""
    total = sum(len(v) for v in SYNONYM_GROUPS.values())
    assert total >= 150


def test_synonym_canonical_dragon():
    """蛟/虬 → 龙。"""
    assert get_canonical("蛟") == "龙"
    assert get_canonical("虬") == "龙"
    assert get_canonical("青龙") == "龙"


def test_synonym_canonical_water():
    """江/河/海/湖 → 水。"""
    assert get_canonical("江") == "水"
    assert get_canonical("河") == "水"
    assert get_canonical("海") == "水"
    assert get_canonical("湖") == "水"


def test_synonym_canonical_teeth():
    """齿 → 牙。"""
    assert get_canonical("齿") == "牙"
    assert get_canonical("牙齿") == "牙"


def test_synonym_canonical_sun_moon():
    """日/金乌 → 太阳; 月/婵娟 → 月亮。"""
    assert get_canonical("日") == "太阳"
    assert get_canonical("金乌") == "太阳"
    assert get_canonical("月") == "月亮"
    assert get_canonical("婵娟") == "月亮"


def test_synonym_get_synonyms_reverse():
    """get_synonyms('龙') 应包含所有龙系变体。"""
    syns = get_synonyms("龙")
    assert "蛟" in syns
    assert "虬" in syns


def test_synonym_all_variants_returns_set():
    """all_variants 返回 set。"""
    v = all_variants()
    assert isinstance(v, set)
    assert len(v) >= 150


# ══════════════════════════════════════════════════════════════
# 2. 同义词匹配 (in _score_entry)
# ══════════════════════════════════════════════════════════════
def test_synonym_matching_via_score_entry():
    """同义词变体应触发 symbol 条目得分。"""
    e = {"symbol": "龙", "aliases": [], "context_modifiers": {}}
    # "蛟" 是 龙 的同义词
    score, _, matched_synonyms = _score_entry(e, ["蛟"])
    assert score > 0
    assert "蛟" in matched_synonyms


def test_synonym_matching_weight_0_5():
    """同义词权重应为 0.5 (vs alias 0.7 / symbol 1.0)。"""
    # 构造: canonical = "龙"
    e = {"symbol": "龙", "aliases": [], "context_modifiers": {}}
    # max_possible = 1.0 + 0.5*0(variant in entry? no) + 0 = 1.0
    # score 加 0.5 → normalized = 0.5
    score, _, _ = _score_entry(e, ["蛟"])
    # 蛟 → canonical = 龙 == entry.symbol → score += 0.5
    # normalized = 0.5 / 1.0 = 0.5
    assert 0.45 <= score <= 0.55


def test_synonym_matching_priority_over_alias():
    """主名匹配 (1.0) > 别名 (0.7) > 同义词 (0.5)。"""
    # 三个完全等价的 entry (symbol=龙, aliases=["金龙"], 无 context)
    e = {"symbol": "龙", "aliases": ["金龙"], "context_modifiers": {}}
    # max_possible = 1.0 + 0.7*1 + 0.9*0 = 1.7
    s_main, _, _ = _score_entry(e, ["龙"])
    s_alias, _, _ = _score_entry(e, ["金龙"])
    s_syn, _, _ = _score_entry(e, ["蛟"])
    # 主名: 1.0 / 1.7 ≈ 0.588
    # 别名: 0.7 / 1.7 ≈ 0.412
    # 同义: 0.5 / 1.7 ≈ 0.294
    assert s_main > s_alias > s_syn
    assert 0.55 < s_main < 0.62
    assert 0.39 < s_alias < 0.43
    assert 0.27 < s_syn < 0.31


def test_synonym_water_via_score_entry():
    """'江' → 水 (同义词)。"""
    e = {"symbol": "水", "aliases": [], "context_modifiers": {}}
    score, _, syns = _score_entry(e, ["江"])
    assert "江" in syns
    assert score > 0


# ══════════════════════════════════════════════════════════════
# 3. 组合梦境
# ══════════════════════════════════════════════════════════════
def test_combo_dragon_water():
    """龙 + 水 → 龙入水 (大吉)。"""
    combos = find_combo({"龙", "水"}, "梦见龙在水中")
    assert any(c["name"] == "龙入水" for c in combos)


def test_combo_dragon_fly():
    """龙 + 飞 → 龙飞上天 (大吉)。"""
    combos = find_combo({"龙", "飞"}, "梦见龙飞上天")
    assert any(c["name"] == "龙飞上天" for c in combos)


def test_combo_snake_ru_huai():
    """蛇 + 入怀中 → 蛇入怀 (大吉, 贵子)。"""
    combos = find_combo({"蛇", "入怀中"}, "梦见蛇入怀中")
    assert any(c["name"] == "蛇入怀" for c in combos)


def test_combo_gold_jade():
    """金 + 玉 → 金玉满堂 (大吉)。"""
    combos = find_combo({"金", "玉"}, "梦见金玉")
    assert any(c["name"] == "金玉满堂" for c in combos)


def test_combo_self_death():
    """死 + 自己 → 自己死 (大吉, 长寿)。"""
    combos = find_combo({"死", "自己"}, "梦见自己死")
    assert any(c["name"] == "自己死" for c in combos)


def test_combo_interpretations_count_at_least_10():
    """组合解读至少 10 条。"""
    assert len(COMBO_INTERPRETATIONS) >= 10


# ══════════════════════════════════════════════════════════════
# 4. 情绪识别
# ══════════════════════════════════════════════════════════════
def test_emotion_luck_keywords_present():
    """LUCK_KEYWORDS 应覆盖 大吉/吉/中性/小凶/凶。"""
    assert "大吉" in LUCK_KEYWORDS
    assert "吉" in LUCK_KEYWORDS
    assert "中性" in LUCK_KEYWORDS
    assert "小凶" in LUCK_KEYWORDS
    assert "凶" in LUCK_KEYWORDS


def test_detect_emotion_daji():
    """"大吉" 关键词 → 大吉倾向。"""
    e = detect_emotion("梦见大吉之象, 进财")
    assert e["luck_tendency"] in {"大吉", "吉"}
    assert e["score"] > 0


def test_detect_emotion_xiong():
    """"凶" 关键词 → 凶倾向。"""
    e = detect_emotion("梦见血光之灾, 慎防")
    assert e["luck_tendency"] in {"小凶", "凶"}
    assert e["score"] < 0


def test_detect_emotion_neutral():
    """无关键词 → 中性。"""
    e = detect_emotion("今天天气真好")
    assert e["luck_tendency"] == "中性"
    assert e["score"] == 0


# ══════════════════════════════════════════════════════════════
# 5. interpret_dream v2 (整合输出)
# ══════════════════════════════════════════════════════════════
def test_interpret_returns_combos():
    """interpret_dream v2 应输出 combos 字段。"""
    r = interpret_dream("梦见龙在水中", top_n=3)
    assert "combos" in r
    assert isinstance(r["combos"], list)


def test_interpret_returns_emotion():
    """interpret_dream v2 应输出 emotion 字段。"""
    r = interpret_dream("梦见大吉之象", top_n=3)
    assert "emotion" in r
    assert "luck_tendency" in r["emotion"]


def test_interpret_returns_category_distribution():
    """interpret_dream v2 应输出 category_distribution 字段。"""
    r = interpret_dream("梦见龙和蛇", top_n=5)
    assert "category_distribution" in r
    assert isinstance(r["category_distribution"], dict)


def test_interpret_top_n_limit():
    """top_n 限制返回数量。"""
    r = interpret_dream("梦见龙蛇虎马鱼", top_n=2)
    assert len(r["matches"]) <= 2


def test_interpret_overall_luck_valid():
    """overall_luck 必须是有效枚举。"""
    valid = {"大吉", "吉", "中吉", "中性", "小凶", "凶", "未知"}
    for dream in ["梦见龙在天上飞", "梦见血", "梦见死"]:
        r = interpret_dream(dream, top_n=1)
        assert r["overall_luck"] in valid


def test_interpret_synonym_dragon_jiang():
    """"梦见蛟" (同义词) 应命中龙条目。"""
    r = interpret_dream("梦见蛟在天上飞", top_n=20)
    assert any(m["symbol"] == "龙" for m in r["matches"])


def test_interpret_synonym_in_matched_synonyms():
    """'matched_synonyms' 字段应包含同义词命中。"""
    r = interpret_dream("梦见蛟在天上飞", top_n=20)
    dragon_match = next((m for m in r["matches"] if m["symbol"] == "龙"), None)
    assert dragon_match is not None
    assert "蛟" in dragon_match["matched_synonyms"]


def test_interpret_combo_dragon_water_activates():
    """'梦见龙入水' 应触发 '龙入水' 组合解读。"""
    r = interpret_dream("梦见龙入水", top_n=5)
    assert any(c["name"] == "龙入水" for c in r["combos"])


# ══════════════════════════════════════════════════════════════
# 6. compute() 引擎接口 + evidence_sources
# ══════════════════════════════════════════════════════════════
def test_compute_has_evidence_sources():
    """compute() 输出含 evidence_sources。"""
    b = Birth(year=1990, month=5, day=15, hour=8, minute=30, gender="male",
              calendar="gregorian", lat=31.23, lng=121.47, tz="Asia/Shanghai")
    r = compute(b, dream_text="梦见龙在天上飞")
    sources = r.raw["evidence_sources"]
    assert any("周公解梦" in s for s in sources)
    assert any("梦占逸旨" in s or "梦溪笔谈" in s for s in sources)


def test_compute_returns_v2_engine_name():
    """compute() engine 字段标识 v2。"""
    b = Birth(year=1990, month=5, day=15, hour=8, minute=30, gender="male",
              calendar="gregorian", lat=31.23, lng=121.47, tz="Asia/Shanghai")
    r = compute(b, dream_text="梦见龙")
    assert "v2" in r.engine


def test_compute_v2_includes_combos_emotion_cat_dist():
    """compute() v2 输出含 combos/emotion/category_distribution。"""
    b = Birth(year=1990, month=5, day=15, hour=8, minute=30, gender="male",
              calendar="gregorian", lat=31.23, lng=121.47, tz="Asia/Shanghai")
    r = compute(b, dream_text="梦见龙在水中")
    assert "combos" in r.raw
    assert "emotion" in r.raw
    assert "category_distribution" in r.raw


def test_compute_without_text_returns_error():
    """无 dream_text → 返回 error。"""
    b = Birth(year=1990, month=5, day=15, hour=8, minute=30, gender="male",
              calendar="gregorian", lat=31.23, lng=121.47, tz="Asia/Shanghai")
    r = compute(b)
    assert "error" in r.raw


# ══════════════════════════════════════════════════════════════
# 7. Backward compatibility (v1 tests still pass)
# ══════════════════════════════════════════════════════════════
def test_score_entry_returns_3_tuple():
    """_score_entry v2 应返回 (score, contexts, synonyms) 三元组。"""
    e = {"symbol": "龙", "aliases": [], "context_modifiers": {"龙飞上天": "大吉"}}
    result = _score_entry(e, ["龙", "龙飞上天"])
    assert len(result) == 3
    score, contexts, synonyms = result
    assert isinstance(score, float)
    assert isinstance(contexts, list)
    assert isinstance(synonyms, list)


def test_extract_keywords_basic():
    """基础关键词提取仍工作。"""
    keywords = _extract_keywords("我梦见一条龙在天上飞")
    assert "龙" in keywords
    assert "飞" in keywords


def test_classic_dragon_lookup():
    """经典龙 → 大吉 (lookup_symbol 仍工作)。"""
    e = lookup_symbol("龙")
    assert e is not None
    assert "大吉" in e["interpretation"]


def test_corpus_stats_includes_total_entries():
    """get_corpus_stats 输出完整。"""
    stats = get_corpus_stats()
    assert "total_entries" in stats
    assert stats["total_entries"] >= 120