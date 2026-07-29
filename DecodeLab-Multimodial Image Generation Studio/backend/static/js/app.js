const API = '';
const logo = '/static/assets/prismora-logo.png';
const $ = (sel, root=document) => root.querySelector(sel);
const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));

const MODES = [
  ['realistic','Photoreal','Authentic photography with refined natural detail'],
  ['natural','Natural','Soft illumination with a lifelike atmosphere'],
  ['cinematic','Cinematic','Filmic lighting with dimensional depth'],
  ['product','Product','Precision styling for premium campaign imagery'],
  ['portrait','Portrait','Refined expression, skin detail and lens character'],
  ['fantasy','Fantasy','Elevated concept artistry with imaginative scale'],
  ['minimal','Minimal','Disciplined composition with intentional space'],
  ['illustration','Illustration','Art-directed forms with polished detail']
];
const STYLES = [
  ['premium','Luxury'], ['editorial','Editorial'], ['commercial','Campaign'], ['film','Cinematic'], ['studio','Studio'], ['raw','Natural Finish']
];
const RATIOS = [
  ['1:1','Square','1024 × 1024'], ['16:9','Widescreen','1344 × 768'], ['9:16','Portrait','768 × 1344'], ['4:5','Social Portrait','1024 × 1280'], ['3:4','Classic Portrait','960 × 1280'], ['4:3','Landscape','1280 × 960'], ['21:9','Ultra Wide','1536 × 640']
];
const RATIO_RESOLUTIONS = {
  '1:1':'1024x1024', '16:9':'1344x768', '9:16':'768x1344', '4:5':'1024x1280',
  '5:4':'1280x1024', '3:4':'960x1280', '4:3':'1280x960', '21:9':'1536x640'
};
const resolutionForRatio = ratio => RATIO_RESOLUTIONS[ratio] || RATIO_RESOLUTIONS['1:1'];
const IDEA_PROMPTS = [
  'A photorealistic luxury perfume bottle on black obsidian glass, prism reflections, soft cyan and violet rim light, commercial campaign quality',
  'A natural portrait of a young founder in a modern studio, authentic skin texture, soft window light, premium editorial framing',
  'A cinematic futuristic city after rain, reflective streets, luminous prism architecture, volumetric atmosphere, ultra detailed',
  'A minimal professional AI workspace with translucent pyramid crystal, calm neutral palette, clean shadows, high-end SaaS brand aesthetic'
];

const VIEW_ROUTES = {
  studio:'create',
  lab:'prompt-lab',
  library:'image-library',
  favorites:'favorites',
  profile:'profile',
  settings:'settings',
  history:'history',
  system:'system'
};
const ROUTE_VIEWS = Object.fromEntries(Object.entries(VIEW_ROUTES).map(([view,route])=>[route,view]));
let renderedView = null;

let state = {
  user:null,
  settings:null,
  theme:'dark',
  view:'studio',
  threads:[],
  generations:[],
  activeThread:null,
  prompt:'',
  enhanced:'',
  negative:'',
  mode:'realistic',
  style:'premium',
  ratio:'1:1',
  resolution:'auto',
  count:1,
  seed:'',
  autoEnhance:true,
  refineFrom:null,
  refineDialog:null,
  refineInstruction:'',
  refinePreserveSubject:true,
  refinePreserveComposition:true,
  refineBusy:false,
  scrollToGenerationId:null,
  search:'',
  busy:false,
  authMode:'login',
  sidebarOpen:false,
  inspectorOpen:false,
  enhancingInline:false,
  enhancingSidebar:false,
  enhancingLab:false,
  enhanceRequestId:0,
  scrollPositions:{},
  sidebarScroll:0,
  inspectorScroll:0,
  forceStudioBottom:false
};

function icon(name){
  const icons={
    spark:'<svg viewBox="0 0 24 24"><path d="M12 2l1.75 6.25L20 10l-6.25 1.75L12 18l-1.75-6.25L4 10l6.25-1.75L12 2z"/><path d="M19 15l.8 2.8L23 19l-3.2.9L19 23l-.9-3.1L15 19l3.1-1.2L19 15z"/></svg>',
    plus:'<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>',
    search:'<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>',
    image:'<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="3"/><path d="M8 13l2.5-2.5L15 15l2-2 4 4"/><circle cx="8" cy="8" r="1.2"/></svg>',
    flask:'<svg viewBox="0 0 24 24"><path d="M10 2v6l-5 9a3 3 0 0 0 2.6 4.5h8.8A3 3 0 0 0 19 17l-5-9V2"/><path d="M8 2h8M7.2 15h9.6"/></svg>',
    heart:'<svg viewBox="0 0 24 24"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 1 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8z"/></svg>',
    user:'<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 22c1.6-4.2 4.3-6 8-6s6.4 1.8 8 6"/></svg>',
    gear:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3.4"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1A2 2 0 1 1 4.2 17l.1-.1A1.7 1.7 0 0 0 4.6 15 1.7 1.7 0 0 0 3 14H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.6-1A1.7 1.7 0 0 0 4.3 7l-.1-.1A2 2 0 1 1 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3H9a1.7 1.7 0 0 0 1-1.6V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.6h.1a1.7 1.7 0 0 0 1.9-.3l.1-.1A2 2 0 1 1 19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9v.1A1.7 1.7 0 0 0 21 10h.1a2 2 0 1 1 0 4H21a1.7 1.7 0 0 0-1.6 1z"/></svg>',
    menu:'<svg viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
    logout:'<svg viewBox="0 0 24 24"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><path d="M10 17l5-5-5-5M15 12H3"/></svg>',
    download:'<svg viewBox="0 0 24 24"><path d="M12 3v12m0 0l-4-4m4 4l4-4"/><path d="M4 21h16"/></svg>',
    open:'<svg viewBox="0 0 24 24"><path d="M14 5h5v5"/><path d="M10 14L19 5"/><path d="M19 13v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h5"/></svg>',
    copy:'<svg viewBox="0 0 24 24"><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M4 16V6a2 2 0 0 1 2-2h10"/></svg>',
    trash:'<svg viewBox="0 0 24 24"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 14h10l1-14M9 7V4h6v3"/></svg>',
    wand:'<svg viewBox="0 0 24 24"><path d="M4 20L20 4"/><path d="M14 4l6 6"/><path d="M5 6l1-3 1 3 3 1-3 1-1 3-1-3-3-1 3-1z"/></svg>',
    history:'<svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/><path d="M12 7v5l3 2"/></svg>',
    sun:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
  };
  return icons[name] || icons.spark;
}

