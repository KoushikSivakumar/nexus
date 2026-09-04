// At the top of app.js
const API_BASE = "/api/v1";

// Example:
async function fetchRepos() {
  const res = await fetch(`${API_BASE}/repos`);
  return res.json();
}

const data = {
  repos: [
    {name:"payments-api", health:76, prs:14, ci:"84%", deploys:8, issue:"delivery risk increased 24%", state:"danger"},
    {name:"auth-service", health:81, prs:9, ci:"91%", deploys:6, issue:"review latency increased 42%", state:"warning"},
    {name:"frontend", health:94, prs:6, ci:"98%", deploys:11, issue:"no significant anomalies", state:"healthy"},
    {name:"notification", health:88, prs:4, ci:"96%", deploys:5, issue:"stable", state:"healthy"},
    {name:"data-pipeline", health:71, prs:18, ci:"79%", deploys:3, issue:"CI instability detected", state:"danger"}
  ],
  prs: [
    {id:"#482", title:"authentication refactor", repo:"payments-api", age:"6d open", reviews:4, failures:7, risk:"HIGH"},
    {id:"#193", title:"notification retry logic", repo:"auth-service", age:"2d open", reviews:2, failures:1, risk:"MEDIUM"},
    {id:"#771", title:"checkout event schema", repo:"payments-api", age:"19h open", reviews:3, failures:2, risk:"MEDIUM"},
    {id:"#204", title:"navigation performance pass", repo:"frontend", age:"8h open", reviews:1, failures:0, risk:"LOW"},
    {id:"#92", title:"warehouse sync recovery", repo:"data-pipeline", age:"4d open", reviews:5, failures:9, risk:"HIGH"}
  ]
};

const main = document.getElementById("main");
const overlay = document.getElementById("commandOverlay");
const commandInput = document.getElementById("commandInput");
const commandResults = document.getElementById("commandResults");
let currentRepo = null;

function sparkline(){
  return `<svg viewBox="0 0 800 150" preserveAspectRatio="none" aria-label="health trend">
    <polyline points="0,103 90,96 180,110 270,76 360,85 450,51 540,59 630,43 710,60 800,31"
      fill="none" stroke="#aaa" stroke-width="1.5"/>
    <circle cx="800" cy="31" r="3" fill="#ededed"/>
  </svg>`;
}

function layoutHead(path,title,desc=""){
  return `<div class="page-head">
    <div><div class="eyebrow">nexus / ${path}</div><h1>${title}</h1>${desc?`<p class="lead">${desc}</p>`:""}</div>
    <button class="link-btn" data-action="refresh">refresh ↻</button>
  </div>`;
}

function overview(){
  return `
  ${layoutHead("overview","good afternoon.","the engineering system is healthy, but delivery risk has increased across 2 repositories.")}
  <section class="health">
    <div><div class="eyebrow">engineering health</div><div class="score">82 <small>/ 100</small></div><div class="delta down" style="margin:14px 0 0">↑ 4.2% this week</div></div>
    <div class="trend">${sparkline()}</div>
  </section>
  <div class="metrics">
    <div class="metric"><div class="metric-value">12</div><div class="metric-label">repositories</div></div>
    <div class="metric"><div class="metric-value">37</div><div class="metric-label">open prs</div></div>
    <div class="metric"><div class="metric-value">94% <span class="delta down">↑</span></div><div class="metric-label">ci success</div></div>
    <div class="metric"><div class="metric-value">14.2</div><div class="metric-label">deployments / week</div></div>
    <div class="metric"><div class="metric-value">19.4h</div><div class="metric-label">median pr cycle</div></div>
  </div>

  <section class="section">
    <div class="section-head"><h2>risks</h2><button class="link-btn" data-nav="repositories">view all →</button></div>
    <div class="risk-list">
      <div class="risk"><span class="level high">HIGH</span><div><div class="risk-title">payments-api</div><div class="risk-meta">delivery risk increased 24% · ci failures +31% · pr cycle +18%</div></div><span class="arrow">→</span></div>
      <div class="risk"><span class="level medium">MED</span><div><div class="risk-title">auth-service</div><div class="risk-meta">review latency increased 42% · 3 prs waiting &gt; 48h</div></div><span class="arrow">→</span></div>
      <div class="risk"><span class="level low">LOW</span><div><div class="risk-title">frontend</div><div class="risk-meta">no significant anomalies detected</div></div><span class="arrow">→</span></div>
    </div>
  </section>

  <section class="section">
    <div class="section-head"><h2>repositories</h2><button class="link-btn" data-nav="repositories">open repositories →</button></div>
    ${repoTable()}
  </section>

  <section class="section">
    <div class="section-head"><h2>recent activity</h2><span class="eyebrow">live</span></div>
    ${activity()}
  </section>`;
}

