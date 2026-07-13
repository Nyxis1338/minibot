import aiohttp
from llm.base import BaseLLMProvider

class QwenProvider(BaseLLMProvider):
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
        # 通义兼容模式剔除不支持字段
        payload.pop("tools", None)
        payload.pop("tool_choice", None)
        url = f"{self.base_url}/chat/completions"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                res = await resp.json()
                if res.get("error"):
                    err_msg = res["error"]["message"]
                    if "Insufficient Balance" in err_msg or "余额" in err_msg:
                        raise Exception("⚠️ 通义千问 账户余额不足，请充值")
                    raise Exception(f"通义千问 接口异常：{err_msg}")
                return res["choices"][0]["message"]["content"].strip()
