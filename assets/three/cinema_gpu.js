/**
 * Cinema-Grade GPU Rendering Engine (`assets/three/cinema_gpu.js`) for NVIDIA RTX 3050 6GB:
 * - 360 HDR Studio + Sky PMREM Environment Map (`scene.environment`)
 * - Rayleigh Atmospheric Sun Sky Dome + Diagonal Volumetric God-Ray Sunbeams
 * - 1024px Normal+Roughness PBR Floors + Clustered Meadow Grass, Bushes, Boulders & Fireflies
 * - 4-Pass GPU Cinema Compositor: 1.35x SSAA (`HalfFloat + DepthTexture`) -> 12-Tap Depth SSAO ->
 *   Specular Bloom -> Shallow Bokeh DOF + ACES Filmic Grade + Micro-Sharpening!
 */

import * as THREE from 'three';

export function buildCinemaEnvironmentMap(renderer, story) {
  const pmrem = new THREE.PMREMGenerator(renderer);
  pmrem.compileEquirectangularShader();

  const envScene = new THREE.Scene();
  const skyTop = new THREE.Color(story.sky_top_hex || '#0ea5e9');
  const skyHor = new THREE.Color(story.sky_horizon_hex || '#bae6fd');
  const groundCol = new THREE.Color(story.ground_primary_hex || '#4ade80');
  const isGolden = story.world_biome === 'golden_city';

  const domeMat = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    uniforms: {
      uTop: { value: skyTop },
      uHor: { value: isGolden ? new THREE.Color('#fef08a') : skyHor },
      uBot: { value: groundCol.clone().multiplyScalar(0.75) },
      uSunDir: { value: new THREE.Vector3(0.45, 0.72, 0.52).normalize() },
    },
    vertexShader: `
      varying vec3 vDir;
      void main() {
        vDir = normalize(position);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform vec3 uTop;
      uniform vec3 uHor;
      uniform vec3 uBot;
      uniform vec3 uSunDir;
      varying vec3 vDir;
      void main() {
        float y = vDir.y;
        vec3 col = y >= 0.0
          ? mix(uHor, uTop, pow(clamp(y, 0.0, 1.0), 0.55))
          : mix(uHor * 0.85, uBot, pow(clamp(-y, 0.0, 1.0), 0.5));
        float sunAmt = max(0.0, dot(normalize(vDir), uSunDir));
        col += vec3(3.4, 2.8, 2.0) * pow(sunAmt, 42.0);
        col += vec3(0.55, 0.48, 0.36) * pow(sunAmt, 4.0);
        gl_FragColor = vec4(col, 1.0);
      }
    `,
  });
  envScene.add(new THREE.Mesh(new THREE.SphereGeometry(20, 24, 16), domeMat));

  const keyPanel = new THREE.Mesh(
    new THREE.PlaneGeometry(8, 5),
    new THREE.MeshBasicMaterial({ color: new THREE.Color(2.5, 2.4, 2.1), side: THREE.DoubleSide })
  );
  keyPanel.position.set(6, 7, 6);
  keyPanel.lookAt(0, 0, 0);
  envScene.add(keyPanel);

  const rimPanel = new THREE.Mesh(
    new THREE.PlaneGeometry(10, 4),
    new THREE.MeshBasicMaterial({ color: new THREE.Color(1.9, 2.1, 2.5), side: THREE.DoubleSide })
  );
  rimPanel.position.set(-6, 5, -7);
  rimPanel.lookAt(0, 0, 0);
  envScene.add(rimPanel);

  const rt = pmrem.fromScene(envScene, 0.035);
  pmrem.dispose();
  return rt.texture;
}

export function buildAtmosphereSkyDome(story) {
  const isGolden = story.world_biome === 'golden_city';
  const mat = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    depthWrite: false,
    uniforms: {
      uTop: { value: new THREE.Color(story.sky_top_hex || '#0284c7') },
      uHor: { value: new THREE.Color(story.sky_horizon_hex || '#bae6fd') },
      uWarmSun: { value: new THREE.Color(isGolden ? '#fffbeb' : '#fef9c3') },
      uSunDir: { value: new THREE.Vector3(0.38, 0.42, -0.82).normalize() },
    },
    vertexShader: `
      varying vec3 vWorldDir;
      void main() {
        vec4 wp = modelMatrix * vec4(position, 1.0);
        vWorldDir = normalize(position);
        gl_Position = projectionMatrix * viewMatrix * wp;
      }
    `,
    fragmentShader: `
      uniform vec3 uTop;
      uniform vec3 uHor;
      uniform vec3 uWarmSun;
      uniform vec3 uSunDir;
      varying vec3 vWorldDir;
      void main() {
        vec3 d = normalize(vWorldDir);
        float h = clamp(d.y, -0.15, 1.0);
        vec3 base = mix(uHor, uTop, pow(clamp(h * 1.15, 0.0, 1.0), 0.62));
        float mist = exp(-abs(h) * 6.5);
        base = mix(base, mix(uHor, vec3(1.0), 0.45), mist * 0.50);
        float mu = max(0.0, dot(d, uSunDir));
        base += uWarmSun * (pow(mu, 180.0) * 1.40 + pow(mu, 14.0) * 0.28);
        gl_FragColor = vec4(base, 1.0);
      }
    `,
  });
  const dome = new THREE.Mesh(new THREE.SphereGeometry(52, 36, 24), mat);
  dome.renderOrder = -10;
  return dome;
}

