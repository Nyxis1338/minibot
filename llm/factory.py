from llm.base import BaseLLMProvider
from llm.universal_provider import UniversalProvider

# 仅存唯一通用实现，所有provider_type共用
# 若以后接入**非 OpenAI 兼容格式**的特殊模型（极少），仅需：
# 1. 在 `llm/` 新增独立专用 Provider 文件；
# 2. 在 `llm_factory.py` 的 `PROVIDER_MAP` 追加一条映射；
# 其余 99% 兼容 OpenAI 协议的模型，全部共用通用类，无需新增文件。

PROVIDER_MAP = {
    "deepseek": UniversalProvider,
    "zhipu": UniversalProvider,
    "qwen": UniversalProvider,
    "other": UniversalProvider
}

def create_llm(provider_type: str, api_key: str, base_url: str, model: str, temperature: float, max_tokens: int) -> BaseLLMProvider | None:
    cls = PROVIDER_MAP.get(provider_type, UniversalProvider)
    return cls(api_key, base_url, model, temperature, max_tokens)

def auto_infer_provider(name: str) -> str | None:
    """兼容旧配置自动推断厂商标识，仅用于兜底兼容历史配置"""
    for key in PROVIDER_MAP.keys():
        if name.startswith(key):
            return key
    return "other"
