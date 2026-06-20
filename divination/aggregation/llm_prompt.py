"""LLM 报告生成器 (LLM-001~009)。

LLM-001: 为 ReadingResult 生成 LLM prompt
LLM-002: Prompt 包含 12 法摘要
LLM-003: Prompt 包含共识
LLM-004: Prompt 包含冲突
LLM-005: Prompt 包含合规规则
LLM-006: 支持 mock 模式
LLM-007: 支持 provider 配置
LLM-008: LLM 输出安全检查
LLM-009: LLM 失败 fallback
"""
from __future__ import annotations

from typing import Any

from .safety import DISCLAIMER, check_output_safety
from .schema import ReadingReport

# ── Provider config (LLM-007) ────────────────────────────────────────────────

SUPPORTED_PROVIDERS = ["openai", "anthropic", "gemini", "deepseek", "mock"]

DEFAULT_COMPLIANCE_RULES = (
    "【合规规则 — LLM 必须遵守】\n"
    "1. 禁止使用绝对化表达: '一定会', '必然', '肯定', '保证', '必须', '100%' 等。"
    " 使用 '倾向于', '较可能', '建议', '综合来看' 代替。\n"
    "2. 禁止提供医疗诊断建议。健康相关内容必须是文化角度的自我反思，"
    " 不得声称治疗或预测疾病。必须声明'请以正规医疗为准'。\n"
    "3. 禁止提供具体投资建议。财运分析只能做趋势参考，不得建议具体操作。\n"
    "4. 禁止提供法律判断。涉及到法律问题必须声明'请咨询持证律师'。\n"
    "5. 必须包含免责声明: '以上内容基于传统文化与符号象征视角，仅供参考，"
    " 不构成任何形式的专业建议。'\n"
    "6. 使用'建议', '可考虑', '值得关注'等建议性语言，禁止使用命令式语气。\n"
    "7. 如果检测到心理危机信号，不要进行命理分析，"
    " 而是提供心理援助热线信息。\n"
)


# ── LLM-001: Prompt builder ─────────────────────────────────────────────────

