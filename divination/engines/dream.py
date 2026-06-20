"""解梦引擎 v2 — 周公解梦 + 同义词扩展 + 组合梦境 + 情绪识别。

文献：
  - 《周公解梦》(托名周公·周代) — 主数据源
  - 《梦占逸旨》(明·陈士元)
  - 《梦溪笔谈》(宋·沈括)
  - 《说文解字》(汉·许慎) — 同族字根源

匹配算法 (v2):
  1. 中文分词 (jieba-like 简化): 按字符 / 词组扫描
  2. 关键词权重:
     - symbol 主名 1.0
     - aliases 0.7
     - 同义词 (variant) 0.5  ← 新增 (来自 dream_synonyms.SYNONYM_GROUPS)
     - context_modifiers 0.9
  3. 组合梦境检测 (新增) — 多符号组合的吉凶判定
  4. 情绪识别 (新增) — 关键词层面吉凶判定
  5. 综合打分 → Top-N 匹配 + 类别分布 + 吉凶倾向

输入: 梦境描述 (自由文本)
输出: 匹配条目 + 组合解读 + 情绪识别 + 类别分布 + 情境建议
"""
from __future__ import annotations

from typing import Any

from ..contracts import Birth, ChartResult
from ..data.dream_corpus import DREAM_ENTRIES, list_by_category, count_by_category
from ..data.dream_synonyms import (
    COMBO_INTERPRETATIONS,
    detect_emotion,
    find_combo,
    get_canonical,
)


