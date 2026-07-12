import asyncio
import uvicorn
import os
import signal
import sys
import webbrowser

from webui.server import create_web_app

# 全局环境标记，保证启动横幅仅打印一次
if "MINIBOT_START" not in os.environ:
    os.environ["MINIBOT_START"] = "1"
    print("=" * 60)
    print("✅ MiniBot Web管理面板已启动")
    web_url = "http://127.0.0.1:7860"
    print(f"🌐 本地访问地址：{web_url}")
    print("=" * 60)

web_app = create_web_app()

# 极简强制退出函数，不等待资源收尾，直接清空循环
def force_exit(signum, frame):
    print("\n[CTRL+C] 强制终止所有异步任务，立刻退出程序")
    loop = asyncio.get_event_loop()
    # 取消全部正在运行的协程
    for task in asyncio.all_tasks(loop):
        task.cancel()
    # 直接关闭事件循环，抛弃所有未完成close操作
    loop.stop()
    sys.exit(0)

# 绑定Ctrl+C信号
signal.signal(signal.SIGINT, force_exit)

@web_app.router.lifespan_context
async def lifespan(app):
    yield
    # 网页正常停止时走优雅清理
    from core.bot_state import stop_bot
    await stop_bot()
    print("[正常退出] 资源已释放")

def open_webui_prompt():
    """启动询问弹窗，选择是否打开浏览器"""
    web_url = "http://127.0.0.1:7860"
    prompt = input("\n是否现在在浏览器中打开webui配置界面（Y/n）？")
    # 去除首尾空格，统一小写
    choice = prompt.strip().lower()
    # 回车 / y / yes 打开浏览器
    if choice in ("", "y", "yes"):
        try:
            webbrowser.open(web_url)
            print(f"✅ 已自动唤起浏览器访问 {web_url}")
        except Exception as e:
            print(f"❌ 自动打开浏览器失败，错误：{str(e)}")
            print(f"请手动访问地址：{web_url}")
    else:
        print(f"已跳过自动打开，你可以手动在浏览器输入地址访问：{web_url}")

if __name__ == "__main__":
    # 先启动uvicorn后台服务，再执行询问弹窗
    import threading
    def run_uvicorn():
        uvicorn.run(web_app, host="0.0.0.0", port=7860, reload=False)
    # 子线程运行web服务，不阻塞主线程输入
    server_thread = threading.Thread(target=run_uvicorn, daemon=True)
    server_thread.start()
    # 等待服务短暂启动完成
    import time
    time.sleep(0.8)
    # 弹出选择询问
    open_webui_prompt()
    # 主线程阻塞，维持程序运行
    while True:
        try:
            time.sleep(3600)
        except KeyboardInterrupt:
            force_exit(signal.SIGINT, None)
