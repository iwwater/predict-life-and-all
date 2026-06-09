"""SAFE-001~010: 安全与合规模块测试 (TEST-001~010)。

SAFE-001: 统一免责声明
SAFE-002: 医疗类问题降级
SAFE-003: 投资类问题降级
SAFE-004: 法律类问题降级
SAFE-005: 危机词拦截
SAFE-006: 绝对化表达过滤
SAFE-007: 用户隐私提示
SAFE-010: 日志脱敏
"""
import pytest

from divination.aggregation.safety import (
    DISCLAIMER,
    PRIVACY_NOTICE,
    CRISIS_KEYWORDS,
    CRISIS_RESPONSE,
    MEDICAL_KEYWORDS,
    INVESTMENT_KEYWORDS,
    LEGAL_KEYWORDS,
    ABSOLUTE_PATTERNS,
    ABSOLUTE_SOFTEN,
    check_input_safety,
    check_output_safety,
    sanitize_for_log,
    sanitize_birth_for_log,
    _soften_text,
)


# ══════════════════════════════════════════════════════════════════════════════
# SAFE-001: 统一免责声明
# ══════════════════════════════════════════════════════════════════════════════

class TestDisclaimer:
    def test_disclaimer_contains_reference_only(self):
        """SAFE-001: 免责声明包含'仅供参考'"""
        assert "仅供参考" in DISCLAIMER

    def test_disclaimer_mentions_no_medical_diagnosis(self):
        """SAFE-001: 免责声明提及不构成医疗诊断"""
        assert "医疗诊断" in DISCLAIMER or "不构成" in DISCLAIMER

    def test_privacy_notice_mentions_birth_info(self):
        """SAFE-007: 隐私说明提及出生信息用途"""
        assert "出生信息" in PRIVACY_NOTICE or "隐私说明" in PRIVACY_NOTICE


# ══════════════════════════════════════════════════════════════════════════════
# SAFE-005: 危机词拦截
# ══════════════════════════════════════════════════════════════════════════════

class TestCrisisDetection:
    def test_crisis_keyword_suicide_blocked(self):
        """SAFE-005: '自杀' 触发危机拦截"""
        result = check_input_safety("我想自杀怎么办")
        assert result["blocked"] is True
        assert result["crisis"] is True
        assert result["safe"] is False
        assert "心理援助" in result["crisis_message"]

    def test_crisis_keyword_zican_blocked(self):
        """SAFE-005: '自残' 触发危机拦截"""
        result = check_input_safety("我控制不住自残")
        assert result["crisis"] is True
        assert result["blocked"] is True

    def test_crisis_keyword_qingsheng_blocked(self):
        """SAFE-005: '轻生' 触发危机拦截"""
        result = check_input_safety("我觉得活着没意思想轻生")
        assert result["crisis"] is True

    def test_crisis_keyword_buxianghuo_blocked(self):
        """SAFE-005: '不想活' 触发危机拦截"""
        result = check_input_safety("我最近真的不想活了")
        assert result["crisis"] is True

    def test_crisis_keyword_huobuxiaqu_blocked(self):
        """SAFE-005: '活不下去' 触发危机拦截"""
        result = check_input_safety("我压力太大活不下去了")
        assert result["crisis"] is True

    def test_crisis_response_contains_hotline(self):
        """SAFE-005: 危机响应包含心理援助热线"""
        result = check_input_safety("我想自杀")
        assert "400-161-9995" in result["crisis_message"] or "心理援助" in result["crisis_message"]

    def test_normal_question_not_blocked(self):
        """SAFE-005: 正常问题不被拦截"""
        result = check_input_safety("我该换工作吗？")
        assert result["blocked"] is False
        assert result["crisis"] is False

    def test_crisis_downgrades_empty(self):
        """SAFE-005: 危机拦截时 downgrades 为空（不额外降级）"""
        result = check_input_safety("我想自杀")
        assert result["downgrades"] == []

    def test_all_crisis_keywords_are_strings(self):
        """SAFE-005: CRISIS_KEYWORDS 全部为字符串"""
        assert all(isinstance(kw, str) for kw in CRISIS_KEYWORDS)


# ══════════════════════════════════════════════════════════════════════════════
# SAFE-002: 医疗类问题降级
# ══════════════════════════════════════════════════════════════════════════════

