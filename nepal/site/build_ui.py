#!/usr/bin/env python3
"""Build the clean UI version of Nepal Occupation Visualizer."""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent

with open(ROOT / 'data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

inline = json.dumps(data, separators=(',', ':'), ensure_ascii=False)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Nepal Occupation Visualizer</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box;}
:root{
  --bg:#0f0d11;--surface:#18151c;--surface2:#211d27;--border:rgba(255,255,255,0.07);
  --fg:#edeaf0;--fg2:#8a8494;--fg3:#5a5462;
  --accent:#c0253f;--accent-dim:rgba(192,37,63,0.15);
  --blue:#2a4f80;--font:'Inter',system-ui,sans-serif;
}
html,body{height:100%;overflow:hidden;}
body{background:var(--bg);color:var(--fg);font-family:var(--font);font-size:14px;display:flex;flex-direction:column;}

/* TOP BAR */
.topbar{display:flex;align-items:center;gap:16px;padding:14px 24px;border-bottom:1px solid var(--border);background:var(--surface);flex-shrink:0;}
.topbar-logo{display:flex;align-items:center;gap:10px;}
.topbar-logo span{font-size:22px;}
.topbar-title{font-size:15px;font-weight:700;letter-spacing:-0.01em;}
.topbar-sub{font-size:11px;color:var(--fg3);margin-top:1px;}
.topbar-divider{width:1px;height:32px;background:var(--border);}
.topbar-stat{display:flex;flex-direction:column;gap:1px;}
.topbar-stat-val{font-size:14px;font-weight:600;}
.topbar-stat-lbl{font-size:10px;color:var(--fg3);text-transform:uppercase;letter-spacing:0.06em;}
.topbar-search{flex:1;max-width:320px;margin-left:auto;display:flex;align-items:center;gap:8px;background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:0 12px;}
.topbar-search svg{color:var(--fg3);flex-shrink:0;}
.topbar-search input{background:none;border:none;outline:none;color:var(--fg);font-family:var(--font);font-size:13px;width:100%;padding:9px 0;}
.topbar-search input::placeholder{color:var(--fg3);}

/* LAYOUT */
.main{display:flex;flex:1;overflow:hidden;}

/* LEFT */
.left{width:300px;flex-shrink:0;border-right:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden;}
.filter-bar{padding:10px 12px;border-bottom:1px solid var(--border);display:flex;flex-wrap:wrap;gap:5px;}
.chip{padding:4px 10px;border-radius:20px;font-size:11px;font-weight:500;border:1px solid var(--border);color:var(--fg2);cursor:pointer;background:transparent;transition:all 0.15s;font-family:var(--font);}
.chip:hover{background:var(--surface2);color:var(--fg);}
.chip.active{background:var(--accent-dim);border-color:var(--accent);color:var(--fg);}
.occ-list{flex:1;overflow-y:auto;padding:8px;}
.occ-list::-webkit-scrollbar{width:4px;}
.occ-list::-webkit-scrollbar-thumb{background:var(--border);border-radius:4px;}
.occ-item{display:flex;align-items:center;gap:10px;padding:9px 10px;border-radius:8px;cursor:pointer;transition:background 0.12s;border:1px solid transparent;margin-bottom:2px;}
.occ-item:hover{background:var(--surface2);}
.occ-item.active{background:var(--accent-dim);border-color:rgba(192,37,63,0.3);}
.occ-score-dot{width:32px;height:32px;border-radius:8px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;}
.occ-info{flex:1;min-width:0;}
.occ-name{font-size:12px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.occ-meta{font-size:11px;color:var(--fg3);margin-top:1px;}
.occ-count{font-size:11px;color:var(--fg3);flex-shrink:0;}
.no-results{padding:32px 16px;text-align:center;color:var(--fg3);font-size:13px;}

/* RIGHT */
.right{flex:1;overflow-y:auto;padding:28px 32px;}
.right::-webkit-scrollbar{width:4px;}
.right::-webkit-scrollbar-thumb{background:var(--border);border-radius:4px;}
.empty-state{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:var(--fg3);text-align:center;gap:12px;}
.empty-state .icon{font-size:48px;opacity:0.25;}
.empty-state h2{font-size:16px;font-weight:600;color:var(--fg2);}
.empty-state p{font-size:13px;max-width:300px;line-height:1.6;}

/* DETAIL */
.detail{display:none;}
.detail.visible{display:block;}
.detail-header{margin-bottom:24px;}
.detail-nsco{font-size:11px;color:var(--fg3);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:5px;}
.detail-title{font-size:26px;font-weight:700;letter-spacing:-0.02em;line-height:1.2;margin-bottom:8px;}
.detail-sector{display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--fg2);background:var(--surface2);border:1px solid var(--border);border-radius:20px;padding:3px 10px;}

