const base = "/api";
let fullConfig = {};
let currentEditLLM = "";
let currentEditPersona = "";
let currentEditGroupId = "";

// Toast提示
function toast(msg, type="suc"){
    const box = document.getElementById("toastBox");
    const div = document.createElement("div");
    div.className = `toast ${type}`;
    div.innerText = msg;
    box.appendChild(div);
    setTimeout(()=>div.remove(), 3000);
}

// 全局刷新全部配置
async function refreshAllConfig(){
    const res = await fetch(`${base}/config/all`);
    const data = await res.json();
    if(data.code === 0){
        fullConfig = data.data;
        renderAllPanel();
    }
}

// 一次性渲染全部面板
function renderAllPanel(){
    renderOneBot();
    renderLLMList();
    renderPersonaList();
    renderGroupList();
}

// ========== OneBot 配置渲染与保存 ==========
function renderOneBot(){
    const ob = fullConfig.onebot;
    document.getElementById("obHost").value = ob.listen_host;
    document.getElementById("obPort").value = ob.listen_port;
    document.getElementById("obToken").value = ob.token;
}

// Host IP格式校验
function checkListenHostValid(hostStr){
    const ipReg = /^(localhost|0\.0\.0\.0|127(\.\d{1,3}){3}|10(\.\d{1,3}){3}|172\.(1[6-9]|2\d|3[01])(\.\d{1,3}){2}|192\.168(\.\d{1,3}){2})$/;
    const parts = hostStr.split(".");
    if (parts.length === 4) {
        for(let p of parts){
            const num = parseInt(p,10);
            if(isNaN(num) || num <0 || num >255){
                return false;
            }
        }
    }
    return ipReg.test(hostStr);
}

async function saveOneBot(){
    const hostVal = document.getElementById("obHost").value.trim();
    const portVal = Number(document.getElementById("obPort").value);
    const tokenVal = document.getElementById("obToken").value.trim();

    if(!hostVal){
        toast("监听Host不能为空！", "err");
        return;
    }
    if(!checkListenHostValid(hostVal)){
        toast("Host格式非法！仅允许 localhost / 0.0.0.0 / 127.0.0.1 / 10/172/192内网段IP", "err");
        return;
    }
    if(isNaN(portVal) || portVal <1 || portVal>65535){
        toast("端口必须是1~65535数字", "err");
        return;
    }

    fullConfig.onebot.listen_host = hostVal;
    fullConfig.onebot.listen_port = portVal;
    fullConfig.onebot.token = tokenVal;

    const res = await fetch(`${base}/config/save`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(fullConfig)
    });
    const ret = await res.json();
    if(ret.code ===0){
        toast("OneBot配置保存成功，重启机器人生效");
    }else{
        toast(ret.msg, "err");
    }
}

// ========== LLM模型列表渲染 ==========
function renderLLMList(){
    const box = document.getElementById("llmListBox");
    box.innerHTML = "";
    const llms = fullConfig.llm_providers;
    const sel = document.getElementById("groupBindLLM");
    sel.innerHTML = "<option value=''>请选择模型</option>";

    for(const name in llms){
        const item = llms[name];
        const div = document.createElement("div");
        div.style="padding:6px 8px;border:1px solid #eee;margin:4px 0;border-radius:4px;cursor:pointer";
        div.innerText = name;
        div.onclick = ()=>{
            currentEditLLM = name;
            document.getElementById("llmName").value = name;
            document.getElementById("llmKey").value = item.api_key;
            document.getElementById("llmUrl").value = item.base_url;
            document.getElementById("llmModel").value = item.model;
            document.getElementById("llmTemp").value = item.temperature;
            document.getElementById("llmMaxTok").value = item.max_tokens;
        };
        box.appendChild(div);
        sel.innerHTML += `<option value="${name}">${name}</option>`;
    }
}

// LLM连通测试（区分402欠费、401密钥错误）
async function testLLMConnect(){
    const key = document.getElementById("llmKey").value.trim();
    const url = document.getElementById("llmUrl").value.trim();
    const model = document.getElementById("llmModel").value.trim();
    const temp = parseFloat(document.getElementById("llmTemp").value);
    const maxTok = parseInt(document.getElementById("llmMaxTok").value);
    if(!key || !url || !model){
        toast("API Key、接口地址、模型名称不能为空！", "err");
        return;
    }
    const testData = {
        api_key: key,
        base_url: url,
        model: model,
        temperature: temp,
        max_tokens: maxTok
    };
    try{
        const res = await fetch(`${base}/llm/test_connect`, {
            method: "POST",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify(testData)
        });
        const ret = await res.json();
        if(ret.code ===0){
            toast("✅ 接口连通测试成功，模型正常可用！", "suc");
        }else{
            toast(`❌ ${ret.msg}`, "err");
        }
    }catch(err){
        toast("❌ 网络请求异常，无法连接后端", "err");
    }
}

async function saveLLM(){
    const name = document.getElementById("llmName").value.trim();
    if(!name){toast("厂商标识不能为空", "err");return;}
    const payload = {
        api_key: document.getElementById("llmKey").value.trim(),
        base_url: document.getElementById("llmUrl").value.trim(),
        model: document.getElementById("llmModel").value.trim(),
        temperature: parseFloat(document.getElementById("llmTemp").value),
        max_tokens: parseInt(document.getElementById("llmMaxTok").value)
    };
    const res = await fetch(`${base}/llm/save?name=${name}`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(payload)
    });
    const ret = await res.json();
    if(ret.code ===0){
        toast("模型保存成功");
        refreshAllConfig();
    }else{
        toast(ret.msg, "err");
    }
}