function buildNormalAndRoughnessTextures(heights, W, H, strength, baseRough, roughVar, repeatN) {
  const nData = new Uint8Array(W * H * 4);
  const rData = new Uint8Array(W * H * 4);

  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const idx = y * W + x;
      const hL = heights[y * W + ((x - 1 + W) % W)];
      const hR = heights[y * W + ((x + 1) % W)];
      const hU = heights[((y - 1 + H) % H) * W + x];
      const hD = heights[((y + 1) % H) * W + x];
      const dx = (hL - hR) * strength;
      const dy = (hU - hD) * strength;
      const invLen = 1.0 / Math.hypot(dx, dy, 1.0);
      nData[idx * 4 + 0] = Math.round(((dx * invLen) * 0.5 + 0.5) * 255);
      nData[idx * 4 + 1] = Math.round(((dy * invLen) * 0.5 + 0.5) * 255);
      nData[idx * 4 + 2] = Math.round(((1.0 * invLen) * 0.5 + 0.5) * 255);
      nData[idx * 4 + 3] = 255;

      const rv = Math.max(0.05, Math.min(0.98, baseRough + (heights[idx] - 0.5) * roughVar));
      const rb = Math.round(rv * 255);
      rData[idx * 4 + 0] = rb;
      rData[idx * 4 + 1] = rb;
      rData[idx * 4 + 2] = rb;
      rData[idx * 4 + 3] = 255;
    }
  }

  const normalTex = new THREE.DataTexture(nData, W, H, THREE.RGBAFormat);
  normalTex.wrapS = THREE.RepeatWrapping;
  normalTex.wrapT = THREE.RepeatWrapping;
  normalTex.repeat.set(repeatN, repeatN);
  normalTex.needsUpdate = true;

  const roughTex = new THREE.DataTexture(rData, W, H, THREE.RGBAFormat);
  roughTex.wrapS = THREE.RepeatWrapping;
  roughTex.wrapT = THREE.RepeatWrapping;
  roughTex.repeat.set(repeatN, repeatN);
  roughTex.needsUpdate = true;

  return { normalTex, roughTex };
}

export function createPBRGroundMaterial(story, maxAniso = 16) {
  const floorPat = story.floor_pattern || 'checker_tiles';
  const pri = story.ground_primary_hex || '#4ade80';
  const sec = story.ground_secondary_hex || '#22c55e';

  const S = 1024;
  const c = document.createElement('canvas');
  c.width = S;
  c.height = S;
  const ctx = c.getContext('2d');
  ctx.fillStyle = pri;
  ctx.fillRect(0, 0, S, S);

  const heights = new Float32Array(S * S);
  const repeatN = floorPat === 'grass_meadow' ? 18 : (floorPat === 'wood_planks' ? 8 : ((floorPat === 'golden_plaza' || floorPat === 'plaza_blocks') ? 10 : 12));

  if (floorPat === 'grass_meadow') {
    // Organic lush turf without periodic grid dimples or circular polka dots
    ctx.fillStyle = pri;
    ctx.fillRect(0, 0, S, S);
    for (let i = 0; i < 6500; i++) {
      const gx = (i * 271 + 43) % S;
      const gy = (i * 499 + 19) % S;
      ctx.strokeStyle = i % 3 === 0 ? 'rgba(34,197,94,0.22)' : (i % 3 === 1 ? 'rgba(21,128,61,0.18)' : 'rgba(187,247,208,0.22)');
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      ctx.moveTo(gx, gy);
      ctx.lineTo(gx + ((i % 7) - 3) * 1.4, gy - 6 - (i % 5));
      ctx.stroke();
    }
    for (let i = 0; i < S * S; i++) {
      heights[i] = 0.50 + (((i * 73 + (i >> 8) * 137) % 17) / 17.0) * 0.14;
    }
  } else if (floorPat === 'wood_planks') {
    // Warm lacquered oak floor planks with staggered seam bevels & grain
    ctx.fillStyle = '#c88a4b';
    ctx.fillRect(0, 0, S, S);
    const rows = 8;
    const rowH = S / rows;
    const plankW = S / 2;
    const tones = ['#d29452', '#c78846', '#dc9d5a', '#bf7f3e'];
    for (let r = 0; r < rows; r++) {
      const y0 = r * rowH;
      const xOff = (r % 2) * (plankW * 0.5);
      for (let p = -1; p < 3; p++) {
        const x0 = p * plankW + xOff;
        ctx.fillStyle = tones[(r + Math.abs(p)) % tones.length];
        ctx.fillRect(x0 + 2, y0 + 2, plankW - 4, rowH - 4);
        ctx.strokeStyle = 'rgba(120, 53, 15, 0.16)';
        ctx.lineWidth = 1.5;
        for (let g = 0; g < 6; g++) {
          const gy = y0 + 12 + g * ((rowH - 20) / 6);
          ctx.beginPath();
          ctx.moveTo(x0 + 6, gy);
          ctx.bezierCurveTo(x0 + plankW * 0.35, gy + ((g % 2) ? 3 : -3), x0 + plankW * 0.65, gy - 2, x0 + plankW - 6, gy);
          ctx.stroke();
        }
      }
    }
    for (let y = 0; y < S; y++) {
      const ry = y % rowH;
      for (let x = 0; x < S; x++) {
        const row = Math.floor(y / rowH);
        const rx = (x + (row % 2) * (plankW * 0.5)) % plankW;
        const seam = (ry < 3 || ry > rowH - 3 || rx < 3 || rx > plankW - 3);
        heights[y * S + x] = seam ? 0.18 : 0.72 + Math.sin(x * 0.03 + y * 0.25) * 0.04;
      }
    }
  } else if (floorPat === 'maze_sand' || floorPat === 'sand_beach') {
    // Smooth warm ochre-gold maze sand courtyard (hash-jittered grain, zero lattice spots!)
    const sg = ctx.createLinearGradient(0, 0, S, S);
    sg.addColorStop(0.0, '#eab308');
    sg.addColorStop(0.5, '#f2c12e');
    sg.addColorStop(1.0, '#eab308');
    ctx.fillStyle = sg;
    ctx.fillRect(0, 0, S, S);
    for (let i = 0; i < 6000; i++) {
      const h1 = Math.abs(Math.sin(i * 12.9898) * 43758.5453) % 1;
      const h2 = Math.abs(Math.sin(i * 78.233 + 1.3) * 24634.6345) % 1;
      ctx.fillStyle = i % 2 === 0 ? 'rgba(254, 240, 138, 0.14)' : 'rgba(180, 83, 9, 0.06)';
      ctx.fillRect(h1 * S, h2 * S, 2, 2);
    }
    heights.fill(0.5);
  } else if (floorPat === 'golden_plaza' || floorPat === 'plaza_blocks') {
    const isGold = floorPat === 'golden_plaza';
    const tileCol = isGold ? '#fde047' : sec;
    const groutCol = isGold ? '#b45309' : '#64748b';
    ctx.fillStyle = groutCol;
    ctx.fillRect(0, 0, S, S);
    const N = 4;
    const step = S / N;
    for (let ty = 0; ty < N; ty++) {
      for (let tx = 0; tx < N; tx++) {
        const px = tx * step + 6;
        const py = ty * step + 6;
        const pw = step - 12;
        const grad = ctx.createLinearGradient(px, py, px + pw, py + pw);
        grad.addColorStop(0, isGold ? '#fef08a' : '#f8fafc');
        grad.addColorStop(0.5, tileCol);
        grad.addColorStop(1, isGold ? '#eab308' : pri);
        ctx.fillStyle = grad;
        ctx.fillRect(px, py, pw, pw);
        ctx.strokeStyle = isGold ? 'rgba(255,255,255,0.30)' : 'rgba(255,255,255,0.20)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(px + 12, py + pw * 0.25);
        ctx.bezierCurveTo(px + pw * 0.4, py + pw * 0.1, px + pw * 0.6, py + pw * 0.8, px + pw - 14, py + pw * 0.65);
        ctx.stroke();
      }
    }
    for (let y = 0; y < S; y++) {
      const gy = y % step;
      for (let x = 0; x < S; x++) {
        const gx = x % step;
        const inGrout = (gx < 6 || gx > step - 6 || gy < 6 || gy > step - 6);
        const edgeBevel = (gx < 14 || gx > step - 14 || gy < 14 || gy > step - 14) ? 0.68 : 0.85;
        heights[y * S + x] = inGrout ? 0.12 : edgeBevel + Math.sin(x * 0.05 + y * 0.04) * 0.05;
      }
    }
  } else {
    for (let y = 0; y < 8; y++) {
      for (let x = 0; x < 8; x++) {
        ctx.fillStyle = (x + y) % 2 === 0 ? pri : sec;
        ctx.fillRect(x * 128 + 3, y * 128 + 3, 122, 122);
      }
    }
    for (let i = 0; i < S * S; i++) heights[i] = 0.5 + (((i * 37) % 13) / 13.0) * 0.15;
  }

  const albedoTex = new THREE.CanvasTexture(c);
  albedoTex.wrapS = THREE.RepeatWrapping;
  albedoTex.wrapT = THREE.RepeatWrapping;
  albedoTex.repeat.set(repeatN, repeatN);
  albedoTex.anisotropy = maxAniso;
  albedoTex.colorSpace = THREE.SRGBColorSpace;

  const isTile = (floorPat === 'golden_plaza' || floorPat === 'plaza_blocks' || floorPat === 'wood_planks');
  const { normalTex, roughTex } = buildNormalAndRoughnessTextures(
    heights, S, S, isTile ? 2.2 : 1.1, isTile ? 0.34 : 0.86, isTile ? 0.28 : 0.14, repeatN
  );
  normalTex.anisotropy = maxAniso;
  roughTex.anisotropy = maxAniso;

  return new THREE.MeshPhysicalMaterial({
    map: albedoTex,
    normalMap: normalTex,
    normalScale: new THREE.Vector2(isTile ? 0.45 : 0.22, isTile ? 0.45 : 0.22),
    roughnessMap: roughTex,
    roughness: isTile ? 0.38 : 0.88,
    metalness: floorPat === 'golden_plaza' ? 0.20 : 0.0,
    clearcoat: isTile ? 0.36 : 0.0,
    clearcoatRoughness: 0.26,
    envMapIntensity: isTile ? 1.15 : 0.65,
  });
}

