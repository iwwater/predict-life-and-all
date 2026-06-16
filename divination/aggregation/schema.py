"""聚合模块数据模型 — 统一 12 术法输入输出契约。

BE-002: schema 文件
BE-011: ReadingRequest
BE-012: DivinationSignal
BE-013: ConsensusItem
BE-014: ConflictItem
BE-015: ReadingReport
BE-016: ReadingResult
BE-017: ValidationResult
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ── 输入模型 ─────────────────────────────────────────────────────────────────

class BirthModel(BaseModel):
    """出生信息（与 server/api/chart.py 的 BirthModel 对齐）。"""
    year: int = Field(..., ge=1500, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(12, ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    gender: Literal["male", "female", "unspecified"] = "unspecified"
    calendar: Literal["gregorian", "lunar"] = "gregorian"
    lat: Optional[float] = None
    lng: Optional[float] = None
    tz: str = "Asia/Shanghai"
    is_leap_month: bool = False


class SpaceModel(BaseModel):
    """空间信息（风水用）。"""
    sitting: Optional[str] = None       # 坐向, e.g. "坐北朝南"
    period: Optional[int] = None        # 元运, e.g. 8
    construction_year: Optional[int] = None
    address: Optional[str] = None


class RealityConstraints(BaseModel):
    """现实条件约束 — 方案 §十四：防止命理结果脱离现实。

    各字段均为 Optional，不提供则该项不参与判断。
    """
    # 财务
    cash_reserve_months: Optional[int] = Field(
        None, ge=0, le=60,
        description="现金储备月数，e.g. 2 表示仅有 2 个月生活费"
    )
    has_formal_contract: Optional[bool] = Field(
        None,
        description="是否已有正式书面合同（非口头 offer）"
    )
    # 地点
    current_city: Optional[str] = Field(None, description="当前所在城市")
    target_city: Optional[str] = Field(None, description="目标城市/是否需要搬迁")
    commute_tolerance: Optional[Literal["accept", "negotiable", "reject"]] = Field(
        None, description="对长途通勤的接受度"
    )
    # 健康
    health_status: Optional[Literal["good", "fair", "poor"]] = Field(
        None, description="当前健康状况"
    )
    # 资质
    has_qualification: Optional[bool] = Field(
        None, description="是否具备目标方向的资质/证书/许可"
    )
    # 家庭
    has_dependents: Optional[bool] = Field(
        None, description="是否有需抚养家庭成员"
    )
    # 备选
    has_backup_plan: Optional[bool] = Field(
        None, description="是否有备选方案（退路）"
    )


class ReadingRequest(BaseModel):
    """主入口请求 — 用户只需输入问题，系统自动调用 12 法。

    BE-011: 支持 goal/question/birth/target_birth/space/methods/depth/language
    """
    goal: Optional[str] = Field(
        None,
        description="目标/意图 — 可留空，由系统从 question 自动推断",
    )
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="用户问题（必填），e.g. '我该换工作吗？'",
    )
    birth: Optional[BirthModel] = Field(
        None,
        description="求测者出生信息（部分术法如六爻/塔罗可不提供）",
    )
    target_birth: Optional[BirthModel] = Field(
        None,
        description="关系对象出生信息（合盘/关系场景）",
    )
    space: Optional[SpaceModel] = Field(
        None,
        description="空间信息（风水相关术法使用）",
    )
    constraints: Optional[RealityConstraints] = Field(
        None,
        description="现实条件约束（方案 §十四）",
    )
    method_options: Optional[dict[str, Any]] = Field(
        None,
        description="术法专属选项: liuyao_mode, meihua_mode, tarot_spread, tarot_mode 等",
    )
    methods: Optional[list[str]] = Field(
        None,
        description="可指定术法子集；不传则默认使用全部 12 法 (M0-05)",
    )
    depth: Literal["free", "standard", "premium"] = Field(
        "standard",
        description="报告深度 — free: 简短摘要, standard: 结构化报告, premium: 深度分析",
    )
    language: Literal["zh", "en"] = Field("zh", description="报告语言")


# ── 统一信号模型 ─────────────────────────────────────────────────────────────

class DivinationSignal(BaseModel):
    """统一信号格式 — 将不同术法的输出标准化为此格式。

    BE-012: method/goal/domain/signal_key/polarity/strength/evidence/confidence
    """
    method: str = Field(..., description="术法标识, e.g. 'bazi_v2', 'ziwei'")
    domain: str = Field(
        ...,
        description="领域: self_life/career/wealth/relationship/health/timing/decision",
    )
    signal_key: str = Field(
        ...,
        description="信号键, e.g. 'day_master_strong', 'career_favorable'",
    )
    polarity: Literal["positive", "negative", "neutral", "mixed"] = Field(
        ...,
        description="极性 — positive: 正向, negative: 负向, neutral: 中性, mixed: 混合",
    )
    strength: float = Field(
        ...,
        ge=0,
        le=1,
        description="信号强度 0-1 (NOR-018)",
    )
    evidence: str = Field(
        "",
        description="盘面依据 — 来自原始排盘的具体证据",
    )
    confidence: float = Field(
        0.5,
        ge=0,
        le=1,
        description="该信号在本术法内的置信度 0-1",
    )
    dimension: Optional[Literal[
        "long_term", "current_cycle", "relationship", "one_question", "space"
    ]] = Field(
        None,
        description="5 维职责分派: long_term/current_cycle/relationship/one_question/space",
    )
    time_scope: Optional[Literal[
        "short_term", "medium_term", "long_term",
        "current_cycle", "one_question", "space",
    ]] = Field(
        None,
        description="时间范围: short_term/medium_term/long_term/current_cycle/one_question/space",
    )
    advice: Optional[str] = Field(
        None,
        description="该信号衍生的行动建议",
    )


# ── 共识/冲突模型 ────────────────────────────────────────────────────────────

class ConsensusItem(BaseModel):
    """多术法共识主题。

    BE-013: 共识主题/支持术法/权重强度/解释
    """
    domain: str
    theme: str = Field(..., description="共识主题, e.g. '事业上升期'")
    supporting_methods: list[str] = Field(
        ...,
        description="支持该结论的术法列表",
    )
    weight_strength: float = Field(
        ...,
        ge=0,
        le=100,
        description="加权共识强度",
    )
    explanation: str = Field(..., description="共识解释")


class ConflictItem(BaseModel):
    """多术法冲突主题。

    BE-014: 正向术法/负向术法/中性术法/冲突解释
    VAL-008: severity — low/medium/high
    VAL-009: resolution — 冲突调和文本
    """
    domain: str
    severity: Literal["low", "medium", "high"] = Field(
        "medium",
        description="冲突严重程度",
    )
    positive_methods: list[str] = Field(
        default_factory=list,
        description="给出正向信号的术法",
    )
    negative_methods: list[str] = Field(
        default_factory=list,
        description="给出负向信号的术法",
    )
    neutral_methods: list[str] = Field(
        default_factory=list,
        description="给出中性信号的术法",
    )
    conflict_explanation: str = Field(
        ...,
        description="冲突解释 — 说明分歧可能的原因",
    )
    resolution: str = Field(
        "",
        description="调和建议 — e.g. '长期可行，但短期不宜急进'",
    )


# ── 验证结果模型 ─────────────────────────────────────────────────────────────

class ValidationResult(BaseModel):
    """交叉验证汇总结果。

    BE-017: consensus/conflicts/overall_score/confidence/risks/timing/action_advice
    """
    consensus: list[ConsensusItem] = Field(default_factory=list)
    conflicts: list[ConflictItem] = Field(default_factory=list)
    overall_score: float = Field(
        50.0,
        ge=0,
        le=100,
        description="综合评分",
    )
    confidence: float = Field(
        50.0,
        ge=0,
        le=100,
        description="整体置信度数值",
    )
    confidence_level: Literal["low", "medium", "medium_high", "high"] = Field(
        "medium",
        description="整体置信等级 (VAL-011)",
    )
    risks: list[str] = Field(
        default_factory=list,
        description="风险提示",
    )
    timing: Optional[dict[str, Any]] = Field(
        None,
        description="时机分析",
    )
    action_advice: list[str] = Field(
        default_factory=list,
        description="行动建议",
    )
    dim_scores: dict[str, float] = Field(
        default_factory=dict,
        description="5 维 0-100 分数 (long_term/current_cycle/relationship/one_question/space)",
    )
    dim_signals_count: dict[str, int] = Field(
        default_factory=dict,
        description="每维有效信号数",
    )
    per_dim_consensus: dict[str, list[ConsensusItem]] = Field(
        default_factory=dict,
        description="按维度分组的共识",
    )
    dim_breakdown: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="每维子结构 {score, signals_count, top_signal, summary}",
    )


# ── 报告模型 ─────────────────────────────────────────────────────────────────

class ReadingReport(BaseModel):
    """三档报告。

    BE-015: free/standard/premium 三档
    """
    free: str = Field(
        "",
        description="简短摘要 ≤500 字，面向快速浏览",
    )
    standard: str = Field(
        "",
        description="标准结构化报告，包含各领域分析",
    )
    premium: str = Field(
        "",
        description="深度报告，含详细分析、LLM 增强解读",
    )


# ── 顶层结果模型 ─────────────────────────────────────────────────────────────

class ReadingResult(BaseModel):
    """API 返回的顶层结果。

    BE-016: 结果总结构，字段稳定返回
    """
    session_id: str = Field(..., description="本次会话 ID")
    intent: dict[str, Any] = Field(
        default_factory=dict,
        description="意图分类结果: {domain, sub_domains, confidence}",
    )
    methods_used: list[str] = Field(
        ...,
        description="实际使用的术法列表 — 必须包含 18 法 (Phase 0 全量)",
    )
    signals: list[DivinationSignal] = Field(
        default_factory=list,
        description="所有术法的统一信号",
    )
    consensus: list[ConsensusItem] = Field(
        default_factory=list,
        description="多术法共识",
    )
    conflicts: list[ConflictItem] = Field(
        default_factory=list,
        description="多术法分歧",
    )
    validation: ValidationResult = Field(
        default_factory=ValidationResult,
        description="交叉验证汇总",
    )
    dim_breakdown: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="每维子结构 {score, signals_count, top_signal, summary}",
    )
    report: ReadingReport = Field(
        default_factory=ReadingReport,
        description="三档报告",
    )
    disclaimer: str = Field(
        ...,
        description="免责声明 (M0-04)",
    )
    elapsed_ms: int = Field(0, description="总耗时（毫秒）")
    errors: list[dict[str, Any]] = Field(
        default_factory=list,
        description="各术法计算错误（如有），不影响整体流程",
    )
    # ── PAY-005: 付费状态字段 ──
    is_unlocked_standard: bool = Field(
        False,
        description="标准版是否已解锁",
    )
    is_unlocked_premium: bool = Field(
        False,
        description="高级版是否已解锁",
    )
    # ── SAFE-002~004: 安全降级标记 ──
    safety_flags: list[str] = Field(
        default_factory=list,
        description="安全标记: medical_downgrade, investment_downgrade, legal_downgrade",
    )
    safety_downgrades: list[str] = Field(
        default_factory=list,
        description="降级提示消息列表",
    )
    # Phase B: §十四 现实条件校正
    reality_adjusted: dict[str, Any] = Field(
        default_factory=dict,
        description="现实条件校正结果: {has_warnings, core_conclusion, dimension_judgments, adjusted_advice}",
    )
    # W10: 合盘缺 partner 标记
    hepan_no_partner: bool = Field(
        False,
        description="hepan 术法因缺少目标对象 birth而降级为一般参考，不计入术法数量",
    )
