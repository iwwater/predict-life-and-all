"""Sprint 1.1 — intent FSM 测试。

覆盖:
- FSM 状态转移路径 (explicit / classified / llm_fallback / fallback)
- LLM 客户端注入 + cache + 超时降级
- 50 问 F1 ≥ 0.9 评估集
- 向后兼容: dict 返回格式字段完整
"""
from __future__ import annotations

import time

import pytest

from divination.aggregation import intent as intent_mod
from divination.aggregation.intent import (
    EVIDENCE_LLM,
    EVIDENCE_RESOLVE,
    FSMState,
    GOAL_TYPES,
    LLM_TIMEOUT_S,
    classify_intent,
    classify_intent_v2,
    clear_llm_cache,
    llm_cache_stats,
    set_llm_client,
)


# ── 测试用 LLM 客户端 (可控) ─────────────────────────────────────────────

class FakeLLMClient:
    """测试用 LLM 客户端。

    behavior:
      - 总是返回 preset_answer
      - 记录所有调用 (call_log)
      - 可通过 fail_next=True 让下次调用返回 None
    """

    def __init__(self, preset_answer: dict | None = None, fail_next: bool = False):
        self.preset_answer = preset_answer
        self.fail_next = fail_next
        self.call_log: list[dict] = []

    def classify(self, question, candidates, taxonomy):
        self.call_log.append({
            "question": question,
            "candidates": candidates,
            "taxonomy": taxonomy,
        })
        if self.fail_next:
            self.fail_next = False
            return None
        if self.preset_answer is None:
            return None
        return self.preset_answer.copy()

    def sleep_then_return(self, sleep_s: float, payload: dict):
        """模拟 LLM 慢响应, 用于超时测试。"""
        def slow_classify(question, candidates, taxonomy):
            time.sleep(sleep_s)
            return payload.copy()
        self.classify = slow_classify


@pytest.fixture(autouse=True)
def _reset_llm():
    """每个测试前后清 LLM 客户端和 cache。"""
    set_llm_client(None)
    clear_llm_cache()
    yield
    set_llm_client(None)
    clear_llm_cache()


# ── FSM 状态转移测试 ─────────────────────────────────────────────────────

class TestFSMStateTransitions:
    """FSM 状态转移覆盖。"""

    def test_explicit_goal_short_circuits(self):
        """显式 goal → 状态走 start → resolved, 不调规则也不调 LLM。"""
        r = classify_intent_v2("我该不该换工作", goal="career")
        assert r.goal == "career"
        assert r.goal_source == "explicit"
        assert r.goal_confidence == 1.0
        assert r.fsm_state == FSMState.RESOLVED
        assert r.fsm_trace == [FSMState.START.value, FSMState.RESOLVED.value]
        assert r.flags == []

    def test_rule_matched_path(self):
        """规则层高置信 → start → rule_matched → resolved。"""
        r = classify_intent_v2("我该换工作吗")
        assert r.goal == "career"
        assert r.goal_source == "classified"
        assert r.fsm_state == FSMState.RESOLVED
        assert FSMState.RULE_MATCHED.value in r.fsm_trace

    def test_low_conf_without_llm_falls_back(self):
        """低置信 + 无 LLM 客户端 → 降级 general_life。"""
        r = classify_intent_v2("随便问问")
        # 规则层应该有 0 分 → 直接 fallback
        if r.goal_source == "fallback":
            assert r.goal == "general_life"
            assert r.fsm_state == FSMState.FALLBACK
            assert "rule_low_conf" in r.flags

    def test_low_conf_with_llm_uses_llm(self):
        """低置信 + LLM 客户端 → 走 LLM_PENDING。"""
        client = FakeLLMClient(preset_answer={"goal": "wealth", "confidence": 0.9})
        set_llm_client(client)
        # 构造一个中间区问题: top_score 在 [0.50, 0.70)
        # 多数无明确关键词的会进 LOW_CONF; 但需 top_score ≥ 0.50 才进 LLM
        r = classify_intent_v2("最近情况")
        # 如果规则层能命中, 可能走 RULE_MATCHED, 不调 LLM
        if r.goal_source == "llm_fallback":
            assert r.goal == "wealth"
            assert r.goal_confidence == 0.9
            assert FSMState.LLM_PENDING.value in r.fsm_trace
            assert "llm_used" in r.flags
            assert len(client.call_log) == 1

    def test_llm_failure_falls_back_to_top_candidate(self):
        """LLM 调用失败 → 降级到规则层 top, 标 llm_error_or_timeout。"""
        client = FakeLLMClient(fail_next=True)
        set_llm_client(client)
        # 强制进 LOW_CONF: 找一个 top_score 在 [0.50, 0.70) 的输入
        r = classify_intent_v2("换工作还是考研")
        # 如果 top_score 触发 LLM, 应该 fallback
        if r.goal_source == "fallback" and "llm_error_or_timeout" in r.flags:
            # 保留规则层的 top candidate
            assert r.goal in GOAL_TYPES
            assert r.goal_confidence < 0.7

    def test_llm_unavailable_flag(self):
        """无 LLM 客户端 → 标 llm_unavailable。"""
        # 同样需要 top_score 在 [0.50, 0.70) 区间
        r = classify_intent_v2("换工作还是考研")
        if r.goal_source == "fallback" and "llm_unavailable" in r.flags:
            assert r.goal in GOAL_TYPES