def build_reading_prompt(
    result: dict[str, Any],
    depth: str = "standard",
) -> str:
    """从 ReadingResult 生成 LLM prompt。

    Args:
        result: ReadingResult 的 dict 形式
        depth: 报告深度 (free/standard/premium)

    Returns:
        完整的 LLM system + user prompt 字符串
    """
    validation = result.get("validation", {})
    signals = result.get("signals", [])
    intent = result.get("intent", {})
    methods = result.get("methods_used", [])

    parts: list[str] = []

    # ── System prompt ──
    if depth == "standard":
        parts.append("你是一位简洁务实的命理分析师。用通俗易懂的语言给出关键发现和实用建议。")
        parts.append("不要冗长罗列术法细节，聚焦用户最关心的方面，给出能直接用的行动参考。")
    else:
        parts.append("你是一个融合中西命理学的综合分析师。")
        parts.append("你接收12种术法的交叉验证结果，生成自然流畅的综合报告。")
    parts.append("")
    parts.append(DEFAULT_COMPLIANCE_RULES)
    parts.append("")

    # ── Intent context ──
    goal_label = intent.get("goal_label", "综合")
    question = intent.get("question", "")
    parts.append("## 用户问题")
    parts.append(f"领域: {goal_label}")
    if question:
        parts.append(f"问题: {question}")
    parts.append("")

    # ── LLM-002: 12 法摘要 ──
    parts.append(f"## 参与术法 ({len(methods)}种)")
    METHOD_LABELS = {
        "bazi_v2": "八字", "ziwei": "紫微", "qimen": "奇门",
        "liuyao": "六爻", "meihua": "梅花", "fengshui": "风水",
        "bazhai": "八宅", "xuankong": "玄空", "western": "西方占星",
        "vedic": "吠陀占星", "tarot": "塔罗", "numerology": "数字命理",
    }
    method_summary = []
    for m in methods:
        m_signals = [s for s in signals if s.get("method") == m]
        if m_signals:
            top = max(m_signals, key=lambda s: s.get("strength", 0))
            method_summary.append(
                f"- {METHOD_LABELS.get(m, m)}: "
                f"{top.get('signal_key', '')} "
                f"({top.get('polarity', 'neutral')}, "
                f"强度{top.get('strength', 0):.0%})"
            )
        else:
            method_summary.append(f"- {METHOD_LABELS.get(m, m)}: 未产生有效信号")
    parts.append("\n".join(method_summary))
    parts.append("")

    # ── LLM-003: 共识 ──
    consensus_list = result.get("consensus", validation.get("consensus", []))
    if consensus_list:
        parts.append("## 多术法共识（以下结论有多个术法一致支持，可信度较高）")
        for c in consensus_list:
            parts.append(f"- {c.get('theme', '')}: {c.get('explanation', '')}")
            parts.append(f"  支持术法: {', '.join(c.get('supporting_methods', []))}")
        parts.append("")

    # ── LLM-004: 冲突 ──
    conflict_list = result.get("conflicts", validation.get("conflicts", []))
    if conflict_list:
        parts.append("## 术法分歧（必须解释分歧原因，不得回避）")
        for c in conflict_list:
            sev = c.get("severity", "medium")
            parts.append(f"- [{sev.upper()}] {c.get('domain', '')}: "
                        f"{c.get('conflict_explanation', '')}")
            parts.append(f"  正向: {', '.join(c.get('positive_methods', []))}")
            parts.append(f"  负向: {', '.join(c.get('negative_methods', []))}")
            if c.get("resolution"):
                parts.append(f"  调和建议: {c['resolution']}")
        parts.append("")

    # ── 五档计票(替代单一分数) ──
    tally = validation.get("tally_by_scope") or {}
    parts.append("## 多术法计票(按 time_scope)")
    if tally:
        for scope, t in tally.items():
            parts.append(
                f"- {scope}: 强支持{t.get('strong_support',0)}/弱支持{t.get('weak_support',0)}/"
                f"中性{t.get('neutral',0)}/弱警示{t.get('weak_warn',0)}/强警示{t.get('strong_warn',0)} "
                f"({t.get('summary','')})"
            )
    else:
        parts.append("- 暂无有效计票信号")
    polarity = validation.get("dimension_polarity") or {}
    if polarity:
        parts.append("## 五维极性")
        for dim, p in polarity.items():
            parts.append(f"- {dim}: {p}")
    parts.append("")

    # ── Risks ──
    risks = validation.get("risks", [])
    if risks:
        parts.append("## 风险提示（需谨慎表达）")
        for r in risks:
            parts.append(f"- {r}")
        parts.append("")

    # ── Timing ──
    timing = validation.get("timing")
    if timing:
        parts.append(f"## 时间窗口: {timing.get('summary', '')}")
        parts.append("")

    # ── Output instruction ──
    if depth == "standard":
        parts.append("## 请你生成一份简洁实用的报告（控制在 800 字以内）")
        parts.append("1. 一句话综合结论（用大白话，不要用专业术语）")
        parts.append("2. 3 条关键发现（每条一句话，说清楚对用户的实际影响）")
        parts.append("3. 3-5 条现在可以做的事（具体、可操作，不要泛泛而谈）")
    elif depth == "premium":
        parts.append("## 请你生成以下格式的报告")
        parts.append("1. 一句话综合结论（含评分和置信度）")
        parts.append("2. 各领域分析（不要逐术法罗列，而是按领域综合）")
        parts.append("3. 多法共识分析")
        parts.append("4. 术法分歧及调和建议")
        parts.append("5. 风险提示（谨慎表达，禁止绝对化）")
        parts.append("6. 行动建议（使用建议性语言，不做命令）")
        parts.append("7. 时间窗口分析")
        parts.append("8. 深入追问的方向建议")
    else:
        # free: minimal
        parts.append("## 请你生成一份简短摘要")
        parts.append("1. 一句话总结")
        parts.append("2. 1-2 条建议")
    parts.append(f"\n{DISCLAIMER}")

    return "\n".join(parts)


