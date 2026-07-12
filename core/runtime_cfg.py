from typing import Dict, Any
from config.config_mgr import cfg_mgr

RUNTIME_CFG: Dict[str, Any] = {}
GROUP_CACHE: Dict[str, Dict[str, Any]] = {}
PERSONA_CACHE: Dict[str, str] = {}
LLM_PROVIDER_CACHE: Dict[str, Dict[str, Any]] = {}
ONEBOT_CFG: Dict[str, Any] = {}

def load_runtime_config():
    global RUNTIME_CFG, GROUP_CACHE, PERSONA_CACHE, LLM_PROVIDER_CACHE, ONEBOT_CFG
    raw = cfg_mgr.load_file()
    RUNTIME_CFG = raw
    ONEBOT_CFG = raw["onebot"]
    LLM_PROVIDER_CACHE = raw["llm_providers"]
    PERSONA_CACHE = raw["personas"]
    GROUP_CACHE.clear()
    for gid, rule in raw["group_rules"].items():
        p_name = rule["bind_persona"]
        p_text = PERSONA_CACHE.get(p_name, "")
        llm_name = rule["bind_llm"]
        GROUP_CACHE[gid] = {
            "bind_llm": llm_name,
            "prompt": p_text,
            "prob": rule["random_prob"],
            "cooldown": rule["cooldown_sec"]
        }
    print("[Runtime] 运行配置一次性加载完成，内存只读")

def get_group_runtime(gid: str) -> Dict[str, Any] | None:
    return GROUP_CACHE.get(gid)

def get_persona_text(name: str) -> str:
    return PERSONA_CACHE.get(name, "")

def get_llm_provider(name: str) -> Dict[str, Any] | None:
    return LLM_PROVIDER_CACHE.get(name)

def get_onebot() -> Dict[str, Any]:
    return ONEBOT_CFG

def get_all_llm_names() -> list:
    return list(LLM_PROVIDER_CACHE.keys())
