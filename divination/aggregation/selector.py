"""术法选择器 — 根据 goal 返回全部 12 法并标记 primary/secondary/reference 三层。

BE-004: 术法选择
SEL-001: ALL_METHODS 固定 12 术法
SEL-002: select_methods(goal) 任意 goal 都返回 12 法
SEL-003: 每个术法标记 tier
SEL-004~013: 每个 goal 各有 primary 配置
SEL-015: 少于 12 法时直接报错
"""
from __future__ import annotations

from typing import Any, Literal, Optional

Tier = Literal["primary", "secondary", "reference"]

# ── SEL-001: 固定 12 术法清单 ──────────────────────────────────────────────

ALL_METHODS: list[str] = [
    "bazi_v2",      # 1. 八字精算版
    "ziwei",        # 2. 紫微斗数
    "qimen",        # 3. 奇门遁甲
    "liuyao",       # 4. 六爻
    "meihua",       # 5. 梅花易数
    "fengshui",     # 6. 风水（八宅+玄空复合）
    "bazhai",       # 7. 八宅
    "xuankong",     # 8. 玄空飞星
    "western",      # 9. 西方占星
    "vedic",        # 10. 吠陀占星
    "tarot",        # 11. 塔罗
    "numerology",   # 12. 数字命理
]

METHOD_LABELS: dict[str, str] = {
    "bazi_v2":    "八字",
    "ziwei":      "紫微",
    "qimen":      "奇门",
    "liuyao":     "六爻",
    "meihua":     "梅花",
    "fengshui":   "风水",
    "bazhai":     "八宅",
    "xuankong":   "玄空",
    "western":    "西方占星",
    "vedic":      "吠陀占星",
    "tarot":      "塔罗",
    "numerology": "数字命理",
}

# ── SEL-003~013: 每个 goal 的 tier 配置 ───────────────────────────────────
#
# primary:   该场景下最权威的术法（权重最高）
# secondary: 有参考价值的术法
# reference: 仍参与聚合，但权重较低

_GOAL_TIER_CONFIG: dict[str, dict[str, list[str]]] = {
    # SEL-004
    "general_life": {
        "primary":    ["bazi_v2", "ziwei", "western", "vedic"],
        "secondary":  ["numerology", "qimen", "liuyao", "meihua"],
        "reference":  ["tarot", "fengshui", "bazhai", "xuankong"],
    },
    # SEL-005
    "career": {
        "primary":    ["bazi_v2", "ziwei", "western", "qimen"],
        "secondary":  ["liuyao", "meihua", "vedic", "tarot"],
        "reference":  ["numerology", "fengshui", "bazhai", "xuankong"],
    },
    # SEL-006
    "wealth": {
        "primary":    ["bazi_v2", "ziwei", "qimen", "western"],
        "secondary":  ["liuyao", "meihua", "vedic", "xuankong"],
        "reference":  ["tarot", "numerology", "fengshui", "bazhai"],
    },
    # SEL-007
    "relationship": {
        "primary":    ["bazi_v2", "ziwei", "western", "tarot"],
        "secondary":  ["vedic", "liuyao", "meihua", "qimen"],
        "reference":  ["numerology", "fengshui", "bazhai", "xuankong"],
    },
    # SEL-008
    "compatibility": {
        "primary":    ["bazi_v2", "ziwei", "western", "vedic"],
        "secondary":  ["tarot", "liuyao", "meihua", "qimen"],
        "reference":  ["numerology", "fengshui", "bazhai", "xuankong"],
    },
    # SEL-009
    "yearly": {
        "primary":    ["bazi_v2", "ziwei", "western", "vedic"],
        "secondary":  ["qimen", "liuyao", "meihua", "xuankong"],
        "reference":  ["tarot", "numerology", "fengshui", "bazhai"],
    },
    # monthly (SEL 隐含)
    "monthly": {
        "primary":    ["qimen", "liuyao", "bazi_v2", "ziwei"],
        "secondary":  ["western", "meihua", "vedic", "tarot"],
        "reference":  ["numerology", "fengshui", "bazhai", "xuankong"],
    },
    # SEL-013
    "daily": {
        "primary":    ["tarot", "numerology", "bazi_v2", "qimen"],
        "secondary":  ["liuyao", "meihua", "ziwei", "western"],
        "reference":  ["vedic", "fengshui", "bazhai", "xuankong"],
    },
    # SEL-010
    "decision": {
        "primary":    ["qimen", "liuyao", "meihua", "tarot"],
        "secondary":  ["bazi_v2", "ziwei", "western", "vedic"],
        "reference":  ["numerology", "fengshui", "bazhai", "xuankong"],
    },
    # SEL-011
    "timing": {
        "primary":    ["qimen", "liuyao", "bazi_v2", "ziwei"],
        "secondary":  ["western", "meihua", "vedic", "xuankong"],
        "reference":  ["tarot", "numerology", "fengshui", "bazhai"],
    },
    # SEL-012
    "fengshui": {
        "primary":    ["fengshui", "bazhai", "xuankong", "qimen"],
        "secondary":  ["bazi_v2", "ziwei", "liuyao", "meihua"],
        "reference":  ["western", "vedic", "tarot", "numerology"],
    },
    # INT-013: health_reflection — 非医疗化的健康自省
    "health_reflection": {
        "primary":    ["bazi_v2", "ziwei", "qimen", "western"],
        "secondary":  ["vedic", "liuyao", "meihua", "numerology"],
        "reference":  ["tarot", "fengshui", "bazhai", "xuankong"],
    },
}