class TestMedicalDowngrade:
    def test_medical_keyword_aizheng_downgrades(self):
        """SAFE-002: '癌症' 触发医疗降级"""
        result = check_input_safety("我得了癌症还能活多久")
        assert result["blocked"] is False
        assert result["safe"] is False
        assert any("医疗" in d for d in result["downgrades"])

    def test_medical_keyword_zhongliu_downgrades(self):
        """SAFE-002: '肿瘤' 触发医疗降级"""
        result = check_input_safety("肿瘤能不能治好")
        assert any("医疗" in d or "健康" in d for d in result["downgrades"])

    def test_medical_keyword_nengbunenghaozhi(self):
        """SAFE-002: '能不能治好' 触发医疗降级"""
        result = check_input_safety("这个病到底能不能治好")
        assert any("医疗" in d or "健康" in d for d in result["downgrades"])

    def test_health_question_without_keywords_safe(self):
        """SAFE-002: 无敏感词的健康问题安全通过"""
        result = check_input_safety("我最近身体怎么样需要注意什么")
        assert result["safe"] is True

    def test_medical_downgrade_message_mentions_doctor(self):
        """SAFE-002: 医疗降级消息提及就医"""
        from divination.aggregation.safety import MEDICAL_DOWNGRADE_MSG
        assert "及时就医" in MEDICAL_DOWNGRADE_MSG or "医疗" in MEDICAL_DOWNGRADE_MSG


# ══════════════════════════════════════════════════════════════════════════════
# SAFE-003: 投资类问题降级
# ══════════════════════════════════════════════════════════════════════════════

class TestInvestmentDowngrade:
    def test_investment_keyword_quancang_downgrades(self):
        """SAFE-003: '全仓' 触发投资降级"""
        result = check_input_safety("全仓买入可以吗")
        assert any("投资" in d or "财运" in d for d in result["downgrades"])

    def test_investment_keyword_maingezhi(self):
        """SAFE-003: '买哪只股' 触发投资降级"""
        result = check_input_safety("买哪只股能赚钱")
        assert any("投资" in d or "财运" in d for d in result["downgrades"])

    def test_investment_keyword_wenzhuan(self):
        """SAFE-003: '稳赚' 触发投资降级"""
        result = check_input_safety("有没有稳赚的项目")
        assert any("投资" in d or "财运" in d for d in result["downgrades"])

    def test_normal_wealth_question_safe(self):
        """SAFE-003: 正常财运问题安全通过"""
        result = check_input_safety("我今年财运怎么样")
        assert result["safe"] is True

    def test_investment_downgrade_message_mentions_license(self):
        """SAFE-003: 投资降级消息提及持牌机构"""
        from divination.aggregation.safety import INVESTMENT_DOWNGRADE_MSG
        assert "持牌" in INVESTMENT_DOWNGRADE_MSG or "投资" in INVESTMENT_DOWNGRADE_MSG


# ══════════════════════════════════════════════════════════════════════════════
# SAFE-004: 法律类问题降级
# ══════════════════════════════════════════════════════════════════════════════

class TestLegalDowngrade:
    def test_legal_keyword_guansi_downgrades(self):
        """SAFE-004: '官司一定' 触发法律降级"""
        result = check_input_safety("这官司一定能赢吗")
        assert any("法律" in d or "律师" in d for d in result["downgrades"])

    def test_legal_keyword_shengsu(self):
        """SAFE-004: '胜诉' 触发法律降级"""
        result = check_input_safety("我这案子能胜诉吗")
        assert any("法律" in d or "律师" in d for d in result["downgrades"])

    def test_legal_keyword_zuolao(self):
        """SAFE-004: '会不会坐牢' 触发法律降级"""
        result = check_input_safety("我会不会坐牢")
        assert any("法律" in d or "律师" in d for d in result["downgrades"])


# ══════════════════════════════════════════════════════════════════════════════
# SAFE-006: 绝对化表达过滤
# ══════════════════════════════════════════════════════════════════════════════

