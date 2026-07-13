import aiohttp
from llm.base import BaseLLMProvider

# 全局错误码映射表，统一区分Key错误 / 额度不足
ERROR_CODE_MAP = {
    "401": "密钥无效/过期，请核对API Key",
    "402": "账户余额/免费额度不足，请充值或更换密钥",
}

class UniversalProvider(BaseLLMProvider):
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
        timeout = aiohttp.ClientTimeout(total=15)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(url, json=payload, headers=headers) as resp:
                    resp_text = await resp.text()
                    # 统一状态码判断
                    if resp.status == 401:
                        raise Exception(f"【401】{ERROR_CODE_MAP['401']}")
                    if resp.status == 402:
                        raise Exception(f"【402】{ERROR_CODE_MAP['402']}")
                    if resp.status != 200:
                        raise Exception(f"接口异常 HTTP{resp.status}，返回内容：{resp_text[:300]}")

                    res = await resp.json()
                    # 接口返回业务错误
                    if res.get("error"):
                        err_msg = res["error"].get("message", str(res["error"]))
                        # 兼容各家自定义余额/密钥报错文本
                        if any(word in err_msg.lower() for word in ["balance", "余额", "额度不足"]):
                            raise Exception(f"【402】{ERROR_CODE_MAP['402']}")
                        if any(word in err_msg.lower() for word in ["invalid key", "密钥错误", "unauthorized", "401"]):
                            raise Exception(f"【401】{ERROR_CODE_MAP['401']}")
                        raise Exception(f"模型接口报错：{err_msg}")

                    return res["choices"][0]["message"]["content"].strip()

            except aiohttp.ClientError:
                raise Exception("网络连接失败，无法访问模型接口，请检查BaseURL或网络")
            except Exception as e:
                raise e
