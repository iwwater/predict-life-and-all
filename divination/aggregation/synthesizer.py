"""报告生成器 — 根据信号和验证结果生成三档报告。

BE-008: 报告生成文件

三档报告:
  - free:   简短摘要 (≤500 字)
  - standard: 结构化分领域报告
  - premium: 深度分析 (扩展 standard + LLM 增强)
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


# ── 免责声明 ─────────────────────────────────────────────────────────────────
# M0-04: 每份报告都包含非医疗、非法律、非投资建议说明

DISCLAIMER = (
    "【免责声明】以上内容为基于传统文化与符号象征视角的参考分析，"
    "不构成医疗诊断、法律建议或投资指导。命理分析具有文化传承价值，"
    "但不应替代专业意见。重大人生决策请结合现实情况，咨询相关专业人士。"
)


def generate(
    signals: list[DivinationSignal],
    validation: ValidationResult,
    intent: dict[str, Any],
    methods_used: list[str],
    depth: str = "standard",
) -> ReadingReport:
    """生成三档报告。

    Args:
        signals: 所有统一信号
        validation: 交叉验证结果
        intent: 意图分类
        methods_used: 使用的术法列表
        depth: 报告深度 (free/standard/premium)

    Returns:
        ReadingReport
    """
    primary_domain = intent.get("goal", intent.get("primary_domain", "self_life"))
    primary_label = intent.get("goal_label", intent.get("primary_label", "综合"))
    confidence = intent.get("goal_confidence", intent.get("confidence", 0.5))

    # 按领域分组信号
    domain_signals: dict[str, list[DivinationSignal]] = {}
    for s in signals:
        domain_signals.setdefault(s.domain, []).append(s)

    free_report = _generate_free(signals, validation, primary_domain, primary_label, methods_used)
    standard_report = _generate_standard(
        domain_signals, validation, intent, methods_used, free_report
    )
    premium_report = _generate_premium(
        domain_signals, validation, intent, methods_used, standard_report
    )

    return ReadingReport(
        free=free_report,
        standard=standard_report,
        premium=premium_report,
    )


def _generate_free(
    signals: list[DivinationSignal],
    validation: ValidationResult,
    primary_domain: str,
    primary_label: str,
    methods_used: list[str],
) -> str:
    """生成简短摘要 (≤500 字)。"""
    lines: list[str] = []

    # 标题
    lines.append(f"## 综合命理分析 · 摘要")
    lines.append(f"*基于 {len(methods_used)} 种术法交叉验证*")
    lines.append("")

    # 整体评分
    score = validation.overall_score
    score_text = "较好" if score > 65 else "中等" if score > 45 else "需关注"
    lines.append(f"**综合评分**: {score}/100 ({score_text})")
    lines.append(f"**置信度**: {validation.confidence}/100")
    lines.append("")

    # 共识摘要
    if validation.consensus:
        lines.append("### 多术法共识")
        for c in validation.consensus[:3]:
            methods_str = "、".join(c.supporting_methods[:4])
            lines.append(f"- **{c.theme}** ({methods_str}等{c.domain})")
    lines.append("")

    # 主要发现
    lines.append("### 主要发现")
    pos_count = sum(1 for s in signals if s.polarity == "positive")
    neg_count = sum(1 for s in signals if s.polarity == "negative")
    neu_count = sum(1 for s in signals if s.polarity == "neutral")
    lines.append(f"- 正向信号: {pos_count}条")
    lines.append(f"- 负向信号: {neg_count}条")
    lines.append(f"- 中性信号: {neu_count}条")

    if validation.conflicts:
        lines.append(f"- ⚠️ 存在 {len(validation.conflicts)} 处术法间分歧，相关结论仅供参考")
    lines.append("")

    # 行动建议
    if validation.action_advice:
        lines.append("### 建议")
        for a in validation.action_advice[:2]:
            lines.append(f"- {a}")
    lines.append("")

    # 免责声明
    lines.append(DISCLAIMER)

    return "\n".join(lines)


def _generate_standard(
    domain_signals: dict[str, list[DivinationSignal]],
    validation: ValidationResult,
    intent: dict[str, Any],
    methods_used: list[str],
    free_text: str,
) -> str:
    """生成标准结构化报告。"""
    lines: list[str] = []

    primary_domain = intent.get("goal", intent.get("primary_domain", "self_life"))
    primary_label = intent.get("goal_label", intent.get("primary_label", "综合"))

    lines.append(f"# 综合命理分析报告")
    lines.append(f"**基于术法**: {'、'.join(methods_used)}")
    lines.append(f"**分析领域**: {primary_label}")
    lines.append(f"**综合评分**: {validation.overall_score}/100 | **置信度**: {validation.confidence}/100")
    lines.append("")

    # ── 意图分析 ──
    lines.append("## 意图分析")
    lines.append(f"- 主领域: {primary_label}")
    sub_goals = intent.get("sub_goals", intent.get("sub_domains", [primary_domain]))
    lines.append(f"- 子领域: {', '.join(sub_goals)}")
    lines.append(f"- 分类置信度: {intent.get('goal_confidence', intent.get('confidence', 0.5)):.0%}")
    lines.append("")

    # ── 术法共识 ──
    if validation.consensus:
        lines.append("## 多术法共识")
        for c in validation.consensus:
            methods_str = "、".join(c.supporting_methods[:5])
            lines.append(f"### {c.theme} ({c.domain})")
            lines.append(f"- 支持术法: {methods_str}")
            lines.append(f"- 共识强度: {c.weight_strength}/100")
            lines.append(f"- {c.explanation}")
            lines.append("")

    # ── 术法分歧 ──
    if validation.conflicts:
        lines.append("## 术法分歧（需关注）")
        for c in validation.conflicts:
            lines.append(f"### {c.domain} 领域")
            lines.append(f"- 正向术法: {', '.join(c.positive_methods)}")
            lines.append(f"- 负向术法: {', '.join(c.negative_methods)}")
            if c.neutral_methods:
                lines.append(f"- 中性术法: {', '.join(c.neutral_methods)}")
            lines.append(f"- 解释: {c.conflict_explanation}")
            lines.append("")

    # ── 分领域详情 ──
    lines.append("## 分领域详情")
    domain_names = {
        "self_life": "本命格局",
        "career": "事业工作",
        "wealth": "财运",
        "relationship": "感情关系",
        "health": "健康",
        "decision": "决策方向",
        "timing": "时机分析",
        "lost_item": "寻物",
        "home_fengshui": "住宅风水",
    }

    for domain, name in domain_names.items():
        sigs = domain_signals.get(domain, [])
        if not sigs:
            continue
        lines.append(f"### {name} ({domain})")

        for s in sigs[:5]:  # 每个领域最多显示5条
            emoji = "✅" if s.polarity == "positive" else "❌" if s.polarity == "negative" else "➖"
            lines.append(f"- {emoji} **{s.signal_key}** ({s.method}): {s.evidence} [强度{s.strength}]")
        lines.append("")

    # ── 风险提示 ──
    if validation.risks:
        lines.append("## 风险提示")
        for r in validation.risks:
            lines.append(f"- ⚠️ {r}")
        lines.append("")

    # ── 行动建议 ──
    if validation.action_advice:
        lines.append("## 行动建议")
        for i, a in enumerate(validation.action_advice, 1):
            lines.append(f"{i}. {a}")
        lines.append("")

    # ── 免责声明 ──
    lines.append("---")
    lines.append(DISCLAIMER)

    return "\n".join(lines)


def _generate_premium(
    domain_signals: dict[str, list[DivinationSignal]],
    validation: ValidationResult,
    intent: dict[str, Any],
    methods_used: list[str],
    standard_text: str,
) -> str:
    """生成深度报告 — 基于 standard 扩展。

    在生产环境中，这里会调用 LLM 进行深度增强解读。
    当前 MVP 版本在 standard 基础上增加更详细的分析。
    """
    lines: list[str] = []

    lines.append("# 深度命理分析报告 (Premium)")
    lines.append(f"**术法数量**: {len(methods_used)}")
    lines.append(f"**综合评分**: {validation.overall_score}/100")
    lines.append("")

    # 信号热度图
    lines.append("## 信号分布热图")
    domain_heat: dict[str, dict[str, int]] = {}
    for s in domain_signals.values():
        for signal in s:
            domain_heat.setdefault(signal.domain, {"positive": 0, "negative": 0, "neutral": 0})
            domain_heat[signal.domain][signal.polarity] += 1

    for domain, counts in domain_heat.items():
        total = sum(counts.values())
        bar = "█" * counts["positive"] + "▒" * counts["neutral"] + "░" * counts["negative"]
        lines.append(f"- {domain}: {bar} (正{counts['positive']}/中{counts['neutral']}/负{counts['negative']})")
    lines.append("")

    # 各术法贡献度
    lines.append("## 各术法贡献度")
    method_signals: dict[str, int] = {}
    for sigs in domain_signals.values():
        for s in sigs:
            method_signals[s.method] = method_signals.get(s.method, 0) + 1

    for method, count in sorted(method_signals.items(), key=lambda x: -x[1]):
        pct = count / max(1, sum(method_signals.values())) * 100
        lines.append(f"- **{method}**: {count}条信号 ({pct:.0f}%)")
    lines.append("")

    # 嵌入 standard 报告核心内容
    lines.append("## 详细分析")
    lines.append(standard_text)

    # LLM 增强提示（生产环境接入）
    lines.append("")
    lines.append("---")
    lines.append("*本报告由 Mystic Hub 12术法聚合引擎生成，如需 AI 深度解读可开启 LLM 增强模式。*")

    return "\n".join(lines)