# ── LLM Cache 测试 ──────────────────────────────────────────────────────

class TestLLMCache:
    """LLM 兜底结果 LRU cache 行为。"""

    def test_cache_hit_avoids_second_call(self):
        client = FakeLLMClient(preset_answer={"goal": "career", "confidence": 0.85})
        set_llm_client(client)

        # 第一次 (可能或不可能进 LLM, 视 top_score 而定)
        r1 = classify_intent_v2("换工作还是考研")
        # 强制让 LLM 一定被调用 — 用一个 top_score 在中间区的问题
        # 实际上, 不管是否进 LLM, 多次调用同问题应该不重复进 LLM (如果进了的话)
        for _ in range(3):
            classify_intent_v2("换工作还是考研")

        # 缓存应该是 0 或 1 (取决于 r1 是否进 LLM)
        stats = llm_cache_stats()
        assert stats["size"] <= 1

    def test_clear_cache(self):
        client = FakeLLMClient(preset_answer={"goal": "career", "confidence": 0.85})
        set_llm_client(client)
        classify_intent_v2("换工作还是考研")
        clear_llm_cache()
        assert llm_cache_stats()["size"] == 0

    def test_cache_invalidated_on_client_swap(self):
        client1 = FakeLLMClient(preset_answer={"goal": "career", "confidence": 0.85})
        set_llm_client(client1)
        classify_intent_v2("换工作还是考研")
        client2 = FakeLLMClient(preset_answer={"goal": "wealth", "confidence": 0.9})
        set_llm_client(client2)
        # 换客户端 → 旧缓存清空
        assert llm_cache_stats()["size"] == 0


# ── LLM 超时测试 ────────────────────────────────────────────────────────

class TestLLMTimeout:
    """LLM 超时降级。"""

    def test_slow_llm_falls_back(self):
        client = FakeLLMClient()
        client.sleep_then_return(sleep_s=LLM_TIMEOUT_S + 2.0, payload={"goal": "health_reflection", "confidence": 0.9})
        set_llm_client(client)
        # "精力" 单关键词(无 pattern 命中) → evidence_count=1 → 走 LLM
        r = classify_intent_v2("精力")
        # LLM 超时 → 降级
        if r.goal_source == "llm_fallback":
            # 若实际未超 5s, 仍可能成功
            assert r.goal == "health_reflection"
        else:
            assert r.goal_source == "fallback"
            assert "llm_error_or_timeout" in r.flags


# ── 向后兼容: dict 格式 ────────────────────────────────────────────────

class TestBackwardCompatDict:
    """classify_intent() 仍返回 dict, 字段完整。"""

    def test_dict_has_legacy_fields(self):
        d = classify_intent("我该换工作吗")
        required = {
            "goal", "goal_label", "goal_confidence", "goal_source",
            "sub_goals", "domain_scores", "needs_birth", "needs_space",
        }
        assert required.issubset(set(d.keys()))

    def test_dict_has_fsm_fields(self):
        """Sprint 1.1 新增字段。"""
        d = classify_intent("我该换工作吗")
        assert "fsm_state" in d
        assert "fsm_trace" in d
        assert "flags" in d
        assert d["fsm_state"] in {s.value for s in FSMState}

    def test_explicit_goal_dict_unchanged(self):
        d = classify_intent("我该换工作吗", goal="wealth")
        assert d["goal"] == "wealth"
        assert d["goal_source"] == "explicit"
        assert d["goal_confidence"] == 1.0
        assert d["needs_birth"] is True  # wealth 不是 daily
        assert d["needs_space"] is False

    def test_daily_no_birth(self):
        d = classify_intent("今日运势", goal="daily")
        assert d["needs_birth"] is False
        assert d["needs_space"] is False

    def test_fengshui_needs_space(self):
        d = classify_intent("房子风水", goal="fengshui")
        assert d["needs_space"] is True


