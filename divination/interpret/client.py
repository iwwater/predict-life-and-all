"""可插拔 LLM 客户端。MockClient 返回富内容模拟解读。"""
from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def complete(self, system: str, user: str) -> str: ...


class MockClient(LLMClient):
    """测试用:不联网,返回多段落的模拟解读,便于验证完整 pipeline 和 UI 展示。"""
    def complete(self, system: str, user: str) -> str:
        return (
            "### 整体印象\n\n"
            "基于你提供的盘面，这是一个内外兼修、倾向于在独立探索与协作借力之间不断调试的能量结构。"
            "整体气场偏于内敛但不乏锋芒，早期需要积累，中期有突破窗口。\n\n"
            "### 性格特质\n\n"
            "**核心优势：**\n"
            "1. 观察力敏锐，能迅速捕捉到别人忽略的细节和氛围变化。\n"
            "2. 有持续学习和自我修正的内在驱动力，不易被一时的得失击倒。\n"
            "3. 在压力下反而能激发出更强的韧性和创造力。\n\n"
            "**潜在盲点：**\n"
            "1. 过于内省时容易陷入反复思量而错失行动的时机。\n"
            "2. 在关系层面倾向于先照顾别人，偶尔忽略自己的边界。\n\n"
            "### 事业与方向\n\n"
            "当前的盘面能量偏向于需要深耕的领域。短期内不宜频繁跳转方向，"
            "在已有积累上做深、做强会比追逐新风口更顺。"
            "留意身边愿意提供资源或信息的人，他们的出现不是偶然。\n\n"
            "中长期来看，大约在两三年后有一个明显的上升波段，"
            "那段时间适合往外走、扩大影响力。现在则是打磨核心能力的阶段。\n\n"
            "### 感情与人际\n\n"
            "盘面显示在关系中你倾向于用行动而不是语言来表达在意。"
            "对方能感受到你的付出，但偶尔也会希望你直接说出来。"
            "适度的坦诚表达，不但不会削弱关系，反而能让彼此的边界更清晰。\n\n"
            "### 当前提示与建议\n\n"
            "1. **把想说的话写下来：** 即使不发给任何人，梳理清楚自己的想法本身就是一次有效的自我对话。\n"
            "2. **在'先照顾好自己'和'照顾他人'之间重新校准：** 本周至少为自己留出三次完全的独处时间。\n"
            "3. **那个搁置了很久的小项目，往前推一步：** 不必做到完美，只要让它在物理世界里有了一点点进展就行。\n\n"
            "(以上为传统文化象征视角的参考，非科学预测，重大决定请结合现实并咨询专业人士。)"
        )


class AnthropicClient(LLMClient):
    """Anthropic Claude 适配器(后端用,需自备 API Key)。
    使用 temperature=0 确保相同输入产生相同输出。
    内置简单 LRU 缓存避免重复 API 调用。
    """
    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-latest"):
        self.api_key = api_key
        self.model = model
        self._cache = {}  # hash → response

    def complete(self, system: str, user: str) -> str:
        import hashlib
        import json
        import urllib.request

        # 缓存键: system + user 的哈希 (相同输入不重复调 API)
        cache_key = hashlib.sha256(
            (system + user).encode("utf-8")
        ).hexdigest()

        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps({
                    "model": self.model,
                    "max_tokens": 4096,
                    "temperature": 0,  # 确定性输出: 相同输入 → 相同解读
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                }).encode("utf-8"),
                headers={
                    "content-type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
            result = "".join(b.get("text", "") for b in data.get("content", []))
            # 缓存结果 (最多 500 条)
            if len(self._cache) < 500:
                self._cache[cache_key] = result
            return result
        except Exception as e:
            return f"[LLM 调用失败:{type(e).__name__}: {e}]"
