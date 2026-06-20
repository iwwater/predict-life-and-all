"""Sprint 1.6 — 现实条件校正引擎 (声明式 rules + 安全转介)。

设计:
  1. CONSTRAINT_RULES 声明式: 每条规则 (trigger, severity, msg, advice) 独立可关
  2. SAFETY_REFERRALS 表: 健康/法财/法律 关键词 → SAFE-002/003/004 降级
  3. RealityConstraintEngine.evaluate() 主入口保持兼容
  4. 自动转介: 用户问题含医疗/投资/法律关键词 → 加 safety_flag, 不出命理结论

参考:
  - 心理咨询 initial interview 的 referral 模式: 严重问题直接转介专业
  - 临床心理学的 triage 阈值 (sprint 1.6 不做临床, 只做"建议就医/咨询律师"提示)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from .schema import DivinationSignal, RealityConstraints

Operator = Literal["lt", "lte", "eq", "gte", "gt", "in", "is_true", "is_false", "is_none"]


# ── 规则数据类 ────────────────────────────────────────────────────────────

@dataclass
class ConstraintRule:
    """单条声明式约束规则。

    trigger.field      — RealityConstraints 字段名
    trigger.op         — 比较算子
    trigger.value      — 比较值
    severity           — "low" | "medium" | "high"
    message            — 警告文本 (可用 {field} 占位)
    advice             — 调整后建议 (可用 {field} 占位)
    requires_signal    — 仅在命理信号满足某条件时触发 (None = 不限)
    id                 — 稳定 ID
    """
    id: str
    field: str
    op: Operator
    value: Any
    severity: Literal["low", "medium", "high"]
    message: str
    advice: str
    requires_signal: Callable[[list[DivinationSignal]], bool] | None = None

    def matches(self, constraints: RealityConstraints) -> bool:
        """规则是否触发。"""
        v = getattr(constraints, self.field, None)
        if self.op == "lt":
            return v is not None and v < self.value
        if self.op == "lte":
            return v is not None and v <= self.value
        if self.op == "gt":
            return v is not None and v > self.value
        if self.op == "gte":
            return v is not None and v >= self.value
        if self.op == "eq":
            return v == self.value
        if self.op == "in":
            return v in self.value
        if self.op == "is_true":
            return v is True
        if self.op == "is_false":
            return v is False
        if self.op == "is_none":
            return v is None
        return False


# ── 规则表 ────────────────────────────────────────────────────────────────

# 触发条件: 通常要求有正向命理信号时, 现实约束才"起冲突" — 无信号不强警告
def _has_career_positive(signals: list[DivinationSignal]) -> bool:
    return any(
        s.polarity == "positive" and s.strength > 0.5
        and s.domain in ("career", "wealth")
        for s in signals
    )

def _has_wealth_strong(signals: list[DivinationSignal]) -> bool:
    return any(
        s.polarity == "positive" and s.strength > 0.6
        and s.domain == "wealth"
        for s in signals
    )

def _has_decision_positive(signals: list[DivinationSignal]) -> bool:
    return any(
        s.polarity == "positive" and s.strength > 0.6
        and s.domain == "decision"
        for s in signals
    )

def _has_health_pressure(signals: list[DivinationSignal]) -> bool:
    return any(
        s.polarity == "negative" and s.strength > 0.4
        and s.domain == "health"
        for s in signals
    )

def _has_dependents_pressure(signals: list[DivinationSignal]) -> bool:
    return any(
        s.polarity == "negative" and s.strength > 0.4
        and s.domain in ("career", "wealth")
        for s in signals
    )


CONSTRAINT_RULES: list[ConstraintRule] = [
    # ── 现金储备 ──
    ConstraintRule(
        id="cash_severe_shortage",
        field="cash_reserve_months", op="lt", value=1,
        severity="high",
        message="现金储备严重不足（{cash_reserve_months}个月）",
        advice="短期内不宜做重大变动, 优先积累现金储备",
        requires_signal=_has_career_positive,
    ),
    ConstraintRule(
        id="cash_low",
        field="cash_reserve_months", op="lte", value=3,
        severity="medium",
        message="现金储备偏低（{cash_reserve_months}个月）",
        advice="确认新收入来源前, 不建议仓促离职或创业",
        requires_signal=_has_career_positive,
    ),
    # ── 合同状态 ──
    ConstraintRule(
        id="contract_only_verbal",
        field="has_formal_contract", op="is_false", value=None,
        severity="high",
        message="仅有口头意向, 尚无正式合同",
        advice="建议等正式合同签署后再做离职决定",
        requires_signal=_has_career_positive,
    ),
    # ── 健康 ──
    ConstraintRule(
        id="health_poor",
        field="health_status", op="eq", value="poor",
        severity="high",
        message="当前健康状况较差",
        advice="建议先将健康恢复到 fair 水平再考虑重大事业变动",
    ),
    ConstraintRule(
        id="health_fair",
        field="health_status", op="eq", value="fair",
        severity="medium",
        message="当前健康状况一般",
        advice="变动期间保持规律作息, 避免过度劳累",
    ),
    # ── 资质 ──
    ConstraintRule(
        id="qualification_missing",
        field="has_qualification", op="is_false", value=None,
        severity="medium",
        message="当前尚不具备目标方向所需资质",
        advice="建议先获取必要资质（证书/许可）, 再进入新领域",
        requires_signal=_has_career_positive,
    ),
    # ── 家庭依赖 ──
    ConstraintRule(
        id="dependents_with_weak_wealth",
        field="has_dependents", op="is_true", value=None,
        severity="high",
        message="有抚养责任, 且当前财运信号偏弱",
        advice="变动方案需优先考虑家庭保障, 不宜冒进",
        requires_signal=_has_dependents_pressure,
    ),
    ConstraintRule(
        id="dependents_general",
        field="has_dependents", op="is_true", value=None,
        severity="low",
        message="有家庭依赖",
        advice="变动决定需考虑家庭安排, 确保不严重影响生活质量",
    ),
    # ── 备选方案 ──
    ConstraintRule(
        id="no_backup_plan",
        field="has_backup_plan", op="is_false", value=None,
        severity="medium",
        message="命理显示有机会但无备选退路, 高风险",
        advice="不要把所有资源押在单一方向, 同时建立备选退路",
        requires_signal=_has_decision_positive,
    ),
    # ── 搬迁/通勤 ──
    ConstraintRule(
        id="commute_rejected",
        field="commute_tolerance", op="eq", value="reject",
        severity="high",
        message="目标地点超出通勤接受范围, 需要搬迁",
        advice="如必须搬迁, 建议先确认新地点的住房和工作条件再决定",
        requires_signal=_has_career_positive,
    ),
]


# ── 安全转介 (SAFE-002/003/004) ───────────────────────────────────────

# 关键词从 safety.py 复用 (避免重复定义)
from .safety import (
    INVESTMENT_DOWNGRADE_MSG,
    LEGAL_DOWNGRADE_MSG,
    MEDICAL_DOWNGRADE_MSG,
    INVESTMENT_KEYWORDS,
    LEGAL_KEYWORDS,
    MEDICAL_KEYWORDS,
)


@dataclass
class SafetyReferral:
    """单一领域转介规则。"""
    flag: str  # safety_flag 名 (medical_downgrade / investment_downgrade / legal_downgrade)
    keywords: tuple[str, ...]
    message: str


SAFETY_REFERRALS: list[SafetyReferral] = [
    SafetyReferral(
        flag="medical_downgrade",
        keywords=tuple(MEDICAL_KEYWORDS),
        message=MEDICAL_DOWNGRADE_MSG,
    ),
    SafetyReferral(
        flag="investment_downgrade",
        keywords=tuple(INVESTMENT_KEYWORDS),
        message=INVESTMENT_DOWNGRADE_MSG,
    ),
    SafetyReferral(
        flag="legal_downgrade",
        keywords=tuple(LEGAL_KEYWORDS),
        message=LEGAL_DOWNGRADE_MSG,
    ),
]


# ── 输出模型 ────────────────────────────────────────────────────────────

@dataclass
class RealityWarning:
    """单项现实警告。"""
    dimension: str
    severity: str
    message: str
    signal_adjusted: str | None = None
    rule_id: str | None = None  # Sprint 1.6: 关联规则 ID


@dataclass
class RealityResult:
    """现实条件校正输出。"""
    has_warnings: bool
    warnings: list[RealityWarning]
    adjusted_advice: list[str]
    core_conclusion: str
    dimension_judgments: dict[str, str] = field(default_factory=dict)
    safety_flags: list[str] = field(default_factory=list)  # Sprint 1.6
    safety_messages: list[str] = field(default_factory=list)


# ── 引擎主入口 ──────────────────────────────────────────────────────────

class RealityConstraintEngine:
    """现实条件校正引擎 (Sprint 1.6: 声明式 + 安全转介)。"""

    SIGNAL_TO_CONSTRAINT_MAP = {
        # 保留向后兼容 — 旧字段映射
        "career_independence": ["cash_reserve_months", "has_backup_plan"],
        "career_pressure": ["cash_reserve_months", "has_dependents"],
        "wealth_opportunity": ["cash_reserve_months", "has_formal_contract"],
        "relationship_attraction": ["has_dependents"],
        "marriage_stability": ["has_dependents"],
        "decision_delay": ["has_backup_plan"],
        "long_term_potential": ["health_status", "has_qualification"],
    }

    def evaluate(
        self,
        signals: list[DivinationSignal],
        constraints: RealityConstraints | None,
        question: str | None = None,  # Sprint 1.6: 用于安全转介关键词扫描
        domain: str = "general",
    ) -> RealityResult:
        """主评估入口。

        Args:
            signals: 标准化后的多法信号列表
            constraints: 现实条件约束 (可 None)
            question: 原始问题 (用于扫描 SAFE 关键词)
            domain: 当前判断领域

        Returns:
            RealityResult
        """
        warnings: list[RealityWarning] = []
        judgments: dict[str, str] = {}
        safety_flags: list[str] = []
        safety_messages: list[str] = []

        # ── 1. 声明式 rules 评估 ──
        if constraints is not None:
            for rule in CONSTRAINT_RULES:
                if not rule.matches(constraints):
                    continue
                if rule.requires_signal is not None and not rule.requires_signal(signals):
                    continue
                # 字段格式化
                try:
                    field_val = getattr(constraints, rule.field, None)
                    msg = rule.message.format(**{rule.field: field_val})
                except (KeyError, IndexError):
                    msg = rule.message
                warnings.append(RealityWarning(
                    dimension=rule.field,
                    severity=rule.severity,
                    message=msg,
                    signal_adjusted=rule.advice,
                    rule_id=rule.id,
                ))
                judgments[rule.field] = msg

        # ── 2. 安全转介 (Sprint 1.6 新) ──
        if question:
            for referral in SAFETY_REFERRALS:
                for kw in referral.keywords:
                    if kw in question:
                        if referral.flag not in safety_flags:
                            safety_flags.append(referral.flag)
                            safety_messages.append(referral.message)
                        break  # 一个 referral flag 只加一次

        # ── 3. 调整建议 + 核心结论 ──
        adjusted_advice = self._build_adjusted_advice(warnings)
        core_conclusion = self._build_core_conclusion(warnings)

        return RealityResult(
            has_warnings=len(warnings) > 0,
            warnings=warnings,
            adjusted_advice=adjusted_advice,
            core_conclusion=core_conclusion,
            dimension_judgments=judgments,
            safety_flags=safety_flags,
            safety_messages=safety_messages,
        )

    def _build_adjusted_advice(self, warnings: list[RealityWarning]) -> list[str]:
        advice: list[str] = []
        for w in warnings:
            if w.severity == "high" and w.signal_adjusted:
                advice.append(w.signal_adjusted)
        for w in warnings:
            if w.severity == "medium" and w.signal_adjusted:
                advice.append(w.signal_adjusted)
        if not advice:
            advice.append("现实条件暂无明显阻碍, 可按命理建议推进。")
        return advice

    def _build_core_conclusion(self, warnings: list[RealityWarning]) -> str:
        if not warnings:
            return "现实条件支持当前方向, 可以积极推进。"
        high = [w for w in warnings if w.severity == "high"]
        if high:
            return f"命理层信号有利, 但现实条件存在 {len(high)} 项高风险, 需谨慎处理。"
        return f"命理层信号有利, 但现实条件有 {len(warnings)} 项需关注, 建议审慎推进。"


# ── 便捷 API ─────────────────────────────────────────────────────────

def check_safety_referral(question: str) -> list[str]:
    """仅检查问题是否触发安全转介 (不跑完整 reality 评估)。

    Returns:
        list of triggered safety flag names
    """
    flags: list[str] = []
    for r in SAFETY_REFERRALS:
        for kw in r.keywords:
            if kw in question:
                if r.flag not in flags:
                    flags.append(r.flag)
                break
    return flags


def list_active_rules() -> list[dict[str, Any]]:
    """列出所有启用规则 (供 admin/debug)。"""
    return [
        {
            "id": r.id,
            "field": r.field,
            "op": r.op,
            "value": r.value,
            "severity": r.severity,
            "message": r.message,
        }
        for r in CONSTRAINT_RULES
    ]