# ── LLM-006: Mock mode ──────────────────────────────────────────────────────

def generate_mock_report(
    result: dict[str, Any],
    depth: str = "standard",
) -> str:
    """无需 API Key 时生成模板化报告 (LLM-006 + LLM-009)。"""
    validation = result.get("validation", {})
    consensus_list = validation.get("consensus", [])
    conflict_list = validation.get("conflicts", [])
    risks = validation.get("risks", [])
    advice = validation.get("action_advice", [])
    intent = result.get("intent", {})

    lines: list[str] = []

    # Headline — 五档计票(无单一分数)
    tally = validation.get("tally_by_scope") or {}
    goal_label = intent.get("goal_label", "综合")
    lines.append(f"## {goal_label}综合分析报告")
    if tally:
        sup_total = sum(t.get("strong_support", 0) + t.get("weak_support", 0) for t in tally.values())
        warn_total = sum(t.get("strong_warn", 0) + t.get("weak_warn", 0) for t in tally.values())
        lines.append(f"多术法计票: {sup_total} 法支持 / {warn_total} 法警示(各 time_scope 详见下文)")
    else:
        lines.append("多术法计票: 暂无有效信号")
    lines.append("")

    # Consensus
    if consensus_list:
        lines.append("### 多术法共识")
        for c in consensus_list[:3]:
            lines.append(f"- **{c.get('theme', '')}**: {c.get('explanation', '')}")
        lines.append("")

    # Conflicts
    if conflict_list:
        lines.append("### 需关注的术法分歧")
        for c in conflict_list[:3]:
            lines.append(f"- {c.get('domain', '')}: {c.get('conflict_explanation', '')}")
        lines.append("")

    # Risks
    if risks:
        lines.append("### 风险提示")
        for r in risks[:5]:
            lines.append(f"- {r}")
        lines.append("")

    # Advice
    if advice:
        lines.append("### 行动建议")
        for a in advice[:5]:
            lines.append(f"- {a}")
        lines.append("")

    # Disclaimer
    lines.append("---")
    lines.append(DISCLAIMER)
    lines.append("")
    lines.append("*本报告由 Mystic Hub 12术法聚合引擎自动生成（Mock 模式）。*")

    return "\n".join(lines)


# ── LLM-008: Output safety check ────────────────────────────────────────────

def check_llm_output(text: str) -> dict[str, Any]:
    """对 LLM 输出做安全检查。

    Returns:
        {
            "safe": bool,
            "needs_softening": bool,
            "issues": [str],
            "softened_text": str,
        }
    """
    result = check_output_safety(text)

    issues: list[str] = []
    needs_softening = False

    if result["absolute_hits"]:
        issues.append(f"发现绝对化表达: {', '.join(result['absolute_hits'])}")
        needs_softening = True

    if result["warnings"]:
        issues.extend(result["warnings"])

    # Check for missing disclaimer (consistent with check_output_safety)
    if "免责声明" not in text and "仅供参考" not in text:
        issues.append("缺少免责声明")

    return {
        "safe": len(issues) == 0,
        "needs_softening": needs_softening,
        "issues": issues,
        "softened_text": result["softened"] if needs_softening else text,
    }


# ── LLM-009: Fallback ───────────────────────────────────────────────────────

def llm_fallback_report(
    result: dict[str, Any],
    depth: str = "standard",
) -> ReadingReport:
    """LLM 调用失败时使用模板报告 (LLM-009)。"""
    mock_text = generate_mock_report(result, depth)

    return ReadingReport(
        free=mock_text[:500] if len(mock_text) > 500 else mock_text,
        standard=mock_text,
        premium=mock_text,
    )
