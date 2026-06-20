"""解读编排：盘面 + 问题 -> 护栏 -> LLM -> 护栏 -> 解读结果。"""
from ..contracts import ChartResult
from . import guardrails, prompts
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
    """Yield JSON-serializable streaming events for the interpret endpoint."""
    client = client or MockClient()
    gi = guardrails.check_input(question)
    if gi.get("block"):
        yield {"type": "done", "meta": {"blocked": True, "softened_terms": [], "methods": [], "flags": ["crisis_redirect"]}}
        return

    msg = prompts.build_messages(charts, question)
    try:
        raw = client.complete(msg["system"], msg["user"])
    except Exception as exc:
        yield {"type": "error", "text": str(exc)}
        return

    text, flags = guardrails.soften_output(raw)
    extra = "\n".join(gi.get("notes", []))
    reading = text + ("\n\n" + extra if extra else "") + "\n\n" + prompts.DISCLAIMER

    for i in range(0, len(reading), 60):
        yield {"type": "delta", "text": reading[i:i + 60]}

    yield {"type": "done", "meta": {
        "blocked": False,
        "softened_terms": flags,
        "methods": [c.method for c in charts],
        "flags": [],
    }}
