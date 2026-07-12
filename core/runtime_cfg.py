from config.config_mgr import cfg_mgr

# 全局：群聊上下文缓存 key=群号 str
group_context_cache = {}

def get_group_runtime(gid: str):
    cfg = cfg_mgr.load_file()
    group_rules = cfg.get("group_rules", {})
    if gid not in group_rules:
        return None
    rule = group_rules[gid]
    # 初始化上下文缓存
    if gid not in group_context_cache:
        group_context_cache[gid] = []
    return {
        "bind_llm": rule["bind_llm"],
        "prompt": cfg["personas"].get(rule["bind_persona"], ""),
        "prob": rule["random_prob"],
        "cooldown": rule["cooldown_sec"],
        "enable_at_reply": rule["enable_at_reply"],
        "enable_random_chat": rule["enable_random_chat"],
        "context_max_len": rule["context_max_len"],
        "context": group_context_cache[gid]
    }

# 更新群上下文
def update_group_context(gid: str, role: str, content: str, max_len: int):
    ctx = group_context_cache.get(gid, [])
    ctx.append({"role": role, "content": content})
    # 限制上下文长度，超出则删除最早对话
    while len(ctx) > max_len:
        ctx.pop(0)
    group_context_cache[gid] = ctx

# 清空单群上下文（可拓展/clear指令调用）
def clear_group_context(gid: str):
    if gid in group_context_cache:
        group_context_cache[gid] = []
