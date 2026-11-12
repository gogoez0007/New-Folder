/**
 * Modular Real-Object 3D Geometry & Knowledge Renderer (`assets/three/object_library.js`).
 *
 * Driven cleanly by `core/object_knowledge_core.py` (`OBJECT_KNOWLEDGE_BASE` recipes):
 * - Cumulus Clouds: Soft layered fluffy white cotton puffs on a flat cloud shelf (zero rock faceted GLBs!)
 * - Latex Balloons: Genuine `LatheGeometry` teardrop profile, pinched neck, tied knot & curved S-tube ribbon string
 * - Commercial Jetliners: Contoured fuselage, cockpit glass, window stripe, swept wings with winglets, twin turbines & tail fin
 * - Hydraulic Lift Chairs: Two-stage telescoping chrome cylinder, foot pump pedal & extra-wide armchair (zero arm clipping!)
 * - Golden Skyscrapers: Stepped art-deco towers, crown parapets, roof spires & glowing grid facades
 * - Tropical Giant Leaf: Heart-lobed extruded leaf blade, central midrib & angled lateral veins
 * - Hollow Ancient Oak: Root buttress flare, bark-rimmed dark hollow doorway & lush billowing foliage crown
 * - Pinched Sausage Links: Curved glossy linked sausage chain atop a contoured ceramic rimmed plate
 * - Stylized Forest Trees: Forked organic trunks + multi-puff canopy crowns (zero torn UV trunks)
 * - Generic Composite Builder: Assembles any new/extensible `composite_parts` recipe declared in Python!
 */

import * as THREE from 'three';
import { GENERATED_OBJECT_BUILDERS } from './generated/custom_objects.js';

function createSkyscraperFacadeTex(baseCol, winCol, cols = 6, rows = 14) {
  const c = document.createElement('canvas');
  c.width = 160;
  c.height = 320;
  const ctx = c.getContext('2d');
  ctx.fillStyle = baseCol || '#eab308';
  ctx.fillRect(0, 0, 160, 320);

  // Subtle vertical structural pilasters
  ctx.fillStyle = 'rgba(0,0,0,0.08)';
  ctx.fillRect(0, 0, 8, 320);
  ctx.fillRect(152, 0, 8, 320);

  const cellW = Math.floor(136 / cols);
  const cellH = Math.floor(296 / rows);
  for (let r = 0; r < rows; r++) {
    for (let cx = 0; cx < cols; cx++) {
      const lit = ((r * 7 + cx * 13) % 5) !== 0;
      ctx.fillStyle = lit ? (winCol || '#fef9c3') : '#b45309';
      ctx.fillRect(12 + cx * cellW + 2, 12 + r * cellH + 3, cellW - 5, cellH - 6);
    }
  }
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function createSoccerBallTex() {
  const c = document.createElement('canvas');
  c.width = 256;
  c.height = 128;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#f8fafc';
  ctx.fillRect(0, 0, 256, 128);
  ctx.fillStyle = '#0f172a';
  const patches = [
    [32, 32], [96, 32], [160, 32], [224, 32],
    [64, 96], [128, 96], [192, 96], [0, 96], [256, 96],
  ];
  for (const [px, py] of patches) {
    ctx.beginPath();
    for (let k = 0; k < 5; k++) {
      const a = (k / 5) * Math.PI * 2 - Math.PI / 2;
      const rx = px + Math.cos(a) * 18;
      const ry = py + Math.sin(a) * 18;
      if (k === 0) ctx.moveTo(rx, ry);
      else ctx.lineTo(rx, ry);
    }
    ctx.closePath();
    ctx.fill();
  }
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function createWindowStripTex() {
  const c = document.createElement('canvas');
  c.width = 128;
  c.height = 256;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#f8fafc';
  ctx.fillRect(0, 0, 128, 256);
  // Paint blue cheatline & passenger window row VERTICALLY along V so rotated fuselage shows horizontal strip!
  for (const xBase of [26, 90]) {
    ctx.fillStyle = '#0284c7';
    ctx.fillRect(xBase, 0, 8, 256);
    ctx.fillStyle = '#0f172a';
    for (let y = 26; y < 232; y += 16) {
      ctx.fillRect(xBase + 10, y, 7, 10);
    }
  }
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function makeMaterialByFinish(colorHex, finish = 'painted_metal', emissiveHex = null) {
  if (finish === 'latex_glossy') {
    return new THREE.MeshPhysicalMaterial({
      color: colorHex || '#ef4444',
      roughness: 0.14,
      metalness: 0.02,
      clearcoat: 1.0,
      clearcoatRoughness: 0.08,
    });
  }
  if (finish === 'fluffy_matte') {
    return new THREE.MeshStandardMaterial({
      color: colorHex || '#ffffff',
      emissive: emissiveHex || '#f1f5f9',
      emissiveIntensity: 0.24,
      roughness: 0.96,
      metalness: 0.0,
    });
  }
  if (finish === 'brushed_chrome') {
    return new THREE.MeshStandardMaterial({
      color: colorHex || '#e2e8f0',
      metalness: 0.88,
      roughness: 0.16,
    });
  }
  if (finish === 'glass_facade') {
    return new THREE.MeshPhysicalMaterial({
      color: colorHex || '#38bdf8',
      roughness: 0.10,
      clearcoat: 0.9,
      transparent: true,
      opacity: 0.86,
    });
  }
  if (finish === 'glazed_food') {
    return new THREE.MeshPhysicalMaterial({
      color: colorHex || '#e11d48',
      roughness: 0.22,
      clearcoat: 0.72,
    });
  }
  if (finish === 'waxy_foliage') {
    return new THREE.MeshPhysicalMaterial({
      color: colorHex || '#22c55e',
      roughness: 0.82,
      metalness: 0.0,
      sheen: 0.55,
      sheenRoughness: 0.72,
      sheenColor: new THREE.Color('#bbf7d0'),
    });
  }
  if (finish === 'organic_bark' || finish === 'matte_wood') {
    return new THREE.MeshStandardMaterial({
      color: colorHex || '#78350f',
      roughness: 0.86,
      metalness: 0.0,
    });
  }
  return new THREE.MeshStandardMaterial({
    color: colorHex || '#f8fafc',
    roughness: 0.35,
    metalness: 0.15,
  });
}

/**
 * Volumetric multi-puff white cumulus cloud (replaces gray low-poly Cloud1..3 GLBs).
 */
export function buildCumulusCloud(seed = 0, scale = 1.0) {
  const g = new THREE.Group();
  const topMat = makeMaterialByFinish('#ffffff', 'fluffy_matte', '#ffffff');
  const bellyMat = makeMaterialByFinish('#f1f5f9', 'fluffy_matte', '#e2e8f0');

  const puffs = [
    { pos: [0.0, 0.34, 0.0], r: 0.56, sx: 1.15, sy: 0.92, sz: 1.0, mat: topMat },
    { pos: [-0.52, 0.22, 0.05], r: 0.44, sx: 1.05, sy: 0.86, sz: 0.95, mat: topMat },
    { pos: [0.54, 0.24, -0.04], r: 0.46, sx: 1.08, sy: 0.88, sz: 0.95, mat: topMat },
    { pos: [-0.94, 0.10, 0.02], r: 0.32, sx: 1.0, sy: 0.82, sz: 0.9, mat: bellyMat },
    { pos: [0.95, 0.12, 0.03], r: 0.34, sx: 1.0, sy: 0.82, sz: 0.9, mat: bellyMat },
    { pos: [0.18, 0.46, 0.12], r: 0.40, sx: 1.0, sy: 0.96, sz: 0.92, mat: topMat },
    { pos: [-0.26, 0.38, -0.14], r: 0.36, sx: 1.0, sy: 0.94, sz: 0.90, mat: topMat },
    { pos: [0.0, 0.04, 0.0], r: 0.46, sx: 2.05, sy: 0.42, sz: 1.05, mat: bellyMat },
  ];

  for (let i = 0; i < puffs.length; i++) {
    const p = puffs[i];
    const m = new THREE.Mesh(new THREE.SphereGeometry(p.r, 20, 16), p.mat);
    const jx = ((seed * 37 + i * 19) % 7 - 3) * 0.015;
    m.position.set(p.pos[0] + jx, p.pos[1], p.pos[2]);
    m.scale.set(p.sx, p.sy, p.sz);
    m.castShadow = false;
    m.receiveShadow = false;
    g.add(m);
  }
  g.scale.setScalar(scale);
  return g;
}

/**
 * Genuine LatheGeometry teardrop latex balloon + pinched neck + tied knot + sinuous ribbon string.
 */
export function buildLatexBalloon(colorHex = '#ef4444', sizeScale = 1.0, stringLen = 0.56) {
  const g = new THREE.Group();

  // Pear/teardrop lathe profile (y = 0 at knot, crown up to y = 0.50)
  const pts = [
    new THREE.Vector2(0.001, 0.0),
    new THREE.Vector2(0.038, 0.018), // rolled lip rim
    new THREE.Vector2(0.016, 0.038), // pinched rubber neck
    new THREE.Vector2(0.045, 0.085),
    new THREE.Vector2(0.115, 0.165),
    new THREE.Vector2(0.178, 0.265),
    new THREE.Vector2(0.192, 0.345),
    new THREE.Vector2(0.168, 0.420),
    new THREE.Vector2(0.105, 0.475),
    new THREE.Vector2(0.001, 0.498),
  ];
  const balloonGeo = new THREE.LatheGeometry(pts, 28);
  const balloonMat = makeMaterialByFinish(colorHex, 'latex_glossy');
  const mesh = new THREE.Mesh(balloonGeo, balloonMat);
  mesh.castShadow = true;

  // Small knot bead under pinched neck
  const knot = new THREE.Mesh(new THREE.SphereGeometry(0.022, 10, 10), balloonMat);
  knot.position.y = 0.012;

  // Natural sinuous dangling ribbon string
  const curve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, 0.0, 0),
    new THREE.Vector3(0.028, -stringLen * 0.28, 0.015),
    new THREE.Vector3(-0.024, -stringLen * 0.62, -0.012),
    new THREE.Vector3(0.016, -stringLen, 0.01),
  ]);
  const stringGeo = new THREE.TubeGeometry(curve, 14, 0.005, 6, false);
  const stringMat = new THREE.MeshBasicMaterial({ color: '#f8fafc' });
  const stringMesh = new THREE.Mesh(stringGeo, stringMat);

  g.add(mesh, knot, stringMesh);
  g.scale.setScalar(sizeScale);
  return g;
}

