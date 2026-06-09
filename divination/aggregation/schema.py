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
    """
    domain: str
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
        description="整体置信度",
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
        description="实际使用的术法列表 — 必须包含 12 法 (M0-05)",
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
