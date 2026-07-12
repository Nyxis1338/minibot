import asyncio
import uvicorn
import os
from webui.server import create_web_app
from core.bot_core import bot_core

# 用环境变量标记当前进程是否已经打印横幅，跨进程隔离
if os.environ.get("MINIBOT_PRINTED") is None:
    os.environ["MINIBOT_PRINTED"] = "1"
    print("=" * 60)
    print("✅ MiniBot 框架启动成功")
    print(f"🌐 Web管理面板访问地址：http://127.0.0.1:7860")
    print("=" * 60)

web_app = create_web_app()

@web_app.router.lifespan_context
async def lifespan(app):
    yield
    await bot_core.stop_bot()
    print("\n🛑 MiniBot 程序已安全退出")

if __name__ == "__main__":
    uvicorn.run(web_app, host="0.0.0.0", port=7860, reload=False)