/**
 * Clean organic multi-puff stylized oak/forest tree (replaces jagged low-poly Tree2..4 GLBs).
 */
function createBarkMaterial(hex = '#78350f') {
  const c = document.createElement('canvas');
  c.width = 256;
  c.height = 256;
  const ctx = c.getContext('2d');
  ctx.fillStyle = hex;
  ctx.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 48; i++) {
    const x = (i * 19 + 7) % 256;
    ctx.fillStyle = i % 2 === 0 ? 'rgba(30, 15, 5, 0.28)' : 'rgba(217, 155, 102, 0.14)';
    ctx.fillRect(x, 0, 3 + (i % 4), 256);
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(2, 2);
  tex.colorSpace = THREE.SRGBColorSpace;
  return new THREE.MeshStandardMaterial({ map: tex, roughness: 0.88, metalness: 0.0 });
}

export function buildStylizedForestTree(seed = 0, targetHeight = 3.5) {
  const g = new THREE.Group();
  const barkMat = createBarkMaterial('#78350f');
  const darkBarkMat = createBarkMaterial('#5c2d16');

  // Flared root plinth + exposed curving 3D surface roots anchoring trunk cleanly to soil
  const rootBase = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.42, 0.36, 14), darkBarkMat);
  rootBase.position.y = 0.18;
  rootBase.castShadow = true;
  for (let r = 0; r < 4; r++) {
    const ang = (r / 4) * Math.PI * 2 + seed * 0.5;
    const rCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(Math.cos(ang) * 0.20, 0.28, Math.sin(ang) * 0.20),
      new THREE.Vector3(Math.cos(ang) * 0.42, 0.10, Math.sin(ang) * 0.42),
      new THREE.Vector3(Math.cos(ang) * 0.62, 0.02, Math.sin(ang) * 0.62),
    ]);
    const rMesh = new THREE.Mesh(new THREE.TubeGeometry(rCurve, 8, 0.055, 8, false), darkBarkMat);
    rMesh.castShadow = true;
    g.add(rMesh);
  }

  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.25, 1.85, 14), barkMat);
  trunk.position.y = 1.05;
  trunk.castShadow = true;
  trunk.receiveShadow = true;

  // Two short supporting fork limbs
  const limbL = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.12, 0.72, 10), barkMat);
  limbL.position.set(-0.22, 1.82, 0.05);
  limbL.rotation.z = 0.55;
  const limbR = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.12, 0.68, 10), barkMat);
  limbR.position.set(0.20, 1.76, -0.05);
  limbR.rotation.z = -0.52;

  // Billowing layered green canopy puffs
  const leafPalette = ['#22c55e', '#16a34a', '#4ade80'];
  const cMain = makeMaterialByFinish(leafPalette[seed % leafPalette.length], 'waxy_foliage');
  const cTop = makeMaterialByFinish(leafPalette[(seed + 1) % leafPalette.length], 'waxy_foliage');
  const cSide = makeMaterialByFinish(leafPalette[(seed + 2) % leafPalette.length], 'waxy_foliage');

  const canopySpec = [
    { pos: [0.0, 2.55, 0.0], r: 0.92, mat: cMain },
    { pos: [-0.55, 2.25, 0.25], r: 0.62, mat: cSide },
    { pos: [0.58, 2.28, -0.18], r: 0.64, mat: cSide },
    { pos: [0.08, 2.30, 0.52], r: 0.56, mat: cTop },
    { pos: [-0.12, 3.05, -0.08], r: 0.62, mat: cTop },
  ];
  g.add(rootBase, trunk, limbL, limbR);
  for (const cp of canopySpec) {
    const puff = new THREE.Mesh(new THREE.SphereGeometry(cp.r, 18, 14), cp.mat);
    puff.position.set(...cp.pos);
    puff.castShadow = true;
    puff.receiveShadow = true;
    g.add(puff);
  }
  const scaleFactor = (targetHeight || 3.5) / 3.65;
  g.scale.setScalar(scaleFactor);
  return g;
}

/**
 * Aerodynamic commercial jet airliner with swept wings, winglets, twin turbines & cabin windows.
 */
function buildAirlinerJet(flyingAirplanes) {
  const g = new THREE.Group();
  const winTex = createWindowStripTex();
  const fuseMat = new THREE.MeshStandardMaterial({ map: winTex, roughness: 0.24, metalness: 0.18 });
  const accentMat = new THREE.MeshStandardMaterial({ color: '#0284c7', roughness: 0.26, metalness: 0.2 });
  const glassMat = new THREE.MeshPhysicalMaterial({ color: '#0f172a', roughness: 0.08, clearcoat: 1.0 });
  const chromeMat = makeMaterialByFinish('#cbd5e1', 'brushed_chrome');

  // Tapered fuselage body + rounded nose + tailcone
  const fuselage = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.26, 2.5, 24), fuseMat);
  fuselage.rotation.z = Math.PI / 2;
  const nose = new THREE.Mesh(new THREE.SphereGeometry(0.32, 20, 16), accentMat);
  nose.scale.set(1.55, 1.0, 1.0);
  nose.position.x = 1.25;
  const tailCone = new THREE.Mesh(new THREE.ConeGeometry(0.26, 0.95, 20), accentMat);
  tailCone.rotation.z = Math.PI / 2;
  tailCone.position.x = -1.70;

  // Cockpit wrap windshield
  const cockpit = new THREE.Mesh(new THREE.SphereGeometry(0.24, 16, 12), glassMat);
  cockpit.scale.set(1.4, 0.72, 0.95);
  cockpit.position.set(1.16, 0.16, 0);

  // Swept main wings with upturned winglets & twin under-wing turbofan engines
  const wingMat = makeMaterialByFinish('#e2e8f0', 'painted_metal');
  for (const side of [-1, 1]) {
    const wing = new THREE.Mesh(new THREE.BoxGeometry(0.82, 0.06, 1.85), wingMat);
    wing.position.set(0.05, -0.05, side * 1.05);
    wing.rotation.y = side * -0.32;
    wing.castShadow = true;

    const winglet = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.28, 0.05), accentMat);
    winglet.position.set(-0.22, 0.10, side * 1.98);
    winglet.rotation.z = 0.22;

    const pod = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.12, 0.56, 16), chromeMat);
    pod.rotation.z = Math.PI / 2;
    pod.position.set(0.22, -0.20, side * 0.72);
    const intake = new THREE.Mesh(new THREE.TorusGeometry(0.13, 0.025, 10, 20), chromeMat);
    intake.rotation.y = Math.PI / 2;
    intake.position.set(0.50, -0.20, side * 0.72);

    const hTail = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.04, 0.72), accentMat);
    hTail.position.set(-1.55, 0.06, side * 0.42);
    hTail.rotation.y = side * -0.28;

    g.add(wing, winglet, pod, intake, hTail);
  }

  // Swept vertical tail stabilizer fin + navigation lights + fluffy jet contrail cones
  const vTail = new THREE.Mesh(new THREE.BoxGeometry(0.66, 0.78, 0.07), accentMat);
  vTail.position.set(-1.48, 0.42, 0);
  vTail.rotation.z = 0.32;

  const navL = new THREE.Mesh(new THREE.SphereGeometry(0.055, 8, 8), new THREE.MeshBasicMaterial({ color: '#ef4444' }));
  navL.position.set(-0.22, 0.24, -2.0);
  const navR = new THREE.Mesh(new THREE.SphereGeometry(0.055, 8, 8), new THREE.MeshBasicMaterial({ color: '#22c55e' }));
  navR.position.set(-0.22, 0.24, 2.0);
  const trailMat = new THREE.MeshBasicMaterial({ color: '#ffffff', transparent: true, opacity: 0.35, depthWrite: false });
  for (const s of [-1, 1]) {
    const trail = new THREE.Mesh(new THREE.ConeGeometry(0.14, 1.8, 10), trailMat);
    trail.rotation.z = -Math.PI / 2;
    trail.position.set(-1.05, -0.20, s * 0.72);
    g.add(trail);
  }

  g.add(fuselage, nose, tailCone, cockpit, vTail, navL, navR);
  g.scale.setScalar(1.38);
  if (flyingAirplanes) flyingAirplanes.push(g);
  return g;
}

