import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const stage = document.getElementById('stage');
const select = document.getElementById('model-select');
const title = document.getElementById('model-title');
const metrics = document.getElementById('model-metrics');
const loadState = document.getElementById('load-state');
const failure = document.getElementById('failure');
const kind = document.getElementById('model-kind');
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
stage.append(renderer.domElement);
const scene = new THREE.Scene();
scene.add(new THREE.AmbientLight(0xffffff, 1.7));
const key = new THREE.DirectionalLight(0xffffff, 2.4);
key.position.set(5, 10, 8);
scene.add(key);
const camera = new THREE.OrthographicCamera(-4, 4, 4, -4, .02, 4000);
camera.position.set(4, 3, -5);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = .07;
controls.enablePan = true;
controls.screenSpacePanning = true;
controls.minZoom = .2;
controls.maxZoom = 20;
controls.mouseButtons.LEFT = THREE.MOUSE.ROTATE;
controls.mouseButtons.MIDDLE = THREE.MOUSE.DOLLY;
controls.mouseButtons.RIGHT = THREE.MOUSE.PAN;
const loader = new GLTFLoader();
let models = [], current = null, root = null, framing = { center: new THREE.Vector3(), radius: 1.8 };
let shading = 'textured', wireframe = false, activeView = 'iso', requestSerial = 0;
let temporary = [], loadCount = 0;
const element = (id) => document.getElementById(id);
function setStatus(message) { loadState.textContent = message; }
function reportError(message) {
  failure.hidden = false;
  failure.textContent = message;
  setStatus('加载失败');
}
function clearError() { failure.hidden = true; failure.textContent = ''; }
function toggleGroup(selector, field, value) {
  for (const button of document.querySelectorAll(selector)) {
    const active = button.dataset[field] === value;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  }
}
function bounds() {
  if (!root) return;
  root.updateWorldMatrix(true, true);
  const box = new THREE.Box3().setFromObject(root);
  const dimensions = box.getSize(new THREE.Vector3());
  framing.center = box.getCenter(new THREE.Vector3());
  framing.radius = Math.max(dimensions.length() * .75, .75);
}
function resize() {
  const w = Math.max(stage.clientWidth, 1), h = Math.max(stage.clientHeight, 1);
  renderer.setSize(w, h, false);
  const visibleHeight = Math.max(framing.radius * 3.0, 1.5);
  camera.left = -visibleHeight * w / h / 2;
  camera.right = visibleHeight * w / h / 2;
  camera.top = visibleHeight / 2;
  camera.bottom = -visibleHeight / 2;
  camera.updateProjectionMatrix();
}
function setView(view) {
  activeView = view;
  toggleGroup('[data-view]', 'view', view);
  const dirs = {
    iso: [1.0, .85, -1.25],
    front: [1, 0, 0],
    left: [0, 0, -1],
    top: [0, 1, 0]
  };
  const dir = new THREE.Vector3(...dirs[view]).normalize();
  const centre = framing.center;
  controls.target.copy(centre);
  camera.up.set(...(view === 'top' ? [1, 0, 0] : [0, 1, 0]));
  camera.position.copy(centre).addScaledVector(dir, framing.radius * 4);
  camera.zoom = 1;
  camera.lookAt(centre);
  camera.updateProjectionMatrix();
  controls.update();
}
function materialsFor(original) {
  const originals = Array.isArray(original) ? original : [original];
  const mapped = originals.map(material => {
    const next = shading === 'clay'
      ? new THREE.MeshStandardMaterial({ color: 0xc3c9be, metalness: 0.03, roughness: .85 })
      : material.clone();
    next.wireframe = wireframe;
    temporary.push(next);
    return next;
  });
  return Array.isArray(original) ? mapped : mapped[0];
}
function appearance() {
  if (!root) return;
  for (const value of temporary) value.dispose();
  temporary = [];
  root.traverse(obj => {
    if (obj.isMesh) {
      obj.material = materialsFor(obj.userData.sourceMaterial);
    }
  });
  toggleGroup('[data-shading]', 'shading', shading);
  element('wire').classList.toggle('active', wireframe);
  element('wire').setAttribute('aria-pressed', String(wireframe));
}
function statistics(object) {
  let tris = 0, verts = 0, meshCount = 0;
  const textures = new Set();
  object.traverse(obj => {
    if (!obj.isMesh || !obj.geometry) return;
    meshCount++;
    const g = obj.geometry;
    const vertex = g.getAttribute('position');
    if (!vertex) return;
    verts += vertex.count;
    tris += (g.index ? g.index.count : vertex.count) / 3;
    const orig = obj.userData.sourceMaterial;
    for (const m of (Array.isArray(orig) ? orig : [orig])) {
      if (m?.map) textures.add(m.map.uuid);
    }
  });
  return { tris, verts, meshCount, textureCount: textures.size };
}
function disposeCurrent() {
  for (const m of temporary) m.dispose();
  temporary = [];
  if (!root) return;
  scene.remove(root);
  root.traverse(obj => {
    if (obj.isMesh) {
      obj.geometry?.dispose();
      const orig = obj.userData.sourceMaterial;
      for (const material of Array.isArray(orig) ? orig : [orig]) {
        material?.map?.dispose();
        material?.dispose();
      }
    }
  });
  root = null;
}
async function loadModel(id) {
  const entry = models.find(item => item.id === id);
  if (!entry) { reportError('模型编号不在索引中：' + id); return; }
  current = entry;
  const serial = ++requestSerial;
  setStatus('读取 GLB…');
  clearError();
  try {
    // Always resolve model assets relative to docs/, never to site origin.
    const path = new URL(entry.file, document.baseURI).href;
    const gltf = await loader.loadAsync(path);
    if (serial !== requestSerial) return;
    disposeCurrent();
    root = gltf.scene;
    root.traverse(obj => {
      if (obj.isMesh) obj.userData.sourceMaterial = obj.material;
    });
    scene.add(root);
    bounds();
    resize();
    const actual = statistics(root);
    if (!actual.meshCount || !actual.tris) throw new Error('GLB 中没有有效的三角网格');
    title.textContent = entry.title;
    kind.textContent = entry.stage === 'pipeline-test' ? '工程测试模型' : entry.category || '三维资产';
    metrics.textContent = `${actual.tris.toLocaleString()} 三角面 · ${actual.verts.toLocaleString()} 顶点 · ${actual.textureCount} 贴图 · ${actual.meshCount} 网格`;
    select.value = id;
    history.replaceState(null, '', '?model=' + encodeURIComponent(id));
    appearance();
    setView('iso');
    setStatus('已加载真实 GLB');
  } catch (error) {
    if (serial === requestSerial) reportError('无法加载真实三维模型。\n' + (error?.message || String(error)) + '\n请检查 GLB 资源、浏览器 WebGL 和网络。');
  }
}
document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
  if (root) setView(button.dataset.view);
}));
document.querySelectorAll('[data-shading]').forEach(button => button.addEventListener('click', () => {
  shading = button.dataset.shading;
  appearance();
}));
element('wire').addEventListener('click', () => { wireframe = !wireframe; appearance(); });
element('reset').addEventListener('click', () => { if (root) setView('iso'); });
select.addEventListener('change', () => loadModel(select.value));
new ResizeObserver(resize).observe(stage);
resize();
renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });
(async function init() {
  try {
    const r = await fetch(new URL('./models.json', document.baseURI), { cache: 'no-cache' });
    if (!r.ok) throw new Error('模型索引 HTTP ' + r.status);
    const data = await r.json();
    models = data.models || [];
    if (!models.length) throw new Error('模型索引为空');
    const params = new URLSearchParams(location.search);
    const modelId = params.get('model') || models[0].id;
    select.replaceChildren(...models.map(item => {
      const option = document.createElement('option');
      option.value = item.id;
      option.textContent = item.title;
      return option;
    }));
    if (!models.some(item => item.id === modelId)) throw new Error('未知模型 ID: ' + modelId);
    await loadModel(modelId);
  } catch (error) {
    reportError('展厅初始化失败：' + (error?.message || error));
  }
})();
