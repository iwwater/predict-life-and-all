"""报告生成器 — 根据信号和验证结果生成三档报告。

REP-001: synthesize_report() 返回 ReadingReport
REP-002: 一句话结论 (headline) — free 报告第一段
REP-003: 免费版 — headline + 评分 + 3条建议
REP-004: 标准版 — 共识/冲突/风险/建议/12法摘要
REP-005: 高级版 — 深度分析/时间窗口/风险拆解/追问上下文
REP-006: 12法依据摘要 — 每个术法至少一条
REP-007: 多法共识段落 — 根据 consensus 自动生成
REP-008: 多法冲突段落 — 根据 conflicts 自动生成
REP-009: 风险提醒 — 谨慎表达，禁止绝对化
REP-010: 行动建议 — 可执行，不做强制命令
REP-011: 免责声明 — 三档报告都必须包含
"""
from __future__ import annotations

from typing import Any

from .schema import (
    ConflictItem,
    ConsensusItem,
    DivinationSignal,
    ReadingReport,
    ValidationResult,
)


# ── 免责声明 (M0-04, REP-011) ─────────────────────────────────────────────────

DISCLAIMER = (
    "【免责声明】以上内容为基于传统文化与符号象征视角的参考分析，仅供参考，"
    "不构成医疗诊断、法律建议或投资指导。命理分析具有文化传承价值，"
    "但不应替代专业意见。重大人生决策请结合现实情况，咨询相关专业人士。"
)


def synthesize_report(
    signals: list[DivinationSignal],
    validation: ValidationResult,
    intent: dict[str, Any],
    methods_used: list[str],
    depth: str = "standard",
) -> ReadingReport:
    """REP-001: 返回 ReadingReport（三档报告）。

    Args:
        signals: 所有统一信号
        validation: 交叉验证结果 (ValidationResult)
        intent: 意图分类结果
        methods_used: 使用的术法名称列表
        depth: 报告深度 (free/standard/premium)
    """
    primary_domain = intent.get("goal", intent.get("primary_domain", "self_life"))
    primary_label = intent.get("goal_label", intent.get("primary_label", "综合"))
    question = intent.get("question", "")

    # Pre-compute reusable structures
    domain_signals: dict[str, list[DivinationSignal]] = {}
    for s in signals:
        domain_signals.setdefault(s.domain, []).append(s)

    method_signals: dict[str, list[DivinationSignal]] = {}
    for s in signals:
        method_signals.setdefault(s.method, []).append(s)

    # Generate headline (REP-002)
    headline = _generate_headline(signals, validation, primary_label, question)

    # REP-003: Free report
    free_report = _build_free(headline, validation, signals, methods_used)

    # REP-004: Standard report
    standard_report = _build_standard(
        headline, domain_signals, method_signals, validation, intent, methods_used
    )

    # REP-005: Premium report
    premium_report = _build_premium(
        headline, domain_signals, method_signals, validation, intent, methods_used, standard_report
    )

    return ReadingReport(free=free_report, standard=standard_report, premium=premium_report)


# ── REP-002: 一句话结论 ───────────────────────────────────────────────────────

def _generate_headline(
    signals: list[DivinationSignal],
    validation: ValidationResult,
    primary_label: str,
    question: str = "",
) -> str:
    """REP-002: 生成一句话结论 — free 报告第一段。"""
    score = validation.overall_score
    pos_count = sum(1 for s in signals if s.polarity == "positive")
    neg_count = sum(1 for s in signals if s.polarity == "negative")
    conf_level = validation.confidence_level

    if score >= 70:
        tone = "整体趋势较为积极"
    elif score >= 55:
        tone = "整体处于平稳发展态势"
    elif score >= 40:
        tone = "需要关注一些潜在挑战"
    else:
        tone = "建议谨慎对待，多做准备"

    methods_n = len(set(s.method for s in signals))

    context = f"针对「{question}」的" if question else ""
    return (
        f"基于{methods_n}种术法交叉验证的综合分析，{context}{tone}。"
        f"正向信号{pos_count}条，负向信号{neg_count}条，"
        f"综合评分{score}/100，置信度{conf_level}。"
    )


# ── REP-003: 免费版报告 ───────────────────────────────────────────────────────