function escapeHtml(s=''){return String(s).replace(/[&<>'"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[m]));}
function escapeAttr(s=''){return escapeHtml(s).replace(/`/g,'&#096;');}
function title(s=''){return String(s).replace(/_/g,' ').replace(/\b\w/g,m=>m.toUpperCase());}
function shortDate(s){try{return new Date(s).toLocaleString([], {month:'short',day:'2-digit',hour:'2-digit',minute:'2-digit'});}catch{return ''}}
function initials(name='U'){return escapeHtml((name||'User').split(/\s+/).map(x=>x[0]).join('').slice(0,2).toUpperCase());}
function imageUrl(img){return img?.url || ''}
function imageExtension(img){
  const clean=imageUrl(img).split('?')[0];
  const match=clean.match(/\.([a-z0-9]+)$/i);
  return match?.[1]?.toLowerCase() || 'png';
}
function historyDownloadName(g,img){return `prismora-generation-${g.id || g.thread_id}.${imageExtension(img)}`}
function activeModeLabel(){return MODES.find(x=>x[0]===state.mode)?.[1] || title(state.mode)}
function generationStatusLabel(status='saved'){return ({completed:'Ready',processing:'Creating',failed:'Attention Needed',saved:'Archived',pending:'Preparing'})[String(status).toLowerCase()] || title(status)}
function cleanEnhancedPrompt(text=''){
  return String(text || '')
    .replace(/\n?Prompt enhancer note:[\s\S]*$/i, '')
    .replace(/\n?Gemini unavailable[\s\S]*$/i, '')
    .trim();
}
function getComposerPrompt(){return ($('#prompt')?.value || state.prompt || '').trim();}
function focusComposer(){setTimeout(()=>{const el=$('#prompt'); if(el){try{el.focus({preventScroll:true});}catch{el.focus();} autoGrowTextarea(el);}},60);}
function routeKeyFromLocation(){return String(window.location.hash||'').replace(/^#\/?/,'').split(/[?&]/)[0].trim();}
function viewFromLocation(){return ROUTE_VIEWS[routeKeyFromLocation()] || 'studio';}
function syncLocationToView(view,{replace=false}={}){
  const route=VIEW_ROUTES[view] || VIEW_ROUTES.studio;
  const hash=`#/${route}`;
  if(window.location.hash===hash) return;
  window.history[replace?'replaceState':'pushState'](null,'',hash);
}
function navigateView(view,{replace=false,resetScroll=false}={}){
  const next=VIEW_ROUTES[view]?view:'studio';
  state.view=next;
  state.sidebarOpen=false;
  syncLocationToView(next,{replace});
  render();
  if(resetScroll){
    state.scrollPositions[next]=0;
    requestAnimationFrame(()=>{const el=$('#workScroll'); if(el)el.scrollTop=0;});
  }
}
function restoreWorkspaceScroll({skipWork=false}={}){
  requestAnimationFrame(()=>{
    const work=$('#workScroll');
    if(work && !skipWork){
      const previousBehavior=work.style.scrollBehavior;
      work.style.scrollBehavior='auto';
      work.scrollTop=state.scrollPositions[state.view] || 0;
      work.style.scrollBehavior=previousBehavior;
    }
    const sidebar=$('#sidebar');
    if(sidebar)sidebar.scrollTop=state.sidebarScroll || 0;
    const inspector=$('#inspector');
    if(inspector)inspector.scrollTop=state.inspectorScroll || 0;
  });
}
function pinStudioToBottomInstantly(){
  const work=$('#workScroll');
  if(!work)return;
  const previousBehavior=work.style.scrollBehavior;
  work.style.scrollBehavior='auto';
  work.scrollTop=work.scrollHeight;
  state.scrollPositions.studio=work.scrollTop;
  requestAnimationFrame(()=>{work.style.scrollBehavior=previousBehavior;});
}
function scrollToPendingGeneration(){
  const generationId=state.scrollToGenerationId;
  if(!generationId)return;
  requestAnimationFrame(()=>requestAnimationFrame(()=>{
    const work=$('#workScroll');
    if(work){
      const distanceFromBottom = Math.max(0, work.scrollHeight - work.clientHeight - work.scrollTop);
      if(distanceFromBottom < 220){
        work.scrollTop = work.scrollHeight;
        state.scrollPositions.studio = Number.MAX_SAFE_INTEGER;
      }
    }
    state.scrollToGenerationId=null;
  }));
}
function friendlyErrorMessage(msg=''){
  if(Array.isArray(msg)){
    const first=msg[0] || {};
    return friendlyErrorMessage(first.msg || first.message || 'Please review the selected generation settings.');
  }
  if(msg && typeof msg==='object'){
    return friendlyErrorMessage(msg.message || msg.detail || msg.error || 'Prismora could not complete this request.');
  }
  const raw = String(msg || '').trim();
  if(!raw) return 'Something went wrong. Please try again.';
  if(/nsfw|nude|nudity|sexual|adult content|explicit|unsafe|offensive/i.test(raw)){
    return 'Prismora is designed for respectful, safe visual creation and cannot produce explicit, adult, offensive, or harmful content. Please revise your prompt.';
  }
  if(/cloudflare token\/account permission failed/i.test(raw)){
    return 'The image engine is not currently available. Please review the service configuration and try again.';
  }
  if(/timed out after retries/i.test(raw)){
    return 'The image took longer than expected to create. Please try again in a moment.';
  }
  if(/quality assurance|quality threshold|semantic alignment|aesthetic threshold/i.test(raw)){
    return 'The visual did not meet Prismora quality standards after an automatic retry. Add clearer subject, action, scene or style detail and try again.';
  }
  if(/incompatible with aspect ratio|selected resolution does not match/i.test(raw)){
    return 'The selected resolution does not match the canvas format. Choose Automatic or the recommended resolution for this ratio.';
  }
  if(/cloudflare request failed:/i.test(raw)){
    return 'Prismora could not complete this creation. Please refine the prompt or try again shortly.';
  }
  if(/backend|database|cloudflare|api error|exception|traceback|connectionerror|runtimeerror|internal server/i.test(raw)){
    return 'Prismora encountered a temporary service issue. Please try again shortly.';
  }
  return raw;
}
function autoGrowTextarea(el){if(!el)return; const maxHeight=window.innerWidth<=900?88:96; el.style.height='auto'; el.style.height=Math.min(el.scrollHeight,maxHeight)+'px'; el.style.overflowY=el.scrollHeight>maxHeight?'auto':'hidden';}

async function api(path, opts={}){
  const res = await fetch(API+path, {credentials:'include', headers:{'Content-Type':'application/json', ...(opts.headers||{})}, ...opts});
  if(!res.ok){
    let msg = 'Prismora could not complete this request. Please try again.';
    try{const data=await res.json(); msg=data.detail || data.error || msg;}catch{}
    msg = friendlyErrorMessage(msg);
    if(res.status===401 && !path.includes('/auth/')){state.user=null; renderAuth();}
    throw new Error(msg);
  }
  return await res.json();
}
async function apiForm(path, form){
  const res = await fetch(API+path, {method:'POST', body:form, credentials:'include'});
  if(!res.ok){let msg='Prismora could not complete this request. Please try again.'; try{msg=(await res.json()).detail||msg;}catch{} throw new Error(friendlyErrorMessage(msg));}
  return await res.json();
}
function applyTheme(){document.documentElement.setAttribute('data-theme', state.theme || 'dark');}
function applySettings(s={}){
  state.settings=s||{};
  state.theme=s.theme||state.theme||'dark';
  state.mode=s.default_mode||state.mode||'realistic';
  state.ratio=s.default_ratio||state.ratio||'1:1';
  state.style=s.default_style||state.style||'premium';
  state.autoEnhance=s.auto_enhance!==false;
  applyTheme();
}
async function boot(){
  applyTheme();
  state.view=viewFromLocation();
  syncLocationToView(state.view,{replace:true});
  try{
    const data=await api('/api/auth/me');
    state.user=data.user; applySettings(data.settings||{}); await loadAll(); if(state.view==='studio') state.forceStudioBottom=true; render();
  }catch{renderAuth();}
}
async function loadAll(){
  const [threads, gens] = await Promise.all([api('/api/threads'), api('/api/generations')]);
  state.threads = threads.items || [];
  state.generations = gens.items || [];
}

function renderAuth(){
  applyTheme();
  document.body.classList.add('auth-body');
  $('#app').innerHTML = `<main class="auth-stage">
    <section class="auth-window auth-single-shell">
      <div class="auth-shell-bg" aria-hidden="true"></div>
      <div class="auth-brand-panel">
        <div class="auth-brand-top">
          <div class="auth-logo-orb"><img src="${logo}" alt="Prismora" class="auth-logo"></div>
          <div><b>Prismora</b><span>AI Visual Studio</span></div>
        </div>
        <div class="auth-copy">
          <p class="eyebrow">Prismora Visual Intelligence</p>
          <h1>Create exceptional visuals with studio-grade intelligence.</h1>
          <p>Develop precise creative direction, generate polished imagery, and perfect every result within one private visual environment.</p>
        </div>
        <div class="auth-feature-strip">
          <span>${icon('wand')} Prompt Intelligence</span>
          <span>${icon('image')} Generative Imaging</span>
          <span>${icon('gear')} Private Creative Suite</span>
        </div>
      </div>
      <form id="authForm" class="auth-form-panel">
        <div class="auth-tabs">
          <button type="button" class="auth-tab ${state.authMode==='login'?'active':''}" data-auth="login">Sign In</button>
          <button type="button" class="auth-tab ${state.authMode==='register'?'active':''}" data-auth="register">Create Account</button>
        </div>
        <div class="auth-form-title">
          <p class="eyebrow">Private Studio Access</p>
          <h2>${state.authMode==='login'?'Welcome to Prismora':'Establish Your Studio'}</h2>
          <p class="form-note">Your creative work and personal preferences remain protected within your private Prismora studio.</p>
        </div>
        ${state.authMode==='register'?`<label class="field"><span>Studio Identity</span><input name="name" required minlength="2" autocomplete="name" placeholder="Muhammad Saad Jadoon"></label>`:''}
        <label class="field"><span>Email</span><input name="email" type="email" required autocomplete="email" placeholder="you@example.com"></label>
        <label class="field"><span>Password</span><input name="password" type="password" required minlength="${state.authMode==='login'?1:8}" autocomplete="${state.authMode==='login'?'current-password':'new-password'}" placeholder="Password"></label>
        <div class="auth-error" id="authErr"></div>
        <button class="primary-btn full" id="authSubmit" type="submit">${state.authMode==='login'?'Open Studio':'Create Studio'}</button>
        ${state.authMode==='login'?`<div class="auth-security-line">
          <span>${icon('shield')} Protected Access</span>
          <span>${icon('sparkles')} Professional Visual Suite</span>
        </div>`:''}
      </form>
    </section>
  </main>`;
  $$('.auth-tab').forEach(btn=>btn.onclick=()=>{state.authMode=btn.dataset.auth; renderAuth();});
  $('#authForm').onsubmit=handleAuth;
}

async function handleAuth(e){
  e.preventDefault();
  const payload=Object.fromEntries(new FormData(e.currentTarget).entries());
  const err=$('#authErr'); err.textContent=''; err.classList.remove('show');
  try{
    await api(state.authMode==='login'?'/api/auth/login':'/api/auth/register',{method:'POST',body:JSON.stringify(payload)});
    const me=await api('/api/auth/me');
    state.user=me.user; state.view=viewFromLocation(); applySettings(me.settings||{}); await loadAll(); render();
  }catch(ex){err.textContent=ex.message || 'Prismora is temporarily unavailable. Please try again.'; err.classList.add('show');}
}

function render(){
  const previousWork=$('#workScroll');
  if(renderedView && previousWork)state.scrollPositions[renderedView]=previousWork.scrollTop;
  const previousSidebar=$('#sidebar');
  if(previousSidebar)state.sidebarScroll=previousSidebar.scrollTop;
  const previousInspector=$('#inspector');
  if(previousInspector)state.inspectorScroll=previousInspector.scrollTop;

  document.body.classList.remove('auth-body');
  applyTheme();
  const showInspector = state.view === 'studio';
  $('#app').innerHTML = `<div class="app-frame ${showInspector?'has-inspector':'no-inspector'} ${state.sidebarOpen?'show-sidebar':''} ${state.inspectorOpen?'show-inspector':''}">
    ${sidebar()}
    <section class="workspace view-${state.view}">
      <button class="icon-button mobile workspace-menu-button" id="menuBtn" type="button" aria-label="Open studio navigation">${icon('menu')}</button>
      <main class="work-scroll" id="workScroll">${renderView()}</main>
      ${state.view==='studio'?composer():''}
    </section>
    ${showInspector?inspector():''}
  </div>${state.refineDialog?refineDialog():''}`;
  renderedView=state.view;
  bind();
  autoGrowTextarea($('#prompt'));
  const pinBottomNow=state.view==='studio' && state.forceStudioBottom;
  if(pinBottomNow){
    pinStudioToBottomInstantly();
    state.forceStudioBottom=false;
    restoreWorkspaceScroll({skipWork:true});
  }else{
    restoreWorkspaceScroll();
  }
  scrollToPendingGeneration();
}
function avatarSmall(){return state.user?.avatar_url?`<img src="${state.user.avatar_url}" alt="">`:`<i>${initials(state.user?.name)}</i>`;}
function sidebar(){
  const nav=[['studio','Create','spark'],['lab','Prompt Studio','flask'],['library','Visual Library','image'],['favorites','Favorites','heart'],['profile','Account','user'],['settings','Settings','gear'],['history','History','history']];
  return `<aside class="sidebar" id="sidebar">
    <div class="brand-card"><img src="${logo}" alt=""><div><b>Prismora</b><span>AI Visual Studio</span></div></div>
    <button class="new-button" id="newThread">${icon('plus')} <span>Create New</span></button>
    <label class="searchbox">${icon('search')}<input id="threadSearch" placeholder="Search creations" value="${escapeAttr(state.search)}"></label>
    <p class="section-label">Creative Suite</p>
    <nav class="nav-list">${nav.map(([v,l,i])=>`<button class="nav-item ${state.view===v?'active':''}" data-view="${v}">${icon(i)}<span>${l}</span></button>`).join('')}</nav>
    <div class="sidebar-footer">
      <button class="sidebar-logout" id="logout" type="button">${icon('logout')}<span>Sign Out</span></button>
      <div class="sidebar-profile">${avatarSmall()}<div><b>${escapeHtml(state.user?.name||'User')}</b><span>${escapeHtml(state.user?.email||'')}</span></div></div>
    </div>
  </aside>`;
}
function inspector(){
  return `<aside class="inspector" id="inspector">
    <div class="panel prompt-panel">
      <p class="eyebrow">Prompt Intelligence</p><h3>Creative Enhancement</h3>
      <p>Transform a concise concept into precise creative direction across composition, lighting, lens, material and atmosphere.</p>
      <button class="primary-btn full" id="enhancePanelBtn" aria-busy="${state.enhancingSidebar?'true':'false'}" ${state.enhancingSidebar?'disabled':''}>${icon('wand')} ${state.enhancingSidebar?'Enhancing…':'Enhance Current Prompt'}</button>
      ${state.enhanced?`<div class="enhanced-preview"><b>Refined Direction</b><p>${escapeHtml(state.enhanced)}</p><div class="enhanced-actions"><button class="primary-btn full" id="useEnhanced">Apply Prompt</button><button class="outline-btn full" id="copyEnhanced">Copy Text</button></div></div>`:''}
    </div>
    <div class="panel"><div class="panel-head"><h3>Visual Direction</h3><span>${activeModeLabel()}</span></div><div class="option-grid modes">${MODES.map(m=>`<button class="option ${state.mode===m[0]?'active':''}" data-mode="${m[0]}"><b>${m[1]}</b><small>${m[2]}</small></button>`).join('')}</div></div>
    <div class="panel"><div class="panel-head"><h3>Creative Finish</h3><span>${title(state.style)}</span></div><div class="option-grid styles">${STYLES.map(s=>`<button class="option compact ${state.style===s[0]?'active':''}" data-style="${s[0]}">${s[1]}</button>`).join('')}</div></div>
    <div class="panel"><div class="panel-head"><h3>Canvas Format</h3><span>${state.ratio}</span></div><div class="ratio-grid">${RATIOS.map(r=>`<button class="ratio-card ${state.ratio===r[0]?'active':''}" data-ratio="${r[0]}"><i data-shape="${r[0].replace(':','-')}"></i><b>${r[0]}</b><small>${r[1]} · ${r[2]}</small></button>`).join('')}</div></div>
    <div class="panel"><div class="form-grid two"><label class="field"><span>Output Resolution</span><select id="resolution">${['auto',resolutionForRatio(state.ratio)].map(r=>`<option value="${r}" ${state.resolution===r?'selected':''}>${r==='auto'?'Automatic':r}</option>`).join('')}</select></label><label class="field"><span>Variations</span><select id="count">${[1,2,3,4].map(n=>`<option value="${n}" ${state.count==n?'selected':''}>${n}</option>`).join('')}</select></label><label class="field"><span>Variation Seed</span><input id="seed" value="${escapeAttr(state.seed)}" placeholder="Automatic"></label><button class="toggle-row" type="button" id="autoEnhance"><span>Intelligent Refinement</span><i class="toggle ${state.autoEnhance?'on':''}"></i></button></div><label class="field"><span>Exclusions</span><textarea id="negative" rows="4" placeholder="unwanted text, artifacts, distorted anatomy, blur">${escapeHtml(state.negative)}</textarea></label></div>
  </aside>`;
}

function renderView(){
  if(state.view==='lab') return labView();
  if(state.view==='library') return libraryView(false);
  if(state.view==='favorites') return libraryView(true);
  if(state.view==='profile') return profileView();
  if(state.view==='settings') return settingsView();
  if(state.view==='history') return historyView();
  if(state.view==='system') return systemView();
  return studioView();
}
function studioView(){
  const gens=state.activeThread?.generations || state.generations.slice(0,4).reverse();
  if(!gens.length && !state.activeThread){
    return `<section class="studio-empty">
      <div class="empty-logo"><img src="${logo}" alt=""></div>
      <p class="eyebrow">Prismora Creation Studio</p>
      <h1>Describe your vision. Prismora shapes the visual.</h1>
      <p>Compose your idea below, then refine its direction, format, finish and output with precision.</p>
      <div class="idea-grid">${IDEA_PROMPTS.map(p=>`<button class="idea-card" data-idea="${escapeAttr(p)}"><b>${escapeHtml(p.split(',')[0])}</b><span>${escapeHtml(p)}</span></button>`).join('')}</div>
    </section>`;
  }
  return `<section class="conversation">
    ${(state.activeThread?threadMessages():gens.map(generationCard).join(''))}
  </section>`;
}
function threadMessages(){
  const gens=state.activeThread.generations || [];
  return gens.map(generationCard).join('');
}
function formatAestheticScore(value){
  return value===null || value===undefined ? '' : Number(value).toFixed(1);
}
function formatSemanticScore(value){
  return value===null || value===undefined ? '' : `${Math.round(Number(value)*100)}%`;
}
function imageQualitySummary(img){
  const metrics=[];
  if(img.aesthetic_score!==null && img.aesthetic_score!==undefined) metrics.push(`<span>Aesthetic ${formatAestheticScore(img.aesthetic_score)}/10</span>`);
  if(img.semantic_score!==null && img.semantic_score!==undefined) metrics.push(`<span>Prompt Match ${formatSemanticScore(img.semantic_score)}</span>`);
  if(Number(img.qa_passed)===1) metrics.push('<span class="verified">Quality Verified</span>');
  else if(img.qa_method==='pixel-quality-fallback') metrics.push('<span>Integrity Verified</span>');
  if(img.moderation_status==='passed') metrics.push('<span class="verified">Safety Verified</span>');
  const warning=img.dimension_warning ? `<p class="dimension-note">${escapeHtml(img.dimension_warning)}</p>` : '';
  return `${metrics.length?`<div class="quality-metrics">${metrics.join('')}</div>`:''}${warning}`;
}
function generationCard(g){
  const imgs=g.images||[];
  const status = generationStatusLabel(g.status||'processing');
  return `<article class="generation-card" id="gen-${g.id}">
    <div class="gen-header"><div><p class="eyebrow">Prismora Creation · ${title(g.mode)} · ${g.aspect_ratio} · ${g.width}×${g.height}</p><h3>${escapeHtml((g.prompt||'Untitled Creation').slice(0,90))}</h3></div><span class="status ${g.status}">${status}</span></div>
    <p class="gen-prompt">${escapeHtml(g.enhanced_prompt || g.prompt || '')}</p>
    ${g.error_message?`<div class="error-box">${escapeHtml(friendlyErrorMessage(g.error_message))}</div>`:''}
    ${imgs.length?`<div class="image-grid ${imgs.length>1?'multi':''}">${imgs.map(img=>`<figure><img src="${imageUrl(img)}" width="${img.width||g.width}" height="${img.height||g.height}" alt="Prismora visual"><figcaption><span>${img.width||g.width}×${img.height||g.height} · ${(img.size_bytes/1024).toFixed(0)}KB</span>${imageQualitySummary(img)}</figcaption></figure>`).join('')}</div>`:''}
    <div class="gen-actions">
      ${imgs[0]?`<a class="outline-btn" href="${imageUrl(imgs[0])}" download>${icon('download')} Download Image</a>`:''}
      <button class="outline-btn" data-copy="${encodeURIComponent(g.enhanced_prompt||g.prompt||'')}">${icon('copy')} Copy Prompt</button>
      <button class="outline-btn" data-refine="${g.id}">${icon('wand')} Refine</button>
      <button class="outline-btn ${g.favorite?'active':''}" data-fav="${g.id}">${icon('heart')} ${g.favorite?'Favorites':'Add to Favorites'}</button>
      <button class="danger-btn" data-delete="${g.id}">${icon('trash')} Remove</button>
    </div>
  </article>`;
}
function composer(){
  return `<section class="composer-shell">
    <div class="composer">
      <div class="composer-chips"><span>${activeModeLabel()}</span><span>${title(state.style)}</span><span>${state.ratio}</span><span>${state.resolution}</span><span>${state.count} variation${state.count>1?'s':''}</span></div>
      <textarea id="prompt" rows="1" placeholder="Describe the visual you want Prismora to create or refine…">${escapeHtml(state.prompt)}</textarea>
      <div class="composer-footer"><span>${state.autoEnhance?'Auto prompt enhancement active':'Manual creative direction'}</span><div><button class="outline-btn" id="inlineEnhanceBtn" aria-busy="${state.enhancingInline?'true':'false'}" ${state.enhancingInline?'disabled':''}>${icon('wand')} ${state.enhancingInline?'Enhancing…':'Enhance Prompt'}</button><button class="primary-btn" id="generateBtn" ${state.busy || state.enhancingInline?'disabled':''}>${state.busy?'Creating…':'Create Image'}</button></div></div>
    </div>
  </section>`;
}
function findGenerationById(id){
  const active=state.activeThread?.generations || [];
  return active.find(g=>Number(g.id)===Number(id)) || state.generations.find(g=>Number(g.id)===Number(id)) || null;
}
function openRefineDialog(id){
  const generation=findGenerationById(id);
  if(!generation)return toast('This creation is not currently available for refinement.');
  state.refineDialog=generation;
  state.refineInstruction='';
  state.refinePreserveSubject=true;
  state.refinePreserveComposition=true;
  state.refineBusy=false;
  render();
  setTimeout(()=>$('#refineInstruction')?.focus({preventScroll:true}),50);
}
function closeRefineDialog(){
  if(state.refineBusy)return;
  state.refineDialog=null;
  state.refineInstruction='';
  render();
}
function refineDialog(){
  const g=state.refineDialog;
  const img=(g?.images||[])[0];
  const quick=['Refine Lighting','Increase Detail','Replace Background','Rebalance Color','Strengthen Composition','Remove Element'];
  return `<div class="modal-backdrop" id="refineBackdrop" role="presentation">
    <section class="refine-dialog" role="dialog" aria-modal="true" aria-labelledby="refineTitle" aria-busy="${state.refineBusy?'true':'false'}">
      <div class="refine-dialog-head"><div><p class="eyebrow">Precision Refinement</p><h2 id="refineTitle">Refine</h2><p>Specify the exact changes you want. Prismora will preserve every detail you leave untouched.</p></div><button class="modal-close" id="closeRefine" type="button" aria-label="Close refinement">×</button></div>
      <div class="refine-dialog-body">
        <div class="refine-source">${img?`<img src="${escapeAttr(imageUrl(img))}" alt="Visual selected for refinement">`:`<div class="image-placeholder">${icon('image')}</div>`}<div><span>Original Visual</span><b>${escapeHtml((g?.prompt||'Prismora Visual').slice(0,100))}</b><small>${title(g?.mode||state.mode)} · ${g?.aspect_ratio||state.ratio}</small></div></div>
        <label class="field"><span>Refinement Direction</span><textarea id="refineInstruction" rows="5" placeholder="Example: Preserve the subject and framing, soften the studio lighting, refine facial detail, and introduce a clean charcoal backdrop.">${escapeHtml(state.refineInstruction)}</textarea></label>
        <div class="refine-quick">${quick.map(item=>`<button type="button" data-refine-chip="${escapeAttr(item)}">${escapeHtml(item)}</button>`).join('')}</div>
        <div class="refine-preserve"><button type="button" id="preserveSubject" class="refine-toggle ${state.refinePreserveSubject?'on':''}"><i></i><span><b>Preserve Subject Identity</b><small>Maintain the same primary subject, defining features and subject count.</small></span></button><button type="button" id="preserveComposition" class="refine-toggle ${state.refinePreserveComposition?'on':''}"><i></i><span><b>Preserve Composition</b><small>Maintain the existing framing and layout unless your direction requires a change.</small></span></button></div>
      </div>
      <div class="refine-dialog-actions"><button class="outline-btn" id="cancelRefineDialog" type="button" ${state.refineBusy?'disabled':''}>Cancel</button><button class="primary-btn" id="submitRefine" type="button" ${state.refineBusy?'disabled':''}>${state.refineBusy?'Refining…':`${icon('wand')} Create Refined Version`}</button></div>
    </section>
  </div>`;
}
async function submitRefinement(){
  const source=state.refineDialog;
  const instruction=($('#refineInstruction')?.value || state.refineInstruction || '').trim();
  if(!source)return;
  if(!instruction)return toast('Add a clear refinement direction before continuing.');
  state.refineInstruction=instruction;
  state.refineBusy=true;
  render();
  const preservation=[];
  if(state.refinePreserveSubject)preservation.push('Preserve the exact subject identity, subject count and defining features.');
  if(state.refinePreserveComposition)preservation.push('Preserve the existing composition and camera framing unless the requested change requires otherwise.');
  const refineInstruction=[instruction,...preservation,'Keep all unspecified visual details unchanged.'].join(' ');
  try{
    const payload={
      prompt:source.enhanced_prompt || source.prompt || instruction,
      negative_prompt:source.negative_prompt || state.negative,
      mode:source.mode || state.mode,
      style:source.style || state.style,
      aspect_ratio:source.aspect_ratio || state.ratio,
      resolution:resolutionForRatio(source.aspect_ratio || state.ratio),
      count:1,
      seed:null,
      auto_enhance:true,
      thread_id:source.thread_id || state.activeThread?.thread?.id || null,
      refine_from_generation_id:source.id,
      refine_instruction:refineInstruction
    };
    const out=await api('/api/generations',{method:'POST',body:JSON.stringify(payload)});
    await loadAll();
    state.activeThread=await api(`/api/threads/${out.thread_id}`);
    state.refineDialog=null;
    state.refineInstruction='';
    state.scrollToGenerationId=out.id;
    toast('Your refined visual is ready.');
  }catch(ex){
    toast(ex.message || 'Prismora could not complete this refinement. Please try again.');
  }finally{
    state.refineBusy=false;
    render();
  }
}

function labView(){
  return `<section class="page prompt-lab-page">
    <div class="page-head lab-head">
      <p class="eyebrow">Prompt Studio</p>
      <h1>Develop precise, production-ready visual direction.</h1>
      <p class="hint">Transform an initial concept into a structured creative specification before image creation.</p>
    </div>
    <div class="lab-layout">
      <div class="panel lab-card lab-input-card">
        <div class="panel-head"><div><p class="eyebrow">Creative Brief</p><h3>Source Concept</h3></div></div>
        <label class="field"><span>Initial Direction</span><textarea id="labPrompt" class="lab-raw" rows="7" placeholder="Describe the core visual concept…">${escapeHtml(state.prompt)}</textarea></label>
        <label class="field"><span>Exclusions</span><textarea id="labNeg" class="lab-negative" rows="4" placeholder="unwanted text, artifacts, distorted anatomy, blur">${escapeHtml(state.negative)}</textarea></label>
        <button class="primary-btn" id="labEnhance" ${state.enhancingLab?'disabled':''}>${icon('wand')} ${state.enhancingLab?'Refining…':'Refine Direction'}</button>
      </div>
      <div class="panel lab-card lab-output-card">
        <div class="panel-head"><div><p class="eyebrow">Refined Direction</p><h3>Production Prompt</h3></div></div>
        <div class="prompt-output">${state.enhanced?escapeHtml(state.enhanced):'Your refined production prompt will appear here, ready for review and image creation.'}</div>
        ${state.enhanced?`<button class="primary-btn full" id="useEnhancedLab">Send to Create</button>`:''}
      </div>
    </div>
  </section>`;
}
function libraryView(favoriteOnly=false){
  const items=state.generations.filter(g=>!favoriteOnly || g.favorite);
  return `<section class="page"><div class="page-head with-action"><div><p class="eyebrow">${favoriteOnly?'Favorites':'Visual Library'}</p><h1>${favoriteOnly?'Curated Selections':'Your Visual Collection'}</h1></div><button class="outline-btn" id="refreshData">Sync Collection</button></div>${items.length?`<div class="library-grid">${items.map(g=>`<button class="library-card" data-thread="${g.thread_id}">${(g.images||[])[0]?`<img src="${imageUrl(g.images[0])}" alt="">`:`<div class="image-placeholder">${icon('image')}</div>`}<div><b>${escapeHtml((g.prompt||'Untitled Creation').slice(0,54))}</b><span>${title(g.mode)} · ${g.aspect_ratio} · ${shortDate(g.created_at)}</span></div></button>`).join('')}</div>`:`<div class="empty-state"><h3>Your collection is ready</h3><p>Create your first visual to begin building a private Prismora collection.</p></div>`}</section>`;
}
function profileView(){
  return `<section class="page profile-page"><div class="page-head"><p class="eyebrow">Account</p><h1>Personal Studio</h1></div><div class="profile-grid">
    <div class="profile-card panel profile-info-card"><div class="profile-top">${state.user?.avatar_url?`<img src="${state.user.avatar_url}" alt="">`:`<div class="avatar-large">${initials(state.user?.name)}</div>`}<div><p class="eyebrow">Studio Identity</p><h2>${escapeHtml(state.user?.name || state.user?.user_uid || 'Prismora Member')}</h2><p>${escapeHtml(state.user?.email||'')}</p></div></div><label class="upload-line"><input type="file" id="avatarFile" accept="image/*">Update Profile Portrait</label><form id="profileForm" class="form-stack"><label class="field"><span>Name</span><input name="name" value="${escapeAttr(state.user?.name||'')}"></label><label class="field"><span>Email</span><input type="email" name="email" value="${escapeAttr(state.user?.email||'')}"></label><button class="primary-btn profile-action">Save Changes</button></form></div>
    <div class="profile-card panel profile-security-card"><p class="eyebrow">Privacy & Security</p><h3>Studio Access</h3><p class="hint">Your identity, active sessions and creative assets remain protected within your private Prismora environment.</p><label class="field"><span>Current password</span><input type="password" autocomplete="current-password" placeholder="Current password" disabled></label><label class="field"><span>New password</span><input type="password" autocomplete="new-password" placeholder="New password" disabled></label><label class="field"><span>Confirm password</span><input type="password" autocomplete="new-password" placeholder="Confirm password" disabled></label><button class="outline-btn full profile-action" type="button" disabled>Update Password</button></div>
  </div></section>`;
}
function settingsView(){
  return `<section class="page settings-page"><div class="page-head"><p class="eyebrow">Settings</p><h1>Studio Preferences</h1><p class="hint">Personalize Prismora’s visual experience and define your preferred creative defaults.</p></div><form id="settingsForm" class="settings-grid">
    <div class="panel settings-card appearance-card"><p class="eyebrow">Interface</p><h3>Visual Experience</h3><label class="field theme-select"><span>Appearance Theme</span><select name="theme"><option ${state.theme==='dark'?'selected':''} value="dark">Dark Prism</option><option ${state.theme==='light'?'selected':''} value="light">Light Prism</option></select></label><button class="toggle-row auto-enhance-row" type="button" id="settingsAuto"><span>Intelligent Prompt Refinement</span><i class="toggle ${state.autoEnhance?'on':''}"></i></button><div class="appearance-status"><div><span>Current Experience</span><b>${state.theme==='dark'?'Dark Prism':'Light Prism'} · ${state.autoEnhance?'Intelligent refinement active':'Manual direction'}</b></div><p>These preferences shape every new creation and maintain a consistent studio experience.</p></div></div>
    <div class="panel settings-card defaults-card"><p class="eyebrow">Creative Defaults</p><h3>Creation Preferences</h3><label class="field"><span>Preferred Visual Mode</span><select name="default_mode">${MODES.map(m=>`<option value="${m[0]}" ${state.mode===m[0]?'selected':''}>${m[1]}</option>`).join('')}</select></label><label class="field"><span>Preferred Finish</span><select name="default_style">${STYLES.map(s=>`<option value="${s[0]}" ${state.style===s[0]?'selected':''}>${s[1]}</option>`).join('')}</select></label><label class="field"><span>Preferred Canvas</span><select name="default_ratio">${RATIOS.map(r=>`<option value="${r[0]}" ${state.ratio===r[0]?'selected':''}>${r[0]} · ${r[1]}</option>`).join('')}</select></label><button class="primary-btn settings-save">Save</button></div>
  </form></section>`;
}
function historyView(){
  const items=state.generations || [];
  return `<section class="page history-page"><div class="page-head with-action"><div><p class="eyebrow">History</p><h1>Creation History</h1><p class="hint">Review every visual together with its original creative direction.</p></div><button class="outline-btn" id="refreshData">Sync Collection</button></div>${items.length?`<div class="history-list">${items.map(g=>{
    const firstImage=(g.images||[])[0];
    return `<article class="history-card"><div class="history-thumb">${firstImage?`<img src="${escapeAttr(imageUrl(firstImage))}" alt="Prismora visual preview">`:`<span class="history-icon">${icon('image')}</span>`}</div><div class="history-copy"><b>${escapeHtml((g.prompt||'Untitled Creation').slice(0,90))}</b><p>${title(g.mode)} · ${g.aspect_ratio} · ${shortDate(g.created_at)}</p></div><div class="history-actions"><button type="button" class="history-action history-open" data-history-open="${g.thread_id}" title="View creation" aria-label="View creation">${icon('open')}<span>View</span></button>${firstImage?`<a class="history-action history-download" href="${escapeAttr(imageUrl(firstImage))}" download="${escapeAttr(historyDownloadName(g,firstImage))}" title="Download visual" aria-label="Download visual">${icon('download')}<span>Download</span></a>`:`<button type="button" class="history-action history-download" disabled title="Visual unavailable" aria-label="Download unavailable">${icon('download')}<span>Download</span></button>`}</div><span class="status ${g.status}">${generationStatusLabel(g.status||'saved')}</span></article>`;
  }).join('')}</div>`:`<div class="empty-state"><h3>Your archive is ready</h3><p>Completed creations will appear here for effortless review and reuse.</p></div>`}</section>`;
}
function systemView(){
  return `<section class="page"><div class="page-head with-action"><div><p class="eyebrow">Studio Services</p><h1>Creative Engine</h1></div><button class="outline-btn" id="healthBtn">Review Service Status</button></div><div class="system-grid"><div class="panel"><b>01 · Creative Direction</b><p>Your concept, exclusions, format, finish and output preferences are composed into one precise visual brief.</p></div><div class="panel"><b>02 · Generative Engine</b><p>Prismora coordinates image creation with resilient processing for a dependable studio experience.</p></div><div class="panel"><b>03 · Image Preparation</b><p>Every visual is validated, prepared and optimized before entering your private collection.</p></div><div class="panel"><b>04 · Private Studio</b><p>Your account, creations, curated selections and preferences remain organized within your private Prismora environment.</p></div></div></section>`;
}

function bind(){
  $('#menuBtn')?.addEventListener('click',()=>{state.sidebarOpen=!state.sidebarOpen; render();});
  $('#inspectorBtn')?.addEventListener('click',()=>{state.inspectorOpen=!state.inspectorOpen; render();});
  $('#themeBtn')?.addEventListener('click',toggleTheme);
  $('#logout')?.addEventListener('click',async()=>{await api('/api/auth/logout',{method:'POST'}); state.user=null; renderAuth();});
  $$('[data-view]').forEach(b=>b.onclick=()=>navigateView(b.dataset.view));
  $('#newThread')?.addEventListener('click',()=>{state.activeThread=null; state.prompt=''; state.enhanced=''; state.refineFrom=null; state.refineDialog=null; state.refineInstruction=''; state.forceStudioBottom=true; navigateView('studio'); focusComposer();});
  $('#threadSearch')?.addEventListener('input',e=>{state.search=e.target.value;});
  $$('[data-thread]').forEach(b=>b.onclick=()=>openThread(Number(b.dataset.thread)));
  $$('[data-history-open]').forEach(b=>b.onclick=()=>openThread(Number(b.dataset.historyOpen)));
  $$('[data-idea]').forEach(b=>b.onclick=()=>{state.prompt=b.dataset.idea; render();});
  $('#prompt')?.addEventListener('input',e=>{state.prompt=e.target.value; autoGrowTextarea(e.target);});
  $('#negative')?.addEventListener('input',e=>{state.negative=e.target.value;});
  $('#resolution')?.addEventListener('change',e=>{state.resolution=e.target.value;});
  $('#count')?.addEventListener('change',e=>{state.count=Number(e.target.value);});
  $('#seed')?.addEventListener('input',e=>{state.seed=e.target.value;});
  $$('.option[data-mode]').forEach(b=>b.onclick=()=>{state.mode=b.dataset.mode; render();});
  $$('.option[data-style]').forEach(b=>b.onclick=()=>{state.style=b.dataset.style; render();});
  $$('.ratio-card').forEach(b=>b.onclick=()=>{state.ratio=b.dataset.ratio; state.resolution='auto'; render();});
  $('#autoEnhance')?.addEventListener('click',()=>{state.autoEnhance=!state.autoEnhance; render();});
  $('#settingsAuto')?.addEventListener('click',()=>{state.autoEnhance=!state.autoEnhance; render();});
  $('#inlineEnhanceBtn')?.addEventListener('click',handleInlineEnhance);
  $('#enhancePanelBtn')?.addEventListener('click',handleSidebarEnhance);
  $('#generateBtn')?.addEventListener('click',generateImage);
  $('#useEnhanced')?.addEventListener('click',handleUseSidebarSuggestion);
  $('#copyEnhanced')?.addEventListener('click',()=>navigator.clipboard?.writeText(state.enhanced||'').then(()=>toast('Refined prompt copied to your clipboard.')));
  $('#labPrompt')?.addEventListener('input',e=>{state.prompt=e.target.value;});
  $('#labNeg')?.addEventListener('input',e=>{state.negative=e.target.value;});
  $('#labEnhance')?.addEventListener('click',handleLabEnhance);
  $('#useEnhancedLab')?.addEventListener('click',()=>{state.prompt=state.enhanced; state.enhanced=''; navigateView('studio'); focusComposer();});
  $$('[data-copy]').forEach(b=>b.onclick=()=>navigator.clipboard?.writeText(decodeURIComponent(b.dataset.copy)).then(()=>toast('Creative direction copied to your clipboard.')));
  $$('[data-refine]').forEach(b=>b.onclick=()=>openRefineDialog(Number(b.dataset.refine)));
  $('#refineInstruction')?.addEventListener('input',e=>{state.refineInstruction=e.target.value;});
  $$('[data-refine-chip]').forEach(b=>b.onclick=()=>{
    const el=$('#refineInstruction');
    const addition=b.dataset.refineChip;
    const current=(el?.value || state.refineInstruction || '').trim();
    state.refineInstruction=current?`${current}${/[.!?]$/.test(current)?'':' .' } ${addition}.`.replace(' .','.'): `${addition}.`;
    if(el){el.value=state.refineInstruction;el.focus();}
  });
  $('#preserveSubject')?.addEventListener('click',()=>{state.refinePreserveSubject=!state.refinePreserveSubject;render();});
  $('#preserveComposition')?.addEventListener('click',()=>{state.refinePreserveComposition=!state.refinePreserveComposition;render();});
  $('#closeRefine')?.addEventListener('click',closeRefineDialog);
  $('#cancelRefineDialog')?.addEventListener('click',closeRefineDialog);
  $('#refineBackdrop')?.addEventListener('click',e=>{if(e.target.id==='refineBackdrop')closeRefineDialog();});
  $('#submitRefine')?.addEventListener('click',submitRefinement);
  $$('[data-fav]').forEach(b=>b.onclick=async()=>{await api(`/api/generations/${b.dataset.fav}/favorite`,{method:'POST'}); await refreshAfterAction();});
  $$('[data-delete]').forEach(b=>b.onclick=async()=>{if(confirm('Remove this creation from your collection?')){await api(`/api/generations/${b.dataset.delete}`,{method:'DELETE'}); await refreshAfterAction();}});
  $('#refreshData')?.addEventListener('click',async()=>{await loadAll(); render(); toast('Your collection is synchronized.');});
  $('#profileForm')?.addEventListener('submit',saveProfile);
  $('#avatarFile')?.addEventListener('change',uploadAvatar);
  $('#settingsForm')?.addEventListener('submit',saveSettings);
  $('#healthBtn')?.addEventListener('click',async()=>{const h=await api('/api/health'); toast(`Studio services online · Prompt intelligence ${h.gemini_configured?'available':'requires setup'} · Image engine ${h.cloudflare_configured?'available':'requires setup'}`);});
}
async function toggleTheme(){
  state.theme = state.theme==='dark'?'light':'dark'; applyTheme();
  try{await api('/api/settings',{method:'PUT',body:JSON.stringify({theme:state.theme, default_mode:state.mode, default_ratio:state.ratio, default_style:state.style, auto_enhance:state.autoEnhance})});}catch{}
  render();
}
async function refreshAfterAction(){
  await loadAll();
  if(state.activeThread?.thread?.id){try{state.activeThread=await api(`/api/threads/${state.activeThread.thread.id}`);}catch{state.activeThread=null;}}
  render();
}
async function openThread(id){
  state.activeThread=await api(`/api/threads/${id}`);
  state.forceStudioBottom=true;
  navigateView('studio');
}
async function requestEnhancedPrompt(prompt, sourceContext=''){
  const out=await api('/api/prompt/enhance',{method:'POST',body:JSON.stringify({prompt, mode:state.mode, style:state.style, aspect_ratio:state.ratio, negative_prompt:state.negative, source_context:sourceContext})});
  return cleanEnhancedPrompt(out.enhanced_prompt || prompt);
}
async function handleInlineEnhance(){
  const sourcePrompt=getComposerPrompt();
  if(!sourcePrompt) return toast('Add a creative direction before continuing.');
  const requestId=++state.enhanceRequestId;
  state.prompt=sourcePrompt; state.enhancingInline=true; render(); focusComposer();
  try{
    const result=await requestEnhancedPrompt(sourcePrompt, state.refineFrom?`Refining generation ${state.refineFrom}`:'');
    if(requestId!==state.enhanceRequestId) return;
    if((state.prompt || '').trim() !== sourcePrompt){
      state.enhanced=result;
      toast('A refined direction is ready for review. Your original prompt remains unchanged.');
    }else{
      state.prompt=result;
      state.enhanced='';
      toast('Your prompt has been refined and is ready for review.');
    }
  }catch(ex){
    toast('Prompt refinement is temporarily unavailable. Your original direction remains unchanged.');
  }finally{
    if(requestId===state.enhanceRequestId){state.enhancingInline=false; render(); focusComposer();}
  }
}
async function handleSidebarEnhance(){
  const sourcePrompt=getComposerPrompt();
  if(!sourcePrompt) return toast('Add a creative direction before continuing.');
  const requestId=++state.enhanceRequestId;
  state.enhancingSidebar=true; render();
  try{
    const result=await requestEnhancedPrompt(sourcePrompt, state.refineFrom?`Refining generation ${state.refineFrom}`:'');
    if(requestId!==state.enhanceRequestId) return;
    state.enhanced=result;
    toast('Your refined direction is ready.');
  }catch(ex){
    toast('Prompt refinement is temporarily unavailable. Your original direction remains unchanged.');
  }finally{
    if(requestId===state.enhanceRequestId){state.enhancingSidebar=false; render();}
  }
}
function handleUseSidebarSuggestion(){
  if(!state.enhanced) return;
  state.prompt=state.enhanced;
  state.enhanced='';
  navigateView('studio');
  focusComposer();
}
async function handleLabEnhance(){
  const prompt=($('#labPrompt')?.value || state.prompt || '').trim();
  if(!prompt) return toast('Add a creative direction before continuing.');
  state.prompt=prompt; state.enhancingLab=true;
  try{
    state.enhanced=await requestEnhancedPrompt(prompt, 'Prompt Lab enhancement');
    render();
    toast('Your prompt has been refined.');
  }catch(ex){toast('Prompt refinement is temporarily unavailable. Your original direction remains unchanged.');}
  finally{state.enhancingLab=false;}
}
async function generateImage(){
  const prompt=($('#prompt')?.value || state.prompt || '').trim();
  if(!prompt) return toast('Add a creative direction before continuing.');
  state.prompt=prompt; state.busy=true; render();
  try{
    const payload={prompt:state.prompt, negative_prompt:state.negative, mode:state.mode, style:state.style, aspect_ratio:state.ratio, resolution:state.resolution, count:state.count, seed:state.seed?Number(state.seed):null, auto_enhance:state.autoEnhance, thread_id:state.activeThread?.thread?.id || null, refine_from_generation_id:state.refineFrom || null, refine_instruction:state.refineFrom ? state.prompt : ''};
    const out=await api('/api/generations',{method:'POST',body:JSON.stringify(payload)});
    await loadAll(); state.activeThread=await api(`/api/threads/${out.thread_id}`); state.prompt=''; state.enhanced=''; state.refineFrom=null; toast('Your creation is ready.');
  }catch(ex){toast(ex.message);} finally{state.busy=false; render();}
}
async function saveProfile(e){
  e.preventDefault();
  try{const payload=Object.fromEntries(new FormData(e.currentTarget).entries()); const out=await api('/api/profile',{method:'PUT',body:JSON.stringify(payload)}); state.user=out.user; toast('Your profile has been updated.'); render();}catch(ex){toast(ex.message);}
}
async function uploadAvatar(e){
  const file=e.target.files?.[0]; if(!file)return;
  const fd=new FormData(); fd.append('file',file);
  try{await apiForm('/api/profile/avatar',fd); const me=await api('/api/auth/me'); state.user=me.user; toast('Your profile portrait has been updated.'); render();}catch(ex){toast(ex.message);}
}
async function saveSettings(e){
  e.preventDefault();
  const fd=Object.fromEntries(new FormData(e.currentTarget).entries());
  try{const out=await api('/api/settings',{method:'PUT',body:JSON.stringify({theme:fd.theme, default_mode:fd.default_mode, default_ratio:fd.default_ratio, default_style:fd.default_style, auto_enhance:state.autoEnhance})}); applySettings(out); toast('Your studio preferences have been saved.'); render();}catch(ex){toast(ex.message);}
}
function toast(msg){
  const message=friendlyErrorMessage(msg);
  const root=$('#toastRoot'); if(!root)return alert(message);
  const t=document.createElement('div');
  t.className='toast';
  if(/respectful, safe visual creation|cannot produce explicit/i.test(message)) t.classList.add('toast-warning');
  t.textContent=message;
  root.appendChild(t);
  setTimeout(()=>t.remove(),4600);
}
function handleBrowserNavigation(){
  const next=viewFromLocation();
  if(next===state.view)return;
  state.view=next;
  state.sidebarOpen=false;
  render();
}
window.addEventListener('popstate',handleBrowserNavigation);
window.addEventListener('hashchange',handleBrowserNavigation);
window.addEventListener('keydown',e=>{if(e.key==='Escape' && state.refineDialog)closeRefineDialog();});
boot();
