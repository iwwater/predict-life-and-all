"""问题意图分类器 — 输入自然语言问题，返回标准 goal 类型。

BE-003: 问题分类
INT-001: classify_intent() — 输入问题，返回 goal
INT-002~013: 支持 12 个 goal 类型
INT-014: 支持显式 goal 覆盖

Sprint 1.1 重写（参考 arxiv 2103.02559 two-stage FSM + AWS Lex V2 0-1 confidence）:
- 显式 FSM 状态: START → RULE_MATCHED → RESOLVED
                    → LOW_CONF → LLM_PENDING → RESOLVED
                    → LOW_CONF → FALLBACK (无 LLM 客户端)
- 阈值: top_score ≥ 0.70 → 直接 resolve
        0.50 ≤ top_score < 0.70 → 触发 LLM 兜底
        top_score < 0.50 → 直接降级 general_life
- LLM 客户端通过 set_llm_client() 注入（默认 None → 降级）
- LLM 结果按 question 文本 hash LRU cache 1000 条
- 失败时降级到 top candidate + flag llm_timeout/llm_error

向后兼容:
- classify_intent() 返回 dict (与 cases.py / reading.py 保持兼容)
- 新增 classify_intent_v2() 返回 IntentResult Pydantic 模型 (内部用)
- 旧 classify() alias 保留
"""
from __future__ import annotations

import hashlib
import re
import time
from collections import OrderedDict
from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, Field

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

# ── FSM 阈值 (参考 arxiv 2103.02559 + Lex V2 0-1 置信度) ─────────────────
#
# 设计要点: 归一化 score 永远以最高分为 1.0, 无法作 FSM 分支依据。
# 改用 evidence_count (命中证据条数) 做 FSM 决策:
#   evidence_count ≥ EVIDENCE_RESOLVE  → RULE_MATCHED → RESOLVED (高置信)
#   evidence_count ≥ EVIDENCE_LLM      → LLM_PENDING → RESOLVED / FALLBACK
#   evidence_count <  EVIDENCE_LLM     → FALLBACK → RESOLVED (降级)
#
# normalized_score (0-1) 仍保留, 仅用于 domain_scores 展示, 不参与 FSM 决策。

EVIDENCE_RESOLVE = 2      # 命中 ≥2 条证据(模式+关键词混合) → 高置信 resolve
EVIDENCE_LLM     = 1      # 命中 1 条证据 → 触发 LLM 兜底
LLM_CACHE_SIZE = 1000
LLM_TIMEOUT_S  = 3.0       # LLM 兜底超时阈值


# ── FSM 状态 ──────────────────────────────────────────────────────────────

class FSMState(str, Enum):
    """意图分类 FSM 状态 — 用于追踪和诊断。"""
    START          = "start"
    RULE_MATCHED   = "rule_matched"        # 规则层拿到 winner
    LOW_CONF       = "low_conf"            # 规则层 winner 不足, 走 LLM
    LLM_PENDING    = "llm_pending"         # 调用 LLM 中
    RESOLVED       = "resolved"            # 最终结果已定
    FALLBACK       = "fallback"            # 降级到 general_life


# ── LLM 客户端协议 (依赖反转 — 业务代码不耦合具体 SDK) ───────────────────

class LLMClient(Protocol):
    """LLM 客户端协议。任何 LLM SDK 适配器实现此协议即可注入。"""

    def classify(
        self,
        question: str,
        candidates: list[tuple[str, float]],
        taxonomy: list[str],
    ) -> dict[str, Any] | None:
        """对 question 在 taxonomy 中分类。

        Args:
            question: 原始问题
            candidates: 规则层 top-3 [(goal, score), ...]
            taxonomy: 12 个标准 goal

        Returns:
            {"goal": "career", "confidence": 0.85} 或 None (失败)
        """


# ── LLM 客户端注入 (单例) ─────────────────────────────────────────────────

_LLM_CLIENT: LLMClient | None = None
_LLM_CACHE: "OrderedDict[str, dict[str, Any]]" = OrderedDict()


def set_llm_client(client: LLMClient | None) -> None:
    """注入 LLM 客户端。传 None 关闭 LLM 兜底。"""
    global _LLM_CLIENT
    _LLM_CLIENT = client
    # 注入新客户端时清缓存 (旧缓存可能用了旧 schema)
    _LLM_CACHE.clear()


def get_llm_client() -> LLMClient | None:
    """获取当前 LLM 客户端 (供测试/debug)。"""
    return _LLM_CLIENT