/* METRIC GRID */
.metric-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px;}
.metric-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px;}
.metric-label{font-size:10px;color:var(--fg3);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:7px;}
.metric-value{font-size:22px;font-weight:700;letter-spacing:-0.02em;}
.metric-sub{font-size:11px;color:var(--fg3);margin-top:3px;}

/* AI EXPOSURE */
.exposure-section{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px;}
.section-label{font-size:10px;color:var(--fg3);text-transform:uppercase;letter-spacing:0.07em;margin-bottom:12px;}
.exposure-row{display:flex;align-items:baseline;gap:10px;margin-bottom:12px;}
.exposure-score{font-size:40px;font-weight:700;letter-spacing:-0.03em;}
.exposure-max{font-size:16px;color:var(--fg3);}
.exposure-tier{display:inline-flex;align-items:center;font-size:12px;font-weight:500;padding:3px 10px;border-radius:6px;}
.exposure-bar-track{height:8px;background:var(--surface2);border-radius:6px;overflow:hidden;margin-bottom:14px;}
.exposure-bar-fill{height:100%;border-radius:6px;transition:width 0.6s cubic-bezier(0.4,0,0.2,1);}
.exposure-rationale{font-size:13px;line-height:1.65;color:var(--fg2);}

/* CHARTS ROW */
.charts-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;}
.chart-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:18px;}
.big-val{font-size:22px;font-weight:700;letter-spacing:-0.02em;margin-bottom:3px;}
.context-text{font-size:12px;color:var(--fg2);margin-bottom:14px;}
.sbar-row{display:flex;align-items:center;gap:8px;margin-bottom:7px;font-size:11px;}
.sbar-name{width:72px;flex-shrink:0;color:var(--fg3);text-align:right;}
.sbar-track{flex:1;height:7px;background:var(--surface2);border-radius:4px;overflow:hidden;}
.sbar-fill{height:100%;border-radius:4px;transition:width 0.5s;}
.sbar-val{width:72px;flex-shrink:0;color:var(--fg3);}
.wpill{display:flex;align-items:center;gap:8px;background:var(--surface2);border-radius:7px;padding:9px 11px;margin-bottom:7px;}
.wpip{width:8px;height:8px;border-radius:50%;flex-shrink:0;}
.wtext{font-size:12px;color:var(--fg2);}

/* EDUCATION */
.edu-section{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:18px;display:flex;align-items:center;gap:16px;margin-bottom:16px;}
.edu-icon{font-size:28px;}
.edu-label{font-size:10px;color:var(--fg3);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;}
.edu-value{font-size:16px;font-weight:600;}
.edu-bucket{font-size:12px;color:var(--fg2);margin-top:2px;}

@media(max-width:860px){
  .left{width:240px;}
  .metric-grid{grid-template-columns:1fr 1fr;}
  .charts-row{grid-template-columns:1fr;}
  .right{padding:18px;}
}
@media(max-width:640px){
  html,body{overflow:auto;}
  .main{flex-direction:column;overflow:visible;}
  .left{width:100%;border-right:none;border-bottom:1px solid var(--border);max-height:240px;}
  .metric-grid{grid-template-columns:1fr;}
  .topbar{flex-wrap:wrap;}
}
</style>
</head>
<body>

