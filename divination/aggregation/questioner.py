"""追问编排器 — 12 goal × 声明式题池 + 自适应选择。

Sprint 1.2 设计:
- QuestionPool: 每 goal 声明 1-3 个候选问题模板
- pick_questions(goal, context) -> list[Question] 最多 2 问
- 自适应: 已填的 context 字段自动跳过对应问题
- 确定性: 同 intent + context → 同 questions
- 升级后接入 cases.py, 替换原 _minimal_questions() 内联实现

题池来源参考 (公开发布的"会审/咨询"实践, 不引用具体竞品):
- 心理咨询初始访谈: 先开放后聚焦
- 医疗问诊: 主诉 → 现病史 → 既往史
- 心理咨询师培训: 每次会话只问 1-2 个关键问题, 不超载
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# ── 公开 API ──────────────────────────────────────────────────────────────

QuestionType = Literal["single_choice", "multi_choice", "text", "scale"]


class Question(BaseModel):
    """单个追问问题。

    id       : 稳定 ID, 客户端用做 answer key
    prompt   : 问题正文
    options  : 候选项 (single_choice / multi_choice 必填)
    required : 是否必答
    type     : single_choice / multi_choice / text / scale
    impact   : 信息增益 1-10, 越大越优先选
    reason   : 为什么问 (给客户端展示, 提升用户完成率)
    skip_if  : 如果 context 含这些 key 且非空, 跳过
    """
    id: str
    prompt: str
    type: QuestionType = "single_choice"
    options: list[str] = Field(default_factory=list)
    required: bool = True
    impact: float = 5.0
    reason: str = ""
    skip_if: list[str] = Field(default_factory=list)


# ── 题池 (声明式 — 每 goal 一组候选) ─────────────────────────────────────

QUESTION_POOL: dict[str, list[Question]] = {
    # ── 事业 ──
    "career": [
        Question(
            id="offer_status",
            prompt="是否已有明确的新机会或 offer？",
            options=["已有正式 offer", "只有口头意向", "还在探索"],
            impact=9.0,
            reason="有/无 offer 决定是否启用'辞职决断'逻辑",
        ),
        Question(
            id="cash_reserve_months",
            prompt="现金储备能支撑多久无收入生活？",
            options=["<1 个月", "1-3 个月", "3-6 个月", "6-12 个月", ">12 个月"],
            impact=8.5,
            reason="现金储备决定命理建议的风险承受度",
            skip_if=["cash_reserve_months"],
        ),
    ],
    # ── 财运 ──
    "wealth": [
        Question(
            id="investment_horizon",
            prompt="这笔决策的时间跨度是？",
            options=["短期 (<3 月)", "中期 (3-12 月)", "长期 (1-5 年)", "超长期 (>5 年)"],
            impact=8.0,
            reason="时间跨度决定该看哪一档信号 (流月/流年/限运)",
        ),
        Question(
            id="risk_tolerance",
            prompt="你能承受多大的本金波动？",
            options=["极保守 (5% 以内)", "保守 (10% 以内)", "中等 (20% 以内)", "激进 (>20%)"],
            impact=8.5,
            reason="命理层面的'机会'需匹配你的承受度, 不然建议就脱节",
        ),
    ],
    # ── 感情 ──
    "relationship": [
        Question(
            id="relationship_status",
            prompt="你们目前是什么状态？",
            options=["单身中", "暧昧中", "交往中", "分开后想复合", "已婚"],
            impact=9.5,
            reason="不同状态推算的命理信号完全不同",
        ),
        Question(
            id="primary_concern",
            prompt="你最想了解的是哪方面？",
            options=["缘分是否到了", "对方是否真心", "相处如何推进", "未来发展走势"],
            impact=7.5,
            reason="聚焦维度提升解读深度",
        ),
    ],
    # ── 合盘 ──
    "compatibility": [
        Question(
            id="relationship_stage",
            prompt="你们现在处于哪个阶段？",
            options=["刚认识", "暧昧中", "交往中", "同居/订婚", "已婚"],
            impact=9.0,
            reason="不同阶段看盘重点不同 (新关系看缘分, 已婚看长期)",
        ),
        Question(
            id="primary_concern",
            prompt="你最关心的方向是？",
            options=["是否合适长期", "性格是否合得来", "事业财运互助", "家庭子女安排"],
            impact=7.5,
            reason="聚焦维度提升解读深度",
        ),
    ],
    # ── 决策 ──
    "decision": [
        Question(
            id="offer_status",
            prompt="是否已有具体备选项 / offer / 对象？",
            options=["已有明确对象", "有几个待选", "还在评估", "没有具体对象"],
            impact=9.5,
            reason="决策对象明确度决定建议是'对比'还是'探索'",
        ),
        Question(
            id="reversibility",
            prompt="这个决定的可逆性如何？",
            options=["完全可逆 (试试看)", "短期可逆 (1-3 月可调)", "难逆 (1-3 年)", "不可逆"],
            impact=9.0,
            reason="可逆性不同, 命理建议的冒险策略不同",
        ),
        Question(
            id="urgency",
            prompt="这个决定需要在多久内做？",
            options=["<1 周", "1-4 周", "1-3 月", "3-12 月", "不急"],
            impact=8.0,
            reason="紧迫度决定建议的颗粒度",
        ),
    ],
    # ── 时机 ──
    "timing": [
        Question(
            id="deadline",
            prompt="你说的'时机'是有外部期限吗？",
            options=["有明确截止 (如合同/签证)", "软性期限 (项目周期)", "没期限, 想知道'最佳'", "自己想设个目标"],
            impact=9.0,
            reason="有外部期限走精确推算, 无期限走趋势分析",
        ),
    ],
    # ── 流年 ──
    "yearly": [
        Question(
            id="focus_areas",
            prompt="今年你重点关注哪几个方面？",
            type="multi_choice",
            options=["事业", "财运", "感情", "健康", "家庭", "学业"],
            impact=8.0,
            reason="多领域聚焦, 解读可分章呈现",
        ),
    ],
    # ── 月运 ──
    "monthly": [
        Question(
            id="focus_areas",
            prompt="本月最关注什么？",
            type="multi_choice",
            options=["事业", "财运", "感情", "健康", "人际"],
            impact=7.5,
            reason="聚焦维度, 解读不散",
        ),
    ],
    # ── 日运 ──
    "daily": [
        Question(
            id="focus_areas",
            prompt="今天最想了解什么？",
            type="single_choice",
            options=["整体运势", "工作", "财运", "感情", "健康提醒"],
            impact=7.0,
            reason="日运聚焦, 一句话即可",
        ),
    ],
    # ── 风水 ──
    "fengshui": [
        Question(
            id="space_focus",
            prompt="你主要看哪个空间？",
            options=["客厅", "主卧", "书房/办公室", "厨房", "入户门", "整体户型"],
            impact=9.0,
            reason="空间不同, 看的星/卦不同",
        ),
        Question(
            id="concern",
            prompt="你重点关心什么？",
            options=["居住健康", "睡眠质量", "财运", "工作事业", "感情关系", "整体平衡"],
            impact=7.5,
            reason="风水调整有侧重, 聚焦后建议更可操作",
        ),
    ],
    # ── 健康自省 ──
    "health_reflection": [
        Question(
            id="duration",
            prompt="这种状态持续多久了？",
            options=["<1 周", "1-4 周", "1-3 月", ">3 月", "长期慢性"],
            impact=8.0,
            reason="持续时间决定信号解读 (短期 vs 长期)",
        ),
        Question(
            id="intensity",
            prompt="强度如何？",
            type="scale",
            options=["轻微", "中等", "明显", "严重影响生活"],
            impact=7.5,
            reason="强度不同, 自省建议的节奏不同",
        ),
    ],
    # ── 本命格局 (general) ──
    "general_life": [
        Question(
            id="focus_areas",
            prompt="你最想深入了解哪些方面？",
            type="multi_choice",
            options=["事业", "财运", "感情", "健康", "家庭", "学业", "人际"],
            impact=7.5,
            reason="多领域聚焦, 解读分章呈现",
        ),
    ],
    # ── 兜底 ──
    "fallback": [
        Question(
            id="primary_concern",
            prompt="你目前最关心的方向是？",
            options=["事业工作", "财运", "感情关系", "健康", "风水", "综合"],
            impact=9.0,
            reason="未知意图, 先聚焦一个方向",
        ),
    ],
}

# ── 自适应选择算法 ───────────────────────────────────────────────────────

def _is_filled(context: dict[str, Any], key: str) -> bool:
    """判断 context[key] 是否已填 (非空)。"""
    val = context.get(key)
    if val is None:
        return False
    if isinstance(val, str) and val.strip() == "":
        return False
    if isinstance(val, (list, dict)) and len(val) == 0:
        return False
    return True


def pick_questions(
    goal: str,
    context: dict[str, Any] | None = None,
    max_n: int = 2,
) -> list[Question]:
    """根据 goal 和已有 context, 自适应选出最多 max_n 个追问。

    算法:
      1. 从 QUESTION_POOL[goal] 取候选列表 (未在白名单 → fallback 兜底)
      2. 跳过条件 (任一):
         a) skip_if 中任一字段已填
         b) q.id 本身已在 context 中且已填 (用户已答过)
      3. 按 impact 降序 (二级: 原始题池顺序)
      4. 取前 max_n 个

    确定性: 同 (goal, context, max_n) → 同结果。
    """
    pool = QUESTION_POOL.get(goal, QUESTION_POOL["fallback"])
    ctx = context or {}

    # Step 1-2: 过滤
    candidates: list[Question] = []
    for q in pool:
        # 2a: skip_if 命中
        if any(_is_filled(ctx, k) for k in q.skip_if):
            continue
        # 2b: 同 id 已答
        if _is_filled(ctx, q.id):
            continue
        candidates.append(q)

    # Step 3: 排序 (impact desc, 原始 index asc 二级)
    indexed = list(enumerate(candidates))
    indexed.sort(key=lambda x: (-x[1].impact, x[0]))
    sorted_qs = [q for _, q in indexed]

    # Step 4: 取 top max_n
    return sorted_qs[:max_n]


# ── 业务层便捷包装 ───────────────────────────────────────────────────────

def get_questions_for_case(
    intent: dict[str, Any],
    context: dict[str, Any] | None = None,
    max_n: int = 2,
) -> list[Question]:
    """从 cases.py 调用的便捷接口。

    Args:
        intent: classify_intent() 返回的 dict, 含 "goal"
        context: 已有 context dict (含 answers/constraints)
        max_n: 最多几个问题

    Returns:
        list[Question] — 客户端按顺序展示
    """
    goal = intent.get("goal", "general_life")
    if intent.get("flags") and "rule_low_conf" in intent["flags"]:
        # 兜底场景, 推 fallback 题目
        goal = "fallback"
    return pick_questions(goal=goal, context=context or {}, max_n=max_n)


# ── 测试辅助 ─────────────────────────────────────────────────────────────

def list_all_goals_with_questions() -> list[str]:
    """返回有定义追问的 goal 列表 (供 admin/调试)。"""
    return sorted(QUESTION_POOL.keys())


def question_count(goal: str) -> int:
    """某 goal 的题池大小 (含会被 skip 的)。"""
    return len(QUESTION_POOL.get(goal, []))
