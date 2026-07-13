import json
import os
from typing import Dict, Any

CONFIG_PATH = "data/config.json"

# 仅最小空骨架，无任何写死厂商、人设、群规则，全部由WebUI配置持久化
EMPTY_SKELETON = {
    "onebot": {
        "listen_host": "0.0.0.0",
        "listen_port": 6199,
        "token": ""
    },
    "llm_providers": {},
    "personas": {},
    "group_rules": {}
}

class ConfigManager:
    def __init__(self):
        os.makedirs("data", exist_ok=True)

    def load_file(self) -> Dict[str, Any]:
        # 文件不存在 → 生成最小空骨架
        if not os.path.exists(CONFIG_PATH):
            self.save_file(EMPTY_SKELETON)
            return EMPTY_SKELETON.copy()
        # 读取已有配置
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        # 递归补全顶层key，兼容残缺旧文件
        filled_data = self._fill_skeleton(raw_data)
        self.save_file(filled_data)
        return filled_data

    def save_file(self, data: Dict[str, Any]):
        # 持久化写入json，WebUI所有修改落地此处
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _fill_skeleton(self, user_cfg: Dict[str, Any]) -> Dict[str, Any]:
        # 修复：先拷贝骨架，再用用户数据覆盖（子字典先骨架再用户，保留默认字段）
        full = EMPTY_SKELETON.copy()
        for top_key, skeleton_sub in EMPTY_SKELETON.items():
            if isinstance(skeleton_sub, dict):
                # 先填充骨架默认值，再叠加用户配置，缺失key保留默认
                sub_target = full[top_key]
                sub_target.update(user_cfg.get(top_key, {}))
            else:
                # 非字典顶层键直接覆盖
                if top_key in user_cfg:
                    full[top_key] = user_cfg[top_key]
        return full

# 全局单例
cfg_mgr = ConfigManager()
