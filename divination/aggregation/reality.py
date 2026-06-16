"""现实条件校正引擎 — 方案 §十四。

将多法信号与用户现实条件对比，发现"命理层说适合/现实层说不足"的
接地气结论，输出警告和调整后的行动建议。

Usage:
    from divination.aggregation.reality import RealityConstraintEngine, RealityResult
    engine = RealityConstraintEngine()
    result = engine.evaluate(signals=signals, constraints=constraints, domain=domain)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .schema import DivinationSignal, RealityConstraints


@dataclass
class RealityWarning:
    """单项现实警告。"""
    dimension: str          # cash / contract / commute / health / qualification / dependents / backup
    severity: str           # low / medium / high
    message: str            # 人类可读警告文本
    signal_adjusted: Optional[str] = None  # 调整后的建议文本


@dataclass
class RealityResult:
    """现实条件校正输出。"""
    has_warnings: bool
    warnings: list[RealityWarning]
    # 调整后的行动建议（命理结论 + 现实调整）
    adjusted_advice: list[str]
    # 核心结论：一句话
    core_conclusion: str
    # 各维度判断
    dimension_judgments: dict[str, str] = field(default_factory=dict)


class RealityConstraintEngine:
    """现实条件校正引擎。"""

    # 命理信号维度 → 现实约束维度的映射关系
    SIGNAL_TO_CONSTRAINT_MAP = {
        "career_independence": ["cash_reserve_months", "has_backup_plan"],
        "career_pressure": ["cash_reserve_months", "has_dependents"],
        "career_favorable": ["cash_reserve_months"],
        "wealth_opportunity": ["cash_reserve_months", "has_formal_contract"],
        "relationship_attraction": ["has_dependents"],
        "marriage_stability": ["has_dependents"],
        "decision_delay": ["has_backup_plan"],
        "long_term_potential": ["health_status", "has_qualification"],
    }

    def evaluate(
        self,
        signals: list[DivinationSignal],
        constraints: Optional[RealityConstraints],
        domain: str = "general",
    ) -> RealityResult:
        """主评估入口。

        Args:
            signals: 标准化后的多法信号列表
            constraints: 现实条件约束（可 None）
            domain: 当前判断领域 (career/wealth/relationship/health/decision)
        """
        if constraints is None:
            return self._empty_result()

        warnings: list[RealityWarning] = []
        adjusted_advice: list[str] = []
        judgments: dict[str, str] = {}

        # ── 现金储备判断 ──────────────────────────────────────────
        if constraints.cash_reserve_months is not None:
            judgment, warning = self._evaluate_cash(
                constraints.cash_reserve_months, signals, domain
            )
            judgments["cash"] = judgment
            if warning:
                warnings.append(warning)

        # ── 合同状态判断 ──────────────────────────────────────────
        if constraints.has_formal_contract is not None:
            judgment, warning = self._evaluate_contract(
                constraints.has_formal_contract, signals, domain
            )
            judgments["contract"] = judgment
            if warning:
                warnings.append(warning)

        # ── 通勤/搬迁判断 ─────────────────────────────────────────
        if constraints.target_city and constraints.current_city:
            judgment, warning = self._evaluate_relocation(
                constraints.target_city, constraints.current_city,
                constraints.commute_tolerance, signals, domain
            )
            judgments["relocation"] = judgment
            if warning:
                warnings.append(warning)

        # ── 健康状态判断 ──────────────────────────────────────────
        if constraints.health_status is not None:
            judgment, warning = self._evaluate_health(
                constraints.health_status, signals, domain
            )
            judgments["health"] = judgment
            if warning:
                warnings.append(warning)

        # ── 资质/证书判断 ─────────────────────────────────────────
        if constraints.has_qualification is not None:
            judgment, warning = self._evaluate_qualification(
                constraints.has_qualification, signals, domain
            )
            judgments["qualification"] = judgment
            if warning:
                warnings.append(warning)

        # ── 家庭依赖判断 ──────────────────────────────────────────
        if constraints.has_dependents is not None:
            judgment, warning = self._evaluate_dependents(
                constraints.has_dependents, signals, domain
            )
            judgments["dependents"] = judgment
            if warning:
                warnings.append(warning)

        # ── 备选方案判断 ──────────────────────────────────────────
        if constraints.has_backup_plan is not None:
            judgment, warning = self._evaluate_backup(
                constraints.has_backup_plan, signals, domain
            )
            judgments["backup"] = judgment
            if warning:
                warnings.append(warning)

        # ── 生成调整建议 ──────────────────────────────────────────
        adjusted_advice = self._build_adjusted_advice(warnings, signals, domain)

        # ── 核心结论 ──────────────────────────────────────────────
        core_conclusion = self._build_core_conclusion(warnings, domain)

        return RealityResult(
            has_warnings=len(warnings) > 0,
            warnings=warnings,
            adjusted_advice=adjusted_advice,
            core_conclusion=core_conclusion,
            dimension_judgments=judgments,
        )

    def _empty_result(self) -> RealityResult:
        return RealityResult(
            has_warnings=False,
            warnings=[],
            adjusted_advice=[],
            core_conclusion="",
            dimension_judgments={},
        )

    # ── 子判断 ─────────────────────────────────────────────────────────────────

    def _evaluate_cash(
        self, months: int, signals: list[DivinationSignal], domain: str,
    ) -> tuple[str, RealityWarning | None]:
        """现金储备判断。"""
        # 查找财运相关信号
        wealth_signals = [s for s in signals if "wealth" in s.domain or "career" in s.domain]
        favorable = any(s.polarity == "positive" and s.strength > 0.6 for s in wealth_signals)

        if months <= 1:
            judgment = "现金极度紧张，仅有不到1个月储备"
            warning = RealityWarning(
                dimension="cash",
                severity="high",
                message="现金储备严重不足（不足1个月生活费），建议先保障基本生存再考虑变动。",
                signal_adjusted="短期内不宜做重大变动，优先积累现金储备。",
            )
        elif months <= 3:
            judgment = "现金储备偏低，低于3个月"
            warning = RealityWarning(
                dimension="cash",
                severity="medium",
                message=f"现金储备仅{months}个月，处于风险区间。新机会需确认资金到位时间。",
                signal_adjusted="确认新收入来源前，不建议仓促离职或创业。",
            )
        elif months >= 12 and favorable:
            judgment = "现金储备充裕（12个月以上），可承受一定风险"
            warning = None
        else:
            judgment = f"现金储备{months}个月，中等水平"
            warning = None

        return judgment, warning

    def _evaluate_contract(
        self, has_contract: bool, signals: list[DivinationSignal], domain: str,
    ) -> tuple[str, RealityWarning | None]:
        """合同状态判断。"""
        career_signals = [s for s in signals if "career" in s.domain]
        favorable = any(s.polarity == "positive" and s.strength > 0.5 for s in career_signals)

        if not has_contract and favorable:
            judgment = "仅有口头 offer，尚无正式合同"
            warning = RealityWarning(
                dimension="contract",
                severity="high",
                message="口头 offer 阶段风险较高，命理显示有机会但合同未落定前不宜做重大决定。",
                signal_adjusted="建议等正式合同签署后再做离职决定，不宜在口头承诺阶段裸辞。",
            )
        elif has_contract:
            judgment = "已有正式书面合同，保障充分"
            warning = None
        else:
            judgment = "未提供合同状态信息"
            warning = None

        return judgment, warning

    def _evaluate_relocation(
        self, target: str, current: str, tolerance: Optional[str],
        signals: list[DivinationSignal], domain: str,
    ) -> tuple[str, RealityWarning | None]:
        """搬迁/通勤判断。"""
        if target == current:
            return "无需搬迁，不涉及地点变化", None

        judgment = f"涉及从{current}到{target}的搬迁"
        if tolerance == "reject":
            warning = RealityWarning(
                dimension="commute",
                severity="high",
                message=f"目标地点{target}超出通勤接受范围，需要搬迁。",
                signal_adjusted="如必须搬迁，建议先确认新地点的住房和工作条件再决定。",
            )
        elif tolerance == "negotiable":
            warning = RealityWarning(
                dimension="commute",
                severity="medium",
                message=f"搬迁至{target}需要适应新环境，目前有调整空间。",
                signal_adjusted="搬迁后需留意适应期，保持弹性。",
            )
        else:
            warning = RealityWarning(
                dimension="commute",
                severity="low",
                message=f"接受搬迁至{target}，机遇与挑战并存。",
                signal_adjusted=None,
            )

        return judgment, warning

    def _evaluate_health(
        self, status: str, signals: list[DivinationSignal], domain: str,
    ) -> tuple[str, RealityWarning | None]:
        """健康状态判断。"""
        health_signals = [s for s in signals if "health" in s.domain]

        if status == "poor":
            judgment = "当前健康状况较差"
            warning = RealityWarning(
                dimension="health",
                severity="high",
                message="健康状况不佳，高压力变动可能加剧身体负担。",
                signal_adjusted="建议先将健康恢复到fair水平再考虑重大事业变动。",
            )
        elif status == "fair":
            judgment = "当前健康状况一般，需留意"
            warning = RealityWarning(
                dimension="health",
                severity="medium",
                message="健康状况一般，高强度变动需注意休息和调整节奏。",
                signal_adjusted="变动期间保持规律作息，避免过度劳累。",
            )
        else:
            judgment = "当前健康状况良好"
            warning = None

        return judgment, warning

    def _evaluate_qualification(
        self, has_qual: bool, signals: list[DivinationSignal], domain: str,
    ) -> tuple[str, RealityWarning | None]:
        """资质/证书判断。"""
        career_signals = [s for s in signals if "career" in s.domain]
        favorable = any(s.polarity == "positive" for s in career_signals)

        if not has_qual and favorable:
            judgment = "缺乏目标方向的资质/证书"
            warning = RealityWarning(
                dimension="qualification",
                severity="medium",
                message="命理显示有机会，但当前尚不具备相应资质，实现路径需补足。",
                signal_adjusted="建议先获取必要资质（证书/许可），再进入新领域。",
            )
        elif has_qual:
            judgment = "具备目标方向所需资质"
            warning = None
        else:
            judgment = "未提供资质信息"
            warning = None

        return judgment, warning

    def _evaluate_dependents(
        self, has_deps: bool, signals: list[DivinationSignal], domain: str,
    ) -> tuple[str, RealityWarning | None]:
        """家庭依赖判断。"""
        wealth_signals = [s for s in signals if "wealth" in s.domain]
        favorable = any(s.polarity == "positive" and s.strength > 0.6 for s in wealth_signals)

        if has_deps and not favorable:
            judgment = "有家庭依赖，但当前财运信号偏弱"
            warning = RealityWarning(
                dimension="dependents",
                severity="high",
                message="有抚养责任，且当前财运信号不足，变动可能影响家庭稳定。",
                signal_adjusted="变动方案需优先考虑家庭保障，不宜冒进。",
            )
        elif has_deps:
            judgment = "有家庭依赖，需平衡家庭与事业"
            warning = RealityWarning(
                dimension="dependents",
                severity="low",
                message="有家庭依赖，变动决定需考虑家庭安排。",
                signal_adjusted="确保变动方案不严重影响家庭生活质量。",
            )
        else:
            judgment = "无家庭依赖，变动自由度较高"
            warning = None

        return judgment, warning

    def _evaluate_backup(
        self, has_backup: bool, signals: list[DivinationSignal], domain: str,
    ) -> tuple[str, RealityWarning | None]:
        """备选方案判断。"""
        decision_signals = [s for s in signals if s.domain == "decision"]
        favorable = any(s.polarity == "positive" and s.strength > 0.6 for s in decision_signals)

        if not has_backup and favorable:
            judgment = "缺乏备选方案/退路"
            warning = RealityWarning(
                dimension="backup",
                severity="medium",
                message="命理显示有机会但无退路，高风险。机会窗口存在时，建议同步准备备选方案。",
                signal_adjusted="不要把所有资源押在单一方向，同时建立备选退路。",
            )
        elif has_backup:
            judgment = "有备选方案/退路，风险可控"
            warning = None
        else:
            judgment = "未提供备选方案信息"
            warning = None

        return judgment, warning

    # ── 输出构建 ─────────────────────────────────────────────────────────────────

    def _build_adjusted_advice(
        self, warnings: list[RealityWarning],
        signals: list[DivinationSignal], domain: str,
    ) -> list[str]:
        """从警告生成调整后的行动建议。"""
        advice = []
        high_severity = [w for w in warnings if w.severity == "high"]
        medium_severity = [w for w in warnings if w.severity == "medium"]

        for w in high_severity:
            if w.signal_adjusted:
                advice.append(w.signal_adjusted)
            else:
                advice.append(w.message)

        for w in medium_severity:
            if w.signal_adjusted:
                advice.append(w.signal_adjusted)

        # 如果没有现实警告，追加一条通用建议
        if not advice:
            advice.append("现实条件暂无明显阻碍，可按命理建议推进。")

        return advice

    def _build_core_conclusion(
        self, warnings: list[RealityWarning], domain: str,
    ) -> str:
        """生成一句话核心结论。"""
        if not warnings:
            return "现实条件支持当前方向，可以积极推进。"

        high = [w for w in warnings if w.severity == "high"]
        if high:
            return f"命理层信号有利，但现实条件存在 {len(high)} 项高风险，需谨慎处理。"
        return f"命理层信号有利，但现实条件有 {len(warnings)} 项需关注，建议审慎推进。"