/**
 * Ergonomic two-stage hydraulic barber/lift chair wide enough for zero character arm clipping.
 */
function buildHydraulicLiftChair(dynamicLiftChairs) {
  const g = new THREE.Group();
  const baseMat = makeMaterialByFinish('#334155', 'painted_metal');
  const chromeMat = makeMaterialByFinish('#e2e8f0', 'brushed_chrome');
  const leatherMat = new THREE.MeshPhysicalMaterial({ color: '#991b1b', roughness: 0.42, clearcoat: 0.22 });
  const trimMat = makeMaterialByFinish('#450a0a', 'painted_metal');

  // Heavy circular steel floor baseplate + outer hydraulic collar
  const plate = new THREE.Mesh(new THREE.CylinderGeometry(0.56, 0.60, 0.06, 28), baseMat);
  plate.position.y = 0.03;
  plate.receiveShadow = true;
  const collar = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.13, 0.26, 18), chromeMat);
  collar.position.y = 0.16;

  // Pivoted foot pump pedal bar with black rubber pad
  const pedal = new THREE.Group();
  pedal.position.set(-0.24, 0.11, 0.0);
  const pedalBar = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 0.42, 10), chromeMat);
  pedalBar.rotation.z = Math.PI / 2;
  pedalBar.position.x = -0.18;
  const pedalPad = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.04, 0.12), baseMat);
  pedalPad.position.set(-0.38, 0.01, 0);
  pedal.add(pedalBar, pedalPad);

  // Telescoping chrome hydraulic cylinder (dynamically stretched every frame; initialized tucked under seat)
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.072, 0.082, 1.0, 20), chromeMat);
  pole.scale.y = 0.28;
  pole.position.y = 0.14;
  pole.castShadow = true;

  // Wide ergonomic swivel seat (`0.84m` outer, `±0.42m` armrests) -> ZERO elbow intersection!
  const seatGroup = new THREE.Group();
  seatGroup.position.y = 0.34;
  const cushion = new THREE.Mesh(new THREE.BoxGeometry(0.76, 0.16, 0.68), leatherMat);
  cushion.position.y = -0.02;
  cushion.castShadow = true;

  const backRest = new THREE.Mesh(new THREE.BoxGeometry(0.76, 0.62, 0.14), leatherMat);
  backRest.position.set(0, 0.30, -0.28);
  backRest.castShadow = true;

  const headRest = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.18, 0.12), trimMat);
  headRest.position.set(0, 0.66, -0.28);

  for (const sx of [-0.41, 0.41]) {
    const post = new THREE.Mesh(new THREE.CylinderGeometry(0.026, 0.026, 0.24, 10), chromeMat);
    post.position.set(sx, 0.10, 0);
    const pad = new THREE.Mesh(new THREE.BoxGeometry(0.10, 0.07, 0.56), trimMat);
    pad.position.set(sx, 0.22, 0.02);
    pad.castShadow = true;
    seatGroup.add(post, pad);
  }
  const footRest = new THREE.Mesh(new THREE.BoxGeometry(0.56, 0.05, 0.18), chromeMat);
  footRest.position.set(0, -0.18, 0.38);

  seatGroup.add(cushion, backRest, headRest, footRest);
  g.add(plate, collar, pedal, pole, seatGroup);
  if (dynamicLiftChairs) {
    dynamicLiftChairs.push({ group: g, pole, seatGroup, pedal });
  }
  return g;
}

/**
 * Multi-tier architectural golden skyscraper cluster.
 */
function buildGoldenSkyline() {
  const g = new THREE.Group();
  const trimGold = new THREE.MeshStandardMaterial({ color: '#fde047', metalness: 0.55, roughness: 0.25 });
  const towers = [
    { pos: [-5.4, 0.0, -3.8], w: 2.5, h: 14.5, d: 2.5, col: '#facc15', win: '#fef9c3', spire: true },
    { pos: [5.4, 0.0, -3.5], w: 2.6, h: 17.0, d: 2.5, col: '#eab308', win: '#fef08a', spire: true },
    { pos: [-2.9, 0.0, -7.4], w: 2.9, h: 20.5, d: 2.7, col: '#fbbf24', win: '#e0f2fe', spire: false },
    { pos: [3.0, 0.0, -7.2], w: 2.9, h: 19.0, d: 2.7, col: '#f59e0b', win: '#fef08a', spire: true },
    { pos: [0.0, 0.0, -10.2], w: 3.6, h: 24.0, d: 3.2, col: '#eab308', win: '#fffbeb', spire: true },
    { pos: [-7.0, 0.0, -8.2], w: 2.7, h: 15.5, d: 2.5, col: '#ca8a04', win: '#fef08a', spire: false },
    { pos: [7.0, 0.0, -8.4], w: 2.7, h: 18.0, d: 2.5, col: '#d97706', win: '#e0f2fe', spire: false },
  ];
  for (const tw of towers) {
    const tex = createSkyscraperFacadeTex(tw.col, tw.win);
    const bodyMat = new THREE.MeshStandardMaterial({ map: tex, metalness: 0.35, roughness: 0.26 });

    // Lower podium tier (65% height)
    const lowerH = tw.h * 0.65;
    const lower = new THREE.Mesh(new THREE.BoxGeometry(tw.w, lowerH, tw.d), bodyMat);
    lower.position.set(tw.pos[0], lowerH * 0.5, tw.pos[2]);
    lower.castShadow = true;
    lower.receiveShadow = true;

    // Upper setback tier
    const upperH = tw.h * 0.35;
    const upper = new THREE.Mesh(new THREE.BoxGeometry(tw.w * 0.76, upperH, tw.d * 0.76), bodyMat);
    upper.position.set(tw.pos[0], lowerH + upperH * 0.5, tw.pos[2]);
    upper.castShadow = true;

    // Parapet crown rim
    const crown = new THREE.Mesh(new THREE.BoxGeometry(tw.w * 0.80, 0.28, tw.d * 0.80), trimGold);
    crown.position.set(tw.pos[0], tw.h + 0.14, tw.pos[2]);

    g.add(lower, upper, crown);
    if (tw.spire) {
      const spire = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.14, 2.2, 8), trimGold);
      spire.position.set(tw.pos[0], tw.h + 1.25, tw.pos[2]);
      g.add(spire);
    }
  }
  return g;
}

/**
 * Heart-lobed veined tropical giant leaf (`THREE.Shape` + ExtrudeGeometry).
 */
