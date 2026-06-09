"""交叉验证引擎 — 对 12 术法的统一信号进行加权交叉验证。

VAL-001: validate_signals(signals, weights)
VAL-002: 按 signal_key 分组归并
VAL-003~005: 正向/负向/中性加权统计
VAL-006~007: 阈值共识/冲突检测
VAL-008: conflict severity (low/medium/high)
VAL-009: conflict resolution 调和建议
VAL-010: overall_score 0-100
VAL-011: confidence_level (low/medium/medium_high/high)
VAL-012: 风险提取 (含 mixed 信号)
VAL-013: 时间窗口提取 (time_scope + timing signals)
VAL-014: 行动建议生成 (advice 字段)
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from .schema import (
    ConflictItem,
    ConsensusItem,
    DivinationSignal,
    ValidationResult,
)

# ── 共识/冲突阈值 ────────────────────────────────────────────────────────────

CONSENSUS_THRESHOLD = 0.15  # 加权强度超过此值 → 共识
CONFLICT_THRESHOLD = 0.06   # 正负双方都超过此值 → 冲突


def validate_signals(
    signals: list[DivinationSignal],
    weights: dict[str, float] | None = None,
    method_entries: list[dict[str, Any]] | None = None,
) -> ValidationResult:
    """VAL-001: 输入 signals + weights，输出 ValidationResult。

    Args:
        signals: 所有术法的统一信号列表 (strength 0-1, confidence 0-1)
        weights: {method_name: weight, ...} — 术法权重字典
        method_entries: [{method, label, tier}, ...] — 可选 tier 信息
    """
    if not signals:
        return ValidationResult(
            overall_score=50,
            confidence=30,
            confidence_level="low",
            risks=["未产生有效信号，建议提供更详细的信息后重试"],
        )

    # 构建默认权重
    if weights is None:
        methods = list(set(s.method for s in signals))
        w = 1.0 / max(1, len(methods))
        weights = {m: w for m in methods}

    # VAL-002: 按 signal_key 分组
    key_groups: dict[str, list[DivinationSignal]] = _group_by_signal_key(signals)

    # VAL-003~005: 加权统计
    stats = _compute_weighted_stats(key_groups, weights)
    # stats: {signal_key: {positive_weight, negative_weight, neutral_weight, ...}}

    # VAL-006: 共识检测
    consensus_items = _detect_consensus_by_weight(stats, weights, signals)

    # VAL-007~009: 冲突检测 (含 severity + resolution)
    conflict_items = _detect_conflicts_by_weight(stats, weights, signals)

    # VAL-010: 综合评分
    overall_score = _compute_overall_score(signals, weights, stats, consensus_items, conflict_items)

    # VAL-011: 置信等级
    confidence_num, confidence_level = _compute_confidence(signals, consensus_items, conflict_items)

    # VAL-012: 风险提取
    risks = _extract_risks(signals, stats, conflict_items)

    # VAL-013: 时间窗口
    timing = _extract_timing(signals)

    # VAL-014: 行动建议
    action_advice = _extract_action_advice(signals, consensus_items, conflict_items)

    return ValidationResult(
        consensus=consensus_items,
        conflicts=conflict_items,
        overall_score=round(overall_score, 1),
        confidence=round(confidence_num, 1),
        confidence_level=confidence_level,
        risks=risks,
        timing=timing,
        action_advice=action_advice,
    )


# ── VAL-002: 按 signal_key 分组 ───────────────────────────────────────────────

def _group_by_signal_key(signals: list[DivinationSignal]) -> dict[str, list[DivinationSignal]]:
    """将信号按 signal_key 归并。"""
    groups: dict[str, list[DivinationSignal]] = defaultdict(list)
    for s in signals:
        groups[s.signal_key].append(s)
    return dict(groups)


# ── VAL-003~005: 加权统计 ─────────────────────────────────────────────────────

def _compute_weighted_stats(
    key_groups: dict[str, list[DivinationSignal]],
    weights: dict[str, float],
) -> dict[str, dict[str, float]]:
    """计算每个 signal_key 的正向/负向/中性加权强度。

    Returns:
        {signal_key: {
            positive_weight: float,
            negative_weight: float,
            neutral_weight: float,
            total_weight: float,
            polarity: str,  # dominant polarity
            method_count: int,
        }}
    """
    stats: dict[str, dict[str, float]] = {}

    for key, sigs in key_groups.items():
        pos_w = 0.0
        neg_w = 0.0
        neu_w = 0.0
        methods = set()

        for s in sigs:
            w = weights.get(s.method, 0.05) * s.strength * s.confidence
            methods.add(s.method)
            if s.polarity == "positive":
                pos_w += w
            elif s.polarity == "negative":
                neg_w += w
            else:
                # neutral/mixed — split: half goes to statistical neutral
                neu_w += w

        total = pos_w + neg_w + neu_w

        # Determine dominant polarity
        if pos_w > neg_w and pos_w > neu_w:
            dominant = "positive"
        elif neg_w > pos_w and neg_w > neu_w:
            dominant = "negative"
        elif neu_w > 0:
            dominant = "neutral"
        else:
            dominant = "mixed"

        stats[key] = {
            "positive_weight": round(pos_w, 4),
            "negative_weight": round(neg_w, 4),
            "neutral_weight": round(neu_w, 4),
            "total_weight": round(total, 4),
            "polarity": dominant,
            "method_count": len(methods),
        }

    return stats


# ── VAL-006: 加权共识检测 ─────────────────────────────────────────────────────

def _detect_consensus_by_weight(
    stats: dict[str, dict[str, float]],
    weights: dict[str, float],
    signals: list[DivinationSignal],
) -> list[ConsensusItem]:
    """基于加权强度的共识检测。

    规则: 某 signal_key 的正向或负向加权强度超过 CONSENSUS_THRESHOLD。
    """
    consensus: list[ConsensusItem] = []

    # Also group by domain for cross-method check
    domain_sigs: dict[str, list[DivinationSignal]] = defaultdict(list)
    for s in signals:
        domain_sigs[s.domain].append(s)

    for key, st in stats.items():
        if st["total_weight"] < 0.05:
            continue

        pos_w = st["positive_weight"]
        neg_w = st["negative_weight"]

        # Find which methods contributed
        related = [s for s in signals if s.signal_key == key]

        if pos_w >= CONSENSUS_THRESHOLD and st["method_count"] >= 2:
            methods = sorted(set(s.method for s in related if s.polarity == "positive"))
            domain = related[0].domain if related else "self_life"
            consensus.append(ConsensusItem(
                domain=domain,
                theme=_consensus_theme(key, "positive"),
                supporting_methods=methods,
                weight_strength=round(min(95, 40 + pos_w * 25), 1),
                explanation=_consensus_explanation(key, "positive", methods, pos_w),
            ))

        if neg_w >= CONSENSUS_THRESHOLD and st["method_count"] >= 2:
            methods = sorted(set(s.method for s in related if s.polarity == "negative"))
            domain = related[0].domain if related else "self_life"
            consensus.append(ConsensusItem(
                domain=domain,
                theme=_consensus_theme(key, "negative"),
                supporting_methods=methods,
                weight_strength=round(min(90, 40 + neg_w * 20), 1),
                explanation=_consensus_explanation(key, "negative", methods, neg_w),
            ))

    # Cross-domain consensus
    if len(consensus) >= 3:
        all_supporting = set()
        for c in consensus:
            all_supporting.update(c.supporting_methods)
        consensus.append(ConsensusItem(
            domain="overall",
            theme="多领域一致趋势",
            supporting_methods=sorted(all_supporting)[:8],
            weight_strength=min(90, 50 + len(consensus) * 5),
            explanation=f"在{len(consensus)}个信号维度均观察到一致趋势，综合分析可信度较高",
        ))

    return consensus


def _consensus_theme(key: str, polarity: str) -> str:
    """根据 key 和极性生成主题。"""
    themes: dict[str, dict[str, str]] = {
        "career_independence":   {"positive": "事业独立性强", "negative": "事业独立性不足"},
        "career_stability":      {"positive": "事业稳定向好", "negative": "事业稳定性存疑"},
        "career_pressure":       {"positive": "事业压力可控", "negative": "事业压力偏大"},
        "wealth_growth":         {"positive": "财富增长可期", "negative": "财富增长乏力"},
        "wealth_risk":           {"positive": "财务风险较低", "negative": "财务风险需关注"},
        "wealth_stability":      {"positive": "财富基础稳固", "negative": "财富基础待夯实"},
        "relationship_attraction": {"positive": "感情吸引力强", "negative": "感情吸引力减弱"},
        "relationship_conflict": {"positive": "感情冲突缓和", "negative": "感情存在矛盾"},
        "marriage_stability":    {"positive": "婚姻基础稳固", "negative": "婚姻需多经营"},
        "decision_support":      {"positive": "决策方向有利", "negative": "当前不宜轻举妄动"},
        "decision_delay":        {"positive": "宜暂缓决策", "negative": "决策窗口收窄"},
        "decision_risk":         {"positive": "决策风险可控", "negative": "决策风险较高"},
        "timing_opportunity":    {"positive": "时机较为有利", "negative": "时机尚不成熟"},
        "timing_obstacle":       {"positive": "障碍可克服", "negative": "时机存在阻力"},
        "timing_transition":     {"positive": "正处于有利转折", "negative": "转折期需谨慎"},
        "health_pressure":       {"positive": "压力可控", "negative": "健康压力偏大"},
        "emotional_pressure":    {"positive": "情绪状态平稳", "negative": "情绪压力需关注"},
        "rest_recovery":         {"positive": "恢复力良好", "negative": "需加强休养"},
        "noble_help":            {"positive": "有贵人相助", "negative": "贵人助力不足"},
        "obstacle_pressure":     {"positive": "阻力较小", "negative": "阻力较大"},
        "mobility_change":       {"positive": "变动时机成熟", "negative": "变动需三思"},
        "relocation_signal":     {"positive": "迁移条件有利", "negative": "当前不宜搬迁"},
        "environment_support":   {"positive": "环境格局有利", "negative": "环境格局需调整"},
        "direction_benefit":     {"positive": "朝向有利", "negative": "朝向存在不利"},
        "layout_risk":           {"positive": "布局风险可控", "negative": "布局存在隐患"},
        "long_term_potential":   {"positive": "长期潜力较大", "negative": "长期发展受限"},
        "short_term_caution":    {"positive": "短期风险较低", "negative": "短期需谨慎"},
        "general_reference":     {"positive": "整体趋势正面", "negative": "整体趋势偏谨慎"},
    }
    default = {"positive": f"{key}信号正面", "negative": f"{key}信号偏负面"}
    return themes.get(key, default).get(polarity, default[polarity])


def _consensus_explanation(key: str, polarity: str, methods: list[str], weight: float) -> str:
    """生成共识解释文本。"""
    m_str = "、".join(methods[:4])
    direction = "一致向好" if polarity == "positive" else "一致偏谨慎"
    return f"{len(methods)}种术法({m_str})在「{key}」上{direction}（加权强度 {weight:.2f}）"


# ── VAL-007~009: 加权冲突检测 ─────────────────────────────────────────────────

def _detect_conflicts_by_weight(
    stats: dict[str, dict[str, float]],
    weights: dict[str, float],
    signals: list[DivinationSignal],
) -> list[ConflictItem]:
    """基于加权强度的冲突检测。

    VAL-007: 正负双方权重都超过 CONFLICT_THRESHOLD → conflict
    VAL-008: severity = low/medium/high
    VAL-009: resolution 调和建议
    """
    conflicts: list[ConflictItem] = []

    for key, st in stats.items():
        pos_w = st["positive_weight"]
        neg_w = st["negative_weight"]

        # 需要双方都超过阈值
        if pos_w < CONFLICT_THRESHOLD or neg_w < CONFLICT_THRESHOLD:
            continue

        related = [s for s in signals if s.signal_key == key]
        pos_methods = sorted(set(s.method for s in related if s.polarity == "positive"))
        neg_methods = sorted(set(s.method for s in related if s.polarity == "negative"))
        neu_methods = sorted(set(s.method for s in related if s.polarity in ("neutral", "mixed")))
        domain = related[0].domain if related else "self_life"

        # VAL-008: severity
        gap = abs(pos_w - neg_w)
        total_conflict = pos_w + neg_w
        if total_conflict > 3.0:
            severity = "high"
        elif total_conflict > 1.5:
            severity = "medium"
        else:
            severity = "low"

        # VAL-009: resolution
        resolution = _generate_resolution(key, pos_w, neg_w, pos_methods, neg_methods, severity)

        conflicts.append(ConflictItem(
            domain=domain,
            severity=severity,
            positive_methods=pos_methods,
            negative_methods=neg_methods,
            neutral_methods=neu_methods,
            conflict_explanation=(
                f"「{key}」存在分歧：{', '.join(pos_methods)}给出正向信号(加权{pos_w:.2f})，"
                f"{', '.join(neg_methods)}给出负向信号(加权{neg_w:.2f})。"
                f"可能是不同术法关注不同时间维度或分析角度所致。"
            ),
            resolution=resolution,
        ))

    return conflicts


def _generate_resolution(
    key: str,
    pos_w: float,
    neg_w: float,
    pos_methods: list[str],
    neg_methods: list[str],
    severity: str,
) -> str:
    """VAL-009: 生成冲突调和建议。"""
    pos_methods_str = "、".join(pos_methods[:3])
    neg_methods_str = "、".join(neg_methods[:3])

    templates = {
        "career_independence": f"建议在{pos_methods_str}提示的方向上主动作为，同时关注{neg_methods_str}提醒的风险点",
        "career_stability": f"长期来看{pos_methods_str}暗示事业有支撑，但短期内{neg_methods_str}提示的不确定性需关注",
        "wealth_growth": f"财富增值建议结合{pos_methods_str}的积极判断，同时审慎对待{neg_methods_str}提示的风险",
        "decision_support": f"决策宜听取{pos_methods_str}的积极建议，但{neg_methods_str}的谨慎提示也需纳入考量",
        "timing_opportunity": f"时机选择上可参考{pos_methods_str}的有利窗口，但{neg_methods_str}建议等待的信号不应忽视",
        "long_term_potential": f"长期来看{pos_methods_str}支持发展潜力，短期{neg_methods_str}提示需做更充分准备",
    }

    if key in templates:
        return templates[key]

    # Generic resolution
    if severity == "high":
        return f"此维度分歧较大，建议结合{pos_methods_str}与{neg_methods_str}两方视角，优先考虑风险较低的路径"
    elif severity == "medium":
        return f"可在{pos_methods_str}支持的方向上推进，同时留意{neg_methods_str}提示的关注点"
    else:
        return f"分歧程度较轻，以{pos_methods_str}的积极面为参考，适当兼顾{neg_methods_str}的保守建议"


# ── VAL-010: 综合评分 ─────────────────────────────────────────────────────────

def _compute_overall_score(
    signals: list[DivinationSignal],
    weights: dict[str, float],
    stats: dict[str, dict[str, float]],
    consensus: list[ConsensusItem],
    conflicts: list[ConflictItem],
) -> float:
    """计算综合评分 0-100。

    正向加权强度多时分数上升；负向多时分数下降。
    """
    if not signals:
        return 50.0

    total_score = 0.0
    total_weight = 0.0

    for s in signals:
        w = weights.get(s.method, 0.05) * s.strength * s.confidence
        if s.polarity == "positive":
            score = 50.0 + s.strength * 50.0
        elif s.polarity == "negative":
            score = 50.0 - s.strength * 50.0
        elif s.polarity == "mixed":
            score = 50.0 + (s.strength * 20.0)  # slightly positive bias
        else:
            score = 50.0
        total_score += score * w
        total_weight += w

    base = total_score / max(0.01, total_weight)

    # Consensus bonus
    consensus_bonus = min(12, sum(c.weight_strength for c in consensus) * 0.08)

    # Conflict penalty (weighted by severity)
    sev_map = {"low": 3, "medium": 6, "high": 10}
    conflict_penalty = min(20, sum(sev_map.get(c.severity, 5) for c in conflicts))

    # Method diversity bonus
    methods_used = len(set(s.method for s in signals))
    method_bonus = min(8, methods_used * 0.6)

    return min(95, max(5, base + consensus_bonus - conflict_penalty + method_bonus))


# ── VAL-011: 置信度计算 ────────────────────────────────────────────────────────

def _compute_confidence(
    signals: list[DivinationSignal],
    consensus: list[ConsensusItem],
    conflicts: list[ConflictItem],
) -> tuple[float, str]:
    """计算置信度数值和等级。

    VAL-011: 共识多、冲突少时 confidence 更高。
    Returns (confidence_numeric, confidence_level)
    """
    if not signals:
        return 30.0, "low"

    # Average per-signal confidence
    avg_signal_conf = sum(s.confidence for s in signals) / len(signals) * 100

    methods_count = len(set(s.method for s in signals))

    # Consensus bonus
    consensus_bonus = min(15, len(consensus) * 3.5)

    # Conflict penalty
    sev_map = {"low": 3, "medium": 7, "high": 12}
    conflict_penalty = min(25, sum(sev_map.get(c.severity, 5) for c in conflicts))

    # Method count bonus
    method_bonus = min(8, methods_count * 0.6)

    score = round(min(92, max(10, avg_signal_conf + consensus_bonus - conflict_penalty + method_bonus)), 1)

    # Map to level
    if score >= 75:
        level = "high"
    elif score >= 60:
        level = "medium_high"
    elif score >= 40:
        level = "medium"
    else:
        level = "low"

    return score, level


# ── VAL-012: 风险提取 ─────────────────────────────────────────────────────────

def _extract_risks(
    signals: list[DivinationSignal],
    stats: dict[str, dict[str, float]],
    conflicts: list[ConflictItem],
) -> list[str]:
    """VAL-012: 从 negative/mixed 信号和冲突中提取风险列表。

    使用谨慎表达，禁止绝对化语言。
    """
    risks: list[str] = []

    # Strong negative signals (strength > 0.6)
    strong_neg = [s for s in signals if s.polarity == "negative" and s.strength > 0.6]
    if strong_neg:
        # Group by signal_key
        neg_keys: dict[str, list[DivinationSignal]] = defaultdict(list)
        for s in strong_neg:
            neg_keys[s.signal_key].append(s)
        for key, sigs in neg_keys.items():
            methods = sorted(set(s.method for s in sigs))
            avg_str = sum(s.strength for s in sigs) / len(sigs)
            if avg_str > 0.75:
                risks.append(f"「{key}」维度在{len(methods)}种术法({', '.join(methods[:3])})中提示较强风险，建议重点关注")
            else:
                risks.append(f"「{key}」维度存在一定不确定性，建议结合实际情况参考")

    # Mixed signals with high strength
    strong_mixed = [s for s in signals if s.polarity == "mixed" and s.strength > 0.5]
    if strong_mixed:
        for s in strong_mixed[:3]:
            risks.append(f"「{s.signal_key}」({s.method})呈现混合信号，建议全面评估后再做决策")

    # High severity conflicts
    for c in conflicts:
        if c.severity == "high":
            risks.append(f"⚠ 高分歧: {c.domain}领域存在显著术法间矛盾，相关结论仅作参考")
        elif c.severity == "medium":
            risks.append(f"⚡ 中度分歧: {c.domain}领域结论需结合多方视角")

    # Low signal coverage
    methods_used = set(s.method for s in signals)
    if len(methods_used) < 6:
        risks.append(f"目前仅{len(methods_used)}种术法产生有效信号（共12法），建议补充出生信息以获得更完整分析")

    return risks


# ── VAL-013: 时间窗口提取 ─────────────────────────────────────────────────────

def _extract_timing(signals: list[DivinationSignal]) -> dict[str, Any] | None:
    """VAL-013: 从 time_scope 和 timing 信号中提取时间窗口信息。"""
    # Direct timing domain signals
    timing_signals = [s for s in signals if s.domain == "timing"]
    # Signals with time_scope field
    scoped_signals = [s for s in signals if s.time_scope]

    if not timing_signals and not scoped_signals:
        return None

    result: dict[str, Any] = {}

    # Time scope distribution
    short = [s for s in scoped_signals if s.time_scope == "short_term"]
    medium = [s for s in scoped_signals if s.time_scope == "medium_term"]
    long = [s for s in scoped_signals if s.time_scope == "long_term"]

    result["short_term_signals"] = len(short)
    result["medium_term_signals"] = len(medium)
    result["long_term_signals"] = len(long)

    # Timing domain analysis
    pos_timing = [s for s in timing_signals if s.polarity == "positive"]
    neg_timing = [s for s in timing_signals if s.polarity == "negative"]

    result["timing_signals_count"] = len(timing_signals)
    result["favorable_count"] = len(pos_timing)
    result["unfavorable_count"] = len(neg_timing)

    # Generate summary
    if len(pos_timing) > len(neg_timing):
        result["summary"] = f"共{len(timing_signals)}条时机信号，以有利为主；短期信号{len(short)}条，中期{len(medium)}条，长期{len(long)}条"
    elif len(neg_timing) > len(pos_timing):
        result["summary"] = f"共{len(timing_signals)}条时机信号，以不利为主，建议耐心等待更佳时机"
    elif long:
        result["summary"] = f"长期趋势信号较多({len(long)}条)，建议拉长时间视角做判断"
    else:
        result["summary"] = f"共{len(timing_signals)}条时机信号，时机信号中性"

    return result


# ── VAL-014: 行动建议提取 ─────────────────────────────────────────────────────

def _extract_action_advice(
    signals: list[DivinationSignal],
    consensus: list[ConsensusItem],
    conflicts: list[ConflictItem],
) -> list[str]:
    """VAL-014: 从 advice 字段 + consensus/conflicts 生成可执行建议。

    输出可执行建议，不做强制命令（使用"建议/可以/可考虑"等）。
    """
    advice: list[str] = []

    # Extract advice from signals
    for s in signals:
        if s.advice and s.advice not in advice:
            advice.append(s.advice)

    # From consensus
    for c in consensus[:4]:
        if c.weight_strength > 55:
            if "有利" in c.theme or "较强" in c.theme or "向好" in c.theme:
                advice.append(f"可积极关注{c.domain}领域的机会，{c.supporting_methods[0]}等术法一致看好")
            elif "压力" in c.theme or "不足" in c.theme or "谨慎" in c.theme:
                advice.append(f"建议在{c.domain}领域多做准备，{', '.join(c.supporting_methods[:2])}等术法提示需关注")

    # From conflicts
    for c in conflicts:
        if c.resolution:
            advice.append(c.resolution)

    # Deduplicate
    seen = set()
    unique = []
    for a in advice:
        if a not in seen:
            seen.add(a)
            unique.append(a)

    if not unique:
        unique.append("建议结合多个术法的交叉验证结果，全面评估后再做决策")

    # Add standard disclaimer advice
    unique.append("以上建议基于传统文化视角，重大决策请咨询相关专业人士")

    return unique[:8]  # cap at 8


# ── 向后兼容 wrapper ──────────────────────────────────────────────────────────

def validate(
    signals: list[DivinationSignal],
    intent: dict[str, Any],
    method_entries: list[dict[str, Any]] | None = None,
) -> ValidationResult:
    """向后兼容的 validate() 包装。

    新代码请直接使用 validate_signals(signals, weights)。
    """
    from .weights import get_weight_for_method

    weights: dict[str, float] = {}
    for s in signals:
        if s.method not in weights:
            weights[s.method] = get_weight_for_method(s.method, "", method_entries or [])

    return validate_signals(signals, weights, method_entries)
