"""Tests for 解梦引擎 (divination/engines/dream.py + data/dream_corpus.py)

来源：docs/CLASSICAL_SOURCES.md §10 玄学知识库
文献：《周公解梦》《梦占逸旨》《梦溪笔谈》
"""
from __future__ import annotations

import pytest

from divination.data.dream_corpus import (
    CATEGORY_LIST,
    DREAM_ENTRIES,
    TOTAL_DREAMS,
    count_by_category,
    list_by_category,
)
from divination.engines.dream import (
    _extract_keywords,
    _score_entry,
    compute,
    get_corpus_stats,
    interpret_dream,
    lookup_symbol,
)


# ── 1. 语料完整性 ─────────────────────────────────
def test_dream_entries_count_at_least_120():
    """梦境条目至少 120 条（扩展后）。"""
    assert TOTAL_DREAMS >= 120
    assert len(DREAM_ENTRIES) >= 120


def test_dream_entries_required_fields():
    """每条梦境必须有 symbol, aliases, category, classic_text, interpretation, context_modifiers。"""
    required = {"symbol", "aliases", "category", "classic_text", "interpretation", "context_modifiers"}
    for entry in DREAM_ENTRIES:
        missing = required - set(entry.keys())
        assert not missing, f"{entry.get('symbol')} 缺失: {missing}"


def test_dream_categories_diverse():
    """分类覆盖至少 6 大类。"""
    assert len(CATEGORY_LIST) >= 6
    # 关键分类必须存在
    required = {"天象", "动物", "行为", "身体", "物品", "植物", "地理", "鬼神"}
    assert required <= set(CATEGORY_LIST)


def test_classic_text_zhougong():
    """周公解梦必须为多数条目来源。"""
    zg_count = sum(1 for e in DREAM_ENTRIES if "周公解梦" in e["classic_text"])
    assert zg_count >= 100  # 至少 100 条应来自周公解梦


# ── 2. 经典梦境符号 ─────────────────────────────────
def test_classic_dragon():
    """龙 → 大吉。"""
    e = lookup_symbol("龙")
    assert e is not None
    assert "大吉" in e["interpretation"]


def test_classic_death_long_life():
    """死亡 → 长寿（与字面相反）。"""
    e = lookup_symbol("死亡")
    assert e is not None
    assert "长寿" in e["interpretation"]


def test_classic_teeth_loss():
    """掉牙 → 亲人离散。"""
    e = lookup_symbol("掉牙")
    assert e is not None
    assert "亲人" in e["interpretation"]


def test_classic_blood_wealth():
    """血 → 财富（与西方相反）。"""
    e = lookup_symbol("血")
    assert e is not None
    assert "财" in e["interpretation"]


def test_classic_wedding_paradox():
    """婚礼 → 古解主凶。"""
    e = lookup_symbol("婚礼")
    assert e is not None
    assert "凶" in e["interpretation"]


def test_classic_cry_joy():
    """哭泣 → 大吉。"""
    e = lookup_symbol("哭泣")
    assert e is not None
    assert "吉" in e["interpretation"]


# ── 3. 关键词提取 ─────────────────────────────────
def test_extract_keywords_basic():
    """基础关键词提取。"""
    keywords = _extract_keywords("我梦见一条龙在天上飞")
    # 应包含 "龙", "飞", "天", "一条"
    assert "龙" in keywords
    assert "飞" in keywords


def test_extract_keywords_punctuation():
    """标点符号应被过滤。"""
    keywords = _extract_keywords("梦见，掉牙！流血。")
    assert "掉牙" in keywords
    assert "血" in keywords
    assert "，" not in keywords and "！" not in keywords


def test_extract_keywords_empty():
    """空输入应返回空列表。"""
    assert _extract_keywords("") == []


def test_extract_keywords_multi_char():
    """多字词组提取。"""
    keywords = _extract_keywords("梦到佛祖保佑")
    assert "佛" in keywords or "佛祖" in keywords


# ── 4. 单条打分 ─────────────────────────────────
def test_score_entry_perfect_match():
    """主名匹配 + 完整别名 + 情境 → 最高分。"""
    e = {"symbol": "龙", "aliases": ["金龙"], "context_modifiers": {"龙飞上天": "大吉"}}
    score, _, _ = _score_entry(e, ["龙", "金龙", "龙飞上天"])
    assert score >= 0.9


def test_score_entry_symbol_only():
    """仅主名匹配（无 context modifiers 时）。"""
    e = {"symbol": "龙", "aliases": ["金龙"], "context_modifiers": {}}
    score, _, _ = _score_entry(e, ["龙"])
    # 1.0 / (1.0 + 0.7*1) = 0.588
    assert 0.5 < score < 0.7


def test_score_entry_no_match():
    """无匹配 → 0。"""
    e = {"symbol": "龙", "aliases": [], "context_modifiers": {}}
    score, _, _ = _score_entry(e, ["蛇"])
    assert score == 0.0


def test_score_entry_context_match():
    """情境修饰匹配返回 contexts。"""
    e = {"symbol": "蛇", "aliases": [], "context_modifiers": {"蛇入怀中": "大吉"}}
    score, contexts, _ = _score_entry(e, ["蛇", "入怀"])
    assert "蛇入怀中" in contexts


def test_score_entry_context_increases_score():
    """情境匹配应增加 contexts 触发的数量。"""
    e_no_ctx = {"symbol": "蛇", "aliases": [], "context_modifiers": {}}
    e_with_ctx = {"symbol": "蛇", "aliases": [], "context_modifiers": {"蛇入怀": "吉"}}
    _, ctx_no, _ = _score_entry(e_no_ctx, ["蛇", "入怀"])
    _, ctx_with, _ = _score_entry(e_with_ctx, ["蛇", "入怀"])
    # 情境触发的 contexts 数应增加
    assert len(ctx_with) > len(ctx_no)


