"""解读编排：盘面 + 问题 -> 护栏 -> LLM -> 护栏 -> 解读结果。"""
import json
from ..contracts import ChartResult
from . import prompts, guardrails
from .client import LLMClient, MockClient


def interpret(charts: list[ChartResult], question: str | None = None,
              client: LLMClient | None = None) -> dict:
    client = client or MockClient()
    gi = guardrails.check_input(question)
    if gi.get("block"):
        return {"blocked": True, "reading": gi["message"], "flags": ["crisis_redirect"]}
    msg = prompts.build_messages(charts, question)
    raw = client.complete(msg["system"], msg["user"])
    text, flags = guardrails.soften_output(raw)
    extra = "\n".join(gi.get("notes", []))
    reading = text + ("\n\n" + extra if extra else "") + "\n\n" + prompts.DISCLAIMER
    return {"blocked": False, "reading": reading, "softened_terms": flags,
            "methods": [c.method for c in charts], "prompt_used": msg}


async def interpret_stream(charts: list[ChartResult], question: str | None = None,
                           client: LLMClient | None = None):
    """Async generator yielding JSON-serializable SSE events for streaming.

    Yields: {"type": "delta", "text": "..."}
            {"type": "done", "meta": {...}}
            {"type": "error", "text": "..."}
    """
    client = client or MockClient()
    gi = guardrails.check_input(question)
    if gi.get("block"):
        yield {"type": "done", "meta": {"blocked": True, "softened_terms": [], "methods": [], "flags": ["crisis_redirect"]}}
        return

    msg = prompts.build_messages(charts, question)
    try:
        raw = client.complete(msg["system"], msg["user"])
    except Exception as e:
        yield {"type": "error", "text": str(e)}
        return

    text, flags = guardrails.soften_output(raw)
    extra = "\n".join(gi.get("notes", []))
    reading = text + ("\n\n" + extra if extra else "") + "\n\n" + prompts.DISCLAIMER

    # Yield in chunks to simulate streaming
    chunk_size = 60
    for i in range(0, len(reading), chunk_size):
        yield {"type": "delta", "text": reading[i:i + chunk_size]}

    yield {"type": "done", "meta": {
        "blocked": False,
        "softened_terms": flags,
        "methods": [c.method for c in charts],
        "flags": [],
    }}

