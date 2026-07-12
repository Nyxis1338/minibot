import asyncio
import uvicorn
import os
import signal
import sys
import webbrowser
import threading
import time
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from webui.api_routers import router as api_router

# 创建WebUI服务
app = FastAPI(title="MiniQQBot 管理后台")
# 挂载静态页面
app.mount("/", StaticFiles(directory="webui/static", html=True), name="static")
app.include_router(api_router)

# 极简强制退出函数
def force_exit(signum, frame):
    print("\n[CTRL+C] 强制终止所有异步任务，立刻退出程序")
    loop = asyncio.get_event_loop()
    for task in asyncio.all_tasks(loop):
        task.cancel()
    loop.stop()
    sys.exit(0)

# 绑定Ctrl+C信号
signal.signal(signal.SIGINT, force_exit)

async def run_web_server():
    # 更换安全端口7860
    web_url = "http://127.0.0.1:7860"
    config = uvicorn.Config(app, host="0.0.0.0", port=7860, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

def open_webui_prompt():
    """启动询问弹窗，选择是否自动打开浏览器"""
    web_url = "http://127.0.0.1:7860"
    prompt = input("\n是否现在在浏览器中打开webui配置界面（Y/n）？")
    choice = prompt.strip().lower()
    if choice in ("", "y", "yes"):
        try:
            webbrowser.open(web_url)
            print(f"✅ 已自动唤起浏览器访问 {web_url}")
        except Exception as e:
            print(f"❌ 自动打开浏览器失败：{str(e)}")
            print(f"请手动复制地址访问：{web_url}")
    else:
        print(f"已跳过自动打开，手动访问地址：{web_url}")

if __name__ == "__main__":
    # 全局环境标记，保证启动横幅仅打印一次
    if "MINIBOT_START" not in os.environ:
        os.environ["MINIBOT_START"] = "1"
        print("=" * 60)
        print("✅ MiniBot Web管理面板已启动")
        web_url = "http://127.0.0.1:7860"
        print(f"🌐 本地访问地址：{web_url}")
        print("=" * 60)

    # 子线程运行Web服务，不阻塞主线程输入弹窗
    server_thread = threading.Thread(target=asyncio.run, args=(run_web_server(),), daemon=True)
    server_thread.start()
    time.sleep(0.8)
    open_webui_prompt()
    # 主线程永久阻塞
    while True:
        try:
            time.sleep(3600)
        except KeyboardInterrupt:
            force_exit(signal.SIGINT, None)
