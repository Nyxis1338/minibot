import asyncio
from adapters.onebot_v11.ws_server import OneBotWSAdapter
from core.event_handler import set_ws_adapter
from config.config_mgr import cfg_mgr

ws_adapter: OneBotWSAdapter | None = None
ws_task = None
bot_running = False

async def start_bot() -> tuple[bool, str]:
    global ws_adapter, ws_task, bot_running
    if bot_running:
        return False, "机器人已在运行，无需重复启动"

    cfg = cfg_mgr.load_file()
    ob_cfg = cfg["onebot"]
    host = ob_cfg["listen_host"]
    port = ob_cfg["listen_port"]
    token = ob_cfg["token"]

    # 初始化WS适配器
    ws_adapter = OneBotWSAdapter(host, port, token)
    from core.event_handler import handle_event
    ws_adapter.set_event_handler(handle_event)
    set_ws_adapter(ws_adapter)

    # 后台异步启动WS循环监听（自动重连）
    loop = asyncio.get_event_loop()
    ws_task = loop.create_task(ws_adapter.start_server())
    bot_running = True
    return True, "机器人启动成功，持续等待NapCat连接"

async def stop_bot() -> tuple[bool, str]:
    global ws_adapter, ws_task, bot_running
    if not bot_running or ws_adapter is None:
        return False, "机器人当前未运行"

    await ws_adapter.stop_server()
    if ws_task:
        ws_task.cancel()
        try:
            await ws_task
        except asyncio.CancelledError:
            pass
    bot_running = False
    ws_adapter = None
    ws_task = None
    return True, "机器人已停止，不再监听NapCat连接"

def get_bot_status():
    global bot_running, ws_adapter
    connect_count = len(ws_adapter.clients) if ws_adapter else 0
    return {
        "running": bot_running,
        "napcat_connected_count": connect_count
    }

def get_llm_by_name(name: str):
    cfg = cfg_mgr.load_file()
    llm_list = cfg["llm_providers"]
    if name not in llm_list:
        return None
    llm_info = llm_list[name]
    from core.llm.base import LLMClient
    return LLMClient(
        api_key=llm_info["api_key"],
        base_url=llm_info["base_url"],
        model=llm_info["model"],
        temp=llm_info["temperature"],
        max_tokens=llm_info["max_tokens"]
    )