def _build_free(
    headline: str,
    validation: ValidationResult,
    signals: list[DivinationSignal],
    methods_used: list[str],
) -> str:
    """REP-003: 免费版 — headline + 评分 + 最多3条建议。"""
    lines: list[str] = []

    # Headline
    lines.append("## 命理综合分析 · 速览")
    lines.append(f"> {headline}")
    lines.append("")

    # Score bar
    score = validation.overall_score
    bar_len = 20
    filled = int(score / 100 * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)
    lines.append(f"**综合评分**: {score}/100 `{bar}`")
    lines.append(f"**可信等级**: {validation.confidence_level}")
    lines.append("")

    # Top consensus
    if validation.consensus:
        top = validation.consensus[0]
        lines.append(f"**核心共识**: {top.theme}")
        if validation.consensus[1:]:
            lines.append(f"另{len(validation.consensus)-1}项共识可查看标准报告")
    lines.append("")

    # Top 3 suggestions
    suggestions = validation.action_advice[:3] if validation.action_advice else ["建议查看标准报告获取详细分析"]
    lines.append("### 核心建议")
    for i, a in enumerate(suggestions, 1):
        lines.append(f"{i}. {a}")
    lines.append("")

    # Disclaimer
    lines.append("---")
    lines.append(DISCLAIMER)

    # Enforce ≤500 chars guideline
    result = "\n".join(lines)
    if len(result) > 600:
        # Truncate suggestions to fit
        result = "\n".join(lines[:8]) + "\n\n---\n" + DISCLAIMER

    return result


# ── REP-004: 标准版报告 ───────────────────────────────────────────────────────

def _build_standard(
    headline: str,
    domain_signals: dict[str, list[DivinationSignal]],
    method_signals: dict[str, list[DivinationSignal]],
    validation: ValidationResult,
    intent: dict[str, Any],
    methods_used: list[str],
) -> str:
    """REP-004: 标准版 — 共识/冲突/风险/建议/12法摘要。"""
    lines: list[str] = []

    primary_domain = intent.get("goal", intent.get("primary_domain", "self_life"))
    primary_label = intent.get("goal_label", intent.get("primary_label", "综合"))
    sub_goals = intent.get("sub_goals", intent.get("sub_domains", [primary_domain]))

    # ── Header ──
    lines.append("# 命理综合分析报告 (标准版)")
    lines.append(f"> {headline}")
    lines.append("")
    lines.append(f"**分析领域**: {primary_label}")
    lines.append(f"**参与术法**: {' · '.join(methods_used)}")
    lines.append(f"**综合评分**: {validation.overall_score}/100 | **可信等级**: {validation.confidence_level}")
    lines.append("")

    # ── Intent analysis ──
    lines.append("## 意图分析")
    lines.append(f"- 用户问题领域: {primary_label}")
    lines.append(f"- 关联子领域: {', '.join(sub_goals[:5])}")
    lines.append(f"- 分类置信度: {intent.get('goal_confidence', intent.get('confidence', 0.5)):.0%}")
    lines.append("")

    # ── REP-007: 多法共识段落 ──
    if validation.consensus:
        lines.append("## 多术法共识")
        for c in validation.consensus:
            methods_str = "、".join(c.supporting_methods[:5])
            if len(c.supporting_methods) > 5:
                methods_str += f"等{len(c.supporting_methods)}法"
            lines.append(f"### {c.theme}")
            lines.append(f"- **支持术法**: {methods_str}")
            lines.append(f"- **共识强度**: {c.weight_strength}/100")
            lines.append(f"- **解读**: {c.explanation}")
            lines.append("")
    else:
        lines.append("## 多术法共识")
        lines.append("本次分析未形成显著的多术法共识，各术法信号较为分散，建议提供更详细的出生信息以获得更聚焦的分析。")
        lines.append("")

    # ── REP-008: 多法冲突段落 ──
    if validation.conflicts:
        lines.append("## 术法分歧（需关注）")
        for c in validation.conflicts:
            sev_icon = {"low": "🟡", "medium": "🟠", "high": "🔴"}.get(c.severity, "⚪")
            lines.append(f"### {sev_icon} {c.domain} · 严重度: {c.severity}")
            lines.append(f"- **正向术法**: {', '.join(c.positive_methods)}")
            lines.append(f"- **负向术法**: {', '.join(c.negative_methods)}")
            if c.neutral_methods:
                lines.append(f"- **中性术法**: {', '.join(c.neutral_methods)}")
            lines.append(f"- **原因分析**: {c.conflict_explanation}")
            if c.resolution:
                lines.append(f"- **调和思路**: {c.resolution}")
            lines.append("")

    # ── REP-006: 12法依据摘要 ──
    lines.append("## 12术法依据摘要")
    for method in methods_used:
        sigs = method_signals.get(method, [])
        if sigs:
            top_sig = max(sigs, key=lambda s: s.strength)
            emoji = {"positive": "✅", "negative": "⚠", "neutral": "➖", "mixed": "🔄"}.get(top_sig.polarity, "➖")
            lines.append(f"- {emoji} **{method}**: {top_sig.signal_key} ({top_sig.polarity}, 强度{top_sig.strength:.0%}) — {top_sig.evidence or '无详细证据'}")
        else:
            lines.append(f"- ⬜ **{method}**: 未产生有效信号（可能因出生信息不完整）")
    lines.append("")

    # ── REP-009: 风险提醒 ──
    if validation.risks:
        lines.append("## 风险提醒")
        for r in validation.risks:
            lines.append(f"- {r}")
        lines.append("")
        lines.append("*以上风险提示基于术法信号的统计分析，仅供参考，不构成确定性判断。*")
        lines.append("")

    # ── REP-010: 行动建议 ──
    if validation.action_advice:
        lines.append("## 行动建议")
        for i, a in enumerate(validation.action_advice, 1):
            lines.append(f"{i}. {a}")
        lines.append("")

    # ── Timing ──
    if validation.timing:
        lines.append("## 时间窗口")
        lines.append(f"- {validation.timing.get('summary', '')}")
        lines.append("")

    # ── Domain breakdown ──
    lines.append("## 分领域信号详情")
    domain_names = {
        "self_life": "本命格局", "career": "事业工作", "wealth": "财运",
        "relationship": "感情关系", "health": "健康自省", "decision": "决策方向",
        "timing": "时机分析", "home_fengshui": "住宅风水",
    }
    for domain, name in domain_names.items():
        sigs = domain_signals.get(domain, [])
        if not sigs:
            continue
        lines.append(f"### {name}")
        for s in sigs[:4]:
            emoji = {"positive": "✅", "negative": "❌", "neutral": "➖", "mixed": "🔄"}.get(s.polarity, "➖")
            lines.append(f"- {emoji} **{s.signal_key}** ({s.method}): 强度{s.strength:.0%} | {s.evidence}")
        lines.append("")

    # ── Disclaimer ──
    lines.append("---")
    lines.append(DISCLAIMER)

    return "\n".join(lines)