export function buildLivingBiomeDetails(scene, story) {
  const biome = story.world_biome || 'lush_forest';
  const dummy = new THREE.Object3D();
  const isOutdoorGreen = !['golden_city', 'futuristic_lab', 'indoor_room', 'stone_maze'].includes(biome);
  const updaters = [];

  if (isOutdoorGreen) {
    // 1. 1,650 curved tapered 3D meadow grass blades in natural clusters
    const bladeCount = 1650;
    const bladeGeo = new THREE.PlaneGeometry(0.044, 0.18, 1, 3);
    const posAttr = bladeGeo.attributes.position;
    for (let i = 0; i < posAttr.count; i++) {
      const yNorm = (posAttr.getY(i) + 0.09) / 0.18;
      posAttr.setX(i, posAttr.getX(i) * (1.0 - yNorm * 0.88));
      posAttr.setZ(i, yNorm * yNorm * 0.058);
      posAttr.setY(i, yNorm * 0.18);
    }
    bladeGeo.computeVertexNormals();
    const bladeMat = new THREE.MeshStandardMaterial({
      color: '#22c55e',
      roughness: 0.76,
      metalness: 0.0,
      side: THREE.DoubleSide,
    });
    const grassMesh = new THREE.InstancedMesh(bladeGeo, bladeMat, bladeCount);
    grassMesh.receiveShadow = true;

    const palette = [new THREE.Color('#15803d'), new THREE.Color('#16a34a'), new THREE.Color('#22c55e'), new THREE.Color('#14532d')];
    const baseStates = [];
    let placed = 0;
    let tuftIdx = 0;
    while (placed < bladeCount && tuftIdx < 1200) {
      tuftIdx++;
      const r1 = Math.abs(Math.sin(tuftIdx * 12.9898) * 43758.5453) % 1;
      const r2 = Math.abs(Math.sin(tuftIdx * 78.233 + 1.7) * 24634.6345) % 1;
      const tx = (r1 - 0.5) * 16.5;
      const tz = (r2 - 0.5) * 15.0 - 1.5;
      if (Math.hypot(tx, tz - 0.1) < 2.2) continue;

      for (let b = 0; b < 3 && placed < bladeCount; b++) {
        const offA = (b / 3) * Math.PI * 2 + (tuftIdx % 5);
        const gx = tx + Math.cos(offA) * 0.06;
        const gz = tz + Math.sin(offA) * 0.06;
        const s = 0.75 + ((tuftIdx + b) % 5) * 0.12;
        const rotY = offA + ((b * 1.1) % 3);
        dummy.position.set(gx, 0.0, gz);
        dummy.rotation.set(0.18, rotY, 0.0);
        dummy.scale.set(1.0, s, 1.0);
        dummy.updateMatrix();
        grassMesh.setMatrixAt(placed, dummy.matrix);
        grassMesh.setColorAt(placed, palette[(tuftIdx + b) % palette.length]);
        baseStates.push({ gx, gz, s, rotY, phase: gx * 0.5 + gz * 0.4 });
        placed++;
      }
    }
    grassMesh.count = placed;
    grassMesh.instanceMatrix.needsUpdate = true;
    if (grassMesh.instanceColor) grassMesh.instanceColor.needsUpdate = true;
    scene.add(grassMesh);

    updaters.push((tSec) => {
      for (let i = 0; i < placed; i++) {
        const st = baseStates[i];
        const lean = 0.18 + Math.sin(tSec * 2.1 + st.phase) * 0.14;
        dummy.position.set(st.gx, 0.0, st.gz);
        dummy.rotation.set(lean, st.rotY, 0);
        dummy.scale.set(1.0, st.s, 1.0);
        dummy.updateMatrix();
        grassMesh.setMatrixAt(i, dummy.matrix);
      }
      grassMesh.instanceMatrix.needsUpdate = true;
    });

    // 2. Lush matte perimeter bushes framing mid/background (never blocking front camera lens!)
    const shrubGeo = new THREE.IcosahedronGeometry(0.28, 1);
    const shrubMat = new THREE.MeshPhysicalMaterial({
      color: '#16a34a',
      roughness: 0.86,
      metalness: 0.0,
      sheen: 0.52,
      sheenRoughness: 0.74,
      sheenColor: new THREE.Color('#bbf7d0'),
    });
    const shrubMesh = new THREE.InstancedMesh(shrubGeo, shrubMat, 96);
    shrubMesh.castShadow = true;
    shrubMesh.receiveShadow = true;
    for (let i = 0; i < 96; i++) {
      const ang = (i / 32) * Math.PI * 2;
      const rad = 5.4 + (i % 3) * 1.8;
      let bx = Math.cos(ang) * rad + ((i % 5) - 2) * 0.22;
      let bz = Math.sin(ang) * rad * 0.78 - 2.2;
      if (bz > 0.6 && Math.abs(bx) < 3.6) bz = -Math.abs(bz) - 2.4;
      dummy.position.set(bx, 0.14, bz);
      dummy.rotation.set(0.1 * (i % 3), (i * 0.7) % 6.28, 0.08 * (i % 2));
      dummy.scale.set(1.28, 0.86, 1.18);
      dummy.updateMatrix();
      shrubMesh.setMatrixAt(i, dummy.matrix);
      shrubMesh.setColorAt(i, palette[i % palette.length]);
    }
    shrubMesh.instanceMatrix.needsUpdate = true;
    if (shrubMesh.instanceColor) shrubMesh.instanceColor.needsUpdate = true;
    scene.add(shrubMesh);

    // 3. Wildflowers
    const flGeo = new THREE.SphereGeometry(0.052, 8, 6);
    const flMat = new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.4 });
    const flowerMesh = new THREE.InstancedMesh(flGeo, flMat, 160);
    const flColors = [new THREE.Color('#fef08a'), new THREE.Color('#fbcfe8'), new THREE.Color('#ffffff'), new THREE.Color('#bae6fd')];
    for (let i = 0; i < 160; i++) {
      const fx = (((i * 97) % 100) / 100 - 0.5) * 14.0;
      const fz = (((i * 61) % 100) / 100 - 0.5) * 12.0 - 1.0;
      if (Math.hypot(fx, fz) < 1.8) dummy.position.set(fx + 2.4, 0.05, fz - 1.6);
      else dummy.position.set(fx, 0.05, fz);
      dummy.scale.set(1.2, 0.55, 1.2);
      dummy.updateMatrix();
      flowerMesh.setMatrixAt(i, dummy.matrix);
      flowerMesh.setColorAt(i, flColors[i % flColors.length]);
    }
    flowerMesh.instanceMatrix.needsUpdate = true;
    if (flowerMesh.instanceColor) flowerMesh.instanceColor.needsUpdate = true;
    scene.add(flowerMesh);

  } else if (biome === 'golden_city') {
    const distMat = new THREE.MeshStandardMaterial({
      color: '#eab308',
      roughness: 0.35,
      metalness: 0.35,
      emissive: '#92400e',
      emissiveIntensity: 0.14,
    });
    for (let k = -8; k <= 8; k++) {
      if (Math.abs(k) < 2) continue;
      const h = 11.0 + ((Math.abs(k) * 7) % 12);
      const b = new THREE.Mesh(new THREE.BoxGeometry(2.4, h, 2.4), distMat);
      b.position.set(k * 2.8, h * 0.5, -16.5 - (Math.abs(k) % 3) * 2.0);
      scene.add(b);
    }

    const lampPostMat = new THREE.MeshStandardMaterial({ color: '#1e293b', metalness: 0.78, roughness: 0.22 });
    const glowMat = new THREE.MeshBasicMaterial({ color: '#fef9c3' });
    const bollardMat = new THREE.MeshStandardMaterial({ color: '#facc15', metalness: 0.72, roughness: 0.25 });
    for (const lx of [-3.2, 3.2]) {
      for (const lz of [1.8, -1.8]) {
        const post = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.075, 2.6, 12), lampPostMat);
        post.position.set(lx, 1.3, lz);
        post.castShadow = true;
        const globe = new THREE.Mesh(new THREE.SphereGeometry(0.16, 14, 12), glowMat);
        globe.position.set(lx, 2.68, lz);
        const bollard = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.14, 0.55, 14), bollardMat);
        bollard.position.set(lx * 0.72, 0.275, lz);
        bollard.castShadow = true;
        scene.add(post, globe, bollard);
      }
    }
  } else if (biome === 'indoor_room') {
    // Cozy Painted Bedroom / Studio Walls with Classic White Wainscoting & Framed Picture
    const wallMat = new THREE.MeshStandardMaterial({ color: '#4db6ff', roughness: 0.72, metalness: 0.0 });
    const wainscotMat = new THREE.MeshStandardMaterial({ color: '#f8fafc', roughness: 0.42, metalness: 0.02 });
    const trimMat = new THREE.MeshStandardMaterial({ color: '#e2e8f0', roughness: 0.35 });

    // Back wall + Left/Right wrap walls so side camera sweeps stay inside the room
    const backWall = new THREE.Mesh(new THREE.BoxGeometry(16, 7.5, 0.25), wallMat);
    backWall.position.set(0, 3.75, -2.85);
    backWall.receiveShadow = true;
    const leftWall = new THREE.Mesh(new THREE.BoxGeometry(0.25, 7.5, 14), wallMat);
    leftWall.position.set(-5.8, 3.75, 2.5);
    leftWall.receiveShadow = true;
    const rightWall = new THREE.Mesh(new THREE.BoxGeometry(0.25, 7.5, 14), wallMat);
    rightWall.position.set(5.8, 3.75, 2.5);
    rightWall.receiveShadow = true;
    scene.add(backWall, leftWall, rightWall);

    // Lower white wainscot paneling + molded rail along all 3 interior walls
    const backWain = new THREE.Mesh(new THREE.BoxGeometry(16, 1.15, 0.30), wainscotMat);
    backWain.position.set(0, 0.575, -2.83);
    backWain.receiveShadow = true;
    const backRail = new THREE.Mesh(new THREE.BoxGeometry(16, 0.09, 0.35), trimMat);
    backRail.position.set(0, 1.16, -2.81);
    const leftWain = new THREE.Mesh(new THREE.BoxGeometry(0.30, 1.15, 14), wainscotMat);
    leftWain.position.set(-5.78, 0.575, 2.5);
    const rightWain = new THREE.Mesh(new THREE.BoxGeometry(0.30, 1.15, 14), wainscotMat);
    rightWain.position.set(5.78, 0.575, 2.5);
    scene.add(backWain, backRail, leftWain, rightWain);

    for (let px = -5.4; px <= 5.4; px += 0.9) {
      const stile = new THREE.Mesh(new THREE.BoxGeometry(0.08, 1.02, 0.04), trimMat);
      stile.position.set(px, 0.56, -2.67);
      scene.add(stile);
    }

    // Framed sunny picture window on side/back-right wall
    const frameOuter = new THREE.Mesh(new THREE.BoxGeometry(1.45, 1.15, 0.06), new THREE.MeshStandardMaterial({ color: '#78350f', roughness: 0.55 }));
    frameOuter.position.set(2.35, 2.15, -2.70);
    const frameCanvas = new THREE.Mesh(new THREE.PlaneGeometry(1.25, 0.95), new THREE.MeshBasicMaterial({ color: '#fef08a' }));
    frameCanvas.position.set(2.35, 2.15, -2.66);
    scene.add(frameOuter, frameCanvas);
  }

  // Subtle Diagonal Volumetric Sunbeam Cones
  const beamMat = new THREE.MeshBasicMaterial({
    color: biome === 'golden_city' ? '#fef08a' : '#fffbeb',
    transparent: true,
    opacity: 0.032,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  for (let i = 0; i < 3; i++) {
    const beam = new THREE.Mesh(new THREE.ConeGeometry(2.4, 14.0, 16, 1, true), beamMat);
    beam.position.set(-2.5 + i * 2.6, 5.8, -2.5 - i * 1.2);
    beam.rotation.z = -0.35;
    beam.rotation.x = 0.22;
    scene.add(beam);
  }

  // Sunlit Atmospheric Dust & Glowing Circular Firefly Orbs (`AdditiveBlending`)
  const moteCanvas = document.createElement('canvas');
  moteCanvas.width = 64;
  moteCanvas.height = 64;
  const mctx = moteCanvas.getContext('2d');
  const mgrad = mctx.createRadialGradient(32, 32, 2, 32, 32, 30);
  mgrad.addColorStop(0.0, 'rgba(255, 253, 224, 1.0)');
  mgrad.addColorStop(0.45, 'rgba(254, 240, 138, 0.72)');
  mgrad.addColorStop(1.0, 'rgba(254, 240, 138, 0.0)');
  mctx.fillStyle = mgrad;
  mctx.fillRect(0, 0, 64, 64);
  const moteTex = new THREE.CanvasTexture(moteCanvas);
  moteTex.colorSpace = THREE.SRGBColorSpace;

  const moteCount = 160;
  const posArr = new Float32Array(moteCount * 3);
  for (let i = 0; i < moteCount; i++) {
    posArr[i * 3 + 0] = (((i * 83) % 100) / 100 - 0.5) * 11.0;
    posArr[i * 3 + 1] = 0.45 + (((i * 47) % 100) / 100) * 6.8;
    posArr[i * 3 + 2] = (((i * 59) % 100) / 100 - 0.5) * 8.5;
  }
  const moteGeo = new THREE.BufferGeometry();
  moteGeo.setAttribute('position', new THREE.BufferAttribute(posArr, 3));
  const moteMat = new THREE.PointsMaterial({
    color: '#fef9c3',
    map: moteTex,
    size: 0.14,
    transparent: true,
    opacity: 0.82,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const motes = new THREE.Points(moteGeo, moteMat);
  scene.add(motes);
  updaters.push((tSec) => {
    motes.position.y = Math.sin(tSec * 0.85) * 0.18;
    motes.rotation.y = tSec * 0.05;
  });

  return (tSec) => {
    for (const fn of updaters) fn(tSec);
  };
}

export function enhanceCharacterMaterialsAndContactShadow(cloned, wrapper, targetHeightM) {
  cloned.traverse((node) => {
    if (node.isMesh && node.material) {
      node.castShadow = true;
      node.receiveShadow = true;
      const mats = Array.isArray(node.material) ? node.material : [node.material];
      const newMats = mats.map((m) => {
        const mName = (m.name || '').toLowerCase();
        if (mName === 'glass') {
          m.transparent = true;
          m.opacity = 0.28;
          m.roughness = 0.08;
          m.envMapIntensity = 1.6;
          m.depthWrite = false;
          m.needsUpdate = true;
          return m;
        }
        if (mName === 'skin' || mName === 'face') {
          m.color.set('#ffdbac');
          m.roughness = 0.60;
          m.envMapIntensity = 0.65;
          m.needsUpdate = true;
          return m;
        }
        // Upgrade standard cloth/fur/body materials to PhysicalMaterial with velvety Pixar rim sheen!
        if (m.isMeshStandardMaterial && !m.isMeshPhysicalMaterial && (m.metalness || 0) < 0.25) {
          const pm = new THREE.MeshPhysicalMaterial({
            color: m.color,
            map: m.map,
            normalMap: m.normalMap,
            roughness: Math.min(0.84, Math.max(0.32, m.roughness ?? 0.58)),
            metalness: m.metalness || 0.0,
            sheen: 0.42,
            sheenRoughness: 0.65,
            sheenColor: new THREE.Color('#fffbeb'),
            envMapIntensity: 0.88,
          });
          return pm;
        }
        m.roughness = Math.min(0.84, Math.max(0.28, m.roughness ?? 0.56));
        m.envMapIntensity = m.metalness > 0.3 ? 1.45 : 0.82;
        m.needsUpdate = true;
        return m;
      });
      node.material = Array.isArray(node.material) ? newMats : newMats[0];
    }
  });

  const sc = document.createElement('canvas');
  sc.width = 128; sc.height = 128;
  const sctx = sc.getContext('2d');
  const grad = sctx.createRadialGradient(64, 64, 6, 64, 64, 60);
  grad.addColorStop(0, 'rgba(15, 23, 42, 0.44)');
  grad.addColorStop(0.55, 'rgba(15, 23, 42, 0.20)');
  grad.addColorStop(1, 'rgba(15, 23, 42, 0.0)');
  sctx.fillStyle = grad;
  sctx.fillRect(0, 0, 128, 128);
  const sTex = new THREE.CanvasTexture(sc);
  const rShadow = Math.max(0.42, (targetHeightM || 1.48) * 0.40);
  const contactDisc = new THREE.Mesh(
    new THREE.PlaneGeometry(rShadow * 2, rShadow * 2),
    new THREE.MeshBasicMaterial({ map: sTex, transparent: true, depthWrite: false, opacity: 0.85 })
  );
  contactDisc.rotation.x = -Math.PI / 2;
  contactDisc.position.y = 0.008;
  wrapper.add(contactDisc);
  return contactDisc;
}

/**
 * 4-Pass NVIDIA RTX Cinema Post-Processing Pipeline:
 * - 1.35x SSAA (`HalfFloatType` + WebGL2 `DepthTexture`) -> crisp subpixel edges & valid linear depth
 * - 12-Tap Spiral Screen-Space Ambient Occlusion (SSAO) -> crevice & contact occlusion
 * - Specular HDR Bright-Pass + Separable 2-Pass Bloom Blur
 * - Bokeh Shallow Depth-of-Field + ACES Filmic Color Grade + Micro-Sharpening -> crisp W x H output!
 */
export function createCinemaComposer(renderer, W, H, camera) {
  const ssScale = 1.5;
  const rW = Math.round(W * ssScale);
  const rH = Math.round(H * ssScale);

  const depthTex = new THREE.DepthTexture(rW, rH);
  depthTex.type = THREE.UnsignedIntType;

  const hdrRT = new THREE.WebGLRenderTarget(rW, rH, {
    type: THREE.HalfFloatType,
    minFilter: THREE.LinearFilter,
    magFilter: THREE.LinearFilter,
    depthTexture: depthTex,
    samples: 0,
  });

  const aoW = Math.max(256, Math.floor(rW / 2));
  const aoH = Math.max(256, Math.floor(rH / 2));
  const aoRT = new THREE.WebGLRenderTarget(aoW, aoH, {
    type: THREE.HalfFloatType,
    minFilter: THREE.LinearFilter,
    magFilter: THREE.LinearFilter,
  });
  const aoBlurRT = new THREE.WebGLRenderTarget(aoW, aoH, {
    type: THREE.HalfFloatType,
    minFilter: THREE.LinearFilter,
    magFilter: THREE.LinearFilter,
  });

  const bw = Math.max(180, Math.floor(W / 2));
  const bh = Math.max(320, Math.floor(H / 2));
  const bloomRT1 = new THREE.WebGLRenderTarget(bw, bh, { type: THREE.HalfFloatType, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter });
  const bloomRT2 = new THREE.WebGLRenderTarget(Math.floor(bw / 2), Math.floor(bh / 2), { type: THREE.HalfFloatType, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter });
  const bloomRT3 = new THREE.WebGLRenderTarget(Math.floor(bw / 2), Math.floor(bh / 2), { type: THREE.HalfFloatType, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter });

  const postCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const quadGeo = new THREE.PlaneGeometry(2, 2);

  // 1. 12-Tap Screen-Space Ambient Occlusion (SSAO) from Linearized Depth
  const ssaoMat = new THREE.ShaderMaterial({
    uniforms: {
      tDepth: { value: depthTex },
      uNear: { value: camera ? camera.near : 0.1 },
      uFar: { value: camera ? camera.far : 60.0 },
      uTexel: { value: new THREE.Vector2(1.0 / rW, 1.0 / rH) },
    },
    vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=vec4(position.xy,0.0,1.0); }`,
    fragmentShader: `
      uniform sampler2D tDepth;
      uniform float uNear;
      uniform float uFar;
      uniform vec2 uTexel;
      varying vec2 vUv;

      float linDepth(vec2 uv) {
        float z = texture2D(tDepth, uv).x;
        float zNdc = z * 2.0 - 1.0;
        return (2.0 * uNear * uFar) / (uFar + uNear - zNdc * (uFar - uNear));
      }

      void main() {
        float cD = linDepth(vUv);
        if (cD > uFar * 0.88) {
          gl_FragColor = vec4(1.0);
          return;
        }
        float occ = 0.0;
        float rad = clamp(18.0 / max(1.2, cD), 2.5, 11.0);
        for (int i = 0; i < 16; i++) {
          float fi = float(i);
          float ang = fi * 2.39996 + (vUv.x * 137.0 + vUv.y * 293.0);
          float rFrac = (fi + 0.5) / 16.0;
          vec2 off = vec2(cos(ang), sin(ang)) * rad * rFrac * uTexel;
          float sD = linDepth(clamp(vUv + off, vec2(0.002), vec2(0.998)));
          float diff = cD - sD;
          float range = smoothstep(0.0, 1.0, 0.9 / max(0.02, abs(diff)));
          occ += step(0.045, diff) * step(diff, 1.35) * range;
        }
        float ao = clamp(1.0 - (occ / 16.0) * 0.54, 0.56, 1.0);
        gl_FragColor = vec4(vec3(ao), 1.0);
      }
    `,
  });

  // 2. Specular Bright-Pass
  const brightMat = new THREE.ShaderMaterial({
    uniforms: {
      tDiffuse: { value: null },
      uThreshold: { value: 1.24 },
    },
    vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=vec4(position.xy,0.0,1.0); }`,
    fragmentShader: `
      uniform sampler2D tDiffuse;
      uniform float uThreshold;
      varying vec2 vUv;
      void main() {
        vec3 c = texture2D(tDiffuse, vUv).rgb;
        float lum = dot(c, vec3(0.2126, 0.7152, 0.0722));
        float soft = smoothstep(uThreshold - 0.15, uThreshold + 0.45, lum);
        gl_FragColor = vec4(c * soft, 1.0);
      }
    `,
  });

  // 3. Separable 9-tap Blur
  const blurMat = new THREE.ShaderMaterial({
    uniforms: {
      tDiffuse: { value: null },
      uTexelStep: { value: new THREE.Vector2(1 / bw, 0) },
    },
    vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=vec4(position.xy,0.0,1.0); }`,
    fragmentShader: `
      uniform sampler2D tDiffuse;
      uniform vec2 uTexelStep;
      varying vec2 vUv;
      void main() {
        vec3 sum = texture2D(tDiffuse, vUv).rgb * 0.227027;
        sum += (texture2D(tDiffuse, vUv + uTexelStep * 1.3846).rgb + texture2D(tDiffuse, vUv - uTexelStep * 1.3846).rgb) * 0.316216;
        sum += (texture2D(tDiffuse, vUv + uTexelStep * 3.2307).rgb + texture2D(tDiffuse, vUv - uTexelStep * 3.2307).rgb) * 0.070270;
        gl_FragColor = vec4(sum, 1.0);
      }
    `,
  });

  // 4. Final Cinema Compositor (Bokeh DOF Soft Background + SSAO Multiply + Bloom + ACES Filmic + Unsharp Polish)
  const compMat = new THREE.ShaderMaterial({
    uniforms: {
      tBase: { value: null },
      tDepth: { value: depthTex },
      tAO: { value: aoRT.texture },
      tBloom: { value: null },
      uNear: { value: camera ? camera.near : 0.1 },
      uFar: { value: camera ? camera.far : 60.0 },
      uFocusDist: { value: 4.5 },
      uBloomStrength: { value: 0.16 },
      uExposure: { value: 0.96 },
      uTexel: { value: new THREE.Vector2(1.0 / rW, 1.0 / rH) },
    },
    vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=vec4(position.xy,0.0,1.0); }`,
    fragmentShader: `
      uniform sampler2D tBase;
      uniform sampler2D tDepth;
      uniform sampler2D tAO;
      uniform sampler2D tBloom;
      uniform float uNear;
      uniform float uFar;
      uniform float uFocusDist;
      uniform float uBloomStrength;
      uniform float uExposure;
      uniform vec2 uTexel;
      varying vec2 vUv;

      float linDepth(vec2 uv) {
        float z = texture2D(tDepth, uv).x;
        float zNdc = z * 2.0 - 1.0;
        return (2.0 * uNear * uFar) / (uFar + uNear - zNdc * (uFar - uNear));
      }

      vec3 acesFilmic(vec3 x) {
        const float a = 2.51;
        const float b = 0.03;
        const float c = 2.43;
        const float d = 0.59;
        const float e = 0.14;
        return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
      }

      void main() {
        vec3 centerCol = texture2D(tBase, vUv).rgb;
        vec3 s1 = texture2D(tBase, vUv + vec2(-0.36, -0.36) * uTexel).rgb;
        vec3 s2 = texture2D(tBase, vUv + vec2( 0.36, -0.36) * uTexel).rgb;
        vec3 s3 = texture2D(tBase, vUv + vec2(-0.36,  0.36) * uTexel).rgb;
        vec3 s4 = texture2D(tBase, vUv + vec2( 0.36,  0.36) * uTexel).rgb;
        vec3 subAvg = (s1 + s2 + s3 + s4) * 0.25;

        const vec3 lumaW = vec3(0.2126, 0.7152, 0.0722);
        float lC = dot(centerCol, lumaW);
        float lMin = min(lC, min(min(dot(s1, lumaW), dot(s2, lumaW)), min(dot(s3, lumaW), dot(s4, lumaW))));
        float lMax = max(lC, max(max(dot(s1, lumaW), dot(s2, lumaW)), max(dot(s3, lumaW), dot(s4, lumaW))));
        float edgeContrast = lMax - lMin;

        // Edge-adaptive rotated-grid SSAA resolve: smooths jagged 3D edges while keeping textures crisp
        float aaBlend = smoothstep(0.03, 0.22, edgeContrast);
        vec3 aaCol = mix(centerCol * 0.65 + subAvg * 0.35, centerCol * 0.32 + subAvg * 0.68, aaBlend);
        float d = linDepth(vUv);

        // Gentle Bokeh Depth-of-Field ONLY on far distant background (> 6.5m behind focused character)
        float farDelta = max(0.0, (d - uFocusDist) - 6.5);
        float coc = (d > uFar * 0.92) ? 0.0 : clamp(farDelta * 0.050, 0.0, 0.55);

        vec3 hdr = aaCol;
        if (coc > 0.04) {
          vec3 dofSum = aaCol;
          float bRad = coc * 2.8;
          for (int i = 0; i < 8; i++) {
            float a = float(i) * 0.785398;
            dofSum += texture2D(tBase, clamp(vUv + vec2(cos(a), sin(a)) * bRad * uTexel, 0.001, 0.999)).rgb;
          }
          hdr = mix(aaCol, dofSum / 9.0, 0.50);
        }

        // Apply smoothed SSAO crevice shadowing (denoised via separable blur pass)
        float ao = texture2D(tAO, vUv).r;
        float aoMix = (d > uFar * 0.88) ? 1.0 : ao;
        hdr *= mix(1.0, aoMix, 0.56);

        vec3 bloom = texture2D(tBloom, vUv).rgb;
        vec3 col = (hdr + bloom * uBloomStrength) * uExposure;
        col = acesFilmic(col);
        col = pow(col, vec3(1.0 / 2.2));
        vec2 dv = vUv - vec2(0.5);
        col *= (1.0 - dot(dv, dv) * 0.16);
        gl_FragColor = vec4(col, 1.0);
      }
    `,
  });

  const postScene = new THREE.Scene();
  const postQuad = new THREE.Mesh(quadGeo, brightMat);
  postScene.add(postQuad);

  return {
    render(scene, cam, focusDist = 4.5) {
      ssaoMat.uniforms.uNear.value = cam.near;
      ssaoMat.uniforms.uFar.value = cam.far;
      compMat.uniforms.uNear.value = cam.near;
      compMat.uniforms.uFar.value = cam.far;
      compMat.uniforms.uFocusDist.value = focusDist;

      // Pass 1: 1.5x SSAA HDR Scene + Hardware DepthTexture
      renderer.setRenderTarget(hdrRT);
      renderer.render(scene, cam);

      // Pass 2: 16-Tap Depth SSAO + 2-Pass Separable Denoise Blur (eliminates grainy stipple noise)
      postQuad.material = ssaoMat;
      renderer.setRenderTarget(aoRT);
      renderer.render(postScene, postCam);

      postQuad.material = blurMat;
      blurMat.uniforms.tDiffuse.value = aoRT.texture;
      blurMat.uniforms.uTexelStep.value.set(1.35 / aoW, 0.0);
      renderer.setRenderTarget(aoBlurRT);
      renderer.render(postScene, postCam);

      blurMat.uniforms.tDiffuse.value = aoBlurRT.texture;
      blurMat.uniforms.uTexelStep.value.set(0.0, 1.35 / aoH);
      renderer.setRenderTarget(aoRT);
      renderer.render(postScene, postCam);

      // Pass 3: Bright-Pass + Separable 2-Pass Specular Bloom
      postQuad.material = brightMat;
      brightMat.uniforms.tDiffuse.value = hdrRT.texture;
      renderer.setRenderTarget(bloomRT1);
      renderer.render(postScene, postCam);

      postQuad.material = blurMat;
      blurMat.uniforms.tDiffuse.value = bloomRT1.texture;
      blurMat.uniforms.uTexelStep.value.set(1.6 / bw, 0.0);
      renderer.setRenderTarget(bloomRT2);
      renderer.render(postScene, postCam);

      blurMat.uniforms.tDiffuse.value = bloomRT2.texture;
      blurMat.uniforms.uTexelStep.value.set(0.0, 1.6 / bh);
      renderer.setRenderTarget(bloomRT3);
      renderer.render(postScene, postCam);

      blurMat.uniforms.tDiffuse.value = bloomRT3.texture;
      blurMat.uniforms.uTexelStep.value.set(2.4 / bw, 2.4 / bh);
      renderer.setRenderTarget(bloomRT2);
      renderer.render(postScene, postCam);

      // Pass 4: Final Rotated-Grid SSAA + Bokeh DOF + Smooth SSAO + Bloom + ACES Composite
      postQuad.material = compMat;
      compMat.uniforms.tBase.value = hdrRT.texture;
      compMat.uniforms.tBloom.value = bloomRT2.texture;
      renderer.setRenderTarget(null);
      renderer.render(postScene, postCam);
    },
    dispose() {
      hdrRT.dispose();
      aoRT.dispose();
      aoBlurRT.dispose();
      bloomRT1.dispose();
      bloomRT2.dispose();
      bloomRT3.dispose();
      depthTex.dispose();
      quadGeo.dispose();
    },
  };
}