function buildTropicalGiantLeaf() {
  const g = new THREE.Group();
  const shape = new THREE.Shape();
  shape.moveTo(0, -0.78);
  shape.bezierCurveTo(0.45, -1.02, 1.05, -0.58, 0.96, 0.08);
  shape.bezierCurveTo(0.88, 0.56, 0.38, 0.92, 0.0, 1.08);
  shape.bezierCurveTo(-0.38, 0.92, -0.88, 0.56, -0.96, 0.08);
  shape.bezierCurveTo(-1.05, -0.58, -0.45, -1.02, 0, -0.78);

  const leafGeo = new THREE.ExtrudeGeometry(shape, { depth: 0.03, bevelEnabled: true, bevelSize: 0.015, bevelThickness: 0.015, bevelSegments: 2 });
  const leafMat = makeMaterialByFinish('#22c55e', 'waxy_foliage');
  const veinMat = makeMaterialByFinish('#15803d', 'waxy_foliage');

  const blade = new THREE.Mesh(leafGeo, leafMat);
  blade.rotation.x = -Math.PI / 2;
  blade.position.y = 0.025;
  blade.receiveShadow = true;
  blade.castShadow = true;

  const midrib = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.036, 1.82, 8), veinMat);
  midrib.rotation.x = Math.PI / 2;
  midrib.position.set(0, 0.055, 0.12);

  g.add(blade, midrib);
  for (let i = -2; i <= 2; i++) {
    for (const s of [-1, 1]) {
      const v = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.016, 0.65, 6), veinMat);
      v.rotation.z = Math.PI / 2;
      v.rotation.y = s * -0.45;
      v.position.set(s * 0.32, 0.052, i * 0.28 + 0.05);
      g.add(v);
    }
  }
  // Sparkling morning dewdrop beads on tropical leaf
  const dewMat = new THREE.MeshPhysicalMaterial({ color: '#e0f2fe', roughness: 0.05, clearcoat: 1.0, transparent: true, opacity: 0.85 });
  for (const [dx, dz, dr] of [[-0.36, 0.28, 0.042], [0.42, -0.18, 0.036], [0.18, 0.56, 0.030]]) {
    const drop = new THREE.Mesh(new THREE.SphereGeometry(dr, 12, 10), dewMat);
    drop.scale.set(1.15, 0.65, 1.15);
    drop.position.set(dx, 0.068, dz);
    g.add(drop);
  }
  return g;
}

/**
 * Curved realistic chain of pinched cartoon sausage links on a rimmed ceramic plate.
 */
function buildSausageOnPlate() {
  const g = new THREE.Group();
  const platePts = [
    new THREE.Vector2(0.001, 0.01),
    new THREE.Vector2(0.22, 0.015),
    new THREE.Vector2(0.32, 0.055),
    new THREE.Vector2(0.34, 0.062),
    new THREE.Vector2(0.30, 0.030),
    new THREE.Vector2(0.001, 0.024),
  ];
  const plateMat = makeMaterialByFinish('#f8fafc', 'ceramic');
  const plate = new THREE.Mesh(new THREE.LatheGeometry(platePts, 28), plateMat);
  plate.receiveShadow = true;
  plate.castShadow = true;
  g.add(plate);

  const sMat = makeMaterialByFinish('#e11d48', 'glazed_food');
  const tieMat = makeMaterialByFinish('#f43f5e', 'glazed_food');
  const links = [
    { pos: [-0.14, 0.072, 0.04], rotY: 0.38 },
    { pos: [0.00, 0.072, -0.02], rotY: -0.22 },
    { pos: [0.14, 0.072, 0.05], rotY: 0.42 },
  ];
  for (const lk of links) {
    const cap = new THREE.Mesh(new THREE.CapsuleGeometry(0.046, 0.11, 10, 14), sMat);
    cap.rotation.z = Math.PI / 2;
    cap.rotation.y = lk.rotY;
    cap.position.set(...lk.pos);
    cap.castShadow = true;
    g.add(cap);
  }
  for (const bx of [-0.07, 0.07]) {
    const knot = new THREE.Mesh(new THREE.SphereGeometry(0.022, 8, 8), tieMat);
    knot.position.set(bx, 0.072, 0.01);
    g.add(knot);
  }
  return g;
}

/**
 * Hollow ancient oak tree with root flare, arched dark doorway recess, and layered foliage puffs.
 */
function buildHollowOakTree(breezeMeshes) {
  const g = new THREE.Group();
  const barkMat = makeMaterialByFinish('#78350f', 'organic_bark');
  const rimMat = makeMaterialByFinish('#92400e', 'organic_bark');
  const cavityMat = new THREE.MeshBasicMaterial({ color: '#090d16' });
  const leafMat = makeMaterialByFinish('#22c55e', 'waxy_foliage');
  const leafDarkMat = makeMaterialByFinish('#16a34a', 'waxy_foliage');

  const rootBase = new THREE.Mesh(new THREE.CylinderGeometry(0.95, 1.32, 0.55, 18), barkMat);
  rootBase.position.y = 0.275;
  rootBase.castShadow = true;

  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.72, 0.98, 3.25, 20), barkMat);
  trunk.position.y = 1.85;
  trunk.castShadow = true;

  // Recessed arched hollow doorway + outer thick bark arch ring
  const archFrame = new THREE.Mesh(new THREE.CylinderGeometry(0.46, 0.50, 0.16, 18), rimMat);
  archFrame.rotation.x = Math.PI / 2;
  archFrame.scale.set(1.0, 1.0, 1.35);
  archFrame.position.set(0, 0.72, 0.92);

  const cavity = new THREE.Mesh(new THREE.CylinderGeometry(0.36, 0.40, 0.20, 18), cavityMat);
  cavity.rotation.x = Math.PI / 2;
  cavity.scale.set(1.0, 1.0, 1.32);
  cavity.position.set(0, 0.72, 0.95);

  g.add(rootBase, trunk, archFrame, cavity);
  const crown = [
    { pos: [0.0, 3.85, 0.0], r: 1.55, mat: leafMat },
    { pos: [-1.0, 3.45, 0.25], r: 1.02, mat: leafDarkMat },
    { pos: [1.0, 3.50, -0.2], r: 1.05, mat: leafDarkMat },
    { pos: [0.15, 4.45, 0.15], r: 1.08, mat: leafMat },
  ];
  for (const cp of crown) {
    const sp = new THREE.Mesh(new THREE.SphereGeometry(cp.r, 18, 14), cp.mat);
    sp.position.set(...cp.pos);
    sp.castShadow = true;
    g.add(sp);
  }
  if (breezeMeshes) breezeMeshes.push(g);
  return g;
}

/**
 * Giant Glossy Stylized Cockroach (segmented carapace, pronotum, 6 articulated legs, 2 curved antennae).
 */
export function buildGiantCockroach() {
  const g = new THREE.Group();
  const shellMat = new THREE.MeshPhysicalMaterial({ color: '#451a03', roughness: 0.18, clearcoat: 0.88, clearcoatRoughness: 0.1 });
  const thoraxMat = new THREE.MeshPhysicalMaterial({ color: '#290f02', roughness: 0.24, clearcoat: 0.72 });
  const limbMat = new THREE.MeshStandardMaterial({ color: '#78350f', roughness: 0.45 });

  // Segmented ovoid carapace & shield thorax (upright/tilted facing viewer cleanly)
  const abdomen = new THREE.Mesh(new THREE.SphereGeometry(0.28, 22, 18), shellMat);
  abdomen.scale.set(0.76, 1.38, 0.56);
  const pronotum = new THREE.Mesh(new THREE.SphereGeometry(0.20, 18, 14), thoraxMat);
  pronotum.scale.set(0.88, 0.85, 0.62);
  pronotum.position.set(0, 0.34, 0.03);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.11, 14, 12), thoraxMat);
  head.position.set(0, 0.48, 0.05);
  abdomen.castShadow = true;
  pronotum.castShadow = true;
  g.add(abdomen, pronotum, head);

  // Gleaming cartoonish googly eyes
  const eyeWhite = new THREE.MeshBasicMaterial({ color: '#ffffff' });
  const pupilMat = new THREE.MeshBasicMaterial({ color: '#0f172a' });
  for (const sx of [-0.055, 0.055]) {
    const ew = new THREE.Mesh(new THREE.SphereGeometry(0.038, 12, 10), eyeWhite);
    ew.position.set(sx, 0.52, 0.12);
    const ep = new THREE.Mesh(new THREE.SphereGeometry(0.020, 10, 8), pupilMat);
    ep.position.set(sx, 0.52, 0.148);
    g.add(ew, ep);

    // Sweeping curved antenna via TubeGeometry
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(sx * 0.8, 0.54, 0.08),
      new THREE.Vector3(sx * 3.8, 0.86, 0.16),
      new THREE.Vector3(sx * 7.2, 1.02, 0.06),
    ]);
    const ant = new THREE.Mesh(new THREE.TubeGeometry(curve, 12, 0.012, 6, false), limbMat);
    g.add(ant);
  }

  // 6 Jointed insect legs (3 per side)
  for (const side of [-1, 1]) {
    for (let row = 0; row < 3; row++) {
      const yBase = 0.24 - row * 0.22;
      const zCurve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(side * 0.14, yBase, 0.02),
        new THREE.Vector3(side * 0.42, yBase + (row === 0 ? 0.08 : -0.06), 0.14),
        new THREE.Vector3(side * 0.54, yBase - 0.18, 0.04),
      ]);
      const leg = new THREE.Mesh(new THREE.TubeGeometry(zCurve, 8, 0.018, 6, false), limbMat);
      leg.castShadow = true;
      g.add(leg);
    }
  }
  return g;
}

