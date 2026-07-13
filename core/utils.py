import os
import json
from typing import Dict, Any
from config.config_mgr import cfg_mgr
from llm.factory import create_llm, auto_infer_provider

# ===================== 配置读取通用 =====================
def get_full_config() -> Dict[str, Any]:
    """全局读取完整配置"""
    return cfg_mgr.load_file()

# ===================== LLM 公共封装（替代原 bot_state.get_llm_by_name） =====================
def get_llm_by_name(name: str):
    cfg = get_full_config()
    llm_list = cfg["llm_providers"]
    if name not in llm_list:
        return None
    llm_info = llm_list[name]

    # 兼容旧配置缺失 provider_type
    if "provider_type" not in llm_info:
        p_type = auto_infer_provider(name)
        if not p_type:
            print(f"[Config Err] 模型【{name}】无法自动识别厂商，请WebUI编辑保存")
            return None
        print(f"[Config Warn] 模型【{name}】缺失provider_type，自动推断为 {p_type}")
    else:
        p_type = llm_info["provider_type"]

    return create_llm(
        provider_type=p_type,
        api_key=llm_info["api_key"],
        base_url=llm_info["base_url"],
        model=llm_info["model"],
        temperature=llm_info["temperature"],
        max_tokens=llm_info["max_tokens"]
    )

# ===================== 群运行时上下文读取 =====================
def get_group_runtime_safe(gid: str):
    """安全读取群配置，全部字段带默认值，杜绝KeyError"""
    cfg = get_full_config()
    group_rules = cfg.get("group_rules", {})
    rule = group_rules.get(gid, {})
    return {
        "cooldown_sec": rule.get("cooldown_sec", 120),
        "random_prob": rule.get("random_prob", 0.12),
        "bind_persona": rule.get("bind_persona", ""),
        "bind_llm": rule.get("bind_llm", ""),
        "enable_at_reply": rule.get("enable_at_reply", True),
        "enable_random_chat": rule.get("enable_random_chat", True),
        "context_max_len": rule.get("context_max_len", 8),
        "context": rule.get("context", [])
    }
