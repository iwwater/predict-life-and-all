"""安全与合规模块 (SAFE-001~010)。

SAFE-001: 统一免责声明 — 所有报告和导出文件都包含
SAFE-002: 医疗类问题降级 — 只做自我反思，不做诊断
SAFE-003: 投资类问题降级 — 不给具体投资建议
SAFE-004: 法律类问题降级 — 不给法律判断
SAFE-005: 危机词拦截 — 自伤、自杀、严重心理危机需安全回应
SAFE-006: 绝对化表达过滤 — 禁止"一定会、必然、保证、必须"
SAFE-007: 用户隐私提示 — 出生信息、合盘信息用途说明
SAFE-008: API 错误不泄露敏感信息
SAFE-009: CORS 生产环境白名单
SAFE-010: 日志脱敏 — 不记录完整出生信息和用户隐私问题
"""
from __future__ import annotations

import re
from typing import Any

# ── SAFE-001: 统一免责声明 ──────────────────────────────────────────────────

DISCLAIMER = (
    "【免责声明】以上内容为基于传统文化与符号象征视角的参考分析，仅供参考，"
    "不构成医疗诊断、法律建议或投资指导。命理分析具有文化传承价值，"
    "但不应替代专业意见。重大人生决策请结合现实情况，咨询相关专业人士。"
)

PRIVACY_NOTICE = (
    "【隐私说明】您提供的出生信息仅用于本次命理分析，不会用于其他用途。"
    "系统不存储完整的个人身份信息，历史报告仅保存在您的本地浏览器中。"
)


# ── SAFE-005: 危机词库 ──────────────────────────────────────────────────────

CRISIS_KEYWORDS: list[str] = [
    "自杀", "自残", "自伤", "轻生", "不想活", "活不下去",
    "想死", "结束生命", "死了算了", "活够了", "没有意义",
    "自我了断", "一了百了",
]

CRISIS_RESPONSE = (
    "听起来你正承受很大的痛苦。这不是命理分析能回答的问题，"
    "也请不要独自承受。\n\n"
    "📞 中国心理援助热线: 400-161-9995\n"
    "📞 北京心理危机研究与干预中心: 010-82951332\n"
    "📞 希望24热线: 400-161-9995\n\n"
    "请与信任的人或专业心理咨询师谈谈。你不需要一个人面对。"
)


# ── SAFE-002~004: 敏感领域关键词 ────────────────────────────────────────────

MEDICAL_KEYWORDS: list[str] = [
    "重病", "绝症", "癌症", "癌", "肿瘤", "能不能治好",
    "会不会死", "寿命", "几时死", "能活多久", "会不会复发",
    "诊断", "手术", "吃药", "治疗方案",
]

INVESTMENT_KEYWORDS: list[str] = [
    "买哪只股", "全仓", "梭哈", "包赚", "稳赚", "必涨",
    "什么时候卖", "该不该卖", "涨停", "跌停", "杠杆",
    "合约", "做空", "做多", "仓位", "止损", "止盈",
]

LEGAL_KEYWORDS: list[str] = [
    "官司一定", "能不能离婚", "该不该离婚", "会不会判",
    "胜诉", "败诉", "会不会坐牢", "能判几年",
]


MEDICAL_DOWNGRADE_MSG = (
    "健康类问题需以正规医疗诊断为准。本分析仅从传统文化自我反思角度提供参考，"
    "不构成任何医学诊断或健康预测。如有身体不适，请及时就医。"
)

INVESTMENT_DOWNGRADE_MSG = (
    "财运分析仅供参考文化视角，不构成具体投资建议。"
    "投资决策请结合自身风险承受能力并咨询持牌金融机构。"
)

LEGAL_DOWNGRADE_MSG = (
    "法律相关问题请咨询持证律师。本分析仅为文化视角参考，"
    "不构成任何法律判断或建议。"
)


# ── SAFE-006: 绝对化表达 ────────────────────────────────────────────────────

ABSOLUTE_PATTERNS: list[str] = [
    "一定", "必然", "肯定会", "绝对", "百分之百",
    "100%", "毫无疑问", "必定", "注定", "保证",
    "必须", "肯定能", "绝不会", "永远会", "不可能",
]

