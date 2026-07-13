import json
import os
from typing import Dict, Any

CONFIG_PATH = "data/config.json"

# 最小空骨架兜底，配置文件丢失/损坏时自动生成
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
        self.path = CONFIG_PATH  # 统一使用全局常量，不再硬编码字符串
        self._cache = None       # 内存缓存
        self._cache_dirty = False

    def load_file(self) -> Dict[str, Any]:
        # 缓存有效直接返回，减少磁盘IO
        if self._cache is not None and not self._cache_dirty:
            return self._cache

        # 配置文件不存在
        if not os.path.exists(self.path):
            sample_path = "data/config.sample.json"
            # 优先读取sample模板，sample损坏则使用内置空骨架
            if os.path.exists(sample_path):
                with open(sample_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            else:
                self._cache = EMPTY_SKELETON.copy()
            self._cache_dirty = False
            return self._cache

        # 配置文件存在，正常读取
        with open(self.path, "r", encoding="utf-8") as f:
            self._cache = json.load(f)
        self._cache_dirty = False
        return self._cache

    def save_file(self, data: Dict[str, Any]):
        self._cache = data
        self._cache_dirty = True
        # 统一全局json导入，无需局部import
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._cache_dirty = False

# 全局单例
cfg_mgr = ConfigManager()
