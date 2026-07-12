import aiohttp
from llm.base import BaseLLM
from config.config_mgr import cfg_mgr

class DeepSeekLLM(BaseLLM):
    def __init__(self):
        llm_cfg = cfg_mgr.config["llm"]
        self.api_key = llm_cfg["api_key"].strip()
        self.base_url = llm_cfg["base_url"].rstrip("/")
        self.url = f"{self.base_url}/chat/completions"
        self.model = llm_cfg["model"]
        self.temp = llm_cfg["temperature"]
        self.max_tokens = llm_cfg["max_tokens"]
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json; charset=utf-8"
        }
        # 全局复用连接会话，只创建一次连接池
        self.session: aiohttp.ClientSession | None = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

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
                print(f"[LLM Debug] HTTP状态码: {resp.status}")
                raw_text = await resp.text()
                if resp.status != 200:
                    return f"AI接口异常 状态码{resp.status}，返回：{raw_text}"
                res = await resp.json()
                return res["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"AI调用失败：{str(e)}"
