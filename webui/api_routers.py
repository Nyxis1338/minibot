from fastapi import APIRouter, Body, Query
from pydantic import BaseModel
from config.config_mgr import cfg_mgr
from core.bot_state import start_bot, stop_bot, get_bot_status

router = APIRouter(prefix="/api")

class OneBotModel(BaseModel):
    listen_host: str
    listen_port: int
    token: str

class LLMProviderModel(BaseModel):
    api_key: str
    base_url: str
    model: str
    temperature: float
    max_tokens: int

class PersonaModel(BaseModel):
    name: str
    prompt: str

# 新增bind_llm
class GroupRuleModel(BaseModel):
    bind_llm: str
    bind_persona: str
    random_prob: float
    cooldown_sec: int

@router.get("/bot/status")
async def bot_status():
    return {"code": 0, "data": get_bot_status()}

@router.post("/bot/start")
async def bot_start():
    ok, msg = await start_bot()
    return {"code": 0 if ok else -1, "msg": msg}

@router.post("/bot/stop")
async def bot_stop():
    ok, msg = await stop_bot()
    return {"code": 0 if ok else -1, "msg": msg}

@router.get("/config/all")
async def get_full_config():
    return {"code": 0, "data": cfg_mgr.load_file()}

@router.post("/config/save")
async def save_full_config(data: dict = Body()):
    try:
        cfg_mgr.save_file(data)
        return {"code": 0, "msg": "配置已保存到文件，重启机器人生效"}
    except Exception as e:
        return {"code": -1, "msg": f"保存失败：{str(e)}"}

@router.get("/config/export")
async def export_cfg():
    return {"code": 0, "data": cfg_mgr.load_file()}

@router.get("/persona/list")
async def list_persona():
    cfg = cfg_mgr.load_file()
    return {"code": 0, "data": cfg["personas"]}

@router.post("/persona/save")
async def save_persona(item: PersonaModel = Body()):
    cfg = cfg_mgr.load_file()
    cfg["personas"][item.name] = item.prompt
    cfg_mgr.save_file(cfg)
    return {"code": 0, "msg": "人设保存成功"}

@router.delete("/persona/del")
async def del_persona(name: str = Query()):
    cfg = cfg_mgr.load_file()
    if name in cfg["personas"]:
        del cfg["personas"][name]
        cfg_mgr.save_file(cfg)
    return {"code": 0, "msg": "人设已删除"}

@router.get("/group/list")
async def list_group():
    cfg = cfg_mgr.load_file()
    return {"code": 0, "data": cfg["group_rules"]}

@router.post("/group/save")
async def save_group(gid: str = Query(), item: GroupRuleModel = Body()):
    cfg = cfg_mgr.load_file()
    cfg["group_rules"][gid] = item.model_dump()
    cfg_mgr.save_file(cfg)
    return {"code": 0, "msg": "群配置保存成功"}

@router.delete("/group/del")
async def del_group(gid: str = Query()):
    cfg = cfg_mgr.load_file()
    if gid in cfg["group_rules"]:
        del cfg["group_rules"][gid]
        cfg_mgr.save_file(cfg)
    return {"code": 0, "msg": "群配置已删除"}

@router.get("/llm/list")
async def list_llm():
    cfg = cfg_mgr.load_file()
    return {"code": 0, "data": cfg["llm_providers"]}

@router.post("/llm/save")
async def save_llm(name: str = Query(), item: LLMProviderModel = Body()):
    cfg = cfg_mgr.load_file()
    cfg["llm_providers"][name] = item.model_dump()
    cfg_mgr.save_file(cfg)
    return {"code": 0, "msg": "模型配置保存成功"}

@router.delete("/llm/del")
async def del_llm(name: str = Query()):
    cfg = cfg_mgr.load_file()
    if name in cfg["llm_providers"]:
        del cfg["llm_providers"][name]
        cfg_mgr.save_file(cfg)
    return {"code": 0, "msg": "模型配置已删除"}
