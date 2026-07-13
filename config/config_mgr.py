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
        self.path = "data/config.json"
        self._cache = None  # 内存缓存
        self._cache_dirty = False

    def load_file(self):
        # 缓存有效直接返回，减少磁盘IO
        if self._cache is not None and not self._cache_dirty:
            return self._cache
        if not os.path.exists(self.path):
            import json
            with open("data/config.sample.json","r",encoding="utf-8") as f:
                self._cache = json.load(f)
                self._cache_dirty = False
                return self._cache
        with open(self.path,"r",encoding="utf-8") as f:
            self._cache = json.load(f)
            self._cache_dirty = False
            return self._cache

    def save_file(self, data):
        self._cache = data
        self._cache_dirty = True
        import json
        with open(self.path,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=2)
        self._cache_dirty = False


# 全局单例
cfg_mgr = ConfigManager()
