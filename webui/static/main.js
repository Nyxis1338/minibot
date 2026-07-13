const base = "/api";
let fullConfig = {};
let currentEditLLM = "";
let currentEditPersona = "";
let currentEditGroupId = "";
let editCachedProviderType = "";

// ====================== 公共工具函数 ======================
function toast(msg, type = "suc") {
    const box = document.getElementById("toastBox");
    const div = document.createElement("div");
    div.className = `toast ${type}`;
    div.innerText = msg;
    box.appendChild(div);
    setTimeout(() => div.remove(), 3000);
}

function openModal(domId) {
    document.getElementById(domId).style.display = "grid";
}

function closeModal(domId) {
    document.getElementById(domId).style.display = "none";
}

// 统一保存全部配置
async function saveFullConfig() {
    try {
        const res = await fetch(`${base}/config/save`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(fullConfig)
        });
        const ret = await res.json();
        if (ret.code === 0) {
            toast("配置保存成功");
            await refreshAllConfig();
            return true;
        } else {
            toast(ret.msg, "err");
            return false;
        }
    } catch (e) {
        toast("保存请求异常：" + e, "err");
        return false;
    }
}

// 刷新全部面板
async function refreshAllConfig() {
    try {
        const res = await fetch(`${base}/config/all`);
        const data = await res.json();
        if (data.code === 0) {
            fullConfig = data.data;
            renderAllPanel();
        }
    } catch (e) {
        toast("刷新配置失败", "err");
    }
}

function renderAllPanel() {
    renderOneBot();
    renderLLMList();
    renderPersonaList();
    renderGroupList();
}

// 自动推断provider_type
function autoGetProvider(name) {
    if (name.startsWith("deepseek")) return "deepseek";
    if (name.startsWith("zhipu") || name === "glm") return "zhipu";
    if (name.startsWith("qwen")) return "qwen";
    return "";
}

// 下载文本文件通用工具
function downloadTextFile(text, filename) {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
}

// ====================== LLM厂商代码导出（核心需求4）======================
function exportLlmProviderCode() {
    const llms = fullConfig.llm_providers;
    if (Object.keys(llms).length === 0) {
        toast("暂无厂商配置，无法导出", "err");
        return;
    }
    let outputText = "# 自动生成provider模板，复制新建 xxx_provider.py\n\n";
    Object.entries(llms).forEach(([name, item]) => {
        const pType = item.provider_type ?? autoGetProvider(name);
        const className = pType.charAt(0).toUpperCase() + pType.slice(1) + "Provider";
        const template = `# ===== ${pType}_provider.py 模板 =====
import aiohttp
from llm.base import BaseLLMProvider

class ${className}(BaseLLMProvider):
    async def chat(self, system_prompt: str, context):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = [{"role": "system", "content": system_prompt}] + context
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": messages
        }
        url = f"{self.base_url}/chat/completions"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                res = await resp.json()
                if res.get("error"):
                    err_msg = res["error"]["message"]
                    raise Exception("接口异常:" + err_msg)
                return res["choices"][0]["message"]["content"].strip()

`;
        outputText += template;
    });
    downloadTextFile(outputText, "llm_provider模板.txt");
    toast("厂商Provider代码文本已下载");
}

// ====================== OneBot 模块 ======================
function renderOneBot() {
    const ob = fullConfig.onebot;
    document.getElementById("obHost").value = ob.listen_host ?? "";
    document.getElementById("obPort").value = ob.listen_port ?? 6199;
    document.getElementById("obToken").value = ob.token ?? "";
}

function checkListenHostValid(hostStr) {
    const ipReg = /^(localhost|0\.0\.0\.0|127(\.\d{1,3}){3}|10(\.\d{1,3}){3}|172\.(1[6-9]|2\d|3[01])(\.\d{1,3}){2}|192\.168(\.\d{1,3}){2})$/;
    const parts = hostStr.split(".");
    if (parts.length === 4) {
        for (let p of parts) {
            const num = parseInt(p, 10);
            if (isNaN(num) || num < 0 || num > 255) return false;
        }
    }
    return ipReg.test(hostStr);
}

async function saveOneBotConfig() {
    const hostVal = document.getElementById("obHost").value.trim();
    const portVal = Number(document.getElementById("obPort").value);
    const tokenVal = document.getElementById("obToken").value.trim();

    if (!hostVal) return toast("监听Host不能为空", "err");
    if (!checkListenHostValid(hostVal)) return toast("Host格式非法", "err");
    if (isNaN(portVal) || portVal < 1 || portVal > 65535) return toast("端口范围1~65535", "err");

    fullConfig.onebot.listen_host = hostVal;
    fullConfig.onebot.listen_port = portVal;
    fullConfig.onebot.token = tokenVal;
    await saveFullConfig();
}

