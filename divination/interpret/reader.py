"""解读编排:盘面 + 问题 -> 护栏 -> LLM -> 护栏 -> 解读。"""
from . import prompts, guardrails
from .client import LLMClient, MockClient


def interpret(charts, question=None, client=None, enhanced_data=None):
    client = client or MockClient()
    gi = guardrails.check_input(question)
    if gi.get("block"):
        return {
            "blocked": True,
            "reading": gi["message"],
            "flags": ["crisis_redirect"],
            "methods": [c.method for c in charts],
            "meta": {"softened_terms": [], "notes": []},
        }
    msg = prompts.build_messages(charts, question, enhanced_data=enhanced_data)
    raw = client.complete(msg["system"], msg["user"])
    text, flags = guardrails.soften_output(raw)
    text = guardrails.strip_preamble(text)
    notes = gi.get("notes", [])
    extra = "\n".join(notes) if notes else ""
    reading = text + (("\n\n" + extra) if extra else "") + prompts.DISCLAIMER
    return {
        "blocked": False,
        "reading": reading,
        "softened_terms": flags,
        "methods": [c.method for c in charts],
        "meta": {"notes": notes},
    }


async def interpret_stream(charts, question=None, client=None, enhanced_data=None):
    """MVP 简化:MockClient 不真流,生成单次完整输出;真 LLM 接入后,这里改为逐 token yield。"""
    out = interpret(charts, question, client, enhanced_data=enhanced_data)
    yield {"type": "delta", "text": out["reading"]}
    yield {"type": "done", "meta": {
        "blocked": out["blocked"],
        "softened_terms": out.get("softened_terms", []),
        "methods": out["methods"],
        "flags": out.get("flags", []),
    }}
