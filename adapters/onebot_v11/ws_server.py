import asyncio
import websockets
import json
from urllib.parse import urlparse, parse_qs
from typing import Callable, Coroutine, Any
from core.runtime_cfg import get_onebot

class OneBotWSAdapter:
    def __init__(self, msg_handler: Callable[[dict], Coroutine[Any, Any, None]]):
        self.msg_handler = msg_handler
        self.ws_server = None
        self.clients = set()
        self.running = False

    async def handle_client(self, websocket):
        path = websocket.request.path
        parsed = urlparse(path)
        params = parse_qs(parsed.query)
        url_token = params.get("access_token", [None])[0]
        header_auth = websocket.request.headers.get("Authorization", "")
        header_token = None
        if header_auth and header_auth.startswith("Bearer "):
            header_token = header_auth[7:]
        real_token = url_token if url_token else header_token
        expect_token = get_onebot()["token"]
        if real_token != expect_token:
            print(f"NapCat鉴权失败，token不匹配")
            await websocket.close(1008)
            return
        print("✅ NapCat 成功接入WS")
        self.clients.add(websocket)
        try:
            async for raw in websocket:
                try:
                    event = json.loads(raw)
                    coro = self.msg_handler(event)
                    asyncio.create_task(coro)
                except json.JSONDecodeError:
                    continue
        finally:
            self.clients.remove(websocket)

    async def send_group_msg(self, group_id: int, message: str):
        send_json = json.dumps({
            "action": "send_group_msg",
            "params": {"group_id": group_id, "message": message}
        })
        for cli in self.clients:
            try:
                await cli.send(send_json)
            except Exception:
                continue

    async def start(self):
        cfg = get_onebot()
        host = cfg["listen_host"]
        port = cfg["listen_port"]
        self.ws_server = await websockets.serve(self.handle_client, host, port)
        self.running = True
        print(f"WS服务启动 ws://{host}:{port}")
        if self.ws_server:
            async with self.ws_server:
                await self.ws_server.serve_forever()

    async def stop(self):
        self.running = False
        if self.ws_server:
            self.ws_server.close()
            await self.ws_server.wait_closed()
        close_tasks = [cli.close() for cli in self.clients]
        await asyncio.gather(*close_tasks, return_exceptions=True)
        self.clients.clear()
        print("WS适配器已停止")