// ====================== LLM 厂商 ======================
function openLlmModal() {
    currentEditLLM = "";
    editCachedProviderType = "";
    document.getElementById("llmModalTitle").innerText = "新增模型厂商";
    const nameInput = document.getElementById("llmName");
    nameInput.disabled = false;
    nameInput.value = "";
    // 新增：重置下拉
    document.getElementById("llmProviderType").value = "deepseek";
    document.getElementById("llmKey").value = "";
    document.getElementById("llmUrl").value = "";
    document.getElementById("llmModel").value = "";
    document.getElementById("llmTemp").value = 0.7;
    document.getElementById("llmMaxTok").value = 1024;
    openModal("llmModal");
}


function renderLLMList() {
    const wrap = document.getElementById("llmListWrap");
    const bindSelect = document.getElementById("groupBindLLM");
    wrap.innerHTML = "";
    bindSelect.innerHTML = `<option value="">请选择模型</option>`;
    const llms = fullConfig.llm_providers;

    Object.entries(llms).forEach(([name, item]) => {
        bindSelect.innerHTML += `<option value="${name}">${name}</option>`;
        const row = document.createElement("div");
        row.className = "item-row";
        row.innerHTML = `
            <span>${name} | 模型：${item.model}</span>
            <div class="item-actions">
                <button class="btn-blue">编辑</button>
                <button class="btn-red">删除</button>
            </div>`;

        row.querySelector(".btn-blue").onclick = () => {
            currentEditLLM = name;
            editCachedProviderType = item.provider_type ?? "";
            document.getElementById("llmModalTitle").innerText = "编辑模型厂商";
            const nameInput = document.getElementById("llmName");
            nameInput.value = name;
            nameInput.disabled = true;
            // 回填原有厂商类型
            document.getElementById("llmProviderType").value = editCachedProviderType;
            document.getElementById("llmKey").value = item.api_key;
            document.getElementById("llmUrl").value = item.base_url;
            document.getElementById("llmModel").value = item.model;
            document.getElementById("llmTemp").value = item.temperature;
            document.getElementById("llmMaxTok").value = item.max_tokens;
            openModal("llmModal");
        };


        row.querySelector(".btn-red").onclick = async () => {
            if (!confirm(`确认删除厂商【${name}】？`)) return;
            await fetch(`${base}/llm/del?name=${name}`, { method: "DELETE" });
            refreshAllConfig();
            toast("厂商已删除");
        };
        wrap.appendChild(row);
    });
}