/**
 * Brushed Stainless Steel Cooking Pot (tilted to trap a bug against wall or resting cleanly).
 */
export function buildCookingPot() {
  const g = new THREE.Group();
  const steelMat = makeMaterialByFinish('#e2e8f0', 'brushed_chrome');
  const darkInnerMat = new THREE.MeshStandardMaterial({ color: '#334155', metalness: 0.7, roughness: 0.35 });

  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.26, 0.38, 28, 1, true), steelMat);
  body.castShadow = true;
  const bottom = new THREE.Mesh(new THREE.CylinderGeometry(0.26, 0.26, 0.04, 24), steelMat);
  bottom.position.y = -0.18;
  const rim = new THREE.Mesh(new THREE.TorusGeometry(0.28, 0.022, 10, 28), steelMat);
  rim.rotation.x = Math.PI / 2;
  rim.position.y = 0.19;
  const interior = new THREE.Mesh(new THREE.CircleGeometry(0.25, 24), darkInnerMat);
  interior.rotation.x = -Math.PI / 2;
  interior.position.y = -0.15;

  for (const side of [-1, 1]) {
    const handle = new THREE.Mesh(new THREE.TorusGeometry(0.068, 0.016, 8, 16, Math.PI), steelMat);
    handle.position.set(side * 0.27, 0.08, 0);
    handle.rotation.z = side * -Math.PI / 2;
    g.add(handle);
  }
  g.add(body, bottom, rim, interior);
  g.rotation.x = -Math.PI / 2 + 0.15;
  return g;
}

/**
 * Long-Handled Sweeping Floor Broom (bright sky-blue handle + angled cap + dual bristles).
 */
export function buildCleaningBroom() {
  const g = new THREE.Group();
  const poleMat = makeMaterialByFinish('#0ea5e9', 'painted_metal');
  const capMat = makeMaterialByFinish('#1e293b', 'painted_metal');
  const bristleMat = makeMaterialByFinish('#fbbf24', 'matte_wood');

  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.024, 1.38, 12), poleMat);
  pole.position.y = 0.85;
  pole.castShadow = true;
  const shroud = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.09, 0.10), capMat);
  shroud.position.y = 0.18;
  shroud.castShadow = true;
  const bristles = new THREE.Mesh(new THREE.BoxGeometry(0.39, 0.16, 0.11), bristleMat);
  bristles.position.y = 0.08;
  bristles.castShadow = true;
  g.add(pole, shroud, bristles);
  g.rotation.z = -0.14;
  return g;
}

/**
 * Oak Gaming Computer Desk + Glowing GTA/Game Widescreen Monitor + Red Gaming Chair.
 */
export function buildComputerDesk() {
  const g = new THREE.Group();
  const deskMat = makeMaterialByFinish('#d99b66', 'matte_wood');
  const legMat = makeMaterialByFinish('#1e293b', 'painted_metal');
  const screenBezel = new THREE.MeshStandardMaterial({ color: '#0f172a', roughness: 0.25, metalness: 0.6 });

  const top = new THREE.Mesh(new THREE.BoxGeometry(1.55, 0.07, 0.72), deskMat);
  top.position.set(0, 0.72, 0);
  top.castShadow = true;
  top.receiveShadow = true;
  g.add(top);

  for (const lx of [-0.68, 0.68]) {
    for (const lz of [-0.28, 0.28]) {
      const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.70, 10), legMat);
      leg.position.set(lx, 0.35, lz);
      leg.castShadow = true;
      g.add(leg);
    }
  }

  // Live vibrant 3D game monitor CanvasTexture (sunset palms & racing city HUD)
  const mc = document.createElement('canvas');
  mc.width = 256; mc.height = 144;
  const mctx = mc.getContext('2d');
  const sg = mctx.createLinearGradient(0, 0, 0, 144);
  sg.addColorStop(0, '#f43f5e');
  sg.addColorStop(0.55, '#fb923c');
  sg.addColorStop(1, '#312e81');
  mctx.fillStyle = sg;
  mctx.fillRect(0, 0, 256, 144);
  mctx.fillStyle = '#0f172a';
  mctx.fillRect(0, 96, 256, 48);
  mctx.fillStyle = '#38bdf8';
  mctx.fillRect(14, 106, 42, 26);
  mctx.fillStyle = '#facc15';
  mctx.font = 'bold 28px Arial';
  mctx.fillText('GAME ON!', 68, 66);
  const screenTex = new THREE.CanvasTexture(mc);
  screenTex.colorSpace = THREE.SRGBColorSpace;

  const monitorBack = new THREE.Mesh(new THREE.BoxGeometry(0.92, 0.54, 0.045), screenBezel);
  monitorBack.position.set(0, 1.15, -0.18);
  monitorBack.castShadow = true;
  const monitorFace = new THREE.Mesh(new THREE.PlaneGeometry(0.84, 0.46), new THREE.MeshBasicMaterial({ map: screenTex }));
  monitorFace.position.set(0, 1.15, -0.155);
  const stand = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.045, 0.24, 12), legMat);
  stand.position.set(0, 0.86, -0.20);
  const kb = new THREE.Mesh(new THREE.BoxGeometry(0.44, 0.025, 0.15), screenBezel);
  kb.position.set(-0.06, 0.77, 0.14);
  g.add(monitorBack, monitorFace, stand, kb);

  // Sleek Red & Black Gaming Chair pulled right cleanly in front of desk
  const chairMat = makeMaterialByFinish('#dc2626', 'painted_metal');
  const seat = new THREE.Mesh(new THREE.BoxGeometry(0.50, 0.08, 0.46), chairMat);
  seat.position.set(0, 0.45, 0.56);
  const back = new THREE.Mesh(new THREE.BoxGeometry(0.46, 0.66, 0.08), chairMat);
  back.position.set(0, 0.78, 0.78);
  const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.36, 10), legMat);
  stem.position.set(0, 0.24, 0.56);
  const basePlate = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.30, 0.05, 16), legMat);
  basePlate.position.set(0, 0.04, 0.56);
  g.add(seat, back, stem, basePlate);
  return g;
}

/**
 * Carved Ashlar Stone Labyrinth Walls framing a clear front-facing maze corridor.
 */
export function buildStoneMazeWalls() {
  const g = new THREE.Group();
  const c = document.createElement('canvas');
  c.width = 256; c.height = 256;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#475569';
  ctx.fillRect(0, 0, 256, 256);
  for (let row = 0; row < 4; row++) {
    const y = row * 64;
    const xOff = (row % 2) * 32;
    for (let col = -1; col < 5; col++) {
      ctx.fillStyle = (row + col) % 2 === 0 ? '#94a3b8' : '#788496';
      ctx.fillRect(col * 64 + xOff + 4, y + 4, 56, 56);
      ctx.fillStyle = 'rgba(255,255,255,0.14)';
      ctx.fillRect(col * 64 + xOff + 4, y + 4, 56, 8);
    }
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(3, 1.5);
  tex.colorSpace = THREE.SRGBColorSpace;
  const stoneMat = new THREE.MeshStandardMaterial({ map: tex, roughness: 0.78, metalness: 0.04 });

  const wallSegments = [
    // Rear labyrinth boundary wall & corridor niches
    { pos: [0.0, 0.90, -2.55], size: [7.6, 1.80, 0.55] },
    { pos: [-2.85, 0.90, -0.35], size: [0.55, 1.80, 4.4] },
    { pos: [2.85, 0.90, -0.35], size: [0.55, 1.80, 4.4] },
    { pos: [-1.45, 0.90, -1.45], size: [1.45, 1.80, 0.45] },
    { pos: [1.55, 0.90, -1.15], size: [1.35, 1.80, 0.45] },
    { pos: [-1.85, 0.90, 0.95], size: [1.10, 1.80, 0.45] },
  ];
  for (const w of wallSegments) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(...w.size), stoneMat);
    m.position.set(...w.pos);
    m.castShadow = true;
    m.receiveShadow = true;
    g.add(m);
  }
  return g;
}

