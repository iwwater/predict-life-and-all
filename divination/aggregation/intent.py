"""问题意图分类器 — 输入自然语言问题，返回标准 goal 类型。

BE-003: 问题分类
INT-001: classify_intent() — 输入问题，返回 goal
INT-002~013: 支持 12 个 goal 类型
INT-014: 支持显式 goal 覆盖
"""
from __future__ import annotations

import re
from typing import Any, Optional

# ── 12 个标准 goal 类型 ────────────────────────────────────────────────────

GOAL_TYPES = [
    "general_life",       # 命盘、人生、整体、综合
    "career",             # 事业、工作、创业、跳槽、升职
    "wealth",             # 财运、赚钱、收入、投资、财富
    "relationship",       # 感情、恋爱、婚姻、桃花、复合
    "compatibility",      # 合盘、合不合、适合结婚、匹配
    "yearly",             # 今年、年度、流年、年运
    "monthly",            # 本月、月运、这个月
    "daily",              # 今日、今天、每日、日运
    "decision",           # 该不该、要不要、是否、选择
    "timing",             # 什么时候、时机、几月、哪天
    "fengshui",           # 风水、房子、搬家、卧室、办公室、方位
    "health_reflection",  # 健康、压力、睡眠、身体状态 — 必须非医疗化
]

GOAL_LABELS: dict[str, str] = {
    "general_life":       "本命格局",
    "career":             "事业工作",
    "wealth":             "财运",
    "relationship":       "感情关系",
    "compatibility":      "合盘匹配",
    "yearly":             "流年运势",
    "monthly":            "月运",
    "daily":              "日运",
    "decision":           "具体决策",
    "timing":             "时机分析",
    "fengshui":           "风水",
    "health_reflection":  "健康自省",
}

# ── 关键词库 ────────────────────────────────────────────────────────────────

_KEYWORD_MAP: dict[str, list[str]] = {
    "general_life": [
        "命盘", "人生", "整体", "综合", "命怎么样", "运势怎么样",
        "看看命", "分析命盘", "算算命", "排盘", "命运如何",
        "我这人", "性格", "一辈子", "一生", "命格", "综合运势",
        "整体运势", "命运走势", "人生方向", "看看运势",
    ],
    "career": [
        "工作", "事业", "职业", "跳槽", "升职", "创业", "换工作",
        "辞职", "面试", "老板", "同事", "公司", "行业", "转行",
        "加薪", "offer", "入职", "离职", "失业", "裁员", "前途",
        "职场", "发展前景", "找工作",
    ],
    "wealth": [
        "财运", "赚钱", "收入", "投资", "财富", "钱", "财",
        "股票", "基金", "理财", "房产", "买房", "生意", "经营",
        "亏损", "债务", "贷款", "分红", "奖金", "发财", "偏财",
        "正财", "经济状况", "能不能做成",
    ],
    "relationship": [
        "感情", "恋爱", "爱情", "婚姻", "结婚", "分手", "离婚",
        "复合", "对象", "另一半", "桃花", "姻缘", "相亲", "暗恋",
        "喜欢", "配偶", "情侣", "夫妻", "出轨", "前任", "暧昧",
        "正缘", "脱单", "单身", "能不能脱单",
    ],
    "compatibility": [
        "合盘", "合不合", "适合结婚", "匹配", "配不配", "合婚",
        "八字合", "合得来", "搭不搭", "配对", "夫妻相", "兼容",
        "两个人合", "我们合", "我俩", "是否合适",
    ],
    "yearly": [
        "今年", "年度", "流年", "年运", "这一年", "今年运势",
        "本年", "全年", "一整年", "这年",
    ],
    "monthly": [
        "本月", "月运", "这个月", "这个月运势", "月度", "当月",
        "这月", "这月整体",
    ],
    "daily": [
        "今日", "今天", "每日", "日运", "今天运势", "今日运势",
        "今天运气", "每日运势",
    ],
    "decision": [
        "该不该", "要不要", "能不能", "是否应该", "如何选择",
        "选哪个", "去还是", "留还是", "二选一", "抉择", "决定",
        "怎么选", "应不应该", "到底该", "我该",
    ],
    "timing": [
        "什么时候", "何时", "几月", "哪天", "还要多久",
        "什么时候能", "还要等多久", "最佳时机", "什么时间",
        "哪一年", "时机", "要等多久",
    ],
    "fengshui": [
        "风水", "房子", "搬家", "卧室", "办公室", "方位",
        "装修", "户型", "朝向", "选房", "买楼", "选址", "布局",
        "家居", "住宅", "乔迁", "盖房",
    ],
    "health_reflection": [
        "健康", "压力", "睡眠", "身体状态", "身体怎么样", "健康吗",
        "精神状态", "身心", "养生", "调理", "疲劳", "失眠",
        "身体", "体力", "精力",
    ],
}

# ── 组合模式（优先级高于单词匹配）──────────────────────────────────────────

