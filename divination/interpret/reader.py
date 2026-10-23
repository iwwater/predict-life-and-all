"""解读编排：盘面 + 问题 -> 护栏 -> LLM -> 护栏 -> 解读结果。"""
import asyncio
import threading
from collections.abc import Iterator

from ..contracts import ChartResult
from . import guardrails, prompts
from .client import LLMClient, MockClient

# 软化替换的最长词是 4 字（"百分之百"/"毫无疑问"），留 16 字余量：
# 只有「确定不会再被后续文本影响」的前缀才会被发出。
_GUARDRAIL_LOOKAHEAD = 16


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


def _pump_stream(gen: Iterator[str], loop: asyncio.AbstractEventLoop,
                 queue: "asyncio.Queue", sentinel: object) -> None:
    """在后台线程里跑同步生成器，把片段交给事件循环（避免阻塞 event loop）。"""
    try:
        for piece in gen:
            if piece:
                loop.call_soon_threadsafe(queue.put_nowait, piece)
    except BaseException as exc:  # noqa: BLE001 - 原样转交主线程决定如何呈现
        loop.call_soon_threadsafe(queue.put_nowait, exc)
    finally:
        loop.call_soon_threadsafe(queue.put_nowait, sentinel)


async def interpret_stream(charts: list[ChartResult], question: str | None = None,
                           client: LLMClient | None = None):
    """逐段吐解读正文。

    真流式：LLM 每吐一段就转发一段（不再「等全文到手再假装逐字」）。
    护栏软化需要看得到完整词，所以保留 ``_GUARDRAIL_LOOKAHEAD`` 个字符的尾巴，
    只发出确定不会被后续文本改写的前缀。
    """
    client = client or MockClient()
    gi = guardrails.check_input(question)
    if gi.get("block"):
        yield {"type": "done", "meta": {"blocked": True, "softened_terms": [], "methods": [], "flags": ["crisis_redirect"]}}
        return

    msg = prompts.build_messages(charts, question)
    queue: asyncio.Queue = asyncio.Queue()
    sentinel = object()
    loop = asyncio.get_running_loop()
    thread = threading.Thread(
        target=_pump_stream,
        args=(client.stream(msg["system"], msg["user"]), loop, queue, sentinel),
        name="llm-stream",
        daemon=True,
    )
    thread.start()

    pending = ""
    flags: list[str] = []

    def _record(new_flags: list[str]) -> None:
        for flag in new_flags:
            if flag not in flags:
                flags.append(flag)

    while True:
        item = await queue.get()
        if item is sentinel:
            break
        if isinstance(item, BaseException):
            yield {"type": "error", "text": str(item)}
            return
        pending += item
        while len(pending) > _GUARDRAIL_LOOKAHEAD:
            emit_raw, pending = pending[:-_GUARDRAIL_LOOKAHEAD], pending[-_GUARDRAIL_LOOKAHEAD:]
            softened, new_flags = guardrails.soften_output(emit_raw)
            _record(new_flags)
            if softened:
                yield {"type": "delta", "text": softened}

    if pending:
        softened, new_flags = guardrails.soften_output(pending)
        _record(new_flags)
        if softened:
            yield {"type": "delta", "text": softened}

    extra = "\n".join(gi.get("notes", []))
    tail = ("\n\n" + extra if extra else "") + "\n\n" + prompts.DISCLAIMER
    yield {"type": "delta", "text": tail}

    yield {"type": "done", "meta": {
        "blocked": False,
        "softened_terms": flags,
        "methods": [c.method for c in charts],
        "flags": [],
    }}
