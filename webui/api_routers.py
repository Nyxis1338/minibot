from fastapi import APIRouter, Body, Query, UploadFile
from pydantic import BaseModel
from config.config_mgr import cfg_mgr
from core.bot_core import bot_core
import asyncio

router = APIRouter(prefix="/api")

# ---------------- Pydantic 数据模型 ----------------
class GlobalSaveModel(BaseModel):
    onebot: dict
    llm: dict
    global_robot: dict

class GroupSaveModel(BaseModel):
    select_persona: str
    random_prob: float
    cooldown_sec: int
    system_prompt: str

class PersonaSaveModel(BaseModel):
    name: str
    prompt: str

# ---------------- 机器人启停 ----------------
@router.post("/bot/start")
async def start_bot():
    asyncio.create_task(bot_core.start_bot())
    print("[LOG] 操作：点击启动机器人")
    return {"code":0, "msg":"机器人启动中"}

@router.post("/bot/stop")
async def stop_bot():
    await bot_core.stop_bot()
    print("[LOG] 操作：点击暂停机器人")
    return {"code":0, "msg":"机器人已暂停"}

@router.get("/bot/status")
async def bot_status():
    return {"code":0, "running": bot_core.running}

# ---------------- 全局配置 ----------------
@router.get("/global/config")
async def get_global():
    print("[LOG] 操作：加载全局配置页面")
    return {"code":0, "data": cfg_mgr.config}

@router.post("/global/save")
async def save_global(data: GlobalSaveModel = Body()):
    try:
        cfg_mgr.config["onebot"] = data.onebot
        cfg_mgr.config["llm"] = data.llm
        cfg_mgr.config["global_robot"] = data.global_robot
        cfg_mgr.save_config()
        print("[SUCCESS] 全局配置保存成功")
        return {"code":0, "msg":"全局配置保存成功，实时生效"}
    except Exception as e:
        print(f"[ERROR] 全局配置保存失败：{str(e)}")
        return {"code":-1, "msg":f"保存失败：{str(e)}"}

# ---------------- 人设库CRUD ----------------
@router.get("/persona/all")
async def get_all_persona():
    print("[LOG] 操作：加载所有人设列表")
    return {"code":0, "data": cfg_mgr.get_all_persona()}

@router.post("/persona/save")
async def save_persona(data: PersonaSaveModel = Body()):
    try:
        cfg_mgr.save_persona(data.name, data.prompt)
        print(f"[SUCCESS] 人设「{data.name}」保存成功")
        return {"code":0, "msg":"人设保存成功"}
    except Exception as e:
        print(f"[ERROR] 人设保存失败：{str(e)}")
        return {"code":-1, "msg":f"保存失败：{str(e)}"}

@router.delete("/persona/del")
async def del_persona(name: str = Query(...)):
    try:
        cfg_mgr.del_persona(name)
        print(f"[SUCCESS] 人设「{name}」已删除")
        return {"code":0, "msg":"人设删除成功"}
    except Exception as e:
        print(f"[ERROR] 人设删除失败：{str(e)}")
        return {"code":-1, "msg":f"删除失败：{str(e)}"}

# ---------------- 分群配置CRUD ----------------
@router.get("/group/all")
async def get_all_group():
    print("[LOG] 操作：加载分群配置列表")
    return {"code":0, "data": cfg_mgr.get_all_group()}

@router.post("/group/save")
async def save_group(
    group_id: str = Query(...),
    data: GroupSaveModel = Body()
):
    try:
        cfg_mgr.set_group(group_id, data.model_dump())
        print(f"[SUCCESS] 群{group_id}配置保存成功")
        return {"code":0, "msg":"群配置保存成功"}
    except Exception as e:
        print(f"[ERROR] 群{group_id} 保存失败：{str(e)}")
        return {"code":-1, "msg":f"群配置保存失败：{str(e)}"}

@router.delete("/group/del")
async def del_group(group_id: str = Query(...)):
    try:
        cfg_mgr.del_group(group_id)
        print(f"[SUCCESS] 群{group_id}配置已删除")
        return {"code":0, "msg":"群配置已删除"}
    except Exception as e:
        print(f"[ERROR] 群{group_id} 删除失败：{str(e)}")
        return {"code":-1, "msg":f"删除失败：{str(e)}"}

# ---------------- 配置导入导出 ----------------
@router.get("/config/export")
async def export_config():
    print("[LOG] 操作：导出全部配置")
    return {"code":0, "data": cfg_mgr.export_all_config()}

@router.post("/config/import")
async def import_config(data: dict = Body()):
    try:
        cfg_mgr.import_all_config(data)
        print("[SUCCESS] 配置导入完成")
        return {"code":0, "msg":"配置导入成功，刷新页面生效"}
    except Exception as e:
        print(f"[ERROR] 配置导入失败：{str(e)}")
        return {"code":-1, "msg":f"导入失败：{str(e)}"}