async function testLLMConnect() {
    const key = document.getElementById("llmKey").value.trim();
    const url = document.getElementById("llmUrl").value.trim();
    const model = document.getElementById("llmModel").value.trim();
    if (!key || !url || !model) return toast("密钥/地址/模型不能为空", "err");
    const payload = {
        api_key: key, base_url: url, model,
        temperature: parseFloat(document.getElementById("llmTemp").value),
        max_tokens: parseInt(document.getElementById("llmMaxTok").value)
    };
    const res = await fetch(`${base}/llm/test_connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });
    const ret = await res.json();
    ret.code === 0 ? toast("接口连通正常") : toast(ret.msg, "err");
}

async function submitLlmForm() {
    const name = document.getElementById("llmName").value.trim();
    if (!name) return toast("厂商标识不能为空", "err");
    // 直接从下拉框读取provider_type，不再靠名称推断
    const provider_type = document.getElementById("llmProviderType").value;

    fullConfig.llm_providers[name] = {
        provider_type,
        api_key: document.getElementById("llmKey").value.trim(),
        base_url: document.getElementById("llmUrl").value.trim(),
        model: document.getElementById("llmModel").value.trim(),
        temperature: parseFloat(document.getElementById("llmTemp").value),
        max_tokens: parseInt(document.getElementById("llmMaxTok").value)
    };
    const ok = await saveFullConfig();
    if (ok) closeModal("llmModal");
}


// ====================== 人设模块 ======================
function openPersonaModal() {
    currentEditPersona = "";
    document.getElementById("personaModalTitle").innerText = "新增人设";
    document.getElementById("personaName").value = "";
    document.getElementById("personaPrompt").value = "";
    openModal("personaModal");
}

function renderPersonaList() {
    const wrap = document.getElementById("personaListWrap");
    const bindSelect = document.getElementById("groupBindPersona");
    wrap.innerHTML = "";
    bindSelect.innerHTML = `<option value="">请选择人设</option>`;
    const personas = fullConfig.personas;

    Object.entries(personas).forEach(([name, prompt]) => {
        bindSelect.innerHTML += `<option value="${name}">${name}</option>`;
        const row = document.createElement("div");
        row.className = "item-row";
        row.innerHTML = `
            <span>${name}</span>
            <div class="item-actions">
                <button class="btn-blue">编辑</button>
                <button class="btn-red">删除</button>
            </div>`;
        row.querySelector(".btn-blue").onclick = () => {
            currentEditPersona = name;
            document.getElementById("personaModalTitle").innerText = "编辑人设";
            document.getElementById("personaName").value = name;
            document.getElementById("personaPrompt").value = prompt;
            openModal("personaModal");
        };
        row.querySelector(".btn-red").onclick = async () => {
            if (!confirm(`删除人设【${name}】？`)) return;
            await fetch(`${base}/persona/del?name=${name}`, { method: "DELETE" });
            refreshAllConfig();
            toast("人设已删除");
        };
        wrap.appendChild(row);
    });
}

async function submitPersonaForm() {
    const name = document.getElementById("personaName").value.trim();
    const prompt = document.getElementById("personaPrompt").value.trim();
    if (!name) return toast("人设名称不能为空", "err");
    fullConfig.personas[name] = prompt;
    const ok = await saveFullConfig();
    if (ok) closeModal("personaModal");
}

// ====================== 群规则（需求3：展示随机概率+冷却） ======================
function openGroupModal() {
    currentEditGroupId = "";
    document.getElementById("groupModalTitle").innerText = "新增群配置";
    document.getElementById("editGroupId").value = "";
    document.getElementById("groupProb").value = 0.12;
    document.getElementById("groupCd").value = 120;
    document.getElementById("switchAtReply").checked = true;
    document.getElementById("switchRandomChat").checked = true;
    document.getElementById("groupCtxLen").value = 8;
    openModal("groupModal");
}

function renderGroupList() {
    const wrap = document.getElementById("groupListWrap");
    wrap.innerHTML = "";
    const groups = fullConfig.group_rules;
    Object.entries(groups).forEach(([gid, rule]) => {
        const row = document.createElement("div");
        row.className = "item-row";
        // 展示新增：随机概率、冷却秒数
        row.innerHTML = `
            <span>群${gid} | 模型：${rule.bind_llm} | 人设：${rule.bind_persona}
            <br>随机概率：${rule.random_prob ?? 0.12} ｜ 冷却：${rule.cooldown_sec ?? 120}秒</span>
            <div class="item-actions">
                <button class="btn-blue">编辑</button>
                <button class="btn-red">删除</button>
            </div>`;
        row.querySelector(".btn-blue").onclick = () => {
            currentEditGroupId = gid;
            document.getElementById("groupModalTitle").innerText = "编辑群配置";
            document.getElementById("editGroupId").value = gid;
            document.getElementById("groupBindLLM").value = rule.bind_llm ?? "";
            document.getElementById("groupBindPersona").value = rule.bind_persona ?? "";
            document.getElementById("groupProb").value = rule.random_prob ?? 0.12;
            document.getElementById("groupCd").value = rule.cooldown_sec ?? 120;
            document.getElementById("switchAtReply").checked = !!rule.enable_at_reply;
            document.getElementById("switchRandomChat").checked = !!rule.enable_random_chat;
            document.getElementById("groupCtxLen").value = rule.context_max_len ?? 8;
            openModal("groupModal");
        };
        row.querySelector(".btn-red").onclick = async () => {
            if (!confirm(`删除群【${gid}】配置？`)) return;
            await fetch(`${base}/group/del?gid=${gid}`);
            refreshAllConfig();
            toast("群配置已删除");
        };
        wrap.appendChild(row);
    });
}

async function submitGroupForm() {
    const gid = document.getElementById("editGroupId").value.trim();
    if (!gid) return toast("请填写群号", "err");
    fullConfig.group_rules[gid] = {
        bind_llm: document.getElementById("groupBindLLM").value,
        bind_persona: document.getElementById("groupBindPersona").value,
        random_prob: parseFloat(document.getElementById("groupProb").value),
        cooldown_sec: parseInt(document.getElementById("groupCd").value),
        enable_at_reply: document.getElementById("switchAtReply").checked,
        enable_random_chat: document.getElementById("switchRandomChat").checked,
        context_max_len: parseInt(document.getElementById("groupCtxLen").value)
    };
    const ok = await saveFullConfig();
    if (ok) closeModal("groupModal");
}

// ====================== 机器人启停 ======================
async function refreshBotStatus() {
    const res = await fetch(`${base}/bot/status`);
    const data = await res.json();
    const dom = document.getElementById("botStatus");
    if (data.code !== 0) return;
    const d = data.data;
    // 需求1：运行绿色加粗 / 停止黑色加粗
    dom.innerHTML = d.running
        ? `<span class="status-online">● 机器人运行中，NapCat连接数：${d.napcat_connected_count}</span>`
        : `<span class="status-offline">● 机器人未启动</span>`;
}

async function startBot() {
    const ret = await (await fetch(`${base}/bot/start`, { method: "POST" })).json();
    ret.code === 0 ? toast(ret.msg) : toast(ret.msg, "err");
    refreshBotStatus();
}

async function stopBot() {
    const ret = await (await fetch(`${base}/bot/stop`, { method: "POST" })).json();
    ret.code === 0 ? toast(ret.msg) : toast(ret.msg, "err");
    refreshBotStatus();
}

// ====================== 导入导出 ======================
async function exportAllConfig() {
    const ret = await fetch(`${base}/config/all`);
    const jsonData = await ret.json();
    const jsonStr = JSON.stringify(jsonData.data, null, 2);
    downloadTextFile(jsonStr, `minibot_config_${new Date().toISOString().slice(0, 10)}.json`);
    toast("配置导出成功");
}



// 页面初始化
window.onload = async () => {
    await refreshAllConfig();
    refreshBotStatus();
    setInterval(refreshBotStatus, 3000);
};
