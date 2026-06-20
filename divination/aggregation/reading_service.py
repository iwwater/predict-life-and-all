"""Reading 主编排服务 — 协调意图分类、术法选择、并行计算、标准化、验证、报告生成。

BE-009: 主服务文件

核心流程:
  1. classify_intent(question, goal) → goal + sub_goals
  2. select_methods(goal) → [{method, label, tier}, ...]
  3. 并行 compute(method) → 12 ChartResult
  4. normalize_all(charts) → unified signals
  5. validate(signals, intent) → consensus + conflicts
  6. synthesize_report(signals, ...) → 三档模板报告（基础/降级用）
  7. LLM 生成 premium 深度报告 → 替换模板 premium
  8. 返回 ReadingResult
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Any

from divination.contracts import Birth
from divination.knowledge import extract_rules_for_chart

from .intent import classify_intent
from .llm_prompt import build_reading_prompt
from .method_inputs import build_method_inputs
from .normalizer import normalize_all
from .reality import RealityConstraintEngine
from .safety import check_input_safety, sanitize_for_log
from .schema import (
    BirthModel,
    ReadingReport,
    ReadingRequest,
    ReadingResult,
    ValidationResult,
)
from .selector import get_method_names, select_methods
from .situation import build_situation
from .synthesizer import DISCLAIMER, synthesize_report
from .validator import validate_signals
from .weights import get_weights

log = logging.getLogger("mystic-hub.reading")


async def run_reading(request: ReadingRequest) -> ReadingResult:
    """执行一次完整的 reading 流程。

    Args:
        request: 用户请求

    Returns:
        ReadingResult
    """
    t0 = time.perf_counter()
    session_id = uuid.uuid4().hex[:12]
    errors: list[dict[str, Any]] = []

    # SAFE-005: 安全检查 — 危机检测和敏感领域降级
    safety = check_input_safety(request.question)
    safety_flags: list[str] = []
    safety_downgrades = safety.get("downgrades", [])

    if safety.get("crisis"):
        # SAFE-005: 危机响应 — 不进行术法计算
        from .schema import ReadingReport as RR, ValidationResult as VR
        crisis_report = RR(
            free=f"【安全提示】\n\n{safety['crisis_message']}",
            standard=f"【安全提示】\n\n{safety['crisis_message']}",
            premium=f"【安全提示】\n\n{safety['crisis_message']}",
        )
        return ReadingResult(
            session_id=session_id,
            intent={"goal": "crisis", "goal_label": "安全响应", "goal_confidence": 1.0, "goal_source": "safety"},
            methods_used=[],
            signals=[],
            consensus=[],
            conflicts=[],
            validation=VR(risks=["安全响应: 暂停常规分析"]),
            report=crisis_report,
            disclaimer=safety["crisis_message"],
            elapsed_ms=0,
            errors=[],
            safety_flags=["crisis_blocked"],
            safety_downgrades=[],
            is_unlocked_standard=True,
            is_unlocked_premium=True,
        )

    if safety_downgrades:
        safety_flags.append("content_downgraded")

    # SAFE-010: 日志脱敏
    safe_question = sanitize_for_log(request.question)

    # Step 1: 意图分类 (INT-001, INT-014)
    intent = classify_intent(
        question=request.question,
        goal=request.goal if hasattr(request, 'goal') and request.goal else None,
    )
    goal = intent["goal"]

    # Step 2: 术法选择 (SEL-002) — 返回 [{method, label, tier}, ...]
    method_entries = select_methods(goal=goal)
    method_names = get_method_names(method_entries)

    # 如果用户指定了 methods，只保留用户选中的
    _req_methods = getattr(request, 'methods', None)
    log.info("DEBUG methods: has=%s val=%s all_methods=%s", hasattr(request, 'methods'), _req_methods, method_names)
    if _req_methods:
        method_names = [m for m in method_names if m in _req_methods]
        log.info("DEBUG filtered: %s", method_names)

    if not method_names:
        raise ValueError("没有可用的术法 — 请至少选择一种术法")

    # Step 1.5: 境限装配 (Sprint 1.3)
    situation = build_situation(
        request=request,
        intent=intent,
        context_answers=getattr(request, "context_answers", None) or {},
    )

    # Step 3-4: 构建术法专属输入 + 并行排盘
    from divination.router import _ENGINES as ENGINES

    # 为每种术法构造只含相关字段的 Birth
    # Sprint 1.4/1.7: 注入 intent + situation + user_selections
    user_selections = getattr(request, "context_answers", None) or {}
    method_births = build_method_inputs(
        birth=_build_birth(request.birth) if request.birth else None,
        target_birth=_build_birth(request.target_birth) if getattr(request, 'target_birth', None) else None,
        space=request.space if hasattr(request, 'space') else None,
        method_options=getattr(request, 'method_options', None),
        question=request.question,
        goal=goal,
        intent=intent,
        situation=situation,
        user_selections=user_selections,
    )

    charts: dict[str, Any] = {}
    for m in method_names:
        if m not in ENGINES:
            errors.append({"method": m, "error": "引擎未注册"})
            continue
        try:
            method_birth = method_births.get(m)
            if method_birth is None:
                # fallback: 默认 birth
                method_birth = _default_birth()
            # hepan 需要 partner Birth 作为 kwarg
            if m == "hepan" and hasattr(method_birth, "partner"):
                charts[m] = ENGINES[m](method_birth, partner=method_birth.partner)
            else:
                charts[m] = ENGINES[m](method_birth)
        except Exception as e:
            log.warning("Method %s failed: %s", m, e)
            errors.append({"method": m, "error": str(e)})
            from divination.contracts import ChartResult
            charts[m] = ChartResult(
                method=m,
                school="west" if m in ("western", "vedic", "tarot", "numerology", "lenormand") else "east",
                engine="placeholder",
                normalized={},
                raw={"_error": str(e), "_placeholder": True},
            )

    # Step 5: 标准化
    signals = normalize_all(charts)

    # Step 6: 计算 weights 并交叉验证
    weights = get_weights(goal, method_entries)
    validation = validate_signals(signals, weights, method_entries)

    # Step 6b: 现实条件校正 (Sprint 1.6: 声明式 + 安全转介)
    reality_result = None
    if request.constraints or request.question:
        engine = RealityConstraintEngine()
        reality_result = engine.evaluate(
            signals=signals,
            constraints=request.constraints,
            question=request.question,  # Sprint 1.6: 用于安全转介关键词扫描
            domain=goal,
        )

    # Step 6c: 古典规则提取 (Phase E)
    # 以信号最多的术法 chart 为 primary_chart
    primary_chart = None
    if method_names and charts:
        def _chart_size(m: str) -> int:
            c = charts.get(m)
            return len(c.raw) if (c and hasattr(c, "raw") and c.raw) else 0
        primary_method = max(method_names, key=_chart_size)
        primary_chart = charts.get(primary_method)
    classical_rules = extract_rules_for_chart(primary_chart, max_rules=5) if primary_chart else []

    # Step 7: 模板报告生成（基础/降级用）
    intent["question"] = request.question  # 供 synthesizer 生成 headline
    template_report = synthesize_report(
        signals=signals,
        validation=validation,
        intent=intent,
        methods_used=method_names,
        depth=request.depth,
        reality=reality_result,
        classical=classical_rules,
    )

    # Step 8: LLM 报告生成（standard 和 premium 都走 LLM，fallback 到模板）
    is_unlocked_standard = False
    is_unlocked_premium = False
    llm_standard_text: str | None = None
    llm_premium_text: str | None = None

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()

    if request.depth in ("standard", "premium"):
        # 标准版 LLM：有 API Key 时生成
        llm_standard_text = await _generate_llm_report(
            signals=signals,
            validation=validation,
            intent=intent,
            methods_used=method_names,
            question=request.question,
            depth="standard",
            api_key=api_key,
        )
        if llm_standard_text:
            is_unlocked_standard = True

    if request.depth == "premium":
        # 深度版 LLM：有 API Key 生成深度报告，无 API Key 用 data-driven mock
        llm_premium_text = await _generate_llm_report(
            signals=signals,
            validation=validation,
            intent=intent,
            methods_used=method_names,
            question=request.question,
            depth="premium",
            api_key=api_key,
        )
        if llm_premium_text and api_key:
            is_unlocked_premium = True

    # 组装最终报告
    report = ReadingReport(
        free=template_report.free,
        standard=llm_standard_text or template_report.standard,
        premium=llm_premium_text or template_report.premium,
    )

    dt_ms = int((time.perf_counter() - t0) * 1000)

    # W10 fix: hepan without target_birth is not a real method for this case
    effective_methods = []
    hepan_no_partner = False
    has_target_birth = getattr(request, 'target_birth', None) is not None
    for m in method_names:
        if m == "hepan" and not has_target_birth:
            hepan_no_partner = True
            continue  # hepan without partner: don't count as real method in 18法
        effective_methods.append(m)

    return ReadingResult(
        session_id=session_id,
        intent=intent,
        methods_used=effective_methods if effective_methods else method_names,
        signals=signals,
        consensus=validation.consensus,
        conflicts=validation.conflicts,
        validation=validation,
        report=report,
        disclaimer=DISCLAIMER,
        elapsed_ms=dt_ms,
        errors=errors,
        safety_flags=safety_flags,
        safety_downgrades=safety_downgrades,
        is_unlocked_standard=is_unlocked_standard,
        is_unlocked_premium=is_unlocked_premium,
        reality_adjusted=_reality_to_dict(reality_result),
        hepan_no_partner=hepan_no_partner,
    )


# ── LLM 深度报告生成 ────────────────────────────────────────────────────────────

def _build_result_dict(
    signals: list,
    validation: ValidationResult,
    intent: dict[str, Any],
    methods_used: list[str],
    question: str,
) -> dict[str, Any]:
    """将内部对象转为 dict，供 LLM prompt builder 使用。"""
    return {
        "validation": {
            "tally_by_scope": {
                k: {
                    "scope": v.scope,
                    "strong_support": v.strong_support,
                    "weak_support": v.weak_support,
                    "neutral": v.neutral,
                    "weak_warn": v.weak_warn,
                    "strong_warn": v.strong_warn,
                    "supporting_methods": v.supporting_methods,
                    "warning_methods": v.warning_methods,
                    "summary": v.summary,
                }
                for k, v in (validation.tally_by_scope or {}).items()
            },
            "dimension_polarity": dict(validation.dimension_polarity or {}),
            "consensus": [
                {
                    "theme": c.theme,
                    "explanation": c.explanation,
                    "supporting_methods": c.supporting_methods,
                    "weight_strength": getattr(c, "weight_strength", 0),
                }
                for c in validation.consensus
            ],
            "conflicts": [
                {
                    "domain": c.domain,
                    "severity": c.severity,
                    "conflict_explanation": c.conflict_explanation,
                    "positive_methods": c.positive_methods,
                    "negative_methods": c.negative_methods,
                    "resolution": getattr(c, "resolution", ""),
                }
                for c in validation.conflicts
            ],
            "risks": validation.risks,
            "action_advice": validation.action_advice,
            "timing": validation.timing,
        },
        "signals": [
            {
                "method": s.method,
                "domain": s.domain,
                "signal_key": s.signal_key,
                "polarity": s.polarity,
                "strength": s.strength,
                "confidence": s.confidence,
                "evidence": s.evidence if s.evidence else "",
            }
            for s in signals
        ],
        "intent": intent,
        "methods_used": methods_used,
    }


async def _generate_llm_report(
    signals: list,
    validation: ValidationResult,
    intent: dict[str, Any],
    methods_used: list[str],
    question: str,
    depth: str,
    api_key: str,
) -> str | None:
    """调用 LLM 生成报告（支持 standard 和 premium）。

    standard: 简洁务实，800字内，聚焦关键发现 + 实操建议
    premium: 全面深度，融合12法交叉分析

    失败时返回 None 以触发降级。
    """
    try:
        result_dict = _build_result_dict(
            signals, validation, intent, methods_used, question,
        )

        if not api_key:
            # 无 API Key: premium 用 data-driven mock, standard 返回 None 触发模板降级
            if depth == "premium":
                return _generate_data_driven_mock(result_dict)
            return None

        # ── 真实 LLM 调用 ──
        from divination.interpret.client import AnthropicClient
        model = os.environ.get("LLM_MODEL", "claude-3-5-haiku-latest").strip()
        llm_client = AnthropicClient(api_key=api_key, model=model)

        prompt = build_reading_prompt(result_dict, depth=depth)

        if depth == "standard":
            system_prompt = (
                "你是一位简洁务实的命理分析师。用通俗易懂的语言给出关键发现和实用建议。"
                "不要罗列术法名称和术语，直接告诉用户：整体好不好、哪里好、哪里要留心、现在该做什么。"
                "使用 Markdown 格式，禁用 emoji。报告控制在 800 字以内。"
            )
            max_tokens = 1500
        else:
            system_prompt = (
                "你是一位严谨的命理分析师，融合中西12种术法进行交叉验证解读。"
                "你的报告风格是「古籍×仪器」：既有古籍的典雅汉字，又有仪器的精确刻度感。"
                "使用 Markdown 格式输出，段落间适当空行。"
                "禁止使用 emoji 字符。"
            )
            max_tokens = 4096

        llm_output = llm_client.complete(
            system=system_prompt, user=prompt, max_tokens=max_tokens,
        )

        if not llm_output or len(llm_output.strip()) < 80:
            log.warning("LLM %s output too short, falling back", depth)
            if depth == "premium":
                return _generate_data_driven_mock(result_dict)
            return None

        from .llm_prompt import check_llm_output
        safety = check_llm_output(llm_output)
        if safety.get("needs_softening"):
            llm_output = safety.get("softened_text", llm_output)

        log.info("LLM %s report generated: %d chars", depth, len(llm_output))
        return llm_output

    except Exception as e:
        log.warning("LLM %s generation failed: %s, using fallback", depth, e)
        if depth == "premium":
            try:
                return _generate_data_driven_mock(result_dict)
            except Exception:
                pass
        return None


def _tone_level(sup_total: int, warn_total: int) -> str:
    """根据 tally_by_scope 累计计票推断整体基调(替代旧 0-100 score 阈值)。

    very_positive : sup_total >= 3 法支持 且 warn_total == 0
    positive      : sup_total >  warn_total 且 warn_total == 0
    cautious      : warn_total >= 3 法警示 且 sup_total == 0
    negative      : warn_total >  sup_total 且 sup_total == 0
    mixed         : 双方均有
    neutral       : 双方均 0
    """
    if sup_total == 0 and warn_total == 0:
        return "neutral"
    if sup_total >= 3 and warn_total == 0:
        return "very_positive"
    if warn_total >= 3 and sup_total == 0:
        return "cautious"
    if sup_total > warn_total and warn_total == 0:
        return "positive"
    if warn_total > sup_total and sup_total == 0:
        return "negative"
    return "mixed"


def _generate_data_driven_mock(result_dict: dict[str, Any]) -> str:
    """无 API Key 时生成数据驱动的深度报告。

    面向普通用户：白话解读 + 实操建议为主，术法细节折叠为附录。
    不再包含免责声明（由前端组件统一渲染）。
    """
    intent = result_dict.get("intent", {})
    validation = result_dict.get("validation", {})
    signals = result_dict.get("signals", [])
    methods = result_dict.get("methods_used", [])
    question = intent.get("question", "")
    goal_label = intent.get("goal_label", "综合")
    tally = validation.get("tally_by_scope") or {}
    sup_total = sum(t.get("strong_support", 0) + t.get("weak_support", 0) for t in tally.values())
    warn_total = sum(t.get("strong_warn", 0) + t.get("weak_warn", 0) for t in tally.values())

    pos_sigs = sorted(
        [s for s in signals if s.get("polarity") == "positive"],
        key=lambda s: s.get("strength", 0), reverse=True,
    )
    neg_sigs = sorted(
        [s for s in signals if s.get("polarity") == "negative"],
        key=lambda s: s.get("strength", 0), reverse=True,
    )

    METHOD_ZH: dict[str, str] = {
        "bazi_v2": "八字", "ziwei": "紫微", "qimen": "奇门",
        "liuyao": "六爻", "meihua": "梅花", "fengshui": "风水",
        "bazhai": "八宅", "xuankong": "玄空", "western": "占星",
        "vedic": "吠陀", "tarot": "塔罗", "numerology": "数理",
        "liuren": "大六壬", "xiaoliuren": "小六壬", "tieban": "铁板神数",
        "lenormand": "雷诺曼", "hepan": "合盘",
    }
    DOMAIN_ZH: dict[str, str] = {
        "self_life": "整体格局", "career": "事业", "wealth": "财运",
        "relationship": "感情", "health": "健康", "decision": "决策",
        "timing": "时机", "home_fengshui": "居家",
        "general": "综合", "monthly": "月运", "yearly": "年运",
    }
    SIGNAL_ZH: dict[str, str] = {
        "short_term_caution": "短期内需谨慎行事",
        "long_term_potential": "长期来看有发展空间",
        "decision_delay": "眼下时机还不够成熟",
        "environment_support": "周围环境较为有利",
        "general_reference": "仅供参考的温和信号",
        "noble_help": "可能会遇到愿意帮你的人",
        "career_pressure": "工作上有些压力",
        "career_independence": "比较适合自己干",
        "marriage_stability": "感情基础比较稳固",
        "relationship_attraction": "近期桃花运不错",
        "timing_transition": "正处在一个转换期",
        "layout_risk": "空间布局上有些地方可能需要调整",
        "direction_benefit": "方位选择上有利好",
        "wealth_opportunity": "财务方面有机会",
        "health_reflection": "身体方面需要多加留意",
    }

    # ── 领域分组 ──
    domain_sigs: dict[str, list[dict]] = {}
    for s in signals:
        domain_sigs.setdefault(s["domain"], []).append(s)

    domain_order = ["self_life", "career", "wealth", "relationship", "decision", "timing", "home_fengshui", "health"]

    # 找出用户最关心的领域（从 question 和 intent 推断）
    primary_domain = intent.get("goal", "self_life")

    lines: list[str] = []

    # ═══ 标题 ═══
    lines.append(f"# {goal_label} · 深度分析")
    lines.append("")
    if question:
        lines.append(f"> 您问的是：「{question}」")
    lines.append(f"> 综合{len(methods)}种术法交叉验证 · {sup_total} 法支持 / {warn_total} 法警示(无单一分数)")
    lines.append("")

    # ═══ 一、白话总览 ═══
    lines.append("## 一句话总结")
    lines.append("")
    tone = _tone_level(sup_total, warn_total)
    if tone == "very_positive":
        lines.append("总体来看，当前运势处于一个**比较有利的阶段**。多个不同的分析角度都给出了积极信号，")
        lines.append("说明这段时间适合推进重要事项，把握住机会的概率比较大。")
    elif tone == "positive":
        lines.append("总体来看，当前运势**平稳中带有机会**。没有特别明显的风险信号，但也不是一切都顺风顺水。")
        lines.append("适合稳扎稳打地推进计划，不必急于求成。")
    elif tone in ("mixed", "neutral"):
        lines.append("总体来看，当前运势**有些复杂**。好消息和需要注意的方面同时存在，不同的分析角度之间也有不同看法。")
        lines.append("建议不要做太大决定，先把情况看清楚再说。")
    else:  # cautious / negative
        lines.append("总体来看，当前运势**需要多留个心眼**。多个分析角度都提示需要注意的地方，")
        lines.append("建议这段时间以稳为主，先把重要决策放一放。")
    lines.append("")

    # ═══ 二、你最关心的 ═══
    primary_name = DOMAIN_ZH.get(primary_domain, "整体")
    primary_sigs = domain_sigs.get(primary_domain, [])
    if not primary_sigs:
        # fallback: use the domain with most signals
        if domain_sigs:
            primary_domain = max(domain_sigs, key=lambda d: len(domain_sigs[d]))
            primary_name = DOMAIN_ZH.get(primary_domain, primary_domain)
            primary_sigs = domain_sigs.get(primary_domain, [])

    lines.append(f"## 关于「{primary_name}」")
    lines.append("")

    dom_pos = sum(s["strength"] for s in primary_sigs if s["polarity"] == "positive")
    dom_neg = sum(s["strength"] for s in primary_sigs if s["polarity"] == "negative")
    dom_pos_n = sum(1 for s in primary_sigs if s["polarity"] == "positive")
    dom_neg_n = sum(1 for s in primary_sigs if s["polarity"] == "negative")

    # 白话解释
    _append_plain_explanation(lines, primary_domain, primary_sigs, dom_pos, dom_neg, dom_pos_n, dom_neg_n, METHOD_ZH, SIGNAL_ZH)
    lines.append("")

    # 具体建议
    _append_domain_advice(lines, primary_domain, primary_sigs, pos_sigs, neg_sigs, METHOD_ZH, SIGNAL_ZH)
    lines.append("")

    # ═══ 三、其他方面 ═══
    other_domains = [d for d in domain_order if d in domain_sigs and d != primary_domain]
    if other_domains:
        lines.append("## 其他方面简览")
        lines.append("")
        for dom in other_domains[:5]:
            sigs = domain_sigs[dom]
            dom_name = DOMAIN_ZH.get(dom, dom)
            pos_n = sum(1 for s in sigs if s["polarity"] == "positive")
            neg_n = sum(1 for s in sigs if s["polarity"] == "negative")
            pos_strength = sum(s["strength"] for s in sigs if s["polarity"] == "positive")
            neg_strength = sum(s["strength"] for s in sigs if s["polarity"] == "negative")

            lines.append(f"**{dom_name}**：")
            if pos_n > neg_n and pos_strength > neg_strength:
                lines.append(f"整体偏顺，{pos_n}个术法给出积极信号。不必太操心这个方面。")
            elif neg_n > pos_n and neg_strength > pos_strength:
                lines.append(f"需要稍微留意一下，{neg_n}个术法提示可能有挑战。但也别太紧张。")
            else:
                lines.append("信号比较中性，说明这个方面当前没有太大波澜，维持现状就好。")
            lines.append("")
    else:
        lines.append("## 其他方面")
        lines.append("")
        lines.append("本次分析中其他领域未产生有效信号，建议补充出生信息或具体问题后重新分析。")
        lines.append("")

    # ═══ 四、需要注意的 ═══
    risks = result_dict.get("validation", {}).get("risks", [])
    conflict_list = result_dict.get("validation", {}).get("conflicts", [])
    if risks or conflict_list or neg_sigs:
        lines.append("## 需要注意的地方")
        lines.append("")
        if neg_sigs[:2]:
            for s in neg_sigs[:2]:
                lines.append(f"- **{SIGNAL_ZH.get(s['signal_key'], s['signal_key'])}**"
                             f"（{METHOD_ZH.get(s['method'], s['method'])}提醒，{DOMAIN_ZH.get(s['domain'], s['domain'])}方面）")
        if risks:
            for r in risks[:2]:
                r_zh = str(r)
                for en_key, zh_key in SIGNAL_ZH.items():
                    r_zh = r_zh.replace(en_key, zh_key)
                lines.append(f"- {r_zh}")
        if conflict_list:
            for c in conflict_list[:1]:
                if c.get("resolution"):
                    lines.append(f"- {c['resolution']}")
        lines.append("")

    # ═══ 五、时间建议 ═══
    timing = result_dict.get("validation", {}).get("timing")
    if timing and timing.get("summary"):
        lines.append("## 时间上的建议")
        lines.append("")
        lines.append(timing.get("summary", ""))
        short_n = timing.get("short_term_signals", 0)
        long_n = timing.get("long_term_signals", 0)
        if short_n > long_n:
            lines.append("近期（1-3个月内）的变化比较关键，建议多留意这段时间的动向。")
        elif long_n > short_n:
            lines.append("信号偏长期，不用太在意短期内的起起伏伏，把眼光放长远一些。")
        lines.append("")

    # ═══ 六、你可以做这些 ═══
    advice = result_dict.get("validation", {}).get("action_advice", [])
    lines.append("## 现在可以做的事")
    lines.append("")
    # 从数据中生成有针对性的建议
    _append_practical_advice(lines, primary_domain, primary_sigs, pos_sigs, neg_sigs, tone, advice, METHOD_ZH, SIGNAL_ZH, DOMAIN_ZH)
    lines.append("")

    # ═══ 七、你还想了解什么 ═══
    lines.append("## 还想了解什么？")
    lines.append("")
    lines.append(f"上面是基于{len(methods)}种术法的综合分析。如果你觉得某个方面还想深入了解，可以继续追问，比如：")
    lines.append("")
    other_qs = _suggest_followups(primary_domain, domain_sigs, DOMAIN_ZH)
    for q in other_qs:
        lines.append(f"- {q}")
    lines.append("")

    return "\n".join(lines)


# ── 辅助函数：白话解读 + 具体建议 ────────────────────────────────────────────────

def _append_plain_explanation(
    lines: list[str], domain: str, sigs: list[dict],
    dom_pos: float, dom_neg: float, pos_n: int, neg_n: int,
    METHOD_ZH: dict, SIGNAL_ZH: dict,
) -> None:
    """为某个领域生成白话解读段落。"""
    if domain == "career":
        if dom_pos > dom_neg * 1.5:
            lines.append("从目前的信息来看，你的事业发展**势头不错**。八字和紫微等传统术数，")
            lines.append("加上西方占星的角度，都比较一致地指向向上的趋势。")
            lines.append("想跳槽或者谈升职的话，这段时间是个不错的窗口期。")
        elif dom_neg > dom_pos * 1.5:
            lines.append("目前事业方面**建议稳一稳**。多个分析角度都提示当前阶段挑战多于机会，")
            lines.append("工作上可能会感到压力比较大。不建议现在裸辞或者做太大的职业变动，")
            lines.append("先把手头的事情做好，等风向转好再说。")
        elif pos_n > 0 or neg_n > 0:
            lines.append("事业方面，好消息和需要留意的信号**同时存在**。")
            lines.append("有的术法看到机会，有的提醒注意压力。")
            lines.append("建议你对机会保持开放心态，但也不要轻易放弃现有的积累。")
        else:
            lines.append("事业方面的信号比较中性，没有特别明显的好坏指向。")
            lines.append("说明当前可能处在一个过渡期，不必太焦虑。")
    elif domain == "wealth":
        if dom_pos > dom_neg * 1.5:
            lines.append("财运方面**看起来不错**。传统的八字和现代的占星分析在这一点上意见比较一致。")
            lines.append("这段时间可以考虑稳健的理财规划，注意你身边出现的机会。")
        elif dom_neg > dom_pos * 1.5:
            lines.append("财运方面**建议保守一些**。目前不是适合大手笔投资或者冒险理财的时机，")
            lines.append("把重点放在储蓄和稳定收入上更稳妥。")
        else:
            lines.append("财运方面，大方向是**求稳**。没有大的风险但也没有暴富的信号。")
            lines.append("该花的别省，该省的别花，保持平常心就好。")
    elif domain == "relationship":
        if dom_pos > dom_neg * 1.5:
            lines.append("感情方面**运势不错**。紫微和占星在桃花和人缘上都给出了比较积极的信号。")
            lines.append("单身的话，接下来几个月遇到有意思的人的概率比较高。")
            lines.append("已经在关系中的，这段时间沟通会比较顺畅。")
        elif dom_neg > dom_pos * 1.5:
            lines.append("感情方面可能**需要多一些耐心**。这段时间容易因为小事产生摩擦，")
            lines.append("建议少一点较真、多一点包容。单身的不用着急，先把注意力放在自己身上。")
        else:
            lines.append("感情方面，整体基调是**平淡中带着小温暖**。")
            lines.append("没有大的波折也没有特别轰烈的桃花，但也是一种难得的安稳。")
    elif domain == "decision":
        if dom_pos > dom_neg * 1.5:
            lines.append("现在**比较适合做决定**。多个术法的信号都提示方向是积极的，")
            lines.append("内心的判断和外部的环境比较一致，可以放心推进。")
        elif dom_neg > dom_pos * 1.5:
            lines.append("现在**不太适合做大决定**。各方面的信号都提示还有看不清的地方，")
            lines.append("不如先放一放，等信息更明朗了再说。")
        else:
            lines.append("决策方面的信号偏向中性，说明**想清楚比想得快更重要**。")
            lines.append("如果你已经有了倾向性的判断，可以相信自己的直觉。如果没有，也不要着急。")
    elif domain == "health":
        if dom_neg > dom_pos:
            lines.append("身体健康方面**需要多加注意**。不是说一定有什么问题，而是现在是一个")
            lines.append("容易被忽略的时期，压力积累或者作息不规律的影响容易被低估。")
            lines.append("定期的体检和规律的运动比平时更重要。")
        else:
            lines.append("健康方面的信号比较平和。继续保持目前的生活方式就好。")
    elif domain == "self_life":
        if dom_pos > dom_neg * 1.5:
            lines.append("整体格局**相当不错**。说明你现在的状态和方向是对的，")
            lines.append("周围的环境也在支持你往前走。保持信心，继续做你正在做的事。")
        elif dom_neg > dom_pos * 1.5:
            lines.append("整体格局**有些逆风**，但不是不能走。就像爬山遇到大雾天，")
            lines.append("虽然看不清路，但脚下还是实的。建议放慢脚步，多回头看走过的路。")
        else:
            lines.append("整体格局**温和中性**。这个阶段不太适合折腾，适合把基础打牢。")
            lines.append("就像春天播种，虽然看不到马上开花，但根在往下扎。")
    else:
        lines.append("这个方面目前信号比较温和，没有太多需要特别关注的地方。")


def _append_domain_advice(
    lines: list[str], domain: str, sigs: list[dict],
    pos_sigs: list[dict], neg_sigs: list[dict],
    METHOD_ZH: dict, SIGNAL_ZH: dict,
) -> None:
    """为某个领域生成具体建议。"""
    lines.append("**具体来说：**")
    lines.append("")
    if domain == "career":
        if any(s["signal_key"] == "career_pressure" for s in sigs):
            lines.append("1. 当前岗位上的压力是真实存在的，但**不一定是坏事**——有时候压力恰恰是你成长的信号。")
            lines.append("   建议先跟直属领导做一次坦诚的沟通，把期望值和你的实际工作量对齐。")
        if any(s["signal_key"] == "career_independence" for s in sigs):
            lines.append("2. 多个角度都提示你**有独立发展的潜质**。如果心里一直有副业或者创业的想法，")
            lines.append("   可以从现在开始做一些小的尝试，而不是立刻完全切换轨道。")
        if any(s["signal_key"] == "long_term_potential" for s in sigs):
            lines.append("3. 长期来看前景不错，**不用太纠结眼前的一城一池**。把当前岗位当成一个跳板，")
            lines.append("   有计划地积累行业人脉和核心能力。")
        if not any(s["signal_key"] in ("career_pressure", "career_independence", "long_term_potential") for s in sigs):
            lines.append("1. 如果没有明确的不满意，**建议不要为了换而换**。在当前岗位上再深耕半年到一年。")
            lines.append("2. 留意你身边那些愿意给你反馈和建议的人，他们可能就是你下一步的关键助力。")
    elif domain == "wealth":
        if any(s["signal_key"] == "wealth_opportunity" for s in sigs):
            lines.append("1. 财运方面有不错的机会信号，但**不是叫你立刻去梭哈**。先做功课，再做决定。")
            lines.append("2. 如果有正在考虑的投资或理财方案，接下来两个月是比较适合推进的时期。")
        else:
            lines.append("1. 现阶段**以积累为主**，不适合大额投机。把消费习惯梳理一下比找新的赚钱路子更实际。")
            lines.append("2. 年内如果一定要做财务上的大决定（比如买房、换车），建议先咨询专业人士。")
    elif domain == "relationship":
        if any(s["signal_key"] == "relationship_attraction" for s in sigs):
            lines.append("1. 桃花运好的时候，**多出去见人**。不是说一定要谈恋爱，但拓展社交圈对你后续的发展有帮助。")
            lines.append("2. 已经在关系中的，这段时间可以安排一些**有仪式感的共同体验**——比如一起去个没去过的地方。")
        else:
            lines.append("1. 感情方面不需要强求。**把注意力放在自己身上**，好的人会在你状态最好的时候自然出现。")
            lines.append("2. 如果已经在一段关系里，建议多一些日常的、不经意的关心，比大张旗鼓的表白更有效。")
    elif domain == "decision":
        lines.append("1. 重大决定建议**做个简单的清单**：把好处和风险分别写下来，看看哪些是你真正在意的。")
        lines.append("2. **别一个人扛**。找一两个你信任的人聊一聊，他们的角度可能会让你看到不一样的画面。")
    elif domain == "health":
        lines.append("1. 把**睡眠**放在第一位。睡好了，很多你以为的'大事'都会在第二天变小。")
        lines.append("2. 如果已经很久没体检了，**近期安排一次**。重点查一下你平时容易忽略的项目。")
    elif domain == "self_life":
        lines.append("1. 你现在走的大的方向**是对的**，不用怀疑。但细节上可以做一些微调。")
        lines.append("2. 找一件你一直想做但总找理由拖着的小事，**这周就去做**。不用大，做了就行。")
    else:
        lines.append("1. 先稳住现有的。**不折腾就是最好的策略**。")
        lines.append("2. 多观察、多记录。过段时间回头看，你会发现自己对事物的判断力在悄悄提升。")


def _append_practical_advice(
    lines: list[str], primary_domain: str, primary_sigs: list[dict],
    pos_sigs: list[dict], neg_sigs: list[dict],
    tone: str,
    advice: list, METHOD_ZH: dict, SIGNAL_ZH: dict, DOMAIN_ZH: dict,
) -> None:
    """生成实操建议列表 — tone 来自 tally_by_scope, 不再用 score。"""
    count = 0
    # 过滤掉太泛的样板建议（"结合交叉验证"、"咨询专业人士"等）
    GENERIC_PATTERNS = [
        "结合多个术法", "交叉验证", "咨询相关专业", "传统文化视角",
        "全面评估后再做决策", "以上建议基于",
    ]
    if advice:
        for a in advice[:3]:
            a_zh = str(a)
            # 跳过过于泛泛的样板建议
            if any(p in a_zh for p in GENERIC_PATTERNS):
                continue
            for en_key, zh_key in SIGNAL_ZH.items():
                a_zh = a_zh.replace(en_key, zh_key)
            count += 1
            lines.append(f"{count}. {a_zh}")

    # 通用建议补齐(基于 tone 字符串, 替代旧 0-100 score 阈值)
    if count < 3:
        if tone in ("very_positive", "positive"):
            if count < 3:
                count += 1; lines.append(f"{count}. 现在是适合行动的时间窗口，想做但一直犹豫的事，可以考虑往前推一步")
            if count < 3:
                count += 1; lines.append(f"{count}. 多跟朋友或同行交流，你的好状态会感染别人，也会吸引更多好机会")
        elif tone == "mixed":
            if count < 3:
                count += 1; lines.append(f"{count}. 保持现状，同时留意身边的小机会。有时候一个小突破能带来意想不到的大变化")
            if count < 3:
                count += 1; lines.append(f"{count}. 把大的目标拆成小的步骤，每天推进一点点，三个月后回头看会有惊喜")
        elif tone == "neutral":
            if count < 3:
                count += 1; lines.append(f"{count}. 这段时间不太适合做大决定，但很适合做准备——查资料、找人聊、做调研")
            if count < 3:
                count += 1; lines.append(f"{count}. 注意休息和调节，人在焦虑的时候做出的判断，事后看往往不够好")
        else:  # cautious / negative
            if count < 3:
                count += 1; lines.append(f"{count}. 先稳住基本盘：保证收入来源、维护好关键关系、照顾好身体健康")
            if count < 3:
                count += 1; lines.append(f"{count}. 跟值得信赖的人多沟通，不要一个人把所有压力都扛着")


def _suggest_followups(primary_domain: str, domain_sigs: dict, DOMAIN_ZH: dict) -> list[str]:
    """根据已有数据生成追问建议。"""
    suggestions: list[str] = []
    if primary_domain != "career":
        suggestions.append("「我最近的事业运势怎么样，适不适合跳槽？」")
    if primary_domain != "wealth":
        suggestions.append("「最近财运如何，有没有好的投资方向？」")
    if primary_domain != "relationship":
        suggestions.append("「我的感情运势怎么样？」")
    suggestions.append("「能帮我看看明年的整体运势吗？」")
    return suggestions[:3]


def _build_birth(bm: BirthModel) -> Birth:
    """将 API 的 BirthModel 转为内部 Birth。"""
    return Birth(
        year=bm.year,
        month=bm.month,
        day=bm.day,
        hour=bm.hour,
        minute=bm.minute,
        gender=bm.gender,
        calendar=bm.calendar,
        lat=bm.lat,
        lng=bm.lng,
        tz=bm.tz,
        is_leap_month=bm.is_leap_month,
    )


def _default_birth() -> Birth:
    """默认出生信息（当用户未提供时）。"""
    import datetime
    now = datetime.datetime.now()
    return Birth(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=12,
        minute=0,
        gender="unspecified",
        calendar="gregorian",
        tz="Asia/Shanghai",
    )


def _reality_to_dict(reality) -> dict[str, Any]:
    """将 RealityResult dataclass 转为 dict，供 API 序列化。"""
    if reality is None:
        return {}
    from .reality import RealityResult
    if not isinstance(reality, RealityResult):
        return {}
    return {
        "has_warnings": reality.has_warnings,
        "core_conclusion": reality.core_conclusion,
        "dimension_judgments": reality.dimension_judgments,
        "adjusted_advice": reality.adjusted_advice,
        "warnings": [
            {
                "dimension": w.dimension,
                "severity": w.severity,
                "message": w.message,
                "signal_adjusted": w.signal_adjusted,
            }
            for w in reality.warnings
        ],
    }
