"""术法权重系统 — 基于 tier 的三层权重分配。

WGT-001: get_weights(goal, selected_methods) — 返回 12 个归一化权重
WGT-002~004: primary=0.65, secondary=0.25, reference=0.10
WGT-005: 总和必须等于 1.0
WGT-006: 每个术法权重 > 0
"""
from __future__ import annotations

from typing import Any

# ── Tier 总权重配置 ───────────────────────────────────────────────────────
# WGT-002~004: primary=0.65, secondary=0.25, reference=0.10

TIER_BUDGET: dict[str, float] = {
    "primary": 0.65,
    "secondary": 0.25,
    "reference": 0.10,
}

# 每个 tier 固定 4 个术法 (SEL spec)
METHODS_PER_TIER: dict[str, int] = {
    "primary": 4,
    "secondary": 4,
    "reference": 4,
}

# 最小权重 (WGT-006: 禁止 0 权重)
_MIN_WEIGHT = 0.001


def get_weights(
    goal: str,
    method_entries: list[dict[str, Any]],
) -> dict[str, float]:
    """根据 goal 和 tier 分配返回 12 个归一化权重。

    WGT-001: 返回 12 个权重
    WGT-005: 总和 = 1.0 (归一化)
    WGT-006: 每个权重 > 0

    Args:
        goal: 标准 goal 类型 (如 "career")
        method_entries: [{method, label, tier}, ...] 来自 selector.select_methods()

    Returns:
        {method_name: weight, ...}  12 项，总和 = 1.0
    """
    # Step 1: 按 tier 分组
    tier_methods: dict[str, list[str]] = {"primary": [], "secondary": [], "reference": []}
    for entry in method_entries:
        tier = entry.get("tier", "reference")
        if tier in tier_methods:
            tier_methods[tier].append(entry["method"])

    # Step 2: 每个 tier 内均匀分配
    weights: dict[str, float] = {}
    for tier, methods in tier_methods.items():
        budget = TIER_BUDGET.get(tier, 0.10)
        n = len(methods)
        if n == 0:
            continue
        per_method = budget / n
        for m in methods:
            weights[m] = per_method

    # Step 3: 确保 12 个方法都有权重 (WGT-006)
    all_methods = [e["method"] for e in method_entries]
    for m in all_methods:
        if m not in weights or weights[m] <= 0:
            weights[m] = _MIN_WEIGHT

    # Step 4: 归一化到 1.0 (WGT-005)
    total = sum(weights.values())
    if total > 0:
        weights = {k: v / total for k, v in weights.items()}

    # 再次确保所有方法都有正权重
    for m in all_methods:
        if m not in weights or weights[m] <= 0:
            weights[m] = _MIN_WEIGHT

    # 最终归一化
    total = sum(weights.values())
    weights = {k: v / total for k, v in weights.items()}

    return weights


def get_weight_for_method(
    method: str,
    goal: str,
    method_entries: list[dict[str, Any]],
) -> float:
    """获取单个术法在指定 goal 下的权重。

    便捷函数 — 调用 get_weights 后取单个值。
    """
    all_weights = get_weights(goal, method_entries)
    return all_weights.get(method, _MIN_WEIGHT)


# ── 向后兼容 ─────────────────────────────────────────────────────────────────
# 旧版 get_weight(method, domain) 仍可用

def get_weight(method: str, domain: str) -> float:
    """向后兼容的单术法权重查询（基于旧版 domain 系统）。

    新代码请使用 get_weights(goal, method_entries)。
    """
    # 默认权重映射
    legacy_defaults: dict[str, float] = {
        "bazi_v2": 0.15, "ziwei": 0.12, "qimen": 0.10,
        "liuyao": 0.09, "meihua": 0.07, "fengshui": 0.07,
        "bazhai": 0.07, "xuankong": 0.07, "western": 0.09,
        "vedic": 0.07, "tarot": 0.06, "numerology": 0.04,
    }
    return legacy_defaults.get(method, 0.05)
