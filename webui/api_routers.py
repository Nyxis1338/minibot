from fastapi import APIRouter, Body, Query
from pydantic import BaseModel
import aiohttp
from config.config_mgr import cfg_mgr
from core.bot_state import start_bot, stop_bot, get_bot_status
import re

router = APIRouter(prefix="/api")

# 预编译IP正则
HOST_REG = re.compile(r"^(localhost|0\.0\.0\.0|127(\.\d{1,3}){3}|10(\.\d{1,3}){3}|172\.(1[6-9]|2\d|3[01])(\.\d{1,3}){2}|192\.168(\.\d{1,3}){2})$")

def is_host_valid(host: str) -> bool:
    if not host:
        return False
    parts = host.split(".")
    if len(parts) == 4:
        for seg in parts:
            if not seg.isdigit():
                return False
            n = int(seg)
            if n < 0 or n > 255:
                return False
    return bool(HOST_REG.match(host))

# 数据模型
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

class GroupRuleModel(BaseModel):
    bind_llm: str
    bind_persona: str
    random_prob: float
    cooldown_sec: int

# LLM测试请求模型
class LLMTestBody(BaseModel):
    api_key: str
    base_url: str
    model: str
    temperature: float
    max_tokens: int

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
    # 后端双重校验 listen_host
    onebot = data.get("onebot", {})
    host = onebot.get("listen_host", "")
    if not is_host_valid(host):
        return {"code": -1, "msg": f"监听Host [{host}] 格式不合法，仅支持 localhost / 0.0.0.0 / 127.0.0.1 / 内网10/172/192段IP"}
    # 端口校验
    port = onebot.get("listen_port", 0)
    if not isinstance(port, int) or port < 1 or port > 65535:
        return {"code": -1, "msg": "端口必须为1~65535数字"}
    try:
        cfg_mgr.save_file(data)
        return {"code": 0, "msg": "配置已保存到文件，重启机器人生效"}
    except Exception as e:
        return {"code": -1, "msg": f"保存失败：{str(e)}"}

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

# 【修复后】LLM连通测试接口，正确接收JSON Body
@router.post("/llm/test_connect")
async def test_llm_connect(body: LLMTestBody = Body()):
    headers = {
        "Authorization": f"Bearer {body.api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": body.model,
        "temperature": body.temperature,
        "max_tokens": body.max_tokens,
        "messages": [{"role": "user", "content": "hi"}]
    }
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = f"{body.base_url.rstrip('/')}/chat/completions"
            async with session.post(url, json=payload, headers=headers) as resp:
                resp_text = await resp.text()
                if resp.status == 200:
                    return {"code": 0, "msg": "接口连通正常"}
                else:
                    return {"code": 1, "msg": f"HTTP{resp.status} 错误返回：{resp_text[:300]}"}
    except aiohttp.ClientError as e:
        return {"code": 1, "msg": f"网络连接失败：{str(e)}"}
    except Exception as e:
        return {"code": 1, "msg": f"未知异常：{str(e)}"}