/**
 * High-Intensity Sci-Fi Laser Barrier Emitter + Incandescent Beam Core & Plasma Aura.
 */
export function buildLaserBeam() {
  const g = new THREE.Group();
  const emitterMat = makeMaterialByFinish('#334155', 'painted_metal');
  const coreMat = new THREE.MeshBasicMaterial({ color: '#ffffff' });
  const glowMat = new THREE.MeshBasicMaterial({
    color: '#ef4444',
    transparent: true,
    opacity: 0.68,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });

  for (const sx of [-1.85, 1.85]) {
    const pod = new THREE.Mesh(new THREE.BoxGeometry(0.28, 0.34, 0.34), emitterMat);
    pod.position.set(sx, 0.0, 0);
    pod.castShadow = true;
    const lens = new THREE.Mesh(new THREE.SphereGeometry(0.11, 14, 12), new THREE.MeshBasicMaterial({ color: '#ef4444' }));
    lens.position.set(sx - Math.sign(sx) * 0.14, 0, 0);
    g.add(pod, lens);
  }
  const coreBeam = new THREE.Mesh(new THREE.CylinderGeometry(0.038, 0.038, 3.55, 16), coreMat);
  coreBeam.rotation.z = Math.PI / 2;
  const outerBeam = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.13, 3.55, 16), glowMat);
  outerBeam.rotation.z = Math.PI / 2;
  g.add(coreBeam, outerBeam);
  return g;
}

/**
 * Metallic Concentric Superhero Shield with Crisp Five-Point Star Emblem.
 */
export function buildHeroShield() {
  const g = new THREE.Group();
  const c = document.createElement('canvas');
  c.width = 512; c.height = 512;
  const ctx = c.getContext('2d');
  const rings = [
    { r: 252, col: '#dc2626' },
    { r: 200, col: '#e2e8f0' },
    { r: 150, col: '#dc2626' },
    { r: 102, col: '#1d4ed8' },
  ];
  for (const rg of rings) {
    ctx.fillStyle = rg.col;
    ctx.beginPath();
    ctx.arc(256, 256, rg.r, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.fillStyle = '#ffffff';
  ctx.beginPath();
  for (let i = 0; i < 10; i++) {
    const r = (i % 2 === 0) ? 86 : 36;
    const a = (i / 10) * Math.PI * 2 - Math.PI / 2;
    const x = 256 + Math.cos(a) * r;
    const y = 256 + Math.sin(a) * r;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.fill();

  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  const shieldMat = new THREE.MeshPhysicalMaterial({ map: tex, metalness: 0.72, roughness: 0.22, clearcoat: 0.7 });
  const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.42, 0.08, 36), shieldMat);
  disc.rotation.x = Math.PI / 2;
  disc.castShadow = true;
  g.add(disc);
  return g;
}

/**
 * Horned Cartoon Guardian Bull (Muscular Bust, Ivory Horns, Gold Nose Ring, Fierce Eyes).
 */
export function buildAngryBull() {
  const g = new THREE.Group();
  const bodyMat = makeMaterialByFinish('#7f1d1d', 'painted_metal');
  const snoutMat = makeMaterialByFinish('#d97706', 'painted_metal');
  const hornMat = makeMaterialByFinish('#fef3c7', 'ceramic');
  const ringMat = makeMaterialByFinish('#facc15', 'brushed_chrome');

  const torso = new THREE.Mesh(new THREE.BoxGeometry(0.92, 0.78, 0.64), bodyMat);
  torso.position.y = 0.42;
  torso.castShadow = true;
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.68, 0.62, 0.62), bodyMat);
  head.position.set(0, 0.96, 0.14);
  head.castShadow = true;
  const snout = new THREE.Mesh(new THREE.BoxGeometry(0.50, 0.28, 0.34), snoutMat);
  snout.position.set(0, 0.80, 0.42);
  const noseRing = new THREE.Mesh(new THREE.TorusGeometry(0.09, 0.022, 10, 20), ringMat);
  noseRing.position.set(0, 0.72, 0.59);
  g.add(torso, head, snout, noseRing);

  for (const sx of [-1, 1]) {
    const horn = new THREE.Mesh(new THREE.ConeGeometry(0.11, 0.46, 14), hornMat);
    horn.position.set(sx * 0.42, 1.24, 0.14);
    horn.rotation.z = sx * -0.58;
    horn.rotation.x = 0.25;
    horn.castShadow = true;
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.055, 10, 8), new THREE.MeshBasicMaterial({ color: '#fef08a' }));
    eye.position.set(sx * 0.18, 1.02, 0.44);
    g.add(horn, eye);
  }
  return g;
}

/**
 * Dense Matte Velvet Leafy Camouflage Bush Thicket.
 */
export function buildCamouflageBush() {
  const g = new THREE.Group();
  const leafPalette = ['#15803d', '#16a34a', '#22c55e'];
  const puffs = [
    [0.0, 0.42, 0.0, 0.46],
    [-0.38, 0.32, 0.12, 0.36],
    [0.38, 0.30, -0.10, 0.36],
    [0.08, 0.66, 0.02, 0.34],
    [-0.18, 0.26, -0.28, 0.32],
  ];
  for (let i = 0; i < puffs.length; i++) {
    const [px, py, pz, pr] = puffs[i];
    const m = new THREE.Mesh(new THREE.IcosahedronGeometry(pr, 1), makeMaterialByFinish(leafPalette[i % leafPalette.length], 'waxy_foliage'));
    m.position.set(px, py, pz);
    m.castShadow = true;
    m.receiveShadow = true;
    g.add(m);
  }
  return g;
}

/**
 * Floating Glowing Strength Power-Up Cyan Orb & Gold Dumbbell Emblem.
 */
export function buildStrengthOrb() {
  const g = new THREE.Group();
  const orbMat = new THREE.MeshPhysicalMaterial({
    color: '#06b6d4',
    emissive: '#0891b2',
    emissiveIntensity: 0.65,
    roughness: 0.12,
    transparent: true,
    opacity: 0.55,
    clearcoat: 1.0,
  });
  const orb = new THREE.Mesh(new THREE.SphereGeometry(0.34, 24, 20), orbMat);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.42, 0.032, 12, 32), new THREE.MeshBasicMaterial({ color: '#67e8f9' }));
  ring.rotation.x = 0.55;

  // Inner metallic gold dumbbell icon
  const goldMat = makeMaterialByFinish('#facc15', 'brushed_chrome');
  const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.34, 12), goldMat);
  bar.rotation.z = Math.PI / 2;
  const bellL = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 0.08, 16), goldMat);
  bellL.rotation.z = Math.PI / 2;
  bellL.position.x = -0.17;
  const bellR = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 0.08, 16), goldMat);
  bellR.rotation.z = Math.PI / 2;
  bellR.position.x = 0.17;
  g.add(orb, ring, bar, bellL, bellR);
  return g;
}

/**
 * Ascending Rainbow Musical Staircase Steps (glowing colorful piano/block stairs ascending left -> right).
 */
export function buildMusicalStaircase() {
  const g = new THREE.Group();
  const colors = ['#ef4444', '#f97316', '#facc15', '#22c55e', '#06b6d4', '#3b82f6', '#ec4899'];
  const baseMat = makeMaterialByFinish('#e2e8f0', 'ceramic');
  for (let i = 0; i < colors.length; i++) {
    const h = 0.24 + i * 0.22;
    const x = -1.65 + i * 0.55;
    const riser = new THREE.Mesh(new THREE.BoxGeometry(0.50, h, 0.78), makeMaterialByFinish(colors[i], 'latex_glossy'));
    riser.position.set(x, h * 0.5, 0);
    riser.castShadow = true;
    riser.receiveShadow = true;
    // White piano key accent strip across front edge of each step
    const strip = new THREE.Mesh(new THREE.BoxGeometry(0.46, 0.04, 0.14), baseMat);
    strip.position.set(x, h + 0.015, 0.30);
    g.add(riser, strip);
  }
  return g;
}

