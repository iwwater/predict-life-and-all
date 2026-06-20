"""Streaming interpretation endpoint.

Request: {"charts": [ChartResult, ...], "question": "...", "client": "mock|anthropic"}
Response: newline-delimited JSON events:
  {"type": "delta", "text": "..."}
  {"type": "done", "meta": {...}}
"""
import json
import logging
import os
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from divination.contracts import ChartResult
from divination.interpret import AnthropicClient, MockClient, interpret_stream

router = APIRouter()
log = logging.getLogger("interpret")


class InterpretRequest(BaseModel):
    charts: list[dict] = Field(..., min_length=1)
    question: str | None = None
    client: Literal["mock", "anthropic"] = "mock"
    enhanced_data: dict | None = None  # cross_validation, peach_blossom, etc.


def _ndjson(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False) + "\n"


def _to_charts(chart_dicts: list[dict]) -> list[ChartResult]:
    out = []
    for i, c in enumerate(chart_dicts):
        if not isinstance(c, dict):
            raise HTTPException(422, f"charts[{i}] must be an object, got {type(c).__name__}")
        if "method" not in c:
            raise HTTPException(422, f"charts[{i}] missing required field: method")
        out.append(
            ChartResult(
                method=c["method"],
                school=c.get("school", "east"),
                engine=c.get("engine", "unknown"),
                normalized=c.get("normalized", {}),
                raw=c.get("raw", {}),
            )
        )
    return out


@router.post("/interpret")
async def interpret_endpoint(body: InterpretRequest):
    if body.client == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise HTTPException(400, "client=anthropic requires server env ANTHROPIC_API_KEY")
        client = AnthropicClient(api_key=api_key)
    else:
        client = MockClient()

    charts = _to_charts(body.charts)

    async def gen():
        try:
            async for chunk in interpret_stream(charts, body.question, client):
                yield _ndjson(chunk)
        except Exception as e:
            log.exception("interpret failed: %s", e)
            yield _ndjson({"type": "error", "text": str(e)})

    return StreamingResponse(gen(), media_type="application/x-ndjson")
