from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os

# 当前文件所在目录
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
# 拼接静态页面绝对路径
STATIC_FOLDER = os.path.join(CUR_DIR, "static")

# 匹配你的文件名 api_routers.py
from .api_routers import router as api_router

def create_web_app():
    app = FastAPI(title="MiniBot Web管理面板")
    # 挂载静态资源，使用绝对路径，避免相对路径识别失败
    app.mount("/static", StaticFiles(directory=STATIC_FOLDER), name="static")
    app.include_router(api_router)

    # 首页跳转
    @app.get("/")
    async def index():
        return RedirectResponse(url="/static/index.html")
    return app
