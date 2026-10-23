"""可插拔 LLM 客户端。产品中替换为真实 provider；测试用 MockClient。"""
from abc import ABC, abstractmethod
from collections.abc import Iterator


class LLMClient(ABC):
    @abstractmethod
    def complete(self, system: str, user: str, max_tokens: int = 1500) -> str: ...

    def stream(self, system: str, user: str, max_tokens: int = 1500) -> Iterator[str]:
        """流式输出。默认实现退化为「先拿全文再切片」——
        只适合没有流式能力的桩客户端；真实 provider 应覆写本方法边收边吐。"""
        text = self.complete(system, user, max_tokens=max_tokens)
        step = 60
        for i in range(0, len(text), step):
            yield text[i:i + step]


class MockClient(LLMClient):
    """测试用：不联网，回显结构化占位，便于验证 pipeline。"""
    def complete(self, system: str, user: str, max_tokens: int = 1500) -> str:
        return ("【整体】（示例占位输出，接入真实模型后此处为解读正文）\n"
                "【事业财运】盘面显示金气偏旺、根气偏弱，倾向于在协作中借力会更顺。\n"
                "【建议】1) 多与人合作；2) 留意春夏之交的机会。")


class AnthropicClient(LLMClient):
    """真实适配器（需自备 API Key）。api.anthropic.com。

    reading_service 以 complete(system=..., user=..., max_tokens=...) 调用，
    此处签名必须对齐；网络调用带 timeout，避免无限阻塞事件循环。
    """
    DEFAULT_TIMEOUT_SECONDS = 120

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", timeout: int = DEFAULT_TIMEOUT_SECONDS):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def _payload(self, system: str, user: str, max_tokens: int, stream: bool) -> bytes:
        import json
        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        if stream:
            body["stream"] = True
        return json.dumps(body).encode()

    def _headers(self, stream: bool) -> dict[str, str]:
        headers = {
            "content-type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        if stream:
            headers["accept"] = "text/event-stream"
        return headers

    def complete(self, system: str, user: str, max_tokens: int = 1500) -> str:
        import json
        import urllib.request
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=self._payload(system, user, max_tokens, stream=False),
            headers=self._headers(stream=False),
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.load(resp)
        return "".join(b.get("text", "") for b in data.get("content", []))

    def stream(self, system: str, user: str, max_tokens: int = 1500) -> Iterator[str]:
        """真流式：Anthropic Messages API 的 SSE，逐段吐 content_block_delta 文本。"""
        import json
        import urllib.request
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=self._payload(system, user, max_tokens, stream=True),
            headers=self._headers(stream=True),
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            for raw in resp:
                line = raw.decode("utf-8", "replace") if isinstance(raw, (bytes, bytearray)) else str(raw)
                line = line.strip()
                if not line or line.startswith(":"):
                    continue
                if not line.startswith("data:"):
                    continue  # event: ping / event: message_start 等
                data = line[len("data:"):].strip()
                if not data or data == "[DONE]":
                    continue
                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    continue
                kind = event.get("type")
                if kind == "content_block_delta":
                    piece = (event.get("delta") or {}).get("text") or ""
                    if piece:
                        yield piece
                elif kind == "error":
                    message = (event.get("error") or {}).get("message") or "stream error"
                    raise RuntimeError(f"LLM stream error: {message}")
