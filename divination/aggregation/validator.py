"""交叉验证引擎 — 对 12 术法的统一信号进行交叉验证。

BE-007: 交叉验证文件
基于现有 cross_validator.py 的设计理念，扩展到全 12 法。

核心逻辑：
  1. 按领域分组所有信号
  2. 检测共识 (≥3 术法独立指向同一结论)
  3. 检测冲突 (≥2 术法给出相反极性)
  4. 计算综合置信度
  5. 生成风险提示和行动建议
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
from .weights import get_weight


def validate(
    signals: list[DivinationSignal],
    intent: dict[str, Any],
    method_entries: list[dict[str, Any]] | None = None,
) -> ValidationResult:
    """对所有信号进行交叉验证。

    Args:
        signals: 所有术法的统一信号列表
        intent: 意图分类结果

    Returns:
        ValidationResult
    """
    if not signals:
        return ValidationResult(
            overall_score=50,
            confidence=30,
            risks=["未产生有效信号，建议提供更详细的信息后重试"],
        )

    primary_domain = intent.get("primary_domain", "self_life")
    sub_domains = intent.get("sub_domains", [primary_domain])

    # Step 1: 按领域分组信号
    domain_signals: dict[str, list[DivinationSignal]] = defaultdict(list)
    for s in signals:
        domain_signals[s.domain].append(s)

    # Step 2: 检测共识
    consensus_items = _detect_consensus(domain_signals, primary_domain)

    # Step 3: 检测冲突
    conflict_items = _detect_conflicts(domain_signals)

    # Step 4: 计算综合评分（传入 tier 信息）
    overall_score = _compute_overall_score(domain_signals, consensus_items, conflict_items, primary_domain, method_entries)

    # Step 5: 计算置信度
    confidence = _compute_confidence(signals, consensus_items, conflict_items)

    # Step 6: 生成风险提示
    risks = _identify_risks(signals, conflict_items)

    # Step 7: 时机分析
    timing = _analyze_timing(signals)

    # Step 8: 行动建议
    action_advice = _generate_action_advice(consensus_items, conflict_items, primary_domain)

    return ValidationResult(
        consensus=consensus_items,
        conflicts=conflict_items,
        overall_score=round(overall_score, 1),
        confidence=round(confidence, 1),
        risks=risks,
        timing=timing,
        action_advice=action_advice,
    )


# ── 辅助函数 ─────────────────────────────────────────────────────────────────

def _build_tier_multiplier(method_entries: list[dict[str, Any]] | None) -> dict[str, float]:
    """从 method_entries 构建 tier 权重。

    primary: 1.5, secondary: 1.0, reference: 0.6
    """
    if not method_entries:
        return {}
    return {
        e["method"]: {"primary": 1.5, "secondary": 1.0, "reference": 0.6}.get(e.get("tier", "secondary"), 1.0)
        for e in method_entries
    }


# ── 共识检测 ─────────────────────────────────────────────────────────────────

def _detect_consensus(
    domain_signals: dict[str, list[DivinationSignal]],
    primary_domain: str,
) -> list[ConsensusItem]:
    """检测多术法共识。

    规则: ≥3 个不同术法在同一领域给出相同极性的信号 → 共识。
    """
    consensus: list[ConsensusItem] = []

    for domain, signals in domain_signals.items():
        # 按极性分组
        pos_methods: set[str] = set()
        neg_methods: set[str] = set()
        neutral_methods: set[str] = set()

        for s in signals:
            if s.polarity == "positive":
                pos_methods.add(s.method)
            elif s.polarity == "negative":
                neg_methods.add(s.method)
            else:
                neutral_methods.add(s.method)

        # Positive consensus
        if len(pos_methods) >= 3:
            theme = _get_domain_theme(domain, "positive")
            cons = ConsensusItem(
                domain=domain,
                theme=theme,
                supporting_methods=sorted(pos_methods),
                weight_strength=min(95, 50 + len(pos_methods) * 10),
                explanation=f"{len(pos_methods)}种术法一致显示{theme}",
            )
            consensus.append(cons)

        # Negative consensus (only flag if relevant)
        if len(neg_methods) >= 3:
            theme = _get_domain_theme(domain, "negative")
            cons = ConsensusItem(
                domain=domain,
                theme=theme,
                supporting_methods=sorted(neg_methods),
                weight_strength=min(90, 50 + len(neg_methods) * 8),
                explanation=f"{len(neg_methods)}种术法一致显示{theme}，建议关注此领域",
            )
            consensus.append(cons)

    # 也检测跨领域共识
    if len(consensus) >= 3:
        all_supporting = set()
        for c in consensus:
            all_supporting.update(c.supporting_methods)
        consensus.append(ConsensusItem(
            domain="overall",
            theme="多领域一致趋势",
            supporting_methods=sorted(all_supporting)[:8],
            weight_strength=min(90, 60 + len(consensus) * 5),
            explanation=f"在{len(consensus)}个领域均观察到一致趋势，综合分析可信度较高",
        ))

    return consensus


def _get_domain_theme(domain: str, polarity: str) -> str:
    """根据领域和极性生成共识主题文本。"""
    themes = {
        "career": {"positive": "事业发展有利", "negative": "事业存在挑战"},
        "wealth": {"positive": "财运向好", "negative": "财运需谨慎"},
        "relationship": {"positive": "感情运较顺", "negative": "感情存在波折"},
        "health": {"positive": "健康状况良好", "negative": "需关注健康"},
        "self_life": {"positive": "命局格局较好", "negative": "命局存在不足"},
        "decision": {"positive": "决策方向有利", "negative": "当前不宜轻举妄动"},
        "timing": {"positive": "时机较为有利", "negative": "建议耐心等待"},
        "lost_item": {"positive": "找回希望较大", "negative": "找回难度较大"},
        "home_fengshui": {"positive": "风水格局较好", "negative": "风水存在不利因素"},
    }
    return themes.get(domain, {}).get(polarity, f"{domain}领域倾向{'正面' if polarity == 'positive' else '需关注'}")


# ── 冲突检测 ─────────────────────────────────────────────────────────────────

def _detect_conflicts(
    domain_signals: dict[str, list[DivinationSignal]],
) -> list[ConflictItem]:
    """检测多术法之间的冲突。

    规则: 同一领域内，≥2 术法正向且 ≥2 术法负向 → 冲突。
    """
    conflicts: list[ConflictItem] = []

    for domain, signals in domain_signals.items():
        pos = set()
        neg = set()
        neutral = set()

        for s in signals:
            if s.polarity == "positive":
                pos.add(s.method)
            elif s.polarity == "negative":
                neg.add(s.method)
            else:
                neutral.add(s.method)

        # 需要至少 2 v 2 才算真正的冲突
        if len(pos) >= 2 and len(neg) >= 2:
            conflicts.append(ConflictItem(
                domain=domain,
                positive_methods=sorted(pos),
                negative_methods=sorted(neg),
                neutral_methods=sorted(neutral),
                conflict_explanation=(
                    f"{domain}领域存在分歧：{', '.join(sorted(pos))}给出正向信号，"
                    f"{', '.join(sorted(neg))}给出负向信号。"
                    f"这可能是不同术法关注不同维度所致，建议结合现实情况判断。"
                ),
            ))

    return conflicts


# ── 综合评分 ─────────────────────────────────────────────────────────────────

def _compute_overall_score(
    domain_signals: dict[str, list[DivinationSignal]],
    consensus: list[ConsensusItem],
    conflicts: list[ConflictItem],
    primary_domain: str,
    method_entries: list[dict[str, Any]] | None = None,
) -> float:
    """计算综合评分 0-100。

    primary tier 权重 ×1.5, secondary ×1.0, reference ×0.6
    """
    if not domain_signals:
        return 50.0

    # tier 权重映射
    tier_multiplier = _build_tier_multiplier(method_entries)

    # 加权平均所有信号
    total_weight = 0.0
    weighted_score = 0.0

    for domain, signals in domain_signals.items():
        for s in signals:
            base_w = get_weight(s.method, domain)
            tier_mul = tier_multiplier.get(s.method, 1.0)
            w = base_w * tier_mul
            score = s.strength if s.polarity == "positive" else (
                100 - s.strength if s.polarity == "negative" else 50
            )
            weighted_score += score * w * s.confidence / 100
            total_weight += w

    base = weighted_score / max(1, total_weight)

    # 共识加分
    consensus_bonus = min(15, len(consensus) * 5)

    # 冲突扣分
    conflict_penalty = min(15, len(conflicts) * 5)

    # 方法数量加分
    methods_used = len(set(s.method for signals in domain_signals.values() for s in signals))
    method_bonus = min(10, methods_used * 0.8)

    return min(95, max(5, base + consensus_bonus - conflict_penalty + method_bonus))


def _compute_confidence(
    signals: list[DivinationSignal],
    consensus: list[ConsensusItem],
    conflicts: list[ConflictItem],
) -> float:
    """计算整体置信度。"""
    if not signals:
        return 30.0

    avg_confidence = sum(s.confidence for s in signals) / len(signals)
    methods_count = len(set(s.method for s in signals))

    consensus_bonus = min(15, len(consensus) * 4)
    conflict_penalty = min(20, len(conflicts) * 6)
    method_bonus = min(10, methods_count * 0.8)

    return round(min(90, max(10, avg_confidence + consensus_bonus - conflict_penalty + method_bonus)), 1)


def _identify_risks(
    signals: list[DivinationSignal],
    conflicts: list[ConflictItem],
) -> list[str]:
    """识别风险提示。"""
    risks: list[str] = []

    # 强负面信号
    strong_negatives = [
        s for s in signals
        if s.polarity == "negative" and s.strength > 70
    ]
    if strong_negatives:
        domains = set(s.domain for s in strong_negatives)
        for d in domains:
            risks.append(f"{d}领域存在较强负面信号，建议谨慎对待")

    # 冲突
    if conflicts:
        risks.append(f"发现{len(conflicts)}处术法间分歧({', '.join(c.domain for c in conflicts)})，相关结论仅供参考")

    # 方法覆盖率
    methods_used = set(s.method for s in signals)
    if len(methods_used) < 6:
        risks.append(f"仅{len(methods_used)}种术法产生有效信号(共12法)，部分术法因数据不足未参与分析")

    return risks


def _analyze_timing(signals: list[DivinationSignal]) -> dict[str, Any] | None:
    """分析时机相关信号。"""
    timing_signals = [s for s in signals if s.domain == "timing"]
    if not timing_signals:
        return None

    pos_timing = [s for s in timing_signals if s.polarity == "positive"]
    neg_timing = [s for s in timing_signals if s.polarity == "negative"]

    return {
        "timing_signals_count": len(timing_signals),
        "favorable_count": len(pos_timing),
        "unfavorable_count": len(neg_timing),
        "summary": (
            f"共{len(timing_signals)}条时机信号，其中{len(pos_timing)}条有利"
            if len(pos_timing) >= len(neg_timing)
            else f"共{len(timing_signals)}条时机信号，其中{len(neg_timing)}条不利，建议等待"
        ),
    }


def _generate_action_advice(
    consensus: list[ConsensusItem],
    conflicts: list[ConflictItem],
    primary_domain: str,
) -> list[str]:
    """生成行动建议。"""
    advice: list[str] = []

    # 基于共识的建议
    for c in consensus[:3]:
        if c.weight_strength > 60:
            if "有利" in c.theme or "较好" in c.theme:
                advice.append(f"可积极把握{c.domain}领域的机会")
            elif "挑战" in c.theme or "波折" in c.theme:
                advice.append(f"建议在{c.domain}领域保持谨慎，多做准备")

    # 通用建议
    if not advice:
        advice.append(f"建议重点关注{primary_domain}领域的发展")

    if conflicts:
        advice.append("存在术法间分歧的领域，建议综合现实情况做判断，不宜仅凭单一方面做重大决定")

    advice.append("以上为传统文化视角的参考，重大决策请咨询相关专业人士")

    return advice