_PATTERN_MAP: list[tuple[str, str]] = [
    # compatibility — 两个人生日/两个人的场景
    (r"(我们?俩|两个人?|我和他|我和她|双方).{0,10}(合不合|配不配|是否合适|合得来|搭不搭)", "compatibility"),
    (r"合盘|合婚|八字合|配对", "compatibility"),
    # yearly
    (r"今年.{0,5}(运势|运程|运气|怎么样|如何)|流年.{0,5}(运势|运程)", "yearly"),
    (r"今年|这一年|全年|一整年", "yearly"),
    # monthly
    (r"(这个月|本月|当月).{0,5}(运势|运程|运气|怎么样)", "monthly"),
    (r"月运|月度运势", "monthly"),
    # daily
    (r"(今天|今日|今天).{0,5}(运势|运程|运气|怎么样)", "daily"),
    (r"日运|每日运势", "daily"),
    # decision
    (r"该不该|要不要|能不能|是否应该|应不应该", "decision"),
    (r"(去还是|留还是|二选一|怎么选|到底该|我该)", "decision"),
    # timing
    (r"什么时候|何时|几月|哪天|还要多久|什么时间|哪一年", "timing"),
    # fengshui
    (r"风水|(房子|住宅|家居|办公室|卧室|装修|选房|买楼|搬家|乔迁)", "fengshui"),
    # health_reflection — non-medical only
    (r"(我|最近|这段时间).{0,5}(身体|健康|睡眠|压力|精神|疲劳).{0,5}(怎么样|如何|状态|好吗)", "health_reflection"),
    (r"(身体|健康|睡眠|压力|精神).{0,3}(调理|自省|反思|状态)", "health_reflection"),
    # career
    (r"(换|跳|找|辞|升).{0,3}(工作|职|槽)|(工作|事业|职场).{0,5}(发展|前景|怎么样)", "career"),
    # wealth
    (r"财.{0,2}(运|怎么样|如何)|(赚钱|收入|投资|理财)", "wealth"),
    # relationship
    (r"(感情|恋爱|爱情|婚姻|桃花|姻缘|脱单)", "relationship"),
    # general_life (catch-most)
    (r"命.{0,2}(盘|运|怎么样|如何|格)|(排盘|算命|运势|命运|综合)", "general_life"),
]


def classify_intent(question: str, goal: Optional[str] = None) -> dict[str, Any]:
    """对用户问题进行意图分类，返回标准 goal 类型。

    INT-001: classify_intent() — 输入问题，返回 goal
    INT-014: 用户显式传 goal 时优先使用

    Args:
        question: 用户自然语言问题
        goal: 用户显式指定的 goal（可选），传入时跳过分类

    Returns:
        {
            "goal": "career",
            "goal_label": "事业工作",
            "goal_confidence": 0.85,
            "goal_source": "explicit" | "classified",
            "sub_goals": [...],
            "domain_scores": {...},
            "needs_birth": True,
            "needs_space": False,
        }
    """
    # INT-014: 显式 goal 覆盖
    if goal and goal in GOAL_TYPES:
        return _build_result(goal, 1.0, "explicit", {goal: 1.0})

    if goal:
        # 用户传了 goal 但不在标准列表中 → 仍然尝试匹配，同时记录
        return _build_result(
            _classify(question)["goal"],
            _classify(question)["goal_confidence"],
            "classified",
            _classify(question)["domain_scores"],
            note=f"用户传入未知 goal='{goal}'，已自动分类",
        )

    return _classify(question)


def _classify(question: str) -> dict[str, Any]:
    """核心分类逻辑。"""
    q = question.lower().strip()

    # Step 1: 正则模式匹配（加分）
    domain_hits: dict[str, float] = {}
    for pattern, goal_type in _PATTERN_MAP:
        if re.search(pattern, q):
            domain_hits[goal_type] = domain_hits.get(goal_type, 0) + 4.0

    # Step 2: 关键词匹配（加分）
    for goal_type, keywords in _KEYWORD_MAP.items():
        for kw in keywords:
            if kw in q:
                # 更长的关键词权重更高
                domain_hits[goal_type] = domain_hits.get(goal_type, 0) + min(len(kw), 6)

    # Step 3: 确定主 goal
    if not domain_hits:
        primary = "general_life"
        confidence = 0.3
        sub_goals = ["general_life"]
    else:
        sorted_goals = sorted(domain_hits.items(), key=lambda x: -x[1])
        primary = sorted_goals[0][0]
        total_score = sum(v for _, v in sorted_goals)
        primary_score = sorted_goals[0][1]
        confidence = min(0.95, primary_score / max(1, total_score) * 0.85 + 0.15)
        # 子 goal：得分 >= 25% 主 goal 分
        threshold = primary_score * 0.25
        sub_goals = [d for d, s in sorted_goals if s >= threshold]

    # Step 4: 计算各 goal 得分
    max_score = max(domain_hits.values()) if domain_hits else 1
    domain_scores = {
        d: round(s / max_score, 2)
        for d, s in sorted(domain_hits.items(), key=lambda x: -x[1])[:8]
    }

    return _build_result(primary, confidence, "classified", domain_scores, sub_goals)


def _build_result(
    goal: str,
    confidence: float,
    source: str,
    domain_scores: dict[str, float],
    sub_goals: list[str] | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """构建统一返回结构。"""
    result: dict[str, Any] = {
        "goal": goal,
        "goal_label": GOAL_LABELS.get(goal, goal),
        "goal_confidence": round(confidence, 2),
        "goal_source": source,
        "sub_goals": sub_goals or [goal],
        "domain_scores": domain_scores,
        "needs_birth": goal not in ("daily",),
        "needs_space": goal == "fengshui",
    }
    if note:
        result["note"] = note
    return result


# ── 向后兼容 ─────────────────────────────────────────────────────────────────

def classify(question: str) -> dict[str, Any]:
    """向后兼容的 alias — 返回旧格式。

    新代码应使用 classify_intent()。
    """
    result = classify_intent(question)
    goal = result["goal"]
    return {
        "primary_domain": goal,
        "primary_label": result["goal_label"],
        "sub_domains": result.get("sub_goals", [goal]),
        "confidence": result["goal_confidence"],
        "needs_birth": result["needs_birth"],
        "needs_space": result["needs_space"],
        "suggested_methods": None,
        "domain_scores": result.get("domain_scores", {}),
    }