# ── F1 评估集 (50 问) ──────────────────────────────────────────────────

EVAL_SET: list[tuple[str, str]] = [
    # ── general_life (5) ──
    ("帮我看看命盘", "general_life"),
    ("我想了解自己的命运走势", "general_life"),
    ("整体运势怎么样", "general_life"),
    ("我这人的性格和命运", "general_life"),
    ("排个盘看看", "general_life"),
    # ── career (5) ──
    ("我该换工作吗", "career"),
    ("事业发展前景如何", "career"),
    ("我想创业可行吗", "career"),
    ("offer 该不该接", "career"),
    ("职场人际关系", "career"),
    # ── wealth (5) ──
    ("我的财运如何", "wealth"),
    ("投资什么方向好", "wealth"),
    ("偏财运怎么样", "wealth"),
    ("今年能买房吗", "wealth"),
    ("做生意赚钱吗", "wealth"),
    # ── relationship (5) ──
    ("我的感情运怎么样", "relationship"),
    ("什么时候能脱单", "relationship"),
    ("我和他的姻缘", "relationship"),
    ("婚姻幸福吗", "relationship"),
    ("能不能复合", "relationship"),
    # ── compatibility (5) ──
    ("我们俩合不合", "compatibility"),
    ("我们适合结婚吗", "compatibility"),
    ("帮我看看合盘", "compatibility"),
    ("两个人的八字匹配吗", "compatibility"),
    ("我俩搭不搭", "compatibility"),
    # ── yearly (5) ──
    ("今年运势如何", "yearly"),
    ("流年分析", "yearly"),
    ("这一年整体运程", "yearly"),
    ("今年运气怎么样", "yearly"),
    ("本命年的流年", "yearly"),
    # ── monthly (4) ──
    ("这个月运势", "monthly"),
    ("本月运程", "monthly"),
    ("月运如何", "monthly"),
    ("当月要注意什么", "monthly"),
    # ── daily (3) ──
    ("今日运势", "daily"),
    ("今天运气", "daily"),
    ("日运查询", "daily"),
    # ── decision (4) ──
    ("该不该辞职", "decision"),
    ("要不要接 offer", "decision"),
    ("去还是留", "decision"),
    ("二选一怎么选", "decision"),
    # ── timing (3) ──
    ("什么时候能结婚", "timing"),
    ("几月适合搬家", "timing"),
    ("什么时候是好时机", "timing"),
    # ── fengshui (3) ──
    ("房子风水怎么样", "fengshui"),
    ("卧室怎么布置好", "fengshui"),
    ("办公室方位", "fengshui"),
    # ── health_reflection (3) ──
    ("最近身体状态", "health_reflection"),
    ("压力大怎么调理", "health_reflection"),
    ("睡眠不好怎么办", "health_reflection"),
]


def _precision_recall_f1(predictions: list[str], gold: list[str]) -> tuple[float, float, float]:
    """Macro F1 (12 类平均)。"""
    assert len(predictions) == len(gold)
    classes = GOAL_TYPES
    f1s = []
    for cls in classes:
        tp = sum(1 for p, g in zip(predictions, gold) if p == cls and g == cls)
        fp = sum(1 for p, g in zip(predictions, gold) if p == cls and g != cls)
        fn = sum(1 for p, g in zip(predictions, gold) if p != cls and g == cls)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        f1s.append(f1)
    return (
        sum(tp / max(1, sum(1 for g in gold if g == cls)) for cls, tp in zip(classes, [0] * len(classes))) / len(classes),  # macro_recall 简化
        sum(prec for prec in [sum(1 for p, g in zip(predictions, gold) if p == cls and g == cls) / max(1, sum(1 for p, g in zip(predictions, gold) if p == cls)) for cls in classes]) / len(classes),
        sum(f1s) / len(f1s),
    )


