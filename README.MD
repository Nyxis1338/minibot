# MiniBot 轻量化QQ群AI机器人

基于 Python + NapCat + OneBot11 自研轻量化机器人框架。  
支持自定义群聊人设、随机插话、@触发 AI 回复、多模型接入以及 Web 可视化管理面板。

## 项目架构

1. NapCatQQ：QQ 底层协议网关，反向 WS 对接本程序。
2. MiniBot 后端：
   - OneBot11 WS 服务端：接收 QQ 消息、发送回复。
   - FastAPI WebUI：可视化配置、启停机器人、模型连通测试。
   - LLM 抽象层：统一对接 DeepSeek / 智谱 / 讯飞星火等 OpenAI 格式大模型。
   - 内存配置管理：启动时一次性加载配置，运行期间优先读取内存，降低 I/O 压力。
3. 核心特性：
   - 多群独立配置：单独插话概率、冷却时间、专属人设 Prompt。
   - 互斥触发逻辑：@机器人时不会并行随机调用 AI，避免接口报错断开。
   - AI 接口错误仅控制台打印，群内静默不发送报错信息。
   - 双重退出机制：网页优雅停止 / Ctrl+C 强制一键销毁所有异步资源。
   - LLM 接口连通测试工具，前端直接校验 Key / 接口地址有效性。

## 环境依赖

### 1. 前置软件

- Python 3.10+
- NapCatQQ Windows 便携版（GitHub NapNeko/NapCatQQ）

### 2. Python 依赖一键安装

```bash
pip install -r requirements.txt
```

## 完整部署步骤

### 步骤 1：初始化配置文件（防密钥泄露）

1. 下载项目源码，保证全路径为英文，且不包含中文或空格。
2. 进入 data 文件夹，复制 config.sample.json，重命名为 config.json。
3. 所有密钥、Token 填写在 config.json 中。该文件已加入 git 忽略，不会上传到开源仓库。

### 步骤 2：启动 NapCatQQ 网关

