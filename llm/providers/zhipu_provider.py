import aiohttp
from llm.base import BaseLLMProvider

class ZhipuProvider(BaseLLMProvider):
    async def chat(self, system_prompt: str, context):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = [{"role": "system", "content": system_prompt}] + context
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": messages
        }
        url = f"{self.base_url}/chat/completions"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                res = await resp.json()
                if res.get("error"):
                    err_msg = res["error"]["message"]
                    if "balance" in err_msg.lower():
                        raise Exception("⚠️ 智谱GLM 账户额度不足，请充值或更换密钥")
                    raise Exception(f"智谱GLM 接口异常：{err_msg}")
                return res["choices"][0]["message"]["content"].strip()