function repoTable(){
  return `<div class="table-wrap"><table><thead><tr><th>repository</th><th>health</th><th>prs</th><th>ci</th><th>deploys / wk</th></tr></thead><tbody>
  ${data.repos.map(r=>`<tr><td><span class="repo-name" data-repo="${r.name}">${r.name}</span></td><td><span class="status"><i class="dot ${r.state}"></i>${r.health}</span></td><td>${r.prs}</td><td>${r.ci}</td><td>${r.deploys}</td></tr>`).join("")}
  </tbody></table></div>`;
}

function activity(){
  const rows=[
    ["15:42","deployment","payments-api","failed","bad"],
    ["15:31","pull req","#482","merged","good"],
    ["14:57","workflow","auth-service","failed","bad"],
    ["14:41","pull req","#194","review requested","warn"],
    ["13:22","deployment","frontend","successful","good"],
    ["12:58","issue","payments-api #831","reopened","warn"]
  ];
  return `<div class="activity">${rows.map(x=>`<div class="activity-row"><span class="time">${x[0]}</span><span class="kind">${x[1]}</span><span>${x[2]}</span><span class="${x[4]}">${x[3]}</span></div>`).join("")}</div>`;
}

function repositories(){
  return `${layoutHead("repositories","repositories","a compact view of engineering health across connected systems.")}
  <section class="section" style="margin-top:0">${repoTable()}</section>
  <div class="split">
    <section class="section"><div class="section-head"><h2>health distribution</h2></div>
      <div class="signal-grid">
        <div class="signal"><div class="eyebrow">healthy</div><div class="v">7</div></div>
        <div class="signal"><div class="eyebrow">degraded</div><div class="v">3</div></div>
        <div class="signal"><div class="eyebrow">high risk</div><div class="v">2</div></div>
        <div class="signal"><div class="eyebrow">avg health</div><div class="v">82 / 100</div></div>
      </div>
    </section>
    <section class="section"><div class="section-head"><h2>system note</h2></div>
      <p class="lead">health scores combine delivery, review, CI/CD and issue-resolution signals. scores are indicators, not individual productivity measures.</p>
    </section>
  </div>`;
}

function repoPage(name){
  const r=data.repos.find(x=>x.name===name) || data.repos[0];
  currentRepo=r.name;
  return `${layoutHead("repositories / "+r.name,r.name,"repository intelligence profile.")}
  <div class="repo-head"><div><div class="eyebrow">engineering signals</div><div class="repo-health">${r.health} <span style="font-size:12px;color:var(--muted)">/ 100</span></div><div class="delta ${r.health<80?"up":"down"}" style="margin-top:10px">${r.health<80?"↓ 8%":"↑ 3%"} this week</div></div>
  <div><div class="eyebrow">current risk</div><div class="level ${r.state==="danger"?"high":r.state==="warning"?"medium":"low"}">${r.state==="danger"?"HIGH":r.state==="warning"?"MEDIUM":"LOW"}</div></div></div>
  <div class="tabs"><button class="active">overview</button><button>pull requests</button><button>ci / cd</button><button>issues</button></div>
  <div class="metrics">
    <div class="metric"><div class="metric-value">29.1h</div><div class="metric-label">pr cycle <span class="delta up">↑ 18%</span></div></div>
    <div class="metric"><div class="metric-value">11.4h</div><div class="metric-label">review latency <span class="delta up">↑ 31%</span></div></div>
    <div class="metric"><div class="metric-value">${r.ci}</div><div class="metric-label">ci success <span class="delta up">↓ 9%</span></div></div>
    <div class="metric"><div class="metric-value">${r.deploys}/w</div><div class="metric-label">deploy frequency</div></div>
    <div class="metric"><div class="metric-value">2.8d</div><div class="metric-label">issue resolution</div></div>
  </div>
  <section class="section"><div class="section-head"><h2>risk analysis</h2><button class="link-btn" data-nav="analyst">investigate →</button></div>
    <div class="callout"><div class="callout-title">${r.state==="danger"?"high":"moderate"} risk signal</div><div style="line-height:1.8">${r.issue}. The strongest contributing signals are CI instability, PR latency and recent change volume.</div></div>
  </section>`;
}

