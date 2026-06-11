"""报告生成器 — 生成三档可读中文报告（不再用 emoji/英文 key/嵌套重复）。

REP-001: synthesize_report() 返回 ReadingReport
REP-002: 一句话结论
REP-003: 免费版 — 速览段落 + 核心建议
REP-004: 标准版 — 叙事性领域分析 + 共识/分歧 + 风险/建议
REP-005: 高级版 — 深度模式分析 + 时窗 + 追问方向（不嵌套标准版）
REP-011: 三档均含免责声明
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

# ── 常量 ─────────────────────────────────────────────────────────────────────

DISCLAIMER = (
    "【免责声明】以上内容为基于传统文化与符号象征视角的参考分析，仅供参考，"
    "不构成医疗诊断、法律建议或投资指导。命理分析具有文化传承价值，"
    "但不应替代专业意见。重大人生决策请结合现实情况，咨询相关专业人士。"
)

METHOD_ZH: dict[str, str] = {
    "bazi_v2": "八字精算", "bazi": "八字", "ziwei": "紫微斗数",
    "qimen": "奇门遁甲", "liuyao": "六爻", "meihua": "梅花易数",
    "fengshui": "风水", "bazhai": "八宅明镜", "xuankong": "玄空飞星",
    "western": "西方占星", "vedic": "吠陀占星",
    "tarot": "塔罗", "numerology": "数字命理",
    "lenormand": "雷诺曼", "liuren": "大六壬", "tieban": "铁板神数",
}

DOMAIN_ZH: dict[str, str] = {
    "self_life": "本命格局", "career": "事业工作", "wealth": "财运",
    "relationship": "感情姻缘", "health": "身心健康", "decision": "决策方向",
    "timing": "时机运势", "home_fengshui": "住宅风水",
    "general": "综合", "monthly": "月运", "yearly": "年运",
}

SIGNAL_ZH: dict[str, str] = {
    "short_term_caution": "短期需谨慎",
    "long_term_potential": "长期有潜力",
    "decision_delay": "时机未到宜等待",
    "environment_support": "环境有助益",
    "general_reference": "一般性参考",
    "noble_help": "贵人相助",
    "career_pressure": "事业有压力",
    "career_independence": "适合自主发展",
    "marriage_stability": "婚姻稳定度高",
    "relationship_attraction": "桃花运旺",
    "timing_transition": "处于转换期",
    "layout_risk": "布局有隐患",
    "direction_benefit": "方位有助益",
    "wealth_opportunity": "财运有机会",
    "health_reflection": "健康需关注",
}

POLARITY_ZH: dict[str, str] = {
    "positive": "吉", "negative": "凶", "neutral": "平", "mixed": "杂",
}


def _sig_name(s: DivinationSignal | dict) -> str:
    """信号的中文显示名。"""
    if isinstance(s, dict):
        key = s.get("signal_key", "")
    else:
        key = s.signal_key
    return SIGNAL_ZH.get(key, key)


def _method_name(m: str) -> str:
    return METHOD_ZH.get(m, m)


def _domain_name(d: str) -> str:
    return DOMAIN_ZH.get(d, d)


# ── REP-001: 主入口 ───────────────────────────────────────────────────────────

def synthesize_report(
    signals: list[DivinationSignal],
    validation: ValidationResult,
    intent: dict[str, Any],
    methods_used: list[str],
    depth: str = "standard",
) -> ReadingReport:
    """返回三档报告（每档独立可读，不互相嵌套）。"""
    primary_label = intent.get("goal_label", intent.get("primary_label", "综合"))
    question = intent.get("question", "")

    # 按领域和方法分组
    domain_sigs: dict[str, list[DivinationSignal]] = {}
    method_sigs: dict[str, list[DivinationSignal]] = {}
    for s in signals:
        domain_sigs.setdefault(s.domain, []).append(s)
        method_sigs.setdefault(s.method, []).append(s)

    headline = _headline(signals, validation, primary_label, question)

    free_report = _build_free(headline, validation, signals, methods_used, question)
    standard_report = _build_standard(headline, domain_sigs, method_sigs, validation, intent, methods_used, question)
    premium_report = _build_premium(headline, domain_sigs, method_sigs, validation, intent, methods_used)

    return ReadingReport(free=free_report, standard=standard_report, premium=premium_report)


# ── REP-002: Headline ──────────────────────────────────────────────────────────

def _headline(
    signals: list[DivinationSignal],
    validation: ValidationResult,
    primary_label: str,
    question: str,
) -> str:
    score = validation.overall_score
    pos_n = sum(1 for s in signals if s.polarity == "positive")
    neg_n = sum(1 for s in signals if s.polarity == "negative")
    method_n = len(set(s.method for s in signals))

    if score >= 70:
        tone = "整体趋势积极向好"
    elif score >= 55:
        tone = "整体态势平稳"
    elif score >= 40:
        tone = "需留意潜在波动"
    else:
        tone = "宜谨慎行事，多作准备"

    ctx = f"就「{question}」所问，" if question else ""
    return (
        f"{ctx}综{method_n}种术法交叉参详，{tone}。"
        f"正向信号{pos_n}条，负向信号{neg_n}条，综合评分{score}分。"
    )


# ── REP-003: 免费版 ───────────────────────────────────────────────────────────

def _build_free(
    headline: str,
    validation: ValidationResult,
    signals: list[DivinationSignal],
    methods_used: list[str],
    question: str,
) -> str:
    lines: list[str] = []

    lines.append(headline)
    lines.append("")

    # 一句话概括
    score = validation.overall_score
    pos_sigs = [s for s in signals if s.polarity == "positive"]
    neg_sigs = [s for s in signals if s.polarity == "negative"]

    if pos_sigs:
        best = max(pos_sigs, key=lambda s: s.strength)
        lines.append(f"最有利的方面是「{_sig_name(best)}」（{_method_name(best.method)}，{_domain_name(best.domain)}），可多加把握。")
    if neg_sigs:
        worst = max(neg_sigs, key=lambda s: s.strength)
        lines.append(f"最需留意的方面是「{_sig_name(worst)}」（{_method_name(worst.method)}），建议谨慎对待。")

    lines.append("")

    # 核心建议
    advice = validation.action_advice[:2] if validation.action_advice else []
    if advice:
        lines.append("核心建议：")
        for a in advice:
            lines.append(f"· {a}")
        lines.append("")

    lines.append("---")
    lines.append(DISCLAIMER)

    return "\n".join(lines)


# ── REP-004: 标准版 ───────────────────────────────────────────────────────────

def _build_standard(
    headline: str,
    domain_sigs: dict[str, list[DivinationSignal]],
    method_sigs: dict[str, list[DivinationSignal]],
    validation: ValidationResult,
    intent: dict[str, Any],
    methods_used: list[str],
    question: str,
) -> str:
    lines: list[str] = []
    primary_label = intent.get("goal_label", intent.get("primary_label", "综合"))

    # ── 标题 ──
    lines.append(f"命书 · {primary_label}")
    lines.append(headline)
    lines.append("")

    # ── 总体判断 ──
    lines.append("【总体判断】")
    score = validation.overall_score

    # 找最强正向和负向信号
    pos_sigs = sorted(
        [s for s in (list(domain_sigs.values()) if domain_sigs else []) for s in (list(domain_sigs.values())[0] if domain_sigs else [])],
        key=lambda s: s.strength, reverse=True
    )
    pos_sigs = sorted(
        [s for ss in domain_sigs.values() for s in ss if s.polarity == "positive"],
        key=lambda s: s.strength, reverse=True,
    )
    neg_sigs = sorted(
        [s for ss in domain_sigs.values() for s in ss if s.polarity == "negative"],
        key=lambda s: s.strength, reverse=True,
    )

    # 综合描述
    method_list = "、".join(_method_name(m) for m in methods_used[:6])
    if len(methods_used) > 6:
        method_list += f"等{len(methods_used)}种术法"
    lines.append(f"本次合参共调用{method_list}，交叉验证后综合评分为{score}分。")

    if pos_sigs and neg_sigs:
        lines.append(
            f"吉象主要体现在{_domain_name(pos_sigs[0].domain)}（{_sig_name(pos_sigs[0])}，"
            f"{_method_name(pos_sigs[0].method)}），"
            f"而{_domain_name(neg_sigs[0].domain)}方面（{_sig_name(neg_sigs[0])}）需多加留意。"
        )
    elif pos_sigs:
        lines.append(f"整体以吉象为主，{_domain_name(pos_sigs[0].domain)}方面（{_sig_name(pos_sigs[0])}）信号最为明确。")
    elif neg_sigs:
        lines.append(f"当前需重点关注{_domain_name(neg_sigs[0].domain)}（{_sig_name(neg_sigs[0])}），宜谨慎行事。")
    else:
        lines.append("各术法信号以中性为主，无明显偏吉或偏凶倾向，属平稳时期。")

    lines.append("")

    # ── 共识分析 ──
    if validation.consensus:
        lines.append("【诸法共识】")
        for c in validation.consensus[:3]:
            supporters = "、".join(_method_name(m) for m in c.supporting_methods[:4])
            if len(c.supporting_methods) > 4:
                supporters += f"等{len(c.supporting_methods)}法"
            lines.append(f"{c.theme}——{c.explanation}（{supporters}一致支持）")
        lines.append("")
    else:
        lines.append("【诸法共识】本次各术法信号较为分散，未形成显著共识，建议提供更详细的出生信息以便深入分析。")
        lines.append("")

    # ── 分歧分析 ──
    if validation.conflicts:
        lines.append("【术法分歧】")
        for c in validation.conflicts[:3]:
            pos_m = "、".join(_method_name(m) for m in c.positive_methods[:3])
            neg_m = "、".join(_method_name(m) for m in c.negative_methods[:3])
            lines.append(f"在{_domain_name(c.domain)}方面存在分歧：{c.conflict_explanation}")
            lines.append(f"  · 正向信号来自{pos_m}，负向信号来自{neg_m}")
            if c.resolution:
                lines.append(f"  · 调和思路：{c.resolution}")
        lines.append("")

    # ── 分领域解析 ──
    domain_order = ["self_life", "career", "wealth", "relationship", "decision", "timing", "home_fengshui", "health"]
    written = False
    for dom in domain_order:
        sigs = domain_sigs.get(dom, [])
        if not sigs:
            continue
        written = True
        dom_name = _domain_name(dom)
        lines.append(f"【{dom_name}】")

        # 按方法分组描述
        for s in sorted(sigs, key=lambda x: x.strength, reverse=True)[:3]:
            polarity_mark = POLARITY_ZH.get(s.polarity, "平")
            evidence = s.evidence if s.evidence else ""
            lines.append(
                f"  {polarity_mark} {_method_name(s.method)}显示：{_sig_name(s)}"
                + (f"（{evidence}）" if evidence else "")
            )

        # 小结该领域
        dom_pos = sum(1 for s in sigs if s.polarity == "positive")
        dom_neg = sum(1 for s in sigs if s.polarity == "negative")
        if dom_pos > dom_neg:
            lines.append(f"  该领域总体偏吉（{dom_pos}吉/{dom_neg}凶），可积极把握。")
        elif dom_neg > dom_pos:
            lines.append(f"  该领域需谨慎对待（{dom_pos}吉/{dom_neg}凶），建议多做准备。")
        else:
            lines.append(f"  该领域信号中性（{dom_pos}吉/{dom_neg}凶），维持现状即可。")
        lines.append("")

    if not written:
        lines.append("【信号概述】本次产生的信号覆盖领域较广，各术法均有输出。由于信号强度整体偏弱，建议补充出生信息后重新分析以获得更明确的指向。")
        lines.append("")

    # ── 风险与建议 ──
    if validation.risks:
        lines.append("【注意事项】")
        for r in validation.risks[:5]:
            lines.append(f"· {r}")
        lines.append("")

    if validation.action_advice:
        lines.append("【行动参考】")
        for i, a in enumerate(validation.action_advice[:5], 1):
            lines.append(f"{i}. {a}")
        lines.append("")

    # ── 时机 ──
    if validation.timing and validation.timing.get("summary"):
        lines.append(f"【时令参考】{validation.timing['summary']}")
        lines.append("")

    lines.append("---")
    lines.append(DISCLAIMER)

    return "\n".join(lines)


# ── REP-005: 高级版 ───────────────────────────────────────────────────────────

def _build_premium(
    headline: str,
    domain_sigs: dict[str, list[DivinationSignal]],
    method_sigs: dict[str, list[DivinationSignal]],
    validation: ValidationResult,
    intent: dict[str, Any],
    methods_used: list[str],
) -> str:
    lines: list[str] = []
    primary_label = intent.get("goal_label", intent.get("primary_label", "综合"))

    lines.append(f"命书 · {primary_label}（深度卷）")
    lines.append(headline)
    lines.append("")

    # ── 全局模式分析 ──
    lines.append("【全局模式】")

    # 信号分布模式
    total_signals = sum(len(v) for v in domain_sigs.values())
    pos_count = sum(1 for ss in domain_sigs.values() for s in ss if s.polarity == "positive")
    neg_count = sum(1 for ss in domain_sigs.values() for s in ss if s.polarity == "negative")
    neu_count = total_signals - pos_count - neg_count

    lines.append(
        f"本次共产生{total_signals}条信号（吉{pos_count}、凶{neg_count}、平{neu_count}），"
        f"覆盖{len(domain_sigs)}个领域、{len(methods_used)}种术法。"
    )

    # 术法贡献概要
    ranked = sorted(method_sigs.items(), key=lambda x: sum(s.strength for s in x[1]), reverse=True)
    top3 = ranked[:3]
    if top3:
        top3_desc = "；".join(
            f"{_method_name(m)}贡献{len(ss)}条信号（偏向{'吉' if sum(1 for s in ss if s.polarity=='positive') > sum(1 for s in ss if s.polarity=='negative') else '中' if sum(1 for s in ss if s.polarity=='positive') == sum(1 for s in ss if s.polarity=='negative') else '凶'}）"
            for m, ss in top3
        )
        lines.append(f"贡献最多的三种术法：{top3_desc}。")

    # 是否有一致性
    if pos_count > neg_count * 2:
        lines.append("诸法整体偏向积极，吉象信号占据主导，可在把握机遇的同时留意个别负面提示。")
    elif neg_count > pos_count * 2:
        lines.append("负面信号占比偏高，建议当前阶段以守为主，待时机明朗后再行决策。")
    else:
        lines.append("吉凶信号分布较为均衡，说明当前处境有多个面向需要分别对待，不宜一概而论。")

    lines.append("")

    # ── 领域深度分析 ──
    lines.append("【领域深度】")
    domain_order = ["self_life", "career", "wealth", "relationship", "decision", "timing", "home_fengshui", "health"]

    for dom in domain_order:
        sigs = domain_sigs.get(dom, [])
        if not sigs:
            continue
        dom_name = _domain_name(dom)
        dom_pos = sum(s.strength for s in sigs if s.polarity == "positive")
        dom_neg = sum(s.strength for s in sigs if s.polarity == "negative")

        if dom_pos > dom_neg * 1.5:
            tendency = "偏吉，诸法指向较为一致"
        elif dom_neg > dom_pos * 1.5:
            tendency = "偏凶，需重点关注"
        elif dom_pos > dom_neg:
            tendency = "略微偏吉，但有分歧需注意"
        elif dom_neg > dom_pos:
            tendency = "略微偏紧，但非全无机会"
        else:
            tendency = "中性平稳"

        lines.append(f"· {dom_name}（{len(sigs)}条信号）：{tendency}。")
        # 列出关键信号
        for s in sorted(sigs, key=lambda x: x.strength, reverse=True)[:2]:
            lines.append(f"  ― {_method_name(s.method)}：{_sig_name(s)}（{POLARITY_ZH.get(s.polarity, '平')}，强度{s.strength:.0%}）")

    lines.append("")

    # ── 术法分歧深度分析 ──
    if validation.conflicts:
        lines.append("【分歧辨析】")
        for c in validation.conflicts[:3]:
            lines.append(f"{_domain_name(c.domain)}：{c.conflict_explanation}")
            if c.resolution:
                lines.append(f"  调和方向：{c.resolution}")
            lines.append(f"  正向术法：{'、'.join(_method_name(m) for m in c.positive_methods[:4])}")
            lines.append(f"  负向术法：{'、'.join(_method_name(m) for m in c.negative_methods[:4])}")
        lines.append("")

    # ── 风险深度 ──
    if validation.risks:
        lines.append("【风险研判】")
        for r in validation.risks:
            # 替换风险文本中的英文 signal key 为中文
            r_zh = r
            for en_key, zh_key in SIGNAL_ZH.items():
                r_zh = r_zh.replace(en_key, zh_key)
            lines.append(f"· {r_zh}")
        lines.append("")

    # ── 时间窗 ──
    if validation.timing:
        t = validation.timing
        lines.append("【时令参详】")
        short_n = t.get("short_term_signals", 0)
        med_n = t.get("medium_term_signals", 0)
        long_n = t.get("long_term_signals", 0)
        lines.append(f"短期信号{short_n}条，中期{med_n}条，长期{long_n}条。{t.get('summary', '')}")
        if short_n > long_n:
            lines.append("信号以近期为主，建议关注未来1-3个月内的变化。")
        elif long_n > short_n:
            lines.append("信号偏向长周期，不必过于纠结短期波动，可从长计议。")
        lines.append("")

    # ── 追问方向 ──
    lines.append("【可深入的方向】")
    weak_domains = [
        d for d in domain_order
        if d in domain_sigs and sum(s.strength for s in domain_sigs[d]) / len(domain_sigs[d]) < 0.45
    ][:3]
    if weak_domains:
        lines.append(f"以下领域信号偏弱，补充出生信息或具体问题可提高精度：{'、'.join(_domain_name(d) for d in weak_domains)}。")

    if validation.conflicts:
        conflict_domains = list(set(_domain_name(c.domain) for c in validation.conflicts[:2]))
        lines.append(f"存在术法分歧的领域（{'、'.join(conflict_domains)}），可针对具体场景进一步追问。")

    lines.append("")

    # ── 免责 ──
    lines.append("---")
    lines.append(DISCLAIMER)
    lines.append("")
    lines.append("*本深度报告由 Mystic Hub 多术法聚合引擎生成，可针对具体领域进一步追问。*")

    return "\n".join(lines)


# ── 向后兼容 ──────────────────────────────────────────────────────────────────

def generate(
    signals: list[DivinationSignal],
    validation: ValidationResult,
    intent: dict[str, Any],
    methods_used: list[str],
    depth: str = "standard",
) -> ReadingReport:
    return synthesize_report(signals, validation, intent, methods_used, depth)
