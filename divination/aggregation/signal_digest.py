"""Sprint 1.4 — 五档 SignalDigest 解析器。

每个术法 normalizer 必须从此模块调用, 严禁 LLM 估档。
所有解析基于规则 (关键词 + 极性/强度), 零外部调用。

5 档 (同 DimensionPolarity):
  STRONG_SUPPORT — 大吉/大利/极佳/极好/上吉/上上
  WEAK_SUPPORT   — 吉/利/可/成/好/顺
  NEUTRAL        — 平/中和/难断/未定/待定
  WEAK_WARN      — 慎/小凶/小阻/微凶
  STRONG_WARN    — 凶/大凶/忌/大败/灾难

参考:
- 公版古籍常用判词 (《滴天髓》《增删卜易》《卜筮正宗》等)
- 不用现代译注/评注
"""
from __future__ import annotations

from .schema import DimensionPolarity, DivinationSignal

# ── 关键词字典 ────────────────────────────────────────────────────────────

# 注意: 顺序敏感 (强在前, 弱在后)
DIGEST_KEYWORDS: dict[DimensionPolarity, tuple[str, ...]] = {
    DimensionPolarity.STRONG_SUPPORT: (
        "大吉", "极吉", "上吉", "上上", "大利", "大胜",
        "极佳", "显贵", "大成", "大成之象", "亨通",
    ),
    DimensionPolarity.WEAK_SUPPORT: (
        "吉", "利", "可", "成", "好", "顺", "小吉", "小利",
        "尚可", "勉强", "略吉", "稍吉", "可用", "可成",
        "利见大人", "大吉之象"  # 含"大吉"但被强档先匹配, 留这里仅文档化
    ),
    DimensionPolarity.NEUTRAL: (
        "平", "平常", "中和", "无显著", "难断", "未定", "待定",
        "平运", "中平", "持平",
    ),
    DimensionPolarity.WEAK_WARN: (
        "慎", "小凶", "小阻", "微凶", "略凶", "稍凶",
        "阻碍", "迟滞", "不宜", "避", "不吉", "不利",
    ),
    DimensionPolarity.STRONG_WARN: (
        "凶", "大凶", "极凶", "上凶", "忌", "大败", "灾难",
        "悔", "咎", "凶险", "凶兆", "必凶", "大不利", "诸事不宜",
    ),
}

# 强/弱分界阈值 (strength)
STRONG_THRESHOLD = 0.60


# ── 解析器 1: 从断语字符串 ──────────────────────────────────────────────

def parse_digest_from_verdict(
    verdict: str | None,
    default: DimensionPolarity = DimensionPolarity.NEUTRAL,
) -> DimensionPolarity:
    """从断语/判词字符串解析 5 档。

    规则:
      1. 空字符串 → default (默认 NEUTRAL)
      2. 强档优先扫描, 但若强档关键词前有"小/微/略/稍/弱"等弱化前缀
         则降级到对应弱档 (避免 "小凶" 误判为 STRONG_WARN)
      3. 全不命中 → NEUTRAL

    Args:
        verdict: 断语/判词/结论字符串 (例: "大吉之象", "卦象小凶")
        default: 解析失败时的默认档

    Returns:
        DimensionPolarity 之一
    """
    if not verdict:
        return default

    v = str(verdict).strip()
    if not v:
        return default

    # 弱化前缀: 出现则把 STRONG_* 降级为 WEAK_*
    weakener = ("小", "微", "略", "稍", "弱")
    has_weakener = any(w in v for w in weakener)

    # 强档优先
    for kw in DIGEST_KEYWORDS[DimensionPolarity.STRONG_SUPPORT]:
        if kw in v:
            return DimensionPolarity.WEAK_SUPPORT if has_weakener else DimensionPolarity.STRONG_SUPPORT
    for kw in DIGEST_KEYWORDS[DimensionPolarity.STRONG_WARN]:
        if kw in v:
            return DimensionPolarity.WEAK_WARN if has_weakener else DimensionPolarity.STRONG_WARN

    # 弱档
    for kw in DIGEST_KEYWORDS[DimensionPolarity.WEAK_SUPPORT]:
        if kw in v:
            return DimensionPolarity.WEAK_SUPPORT
    for kw in DIGEST_KEYWORDS[DimensionPolarity.WEAK_WARN]:
        if kw in v:
            return DimensionPolarity.WEAK_WARN

    # 中性关键词
    for kw in DIGEST_KEYWORDS[DimensionPolarity.NEUTRAL]:
        if kw in v:
            return DimensionPolarity.NEUTRAL

    return default


# ── 解析器 2: 从 polarity + strength ────────────────────────────────────

def digest_from_polarity_strength(
    polarity: str,
    strength: float,
) -> DimensionPolarity:
    """从极性 + 强度推导 5 档 (供 normalizer 已构造 polarity 的场景用)。

    映射:
      positive + strength ≥ 0.60 → STRONG_SUPPORT
      positive + strength < 0.60 → WEAK_SUPPORT
      negative + strength ≥ 0.60 → STRONG_WARN
      negative + strength < 0.60 → WEAK_WARN
      neutral / mixed            → NEUTRAL
    """
    if polarity == "positive":
        if strength >= STRONG_THRESHOLD:
            return DimensionPolarity.STRONG_SUPPORT
        return DimensionPolarity.WEAK_SUPPORT
    if polarity == "negative":
        if strength >= STRONG_THRESHOLD:
            return DimensionPolarity.STRONG_WARN
        return DimensionPolarity.WEAK_WARN
    return DimensionPolarity.NEUTRAL  # neutral / mixed → NEUTRAL


# ── 混合解析 (优先用 verdict, 回退到 polarity) ──────────────────────────

def determine_signal_digest(
    verdict: str | None = None,
    polarity: str | None = None,
    strength: float = 0.5,
) -> DimensionPolarity:
    """优先 verdict 解析, 回退 polarity+strength, 仍未知则 NEUTRAL。

    正常流:
      1. verdict 非空 → parse_digest_from_verdict
      2. 否则 polarity 非空 → digest_from_polarity_strength
      3. 兜底 NEUTRAL
    """
    if verdict and str(verdict).strip():
        return parse_digest_from_verdict(verdict)
    if polarity:
        return digest_from_polarity_strength(polarity, strength)
    return DimensionPolarity.NEUTRAL


# ── Signal 工厂 (封装, 防 normalizer 漏设) ──────────────────────────────

def attach_digest(signal: DivinationSignal) -> DivinationSignal:
    """给 signal 自动派生 signal_digest (如果还没设)。

    优先用 signal.evidence (含断语关键词) 解析, 回退 polarity+strength。
    已设的 signal_digest 不会被覆盖。
    """
    if signal.signal_digest is not None:
        return signal

    # evidence 中常含"用神甲木身强"等带判词的串
    digest = determine_signal_digest(
        verdict=signal.evidence,
        polarity=signal.polarity,
        strength=signal.strength,
    )
    return signal.model_copy(update={"signal_digest": digest})