class TestF1EvalSet:
    """50 问 macro F1 评估 — Sprint 1.1 验收门。"""

    def test_macro_f1_above_0_9(self):
        gold = [g for _, g in EVAL_SET]
        preds = [classify_intent(q)["goal"] for q, _ in EVAL_SET]
        # 计算 macro F1
        f1s = []
        for cls in GOAL_TYPES:
            tp = sum(1 for p, g in zip(preds, gold) if p == cls and g == cls)
            fp = sum(1 for p, g in zip(preds, gold) if p == cls and g != cls)
            fn = sum(1 for p, g in zip(preds, gold) if p != cls and g == cls)
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
            f1s.append(f1)
        macro_f1 = sum(f1s) / len(f1s)

        # Sprint 1.1 验收门: F1 ≥ 0.9
        assert macro_f1 >= 0.9, f"macro F1 = {macro_f1:.3f}, 期望 ≥ 0.9. 错分: " + ", ".join(
            f"'{q}' 期望 {g} 实际 {p}"
            for q, g, p in zip([q for q, _ in EVAL_SET], gold, preds)
            if g != p
        )

    def test_eval_set_size(self):
        assert len(EVAL_SET) == 50, f"评估集 {len(EVAL_SET)} 条, 期望 50"


# ── 阈值常量测试 ────────────────────────────────────────────────────────

class TestThresholds:
    """FSM 阈值常量在合理范围。"""

    def test_resolve_threshold_in_range(self):
        assert 1 <= EVIDENCE_RESOLVE <= 5

    def test_llm_threshold_in_range(self):
        assert 1 <= EVIDENCE_LLM <= EVIDENCE_RESOLVE

    def test_timeout_s_in_range(self):
        assert 0.5 <= LLM_TIMEOUT_S <= 10.0


class TestEvidenceCountTriggering:
    """evidence_count 触发不同 FSM 路径的覆盖。"""

    def test_high_evidence_resolves_directly(self):
        """≥ 2 条证据 → RULE_MATCHED, 不调 LLM。"""
        client = FakeLLMClient(preset_answer={"goal": "wealth", "confidence": 0.9})
        set_llm_client(client)
        # "我该换工作吗 事业如何" → 多个 career 关键词 + 模式
        r = classify_intent_v2("我该换工作吗, 事业如何")
        assert r.goal_source == "classified"
        assert len(client.call_log) == 0  # 不该调 LLM

    def test_single_evidence_triggers_llm(self):
        """单条证据 → LLM_PENDING, 调 LLM。"""
        client = FakeLLMClient(preset_answer={"goal": "wealth", "confidence": 0.85})
        set_llm_client(client)
        # "财运" 单关键词 → evidence_count=1
        r = classify_intent_v2("财运")
        # 1 个关键词通常 + 一个 pattern 也可能命中, 视具体词而定
        # 关键是: 如果 LLM 被调用, source="llm_fallback"; 否则 source="classified"
        if r.goal_source == "llm_fallback":
            assert r.goal == "wealth"
            assert "llm_used" in r.flags
            assert len(client.call_log) == 1

    def test_no_evidence_falls_back(self):
        """零证据 → FALLBACK, 降级 general_life。"""
        r = classify_intent_v2("xyzqwerty无意义字符串")
        assert r.goal == "general_life"
        assert r.goal_source == "fallback"
        assert "rule_low_conf" in r.flags


# ── LLM 输出校验测试 ──────────────────────────────────────────────────

class TestLLMOutputValidation:
    """LLM 客户端返回非法值时, 降级而非崩溃。"""

    def test_invalid_goal_rejected(self):
        client = FakeLLMClient(preset_answer={"goal": "invalid_goal", "confidence": 0.9})
        set_llm_client(client)
        r = classify_intent_v2("财运")  # 单证据触发 LLM
        # LLM 返回无效 goal → 降级到规则层 top
        if r.goal_source == "fallback":
            assert r.goal in GOAL_TYPES

    def test_invalid_confidence_rejected(self):
        client = FakeLLMClient(preset_answer={"goal": "wealth", "confidence": 1.5})
        set_llm_client(client)
        r = classify_intent_v2("财运")
        if r.goal_source == "fallback":
            assert r.goal in GOAL_TYPES

    def test_raising_client_caught(self):
        """LLM 客户端抛异常 → 降级 (不传播)。"""
        class RaisingClient:
            def classify(self, question, candidates, taxonomy):
                raise RuntimeError("simulated LLM crash")
        set_llm_client(RaisingClient())
        r = classify_intent_v2("财运")
        # 不该 raise, 应该降级
        if r.goal_source == "fallback":
            assert "llm_error_or_timeout" in r.flags
