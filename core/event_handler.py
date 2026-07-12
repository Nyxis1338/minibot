import asyncio
import random
from config.config_mgr import cfg_mgr
from llm.deepseek_provider import DeepSeekLLM
from adapters.onebot_v11.ws_server import OneBotWSAdapter

group_last_send = {}
llm_client: DeepSeekLLM | None = None
ws_adapter: OneBotWSAdapter | None = None

def init_handler(adapter: OneBotWSAdapter):
    global llm_client, ws_adapter
    ws_adapter = adapter
    llm_client = DeepSeekLLM()

async def handle_event(event: dict):
    global llm_client, ws_adapter
    if llm_client is None or ws_adapter is None:
        return
    if event.get("post_type") != "message" or event.get("message_type") != "group":
        return
    group_id = str(event["group_id"])
    bot_qq = str(event["self_id"])
    sender = str(event["user_id"])
    raw_msg = event["raw_message"]
    if sender == bot_qq:
        return
    g_cfg = cfg_mgr.get_group_cfg(group_id)
    now_ts = asyncio.get_event_loop().time()
    last_ts = group_last_send.get(group_id, 0)
    if now_ts - last_ts < g_cfg["cooldown_sec"]:
        return
    at_tag = f"[CQ:at,qq={bot_qq}]"
    is_at = at_tag in raw_msg
    clean_msg = raw_msg.replace(at_tag, "").strip()
    reply = ""
    if is_at:
        reply = await llm_client.chat(g_cfg["system_prompt"], clean_msg)
    else:
        if random.random() < g_cfg["random_prob"]:
            reply = await llm_client.chat(g_cfg["system_prompt"], raw_msg)
    if not reply.strip():
        return
    await ws_adapter.send_group_msg(int(group_id), reply)
    group_last_send[group_id] = now_ts