# ── 5. 完整梦境解读 ─────────────────────────────
def test_interpret_dream_dragon():
    """梦见龙 → 主吉。"""
    r = interpret_dream("我梦见一条龙在天上飞", top_n=3)
    assert len(r["matches"]) > 0
    top = r["matches"][0]
    assert top["symbol"] == "龙"
    assert top["score"] > 0.5


def test_interpret_dream_falling_teeth():
    """梦见掉牙 → 命中掉牙条目。"""
    r = interpret_dream("梦见自己掉牙", top_n=3)
    assert any(m["symbol"] == "掉牙" for m in r["matches"])


def test_interpret_dream_riding_horse():
    """梦见骑马 → 命中马。"""
    r = interpret_dream("梦里骑着一匹马", top_n=3)
    assert any(m["symbol"] == "马" for m in r["matches"])


def test_interpret_dream_water():
    """梦见水 → 命中水。"""
    r = interpret_dream("看见大水", top_n=3)
    assert any(m["symbol"] == "水" for m in r["matches"])


def test_interpret_dream_no_match():
    """无匹配梦境（与所有符号都无关的文本）。"""
    # 用与所有符号都无关的纯文本
    r = interpret_dream("今天我学习了新知识", top_n=3)
    # 任何匹配都应 score < 0.3 (微弱匹配)
    for m in r["matches"]:
        assert m["score"] < 0.3, f"意外强匹配: {m}"


def test_interpret_dream_overall_luck_classification():
    """overall_luck 必须是有效枚举。"""
    valid = {"大吉", "吉", "中吉", "中性", "凶", "未知"}
    for dream in ["梦见龙", "梦见死", "梦见掉牙", "梦见血"]:
        r = interpret_dream(dream, top_n=1)
        assert r["overall_luck"] in valid


def test_interpret_dream_top_n_limit():
    """top_n 限制返回数量。"""
    r = interpret_dream("梦见龙蛇虎马鱼", top_n=2)
    assert len(r["matches"]) <= 2


def test_interpret_dream_sorted_by_score():
    """结果应按 score 降序。"""
    r = interpret_dream("梦见龙飞", top_n=5)
    scores = [m["score"] for m in r["matches"]]
    assert scores == sorted(scores, reverse=True)


def test_interpret_dream_returns_full_dict():
    """返回完整字段。"""
    r = interpret_dream("梦见龙", top_n=1)
    required = {"dream_text", "keywords", "matches", "summary", "overall_luck"}
    assert required <= set(r.keys())


def test_interpret_dream_summary_includes_top_match():
    """摘要应包含 Top 1 符号名。"""
    r = interpret_dream("梦见龙在天上飞", top_n=3)
    assert "龙" in r["summary"]


def test_interpret_dream_strong_match_high_score():
    """强匹配 → score >= 0.5 (实际算法上下文有多个 modifier 会被算入)。"""
    r = interpret_dream("梦见一条龙在天上飞", top_n=1)
    if r["matches"]:
        assert r["matches"][0]["score"] >= 0.5


# ── 6. lookup_symbol ───────────────────────────────
def test_lookup_symbol_exact():
    """精确查询。"""
    e = lookup_symbol("龙")
    assert e is not None
    assert e["symbol"] == "龙"


def test_lookup_symbol_alias():
    """别名查询。"""
    e = lookup_symbol("蛟龙")  # 是龙的别名
    assert e is not None
    assert e["symbol"] == "龙"


def test_lookup_symbol_unknown():
    """未知符号 → None。"""
    e = lookup_symbol("不存在的符号")
    assert e is None


# ── 7. 按分类查询 ───────────────────────────────
def test_list_by_category_animal():
    """动物类至少 5 条。"""
    animals = list_by_category("动物")
    assert len(animals) >= 5
    symbols = {a["symbol"] for a in animals}
    assert "龙" in symbols or "蛇" in symbols


def test_list_by_category_celestial():
    """天象类至少 5 条。"""
    celestial = list_by_category("天象")
    assert len(celestial) >= 5


def test_count_by_category_total():
    """分类统计总和 = TOTAL_DREAMS。"""
    counts = count_by_category()
    assert sum(counts.values()) == TOTAL_DREAMS


# ── 8. get_corpus_stats ─────────────────────────
def test_corpus_stats_has_required_fields():
    """统计必须含 total_entries, categories, classic_sources。"""
    stats = get_corpus_stats()
    for k in ["total_entries", "categories", "classic_sources"]:
        assert k in stats


def test_corpus_stats_total_matches():
    """total_entries 应等于 DREAM_ENTRIES 长度。"""
    stats = get_corpus_stats()
    assert stats["total_entries"] == len(DREAM_ENTRIES)


# ── 9. compute() 引擎接口 ──────────────────────
def test_compute_with_text():
    """compute() 接受 dream_text。"""
    from divination.contracts import Birth
    b = Birth(year=1990, month=5, day=15, hour=8, minute=30, gender="male",
              calendar="gregorian", lat=31.23, lng=121.47, tz="Asia/Shanghai")
    r = compute(b, dream_text="梦见龙在天上飞")
    assert r.method == "dream"
    assert "matches" in r.raw
    assert "summary" in r.raw


def test_compute_without_text():
    """compute() 无 dream_text → 返回 error。"""
    from divination.contracts import Birth
    b = Birth(year=1990, month=5, day=15, hour=8, minute=30, gender="male",
              calendar="gregorian", lat=31.23, lng=121.47, tz="Asia/Shanghai")
    r = compute(b)
    assert "error" in r.raw
