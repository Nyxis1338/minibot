import aiohttp
from llm.base import BaseLLM
from core.runtime_cfg import get_llm_provider

class QwenLLM(BaseLLM):
    def __init__(self):
        provider_cfg = get_llm_provider("qwen")
        self.api_key = provider_cfg["api_key"].strip()
        self.base_url = provider_cfg["base_url"].rstrip("/")
        self.url = f"{self.base_url}/chat/completions"
        self.model = provider_cfg["model"]
        self.temp = provider_cfg["temperature"]
        self.max_tokens = provider_cfg["max_tokens"]
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json; charset=utf-8"
        }
        self.session: aiohttp.ClientSession | None = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            try:
                await self.session.close()
            except Exception:
                pass
            self.session = None

    async def chat(self, system_prompt: str, user_text: str) -> str:
        payload = {
            "model": self.model,
            "temperature": self.temp,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ]
        }
        try:
            session = await self.get_session()
            async with session.post(self.url, json=payload, headers=self.headers) as resp:
                raw_text = await resp.text()
                if resp.status != 200:
                    raise Exception(f"HTTP {resp.status} 返回：{raw_text}")
                res = await resp.json()
                return res["choices"][0]["message"]["content"].strip()
        except (aiohttp.ClientError, ConnectionResetError, OSError) as e:
            # 连接断开主动销毁会话，下次请求自动重建
            if self.session is not None:
                await self.session.close()
                self.session = None
            raise Exception(f"连接断开：{str(e)}")
        except Exception as e:
            raise e
