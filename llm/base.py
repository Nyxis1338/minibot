from abc import ABC, abstractmethod
# LLM 抽象基类

class BaseLLM(ABC):
    @abstractmethod
    async def chat(self, system_prompt: str, user_text: str) -> str:
        """异步对话接口，统一入参出参"""
        pass
