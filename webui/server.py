from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(CUR_DIR, "static")

# 导入接口路由
from .api_routers import router as api_router

def create_web_app():
    app = FastAPI(title="MiniBot 配置管理面板")
    app.mount("/static", StaticFiles(directory=STATIC_FOLDER), name="static")
    app.include_router(api_router)

    @app.get("/")
    async def index():
        return RedirectResponse(url="/static/index.html")
    return app
