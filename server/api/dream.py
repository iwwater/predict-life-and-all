"""POST /api/knowledge/dream — 周公解梦端点.

端点:
    POST /api/knowledge/dream  {dream_text, top_n}  - 单次梦境解读
    GET  /api/knowledge/dream/stats                  - 语料统计

设计:
    - 复用 divination.engines.dream 引擎
    - 输入: 梦境描述 (中文自由文本)
    - 输出: Top N 匹配 + 解读 + 出处 + 情境
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from divination.engines.dream import get_corpus_stats, interpret_dream

router = APIRouter(prefix="/api/knowledge/dream", tags=["dream"])


class DreamInterpretRequest(BaseModel):
    dream_text: str = Field(..., min_length=4, max_length=500, description="梦境描述")
    top_n: int = Field(default=5, ge=1, le=10, description="返回 Top N 匹配")


class DreamMatchResponse(BaseModel):
    symbol: str
    category: str
    score: float
    interpretation: str
    classic_text: str
    matched_contexts: list[str] = []
    context_meanings: list[str] = []


class DreamInterpretResponse(BaseModel):
    dream_text: str
    keywords: list[str]
    matches: list[DreamMatchResponse]
    summary: str
    overall_luck: str


class DreamStatsResponse(BaseModel):
    total_entries: int
    categories: dict[str, int]
    classic_sources: list[str]


@router.post("", response_model=DreamInterpretResponse)
def interpret(dream_req: DreamInterpretRequest):
    """梦境解读主端点。

    输入: 梦境描述 + top_n
    输出: 匹配条目 + 摘要 + 综合判断
    """
    result = interpret_dream(dream_req.dream_text, top_n=dream_req.top_n)
    return DreamInterpretResponse(
        dream_text=result["dream_text"],
        keywords=result["keywords"],
        matches=[
            DreamMatchResponse(
                symbol=m["symbol"],
                category=m["category"],
                score=m["score"],
                interpretation=m["interpretation"],
                classic_text=m["classic_text"],
                matched_contexts=m["matched_contexts"],
                context_meanings=m["context_meanings"],
            )
            for m in result["matches"]
        ],
        summary=result["summary"],
        overall_luck=result["overall_luck"],
    )


@router.get("/stats", response_model=DreamStatsResponse)
def stats():
    """返回语料库统计。"""
    s = get_corpus_stats()
    return DreamStatsResponse(
        total_entries=s["total_entries"],
        categories=s["categories"],
        classic_sources=s["classic_sources"],
    )
