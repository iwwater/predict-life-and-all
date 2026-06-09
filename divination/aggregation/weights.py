"""术法领域权重配置 — 决定每种术法在不同生命领域的可信度权重。

BE-005: 权重文件
从 divination/engines/cross_validator.py 的 SYSTEM_DOMAIN_WEIGHTS 扩展而来，
覆盖全部 12 术法。
"""
from __future__ import annotations

# ── 12 术法在不同领域的权重 (0-1) ────────────────────────────────────────
# 基于各术法的经典理论定位：
#   - 八字(命): 格局/性格/事业/财运最擅长
#   - 紫微(命): 十二宫全面，关系/本命尤其强
#   - 奇门(卜): 决策/时机/失物极强
#   - 六爻(卜): 一事一问，决策力强
#   - 梅花(卜): 快速起卦，趋势判断
#   - 八宅(风水): 住宅吉凶方
#   - 玄空(风水): 元运理气
#   - 风水(复合): 综合风水判断，结合八宅+玄空
#   - 西方占星: 心理/性格/关系
#   - 吠陀占星: 本命/运程
#   - 塔罗: 当下指引/决策
#   - 数字命理: 人生方向参考

METHOD_DOMAIN_WEIGHTS: dict[str, dict[str, float]] = {
    # ── 东方命理 ──
    "bazi_v2": {
        "self_life": 0.85,
        "career": 0.80,
        "wealth": 0.85,
        "relationship": 0.60,
        "health": 0.65,
        "decision": 0.40,
        "timing": 0.80,
        "lost_item": 0.10,
        "home_fengshui": 0.15,
    },
    "ziwei": {
        "self_life": 0.80,
        "career": 0.75,
        "wealth": 0.70,
        "relationship": 0.80,
        "health": 0.75,
        "decision": 0.40,
        "timing": 0.75,
        "lost_item": 0.15,
        "home_fengshui": 0.25,
    },
    # ── 东方占卜 ──
    "qimen": {
        "self_life": 0.35,
        "career": 0.70,
        "wealth": 0.75,
        "relationship": 0.45,
        "health": 0.40,
        "decision": 0.90,
        "timing": 0.85,
        "lost_item": 0.85,
        "home_fengshui": 0.55,
    },
    "liuyao": {
        "self_life": 0.30,
        "career": 0.70,
        "wealth": 0.75,
        "relationship": 0.70,
        "health": 0.50,
        "decision": 0.85,
        "timing": 0.70,
        "lost_item": 0.80,
        "home_fengshui": 0.35,
    },
    "meihua": {
        "self_life": 0.30,
        "career": 0.60,
        "wealth": 0.55,
        "relationship": 0.60,
        "health": 0.40,
        "decision": 0.75,
        "timing": 0.65,
        "lost_item": 0.70,
        "home_fengshui": 0.30,
    },
    # ── 风水 ──
    "fengshui": {
        "self_life": 0.20,
        "career": 0.30,
        "wealth": 0.55,
        "relationship": 0.25,
        "health": 0.60,
        "decision": 0.35,
        "timing": 0.30,
        "lost_item": 0.10,
        "home_fengshui": 0.90,
    },
    "bazhai": {
        "self_life": 0.25,
        "career": 0.30,
        "wealth": 0.45,
        "relationship": 0.25,
        "health": 0.55,
        "decision": 0.25,
        "timing": 0.20,
        "lost_item": 0.05,
        "home_fengshui": 0.85,
    },
    "xuankong": {
        "self_life": 0.15,
        "career": 0.25,
        "wealth": 0.50,
        "relationship": 0.15,
        "health": 0.50,
        "decision": 0.20,
        "timing": 0.40,
        "lost_item": 0.05,
        "home_fengshui": 0.90,
    },
    # ── 西方 ──
    "western": {
        "self_life": 0.75,
        "career": 0.60,
        "wealth": 0.40,
        "relationship": 0.80,
        "health": 0.55,
        "decision": 0.40,
        "timing": 0.50,
        "lost_item": 0.10,
        "home_fengshui": 0.10,
    },
    "vedic": {
        "self_life": 0.70,
        "career": 0.55,
        "wealth": 0.45,
        "relationship": 0.65,
        "health": 0.60,
        "decision": 0.30,
        "timing": 0.55,
        "lost_item": 0.10,
        "home_fengshui": 0.15,
    },
    "tarot": {
        "self_life": 0.50,
        "career": 0.55,
        "wealth": 0.40,
        "relationship": 0.70,
        "health": 0.35,
        "decision": 0.75,
        "timing": 0.45,
        "lost_item": 0.50,
        "home_fengshui": 0.15,
    },
    "numerology": {
        "self_life": 0.55,
        "career": 0.35,
        "wealth": 0.25,
        "relationship": 0.30,
        "health": 0.20,
        "decision": 0.20,
        "timing": 0.35,
        "lost_item": 0.05,
        "home_fengshui": 0.10,
    },
}


# ── 方法默认权重（无特定领域时使用） ────────────────────────────────────────

METHOD_DEFAULT_WEIGHT: dict[str, float] = {
    "bazi_v2": 0.80,
    "ziwei": 0.75,
    "qimen": 0.60,
    "liuyao": 0.60,
    "meihua": 0.50,
    "fengshui": 0.55,
    "bazhai": 0.45,
    "xuankong": 0.50,
    "western": 0.60,
    "vedic": 0.55,
    "tarot": 0.50,
    "numerology": 0.35,
}


def get_weight(method: str, domain: str) -> float:
    """获取指定术法在指定领域的权重。

    Args:
        method: 术法标识
        domain: 领域 (self_life/career/wealth/...)

    Returns:
        权重 0-1
    """
    method_weights = METHOD_DOMAIN_WEIGHTS.get(method, {})
    return method_weights.get(domain, METHOD_DEFAULT_WEIGHT.get(method, 0.5))


def get_all_weights_for_domain(domain: str) -> dict[str, float]:
    """获取所有术法在指定领域的权重。

    Returns:
        {method: weight, ...}
    """
    return {m: get_weight(m, domain) for m in METHOD_DOMAIN_WEIGHTS}


def get_top_methods_for_domain(domain: str, n: int = 5) -> list[tuple[str, float]]:
    """获取指定领域权重最高的几个术法。"""
    weights = get_all_weights_for_domain(domain)
    return sorted(weights.items(), key=lambda x: -x[1])[:n]
