import asyncio
import random
import json
from core.runtime_cfg import get_group_runtime, update_group_context
from adapters.onebot_v11.ws_server import OneBotWSAdapter

ws_adapter: OneBotWSAdapter | None = None
group_last_send = {}

def set_ws_adapter(adapter: OneBotWSAdapter):
    global ws_adapter
    ws_adapter = adapter

async def handle_event(event: dict):
    global ws_adapter, group_last_send
    if ws_adapter is None:
        return
    # 只处理群消息
    if event.get("post_type") != "message" or event.get("message_type") != "group":
        return
    gid = str(event["group_id"])
    bot_qq = str(event["self_id"])
    raw_msg = event["raw_message"]
    sender = str(event["user_id"])
    # 过滤机器人自身消息
    if sender == bot_qq:
        return

    g_cfg = get_group_runtime(gid)
    if g_cfg is None:
        print(f"[Skip] 群{gid} 无配置，跳过")
        return
    cooldown = g_cfg["cooldown"]
    prob = g_cfg["prob"]
    sys_prompt = g_cfg["prompt"]
    target_llm_name = g_cfg["bind_llm"]
    enable_at = g_cfg["enable_at_reply"]
    enable_random = g_cfg["enable_random_chat"]
    ctx_max = g_cfg["context_max_len"]
    ctx_list = g_cfg["context"]

    # 冷却判断
    now = asyncio.get_event_loop().time()
    last = group_last_send.get(gid, 0)
    diff = now - last
    if diff < cooldown:
        print(f"[Skip] 群{gid} 冷却中，剩余 {cooldown - diff:.1f}s，阈值{cooldown}")
        return

    from core.bot_state import get_llm_by_name
    llm_client = get_llm_by_name(target_llm_name)
    if llm_client is None:
        print(f"[LLM] 群{gid} 绑定模型 {target_llm_name} 未初始化，跳过")
        return

    at_tag = f"[CQ:at,qq={bot_qq}]"
    is_at = at_tag in raw_msg
    clean_msg = raw_msg.replace(at_tag, "").strip()
    reply_text = None

    # 分支1：@机器人回复
    if is_at:
        if not enable_at:
            print(f"[Skip] 群{gid} @回复开关已关闭，忽略消息")
            return
        print(f"[Trigger] 群{gid} | 触发方式：@机器人 | 原始消息：{raw_msg}")
        # 存入用户消息上下文
        update_group_context(gid, "user", clean_msg, ctx_max)
        try:
            reply_text = await llm_client.chat(sys_prompt, ctx_list)
            # 存入AI回复上下文
            update_group_context(gid, "assistant", reply_text, ctx_max)
        except Exception as e:
            print(f"[LLM ERROR] 群{gid} @调用失败：{str(e)}")
            return
    # 分支2：随机插话
    else:
        if not enable_random:
            print(f"[Skip] 群{gid} 随机插话开关已关闭，忽略普通消息")
            return
        rand_val = random.random()
        print(f"[Trigger] 群{gid} | 触发方式：随机概率 | 当前随机值：{rand_val:.4f} | 阈值：{prob:.4f} | 原始消息：{raw_msg}")
        if rand_val < prob:
            update_group_context(gid, "user", raw_msg, ctx_max)
            try:
                reply_text = await llm_client.chat(sys_prompt, ctx_list)
                update_group_context(gid, "assistant", reply_text, ctx_max)
            except Exception as e:
                print(f"[LLM ERROR] 群{gid} 随机插话调用失败：{str(e)}")
                return

    # 下发回复
    if reply_text and reply_text.strip():
        send_data = {
            "action": "send_group_msg",
            "params": {"group_id": int(gid), "message": reply_text}
        }
        send_json = json.dumps(send_data)
        for cli in ws_adapter.clients:
            try:
                await cli.send(send_json)
            except Exception:
                continue
        group_last_send[gid] = now
