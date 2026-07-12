from abc import ABC, abstractmethod

class BaseLLM(ABC):
    @abstractmethod
    async def chat(self, system_prompt: str, user_text: str) -> str:
        pass

    @abstractmethod
    async def close(self):
        pass