async function delLLM(){
    if(!currentEditLLM){toast("请先选中一个厂商", "err");return;}
    const res = await fetch(`${base}/llm/del?name=${currentEditLLM}`, {method:"DELETE"});
    await res.json();
    toast("厂商已删除");
    refreshAllConfig();
}

// ========== 人设管理 ==========
function renderPersonaList(){
    const box = document.getElementById("personaListBox");
    box.innerHTML = "";
    const pers = fullConfig.personas;
    const sel = document.getElementById("groupBindPersona");
    sel.innerHTML = "<option value=''>请选择人设</option>";

    for(const name in pers){
        const div = document.createElement("div");
        div.style="padding:6px 8px;border:1px solid #eee;margin:4px 0;border-radius:4px;cursor:pointer";
        div.innerText = name;
        div.onclick = ()=>{
            currentEditPersona = name;
            document.getElementById("personaName").value = name;
            document.getElementById("personaPrompt").value = pers[name];
        };
        box.appendChild(div);
        sel.innerHTML += `<option value="${name}">${name}</option>`;
    }
}

async function savePersona(){
    const name = document.getElementById("personaName").value.trim();
    const prompt = document.getElementById("personaPrompt").value.trim();
    if(!name){toast("人设名称不能为空", "err");return;}
    const payload = {name, prompt};
    const res = await fetch(`${base}/persona/save`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(payload)
    });
    const ret = await res.json();
    if(ret.code ===0){
        toast("人设保存成功");
        refreshAllConfig();
    }else{
        toast(ret.msg, "err");
    }
}

async function delPersona(){
    if(!currentEditPersona){toast("请先选中人设", "err");return;}
    const res = await fetch(`${base}/persona/del?name=${currentEditPersona}`, {method:"DELETE"});
    await res.json();
    toast("人设已删除");
    refreshAllConfig();
}

// ========== 群配置渲染（双开关+上下文） ==========
function renderGroupList(){
    const box = document.getElementById("groupListBox");
    box.innerHTML = "";
    const groups = fullConfig.group_rules;
    for(const gid in groups){
        const div = document.createElement("div");
        div.style="padding:6px 8px;border:1px solid #eee;margin:4px 0;border-radius:4px;cursor:pointer";
        div.innerText = `群${gid}`;
        div.onclick = ()=>renderGroupForm(gid);
        box.appendChild(div);
    }
}

function renderGroupForm(gid){
    currentEditGroupId = gid;
    const rule = fullConfig.group_rules[gid];
    document.getElementById("groupBindLLM").value = rule.bind_llm;
    document.getElementById("groupBindPersona").value = rule.bind_persona;
    document.getElementById("groupProb").value = rule.random_prob;
    document.getElementById("groupCd").value = rule.cooldown_sec;
    document.getElementById("switchAtReply").checked = rule.enable_at_reply;
    document.getElementById("switchRandomChat").checked = rule.enable_random_chat;
    document.getElementById("groupCtxLen").value = rule.context_max_len;
    document.getElementById("editGroupId").value = gid;
}

async function saveGroupRule(){
    const gid = document.getElementById("editGroupId").value.trim();
    if(!gid){toast("请填写群号", "err");return;}
    const payload = {
        bind_llm: document.getElementById("groupBindLLM").value,
        bind_persona: document.getElementById("groupBindPersona").value,
        random_prob: parseFloat(document.getElementById("groupProb").value),
        cooldown_sec: parseInt(document.getElementById("groupCd").value),
        enable_at_reply: document.getElementById("switchAtReply").checked,
        enable_random_chat: document.getElementById("switchRandomChat").checked,
        context_max_len: parseInt(document.getElementById("groupCtxLen").value)
    };
    const res = await fetch(`${base}/group/save?gid=${gid}`,{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(payload)
    });
    const data = await res.json();
    if(data.code === 0){
        toast("群配置保存成功");
        refreshAllConfig();
    }else{
        toast(data.msg, "err");
    }
}

async function delGroupRule(){
    const gid = document.getElementById("editGroupId").value.trim();
    if(!gid){toast("请选择群", "err");return;}
    const res = await fetch(`${base}/group/del?gid=${gid}`, {method:"DELETE"});
    await res.json();
    toast("群配置已删除");
    refreshAllConfig();
}

// ========== 机器人启停 ==========
async function refreshBotStatus(){
    const res = await fetch(`${base}/bot/status`);
    const data = await res.json();
    const dom = document.getElementById("botStatus");
    if(data.code !==0) return;
    const d = data.data;
    if(d.running){
        dom.innerHTML = `<span style="color:#0ea863">● 机器人运行中，NapCat在线连接数：${d.napcat_connected_count}</span>`;
    }else{
        dom.innerHTML = `<span style="color:#e04343">● 机器人已停止，未监听WS端口</span>`;
    }
}

async function startBot(){
    const res = await fetch(`${base}/bot/start`, {method:"POST"});
    const ret = await res.json();
    if(ret.code ===0){
        toast(ret.msg, "suc");
    }else{
        toast(ret.msg, "err");
    }
    refreshBotStatus();
}

async function stopBot(){
    const res = await fetch(`${base}/bot/stop`, {method:"POST"});
    const ret = await res.json();
    if(ret.code ===0){
        toast(ret.msg, "suc");
    }else{
        toast(ret.msg, "err");
    }
    refreshBotStatus();
}

// 页面加载自动初始化
window.onload = async ()=>{
    await refreshAllConfig();
    refreshBotStatus();
    setInterval(refreshBotStatus, 3000);
}