1. 解压 NapCat 至纯英文路径，双击 launcher.bat。
2. 浏览器打开 NapCat WebUI：[http://127.0.0.1:6099/webui/]
3. 在“网络配置 → 反向 WebSocket 客户端”中填写参数：
   - WS 地址：`ws://127.0.0.1:6199/ws`
   - Access Token：自定义密钥（示例：`bot123456`）
   - 消息格式：Array
4. 保存配置，重启 NapCat，并扫码登录你的 QQ 小号机器人账号。

### 步骤 3：启动 MiniBot 主程序

在项目根目录终端执行：

```bash
python main.py
```

启动成功后会输出类似提示：

```text
✅ MiniBot WebUI 已启动
访问地址：http://127.0.0.1:7860
```

### 步骤 4：WebUI 后台完整配置教程

浏览器打开 `http://127.0.0.1:7860`，进入可视化面板。

#### 1. OneBot 基础配置

- 监听端口默认 6199，Token 必须与 NapCat 设置完全一致。
- 点击保存后，配置会实时更新到内存并持久化写入 config.json。

#### 2. 大模型厂商配置（核心功能）

1. 点击“新增模型厂商”，填写表单参数：
   - 厂商标识：自定义英文名称（例如 deepseek / glm / spark）
   - API Key：你的大模型平台密钥
   - Base URL：模型接口地址（例如 DeepSeek：`https://api.deepseek.com/v1/chat/completions`）
   - 模型名称、temperature、最大输出 tokens
2. 点击“🔍 测试接口连通性”按钮，校验接口可用性；测试成功后再保存配置。

#### 3. 人设 Prompt 配置

可自定义多套 AI 人设（如大女主、温柔聊天、搞笑搭话），保存后可绑定给任意 QQ 群使用。

#### 4. 群聊独立规则配置

每个 QQ 群可单独配置：

- 绑定使用的大模型
- 绑定专属人设
- 随机插话概率（取值 0~1，0 = 仅 @回复，不主动插话）
- 群发言冷却时间（单位：秒，防止高频刷屏）

#### 5. 机器人启停控制

- 启动机器人：一次性初始化所有模型客户端，开启 WS 监听，对接 NapCat 网关。
- 停止机器人：优雅关闭所有 LLM 会话、WS 服务，完整释放全部异步资源。

## QQ 群使用说明

1. @机器人 + 任意消息：强制 AI 回复，不受插话概率、冷却限制。
2. 普通群消息：根据配置概率随机插话，冷却时间内不会重复响应。
3. AI 接口异常 / 网络断开：仅终端打印错误日志，群内保持沉默，不会发送报错消息。

## 程序两种退出方式

1. 推荐优雅退出：WebUI 面板点击“停止机器人”，完整释放网络和协程资源，控制台无警告。
2. 紧急强制终止：终端按下 `Ctrl+C`，强制销毁全部异步任务，程序快速退出；这会残留少量资源警告，但不影响功能与配置。

## 项目文件完整目录结构

```text
MiniBot/
├── main.py                # 程序入口，信号捕获、Web服务启动
├── .gitignore             # Git过滤规则，屏蔽密钥、缓存文件
├── data/
│   ├── config.sample.json # 公开空白模板（无密钥，用于 GitHub 分享）
│   └── config.json       # 本地真实配置（git 忽略，存储 API Key、Token）
├── core/
│   ├── bot_state.py      # 机器人全局状态、模型池管理
│   ├── bot_core.py       # 机器人核心逻辑
│   ├── event_handler.py  # QQ消息处理、AI调用、随机插话互斥逻辑
│   └── runtime_cfg.py    # 运行时配置管理
├── adapters/
│   └── onebot_v11/
│       └── ws_server.py  # OneBot11 反向 WS 服务端实现
├── llm/
│   ├── base.py           # LLM 抽象基类（统一多模型接口）
│   ├── deepseek_provider.py
│   ├── qwen_provider.py
│   └── zhipu_provider.py
├── webui/
│   ├── server.py         # FastAPI Web 服务入口
│   ├── api_routers.py    # 后端接口（配置保存、模型连通测试接口）
│   └── static/index.html # 前端可视化管理页面
```

## data/config.sample.json 模板内容

```json
{
  "onebot": {
    "listen_host": "0.0.0.0",
    "listen_port": 6199,
    "token": ""
  },
  "llm_providers": {},
  "personas": {},
  "group_rules": {}
}
```

## 常见问题排查

1. NapCat 连接报错 ECONNREFUSED
   - 启动顺序：先运行 MiniBot，再重启 NapCat；检查 6199 端口是否被其他程序占用。
2. AI 调用提示 Server disconnected
   - 代码已做 @消息与随机插话互斥逻辑，不会并发发起 AI 请求；内置连接自动重建容错。
3. Ctrl+C 终端出现未关闭会话警告
   - 属于正常现象，不会损坏配置、不会影响程序运行；网页正常停止无该警告。
4. WebUI 保存配置失败
   - 检查 data 文件夹读写权限；确认 JSON 内容无语法错误。
5. 模型测试连接失败
   - 核对 API Key、接口地址、模型名称；检查本地网络是否可访问大模型服务商接口。

## 二次开发拓展说明

1. 新增大模型：仅需在 llm 目录新建 provider 文件，继承 BaseLLM 抽象类，实现 chat() 和 close() 两个抽象方法。
2. 新增 Web 功能：在 webui/api_routers.py 添加接口，前端 index.html 补充交互逻辑。
3. 所有业务配置统一读写内存，仅启动 / 保存时读写磁盘，性能损耗极低。

## 开源安全说明

1. config.sample.json 空白模板无任何密钥，可直接上传至 GitHub。
2. 本地真实配置文件 config.json 已加入 git 忽略，不会泄露私人 API 密钥、OneBot Token。
3. 所有密钥、敏感信息均本地存储，程序不会上传任何隐私数据至第三方平台。

```