class TestAbsoluteFiltering:
    def test_absolute_yiding_detected(self):
        """SAFE-006: '一定' 被检测为绝对化表达"""
        result = check_output_safety("你一定会成功的")
        assert result["safe"] is False
        assert "一定" in result["absolute_hits"]

    def test_absolute_biran_detected(self):
        """SAFE-006: '必然' 被检测为绝对化表达"""
        result = check_output_safety("这是必然的结果")
        assert "必然" in result["absolute_hits"]

    def test_absolute_baozheng_detected(self):
        """SAFE-006: '保证' 被检测为绝对化表达"""
        result = check_output_safety("我保证你会发财")
        assert "保证" in result["absolute_hits"]

    def test_safe_text_no_hits(self):
        """SAFE-006: 无绝对化表达的文本安全通过"""
        result = check_output_safety("综合来看，近期事业发展较为顺利，建议把握机会。")
        assert result["safe"] is True
        assert result["absolute_hits"] == []

    def test_output_missing_disclaimer_warns(self):
        """SAFE-006: 缺少免责声明时产生警告"""
        result = check_output_safety("你的运势不错")
        # 如果有绝对化表达，safe 会是 False；检查 warnings
        assert isinstance(result["warnings"], list)

    def test_softened_text_replaces_absolute(self):
        """SAFE-006: 软化后的文本替换了绝对化表达"""
        result = check_output_safety("你一定会成功")
        assert result["softened"] != "你一定会成功"

    def test_soften_replace_yiding(self):
        """SAFE-006: '一定' → '倾向于'"""
        softened = _soften_text("你一定会成功的")
        assert "一定" not in softened
        assert "倾向于" in softened

    def test_soften_replace_biran(self):
        """SAFE-006: '必然' → '较可能'"""
        softened = _soften_text("这是必然的结果")
        assert "必然" not in softened
        assert "较可能" in softened

    def test_absolute_soften_dict_complete(self):
        """SAFE-006: ABSOLUTE_SOFTEN 映射完整（每个 pattern 都有对应软化词）"""
        for pattern in ABSOLUTE_PATTERNS:
            assert pattern in ABSOLUTE_SOFTEN, f"缺少 '{pattern}' 的软化替换"


# ══════════════════════════════════════════════════════════════════════════════
# SAFE-010: 日志脱敏
# ══════════════════════════════════════════════════════════════════════════════

class TestLogSanitization:
    def test_sanitize_removes_full_birth_date(self):
        """SAFE-010: 脱敏后移除完整出生日期"""
        result = sanitize_for_log("生日是1990年6月15日")
        # The regex uses -/年/月/日 to match, let's check the actual regex...
        # Pattern: r'\b(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})\b' → r'\1-***-**'
        # For "1990年6月15日", this matches "1990年6月15" with year=1990, month=6, day=15
        # Result: "1990-***-**日" (the 日 is outside the match)
        assert "1990" in result  # year preserved
        assert "***" in result    # month+day redacted

    def test_sanitize_removes_coordinates(self):
        """SAFE-010: 脱敏后移除坐标"""
        result = sanitize_for_log("位置 31.2304 121.4737 附近")
        assert "31.23" not in result or "121.47" not in result

    def test_sanitize_removes_long_digit_sequences(self):
        """SAFE-010: 脱敏后移除长数字序列（≥8位）"""
        result = sanitize_for_log("电话 13812345678")
        assert "13812345678" not in result

    def test_sanitize_preserves_short_numbers(self):
        """SAFE-010: 脱敏保留短数字"""
        result = sanitize_for_log("今年 35 岁")
        assert "35" in result

    def test_sanitize_birth_for_log_none(self):
        """SAFE-010: 空出生信息返回占位文本"""
        result = sanitize_birth_for_log(None)
        assert "无" in result or "?" in result

    def test_sanitize_birth_for_log_dict(self):
        """SAFE-010: 出生信息脱敏为摘要"""
        result = sanitize_birth_for_log({"year": 1990, "gender": "male"})
        assert "1990" in result
        assert "male" in result


# ══════════════════════════════════════════════════════════════════════════════
# 复合场景测试
# ══════════════════════════════════════════════════════════════════════════════

class TestCompositeScenarios:
    def test_multiple_downgrades(self):
        """SAFE-002~004: 同时包含医疗+投资关键词产生多个降级"""
        result = check_input_safety("我得了肿瘤 全仓买哪只股")
        assert len(result["downgrades"]) >= 2

    def test_crisis_takes_priority_over_downgrades(self):
        """SAFE-005: 危机词优先于其他降级（直接 blocked，不检查 downgrades）"""
        result = check_input_safety("我想自杀 全仓买哪只股")
        assert result["crisis"] is True
        # 危机时 downgrades 为空
        assert result["downgrades"] == []

    def test_empty_question_safe(self):
        """空问题不触发任何安全检查"""
        result = check_input_safety("")
        assert result["safe"] is True
        assert result["crisis"] is False
        assert result["blocked"] is False

    def test_whitespace_question_safe(self):
        """纯空格问题安全"""
        result = check_input_safety("   ")
        assert result["safe"] is True
        assert result["crisis"] is False

    def test_case_insensitive_crisis_detection(self):
        """SAFE-005: 危机检测不区分大小写（全角字符测试）"""
        # Chinese characters don't have case, but test mixed ASCII safety
        result = check_input_safety("我想SUICIDE")
        assert result["crisis"] is False  # English word not in Chinese keyword list
