import asyncio
import websockets
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
from typing import Set

class OneBotWSAdapter:
    def __init__(self, host: str, port: int, token: str):
        self.host = host
        self.port = port
        self.token = token
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        self.running = False
        self.event_handler = None

    def set_event_handler(self, handler):
        self.event_handler = handler

    async def handle_conn(self, websocket):
        # Token鉴权
        path = websocket.path
        token_ok = False
        if "?" in path:
            query_str = path.split("?")[1]
            params = dict(p.split("=") for p in query_str.split("&") if "=" in p)
            token_ok = params.get("token", "") == self.token
        if not token_ok:
            print(f"[WS] 收到非法连接，Token校验失败，断开")
            await websocket.close(code=1008, reason="token invalid")
            return

        print(f"[WS] NapCat 反向WS连接建立成功！")
        self.clients.add(websocket)
        try:
            async for raw in websocket:
                try:
                    data = eval(raw) if raw.startswith("{") else None
                    if data and self.event_handler:
                        asyncio.create_task(self.event_handler(data))
                except Exception as e:
                    print(f"[WS] 消息解析异常: {str(e)}")
        except (ConnectionClosedOK, ConnectionClosedError):
            print(f"[WS] NapCat 连接断开，等待重连...")
        finally:
            self.clients.discard(websocket)

    async def start_server(self):
        self.running = True
        while self.running:
            try:
                print(f"[WS] 正在启动监听 {self.host}:{self.port}，等待NapCat反向连接...")
                self.server = await websockets.serve(
                    self.handle_conn,
                    host=self.host,
                    port=self.port
                )
                await self.server.wait_closed()
            except Exception as e:
                print(f"[WS] 服务异常，5秒后自动重试: {str(e)}")
                await asyncio.sleep(5)

    async def stop_server(self):
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        # 断开所有现有NapCat连接
        for cli in list(self.clients):
            await cli.close()
        self.clients.clear()
        print("[WS] WS监听服务已完全停止")