ABSOLUTE_SOFTEN: dict[str, str] = {
    "一定": "倾向于", "必然": "较可能", "肯定会": "往往会",
    "绝对": "通常", "必定": "多半", "注定": "倾向于",
    "保证": "倾向于", "必须": "建议", "百分之百": "较高概率",
    "100%": "较高概率", "毫无疑问": "综合来看",
    "肯定能": "较可能", "绝不会": "通常不会", "永远会": "倾向于",
    "不可能": "概率较低",
}


# ── Public API ──────────────────────────────────────────────────────────────

def check_input_safety(question: str) -> dict[str, Any]:
    """检查用户输入的安全性。

    SAFE-005: 危机词拦截
    SAFE-002~004: 敏感领域降级

    Returns:
        {
            "blocked": bool,       # 是否应阻止解读
            "crisis": bool,        # 是否为危机
            "crisis_message": str, # 危机响应
            "downgrades": [str],   # 降级提示
            "safe": bool,          # 完全安全
        }
    """
    q = question.lower().strip()
    downgrades: list[str] = []

    # SAFE-005: 危机检测
    for kw in CRISIS_KEYWORDS:
        if kw in q:
            return {
                "blocked": True,
                "crisis": True,
                "crisis_message": CRISIS_RESPONSE,
                "downgrades": [],
                "safe": False,
            }

    # SAFE-002: 医疗降级
    medical_hits = [kw for kw in MEDICAL_KEYWORDS if kw in q]
    if medical_hits:
        downgrades.append(MEDICAL_DOWNGRADE_MSG)

    # SAFE-003: 投资降级
    invest_hits = [kw for kw in INVESTMENT_KEYWORDS if kw in q]
    if invest_hits:
        downgrades.append(INVESTMENT_DOWNGRADE_MSG)

    # SAFE-004: 法律降级
    legal_hits = [kw for kw in LEGAL_KEYWORDS if kw in q]
    if legal_hits:
        downgrades.append(LEGAL_DOWNGRADE_MSG)

    return {
        "blocked": False,
        "crisis": False,
        "crisis_message": "",
        "downgrades": downgrades,
        "safe": len(downgrades) == 0,
    }


def check_output_safety(text: str) -> dict[str, Any]:
    """检查输出文本的安全性。

    SAFE-006: 检测并标记绝对化表达

    Returns:
        {
            "safe": bool,
            "absolute_hits": [str],
            "softened": str,     # 软化后的文本（可选）
            "warnings": [str],
        }
    """
    hits: list[str] = []
    warnings: list[str] = []

    for pattern in ABSOLUTE_PATTERNS:
        if pattern in text:
            hits.append(pattern)

    # Check for missing disclaimer
    if "免责声明" not in text and "仅供参考" not in text:
        warnings.append("输出缺少免责声明")

    # Check for medical/legal/investment conclusions
    for kw in ["一定能治好", "肯定会涨", "官司必赢", "绝对不会亏"]:
        if kw in text:
            warnings.append(f"输出包含不当结论: '{kw}'")

    return {
        "safe": len(hits) == 0,
        "absolute_hits": hits,
        "softened": _soften_text(text) if hits else text,
        "warnings": warnings,
    }


def sanitize_for_log(text: str) -> str:
    """SAFE-010: 日志脱敏 — 移除完整出生信息。

    保留前 2 个字符，其余替换为 ***。
    """
    # Redact birth patterns like "1990-06-15" or "1990年6月15日"
    # Use digit boundaries (?<!\d) / (?!\d) instead of \b because CJK chars
    # are word characters in Python 3 regex, so \b doesn't separate them from digits.
    text = re.sub(r'(?<!\d)(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})[日]?(?!\d)', r'\1-***-**', text)
    # Redact coordinates
    text = re.sub(r'\b\d{2,3}\.\d{2,6}\b', '**.**', text)
    # Redact long digit sequences (potential phone numbers)
    text = re.sub(r'\b\d{8,}\b', '****', text)
    return text


def sanitize_birth_for_log(birth_dict: dict[str, Any] | None = None) -> str:
    """SAFE-010: 将出生信息脱敏后返回摘要字符串。"""
    if not birth_dict:
        return "无出生信息"
    year = birth_dict.get("year", "?")
    gender = birth_dict.get("gender", "?")
    return f"出生年={year}, 性别={gender}"


# ── Internal helpers ────────────────────────────────────────────────────────

def _soften_text(text: str) -> str:
    """SAFE-006: 替换绝对化表达。"""
    result = text
    for abs_word, soft in ABSOLUTE_SOFTEN.items():
        result = result.replace(abs_word, soft)
    return result
