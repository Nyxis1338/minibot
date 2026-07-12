import asyncio
from typing import Dict
from llm.base import BaseLLM
from adapters.onebot_v11.ws_server import OneBotWSAdapter
from core.event_handler import handle_event, set_ws_adapter
from core.runtime_cfg import load_runtime_config, get_onebot, get_all_llm_names
from llm.deepseek_provider import DeepSeekLLM
from llm.zhipu_provider import ZhipuLLM
from llm.qwen_provider import QwenLLM

IS_BOT_RUNNING = False
WS_ADAPTER: OneBotWSAdapter | None = None
WS_TASK: asyncio.Task | None = None
# 多模型实例池 key=厂商标识
LLM_POOL: Dict[str, BaseLLM] = {}

def get_llm_by_name(name: str) -> BaseLLM | None:
    return LLM_POOL.get(name)

async def start_bot():
    global IS_BOT_RUNNING, WS_ADAPTER, WS_TASK, LLM_POOL
    if IS_BOT_RUNNING:
        return False, "机器人已在运行中"
    load_runtime_config()
    LLM_POOL.clear()
    # 初始化所有配置内存在的模型厂商
    all_llm = get_all_llm_names()
    for name in all_llm:
        try:
            if name == "deepseek":
                ins = DeepSeekLLM()
                LLM_POOL[name] = ins
            elif name == "zhipu":
                ins = ZhipuLLM()
                LLM_POOL[name] = ins
            elif name == "qwen":
                ins = QwenLLM()
                LLM_POOL[name] = ins
            print(f"[Bot] 加载模型厂商 {name} 完成")
        except Exception as e:
            print(f"[Bot] 厂商 {name} 初始化失败：{e}")
    # 启动WS
    ws_cfg = get_onebot()
    WS_ADAPTER = OneBotWSAdapter(msg_handler=handle_event)
    set_ws_adapter(WS_ADAPTER)
    WS_TASK = asyncio.create_task(WS_ADAPTER.start())
    IS_BOT_RUNNING = True
    print("[Bot] 机器人启动成功，WS服务等待NapCat连接")
    return True, "启动成功"

async def stop_bot():
    global IS_BOT_RUNNING, WS_ADAPTER, WS_TASK, LLM_POOL
    if not IS_BOT_RUNNING:
        return False, "机器人未启动"
    # 1、停止WS适配器
    if WS_ADAPTER is not None:
        try:
            await WS_ADAPTER.stop()
        except Exception as e:
            print(f"[Stop Warn] WS适配器关闭异常：{e}")
    # 2、取消WS后台任务
    if WS_TASK is not None:
        WS_TASK.cancel()
        try:
            await WS_TASK
        except (asyncio.CancelledError, Exception):
            pass
    # 3、逐个关闭所有LLM aiohttp会话
    close_coros = []
    for ins in LLM_POOL.values():
        close_coros.append(ins.close())
    if close_coros:
        await asyncio.gather(*close_coros, return_exceptions=True)
    LLM_POOL.clear()
    IS_BOT_RUNNING = False
    WS_ADAPTER = None
    WS_TASK = None
    print("[Bot] 机器人所有资源已停止释放")
    return True, "停止成功"

def get_bot_status():
    return {"running": IS_BOT_RUNNING}