<header class="topbar">
  <div class="topbar-logo">
    <span>🇳🇵</span>
    <div>
      <div class="topbar-title">Nepal Occupation Visualizer</div>
      <div class="topbar-sub">AI Exposure &amp; Labor Market · NSCO 2021</div>
    </div>
  </div>
  <div class="topbar-divider"></div>
  <div class="topbar-stat">
    <div class="topbar-stat-val" id="statTotal">52</div>
    <div class="topbar-stat-lbl">Occupations</div>
  </div>
  <div class="topbar-stat">
    <div class="topbar-stat-val">13.9M</div>
    <div class="topbar-stat-lbl">Workforce</div>
  </div>
  <div class="topbar-stat">
    <div class="topbar-stat-val" id="statAvgExposure">2.3<span style="font-size:11px;color:var(--fg3);">/10</span></div>
    <div class="topbar-stat-lbl">Avg AI Exposure</div>
  </div>
  <div class="topbar-search">
    <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
    <input type="text" id="searchInput" placeholder="Search occupation…" autocomplete="off">
  </div>
</header>

<div class="main">
  <aside class="left">
    <div class="filter-bar" id="filterBar">
      <button class="chip active" data-sector="All">All</button>
    </div>
    <div class="occ-list" id="occList"></div>
  </aside>

  <main class="right">
    <div class="empty-state" id="emptyState">
      <div class="icon">🔍</div>
      <h2>Select an occupation</h2>
      <p>Use the search bar or browse the list on the left to explore AI exposure, salary, and education data for any Nepali occupation.</p>
    </div>

    <div class="detail" id="detailPanel">
      <div class="detail-header">
        <div class="detail-nsco" id="dNsco"></div>
        <div class="detail-title" id="dTitle"></div>
        <span class="detail-sector" id="dSector"></span>
      </div>

      <div class="metric-grid">
        <div class="metric-card">
          <div class="metric-label">Monthly Salary</div>
          <div class="metric-value" id="dSalary"></div>
          <div class="metric-sub">Average, NPR</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Workforce Size</div>
          <div class="metric-value" id="dSize"></div>
          <div class="metric-sub" id="dSizeSub"></div>
        </div>
        <div class="metric-card">
          <div class="metric-label">AI Exposure</div>
          <div class="metric-value" id="dExpSmall"></div>
          <div class="metric-sub">out of 10</div>
        </div>
      </div>

      <div class="exposure-section">
        <div class="section-label">AI Exposure Score — How much can AI reshape this job?</div>
        <div class="exposure-row">
          <div class="exposure-score" id="dScore"></div>
          <div class="exposure-max">/10</div>
          <div class="exposure-tier" id="dTier"></div>
        </div>
        <div class="exposure-bar-track"><div class="exposure-bar-fill" id="dBar"></div></div>
        <div class="exposure-rationale" id="dRationale"></div>
      </div>

      <div class="charts-row">
        <div class="chart-card">
          <div class="section-label">Salary Comparison</div>
          <div class="big-val" id="dSalBig"></div>
          <div class="context-text" id="dSalCtx"></div>
          <div id="dSalBars"></div>
        </div>
        <div class="chart-card">
          <div class="section-label">Workforce Breakdown</div>
          <div class="big-val" id="dWfBig"></div>
          <div class="context-text" id="dWfCtx"></div>
          <div id="dWfPills"></div>
        </div>
      </div>

      <div class="edu-section">
        <div class="edu-icon" id="dEduIcon"></div>
        <div>
          <div class="edu-label">Minimum Education Required</div>
          <div class="edu-value" id="dEduVal"></div>
          <div class="edu-bucket" id="dEduBucket"></div>
        </div>
      </div>
    </div>
  </main>
</div>

<script>
const OCCUPATIONS = __INLINE_DATA__;
const TOTAL_WF = OCCUPATIONS.reduce((s,d)=>s+(d.jobs||0),0);
const MIN_WAGE = 19550;
let selectedId = null, activeFilter = 'All', searchQuery = '';

const SECTORS = [...new Set(OCCUPATIONS.map(d=>d.category))].sort();

function fmtNPR(n){if(n==null)return'—';return'NPR\u00a0'+n.toLocaleString('en-NP');}
function fmtNum(n){if(n==null)return'—';if(n>=1e6)return(n/1e6).toFixed(1)+'M';if(n>=1e3)return(n/1e3).toFixed(0)+'K';return n.toLocaleString();}