function pulls(){
  return `${layoutHead("pull requests","pull requests","open changes ranked by engineering risk and age.")}
  <div class="eyebrow">37 open · filter: [all] [high risk] [stale]</div>
  <section class="section" style="margin-top:18px">
    ${data.prs.map(p=>`<div class="pr-card"><div class="pr-id">${p.id}</div><div><div class="pr-title">${p.title}</div><div class="pr-meta">${p.repo} · ${p.age} · ${p.reviews} reviews · ${p.failures} CI failures</div></div><div class="risk-pill level ${p.risk==="HIGH"?"high":p.risk==="MEDIUM"?"medium":"low"}">${p.risk}</div></div>`).join("")}
  </section>`;
}

function cicd(){
  return `${layoutHead("ci / cd","workflow health","continuous integration and deployment signals across connected repositories.")}
  <section class="cicd-grid">
    <div><div class="eyebrow">ci success</div><div class="big-stat">94.2%</div><div class="delta down" style="margin-top:12px">↓ 1.8% vs previous week</div></div>
    <div><div class="eyebrow">repository success rates</div>
      ${data.repos.slice(0,4).map(r=>`<div class="bar-row"><span>${r.name}</span><div class="bar"><i style="width:${parseInt(r.ci)}%"></i></div><span>${r.ci}</span></div>`).join("")}
    </div>
  </section>
  <section class="section"><div class="section-head"><h2>failure patterns</h2></div>
    <div class="signal-grid">
      <div class="signal"><div class="eyebrow">integration tests</div><div class="v">47%</div></div>
      <div class="signal"><div class="eyebrow">lint</div><div class="v">21%</div></div>
      <div class="signal"><div class="eyebrow">unit tests</div><div class="v">18%</div></div>
      <div class="signal"><div class="eyebrow">build</div><div class="v">14%</div></div>
    </div>
    <div class="callout"><div class="callout-title">anomaly detected</div><div>integration-test failures are 42% above the rolling baseline for payments-api.</div></div>
  </section>`;
}

function analyst(){
  return `${layoutHead("analyst","engineering analyst","ask NEXUS to investigate engineering signals using evidence from repositories, CI/CD, deployments and documentation.")}
  <div class="analyst">
    <div class="eyebrow">investigation / payments-api</div>
    <h2 style="font-size:20px;margin-top:8px">why is payments-api becoming risky?</h2>
    <div class="investigation">
      ${["repository metrics","pull requests","ci failures","deployments","recent issues","engineering documentation"].map(x=>`<div class="investigation-row"><span class="check">[✓]</span>${x}</div>`).join("")}
    </div>
    <div class="finding">
      <div class="section-head"><h2>finding</h2><span class="confidence">confidence 87%</span></div>
      <div class="finding-box">payments-api has entered a high-risk state. The strongest signal is CI instability following the recent authentication refactor.</div>
    </div>
    <div class="evidence">
      <div class="section-head"><h2>evidence</h2></div>
      ${[
        ["01","CI failure rate increased","8% → 31% over the last 7 days","CI / metrics"],
        ["02","PR cycle time increased","18.2h → 29.1h","Repository metrics"],
        ["03","PR #482 remains open","6 days · 4 review cycles · 7 CI failures","Pull request"],
        ["04","Deployment instability","3 failures followed the authentication refactor","Deployment history"]
      ].map(e=>`<div class="evidence-row"><span class="evidence-num">${e[0]}</span><div><div>${e[1]}</div><div class="evidence-meta">${e[2]}</div></div><span class="evidence-meta">${e[3]}</span></div>`).join("")}
    </div>
    <div class="finding">
      <div class="section-head"><h2>interpretation</h2></div>
      <p class="lead">The evidence points toward a delivery bottleneck rather than a single isolated failure. Repeated CI failures are increasing review and merge time, while the authentication refactor appears correlated with recent deployment instability.</p>
    </div>
    <div class="prompt">&gt; ask a follow-up...</div>
  </div>`;
}