/**
 * Glossy 3D Floating Musical Note (oval notehead, vertical stem, curved flag).
 */
export function buildFloatingMusicalNote() {
  const g = new THREE.Group();
  const noteMat = makeMaterialByFinish('#a855f7', 'latex_glossy');
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.16, 18, 14), noteMat);
  head.scale.set(1.25, 0.88, 0.65);
  head.rotation.z = 0.32;
  head.castShadow = true;
  const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.032, 0.032, 0.62, 12), noteMat);
  stem.position.set(0.14, 0.30, 0);
  const flag = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.11, 0.06), noteMat);
  flag.position.set(0.24, 0.54, 0);
  flag.rotation.z = -0.38;
  g.add(head, stem, flag);
  return g;
}

/**
 * Pastel French Macaron Cookies Trio (domed shells + buttercream filling ring).
 */
export function buildMacarons() {
  const g = new THREE.Group();
  const creamMat = makeMaterialByFinish('#fffbeb', 'glazed_food');
  const specs = [
    { pos: [-0.65, 0.0, 0.0], col: '#fb7185' },
    { pos: [0.0, 0.25, 0.15], col: '#38bdf8' },
    { pos: [0.65, -0.05, -0.10], col: '#a855f7' },
  ];
  for (const sp of specs) {
    const m = new THREE.Group();
    const shellMat = makeMaterialByFinish(sp.col, 'glazed_food');
    const bot = new THREE.Mesh(new THREE.CylinderGeometry(0.19, 0.17, 0.075, 22), shellMat);
    bot.position.y = -0.055;
    const fill = new THREE.Mesh(new THREE.CylinderGeometry(0.175, 0.175, 0.055, 22), creamMat);
    const top = new THREE.Mesh(new THREE.SphereGeometry(0.19, 20, 14, 0, Math.PI * 2, 0, Math.PI * 0.55), shellMat);
    top.scale.y = 0.62;
    top.position.y = 0.02;
    m.add(bot, fill, top);
    m.position.set(...sp.pos);
    m.rotation.z = 0.15;
    g.add(m);
  }
  return g;
}

/**
 * Glossy Cartoon Giant Roasted Turkey Drumstick (glazed meat bulge + white leg bone & twin knuckles).
 */
export function buildGiantTurkeyLeg() {
  const g = new THREE.Group();
  const meatMat = makeMaterialByFinish('#9a3412', 'glazed_food');
  const boneMat = makeMaterialByFinish('#fef9c3', 'ceramic');
  const drum = new THREE.Mesh(new THREE.SphereGeometry(0.24, 20, 16), meatMat);
  drum.scale.set(1.0, 1.0, 1.48);
  drum.castShadow = true;
  const bone = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.055, 0.36, 14), boneMat);
  bone.rotation.x = Math.PI / 2;
  bone.position.z = 0.38;
  for (const sx of [-0.045, 0.045]) {
    const knob = new THREE.Mesh(new THREE.SphereGeometry(0.058, 12, 10), boneMat);
    knob.position.set(sx, 0, 0.55);
    g.add(knob);
  }
  g.add(drum, bone);
  g.rotation.set(0.35, 0.45, 0.18);
  return g;
}

/**
 * Clean Outdoor Patio Folding Chair (aluminum frame legs + cobalt blue canvas seat & backrest).
 */
export function buildFoldingChair() {
  const g = new THREE.Group();
  const tubeMat = makeMaterialByFinish('#cbd5e1', 'brushed_chrome');
  const canvasMat = makeMaterialByFinish('#2563eb', 'fabric');
  const seat = new THREE.Mesh(new THREE.BoxGeometry(0.54, 0.06, 0.48), canvasMat);
  seat.position.set(0, 0.44, 0);
  seat.castShadow = true;
  const back = new THREE.Mesh(new THREE.BoxGeometry(0.54, 0.52, 0.06), canvasMat);
  back.position.set(0, 0.72, -0.22);
  back.rotation.x = -0.14;
  back.castShadow = true;
  for (const sx of [-0.24, 0.24]) {
    const legF = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 0.48, 8), tubeMat);
    legF.position.set(sx, 0.22, 0.16);
    legF.rotation.x = -0.22;
    const legB = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 0.48, 8), tubeMat);
    legB.position.set(sx, 0.22, -0.16);
    legB.rotation.x = 0.22;
    g.add(legF, legB);
  }
  g.add(seat, back);
  return g;
}

/**
 * Authentic Red Clay Brick Courtyard Wall (terracotta courses + mortar + grey stone coping top).
 */
export function buildBrickWall() {
  const g = new THREE.Group();
  const c = document.createElement('canvas');
  c.width = 256; c.height = 256;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#94a3b8';
  ctx.fillRect(0, 0, 256, 256);
  for (let row = 0; row < 8; row++) {
    const y = row * 32;
    const xOff = (row % 2) * 32;
    for (let col = -1; col < 5; col++) {
      ctx.fillStyle = (row + col) % 2 === 0 ? '#b91c1c' : '#991b1b';
      ctx.fillRect(col * 64 + xOff + 3, y + 3, 58, 26);
    }
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(3, 2);
  tex.colorSpace = THREE.SRGBColorSpace;

  const brickMat = new THREE.MeshStandardMaterial({ map: tex, roughness: 0.82 });
  const capMat = makeMaterialByFinish('#cbd5e1', 'ceramic');
  const wall = new THREE.Mesh(new THREE.BoxGeometry(3.2, 1.94, 0.62), brickMat);
  wall.position.y = 0.97;
  wall.castShadow = true;
  wall.receiveShadow = true;
  const cap = new THREE.Mesh(new THREE.BoxGeometry(3.32, 0.12, 0.72), capMat);
  cap.position.y = 1.96;
  cap.castShadow = true;
  cap.receiveShadow = true;
  g.add(wall, cap);
  return g;
}

/**
 * Detailed Cartoon Black Pickup Truck with Cab, Tinted Windshield, Chrome Grille, 4 Wheels & Open Cargo Bed.
 */
export function buildPickupTruck() {
  const g = new THREE.Group();
  const bodyMat = makeMaterialByFinish('#1e293b', 'painted_metal');
  const cabMat = makeMaterialByFinish('#0f172a', 'painted_metal');
  const glassMat = makeMaterialByFinish('#38bdf8', 'glass_facade');
  const chromeMat = makeMaterialByFinish('#e2e8f0', 'brushed_chrome');
  const tireMat = new THREE.MeshStandardMaterial({ color: '#09090b', roughness: 0.88 });

  // Lower chassis + hood + open truck bed walls
  const chassis = new THREE.Mesh(new THREE.BoxGeometry(3.2, 0.52, 1.55), bodyMat);
  chassis.position.set(0, 0.56, 0);
  chassis.castShadow = true;
  const cab = new THREE.Mesh(new THREE.BoxGeometry(1.18, 0.64, 1.44), cabMat);
  cab.position.set(-0.45, 1.12, 0);
  cab.castShadow = true;
  const windshield = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.46, 1.28), glassMat);
  windshield.position.set(-1.02, 1.12, 0);
  const bedFloor = new THREE.Mesh(new THREE.BoxGeometry(1.48, 0.08, 1.42), new THREE.MeshStandardMaterial({ color: '#334155', roughness: 0.7 }));
  bedFloor.position.set(0.84, 0.84, 0);
  const tailGate = new THREE.Mesh(new THREE.BoxGeometry(0.10, 0.42, 1.48), bodyMat);
  tailGate.position.set(1.56, 0.98, 0);
  const bumper = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.16, 1.60), chromeMat);
  bumper.position.set(-1.62, 0.42, 0);
  g.add(chassis, cab, windshield, bedFloor, tailGate, bumper);

  for (const wx of [-0.95, 0.95]) {
    for (const wz of [-0.78, 0.78]) {
      const wheel = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.32, 0.24, 18), tireMat);
      wheel.rotation.x = Math.PI / 2;
      wheel.position.set(wx, 0.32, wz);
      wheel.castShadow = true;
      g.add(wheel);
    }
  }
  return g;
}

/**
 * Generic data-driven composite builder for any extensible prop declared in `OBJECT_KNOWLEDGE_BASE`.
 */
