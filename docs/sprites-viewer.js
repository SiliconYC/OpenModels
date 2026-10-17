// Pure 2D PNG player: no Three.js, no per-vehicle code and no arbitrary asset URLs.
const $ = id => document.getElementById(id);
const canvas = $('sprite-canvas'), ctx = canvas.getContext('2d', { alpha: true });
const controls = ['previous','next','play'];
const state = { catalog: [], manifest: null, asset: null, level: 16, size: 128,
  slot: 0, playing: false, lastTick: 0, frame: null, pending: 0, animation: 0,
  cache: new Map(), dragging: false, dragX: 0, dragTravel: 0, error: '' };
const safeId = value => typeof value === 'string' && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value) && value.length <= 64;
const own = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key);
const expectedSlots = level => Array.from({length: level}, (_, i) => i * (64 / level));
const pngName = slot => 'frames/' + String(slot).padStart(3,'0') + '.png';
function fail(reason) {
  state.playing = false; cancelAnimationFrame(state.animation); state.error = reason;
  $('failure').textContent = reason; $('failure').hidden = false;
  $('load-state').textContent = '加载失败'; syncControls();
}
function clearFailure() { state.error = ''; $('failure').hidden = true; $('failure').textContent = ''; }
function validCatalog(value) {
  if (!value || value.schema_version !== 1 || !Array.isArray(value.assets) || !value.assets.length) throw Error('目录结构或版本无效');
  const seen = new Set();
  for (const a of value.assets) {
    if (!safeId(a.asset_id) || !safeId(a.variant) || !['fixture','approved','planned'].includes(a.release_status) || typeof a.title !== 'string') throw Error('目录资产字段非法');
    const id = a.asset_id + '/' + a.variant;
    if (seen.has(id)) throw Error('目录资产重复'); seen.add(id);
    if (a.release_status !== 'planned' && a.manifest !== 'assets/sprites/' + id + '/manifest.json') throw Error('manifest 路径不受信任');
    if (a.release_status === 'planned' && own(a,'manifest')) throw Error('未发布资产不能指定可播放 manifest');
  }
  return value.assets;
}
function validManifest(m, entry) {
  if (!m || m.schema_version !== 1 || m.asset_id !== entry.asset_id || m.variant !== entry.variant ||
      m.release_status !== entry.release_status || m.heading_slots !== 64 || m.degrees_per_slot !== 5.625 ||
      !['fixture','approved'].includes(m.release_status)) throw Error('manifest 版本、资产身份或方向契约不匹配');
  const c = m.canvas;
  if (!c || !Number.isInteger(c.width) || !Number.isInteger(c.height) ||
      c.width < 16 || c.height < 16 || c.width > 4096 || c.height > 4096 ||
      c.alpha !== 'straight' || c.color_space !== 'sRGB' ||
      !Array.isArray(m.pivot_px) || m.pivot_px.length !== 2 ||
      !m.pivot_px.every((v,i) => Number.isInteger(v) && v >= 0 && v < (i===0 ? c.width : c.height))) throw Error('canvas 或 pivot 非法');
  if (!Array.isArray(m.available_levels) || !m.available_levels.length ||
      !m.available_levels.every(l => [16,32,64].includes(l)) ||
      new Set(m.available_levels).size !== m.available_levels.length ||
      !m.frames || Array.isArray(m.frames) || typeof m.frames !== 'object') throw Error('方向档位或帧映射非法');
  for (const [key,value] of Object.entries(m.frames)) {
    if (!/^(0[0-5][0-9]|06[0-3])$/.test(key) || value !== 'frames/' + key + '.png') throw Error('帧编号或路径不合法: ' + key);
  }
  for (const level of m.available_levels)
    if (!expectedSlots(level).every(slot => own(m.frames,String(slot).padStart(3,'0')) && m.frames[String(slot).padStart(3,'0')] === pngName(slot)))
      throw Error(level + ' 向不完整，拒绝标记为可用');
  return m;
}
function checkedURL(path, base = document.baseURI) {
  if (typeof path !== 'string' || !/^[a-zA-Z0-9_./-]+$/.test(path) || path.startsWith('/') || path.split('/').includes('..') || path.includes('//')) throw Error('不安全的资源路径');
  const url = new URL(path, base), baseURL = new URL('.', base);
  if (url.origin !== baseURL.origin || !url.pathname.startsWith(baseURL.pathname)) throw Error('资源超出 Pages 目录');
  return url.href;
}
async function jsonFrom(path, base = document.baseURI) {
  const response = await fetch(checkedURL(path, base), {cache:'no-cache',redirect:'error'});
  if (!response.ok) throw Error(path + ' HTTP ' + response.status);
  return response.json();
}
function frameURL(slot) {
  const path = state.manifest.frames[String(slot).padStart(3,'0')];
  return checkedURL(path, checkedURL(state.asset.manifest));
}
function imageFor(slot) {
  if (state.cache.has(slot)) return state.cache.get(slot);
  const p = new Promise((resolve,reject) => {
    const img = new Image();
    img.onload = async () => {
      try {
        if (img.naturalWidth !== state.manifest.canvas.width || img.naturalHeight !== state.manifest.canvas.height) throw Error('PNG 尺寸与 manifest 不符');
        if (img.decode) await img.decode();
        resolve(img);
      } catch(e){reject(e);}
    };
    img.onerror = () => reject(Error(String(slot).padStart(3,'0') + '.png 资源 404、缺帧或损坏'));
    img.src = frameURL(slot);
  });
  state.cache.set(slot,p);
  // Failed promises must not masquerade as permanent successfully decoded frames.
  p.catch(()=>state.cache.delete(slot));
  return p;
}
function draw() {
  ctx.clearRect(0,0,canvas.width,canvas.height);
  if (!state.frame || !state.manifest) return;
  const m = state.manifest, scale = state.size / m.canvas.width;
  ctx.imageSmoothingEnabled = false;
  // Stable coordinate origin: all frames use the SAME logical pivot (260,260).
  ctx.drawImage(state.frame, 260 - m.pivot_px[0] * scale, 260 - m.pivot_px[1] * scale,
    m.canvas.width * scale, m.canvas.height * scale);
}
function syncControls() {
  for (const name of controls) $(name).disabled = !state.manifest || !!state.error;
  $('play').textContent = state.playing ? '暂停旋转' : '自动旋转';
  $('play').setAttribute('aria-pressed', String(state.playing));
  for (const button of document.querySelectorAll('[data-level]')) {
    const level = Number(button.dataset.level);
    button.disabled = !state.manifest?.available_levels.includes(level);
    button.classList.toggle('active', level === state.level && !button.disabled);
    button.setAttribute('aria-pressed',String(button.classList.contains('active')));
  }
  for (const button of document.querySelectorAll('[data-size]')) {
    const on = Number(button.dataset.size) === state.size;
    button.classList.toggle('active',on); button.setAttribute('aria-pressed',String(on));
  }
  $('frame-readout').textContent = state.manifest ?
    '槽 ' + String(state.slot).padStart(3,'0') + ' / 063 · ' + (state.slot * 5.625).toFixed(3).replace(/0+$/,'').replace(/\.$/,'') + '° · ' + state.level + ' 向' :
    '槽 — / 角度 —';
}
async function show(slot) {
  if (!state.manifest || state.error) return;
  const step = 64 / state.level;
  state.slot = ((Math.round(slot / step) * step) % 64 + 64) % 64;
  const seq = ++state.pending, asset = state.asset;
  syncControls(); $('load-state').textContent = '加载帧…';
  try {
    const img = await imageFor(state.slot);
    if (seq !== state.pending || asset !== state.asset) return;
    state.frame = img; draw(); $('load-state').textContent = '已加载真实 PNG';
    // Only immediate neighbours; avoid decoding a full high-resolution 64-frame set.
    const next = (state.slot + step) % 64, prev = (state.slot + 64 - step) % 64;
    imageFor(next).catch(()=>{}); imageFor(prev).catch(()=>{});
  } catch(error) { if(seq === state.pending) fail('帧加载失败：' + (error.message || String(error))); }
}
function pause() {state.playing=false;cancelAnimationFrame(state.animation);syncControls();}
function tick(now) {
  if (!state.playing) return;
  if (now - state.lastTick >= 120) {state.lastTick=now;show(state.slot+64/state.level);}
  state.animation=requestAnimationFrame(tick);
}
async function loadAsset(entry, requestedLevel, requestedHeading) {
  pause(); clearFailure(); ++state.pending; state.cache.clear(); state.frame=null; state.manifest=null; state.asset=entry; draw(); syncControls();
  $('load-state').textContent = '读取 manifest…';
  try {
    const manifest = validManifest(await jsonFrom(entry.manifest),entry);
    state.manifest=manifest;
    state.level=manifest.available_levels.includes(requestedLevel) ? requestedLevel : manifest.available_levels[0];
    state.slot=Number.isInteger(requestedHeading) && requestedHeading>=0 && requestedHeading<64 ? requestedHeading : 0;
    $('asset-status').textContent = entry.release_status === 'fixture' ? '程序化测试夹具 · 非正式美术 · ' + manifest.available_levels.join(' / ') + ' 向' : '正式已批准资产';
    $('asset-select').value=entry.asset_id+'/'+entry.variant;
    syncControls(); await show(state.slot); updateURL();
  }catch(error){fail('资产初始化失败：' +(error.message||String(error)));}
}
function updateURL() {
  if (!state.asset || state.error) return;
  const p=new URLSearchParams({asset:state.asset.asset_id,variant:state.asset.variant,level:String(state.level),heading:String(state.slot)});
  history.replaceState(null,'','?'+p);
}
function move(delta) {pause();show(state.slot + delta * 64 / state.level);updateURL();}
$('previous').addEventListener('click',()=>move(-1));
$('next').addEventListener('click',()=>move(1));
$('play').addEventListener('click',()=>{
  if(state.playing) return pause();
  if(!state.manifest||state.error)return;
  state.playing=true;state.lastTick=performance.now();syncControls();state.animation=requestAnimationFrame(tick);
});
document.querySelectorAll('[data-level]').forEach(button=>button.addEventListener('click',()=>{
  const level=Number(button.dataset.level);
  if(!state.manifest?.available_levels.includes(level))return;
  pause();state.level=level;state.cache.clear();show(state.slot);updateURL();
}));
document.querySelectorAll('[data-size]').forEach(button=>button.addEventListener('click',()=>{
  state.size=Number(button.dataset.size);draw();syncControls();
}));
$('checker').addEventListener('change',event=>$('canvas-holder').classList.toggle('checkered',event.target.checked));
canvas.addEventListener('pointerdown',event=>{if(!state.manifest||state.error)return;pause();state.dragging=true;state.dragX=event.clientX;state.dragTravel=0;canvas.setPointerCapture(event.pointerId);});
canvas.addEventListener('pointermove',event=>{
  if(!state.dragging)return;
  state.dragTravel+=event.clientX-state.dragX;state.dragX=event.clientX;
  const steps=Math.trunc(state.dragTravel / 20);
  if(steps){state.dragTravel-=steps*20;show(state.slot+steps*(64/state.level));updateURL();}
});
function release(){state.dragging=false;state.dragTravel=0;}
canvas.addEventListener('pointerup',release);canvas.addEventListener('pointercancel',release);canvas.addEventListener('lostpointercapture',release);
$('asset-select').addEventListener('change',()=>{
  const entry=state.catalog.find(a=>a.asset_id+'/'+a.variant===$('asset-select').value);
  if(entry&&entry.release_status!=='planned') loadAsset(entry,16,0);
});
window.__spriteViewerStatus=()=>({asset:state.asset?.asset_id,slot:state.slot,level:state.level,size:state.size,loaded:!!state.frame,error:state.error,playing:state.playing,pivot:state.manifest?.pivot_px,available_levels:state.manifest?.available_levels});
(async function init(){
  try{
    const assets=validCatalog(await jsonFrom('sprites-catalog.json'));
    state.catalog=assets;
    const selector=$('asset-select');
    selector.replaceChildren(...assets.map(a=>{
      const option=document.createElement('option');option.value=a.asset_id+'/'+a.variant;option.textContent=a.title+(a.release_status==='fixture'?' · 测试夹具':a.release_status==='planned'?' · 尚未发布':'');option.disabled=a.release_status==='planned';return option;
    }));
    const params=new URLSearchParams(location.search);
    const requested=params.get('asset'), variant=params.get('variant');
    let entry=assets.find(a=>a.asset_id===requested&&a.variant===variant);
    if(requested&&!entry)throw Error('未知资产 ID 或 variant，不允许拼接任意资源地址');
    if(entry?.release_status==='planned')throw Error('该资产尚未发布');
    entry ||= assets.find(a=>a.release_status!=='planned');
    if(!entry)throw Error('目前没有可播放资源');
    await loadAsset(entry,Number(params.get('level')),Number(params.get('heading')));
  }catch(error){fail('目录加载失败：'+(error.message||String(error)));}
})();