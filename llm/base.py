import aiohttp

class LLMClient:
    def __init__(self, api_key: str, base_url: str, model: str, temp: float, max_tokens: int):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/") + "/chat/completions"
        self.model = model
        self.temp = temp
        self.max_tokens = max_tokens

    async def chat(self, system_prompt: str, context: list[dict]) -> str:
        """
        system_prompt: 人设系统提示词
        context: 对话上下文数组 [{"role":"user","content":"xxx"},{"role":"assistant","content":"xxx"}]
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = [{"role": "system", "content": system_prompt}] + context
        payload = {
            "model": self.model,
            "temperature": self.temp,
            "max_tokens": self.max_tokens,
            "messages": messages
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, json=payload, headers=headers) as resp:
                res = await resp.json()
                if res.get("error"):
                    raise Exception(res["error"]["message"])
                return res["choices"][0]["message"]["content"].strip()