function buildCompositeFromRecipe(recipe) {
  const g = new THREE.Group();
  for (const p of (recipe.composite_parts || [])) {
    const [sx, sy, sz] = p.size || [0.3, 0.3, 0.3];
    let geo;
    if (p.shape === 'sphere') geo = new THREE.SphereGeometry(sx, 20, 16);
    else if (p.shape === 'cylinder') geo = new THREE.CylinderGeometry(sx, sz || sx, sy, 18);
    else if (p.shape === 'cone') geo = new THREE.ConeGeometry(sx, sy, 18);
    else if (p.shape === 'torus') geo = new THREE.TorusGeometry(sx, sy, 12, 24);
    else if (p.shape === 'capsule') geo = new THREE.CapsuleGeometry(sx, sy, 8, 12);
    else geo = new THREE.BoxGeometry(sx, sy, sz);

    const mesh = new THREE.Mesh(geo, makeMaterialByFinish(p.color || '#f8fafc', p.finish || recipe.surface_finish));
    if (p.offset) mesh.position.set(p.offset[0], p.offset[1], p.offset[2]);
    if (p.rotation) mesh.rotation.set(p.rotation[0], p.rotation[1], p.rotation[2]);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    g.add(mesh);
  }
  return g;
}

/**
 * Master knowledge-driven builder invoked by `stage3d.html`.
 * Returns a THREE.Group if handled cleanly by the Object Knowledge Library, or `null` to defer to inline fallback props.
 */
export function buildKnowledgeObject(propSpec, recipe, ctx) {
  const ptype = propSpec.prop_type;
  const key = recipe ? recipe.builder_key : ptype;
  const g = new THREE.Group();
  g.position.set(propSpec.position[0], propSpec.position[1], propSpec.position[2]);
  g.rotation.y = propSpec.rotation_y || 0;
  g.scale.setScalar(propSpec.scale || 1.0);

  if (key === 'cumulus_cloud') {
    g.add(buildCumulusCloud(0, 1.0));
    if (ctx.breezeMeshes) ctx.breezeMeshes.push(g);
    return g;
  }
  if (key === 'latex_balloon_cluster' || ptype === 'balloon_bundle_red' || ptype === 'balloon_bunch') {
    const colors = ptype === 'balloon_bundle_red'
      ? ['#ef4444', '#dc2626']
      : ['#ef4444', '#00f5d4', '#ffbe0b', '#8338ec'];
    const count = colors.length;
    for (let i = 0; i < count; i++) {
      const ang = ((i - (count - 1) * 0.5) * 0.34);
      const b = buildLatexBalloon(colors[i], ptype === 'balloon_bundle_red' ? 1.05 : 0.85, 0.55);
      b.position.set((i - (count - 1) * 0.5) * 0.30, 0.62 + (i % 2) * 0.14, (i % 2) * 0.08);
      b.rotation.z = -ang * 0.5;
      g.add(b);
    }
    if (ctx.breezeMeshes) ctx.breezeMeshes.push(g);
    return g;
  }
  if (key === 'airliner_jet' || ptype === 'flying_airplane') {
    const jet = buildAirlinerJet(null);
    g.add(jet);
    if (ctx.flyingAirplanes) ctx.flyingAirplanes.push(g);
    return g;
  }
  if (key === 'hydraulic_lift_chair' || ptype === 'hydraulic_lift_chair') {
    const chair = buildHydraulicLiftChair(ctx.dynamicLiftChairs);
    g.add(chair);
    // Keep outer group's position tracked properly by lift updater
    chair.userData.hostGroup = g;
    if (ctx.dynamicLiftChairs && ctx.dynamicLiftChairs.length > 0) {
      ctx.dynamicLiftChairs[ctx.dynamicLiftChairs.length - 1].group = g;
    }
    return g;
  }
  if (key === 'golden_skyline' || ptype === 'skyscraper_city') {
    g.add(buildGoldenSkyline());
    return g;
  }
  if (key === 'tropical_giant_leaf' || ptype === 'jungle_giant_leaf') {
    g.add(buildTropicalGiantLeaf());
    return g;
  }
  if (key === 'sausage_on_plate' || ptype === 'sausage_prop') {
    g.add(buildSausageOnPlate());
    return g;
  }
  if (key === 'hollow_oak_tree' || ptype === 'hollow_tree_trunk') {
    g.add(buildHollowOakTree(ctx.breezeMeshes));
    return g;
  }
  if (key === 'stylized_forest_tree' || ptype === 'oak_tree' || ptype === 'pine_tree') {
    const seed = Math.abs(Math.round((propSpec.position[0] * 13 + propSpec.position[2] * 7)));
    g.add(buildStylizedForestTree(seed, propSpec.target_height_m || 3.4));
    if (ctx.breezeMeshes) ctx.breezeMeshes.push(g);
    return g;
  }
  if (key === 'soccer_ball' || ptype === 'soccer_ball') {
    const ball = new THREE.Mesh(
      new THREE.SphereGeometry(0.18, 20, 16),
      new THREE.MeshPhysicalMaterial({ map: createSoccerBallTex(), roughness: 0.25, clearcoat: 0.6 })
    );
    ball.position.y = 0.18;
    ball.castShadow = true;
    g.add(ball);
    return g;
  }
  if (key === 'giant_cockroach' || ptype === 'giant_cockroach') {
    g.add(buildGiantCockroach());
    if (ctx.breezeMeshes) ctx.breezeMeshes.push(g);
    return g;
  }
  if (key === 'cooking_pot' || ptype === 'cooking_pot') {
    g.add(buildCookingPot());
    return g;
  }
  if (key === 'cleaning_broom' || ptype === 'cleaning_broom') {
    g.add(buildCleaningBroom());
    return g;
  }
  if (key === 'computer_desk' || ptype === 'computer_desk') {
    g.add(buildComputerDesk());
    return g;
  }
  if (key === 'stone_maze_walls' || ptype === 'stone_maze_walls') {
    g.add(buildStoneMazeWalls());
    return g;
  }
  if (key === 'laser_beam' || ptype === 'laser_beam') {
    g.add(buildLaserBeam());
    return g;
  }
  if (key === 'hero_shield' || ptype === 'hero_shield') {
    g.add(buildHeroShield());
    if (ctx.breezeMeshes) ctx.breezeMeshes.push(g);
    return g;
  }
  if (key === 'angry_bull' || ptype === 'angry_bull') {
    g.add(buildAngryBull());
    return g;
  }
  if (key === 'camouflage_bush' || ptype === 'camouflage_bush') {
    g.add(buildCamouflageBush());
    if (ctx.breezeMeshes) ctx.breezeMeshes.push(g);
    return g;
  }
  if (key === 'strength_orb' || ptype === 'strength_orb') {
    g.add(buildStrengthOrb());
    if (ctx.breezeMeshes) ctx.breezeMeshes.push(g);
    return g;
  }
  if (key === 'musical_staircase' || ptype === 'musical_staircase') {
    g.add(buildMusicalStaircase());
    return g;
  }
  if (key === 'musical_note' || ptype === 'musical_note') {
    g.add(buildFloatingMusicalNote());
    if (ctx.breezeMeshes) ctx.breezeMeshes.push(g);
    return g;
  }
  if (key === 'macarons' || ptype === 'macarons') {
    g.add(buildMacarons());
    if (ctx.breezeMeshes) ctx.breezeMeshes.push(g);
    return g;
  }
  if (key === 'giant_turkey_leg' || ptype === 'giant_turkey_leg') {
    g.add(buildGiantTurkeyLeg());
    return g;
  }
  if (key === 'folding_chair' || ptype === 'folding_chair') {
    g.add(buildFoldingChair());
    return g;
  }
  if (key === 'brick_wall' || ptype === 'brick_wall') {
    g.add(buildBrickWall());
    return g;
  }
  if (key === 'pickup_truck' || ptype === 'pickup_truck') {
    g.add(buildPickupTruck());
    return g;
  }
  const genFn = GENERATED_OBJECT_BUILDERS[ptype] || GENERATED_OBJECT_BUILDERS[key];
  if (typeof genFn === 'function') {
    g.add(genFn(THREE, makeMaterialByFinish));
    return g;
  }
  if (key === 'composite_recipe' && recipe && recipe.composite_parts && recipe.composite_parts.length > 0) {
    g.add(buildCompositeFromRecipe(recipe));
    return g;
  }
  return null;
}
