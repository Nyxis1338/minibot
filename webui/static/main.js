const base = "/api";
let fullConfig = {};
let currentEditLLM = "";
let currentEditPersona = "";
let currentEditGroupId = "";
// 新增全局临时缓存：存放编辑条目自带的provider_type
let editCachedProviderType = "";
// Toast提示
function toast(msg, type="suc"){
    const box = document.getElementById("toastBox");
    const div = document.createElement("div");
    div.className = `toast ${type}`;
    div.innerText = msg;
    box.appendChild(div);
    setTimeout(()=>div.remove(), 3000);
}
// 弹窗通用开关
function openModal(domId){document.getElementById(domId).style.display="grid"}
function closeModal(domId){document.getElementById(domId).style.display="none"}
// 全局拉取配置并渲染全部面板
async function refreshAllConfig(){
    const res = await fetch(`${base}/config/all`);
    const data = await res.json();
    if(data.code === 0){
        fullConfig = data.data;
        renderAllPanel();
    }
}
function renderAllPanel(){
    renderOneBot();
    renderLLMList();
    renderPersonaList();
    renderGroupList();
}
// ========== OneBot 渲染与保存逻辑（新增） ==========
function renderOneBot(){
    const ob = fullConfig.onebot;
    document.getElementById("obHost").value = ob.listen_host;
    document.getElementById("obPort").value = ob.listen_port;
    document.getElementById("obToken").value = ob.token;
}
// IP格式校验
function checkListenHostValid(hostStr){
    const ipReg = /^(localhost|0\.0\.0\.0|127(\.\d{1,3}){3}|10(\.\d{1,3}){3}|172\.(1[6-9]|2\d|3[01])(\.\d{1,3}){2}|192\.168(\.\d{1,3}){2})$/;
    const parts = hostStr.split(".");
    if (parts.length === 4) {
        for(let p of parts){
            const num = parseInt(p,10);
            if(isNaN(num) || num <0 || num >255) return false;
        }
    }
    return ipReg.test(hostStr);
}
async function saveOneBotConfig(){
    const hostVal = document.getElementById("obHost").value.trim();
    const portVal = Number(document.getElementById("obPort").value);
    const tokenVal = document.getElementById("obToken").value.trim();
    if(!hostVal){
        toast("监听Host不能为空！", "err");
        return;
    }
    if(!checkListenHostValid(hostVal)){
        toast("Host格式非法，仅支持localhost/0.0.0.0/127.0.0.1/内网段", "err");
        return;
    }
    if(isNaN(portVal) || portVal <1 || portVal>65535){
        toast("端口范围必须1~65535", "err");
        return;
    }
    // 更新内存配置
    fullConfig.onebot.listen_host = hostVal;
    fullConfig.onebot.listen_port = portVal;
    fullConfig.onebot.token = tokenVal;
    // 提交后端持久化写入config.json
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
// ========== 大模型厂商 ==========
function openLlmModal(){
    currentEditLLM = "";
    editCachedProviderType = "";
    document.getElementById("llmModalTitle").innerText="新增模型厂商";
    // 新增：标识框可编辑
    const nameInput = document.getElementById("llmName");
    nameInput.disabled = false;
    nameInput.value="";
    document.getElementById("llmKey").value="";
    document.getElementById("llmUrl").value="";
    document.getElementById("llmModel").value="";
    document.getElementById("llmTemp").value=0.7;
    document.getElementById("llmMaxTok").value=1024;
    openModal("llmModal");
}
function renderLLMList(){
    const wrap=document.getElementById("llmListWrap");
    wrap.innerHTML="";
    const llms=fullConfig.llm_providers;
    const bindSelect=document.getElementById("groupBindLLM");
    bindSelect.innerHTML=`<option value="">请选择模型</option>`;
    Object.entries(llms).forEach(([name,item])=>{
        bindSelect.innerHTML += `<option value="${name}">${name}</option>`;
        const row=document.createElement("div");
        row.className="item-row";
        row.innerHTML = `
            <span>${name} | 模型：${item.model}</span>
            <div class="item-actions">
                <button class="btn-blue">编辑</button>
                <button class="btn-red">删除</button>
            </div>`;
        row.querySelector(".btn-blue").onclick=()=>{
            currentEditLLM=name;
            // 修复：不存在provider_type则自动推断，杜绝undefined
            if("provider_type" in item){
                editCachedProviderType = item.provider_type;
            }else{
                if(name.startsWith("deepseek")) editCachedProviderType = "deepseek";
                else if(name.startsWith("zhipu") || name==="glm") editCachedProviderType = "zhipu";
                else if(name.startsWith("qwen")) editCachedProviderType = "qwen";
                else editCachedProviderType = "";
            }
            document.getElementById("llmModalTitle").innerText="编辑模型厂商";
            const nameInput = document.getElementById("llmName");
            nameInput.value=name;
            nameInput.disabled = true;
            document.getElementById("llmKey").value=item.api_key;
            document.getElementById("llmUrl").value=item.base_url;
            document.getElementById("llmModel").value=item.model;
            document.getElementById("llmTemp").value=item.temperature;
            document.getElementById("llmMaxTok").value=item.max_tokens;
            openModal("llmModal");
        }

        row.querySelector(".btn-red").onclick=async ()=>{
            if(!confirm(`确认删除厂商【${name}】？`))return;
            await fetch(`${base}/llm/del?name=${name}`,{method:"DELETE"});
            toast("厂商已删除");
            refreshAllConfig();
        }
        wrap.appendChild(row);
    })
}
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
    const testData = {api_key:key,base_url:url,model:model,temperature:temp,max_tokens:maxTok};
    try{
        const res = await fetch(`${base}/llm/test_connect`, {
            method: "POST",headers: {"Content-Type":"application/json"},body: JSON.stringify(testData)
        });
        const ret = await res.json();
        ret.code===0 ? toast("✅ 接口连通测试成功") : toast(`❌ ${ret.msg}`,"err");
    }catch(err){toast("❌ 网络请求异常","err");}
}
async function submitLlmForm(){
    const name=document.getElementById("llmName").value.trim();
    if(!name){toast("厂商标识不能为空","err");return;}
    let provider_type;
    if(currentEditLLM !== ""){
        provider_type = editCachedProviderType;
        // 兜底：缓存为空重新推断
        if(!provider_type){
            if(name.startsWith("deepseek")) provider_type = "deepseek";
            else if(name.startsWith("zhipu") || name==="glm") provider_type = "zhipu";
            else if(name.startsWith("qwen")) provider_type = "qwen";
            else {
                toast("无法自动匹配厂商类型，请修改名称","err");
                return;
            }
        }
    }else{
        if(name.startsWith("deepseek")) provider_type = "deepseek";
        else if(name.startsWith("zhipu") || name==="glm") provider_type = "zhipu";
        else if(name.startsWith("qwen")) provider_type = "qwen";
        else {
            toast("新增的厂商标识无法自动匹配provider_type，请调整命名", "err");
            return;
        }
    }
    const payload={
        provider_type: provider_type,
        api_key: document.getElementById("llmKey").value.trim(),
        base_url: document.getElementById("llmUrl").value.trim(),
        model: document.getElementById("llmModel").value.trim(),
        temperature: parseFloat(document.getElementById("llmTemp").value),
        max_tokens: parseInt(document.getElementById("llmMaxTok").value)
    };
    const res=await fetch(`${base}/llm/save?name=${name}`,{
        method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)
    });
    const ret=await res.json();
    if(ret.code===0){
        toast("模型配置保存成功");
        closeModal("llmModal");
        refreshAllConfig();
    }else toast(ret.msg,"err");
}

