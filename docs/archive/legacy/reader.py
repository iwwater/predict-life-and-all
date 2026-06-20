"""解读编排：盘面 + 问题 -> 护栏 -> LLM -> 护栏 -> 解读结果。"""
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
