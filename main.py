import asyncio
import uvicorn
import os
import signal
from webui.server import create_web_app
from core.bot_state import stop_bot

# 全局环境标记，保证启动横幅仅打印一次
if "MINIBOT_START" not in os.environ:
    os.environ["MINIBOT_START"] = "1"
    print("=" * 60)
    print("✅ MiniBot Web管理面板已启动")
    print(f"🌐 访问地址：http://127.0.0.1:7860")
    print("⚠️  请打开网页配置完成后，手动点击【启动机器人】连接NapCat")
    print("=" * 60)

web_app = create_web_app()
shutdown_task: asyncio.Task | None = None

async def full_shutdown():
    """完整异步资源清理：停止机器人、关闭LLM、WS、事件循环收尾"""
    print("\n[Signal] 检测到 Ctrl+C，开始安全释放所有资源...")
    try:
        await stop_bot()
    except Exception as e:
        print(f"[Shutdown Warn] 机器人停止异常：{e}")
    loop = asyncio.get_running_loop()
    tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    print("[Signal] 全部异步资源释放完成，程序退出")

def handle_sigint(signum, frame):
    """同步信号处理器，调度异步清理"""
    global shutdown_task
    loop = asyncio.get_running_loop()
    if shutdown_task is None or shutdown_task.done():
        shutdown_task = loop.create_task(full_shutdown())

# 注册Ctrl+C中断信号
signal.signal(signal.SIGINT, handle_sigint)

@web_app.router.lifespan_context
async def lifespan(app):
    yield
    # 正常网页点击停止/正常退出时也执行清理
    await full_shutdown()

if __name__ == "__main__":
    uvicorn.run(web_app, host="0.0.0.0", port=7860, reload=False)
