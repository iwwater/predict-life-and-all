"""Sprint 1.5 — 分 scope 五档计票 + 分歧并陈引擎。

从 validator.py 抽出 _tally_by_scope 及其相关逻辑, 形成独立 TallyEngine。

设计:
  TallyEngine.tally_by_scope()      — 原始计票 (单条 signal → ScopeTally)
  TallyEngine.normalize()            — 计票归一化: 应用"≥2 法一致"规则
  TallyEngine.divergence_view()      — 分歧并陈: 支持/警示方法列表 + 一句话

输出原则:
  - 无单一分数
  - 分歧必并陈 (consensus + conflict 分别显式列)
  - 自动 summary 文本, 可直接渲染

参考:
  - arxiv 2103.02559 multi-method aggregation 思路
  - Delphi method 多轮共识 (本场景是单轮, 但保留 "多法一致" 阈值)
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from .schema import (
    ConflictItem,
    ConsensusItem,
    DivinationSignal,
    ScopeTally,
    TimeScope,
)

# ── 阈值常量 ──────────────────────────────────────────────────────────────

SUPPORT_STRONG_THRESHOLD = 0.40  # 加权强度 ≥ 此值 → 强档
SUPPORT_WEAK_THRESHOLD = 0.15    # 加权强度 ≥ 此值 → 弱档
MIN_METHODS_FOR_STRONG = 2       # 至少 2 个独立方法 → 算"多法一致"

VALID_SCOPES: tuple[str, ...] = (
    "long_term", "current_cycle", "short_term",
    "space", "one_question", "relationship", "medium_term",
)


# ── TallyEngine ──────────────────────────────────────────────────────────

class TallyEngine:
    """分 scope 五档计票 + 分歧并陈引擎。

    确定性: 同 inputs → 同 outputs (无随机, 无 LLM)。
    """

    def tally_by_scope(
        self,
        signals: list[DivinationSignal],
        weights: dict[str, float] | None = None,
    ) -> dict[TimeScope, ScopeTally]:
        """按 time_scope 分组, 每组内 5 档各计数。

        Args:
            signals: 所有术法的统一信号
            weights: {method: weight, ...}, 缺省时均匀分

        Returns:
            {time_scope: ScopeTally(...), ...}
        """
        tally: dict[TimeScope, ScopeTally] = {}

        for s in signals:
            scope = self._resolve_scope(s)
            if scope not in tally:
                tally[scope] = ScopeTally(scope=scope)
            t = tally[scope]

            if s.polarity == "positive":
                if s.strength >= SUPPORT_STRONG_THRESHOLD:
                    t.strong_support += 1
                    if s.method not in t.supporting_methods:
                        t.supporting_methods.append(s.method)
                else:
                    t.weak_support += 1
                    if s.method not in t.supporting_methods:
                        t.supporting_methods.append(s.method)
            elif s.polarity == "negative":
                if s.strength >= SUPPORT_STRONG_THRESHOLD:
                    t.strong_warn += 1
                    if s.method not in t.warning_methods:
                        t.warning_methods.append(s.method)
                else:
                    t.weak_warn += 1
                    if s.method not in t.warning_methods:
                        t.warning_methods.append(s.method)
            else:  # neutral / mixed
                t.neutral += 1

        # 自动 summary
        for t in tally.values():
            t.summary = self._build_tally_summary(t)
        return tally

    def normalize(
        self,
        tally: dict[TimeScope, ScopeTally],
    ) -> dict[TimeScope, ScopeTally]:
        """归一化: 应用"≥ MIN_METHODS_FOR_STRONG 法一致"规则。

        修改 in-place: 不满足阈值的方法从 strong_support 降为 weak_support。
        返回原对象 (便于链式)。
        """
        for t in tally.values():
            n_support = len(t.supporting_methods)
            n_warn = len(t.warning_methods)

            # 强档降级 (不够多法一致 → 弱档)
            if t.strong_support > 0 and n_support < MIN_METHODS_FOR_STRONG:
                t.weak_support += t.strong_support
                t.strong_support = 0

            if t.strong_warn > 0 and n_warn < MIN_METHODS_FOR_STRONG:
                t.weak_warn += t.strong_warn
                t.strong_warn = 0

            t.summary = self._build_tally_summary(t)
        return tally

    def divergence_view(
        self,
        tally: dict[TimeScope, ScopeTally],
    ) -> dict[TimeScope, dict[str, Any]]:
        """分歧并陈: 每个 scope 的支持/警示两边都列。

        Returns:
            {scope: {
                "consensus": [支持方法列表],
                "warning":   [警示方法列表],
                "consensus_count": int,
                "warning_count":   int,
                "verdict":         "strong_consensus" | "weak_consensus" | "divergence" | "neutral",
                "summary":         "一句话" (来自 tally.summary),
            }, ...}
        """
        out: dict[TimeScope, dict[str, Any]] = {}
        for scope, t in tally.items():
            sup = t.strong_support + t.weak_support
            warn = t.strong_warn + t.weak_warn
            if t.strong_support >= MIN_METHODS_FOR_STRONG and warn == 0:
                verdict = "strong_consensus"
            elif sup > 0 and warn == 0:
                verdict = "weak_consensus"
            elif warn > 0 and sup > 0:
                verdict = "divergence"
            elif t.strong_warn >= MIN_METHODS_FOR_STRONG and sup == 0:
                verdict = "strong_warning"
            else:
                verdict = "neutral"
            out[scope] = {
                "consensus": list(t.supporting_methods),
                "warning": list(t.warning_methods),
                "consensus_count": sup,
                "warning_count": warn,
                "verdict": verdict,
                "summary": t.summary,
            }
        return out

    def to_tally_report(
        self,
        tally: dict[TimeScope, ScopeTally],
    ) -> list[dict[str, Any]]:
        """输出渲染友好的报告 (供前端)."""
        rows: list[dict[str, Any]] = []
        for scope, t in tally.items():
            rows.append({
                "scope": scope,
                "strong_support": t.strong_support,
                "weak_support": t.weak_support,
                "neutral": t.neutral,
                "weak_warn": t.weak_warn,
                "strong_warn": t.strong_warn,
                "supporting_methods": list(t.supporting_methods),
                "warning_methods": list(t.warning_methods),
                "summary": t.summary,
            })
        return rows

    # ── 内部 ────────────────────────────────────────────────────────────

    @staticmethod
    def _resolve_scope(s: DivinationSignal) -> TimeScope:
        """从 signal 推断 scope。无 → long_term。"""
        scope = s.time_scope or s.dimension or "long_term"
        if scope not in VALID_SCOPES:
            return "long_term"
        return scope  # type: ignore[return-value]

    @staticmethod
    def _build_tally_summary(t: ScopeTally) -> str:
        """从 ScopeTally 生成一句话小结。

        模板:
          N 法支持, M 法警示 → 一致向好
          N 法支持, M 法警示 → 存在分歧
          警示为主 → 多法警示
          全中性 → 倾向不明
        """
        sup = t.strong_support + t.weak_support
        warn = t.strong_warn + t.weak_warn
        if sup == 0 and warn == 0:
            return f"{t.scope} 倾向不明 (仅中性信号)"

        if sup > 0 and warn == 0:
            tone = "一致向好" if t.strong_support >= MIN_METHODS_FOR_STRONG else "倾向偏正"
            return f"{t.scope}: {sup} 法支持, 无警示 ({tone})"

        if warn > 0 and sup == 0:
            tone = "多法警示" if t.strong_warn >= MIN_METHODS_FOR_STRONG else "倾向偏负"
            return f"{t.scope}: {warn} 法警示, 无支持 ({tone})"

        # 分歧
        return f"{t.scope}: 分歧 — {sup} 法支持 vs {warn} 法警示"


# ── 便捷函数 (供 validator 调) ───────────────────────────────────────────

def tally_signals(
    signals: list[DivinationSignal],
    weights: dict[str, float] | None = None,
    normalize: bool = True,
) -> dict[TimeScope, ScopeTally]:
    """一步到位: tally + (可选)归一化。"""
    engine = TallyEngine()
    t = engine.tally_by_scope(signals, weights)
    if normalize:
        engine.normalize(t)
    return t


def build_divergence_view(
    tally: dict[TimeScope, ScopeTally],
) -> dict[TimeScope, dict[str, Any]]:
    """便捷: 分歧并陈视图。"""
    return TallyEngine().divergence_view(tally)
