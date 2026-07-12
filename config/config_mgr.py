import json
import os
from typing import Dict, Any

CONFIG_PATH = "data/config.json"

# 默认模板（新增robot_personas人设库）
DEFAULT_CONFIG = {
    "bot_running": False,
    "onebot": {
        "listen_host": "0.0.0.0",
        "listen_port": 6199,
        "token": "bot123456"
    },
    "llm": {
        "api_key": "sk-f8adf4015fb548169eb4d3c19afc7537",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-v4-flash",
        "temperature": 0.7,
        "max_tokens": 600
    },
    "global_robot": {
        "select_persona": "大女主",
        "random_prob": 0.12,
        "cooldown_sec": 120,
        "system_prompt": ""
    },
    # 人设库
    "robot_personas": {
        "大女主": """
你是独立清醒、气场沉稳的大女主。
理智通透、温柔有底线、有主见、不讨好、不卑微、不恋爱脑。
聊天规则：
1. 被@时认真完整回答；
2. 普通消息随缘接话，不强行刷屏；
3. 输出干净无特殊符号、无大量换行。
""",
        "冷漠男": """
性格冷淡话少，惜字如金，不爱闲聊，只回答核心问题。
语气平淡克制，不主动找话题，简短回复，不发表多余情绪。
""",
        "搞笑搭子": """
幽默随和，擅长接梗玩梗，轻松沙雕，适配闲聊群。
回复简短有趣，不长篇大论，贴合群内聊天氛围。
"""
    },
    # 预设示范群
    "group_custom": {
        "12345678": {
            "select_persona": "搞笑搭子",
            "random_prob": 0.3,
            "cooldown_sec": 60,
            "system_prompt": ""
        }
    }
}

class ConfigManager:
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(CONFIG_PATH):
            self.config = DEFAULT_CONFIG
            self.save_config()
        else:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            # 兼容旧配置：缺少字段自动补全默认值
            self._fill_default()

    def _fill_default(self):
        # 补全缺失顶层key
        for k, v in DEFAULT_CONFIG.items():
            if k not in self.config:
                self.config[k] = v
        self.save_config()

    def save_config(self):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    # ---------------- 人设库CRUD ----------------
    def get_all_persona(self) -> dict:
        return self.config["robot_personas"]

    def save_persona(self, name: str, prompt: str):
        self.config["robot_personas"][name] = prompt
        self.save_config()

    def del_persona(self, name: str):
        if name in self.config["robot_personas"]:
            del self.config["robot_personas"][name]
            self.save_config()

    def get_persona_prompt(self, name: str) -> str:
        return self.config["robot_personas"].get(name, "")

    # ---------------- 群配置工具（已修复缺失字段兼容） ----------------
    def get_group_cfg(self, group_id: str) -> Dict[str, Any]:
        global_cfg = self.config["global_robot"]
        group_custom = self.config["group_custom"].get(group_id, {})
        # 多层兜底，兼容旧配置无字段
        persona_name = group_custom.get("select_persona", global_cfg.get("select_persona", "大女主"))
        persona_text = self.get_persona_prompt(persona_name)
        group_prompt = group_custom.get("system_prompt", "").strip()
        final_prompt = group_prompt if group_prompt else persona_text
        return {
            "select_persona": persona_name,
            "random_prob": group_custom.get("random_prob", global_cfg.get("random_prob", 0.12)),
            "cooldown_sec": group_custom.get("cooldown_sec", global_cfg.get("cooldown_sec", 120)),
            "system_prompt": final_prompt
        }

    def set_group(self, group_id: str, data: dict):
        self.config["group_custom"][group_id] = data
        self.save_config()

    def del_group(self, group_id: str):
        if group_id in self.config["group_custom"]:
            del self.config["group_custom"][group_id]
            self.save_config()

    def get_all_group(self) -> dict:
        return self.config["group_custom"]

    # 配置导入导出
    def export_all_config(self) -> dict:
        return self.config

    def import_all_config(self, new_cfg: dict):
        self.config = new_cfg
        self.save_config()

# 全局单例
cfg_mgr = ConfigManager()
