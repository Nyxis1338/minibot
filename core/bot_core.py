import asyncio
from adapters.onebot_v11.ws_server import OneBotWSAdapter
from core.event_handler import handle_event, init_handler
from config.config_mgr import cfg_mgr

class BotCore:
    def __init__(self):
        self.ws_adapter = OneBotWSAdapter(msg_handler=handle_event)
        init_handler(self.ws_adapter)
        self.task = None
        self.running = False

    async def start_bot(self):
        if self.running:
            return
        self.running = True
        cfg_mgr.config["bot_running"] = True
        cfg_mgr.save_config()
        self.task = asyncio.create_task(self.ws_adapter.start())
        print("机器人核心已启动，等待NapCat连接")

    async def stop_bot(self):
        if not self.running:
            return
        self.running = False
        cfg_mgr.config["bot_running"] = False
        cfg_mgr.save_config()
        await self.ws_adapter.stop()
        if self.task:
            self.task.cancel()
        print("机器人已暂停")

# 全局单例
bot_core = BotCore()
