from abc import ABC, abstractmethod
from typing import List, Dict

class BaseLLMProvider(ABC):
    def __init__(self, api_key: str, base_url: str, model: str, temperature: float, max_tokens: int):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    async def chat(self, system_prompt: str, context: List[Dict]) -> str:
        """
        context: [{"role":"user","content":"xxx"}, {"role":"assistant","content":"xxx"}]
        单消息等价于只包含1条user的上下文数组，统一复用该接口
        """
        pass
