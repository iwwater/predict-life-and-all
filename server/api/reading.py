"""POST /api/reading — 12 术法聚合解读主入口。

BE-010: API 文件
M0-03: 用户可以只输入问题，系统自动调用 12 法
"""
from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from divination.aggregation import (
    DISCLAIMER,
    ReadingRequest,
    ReadingResult,
    run_reading,
)
from divination.aggregation.schema import BirthModel, SpaceModel

router = APIRouter()
log = logging.getLogger("mystic-hub.reading-api")


# ── API 请求模型 (与 aggregation schema 对齐但有额外验证) ───────────────────

class ReadingAPIRequest(BaseModel):
    """POST /api/reading 请求体。

    用户只需输入 question，其他字段可选。
    """
    goal: str | None = Field(
        None,
        description="目标/意图 — 可留空",
        max_length=200,
    )
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="用户问题（必填）",
    )
    birth: BirthModel | None = Field(
        None,
        description="求测者出生信息",
    )
    target_birth: BirthModel | None = Field(
        None,
        description="关系对象出生信息",
    )
    space: SpaceModel | None = Field(
        None,
        description="空间信息（风水用）",
    )
    method_options: dict[str, Any] | None = Field(
        None,
        description="术法专属选项: liuyao_mode, meihua_mode, tarot_spread 等",
    )
    methods: list[str] | None = Field(
        None,
        min_length=1,
        max_length=12,
        description="指定术法子集；不传则默认全部 12 法",
    )
    depth: str = Field(
        "standard",
        pattern="^(free|standard|premium)$",
        description="报告深度",
    )
    language: str = Field(
        "zh",
        pattern="^(zh|en)$",
        description="报告语言",
    )


# ── 端点 ─────────────────────────────────────────────────────────────────────

@router.post("/reading", response_model=ReadingResult)
async def reading_endpoint(body: ReadingAPIRequest):
    """12 术法聚合解读主入口。

    用户只需输入问题，系统自动：
    1. 识别意图领域
    2. 选择全部 12 术法进行排盘
    3. 标准化为统一信号
    4. 交叉验证，检测共识与分歧
    5. 生成三档报告（free/standard/premium）

    返回 ReadingResult，其中 methods_used 保证包含全部 12 种术法。
    """
    t0 = time.perf_counter()
    log.info("Reading request: %s methods=%s", body.question[:80], body.methods)

    # 转换为内部 Request
    request = ReadingRequest(
        goal=body.goal,
        question=body.question,
        birth=body.birth,
        target_birth=body.target_birth,
        space=body.space,
        method_options=body.method_options,
        methods=body.methods,
        depth=body.depth,  # type: ignore[arg-type]
        language=body.language,  # type: ignore[arg-type]
    )

    try:
        result = await run_reading(request)
    except Exception as e:
        log.exception("Reading failed: %s", e)
        raise HTTPException(500, f"{type(e).__name__}: {e}")

    dt_ms = int((time.perf_counter() - t0) * 1000)
    log.info(
        "Reading completed: session=%s methods=%d signals=%d elapsed=%dms",
        result.session_id,
        len(result.methods_used),
        len(result.signals),
        dt_ms,
    )

    return result


# ── 健康检查 ─────────────────────────────────────────────────────────────────

@router.get("/reading/health")
def reading_health():
    """Reading 服务健康检查。"""
    from divination.aggregation.selector import FIXED_12_METHODS

    return {
        "status": "ok",
        "module": "reading",
        "methods_available": len(FIXED_12_METHODS),
        "methods": FIXED_12_METHODS,
        "disclaimer": DISCLAIMER[:80] + "...",
    }
