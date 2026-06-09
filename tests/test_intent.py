"""INT-015: classify_intent 单元测试 — 每个 goal 至少 3 条测试用例。"""
import pytest
from divination.aggregation.intent import classify_intent, GOAL_TYPES


class TestGeneralLife:
    """INT-002: general_life 命盘、人生、整体、综合"""
    cases = [
        "帮我看看命盘",
        "我的人生运势怎么样",
        "综合分析一下我的命运",
        "帮我排个盘看看",
        "我想了解自己的命运走势",
    ]

    @pytest.mark.parametrize("question", cases)
    def test_classify(self, question):
        r = classify_intent(question)
        assert r["goal"] == "general_life", f"Expected general_life, got {r['goal']} for: {question}"


class TestCareer:
    """INT-003: career 事业、工作、创业、跳槽、升职"""
    cases = [
        "我该换工作吗",
        "我适合创业吗",
        "事业发展前景怎么样",
        "职场人际关系如何",
        "转行做什么方向好",
    ]

    @pytest.mark.parametrize("question", cases)
    def test_classify(self, question):
        r = classify_intent(question)
        assert r["goal"] == "career", f"Expected career, got {r['goal']} for: {question}"


class TestWealth:
    """INT-004: wealth 财运、赚钱、收入、投资、财富"""
    cases = [
        "我的财运怎么样",
        "投资什么方向好",
        "偏财运如何",
        "求财方向在哪里",
        "做生意财运好吗",
    ]

    @pytest.mark.parametrize("question", cases)
    def test_classify(self, question):
        r = classify_intent(question)
        assert r["goal"] == "wealth", f"Expected wealth, got {r['goal']} for: {question}"


class TestRelationship:
    """INT-005: relationship 感情、恋爱、婚姻、桃花、复合"""
    cases = [
        "我的感情运怎么样",
        "能不能脱单",
        "感情方面有什么需要注意",
        "姻缘运势如何",
        "我的婚姻会幸福吗",
    ]

    @pytest.mark.parametrize("question", cases)
    def test_classify(self, question):
        r = classify_intent(question)
        assert r["goal"] == "relationship", f"Expected relationship, got {r['goal']} for: {question}"


class TestCompatibility:
    """INT-006: compatibility 合盘、合不合、适合结婚、匹配"""
    cases = [
        "我们俩合不合",
        "我和她八字合不合",
        "我们适合结婚吗",
        "帮我看看合盘",
        "两个人的八字匹配吗",
    ]

    @pytest.mark.parametrize("question", cases)
    def test_classify(self, question):
        r = classify_intent(question)
        assert r["goal"] == "compatibility", f"Expected compatibility, got {r['goal']} for: {question}"


class TestYearly:
    """INT-007: yearly 今年、年度、流年、年运"""
    cases = [
        "今年运势怎么样",
        "看看流年运势",
        "这一年的运气如何",
        "今年整体运程",
        "流年分析",
    ]

    @pytest.mark.parametrize("question", cases)
    def test_classify(self, question):
        r = classify_intent(question)
        assert r["goal"] == "yearly", f"Expected yearly, got {r['goal']} for: {question}"


class TestMonthly:
    """INT-008: monthly 本月、月运、这个月"""
    cases = [
        "这个月运势怎么样",
        "月运如何",
        "当月运势分析",
        "这月整体运程",
        "本月有什么要注意的",
    ]

    @pytest.mark.parametrize("question", cases)
    def test_classify(self, question):
        r = classify_intent(question)
        assert r["goal"] == "monthly", f"Expected monthly, got {r['goal']} for: {question}"


class TestDaily:
    """INT-009: daily 今日、今天、每日、日运"""
    cases = [
        "今日运势",
        "今天的运气怎么样",
        "每日运势如何",
        "今天适合做什么",
        "日运查询",
    ]

    @pytest.mark.parametrize("question", cases)
    def test_classify(self, question):
        r = classify_intent(question)
        assert r["goal"] == "daily", f"Expected daily, got {r['goal']} for: {question}"


class TestDecision:
    """INT-010: decision 该不该、要不要、是否、选择"""
    cases = [
        "我该不该辞职",
        "要不要接受这个offer",
        "如何选择这两个机会",
        "该不该分手",
        "我该去还是留",
    ]

    @pytest.mark.parametrize("question", cases)
    def test_classify(self, question):
        r = classify_intent(question)
        assert r["goal"] == "decision", f"Expected decision, got {r['goal']} for: {question}"


class TestTiming:
    """INT-011: timing 什么时候、时机、几月、哪天"""
    cases = [
        "什么时候能结婚",
        "最佳时机是什么时候",
        "几月份适合搬家",
        "哪天开业比较好",
        "还要等多久才能有结果",
    ]

    @pytest.mark.parametrize("question", cases)
    def test_classify(self, question):
        r = classify_intent(question)
        assert r["goal"] == "timing", f"Expected timing, got {r['goal']} for: {question}"


class TestFengshui:
    """INT-012: fengshui 风水、房子、搬家、卧室、办公室、方位"""
    cases = [
        "房子风水怎么样",
        "卧室应该怎么布置",
        "办公室方位好不好",
        "搬家需要注意什么风水",
        "这个户型风水好吗",
    ]

    @pytest.mark.parametrize("question", cases)
    def test_classify(self, question):
        r = classify_intent(question)
        assert r["goal"] == "fengshui", f"Expected fengshui, got {r['goal']} for: {question}"


class TestHealthReflection:
    """INT-013: health_reflection 健康、压力、睡眠、身体状态 — 非医疗化"""
    cases = [
        "最近身体状态怎么样",
        "我最近压力大，怎么调理",
        "睡眠不好怎么改善",
        "身体调理有什么建议",
        "最近精力不足怎么办",
    ]

    @pytest.mark.parametrize("question", cases)
    def test_classify(self, question):
        r = classify_intent(question)
        assert r["goal"] == "health_reflection", f"Expected health_reflection, got {r['goal']} for: {question}"


class TestExplicitGoal:
    """INT-014: 显式 goal 覆盖"""

    def test_explicit_goal_overrides_classification(self):
        """用户传了 goal 时优先使用用户 goal。"""
        r = classify_intent("我该换工作吗", goal="career")
        assert r["goal"] == "career"
        assert r["goal_source"] == "explicit"
        assert r["goal_confidence"] == 1.0

    def test_explicit_goal_different_from_question(self):
        """即使用户问题暗示不同领域，也以显式 goal 为准。"""
        r = classify_intent("我的财运如何", goal="relationship")
        assert r["goal"] == "relationship"
        assert r["goal_source"] == "explicit"

    def test_unknown_goal_falls_back_to_classify(self):
        """用户传了不在标准列表的 goal → 自动分类 + note。"""
        r = classify_intent("我该换工作吗", goal="unknown_goal")
        assert "note" in r
        assert r["goal_source"] == "classified"


class TestAllGoalsCovered:
    """验证 12 个 goal 类型都有覆盖。"""

    def test_all_goals_in_goal_types(self):
        assert len(GOAL_TYPES) == 12
        expected = {
            "general_life", "career", "wealth", "relationship",
            "compatibility", "yearly", "monthly", "daily",
            "decision", "timing", "fengshui", "health_reflection",
        }
        assert set(GOAL_TYPES) == expected

    def test_classify_returns_valid_structure(self):
        r = classify_intent("测试问题")
        required = {"goal", "goal_label", "goal_confidence", "goal_source", "sub_goals", "domain_scores"}
        assert required.issubset(set(r.keys()))
        assert r["goal"] in GOAL_TYPES