// ========== 人设 ==========
function openPersonaModal(){
    currentEditPersona="";
    document.getElementById("personaModalTitle").innerText="新增人设";
    document.getElementById("personaName").value="";
    document.getElementById("personaPrompt").value="";
    openModal("personaModal");
}
function renderPersonaList(){
    const wrap=document.getElementById("personaListWrap");
    wrap.innerHTML="";
    const personas=fullConfig.personas;
    const bindSelect=document.getElementById("groupBindPersona");
    bindSelect.innerHTML=`<option value="">请选择人设</option>`;
    Object.entries(personas).forEach(([name,prompt])=>{
        bindSelect.innerHTML += `<option value="${name}">${name}</option>`;
        const row=document.createElement("div");
        row.className="item-row";
        row.innerHTML = `
            <span>${name}</span>
            <div class="item-actions">
                <button class="btn-blue">编辑</button>
                <button class="btn-red">删除</button>
            </div>`;
        row.querySelector(".btn-blue").onclick=()=>{
            currentEditPersona=name;
            document.getElementById("personaModalTitle").innerText="编辑人设";
            document.getElementById("personaName").value=name;
            document.getElementById("personaPrompt").value=prompt;
            openModal("personaModal");
        }
        row.querySelector(".btn-red").onclick=async ()=>{
            if(!confirm(`确认删除人设【${name}】？`))return;
            await fetch(`${base}/persona/del?name=${name}`,{method:"DELETE"});
            toast("人设已删除");
            refreshAllConfig();
        }
        wrap.appendChild(row);
    })
}
async function submitPersonaForm(){
    const name=document.getElementById("personaName").value.trim();
    const prompt=document.getElementById("personaPrompt").value.trim();
    if(!name){toast("人设名称不能为空","err");return;}
    const payload={name,prompt};
    const res=await fetch(`${base}/persona/save`,{
        method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)
    });
    const ret=await res.json();
    if(ret.code===0){
        toast("人设保存成功");
        closeModal("personaModal");
        refreshAllConfig();
    }else toast(ret.msg,"err");
}
// ========== QQ群配置 ==========
function openGroupModal(){
    currentEditGroupId="";
    document.getElementById("groupModalTitle").innerText="新增群配置";
    document.getElementById("editGroupId").value="";
    document.getElementById("groupProb").value=0.12;
    document.getElementById("groupCd").value=120;
    document.getElementById("switchAtReply").checked=true;
    document.getElementById("switchRandomChat").checked=true;
    document.getElementById("groupCtxLen").value=8;
    openModal("groupModal");
}
function renderGroupList(){
    const wrap=document.getElementById("groupListWrap");
    wrap.innerHTML="";
    const groups=fullConfig.group_rules;
    Object.entries(groups).forEach(([gid,rule])=>{
        const row=document.createElement("div");
        row.className="item-row";
        row.innerHTML = `
            <span>群${gid} | 模型：${rule.bind_llm} | 人设：${rule.bind_persona}</span>
            <div class="item-actions">
                <button class="btn-blue">编辑</button>
                <button class="btn-red">删除</button>
            </div>`;
        row.querySelector(".btn-blue").onclick=()=>{
            currentEditGroupId=gid;
            document.getElementById("groupModalTitle").innerText="编辑群配置";
            document.getElementById("editGroupId").value=gid;
            document.getElementById("groupBindLLM").value=rule.bind_llm;
            document.getElementById("groupBindPersona").value=rule.bind_persona;
            document.getElementById("groupProb").value=rule.random_prob;
            document.getElementById("groupCd").value=rule.cooldown_sec;
            document.getElementById("switchAtReply").checked=rule.enable_at_reply;
            document.getElementById("switchRandomChat").checked=rule.enable_random_chat;
            document.getElementById("groupCtxLen").value=rule.context_max_len;
            openModal("groupModal");
        }
        row.querySelector(".btn-red").onclick=async ()=>{
            if(!confirm(`确认删除群【${gid}】配置？`))return;
            await fetch(`${base}/group/del?gid=${gid}`,{method:"DELETE"});
            toast("群配置已删除");
            refreshAllConfig();
        }
        wrap.appendChild(row);
    })
}
async function submitGroupForm(){
    const gid=document.getElementById("editGroupId").value.trim();
    if(!gid){toast("请填写群号","err");return;}
    const payload={
        bind_llm: document.getElementById("groupBindLLM").value,
        bind_persona: document.getElementById("groupBindPersona").value,
        random_prob: parseFloat(document.getElementById("groupProb").value),
        cooldown_sec: parseInt(document.getElementById("groupCd").value),
        enable_at_reply: document.getElementById("switchAtReply").checked,
        enable_random_chat: document.getElementById("switchRandomChat").checked,
        context_max_len: parseInt(document.getElementById("groupCtxLen").value)
    };
    const res=await fetch(`${base}/group/save?gid=${gid}`,{
        method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)
    });
    const ret=await res.json();
    if(ret.code === 0){
        toast("群配置保存成功");
        closeModal("groupModal");
        refreshAllConfig();
    }else toast(ret.msg,"err");
}
// ========== 机器人启停 ==========
async function refreshBotStatus(){
    const res = await fetch(`${base}/bot/status`);
    const data = await res.json();
    const dom = document.getElementById("botStatus");
    if(data.code !==0) return;
    const d = data.data;
    d.running ? dom.innerHTML=`<span style="color:#0ea863">● 机器人运行中，NapCat在线连接数：${d.napcat_connected_count}</span>`
    : dom.innerHTML=`<span style="color:#e04343">● 机器人已停止，未监听WS端口</span>`;
}
async function startBot(){
    const ret=await (await fetch(`${base}/bot/start`,{method:"POST"})).json();
    ret.code===0 ? toast(ret.msg) : toast(ret.msg,"err");
    refreshBotStatus();
}
async function stopBot(){
    const ret=await (await fetch(`${base}/bot/stop`,{method:"POST"})).json();
    ret.code===0 ? toast(ret.msg) : toast(ret.msg,"err");
    refreshBotStatus();
}
// ========== 配置导入导出 ==========
async function exportAllConfig(){
    try{
        const ret=await (await fetch(`${base}/config/all`)).json();
        if(ret.code !== 0){toast("获取配置失败："+ret.msg,"err");return;}
        const jsonStr = JSON.stringify(ret.data, null, 2);
        const blob = new Blob([jsonStr], {type:"application/json;charset=utf-8"});
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        const date = new Date().toISOString().slice(0,10);
        a.href = url;a.download = `minibot_config_backup_${date}.json`;
        document.body.appendChild(a);a.click();
        document.body.removeChild(a);URL.revokeObjectURL(url);
        toast("配置备份导出成功！");
    }catch(e){toast("导出异常："+String(e),"err");}
}
async function importConfigFile(){
    const fileDom = document.getElementById("importConfigFile");
    const file = fileDom.files[0];
    if(!file) return;
    try{
        const cfgData = JSON.parse(await file.text());
        const ret=await (await fetch(`${base}/config/save`,{
            method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(cfgData)
        })).json();
        if(ret.code === 0){
            toast("导入成功，自动刷新页面");
            await refreshAllConfig();
        }else toast(ret.msg,"err");
    }catch(err){toast("JSON文件格式错误","err");}
    fileDom.value = "";
}
// 页面加载初始化
window.onload = async ()=>{
    await refreshAllConfig();
    refreshBotStatus();
    setInterval(refreshBotStatus, 3000);
}