function expColor(s10){
  const t=s10/10;
  if(t<0.25)return'#2a5c90';
  if(t<0.45)return'#3a7ab0';
  if(t<0.6)return'#c07820';
  if(t<0.75)return'#b83030';
  return'#c0253f';
}

function tierInfo(s10){
  if(s10<=1)return['Minimal','rgba(42,92,144,0.18)','#5090c0'];
  if(s10<=3)return['Low','rgba(42,92,144,0.15)','#4a80b0'];
  if(s10<=5)return['Moderate','rgba(192,120,32,0.2)','#d09030'];
  if(s10<=7)return['High','rgba(184,48,48,0.2)','#c04848'];
  return['Very High','rgba(192,37,63,0.22)','#d03050'];
}

function eduIcon(b){
  return{
    'No formal education':'🌾','Vocational / Training':'🔧','SEE (Grade 10)':'📋',
    '+2 / Proficiency':'📖','Diploma':'📜',"Bachelor's Degree":'🎓',"Master's Degree or above":'🏅'
  }[b]||'📋';
}

function sectorEmoji(c){
  return{'Managers':'🏢','Professionals':'💡','Technicians and Associates':'⚙️',
    'Clerical Support':'📁','Service and Sales':'🛍️','Skilled Agricultural':'🌾',
    'Craft and Trades':'🔨','Plant and Machine Operators':'🏭',
    'Elementary Occupations':'👷','Armed Forces':'🎖️'}[c]||'💼';
}

// Build sector chips
(function(){
  const bar=document.getElementById('filterBar');
  SECTORS.forEach(s=>{
    const b=document.createElement('button');
    b.className='chip'; b.dataset.sector=s; b.textContent=s;
    bar.appendChild(b);
  });
  bar.addEventListener('click',e=>{
    const chip=e.target.closest('.chip');
    if(!chip)return;
    activeFilter=chip.dataset.sector;
    bar.querySelectorAll('.chip').forEach(c=>c.classList.toggle('active',c.dataset.sector===activeFilter));
    renderList();
  });
})();

function filtered(){
  let list=OCCUPATIONS;
  if(activeFilter!=='All')list=list.filter(d=>d.category===activeFilter);
  if(searchQuery){const q=searchQuery.toLowerCase();list=list.filter(d=>d.title.toLowerCase().includes(q)||d.sector?.toLowerCase().includes(q)||d.nsco_code?.includes(q));}
  return list.slice().sort((a,b)=>(b.jobs||0)-(a.jobs||0));
}

function renderList(){
  const list=filtered();
  document.getElementById('statTotal').textContent=list.length;
  const el=document.getElementById('occList');
  if(!list.length){el.innerHTML='<div class="no-results">No results. Try a different search.</div>';return;}
  el.innerHTML=list.map(d=>{
    const col=expColor(d.exposure||0);
    const rgb=col.slice(1).match(/.{2}/g).map(x=>parseInt(x,16)).join(',');
    return`<div class="occ-item${d.occupation_id===selectedId?' active':''}" data-id="${d.occupation_id}">
      <div class="occ-score-dot" style="background:rgba(${rgb},0.15);color:${col};">${d.exposure??'—'}</div>
      <div class="occ-info">
        <div class="occ-name">${d.title}</div>
        <div class="occ-meta">${d.category}</div>
      </div>
      <div class="occ-count">${fmtNum(d.jobs)}</div>
    </div>`;
  }).join('');
  el.querySelectorAll('.occ-item').forEach(item=>item.addEventListener('click',()=>selectOcc(item.dataset.id)));
}

function selectOcc(id){
  selectedId=id;
  const d=OCCUPATIONS.find(o=>o.occupation_id===id);
  document.querySelectorAll('.occ-item').forEach(el=>el.classList.toggle('active',el.dataset.id===id));
  renderDetail(d);
}