# ── REP-005: 高级版报告 ───────────────────────────────────────────────────────

def _build_premium(
    headline: str,
    domain_signals: dict[str, list[DivinationSignal]],
    method_signals: dict[str, list[DivinationSignal]],
    validation: ValidationResult,
    intent: dict[str, Any],
    methods_used: list[str],
    standard_text: str,
) -> str:
    """REP-005: 高级版 — 深度分析/时间窗口/风险拆解/追问上下文。"""
    lines: list[str] = []

    lines.append("# 命理深度分析报告 (Premium)")
    lines.append(f"> {headline}")
    lines.append("")
    lines.append(f"**综合评分**: {validation.overall_score}/100 | **可信等级**: {validation.confidence_level}")
    lines.append(f"**术法覆盖**: {len(methods_used)}/12 法")
    lines.append("")

    # ── Signal heatmap ──
    lines.append("## 信号强度热力图")
    domain_heat: dict[str, dict[str, float]] = {}
    for signals in domain_signals.values():
        for s in signals:
            domain_heat.setdefault(s.domain, {"pos": 0.0, "neg": 0.0, "neu": 0.0, "count": 0.0})
            h = domain_heat[s.domain]
            h["count"] += 1
            if s.polarity == "positive":
                h["pos"] += s.strength
            elif s.polarity == "negative":
                h["neg"] += s.strength
            else:
                h["neu"] += s.strength

    for domain, h in sorted(domain_heat.items(), key=lambda x: -x[1]["count"]):
        total = max(1, h["pos"] + h["neg"] + h["neu"])
        p_pos = int(h["pos"] / total * 20)
        p_neg = int(h["neg"] / total * 20)
        p_neu = int(h["neu"] / total * 20)
        bar = "🟢" * p_pos + "🔴" * p_neg + "⚪" * p_neu
        lines.append(f"- **{domain}** ({int(h['count'])}条): {bar}")

    lines.append("")

    # ── Method contribution ──
    lines.append("## 各术法贡献度排名")
    ranked = sorted(method_signals.items(), key=lambda x: -sum(s.strength for s in x[1]))
    for method, sigs in ranked:
        total_str = sum(s.strength for s in sigs)
        avg_str = total_str / max(1, len(sigs))
        trends = set(s.polarity for s in sigs)
        trend_str = "/".join(sorted(trends))
        lines.append(f"- **{method}**: {len(sigs)}条信号 | 强度均值{avg_str:.0%} | 倾向{trend_str}")
    lines.append("")

    # ── Risk breakdown (REP-009 enhanced) ──
    if validation.risks:
        lines.append("## 风险深度拆解")
        # Group risks by severity
        high_risk = [c for c in validation.conflicts if c.severity == "high"]
        med_risk = [c for c in validation.conflicts if c.severity == "medium"]

        if high_risk:
            lines.append("### 🔴 高风险维度")
            for c in high_risk:
                lines.append(f"- **{c.domain}**: {c.conflict_explanation}")
                if c.resolution:
                    lines.append(f"  → 调和思路: {c.resolution}")
            lines.append("")

        if med_risk:
            lines.append("### 🟠 中度风险维度")
            for c in med_risk:
                lines.append(f"- **{c.domain}**: {c.conflict_explanation}")
            lines.append("")

        lines.append("### 风险提示清单")
        for r in validation.risks:
            lines.append(f"- {r}")
        lines.append("")

    # ── Time window analysis ──
    if validation.timing:
        lines.append("## 时间窗口分析")
        t = validation.timing
        short_n = t.get("short_term_signals", 0)
        med_n = t.get("medium_term_signals", 0)
        long_n = t.get("long_term_signals", 0)
        lines.append(f"- 短期信号: {short_n}条")
        lines.append(f"- 中期信号: {med_n}条")
        lines.append(f"- 长期信号: {long_n}条")
        lines.append(f"- **综合**: {t.get('summary', '')}")
        lines.append("")

        # Temporal recommendation
        if short_n > long_n:
            lines.append("> 信号以短期为主，建议关注近期 1-3 个月内的变化，及时调整策略。")
        elif long_n > short_n:
            lines.append("> 信号以长期为主，建议从长远视角规划，不必过于纠结短期波动。")
        lines.append("")

    # ── Follow-up context ──
    lines.append("## 追问上下文")
    lines.append("以下为系统根据当前分析自动生成的追问方向，可帮助进一步聚焦：")
    lines.append("")

    # Generate follow-up from weak signals
    weak_signals = [s for s in method_signals.values() for s in s if s.strength < 0.35]
    if weak_signals:
        weak_keys = list(set(s.signal_key for s in weak_signals))[:3]
        for wk in weak_keys:
            lines.append(f"- 关于「{wk}」的信号较弱，可以提供更详细的出生时间或具体问题进行深入分析")

    if validation.conflicts:
        conflict_domains = list(set(c.domain for c in validation.conflicts))[:2]
        lines.append(f"- 存在术法分歧的领域（{', '.join(conflict_domains)}），可针对具体决策场景追问细节")

    if len(methods_used) < 12:
        lines.append("- 部分术法未参与分析，补充完整的出生信息可激活更多术法")

    lines.append("")

    # ── Full standard report embedded ──
    lines.append("## 详细分析报告")
    lines.append(standard_text)

    # ── Footer ──
    lines.append("")
    lines.append("---")
    lines.append("*本深度报告由 Mystic Hub 12术法聚合引擎生成，如需进一步解读可针对具体领域追问。*")

    return "\n".join(lines)


# ── 向后兼容 ─────────────────────────────────────────────────────────────────

def generate(
    signals: list[DivinationSignal],
    validation: ValidationResult,
    intent: dict[str, Any],
    methods_used: list[str],
    depth: str = "standard",
) -> ReadingReport:
    """向后兼容的 generate() 包装。

    新代码请直接使用 synthesize_report()。
    """
    return synthesize_report(signals, validation, intent, methods_used, depth)