def select_methods(
    goal: Optional[str] = None,
    user_methods: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """根据 goal 返回全部 12 术法及其 tier 标记。

    SEL-002: 任意 goal 都返回 12 法
    SEL-003: 每个术法含 tier 和 label
    SEL-015: 少于 12 法直接报错

    Args:
        goal: 标准 goal 类型（如 "career"）
        user_methods: 用户指定的术法子集

    Returns:
        [{"method": "bazi_v2", "label": "八字", "tier": "primary"}, ...]

    Raises:
        AssertionError: 当结果少于 12 法时 (SEL-015)
    """
    # 用户指定子集
    if user_methods:
        valid = [m for m in user_methods if m in ALL_METHODS]
        # 填充到 12 法（用 reference 兜底）
        remaining = [m for m in ALL_METHODS if m not in valid]
        config = _GOAL_TIER_CONFIG.get(goal or "general_life",
                                        _GOAL_TIER_CONFIG["general_life"])
        methods = _build_method_list(valid + remaining, config)
        # SEL-015: 防删减断言
        assert len(methods) >= 12, (
            f"SEL-015: 术法数量不足! 当前 {len(methods)} < 12。"
            f"user_methods={user_methods}, valid={valid}"
        )
        return methods

    # 默认全 12 法
    config = _GOAL_TIER_CONFIG.get(goal or "general_life",
                                    _GOAL_TIER_CONFIG["general_life"])
    methods = _build_method_list(ALL_METHODS, config)

    # SEL-015: 防删减断言
    assert len(methods) >= 12, (
        f"SEL-015: 术法数量不足! 当前 {len(methods)} < 12, goal={goal}"
    )

    return methods


def _build_method_list(
    methods: list[str],
    config: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """给术法列表标记 tier。"""
    primary_set = set(config.get("primary", []))
    secondary_set = set(config.get("secondary", []))
    reference_set = set(config.get("reference", []))

    result: list[dict[str, Any]] = []
    for m in methods:
        if m in primary_set:
            tier: Tier = "primary"
        elif m in secondary_set:
            tier = "secondary"
        elif m in reference_set:
            tier = "reference"
        else:
            tier = "reference"  # 未配置的兜底

        result.append({
            "method": m,
            "label": METHOD_LABELS.get(m, m),
            "tier": tier,
        })
    return result


def get_method_names(methods: list[dict[str, Any]]) -> list[str]:
    """提取纯方法名列表（用于向后兼容）。"""
    return [m["method"] for m in methods]


def get_primary_methods(goal: str) -> list[str]:
    """获取指定 goal 的 primary 术法列表。"""
    config = _GOAL_TIER_CONFIG.get(goal, _GOAL_TIER_CONFIG["general_life"])
    return config.get("primary", [])


def get_tier_for_method(method: str, goal: str) -> Tier:
    """获取指定术法在指定 goal 下的 tier。"""
    config = _GOAL_TIER_CONFIG.get(goal, _GOAL_TIER_CONFIG["general_life"])
    if method in config.get("primary", []):
        return "primary"
    if method in config.get("secondary", []):
        return "secondary"
    return "reference"


# ── 向后兼容 ─────────────────────────────────────────────────────────────────

# FIXED_12_METHODS 别名
FIXED_12_METHODS = list(ALL_METHODS)