function render(page="overview"){
  document.querySelectorAll(".topnav button").forEach(b=>b.classList.toggle("active",b.dataset.nav===page));
  if(page==="overview") main.innerHTML=overview();
  else if(page==="repositories") main.innerHTML=repositories();
  else if(page==="pulls") main.innerHTML=pulls();
  else if(page==="cicd") main.innerHTML=cicd();
  else if(page==="analyst") main.innerHTML=analyst();
  else if(page==="repo") main.innerHTML=repoPage(currentRepo);
  bind();
  window.scrollTo({top:0,behavior:"smooth"});
}

function bind(){
  document.querySelectorAll("[data-nav]").forEach(el=>el.onclick=()=>render(el.dataset.nav));
  document.querySelectorAll("[data-repo]").forEach(el=>el.onclick=()=>{currentRepo=el.dataset.repo;render("repo")});
  document.querySelectorAll('[data-action="refresh"]').forEach(el=>el.onclick=()=>toast("data refreshed · simulated local prototype"));
}

function toast(msg){
  const t=document.getElementById("toast");t.textContent=msg;t.classList.remove("hidden");
  clearTimeout(window.toastTimer);window.toastTimer=setTimeout(()=>t.classList.add("hidden"),2200);
}

const commands=[
  ["overview","navigation"],["repositories","navigation"],["pull requests","navigation"],["ci / cd","navigation"],["analyst","intelligence"],
  ...data.repos.map(r=>[r.name,"repository"]),...data.prs.map(p=>[`${p.id} ${p.title}`,"pull request"])
];
function openCommand(){
  overlay.classList.remove("hidden");commandInput.value="";renderCommands("");commandInput.focus();
}
function closeCommand(){overlay.classList.add("hidden")}
function renderCommands(q){
  const list=commands.filter(x=>x[0].toLowerCase().includes(q.toLowerCase())).slice(0,8);
  commandResults.innerHTML=list.map((x,i)=>`<div class="command-result ${i===0?"selected":""}" data-cmd="${x[0]}"><strong>${x[0]}</strong><small>${x[1]}</small></div>`).join("");
  document.querySelectorAll("[data-cmd]").forEach(el=>el.onclick=()=>executeCommand(el.dataset.cmd));
}
function executeCommand(cmd){
  closeCommand();
  if(cmd==="overview") return render("overview");
  if(cmd==="repositories") return render("repositories");
  if(cmd==="pull requests") return render("pulls");
  if(cmd==="ci / cd") return render("cicd");
  if(cmd==="analyst") return render("analyst");
  const r=data.repos.find(x=>x.name===cmd); if(r){currentRepo=r.name;return render("repo")}
  const p=data.prs.find(x=>`${x.id} ${x.title}`===cmd); if(p){toast(`opened ${p.id} · ${p.title}`);return}
}
commandInput.addEventListener("input",e=>renderCommands(e.target.value));
document.getElementById("commandOpen").onclick=openCommand;
overlay.addEventListener("click",e=>{if(e.target===overlay)closeCommand()});
document.addEventListener("keydown",e=>{
  if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==="k"){e.preventDefault();openCommand()}
  if(e.key==="Escape")closeCommand();
  if(!overlay.classList.contains("hidden")&&e.key==="Enter"){
    const selected=document.querySelector(".command-result.selected");if(selected)executeCommand(selected.dataset.cmd)
  }
  if(!overlay.classList.contains("hidden")&&e.key==="ArrowDown"){
    e.preventDefault();const rows=[...document.querySelectorAll(".command-result")];const i=rows.findIndex(x=>x.classList.contains("selected"));if(rows.length){rows[i]?.classList.remove("selected");rows[(i+1)%rows.length].classList.add("selected")}}
  if(!overlay.classList.contains("hidden")&&e.key==="ArrowUp"){
    e.preventDefault();const rows=[...document.querySelectorAll(".command-result")];const i=rows.findIndex(x=>x.classList.contains("selected"));if(rows.length){rows[i]?.classList.remove("selected");rows[(i-1+rows.length)%rows.length].classList.add("selected")}}
});
document.getElementById("userButton").onclick=()=>toast("demo account · local prototype");
render();
