const base = "/api";
let fullConfig = {};
let currentEditLLM = "";
let currentEditPersona = "";
let currentEditGroupId = "";

// ====================== 配置路径常量统一管理 ======================
const CONFIG_PATH = {
    onebot: "onebot",
    llm: "llm_providers",
    persona: "personas",
    group: "group_rules"
};

// ====================== 表单ID <-> 配置路径映射表 ======================
// OneBot 单对象表单映射
const formKeyMap = {
    obHost: "onebot.listen_host",
    obPort: "onebot.listen_port",
    obToken: "onebot.token"
};
// LLM弹窗输入框映射 domId -> dataKey
const llmFieldMap = {
    llmName: "key",
    llmProviderType: "provider_type",
    llmKey: "api_key",
    llmUrl: "base_url",
    llmModel: "model",
    llmTemp: "temperature",
    llmMaxTok: "max_tokens"
};
// 人设弹窗映射
const personaFieldMap = {
    personaName: "key",
    personaPrompt: "prompt"
};
// 群配置弹窗映射
const groupFieldMap = {
    editGroupId: "key",
    groupBindLLM: "bind_llm",
    groupBindPersona: "bind_persona",
    groupProb: "random_prob",
    groupCd: "cooldown_sec",
    switchAtReply: "enable_at_reply",
    switchRandomChat: "enable_random_chat",
    groupCtxLen: "context_max_len"
};

// ====================== 基础公共工具 ======================
function toast(msg, type = "suc") {
    const box = document.getElementById("toastBox");
    const div = document.createElement("div");
    div.className = `p-3 rounded-lg mb-2 text-white shadow-lg ${type === "suc" ? "bg-green-500" : "bg-red-500"}`;
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
// 根据路径读取对象值
function getObjByPath(obj, path) {
    return path.split(".").reduce((o, k) => o?.[k], obj);
}
// 根据路径写入对象值
function setObjByPath(obj, path, val) {
    const keys = path.split(".");
    const last = keys.pop();
    const target = keys.reduce((o, k) => {
        if (!o[k]) o[k] = {};
        return o[k];
    }, obj);
    target[last] = val;
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

// ====================== 单对象表单通用读写（OneBot专用） ======================
// 配置回填表单
function bindFormToConfig() {
    Object.entries(formKeyMap).forEach(([domId, cfgPath]) => {
        const el = document.getElementById(domId);
        if (!el) return;
        const val = getObjByPath(fullConfig, cfgPath);
        if (el.type === "checkbox") el.checked = !!val;
        else el.value = val ?? "";
    });
}
// 表单写入配置
function collectFormToConfig() {
    Object.entries(formKeyMap).forEach(([domId, cfgPath]) => {
        const el = document.getElementById(domId);
        if (!el) return;
        let val;
        if (el.type === "checkbox") val = el.checked;
        else if (el.type === "number") val = Number(el.value.trim());
        else val = el.value.trim();
        setObjByPath(fullConfig, cfgPath, val);
    });
}

// ====================== 字典集合通用CRUD工具（LLM/人设/群共用） ======================
/**
 * 弹窗批量收集表单数据
 * @param {Object} fieldMap domId -> dataKey
 * @returns {Object} 表单数据对象
 */
function collectModalForm(fieldMap) {
    const data = {};
    Object.entries(fieldMap).forEach(([domId, dataKey]) => {
        const el = document.getElementById(domId);
        if (!el) return;
        let val;
        if (el.type === "checkbox") val = el.checked;
        else if (el.type === "number") val = Number(el.value.trim());
        else val = el.value.trim();
        data[dataKey] = val;
    });
    return data;
}
/**
 * 通用渲染字典列表
 * @param {string} cfgPath 配置路径
 * @param {string} wrapId 列表容器ID
 * @param {string|null} bindSelectId 绑定下拉框ID
 * @param {Function} renderRowHtml 单行模板回调
 * @param {Function} openEditModal 编辑弹窗回调
 */
function renderDictList(cfgPath, wrapId, bindSelectId, renderRowHtml, openEditModal) {
    const wrap = document.getElementById(wrapId);
    wrap.innerHTML = "";
    const dict = getObjByPath(fullConfig, cfgPath) || {};

    // 同步渲染绑定下拉选择框
    if (bindSelectId) {
        const sel = document.getElementById(bindSelectId);
        sel.innerHTML = `<option value="">请选择</option>`;
        Object.keys(dict).forEach(k => sel.innerHTML += `<option value="${k}">${k}</option>`);
    }

    Object.entries(dict).forEach(([key, item]) => {
        const row = document.createElement("div");
        row.className = "flex justify-between items-center flex-wrap gap-2 p-3 border border-slate-200 rounded-lg my-2 bg-slate-50";
        row.innerHTML = renderRowHtml(key, item);

        row.querySelector(".bg-blue-500").onclick = () => openEditModal(key, item);
        row.querySelector(".bg-red-500").onclick = async () => {
            if (!confirm(`确认删除【${key}】？`)) return;
            const targetDict = getObjByPath(fullConfig, cfgPath);
            delete targetDict[key];
            await saveFullConfig();
            refreshAllConfig();
            toast("删除成功");
        };
        wrap.appendChild(row);
    });
}
/**
 * 通用保存字典项（新增/编辑统一逻辑）
 * @param {string} cfgPath 配置路径
 * @param {string} editKey 当前编辑key，空则新增
 * @param {Object} data 表单收集数据
 * @param {string} modalId 弹窗ID
 */
async function submitDictItem(cfgPath, editKey, data, modalId) {
    const targetDict = getObjByPath(fullConfig, cfgPath);
    const realKey = editKey || data.key;
    if (!realKey) return toast("标识不能为空", "err");
    const saveData = { ...data };
    delete saveData.key;
    targetDict[realKey] = saveData;
    const ok = await saveFullConfig();
    if (ok) closeModal(modalId);
}

// ====================== 全局配置刷新/保存 ======================
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
    bindFormToConfig();
    renderLLMList();
    renderPersonaList();
    renderGroupList();
}

// ====================== OneBot 配置模块 ======================
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
    if (!hostVal) return toast("监听Host不能为空", "err");
    if (!checkListenHostValid(hostVal)) return toast("Host格式非法", "err");
    if (isNaN(portVal) || portVal < 1 || portVal > 65535) return toast("端口范围1~65535", "err");
    collectFormToConfig();
    await saveFullConfig();
}