# ══════════════════════════════════════════════════════════════
# 1. 关键词分词（简化版）
# ══════════════════════════════════════════════════════════════
def _extract_keywords(text: str) -> list[str]:
    """从梦境描述中提取关键词。

    简化策略:
      1. 按空格/标点分句
      2. 每个分句 1-4 字滑动窗口
      3. 与数据库 symbol/aliases/context_modifiers 匹配

    Args:
        text: 梦境描述（如 "我梦见一条龙在天上飞"）

    Returns:
        提取的关键词列表
    """
    import re
    text = re.sub(r"[，。！？、；：""''「」『』《》（）()\[\]]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return []

    keywords = set()
    chars = text
    for window_size in range(1, 5):
        for i in range(len(chars) - window_size + 1):
            word = chars[i:i + window_size]
            if len(word.strip()) == window_size:
                keywords.add(word)
    return list(keywords)


# ══════════════════════════════════════════════════════════════
# 2. 单条目打分 (v2: 加入同义词权重 0.5)
# ══════════════════════════════════════════════════════════════
def _score_entry(entry: dict, keywords: list[str]) -> tuple[float, list[str], list[str]]:
    """对单个梦境条目打分 (v2)。

    Args:
        entry: 单个梦境条目
        keywords: 提取的关键词列表

    Returns:
        (score, matched_contexts, matched_synonyms)
        - score: 0-1 之间
        - matched_contexts: 触发的情境修饰
        - matched_synonyms: 触发的同义词 variants (新)
    """
    score = 0.0
    matched_contexts: list[str] = []
    matched_synonyms: list[str] = []

    # 主名匹配
    if entry["symbol"] in keywords:
        score += 1.0

    # 别名匹配
    for alias in entry.get("aliases", []):
        if alias in keywords:
            score += 0.7

    # 同义词匹配 (v2 新增) — 通过 canonical (主符号或别名) 反查
    for kw in keywords:
        canonical = get_canonical(kw)
        if canonical and (canonical == entry["symbol"] or canonical in entry.get("aliases", [])):
            score += 0.5
            matched_synonyms.append(kw)

    # 情境修饰匹配
    for ctx_key, ctx_meaning in entry.get("context_modifiers", {}).items():
        for kw in keywords:
            if kw in ctx_key:
                score += 0.9
                matched_contexts.append(ctx_key)
                break

    # 归一化: 最高可能得分 = 1.0 + 0.7*N_alias + 0.5*N_synonyms + 0.9*N_ctx
    n_ctx = len(entry.get("context_modifiers", {}))
    max_possible = 1.0 + 0.7 * len(entry.get("aliases", [])) + 0.9 * n_ctx
    if max_possible > 0:
        normalized = min(score / max_possible, 1.0)
    else:
        normalized = 0.0

    return normalized, matched_contexts, matched_synonyms


# ══════════════════════════════════════════════════════════════
# 3. 完整梦境分析 (v2: 含组合梦境 + 情绪识别 + 类别分布)
# ══════════════════════════════════════════════════════════════
def interpret_dream(dream_text: str, top_n: int = 5) -> dict[str, Any]:
    """解梦主函数 v2。

    Args:
        dream_text: 梦境描述 (中文自由文本)
        top_n: 返回 Top N 个匹配

    Returns:
        {
            "dream_text": 原始输入,
            "keywords": 提取的关键词列表,
            "matches": Top N 匹配 (含 synonyms 触发记录),
            "combos": 组合梦境解读列表 (v2 新),
            "emotion": 情绪吉凶识别 (v2 新),
            "category_distribution": 类别分布 (v2 新),
            "summary": 综合解读摘要,
            "overall_luck": 总体吉凶
        }
    """
    keywords = _extract_keywords(dream_text)

    scored: list[tuple[float, dict, list[str], list[str]]] = []
    for entry in DREAM_ENTRIES:
        score, contexts, synonyms = _score_entry(entry, keywords)
        if score > 0.0:
            scored.append((score, entry, contexts, synonyms))

    # 按得分降序
    scored.sort(key=lambda x: -x[0])

    # 取 Top N
    top_matches = scored[:top_n]

    # 整理输出
    matches = []
    for score, entry, contexts, synonyms in top_matches:
        matches.append({
            "symbol": entry["symbol"],
            "category": entry["category"],
            "score": round(score, 3),
            "interpretation": entry["interpretation"],
            "classic_text": entry["classic_text"],
            "matched_contexts": contexts,
            "matched_synonyms": synonyms,  # v2 新
            "context_meanings": [entry["context_modifiers"].get(c, "") for c in contexts],
        })

    # ── 类别分布 ──
    cat_dist: dict[str, int] = {}
    for _, entry, _, _ in scored:
        cat = entry["category"]
        cat_dist[cat] = cat_dist.get(cat, 0) + 1

    # ── 组合梦境检测 ──
    # 收集所有命中的主符号 (含别名解析为 symbol)
    hit_symbols: set[str] = set()
    for _, entry, _, _ in scored:
        hit_symbols.add(entry["symbol"])

    combos = find_combo(hit_symbols, dream_text)

    # ── 情绪识别 ──
    emotion = detect_emotion(dream_text)

    # ── 综合摘要 (v2: 含组合梦境 + 情绪) ──
    if not matches and not combos:
        summary = "未匹配到已收录的梦境符号。建议尝试更具体的描述（如提及动物、物品、行为）。"
        overall_luck = "未知"
    else:
        # 优先: 组合梦境 + 情绪 + Top 1
        top_match = matches[0] if matches else None

        parts = []
        if combos:
            parts.append(f"组合梦境: 「{combos[0]['name']}」 - {combos[0]['interpretation']}")
        if top_match:
            parts.append(f"主匹配: {top_match['symbol']} ({top_match['score']:.0%})")
        if emotion["evidence_keywords"]:
            parts.append(f"情绪倾向: {emotion['luck_tendency']}")
        summary = " | ".join(parts) if parts else "未匹配"

        # overall_luck 优先级: combo > emotion > top_match
        if combos:
            combo_text = combos[0]["interpretation"]
            if "大吉" in combo_text:
                overall_luck = "大吉"
            elif "凶" in combo_text and "吉" not in combo_text:
                overall_luck = "凶"
            else:
                overall_luck = "吉"
        elif emotion["evidence_keywords"]:
            overall_luck = emotion["luck_tendency"]
        elif top_match:
            overall_luck = "大吉" if "大吉" in top_match["interpretation"] else \
                          "吉" if "吉" in top_match["interpretation"] and "凶" not in top_match["interpretation"] else \
                          "凶" if "凶" in top_match["interpretation"] and "吉" not in top_match["interpretation"] else "中性"
        else:
            overall_luck = "中性"

    return {
        "dream_text": dream_text,
        "keywords": keywords,
        "matches": matches,
        "combos": combos,                       # v2 新
        "emotion": emotion,                     # v2 新
        "category_distribution": cat_dist,      # v2 新
        "summary": summary,
        "overall_luck": overall_luck,
    }


# ══════════════════════════════════════════════════════════════
# 4. 按符号精确查询
# ══════════════════════════════════════════════════════════════
def lookup_symbol(symbol: str) -> dict | None:
    """精确查询某符号的完整信息。"""
    for entry in DREAM_ENTRIES:
        if entry["symbol"] == symbol or symbol in entry.get("aliases", []):
            return entry
    return None


# ══════════════════════════════════════════════════════════════
# 5. 按分类查询
# ══════════════════════════════════════════════════════════════
def list_by_category_dreams(category: str) -> list[dict]:
    """按分类查询梦境（包装 data/dream_corpus）。"""
    return list_by_category(category)


def get_corpus_stats() -> dict:
    """返回语料库统计。"""
    return {
        "total_entries": len(DREAM_ENTRIES),
        "categories": count_by_category(),
        "classic_sources": sorted({e["classic_text"] for e in DREAM_ENTRIES}),
    }


# ══════════════════════════════════════════════════════════════
# 6. 引擎 compute (与其他 engines 一致的接口)
# ══════════════════════════════════════════════════════════════
def compute(b: Birth, dream_text: str = "") -> ChartResult:
    """解梦引擎主函数。

    用法:
        compute(birth, dream_text="我梦见一条龙在天上飞")
    """
    if not dream_text:
        return ChartResult(
            method="dream", school="east", engine="self(周公解梦 v2)",
            normalized={"elements": {}, "timeline": []},
            raw={"error": "请输入梦境描述"}
        )

    result = interpret_dream(dream_text)

    return ChartResult(
        method="dream", school="east", engine="self(周公解梦 v2)",
        normalized={"elements": {}, "timeline": []},
        raw={
            "dream_text": result["dream_text"],
            "matches": result["matches"],
            "combos": result["combos"],
            "emotion": result["emotion"],
            "category_distribution": result["category_distribution"],
            "summary": result["summary"],
            "overall_luck": result["overall_luck"],
            "corpus_stats": get_corpus_stats(),
            "evidence_sources": [
                "《周公解梦》(托名周公·周代) — 主数据源",
                "《梦占逸旨》(明·陈士元) — 解梦理论",
                "《梦溪笔谈》(宋·沈括) — 笔记解梦观察",
                "《说文解字》(汉·许慎) — 同族字根源",
            ],
        }
    )


# ══════════════════════════════════════════════════════════════
# 7. 自检
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=== 解梦引擎 v2 自检 ===\n")

    # 1. 语料统计
    stats = get_corpus_stats()
    print(f"1. 语料统计:")
    print(f"   总条目: {stats['total_entries']}")
    print(f"   分类: {stats['categories']}")
    print(f"   出处: {stats['classic_sources']}")

    # 2. 测试梦境
    print("\n2. 梦境匹配测试 (含同义词 + 组合梦境):")
    test_dreams = [
        "我梦见一条龙在天上飞",
        "梦见蛟龙入水中",                      # 同义词: 蛟 → 龙
        "梦见掉牙",
        "看见大水涌来",
        "梦里骑着一匹黑马",
        "结婚典礼上自己穿着红衣",
        "梦到佛祖",
        "梦到白色花朵盛开",
        "梦见血光之灾",
    ]
    for d in test_dreams:
        r = interpret_dream(d, top_n=3)
        print(f"\n   梦境: {d}")
        print(f"   摘要: {r['summary']}")
        print(f"   吉凶: {r['overall_luck']}")
        if r["combos"]:
            print(f"   组合: {[c['name'] for c in r['combos']]}")
        for m in r['matches']:
            ctx = f" (情境: {', '.join(m['matched_contexts'])})" if m['matched_contexts'] else ""
            syn = f" (同义: {', '.join(m['matched_synonyms'])})" if m['matched_synonyms'] else ""
            print(f"     - {m['symbol']} ({m['category']}): {m['score']:.0%} | {m['interpretation'][:30]}...{ctx}{syn}")