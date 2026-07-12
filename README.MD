# MiniBot

```text
MiniBot/
├── main.py                     # 程序入口，启动 FastAPI + 机器人异步循环
├── data/
│   └── config.json             # 自动生成，持久化所有配置
├── config/
│   └── config_mgr.py           # Model：配置读写、合并群配置
├── adapters/
│   └── onebot_v11/
│       └── ws_server.py        # OneBot11 反向 WS 服务端适配器
├── llm/
│   ├── base.py                 # LLM 抽象基类
│   └── deepseek_provider.py    # DeepSeek 异步实现
├── core/
│   ├── bot_core.py             # 机器人总控制器
│   └── event_handler.py        # 消息业务处理器（核心逻辑）
├── webui/
│   ├── api_routes.py           # Web 后端接口（CRUD 配置、启停机器人）
│   ├── server.py               # FastAPI Web 服务启动
│   └── static/
│       └── index.html          # 可视化管理页面（群配置、全局参数、启停）
└── requirements.txt            # 依赖清单
```
