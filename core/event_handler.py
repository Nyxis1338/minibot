import asyncio
import random
import json
from adapters.onebot_v11.ws_server import OneBotWSAdapter
# 只单向导入utils，无任何反向依赖
from core.utils import get_llm_by_name, get_group_runtime_safe

ws_adapter: OneBotWSAdapter | None = None
group_last_send = {}

def set_ws_adapter(adapter: OneBotWSAdapter):
    global ws_adapter
    ws_adapter = adapter

# 上下文更新函数提前声明，统一规范
async def update_group_context(gid: str, role: str, content: str, max_len: int):
    from core.utils import get_full_config
    from config.config_mgr import cfg_mgr
    cfg = get_full_config()
    group = cfg["group_rules"].setdefault(gid, {})
    ctx = group.setdefault("context", [])
    ctx.append({"role": role, "content": content})
    if len(ctx) > max_len:
        ctx = ctx[-max_len:]
    cfg["group_rules"][gid]["context"] = ctx
    cfg_mgr.save_file(cfg)

async def handle_event(event: dict):
    global ws_adapter, group_last_send
    if ws_adapter is None or not ws_adapter.clients:
        return
    if event.get("post_type") != "message" or event.get("message_type") != "group":
        return
    gid = str(event["group_id"])
    bot_qq = str(event["self_id"])
    raw_msg = event["raw_message"]
    sender = str(event["user_id"])
    if sender == bot_qq:
        return

    # 使用utils安全读取，自带默认值，杜绝KeyError
    g_cfg = get_group_runtime_safe(gid)
    if not g_cfg:
        print(f"[Skip] 群{gid} 无配置，跳过")
        return

    # ========== 新增：拦截@全体成员逻辑 ==========
    msg_segments = event.get("message", [])
    has_at_all = False
    for seg in msg_segments:
        if seg.get("type") == "at" and seg["data"].get("qq") == "all":
            has_at_all = True
            break
    if has_at_all:
        print(f"[Skip] 群{gid} 消息包含@全体成员，拦截AI回复防风控")
        return
    # ==========================================

    cooldown = g_cfg["cooldown_sec"]
    prob = g_cfg["random_prob"]
    sys_prompt = g_cfg["bind_persona"]
    target_llm_name = g_cfg["bind_llm"]

    # 新增提前校验空模型
    if not target_llm_name or target_llm_name.strip() == "":
        print(f"[Skip] 群{gid} 绑定模型名称为空，跳过AI调用")
        return
    llm_client = get_llm_by_name(target_llm_name)
    if llm_client is None:
        print(f"[LLM] 群{gid} 绑定模型 {target_llm_name} 未初始化，跳过")
        return

    enable_at = g_cfg["enable_at_reply"]
    enable_random = g_cfg["enable_random_chat"]
    ctx_max = g_cfg["context_max_len"]
    ctx_list = g_cfg["context"]
    now = asyncio.get_event_loop().time()
    last = group_last_send.get(gid, 0)
    diff = now - last
    if diff < cooldown:
        print(f"[Skip] 群{gid} 冷却中，剩余 {cooldown - diff:.1f}s，阈值{cooldown}")
        return

    at_tag = f"[CQ:at,qq={bot_qq}]"
    is_at = at_tag in raw_msg
    clean_msg = raw_msg.replace(at_tag, "").strip()
    reply_text = None

    # @触发分支
    if is_at:
        if not enable_at:
            print(f"[Skip] 群{gid} @回复开关已关闭，忽略消息")
            return
        print(f"[Trigger] 群{gid} | @触发 | 消息：{raw_msg}")
        await update_group_context(gid, "user", clean_msg, ctx_max)
        new_g_cfg = get_group_runtime_safe(gid)
        ctx_list = new_g_cfg["context"]
        try:
            reply_text = await llm_client.chat(sys_prompt, ctx_list)
            await update_group_context(gid, "assistant", reply_text, ctx_max)
        except Exception as e:
            print(f"[LLM ERROR] @调用失败: {str(e)}")
            return
    # 随机插话分支
    else:
        if not enable_random:
            return
        rand_val = random.random()
        print(f"[Trigger] 群{gid} 随机值{rand_val:.4f} 阈值{prob:.4f}")
        # 修复：< 改为 <= 达到阈值正常触发
        if rand_val <= prob:
            await update_group_context(gid, "user", raw_msg, ctx_max)
            new_g_cfg = get_group_runtime_safe(gid)
            ctx_list = new_g_cfg["context"]
            try:
                reply_text = await llm_client.chat(sys_prompt, ctx_list)
                await update_group_context(gid, "assistant", reply_text, ctx_max)
            except Exception as e:
                print(f"[LLM ERROR] 随机调用失败: {str(e)}")
                return
    # 发送消息
    if reply_text and reply_text.strip():
        send_data = {"action": "send_group_msg", "params": {"group_id": int(gid), "message": reply_text}}
        send_json = json.dumps(send_data)
        conn_count = len(ws_adapter.clients)
        if conn_count == 0:
            print(f"[Send Warn] 群{gid} 无NapCat/Lagrange连接")
            return
        for cli in ws_adapter.clients:
            try:
                await cli.send(send_json)
                print(f"[Send OK] 群{gid} 已推送AI回复")
            except Exception:
                print(f"[Send Fail] 群{gid} 单连接发送失败")
                continue
        group_last_send[gid] = now

# 保留原有上下文更新函数，移至文件上方规范排版
async def update_group_context(gid: str, role: str, content: str, max_len: int):
    from core.utils import get_full_config
    from config.config_mgr import cfg_mgr
    cfg = get_full_config()
    group = cfg["group_rules"].setdefault(gid, {})
    ctx = group.setdefault("context", [])
    ctx.append({"role": role, "content": content})
    if len(ctx) > max_len:
        ctx = ctx[-max_len:]
    cfg["group_rules"][gid]["context"] = ctx
    cfg_mgr.save_file(cfg)