def clear_llm_cache() -> None:
    """清空 LLM 结果缓存。"""
    _LLM_CACHE.clear()


def llm_cache_stats() -> dict[str, int]:
    """返回 LLM 缓存统计。"""
    return {
        "size": len(_LLM_CACHE),
        "max_size": LLM_CACHE_SIZE,
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


# ── 内部模型 ──────────────────────────────────────────────────────────────

class IntentResult(BaseModel):
    """意图分类结果 — 内部 Pydantic 模型。"""
    goal: str
    goal_label: str
    goal_confidence: float
    goal_source: str       # explicit | classified | llm_fallback | fallback
    sub_goals: list[str]
    domain_scores: dict[str, float]
    needs_birth: bool
    needs_space: bool
    fsm_state: FSMState
    fsm_trace: list[str]   # FSM 状态转移轨迹, 供 debug
    note: str | None = None
    flags: list[str] = Field(default_factory=list)


# ── 规则层评分 ────────────────────────────────────────────────────────────

def _rule_score(question: str) -> dict[str, float]:
    """规则层评分 — 返回 {goal: 归一化分数 0-1} + evidence_count (命中证据条数)。

    Args:
        question: 用户原始问题

    Returns:
        {
            "scores": {goal: 归一化分数 0-1, ...},
            "evidence_count": int,  # 总命中证据数(模式+关键词去重)
            "top_goal": str,        # 最高分 goal
            "raw_top": float,       # 最高原始分(未归一化)
        }

    计分规则 (参考 Lex V2 / Rasa 实践):
      正则模式命中: +4.0 (高优先级, 表达明确意图)
      关键词命中: +min(len(keyword), 6) (更长的关键词权更高)
      归一化: 取最高分 = 1.0, 其余按比例归一化

    FSM 分支用 evidence_count, scores 仅供展示。
    """
    q = question.lower().strip()
    domain_hits: dict[str, float] = {}
    evidence_count = 0

    # Step 1: 正则模式
    for pattern, goal_type in _PATTERN_MAP:
        if re.search(pattern, q):
            domain_hits[goal_type] = domain_hits.get(goal_type, 0) + 4.0
            evidence_count += 1

    # Step 2: 关键词
    for goal_type, keywords in _KEYWORD_MAP.items():
        for kw in keywords:
            if kw in q:
                domain_hits[goal_type] = domain_hits.get(goal_type, 0) + min(len(kw), 6)
                evidence_count += 1

    if not domain_hits:
        return {
            "scores": {},
            "evidence_count": 0,
            "top_goal": "general_life",
            "raw_top": 0.0,
        }

    # 归一化: max → 1.0
    max_score = max(domain_hits.values())
    scores = {g: round(s / max_score, 3) for g, s in domain_hits.items()}
    top_goal = max(domain_hits, key=domain_hits.get)
    return {
        "scores": scores,
        "evidence_count": evidence_count,
        "top_goal": top_goal,
        "raw_top": domain_hits[top_goal],
    }


def _top_n(scores: dict[str, float], n: int = 3) -> list[tuple[str, float]]:
    """取 top-N (goal, score)。"""
    return sorted(scores.items(), key=lambda x: -x[1])[:n]


# ── FSM 兜底 LLM 调用 ────────────────────────────────────────────────────

def _llm_fallback_classify(
    question: str,
    candidates: list[tuple[str, float]],
) -> dict[str, Any] | None:
    """调用 LLM 兜底分类。带超时 + cache。

    Returns:
        {"goal": "career", "confidence": 0.85} 或 None
    """
    if _LLM_CLIENT is None:
        return None

    cache_key = hashlib.sha256(question.encode("utf-8")).hexdigest()
    if cache_key in _LLM_CACHE:
        # LRU: 移动到末尾
        _LLM_CACHE.move_to_end(cache_key)
        return _LLM_CACHE[cache_key]

    t0 = time.perf_counter()
    try:
        result = _LLM_CLIENT.classify(
            question=question,
            candidates=candidates,
            taxonomy=GOAL_TYPES,
        )
    except Exception:
        result = None
    elapsed = time.perf_counter() - t0

    if result is None:
        return None

    # 校验: goal 必须在 taxonomy 中, confidence 0-1
    goal = result.get("goal") if isinstance(result, dict) else None
    conf = result.get("confidence", 0.0) if isinstance(result, dict) else 0.0
    if goal not in GOAL_TYPES or not (0.0 <= conf <= 1.0):
        return None

    # 超时: 即使返回了 result, 视为不可信
    if elapsed > LLM_TIMEOUT_S:
        return None

    payload = {"goal": goal, "confidence": float(conf), "elapsed_ms": int(elapsed * 1000)}
    _LLM_CACHE[cache_key] = payload
    if len(_LLM_CACHE) > LLM_CACHE_SIZE:
        _LLM_CACHE.popitem(last=False)
    return payload


# ── FSM 核心: classify_intent_v2() ────────────────────────────────────────

def classify_intent_v2(
    question: str,
    goal: str | None = None,
) -> IntentResult:
    """显式 FSM 意图分类。返回 IntentResult 模型。

    FSM 状态转移:
      START
        ├── goal 在 GOAL_TYPES         → RESOLVED (explicit)
        ├── goal 给了但不在白名单     → LOW_CONF (走分类, 标 note)
        └── goal = None
            ├── 规则层 top ≥ 0.70      → RULE_MATCHED → RESOLVED (classified)
            ├── 规则层 top ∈ [0.50, 0.70)
            │     ├── LLM 客户端有     → LLM_PENDING → RESOLVED (llm_fallback)
            │     └── LLM 客户端无     → FALLBACK → RESOLVED (fallback)
            └── 规则层 top < 0.50      → FALLBACK → RESOLVED (fallback)
    """
    trace: list[str] = [FSMState.START.value]

    # Step 1: 显式 goal 优先
    if goal and goal in GOAL_TYPES:
        trace.append(FSMState.RESOLVED.value)
        return IntentResult(
            goal=goal,
            goal_label=GOAL_LABELS.get(goal, goal),
            goal_confidence=1.0,
            goal_source="explicit",
            sub_goals=[goal],
            domain_scores={goal: 1.0},
            needs_birth=goal not in ("daily",),
            needs_space=goal == "fengshui",
            fsm_state=FSMState.RESOLVED,
            fsm_trace=trace,
        )

    # Step 2: 规则层评分
    rule = _rule_score(question)
    scores = rule["scores"]
    evidence_count = rule["evidence_count"]
    top = _top_n(scores, 3)
    if top:
        top_goal = rule["top_goal"]
        top_score = scores[top_goal]  # 归一化分数, 展示用
    else:
        top_goal = "general_life"
        top_score = 0.0
        top = [("general_life", 0.0)]

    # Step 3: FSM 状态转移 (用 evidence_count 而非归一化 score)
    flags: list[str] = []
    note: str | None = None

    if evidence_count >= EVIDENCE_RESOLVE:
        # 多条证据命中 → 高置信 resolve
        trace.append(FSMState.RULE_MATCHED.value)
        trace.append(FSMState.RESOLVED.value)
        # 置信度基于证据数 + 归一化分
        confidence = min(0.95, 0.55 + evidence_count * 0.08 + top_score * 0.2)
        threshold = top_score * 0.25
        sub_goals = [g for g, s in top if s >= threshold] or [top_goal]
        return IntentResult(
            goal=top_goal,
            goal_label=GOAL_LABELS.get(top_goal, top_goal),
            goal_confidence=round(confidence, 2),
            goal_source="classified",
            sub_goals=sub_goals,
            domain_scores={g: round(s, 2) for g, s in top},
            needs_birth=top_goal not in ("daily",),
            needs_space=top_goal == "fengshui",
            fsm_state=FSMState.RESOLVED,
            fsm_trace=trace,
        )

    trace.append(FSMState.LOW_CONF.value)

    if evidence_count < EVIDENCE_LLM:
        # 零证据 → 降级 general_life
        trace.append(FSMState.FALLBACK.value)
        trace.append(FSMState.RESOLVED.value)
        flags.append("rule_low_conf")
        return IntentResult(
            goal="general_life",
            goal_label=GOAL_LABELS["general_life"],
            goal_confidence=0.3,
            goal_source="fallback",
            sub_goals=["general_life"],
            domain_scores={g: round(s, 2) for g, s in top},
            needs_birth=True,
            needs_space=False,
            fsm_state=FSMState.FALLBACK,
            fsm_trace=trace,
            note="问题意图不明确, 降级到 general_life",
            flags=flags,
        )

    # 单条证据 → 走 LLM 兜底
    trace.append(FSMState.LLM_PENDING.value)
    llm_result = _llm_fallback_classify(question, top)

    if llm_result is None:
        # LLM 不可用/超时 → 降级到 top candidate (但保留原 score)
        trace.append(FSMState.FALLBACK.value)
        if _LLM_CLIENT is None:
            flags.append("llm_unavailable")
            note = "LLM 客户端未注入, 使用规则层结果"
        else:
            flags.append("llm_error_or_timeout")
            note = "LLM 调用失败/超时, 使用规则层结果"
        confidence = min(0.65, 0.4 + top_score * 0.2)
        return IntentResult(
            goal=top_goal,
            goal_label=GOAL_LABELS.get(top_goal, top_goal),
            goal_confidence=round(confidence, 2),
            goal_source="fallback",
            sub_goals=[g for g, _ in top],
            domain_scores={g: round(s, 2) for g, s in top},
            needs_birth=top_goal not in ("daily",),
            needs_space=top_goal == "fengshui",
            fsm_state=FSMState.FALLBACK,
            fsm_trace=trace,
            note=note,
            flags=flags,
        )

    # LLM 返回有效结果
    trace.append(FSMState.RESOLVED.value)
    llm_goal = llm_result["goal"]
    llm_conf = llm_result["confidence"]
    flags.append("llm_used")
    return IntentResult(
        goal=llm_goal,
        goal_label=GOAL_LABELS.get(llm_goal, llm_goal),
        goal_confidence=round(llm_conf, 2),
        goal_source="llm_fallback",
        sub_goals=[llm_goal, top_goal] if llm_goal != top_goal else [llm_goal],
        domain_scores={g: round(s, 2) for g, s in top},
        needs_birth=llm_goal not in ("daily",),
        needs_space=llm_goal == "fengshui",
        fsm_state=FSMState.RESOLVED,
        fsm_trace=trace,
        flags=flags,
    )


# ── 向后兼容: classify_intent() 返回 dict ──────────────────────────────

def classify_intent(question: str, goal: str | None = None) -> dict[str, Any]:
    """对用户问题进行意图分类，返回标准 goal 类型。

    INT-001: classify_intent() — 输入问题，返回 goal
    INT-014: 用户显式传 goal 时优先使用 (Sprint 1.1: explicit 走 FSM 快速通道)
    """
    # 显式 goal 走老分支 (保持 dict 结构 + note 兼容老测试)
    if goal and goal in GOAL_TYPES:
        return _build_dict_result(
            goal=goal,
            confidence=1.0,
            source="explicit",
            domain_scores={goal: 1.0},
            sub_goals=[goal],
        )

    # 显式 goal 但不在白名单 → 走分类, 标 note (兼容老测试 test_unknown_goal_falls_back_to_classify)
    if goal:
        result = classify_intent_v2(question, goal=None)
        d = _result_to_dict(result)
        d["note"] = f"用户传入未知 goal='{goal}'，已自动分类"
        return d

    # 走完整 FSM
    result = classify_intent_v2(question, goal=None)
    return _result_to_dict(result)


def _result_to_dict(r: IntentResult) -> dict[str, Any]:
    """IntentResult → dict (向后兼容 cases.py / reading.py)。"""
    out: dict[str, Any] = {
        "goal": r.goal,
        "goal_label": r.goal_label,
        "goal_confidence": r.goal_confidence,
        "goal_source": r.goal_source,
        "sub_goals": r.sub_goals,
        "domain_scores": r.domain_scores,
        "needs_birth": r.needs_birth,
        "needs_space": r.needs_space,
        "fsm_state": r.fsm_state.value,
        "fsm_trace": r.fsm_trace,
        "flags": r.flags,
    }
    if r.note:
        out["note"] = r.note
    return out


def _build_dict_result(
    goal: str,
    confidence: float,
    source: str,
    domain_scores: dict[str, float],
    sub_goals: list[str] | None = None,
) -> dict[str, Any]:
    """构造 legacy dict 格式 (仅 explicit 路径用)。"""
    return {
        "goal": goal,
        "goal_label": GOAL_LABELS.get(goal, goal),
        "goal_confidence": round(confidence, 2),
        "goal_source": source,
        "sub_goals": sub_goals or [goal],
        "domain_scores": domain_scores,
        "needs_birth": goal not in ("daily",),
        "needs_space": goal == "fengshui",
        "fsm_state": FSMState.RESOLVED.value,
        "fsm_trace": [FSMState.START.value, FSMState.RESOLVED.value],
        "flags": [],
    }


# ── 向后兼容: classify() alias ────────────────────────────────────────────

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