// ====================== LLM厂商模块（通用化极简） ======================
function openLlmModal(editKey = "", editItem = null) {
    currentEditLLM = editKey;
    document.getElementById("llmModalTitle").innerText = editKey ? "编辑模型厂商" : "新增模型厂商";
    const nameInput = document.getElementById("llmName");
    nameInput.value = "";
    nameInput.disabled = !!editKey;
    document.getElementById("llmProviderType").value = "deepseek";
    document.getElementById("llmKey").value = "";
    document.getElementById("llmUrl").value = "";
    document.getElementById("llmModel").value = "";
    document.getElementById("llmTemp").value = 0.7;
    document.getElementById("llmMaxTok").value = 1024;

    if (editItem) {
        nameInput.value = editKey;
        document.getElementById("llmProviderType").value = editItem.provider_type;
        document.getElementById("llmKey").value = editItem.api_key;
        document.getElementById("llmUrl").value = editItem.base_url;
        document.getElementById("llmModel").value = editItem.model;
        document.getElementById("llmTemp").value = editItem.temperature;
        document.getElementById("llmMaxTok").value = editItem.max_tokens;
    }
    openModal("llmModal");
}
function renderLLMList() {
    renderDictList(
        CONFIG_PATH.llm,
        "llmListWrap",
        "groupBindLLM",
        (k, item) => `
            <span class="flex-1 min-w-[300px]">${k} | 模型：${item.model}</span>
            <div class="flex gap-1.5">
                <button class="bg-blue-500 text-white px-2 py-1 rounded text-sm">编辑</button>
                <button class="bg-red-500 text-white px-2 py-1 rounded text-sm">删除</button>
            </div>`,
        (k, item) => openLlmModal(k, item)
    );
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
    const data = collectModalForm(llmFieldMap);
    if (!data.key) return toast("厂商标识不能为空", "err");
    await submitDictItem(CONFIG_PATH.llm, currentEditLLM, data, "llmModal");
}
// LLM Provider代码导出
function exportLlmProviderCode() {
    const llms = getObjByPath(fullConfig, CONFIG_PATH.llm);
    if (Object.keys(llms).length === 0) {
        toast("暂无厂商配置，无法导出", "err");
        return;
    }
    let outputText = "# 自动生成provider模板，复制新建 xxx_provider.py\n\n";
    Object.entries(llms).forEach(([name, item]) => {
        const pType = item.provider_type;
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

// ====================== 人设模块 ======================
function openPersonaModal(editKey = "", editItem = null) {
    currentEditPersona = editKey;
    document.getElementById("personaModalTitle").innerText = editKey ? "编辑人设" : "新增人设";
    document.getElementById("personaName").value = "";
    document.getElementById("personaPrompt").value = "";
    if (editItem) {
        document.getElementById("personaName").value = editKey;
        document.getElementById("personaPrompt").value = editItem.prompt;
    }
    openModal("personaModal");
}
function renderPersonaList() {
    renderDictList(
        CONFIG_PATH.persona,
        "personaListWrap",
        "groupBindPersona",
        (k) => `
            <span class="flex-1 min-w-[300px]">${k}</span>
            <div class="flex gap-1.5">
                <button class="bg-blue-500 text-white px-2 py-1 rounded text-sm">编辑</button>
                <button class="bg-red-500 text-white px-2 py-1 rounded text-sm">删除</button>
            </div>`,
        (k, item) => openPersonaModal(k, item)
    );
}
async function submitPersonaForm() {
    const data = collectModalForm(personaFieldMap);
    if (!data.key) return toast("人设名称不能为空", "err");
    await submitDictItem(CONFIG_PATH.persona, currentEditPersona, data, "personaModal");
}

// ====================== 群配置模块 ======================
function openGroupModal(editKey = "", editItem = null) {
    currentEditGroupId = editKey;
    document.getElementById("groupModalTitle").innerText = editKey ? "编辑群配置" : "新增群配置";
    document.getElementById("editGroupId").value = "";
    document.getElementById("groupProb").value = 0.12;
    document.getElementById("groupCd").value = 120;
    document.getElementById("switchAtReply").checked = true;
    document.getElementById("switchRandomChat").checked = true;
    document.getElementById("groupCtxLen").value = 8;

    if (editItem) {
        document.getElementById("editGroupId").value = editKey;
        document.getElementById("groupBindLLM").value = editItem.bind_llm || "";
        document.getElementById("groupBindPersona").value = editItem.bind_persona || "";
        document.getElementById("groupProb").value = editItem.random_prob ?? 0.12;
        document.getElementById("groupCd").value = editItem.cooldown_sec ?? 120;
        document.getElementById("switchAtReply").checked = !!editItem.enable_at_reply;
        document.getElementById("switchRandomChat").checked = !!editItem.enable_random_chat;
        document.getElementById("groupCtxLen").value = editItem.context_max_len ?? 8;
    }
    openModal("groupModal");
}
function renderGroupList() {
    renderDictList(
        CONFIG_PATH.group,
        "groupListWrap",
        null,
        (k, item) => `
            <span class="flex-1 min-w-[300px]">群${k} | 模型：${item.bind_llm} | 人设：${item.bind_persona}
            <br>随机概率：${item.random_prob ?? 0.12} ｜ 冷却：${item.cooldown_sec ?? 120}秒</span>
            <div class="flex gap-1.5">
                <button class="bg-blue-500 text-white px-2 py-1 rounded text-sm">编辑</button>
                <button class="bg-red-500 text-white px-2 py-1 rounded text-sm">删除</button>
            </div>`,
        (k, item) => openGroupModal(k, item)
    );
}
async function submitGroupForm() {
    const data = collectModalForm(groupFieldMap);
    if (!data.key) return toast("请填写群号", "err");
    await submitDictItem(CONFIG_PATH.group, currentEditGroupId, data, "groupModal");
}

// ====================== 机器人启停 & 状态 ======================
async function refreshBotStatus() {
    const res = await fetch(`${base}/bot/status`);
    const data = await res.json();
    const dom = document.getElementById("botStatus");
    if (data.code !== 0) return;
    const d = data.data;
    dom.innerHTML = d.running
        ? `<span class="text-green-500 font-bold text-base">● 机器人运行中，NapCat/Lagrange连接数：${d.napcat_connected_count}</span>`
        : `<span class="text-gray-900 font-bold text-base">● 机器人未启动</span>`;
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

// ====================== 配置导出 ======================
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
