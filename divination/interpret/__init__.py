"""divination.interpret  ——  盘面 → 护栏 → LLM → 护栏 → 解读。

设计见前端设计计划书 §2.3 与 解读层.md。
可插拔 LLM 客户端:MockClient(测试)/ AnthropicClient(示例)/ 自定义。
"""
from .reader import interpret, interpret_stream
from . import prompts, guardrails
from .client import LLMClient, MockClient, AnthropicClient

__all__ = [
    "interpret", "interpret_stream", "prompts", "guardrails",
    "LLMClient", "MockClient", "AnthropicClient",
]