function renderDetail(d){
  document.getElementById('emptyState').style.display='none';
  document.getElementById('detailPanel').classList.add('visible');

  document.getElementById('dNsco').textContent=`NSCO ${d.nsco_code||'—'}  ·  ${d.nsco_division_name||''}`;
  document.getElementById('dTitle').textContent=d.title;
  document.getElementById('dSector').innerHTML=`${sectorEmoji(d.category)} ${d.sector||d.category}`;

  document.getElementById('dSalary').textContent=fmtNPR(d.pay_monthly);
  document.getElementById('dSize').textContent=fmtNum(d.jobs);
  document.getElementById('dSizeSub').textContent=d.jobs?`${(d.jobs/TOTAL_WF*100).toFixed(1)}% of workforce`:'Estimated';
  document.getElementById('dExpSmall').textContent=d.exposure??'—';

  const s10=d.exposure??0, col=expColor(s10);
  const[tlbl,tbg,tcol]=tierInfo(s10);
  const scoreEl=document.getElementById('dScore');
  scoreEl.textContent=d.exposure??'—'; scoreEl.style.color=col;
  const tierEl=document.getElementById('dTier');
  tierEl.textContent=tlbl; tierEl.style.background=tbg; tierEl.style.color=tcol;
  const bar=document.getElementById('dBar');
  bar.style.width='0'; bar.style.background=col;
  setTimeout(()=>{bar.style.width=(s10*10)+'%';},60);
  document.getElementById('dRationale').textContent=d.exposure_rationale||'';

  // Salary bars
  const bmarks=[{n:'Min. Wage',v:MIN_WAGE},{n:'Nat. Avg.',v:30000},{n:'This job',v:d.pay_monthly},{n:'Doctor',v:120000}];
  const maxP=Math.max(...bmarks.map(b=>b.v||0));
  document.getElementById('dSalBig').textContent=fmtNPR(d.pay_monthly);
  const m=d.pay_monthly||0;
  document.getElementById('dSalCtx').textContent=m>MIN_WAGE?`+${(((m-MIN_WAGE)/MIN_WAGE)*100).toFixed(0)}% above minimum wage`:m===MIN_WAGE?'At minimum wage':`${(((MIN_WAGE-m)/MIN_WAGE)*100).toFixed(0)}% below minimum wage`;
  document.getElementById('dSalBars').innerHTML=bmarks.map(b=>{
    const pct=maxP?(b.v/maxP*100):0;
    const isThis=b.n==='This job';
    return`<div class="sbar-row">
      <div class="sbar-name">${b.n}</div>
      <div class="sbar-track"><div class="sbar-fill" style="width:${pct}%;background:${isThis?col:'#3a3542'}"></div></div>
      <div class="sbar-val" style="color:${isThis?'var(--fg)':'var(--fg3)'}">${fmtNPR(b.v)}</div>
    </div>`;
  }).join('');

  // Workforce pills
  document.getElementById('dWfBig').textContent=fmtNum(d.jobs);
  const sh=(d.jobs/TOTAL_WF*100).toFixed(2);
  document.getElementById('dWfCtx').textContent=`${sh}% of Nepal's 13.9M tracked workforce`;
  const secTotal=OCCUPATIONS.filter(o=>o.category===d.category).reduce((s,o)=>s+(o.jobs||0),0);
  const secSh=secTotal?(d.jobs/secTotal*100).toFixed(1):'0';
  document.getElementById('dWfPills').innerHTML=`
    <div class="wpill"><div class="wpip" style="background:${col}"></div><div class="wtext"><b>${fmtNum(d.jobs)}</b> workers in this role</div></div>
    <div class="wpill"><div class="wpip" style="background:#3a6090"></div><div class="wtext"><b>${(d.jobs/TOTAL_WF*100).toFixed(1)}%</b> of total tracked workforce</div></div>
    <div class="wpill"><div class="wpip" style="background:#5a5462"></div><div class="wtext"><b>${secSh}%</b> of ${d.category} sector (${fmtNum(secTotal)} total)</div></div>
  `;

  document.getElementById('dEduIcon').textContent=eduIcon(d.education_bucket);
  document.getElementById('dEduVal').textContent=d.education||'—';
  document.getElementById('dEduBucket').textContent=d.education_bucket||'';
}

document.getElementById('searchInput').addEventListener('input',e=>{
  searchQuery=e.target.value.trim();
  renderList();
});

renderList();
</script>
</body>
</html>"""

result = HTML_TEMPLATE.replace('__INLINE_DATA__', inline)

with open(ROOT / 'index.html', 'w', encoding='utf-8') as f:
    f.write(result)

print(f"OK — {len(result)} bytes written to nepal/site/index.html")
