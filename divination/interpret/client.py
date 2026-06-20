"""可插拔 LLM 客户端。产品中替换为真实 provider；测试用 MockClient。"""
from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def complete(self, system: str, user: str) -> str: ...


class MockClient(LLMClient):
    """测试用：不联网，回显结构化占位，便于验证 pipeline。"""
    def complete(self, system: str, user: str) -> str:
        return ("【整体】（示例占位输出，接入真实模型后此处为解读正文）\n"
                "【事业财运】盘面显示金气偏旺、根气偏弱，倾向于在协作中借力会更顺。\n"
                "【建议】1) 多与人合作；2) 留意春夏之交的机会。")


class AnthropicClient(LLMClient):
    """真实适配器示例（需自备 API Key）。api.anthropic.com。"""
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key; self.model = model

    def complete(self, system: str, user: str) -> str:
        import json
        import urllib.request
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps({"model": self.model, "max_tokens": 1500,
                             "system": system, "messages": [{"role": "user", "content": user}]}).encode(),
            headers={"content-type": "application/json", "x-api-key": self.api_key,
                     "anthropic-version": "2023-06-01"})
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
        return "".join(b.get("text", "") for b in data.get("content", []))
