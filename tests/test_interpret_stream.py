"""⑦ 假流式修复的回归测试：解读端点必须边收边吐，而不是憋完全文再切片。"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

import server.main as main_module
from divination.contracts import ChartResult
from divination.interpret import AnthropicClient, interpret_stream
from divination.interpret.client import LLMClient
from divination.interpret.prompts import DISCLAIMER


def _charts() -> list[ChartResult]:
    return [ChartResult(
        method="bazi",
        school="east",
        engine="bazi",
        normalized={"elements": {"金": 2}},
        raw={"pillars": {"year": "庚午", "month": "壬午", "day": "辛亥", "hour": "壬辰"},
             "day_master": "辛"},
    )]


class _FakeStreamClient(LLMClient):
    """按预设片段「边算边吐」的桩客户端。"""

    def __init__(self, pieces: list[str]):
        self.pieces = pieces
        self.stream_calls = 0
        self.complete_calls = 0

    def complete(self, system: str, user: str, max_tokens: int = 1500) -> str:
        self.complete_calls += 1
        return "".join(self.pieces)

    def stream(self, system: str, user: str, max_tokens: int = 1500):
        self.stream_calls += 1
        for piece in self.pieces:
            yield piece


class _BoomClient(LLMClient):
    def complete(self, system: str, user: str, max_tokens: int = 1500) -> str:  # pragma: no cover
        raise RuntimeError("should not be called")

    def stream(self, system: str, user: str, max_tokens: int = 1500):
        yield "开头一点点"
        raise RuntimeError("上游模型断流")


async def _collect(charts, question=None, client=None, limit: int = 200):
    events = []
    async for event in interpret_stream(charts, question, client):
        events.append(event)
        if len(events) >= limit:  # pragma: no cover - 防御死循环
            break
    return events


def _run(coro):
    import asyncio

    return asyncio.run(coro)


def test_stream_uses_stream_not_complete():
    client = _FakeStreamClient(["一二三四五六七八九十" * 3, "再补一段文字" * 3])
    events = _run(_collect(_charts(), None, client))
    assert client.stream_calls == 1
    assert client.complete_calls == 0
    deltas = [e for e in events if e["type"] == "delta"]
    assert len(deltas) >= 2, "应该分多次吐出，而不是一次性给全文"
    assert events[-1]["type"] == "done"
    assert events[-1]["meta"]["methods"] == ["bazi"]


def test_stream_text_matches_non_stream_reading():
    pieces = ["【整体】盘面平稳。", "【事业】宜合作。", "【建议】留意秋冬。"]
    client = _FakeStreamClient(pieces)
    events = _run(_collect(_charts(), None, client))
    streamed = "".join(e["text"] for e in events if e["type"] == "delta")
    assert streamed == "".join(pieces) + "\n\n" + DISCLAIMER


def test_softening_survives_chunk_boundary():
    """软化词被切在两个片段之间时，仍然必须被替换掉。"""
    client = _FakeStreamClient(["这段话说你的命是注", "定的，不会变。"])
    events = _run(_collect(_charts(), None, client))
    text = "".join(e["text"] for e in events if e["type"] == "delta")
    assert "注定" not in text
    assert "倾向于" in text
    assert events[-1]["meta"]["softened_terms"] == ["注定"]


def test_stream_error_is_reported_not_swallowed():
    events = _run(_collect(_charts(), None, _BoomClient()))
    errors = [e for e in events if e["type"] == "error"]
    assert len(errors) == 1
    assert "上游模型断流" in errors[0]["text"]
    assert not [e for e in events if e["type"] == "done"], "出错时不应再补 done"


def test_crisis_question_still_blocks_before_llm():
    client = _FakeStreamClient(["不该被调用"])
    events = _run(_collect(_charts(), "我不想活了", client))
    assert client.stream_calls == 0
    assert len(events) == 1
    assert events[0]["meta"]["blocked"] is True


def test_medical_note_appended_before_disclaimer():
    client = _FakeStreamClient(["正文"])
    events = _run(_collect(_charts(), "我这个病能不能治好", client))
    text = "".join(e["text"] for e in events if e["type"] == "delta")
    assert "正规医疗" in text
    assert text.endswith(DISCLAIMER)


class _FakeSSEResponse:
    def __init__(self, lines: list[bytes]):
        self._lines = lines

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __iter__(self):
        return iter(self._lines)


def test_anthropic_stream_parses_sse(monkeypatch):
    lines = [
        b"event: message_start\n",
        b"data: {\"type\":\"message_start\"}\n",
        b"\n",
        b"event: content_block_delta\n",
        "data: ".encode() + json.dumps({"type": "content_block_delta", "delta": {"type": "text_delta", "text": "第一段"}}, ensure_ascii=False).encode() + b"\n",
        "data: ".encode() + json.dumps({"type": "content_block_delta", "delta": {"type": "text_delta", "text": "第二段"}}, ensure_ascii=False).encode() + b"\n",
        b"data: [DONE]\n",
    ]

    import urllib.request

    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=None: _FakeSSEResponse(lines))
    client = AnthropicClient(api_key="test-key")
    assert list(client.stream("sys", "usr")) == ["第一段", "第二段"]


def test_interpret_endpoint_streams_ndjson():
    client = TestClient(main_module.app)
    resp = client.post(
        "/api/interpret",
        json={
            "charts": [{
                "method": "bazi",
                "normalized": {"elements": {"金": 2}},
                "raw": {"pillars": {"year": "庚午", "month": "壬午", "day": "辛亥", "hour": "壬辰"},
                        "day_master": "辛"},
            }],
            "client": "mock",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/x-ndjson")
    events = [json.loads(line) for line in resp.text.splitlines() if line.strip()]
    assert events[-1]["type"] == "done"
    assert events[-1]["meta"]["methods"] == ["bazi"]
    assert sum(1 for e in events if e["type"] == "delta") >= 2
    joined = "".join(e["text"] for e in events if e["type"] == "delta")
    assert joined.endswith(DISCLAIMER)
