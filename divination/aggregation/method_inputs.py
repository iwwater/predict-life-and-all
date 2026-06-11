"""术法输入画像 — 为每种术法构造只含相关字段的 Birth 对象。

核心原则：塔罗不需要八字，玄空不需要生日，六爻可手动摇卦。
每种术法只接收它真正需要的参数，避免无关数据污染计算结果。
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Optional

from divination.contracts import Birth
from .selector import ALL_METHODS


# ── 术法输入画像 ────────────────────────────────────────────────────────────────
# 每种术法声明：需要哪些 Birth 字段、是否需要空间数据、支持的模式等

INPUT_PROFILES: dict[str, dict[str, Any]] = {
    # ═══ 东方命理（全需出生） ═══
    "bazi_v2": {
        "needs_birth": True,
        "birth_fields": ["year", "month", "day", "hour", "minute", "gender", "calendar", "tz", "lat", "lng", "is_leap_month"],
        "needs_space": False,
        "needs_question": True,
        "default_mode": "natal",
    },
    "ziwei": {
        "needs_birth": True,
        "birth_fields": ["year", "month", "day", "hour", "minute", "gender", "tz", "is_leap_month", "lat", "lng"],
        "needs_space": False,
        "needs_question": False,
        "default_mode": "natal",
    },
    "qimen": {
        "needs_birth": True,
        "birth_fields": ["year", "month", "day", "hour", "minute", "lng"],
        "needs_space": False,
        "needs_question": False,
        "default_mode": "natal",
    },

    # ═══ 六爻 / 梅花（模式依赖） ═══
    "liuyao": {
        "needs_birth": "conditional",  # 仅 time_qigua 模式需要
        "birth_fields": ["year", "month", "day", "hour", "minute"],
        "needs_space": False,
        "needs_question": True,
        "needs_seed": True,           # 数字 / 手动模式
        "has_modes": True,
        "modes": ["time_qigua", "manual_coin", "number_qigua"],
        "default_mode": "time_qigua",
    },
    "meihua": {
        "needs_birth": "conditional",
        "birth_fields": ["year", "month", "day", "hour", "minute"],
        "needs_space": False,
        "needs_question": True,
        "needs_seed": True,
        "has_modes": True,
        "modes": ["time_qigua", "number_qigua", "external_omen"],
        "default_mode": "time_qigua",
    },

    # ═══ 风水系（部分需要出生） ═══
    "fengshui": {
        "needs_birth": True,          # 需要生命卦（八宅部分）
        "birth_fields": ["year", "month", "day", "hour", "minute", "gender"],
        "needs_space": True,
        "space_fields": ["sitting", "construction_year"],
        "needs_question": False,
    },
    "bazhai": {
        "needs_birth": True,          # 生命卦模式需要
        "birth_fields": ["year", "month", "day", "hour", "minute", "gender"],
        "needs_space": True,
        "space_fields": ["sitting"],
        "needs_question": False,
        "default_mode": "residential_bazhai",
    },
    "xuankong": {
        "needs_birth": False,         # 玄空不需要出生日期！
        "birth_fields": [],
        "needs_space": True,
        "space_fields": ["sitting", "construction_year", "period"],
        "needs_question": False,
        "non_birth_defaults": {"sitting": "子", "period": 8},
    },

    # ═══ 西方占星 / 吠陀（全需出生 + 地点） ═══
    "western": {
        "needs_birth": True,
        "birth_fields": ["year", "month", "day", "hour", "minute", "lat", "lng", "tz"],
        "needs_space": False,
        "needs_question": False,
        "default_mode": "natal",
    },
    "vedic": {
        "needs_birth": True,
        "birth_fields": ["year", "month", "day", "hour", "minute", "lat", "lng", "tz"],
        "needs_space": False,
        "needs_question": False,
        "default_mode": "natal",
    },

    # ═══ 塔罗 / 数字命理（不需要出生） ═══
    "tarot": {
        "needs_birth": False,          # 塔罗完全不需要出生日期
        "birth_fields": [],
        "needs_space": False,
        "needs_question": True,
        "needs_seed": True,
        "needs_spread": True,
        "spread_options": ["celtic_cross", "three_card", "single", "horseshoe", "star"],
        "default_spread": "celtic_cross",
        "default_mode": "reflective",
    },
    "numerology": {
        "needs_birth": "minimal",      # 只需年月日
        "birth_fields": ["year", "month", "day"],
        "needs_space": False,
        "needs_question": True,
        "has_name": True,              # 可选名字
        "default_mode": "life_path",
    },
}


def build_method_inputs(
    birth: Optional[Birth],
    space: Optional[Any],
    method_options: Optional[dict[str, Any]],
    question: str,
    goal: str,
) -> dict[str, Birth]:
    """为每种术法构造专属的 Birth 对象。

    只填充该术法需要的字段，避免无关数据污染。
    无出生信息时，非出生依赖的术法仍可正常运作。

    Args:
        birth: 用户提供的出生信息（可为 None）
        space: 空间信息（可为 None，有 sitting/construction_year 等属性）
        method_options: 前端传来的术法选项（liuyao_mode, tarot_spread 等）
        question: 用户问题
        goal: 分析目标

    Returns:
        {method_name: Birth} — 每个术法一个定制 Birth
    """
    opts = method_options or {}

    # 从 space 提取风水相关字段
    sitting = getattr(space, "sitting", None) if space else None
    construction_year = getattr(space, "construction_year", None) if space else None
    period = getattr(space, "period", None) if space else None

    # 从 method_options 提取术法专属设置
    liuyao_mode = opts.get("liuyao_mode", "time_qigua")
    liuyao_tosses = opts.get("liuyao_tosses", None)
    meihua_mode = opts.get("meihua_mode", "time_qigua")
    meihua_seed = opts.get("meihua_seed", None)
    tarot_spread = opts.get("tarot_spread", "celtic_cross")
    tarot_mode = opts.get("tarot_mode", "reflective")

    # 构建默认出生（当用户未提供出生信息时用于需要出生的术法）
    _default_birth = _make_default_birth()

    inputs: dict[str, Birth] = {}

    for method in ALL_METHODS:
        profile = INPUT_PROFILES.get(method)
        if not profile:
            # 未知术法：传完整出生
            inputs[method] = birth if birth else _make_default_birth()
            continue

        # 决定用哪个出生
        needs_birth = profile.get("needs_birth", True)
        use_birth: Optional[Birth] = None

        if needs_birth is True:
            use_birth = birth if birth else _default_birth
        elif needs_birth == "conditional":
            # 模式依赖：time 模式需要出生，其他不需要
            m = _resolve_mode(method, opts, profile)
            if m == "time_qigua":
                use_birth = birth if birth else _default_birth
            else:
                use_birth = _empty_birth()
        elif needs_birth == "minimal":
            use_birth = birth if birth else _default_birth
        else:
            # needs_birth is False
            use_birth = _empty_birth()

        # 构建 Birth：只填需要的字段
        if use_birth is not None:
            b = _pick_fields(use_birth, profile.get("birth_fields", []))
        else:
            b = _empty_birth()

        # 注入 question / mode / subject
        b.question = question
        b.subject = goal

        # 注入 mode
        b.mode = _resolve_mode(method, opts, profile)

        # 注入空间字段
        if profile.get("needs_space"):
            b.sitting = sitting or profile.get("non_birth_defaults", {}).get("sitting")
            b.construction_year = construction_year or profile.get("non_birth_defaults", {}).get("construction_year")
            b.period = period or profile.get("non_birth_defaults", {}).get("period")

        # 注入塔罗牌阵/模式
        if method == "tarot":
            b.spread = tarot_spread or profile.get("default_spread", "celtic_cross")
            b.mode = tarot_mode or profile.get("default_mode", "reflective")
            # 从 question 派生 seed（保证同一问题得相同牌）
            if question:
                b.seed = _question_seed(question)

        # 注入六爻手动摇卦
        if method == "liuyao" and liuyao_mode == "manual_coin" and liuyao_tosses:
            b.tosses = liuyao_tosses
            b.mode = "manual_coin"
        elif method == "liuyao" and liuyao_mode == "number_qigua":
            b.mode = "number_qigua"
            if question:
                b.seed = _question_seed(question)

        # 注入梅花数字/外应
        if method == "meihua" and meihua_mode == "number_qigua":
            b.mode = "number_qigua"
            b.seed = meihua_seed or (_question_seed(question) if question else None)
        elif method == "meihua" and meihua_mode == "external_omen":
            b.mode = "external_omen"
            b.seed = meihua_seed or (_question_seed(question) if question else None)

        inputs[method] = b

    return inputs


# ── 辅助函数 ────────────────────────────────────────────────────────────────────

def _make_default_birth() -> Birth:
    """构造默认出生信息（上海 1990-06-15 12:00）。"""
    return Birth(
        year=1990, month=6, day=15, hour=12, minute=0,
        gender="unspecified", calendar="gregorian",
        lat=31.23, lng=121.47, tz="Asia/Shanghai",
    )


def _empty_birth() -> Birth:
    """构造空出生信息（无默认值，防止非出生术法被污染）。"""
    return Birth(
        year=2000, month=1, day=1, hour=12, minute=0,
        gender="unspecified", calendar="gregorian",
    )


def _pick_fields(source: Birth, fields: list[str]) -> Birth:
    """从 source Birth 中只提取指定字段构造新 Birth。

    未指定的字段使用 source 的值或 Birth 默认值。
    始终保证 year/month/day 存在（Birth 的必填字段）。
    """
    kwargs: dict[str, Any] = {
        "year": source.year,
        "month": source.month,
        "day": source.day,
    }
    for f in fields:
        if hasattr(source, f):
            kwargs[f] = getattr(source, f)
    return Birth(**kwargs)


def _resolve_mode(method: str, opts: dict, profile: dict) -> Optional[str]:
    """解析术法运行模式。"""
    if method == "liuyao":
        return opts.get("liuyao_mode", profile.get("default_mode", "time_qigua"))
    if method == "meihua":
        return opts.get("meihua_mode", profile.get("default_mode", "time_qigua"))
    if method == "tarot":
        return opts.get("tarot_mode", profile.get("default_mode", "reflective"))
    return profile.get("default_mode", None)


def _question_seed(question: str) -> str:
    """从问题文本派生确定性种子（同一问题 → 同一结果）。"""
    import hashlib
    return hashlib.sha256(question.encode()).hexdigest()[:16]


# ── 前端表单提示 ────────────────────────────────────────────────────────────────

def get_input_form_hints() -> dict[str, Any]:
    """返回前端表单需要展示的高级设置选项。"""
    return {
        "liuyao": {
            "label": "六爻",
            "modes": [
                {"value": "time_qigua", "label": "时间起卦", "desc": "根据出生时间自动起卦（需填写出生信息）"},
                {"value": "manual_coin", "label": "手动摇卦", "desc": "自行摇铜钱六次，输入每次结果"},
                {"value": "number_qigua", "label": "数字起卦", "desc": "输入三个数字或由问题自动生成"},
            ],
        },
        "meihua": {
            "label": "梅花易数",
            "modes": [
                {"value": "time_qigua", "label": "时间起卦", "desc": "根据出生时间起卦"},
                {"value": "number_qigua", "label": "数字起卦", "desc": "输入数字或由问题生成"},
                {"value": "external_omen", "label": "外应起卦", "desc": "以问题文字笔画/意象起卦"},
            ],
        },
        "tarot": {
            "label": "塔罗",
            "spreads": [
                {"value": "celtic_cross", "label": "凯尔特十字", "desc": "10张牌 · 全面深度解读"},
                {"value": "three_card", "label": "三张牌", "desc": "过去·现在·未来"},
                {"value": "single", "label": "单张牌", "desc": "快速指引"},
                {"value": "horseshoe", "label": "马蹄阵", "desc": "7张牌 · 发展趋势"},
                {"value": "star", "label": "星形阵", "desc": "6张牌 · 多角度分析"},
            ],
            "modes": [
                {"value": "reflective", "label": "反思模式", "desc": "侧重自我觉察"},
                {"value": "deep", "label": "深度模式", "desc": "侧重命运解读"},
                {"value": "quick", "label": "快速模式", "desc": "简明扼要"},
            ],
        },
    }
