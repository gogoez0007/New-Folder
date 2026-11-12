/**
 * Dynamic 3D Facial Expression, Blink, Lip-Sync & Anatomically Safe Head/Spine Kinematics (`assets/three/face_rig.js`).
 */

import * as THREE from 'three';
import { GENERATED_EXPRESSION_PROFILES, applyGeneratedFaceExpression } from './generated/custom_expressions.js';
import { GENERATED_MOTION_PROFILES } from './generated/custom_motions.js';

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

export function findBestHeadAndSpineBones(cloned) {
  let headBone = null;
  let spineBone = null;
  let upperArmL = null;
  let upperArmR = null;
  const allBones = [];
  cloned.traverse((n) => {
    if (n.isBone) allBones.push(n);
  });

  for (const b of allBones) {
    if (/^(head|b_head_05|mixamorig:head)$/i.test(b.name || '')) {
      headBone = b;
      break;
    }
  }
  if (!headBone) {
    for (const b of allBones) {
      const nm = b.name || '';
      if (/head/i.test(nm) && !/headband|headtop|end$/i.test(nm)) {
        headBone = b;
        break;
      }
    }
  }

  for (const b of allBones) {
    if (/^(chest|torso|spine2|spine1|spine|b_spine_02|mixamorig:spine1)$/i.test(b.name || '')) {
      spineBone = b;
      break;
    }
  }
  if (!spineBone) {
    for (const b of allBones) {
      if (/spine|chest|torso/i.test(b.name || '')) {
        spineBone = b;
        break;
      }
    }
  }

  for (const b of allBones) {
    const nm = b.name || '';
    if (!upperArmL && (/^(upperarm\.l|upper_arm\.l|mixamorig:leftarm)$/i.test(nm) || (/upper.*arm|shoulder/i.test(nm) && /[\._]l$|left/i.test(nm)))) {
      upperArmL = b;
    }
    if (!upperArmR && (/^(upperarm\.r|upper_arm\.r|mixamorig:rightarm)$/i.test(nm) || (/upper.*arm|shoulder/i.test(nm) && /[\._]r$|right/i.test(nm)))) {
      upperArmR = b;
    }
  }

  return { headBone, spineBone, upperArmL, upperArmR };
}

function collectFaceAnchorVertices(cloned, faceAnchor, wrapper, minWorldY) {
  wrapper.updateMatrixWorld(true);
  const invAnchor = new THREE.Matrix4().copy(faceAnchor.matrixWorld).invert();
  const vWorld = new THREE.Vector3();
  const pts = [];

  cloned.traverse((n) => {
    if (!n.isMesh || !n.geometry || !n.geometry.attributes || !n.geometry.attributes.position) return;
    const pos = n.geometry.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      if (n.isSkinnedMesh && typeof n.getVertexPosition === 'function') {
        n.getVertexPosition(i, vWorld);
        vWorld.applyMatrix4(n.matrixWorld);
      } else {
        vWorld.fromBufferAttribute(pos, i).applyMatrix4(n.matrixWorld);
      }
      if (vWorld.y >= minWorldY) {
        const vLocal = vWorld.clone().applyMatrix4(invAnchor);
        pts.push(vLocal);
      }
    }
  });
  return pts;
}

function maxZNear(pts, tx, ty, xTol, yTol) {
  let best = -Infinity;
  for (const p of pts) {
    if (Math.abs(p.x - tx) <= xTol && Math.abs(p.y - ty) <= yTol) {
      if (p.z > best) best = p.z;
    }
  }
  return isFinite(best) ? best : null;
}

/**
 * Attach calibrated `faceAnchor` & expressive 3D face rig (never obscuring noses or floating above animal skulls).
 */
export function attachExpressiveFaceRig(cloned, wrapper, headBone, cSpec) {
  if (!headBone) return null;

  wrapper.updateMatrixWorld(true);
  const wQ = new THREE.Quaternion();
  const hQ = new THREE.Quaternion();
  const hS = new THREE.Vector3();
  wrapper.getWorldQuaternion(wQ);
  headBone.getWorldQuaternion(hQ);
  headBone.getWorldScale(hS);

  const faceAnchor = new THREE.Group();
  faceAnchor.name = '__faceAnchor';
  faceAnchor.quaternion.copy(hQ).invert().multiply(wQ);
  faceAnchor.scale.set(
    1.0 / Math.max(1e-4, Math.abs(hS.x)),
    1.0 / Math.max(1e-4, Math.abs(hS.y)),
    1.0 / Math.max(1e-4, Math.abs(hS.z))
  );
  headBone.add(faceAnchor);

  const anchorWorldPos = new THREE.Vector3();
  wrapper.updateMatrixWorld(true);
  faceAnchor.getWorldPosition(anchorWorldPos);
  const pts = collectFaceAnchorVertices(cloned, faceAnchor, wrapper, anchorWorldPos.y - 0.04);
  if (pts.length === 0) {
    headBone.remove(faceAnchor);
    return null;
  }

  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity, maxZ = -Infinity;
  for (const p of pts) {
    if (p.x < minX) minX = p.x;
    if (p.x > maxX) maxX = p.x;
    if (p.y < minY) minY = p.y;
    if (p.y > maxY) maxY = p.y;
    if (p.z > maxZ) maxZ = p.z;
  }

  const rigFam = cSpec.rig_family || '';
  const glbName = (cSpec.glb_model || '').toLowerCase();
  const isQuad = (
    rigFam === 'animal_quadruped' ||
    rigFam === 'dinosaur' ||
    rigFam === 'sky_bird' ||
    cSpec.role === 'pet_animal' ||
    cSpec.role === 'wild_creature' ||
    cSpec.role === 'sky_bird'
  );
  const isBlankFace = (rigFam === 'quaternius_human');
  const isBearded = /lorekeeper|hiker|farmer|engineer|dwarf/i.test(glbName);
  const isMonster = /monstercostume/i.test(glbName);

  const headH = Math.max(0.18, maxY - Math.max(-0.04, minY));
  const headW = Math.max(0.18, maxX - minX);

  let eyeY = isBlankFace ? (minY + headH * 0.52) : (headH * 0.36);
  if (isQuad) {
    eyeY = clamp(maxY - headH * 0.36, 0.02, maxY - 0.04);
  }
  const eyeSepX = isQuad ? clamp(headW * 0.24, 0.045, 0.095) : clamp(headW * 0.165, 0.068, 0.105);
  const eyeScale = isQuad ? 0.60 : 0.90;

  // Place mouth strictly below nose at KayKit chin-mouth ratio (`eyeY - headH * 0.24`)
  const mouthY = isBlankFace ? (minY + headH * 0.24) : Math.max(0.035, eyeY - headH * 0.24);
  const mouthScale = isMonster ? 0.62 : 1.0;

  let eyeZ = maxZNear(pts, eyeSepX * 0.65, eyeY, 0.075, 0.045);
  let mouthZ = maxZNear(pts, 0.0, mouthY, 0.045, 0.030);
  const fallbackZ = Math.min(maxZ * 0.78, 0.25);
  if (eyeZ === null) eyeZ = fallbackZ;
  if (mouthZ === null) mouthZ = eyeZ - 0.005;

  if (isMonster) {
    eyeZ = clamp(eyeZ, 0.16, 0.245);
    mouthZ = clamp(mouthZ, 0.16, 0.245);
  }

  const rig = {
    faceAnchor,
    isQuad,
    isBlankFace,
    isBearded,
    eyeY,
    mouthY,
    eyeSepX,
    eyeZ,
    mouthZ,
    browBaseY: eyeY + 0.055 * eyeScale,
    lidL: null,
    lidR: null,
    browL: null,
    browR: null,
    mouthGroup: null,
    mouthSmile: null,
    mouthOpenCavity: null,
    upperTeeth: null,
    lipRim: null,
    smoothOpen: 0.0,
    smoothWidth: 1.0,
    blushL: null,
    blushR: null,
    tearGroup: null,
  };

  // For quadruped animals (`ShibaInu`, `Fox`, `Cow`, `Alpaca`), keep crisp natural faces cleanly;
  // ONLY mount face-tracked 3D crying teardrops & expressive cheek reactions (ZERO floating brow bars over skulls!).
  if (isQuad) {
    const tearGroup = new THREE.Group();
    const tearMat = new THREE.MeshPhysicalMaterial({ color: '#38bdf8', roughness: 0.1, transparent: true, opacity: 0.90 });
    const zTear = Math.min(maxZ, eyeZ + 0.015);
    const tL = new THREE.Mesh(new THREE.SphereGeometry(0.014, 10, 10), tearMat);
    tL.scale.set(0.8, 1.35, 0.8);
    tL.position.set(-eyeSepX * 0.85, eyeY - 0.025, zTear);
    const tR = tL.clone();
    tR.position.x = eyeSepX * 0.85;
    tearGroup.add(tL, tR);
    tearGroup.visible = false;
    faceAnchor.add(tearGroup);
    rig.tearGroup = tearGroup;
    return rig;
  }

  // 1. Blank-face GLBs (if Quaternius fallback ever runs): sculpted white cornea + iris + pupil + glint!
  if (isBlankFace) {
    const scleraMat = new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.15 });
    const irisMat = new THREE.MeshStandardMaterial({ color: '#1e293b', roughness: 0.1 });
    const glintMat = new THREE.MeshBasicMaterial({ color: '#ffffff' });

    for (const sx of [-1, 1]) {
      const eg = new THREE.Group();
      eg.position.set(sx * eyeSepX, eyeY, eyeZ + 0.005);
      const sclera = new THREE.Mesh(new THREE.SphereGeometry(0.032 * eyeScale, 14, 12), scleraMat);
      sclera.scale.set(0.88, 1.15, 0.55);
      const pupil = new THREE.Mesh(new THREE.SphereGeometry(0.020 * eyeScale, 12, 10), irisMat);
      pupil.scale.set(0.92, 1.10, 0.55);
      pupil.position.z = 0.011;
      const glint = new THREE.Mesh(new THREE.SphereGeometry(0.006 * eyeScale, 8, 8), glintMat);
      glint.position.set(-0.008 * eyeScale, 0.010 * eyeScale, 0.019);
      eg.add(sclera, pupil, glint);
      faceAnchor.add(eg);
    }
  }

  // 2. Natural Blinking & Expressive Upper Eyelids (used on blinks, angry scowls, crying squints!)
  const lidMat = new THREE.MeshStandardMaterial({ color: '#eab68d', roughness: 0.65 });
  const lidGeo = new THREE.BoxGeometry(0.052 * eyeScale, 0.028 * eyeScale, 0.016);
  const lidL = new THREE.Mesh(lidGeo, lidMat);
  lidL.position.set(-eyeSepX, eyeY + 0.010, eyeZ + 0.012);
  lidL.visible = false;
  const lidR = new THREE.Mesh(lidGeo, lidMat);
  lidR.position.set(eyeSepX, eyeY + 0.010, eyeZ + 0.012);
  lidR.visible = false;
  faceAnchor.add(lidL, lidR);
  rig.lidL = lidL;
  rig.lidR = lidR;

  // 3. Articulated Eyebrows ONLY when model lacks baked colorful brows (blank faces), OR subtle outer expressive lids
  if (isBlankFace) {
    const browMat = new THREE.MeshStandardMaterial({ color: '#2c1810', roughness: 0.45 });
    const browGeo = new THREE.CapsuleGeometry(0.011 * eyeScale, 0.044 * eyeScale, 6, 8);
    const browL = new THREE.Mesh(browGeo, browMat);
    browL.rotation.z = Math.PI / 2;
    browL.position.set(-eyeSepX, rig.browBaseY, eyeZ + 0.016);
    const browR = new THREE.Mesh(browGeo, browMat);
    browR.rotation.z = Math.PI / 2;
    browR.position.set(eyeSepX, rig.browBaseY, eyeZ + 0.016);
    faceAnchor.add(browL, browR);
    rig.browL = browL;
    rig.browR = browR;
  }

  // 4. Anatomical Reactive 3D Mouth ONLY for blank-face GLBs (never overlay holes onto characters with painted mouths!)
  if (isBlankFace) {
    const mg = new THREE.Group();
    mg.position.set(0, mouthY, mouthZ + 0.008);
    mg.scale.setScalar(mouthScale);

    const cavityMat = new THREE.MeshBasicMaterial({ color: '#58101c' });
    const cavity = new THREE.Mesh(new THREE.SphereGeometry(0.025 * eyeScale, 16, 12), cavityMat);
    cavity.scale.set(1.05, 0.12, 0.30);
    cavity.visible = false;

    const teethMat = new THREE.MeshStandardMaterial({ color: '#fffbeb', roughness: 0.25 });
    const upperTeeth = new THREE.Mesh(new THREE.BoxGeometry(0.032 * eyeScale, 0.010 * eyeScale, 0.008), teethMat);
    upperTeeth.position.set(0, 0.013 * eyeScale, 0.008);
    upperTeeth.visible = false;

    const tongueMat = new THREE.MeshStandardMaterial({ color: '#fb7185', roughness: 0.4 });
    const tongue = new THREE.Mesh(new THREE.SphereGeometry(0.014 * eyeScale, 10, 8), tongueMat);
    tongue.scale.set(1.02, 0.50, 0.42);
    tongue.position.set(0, -0.009 * eyeScale, 0.007);
    cavity.add(tongue);

    const lipMat = new THREE.MeshStandardMaterial({ color: '#e29587', roughness: 0.52 });
    const lipRim = new THREE.Mesh(new THREE.TorusGeometry(0.024 * eyeScale, 0.0042 * eyeScale, 8, 18), lipMat);
    lipRim.scale.set(1.05, 0.18, 0.42);
    lipRim.position.z = 0.004;
    lipRim.visible = false;

    const smileMat = new THREE.MeshStandardMaterial({ color: '#7c2d12', roughness: 0.5 });
    const smile = new THREE.Mesh(new THREE.TorusGeometry(0.021 * eyeScale, 0.0042 * eyeScale, 8, 16, Math.PI), smileMat);
    smile.rotation.z = Math.PI;

    mg.add(cavity, upperTeeth, lipRim, smile);
    faceAnchor.add(mg);
    rig.mouthGroup = mg;
    rig.mouthOpenCavity = cavity;
    rig.upperTeeth = upperTeeth;
    rig.lipRim = lipRim;
    rig.mouthSmile = smile;
  }

  // 5. Soft Rosy Cheek Blush
  const blushMat = new THREE.MeshBasicMaterial({ color: '#fb7185', transparent: true, opacity: 0.42 });
  const blushGeo = new THREE.SphereGeometry(0.022 * eyeScale, 10, 8);
  const blushL = new THREE.Mesh(blushGeo, blushMat);
  blushL.scale.set(1.2, 0.72, 0.25);
  blushL.position.set(-eyeSepX * 1.15, eyeY - 0.048 * eyeScale, eyeZ + 0.006);
  blushL.visible = false;
  const blushR = blushL.clone();
  blushR.position.x = eyeSepX * 1.15;
  blushR.visible = false;
  faceAnchor.add(blushL, blushR);
  rig.blushL = blushL;
  rig.blushR = blushR;

  // 6. Crying 3D Teardrops anchored cleanly under eyes
  const tearGroup = new THREE.Group();
  const tearMat = new THREE.MeshPhysicalMaterial({ color: '#38bdf8', roughness: 0.1, transparent: true, opacity: 0.88 });
  const tL = new THREE.Mesh(new THREE.SphereGeometry(0.018 * eyeScale, 10, 10), tearMat);
  tL.scale.set(0.8, 1.35, 0.8);
  tL.position.set(-eyeSepX, eyeY - 0.032, eyeZ + 0.016);
  const tR = tL.clone();
  tR.position.x = eyeSepX;
  tearGroup.add(tL, tR);
  tearGroup.visible = false;
  faceAnchor.add(tearGroup);
  rig.tearGroup = tearGroup;

  return rig;
}

export function updateExpressiveFaceRig(rig, expression, isSpeaking, mouthVal, tSec, aIdx, customExprProfiles = null) {
  if (!rig) return;

  const expr = String(expression || 'happy').trim().toLowerCase().replace(/[\s-]+/g, '_');
  const blinkPhase = (tSec + aIdx * 0.91) % 3.1;
  const isBlinking = (blinkPhase > 2.94);

  const customCand = (customExprProfiles && customExprProfiles[expr]) || GENERATED_EXPRESSION_PROFILES[expr] || null;
  const customProf = (customCand && ('brow_lift' in customCand || 'expression_id' in customCand)) ? customCand : null;
  if (customProf) {
    applyGeneratedFaceExpression(rig, customProf, tSec, mouthVal, isSpeaking);
    if (isBlinking && rig.lidL && rig.lidR) {
      rig.lidL.visible = true;
      rig.lidR.visible = true;
      rig.lidL.position.y = rig.eyeY;
      rig.lidR.position.y = rig.eyeY;
      rig.lidL.scale.y = 1.25;
      rig.lidR.scale.y = 1.25;
      rig.lidL.rotation.z = 0;
      rig.lidR.rotation.z = 0;
    }
    return;
  }

  if (rig.lidL && rig.lidR) {
    if (isBlinking) {
      rig.lidL.visible = true;
      rig.lidR.visible = true;
      rig.lidL.position.y = rig.eyeY;
      rig.lidR.position.y = rig.eyeY;
      rig.lidL.scale.y = 1.25;
      rig.lidR.scale.y = 1.25;
      rig.lidL.rotation.z = 0;
      rig.lidR.rotation.z = 0;
    } else if (expr === 'angry' || expr === 'determined') {
      rig.lidL.visible = true;
      rig.lidR.visible = true;
      rig.lidL.position.y = rig.eyeY + 0.014;
      rig.lidR.position.y = rig.eyeY + 0.014;
      rig.lidL.scale.y = 0.65;
      rig.lidR.scale.y = 0.65;
      rig.lidL.rotation.z = -0.35;
      rig.lidR.rotation.z = 0.35;
    } else if (expr === 'crying' || expr === 'sad') {
      rig.lidL.visible = true;
      rig.lidR.visible = true;
      rig.lidL.position.y = rig.eyeY + 0.010;
      rig.lidR.position.y = rig.eyeY + 0.010;
      rig.lidL.scale.y = 0.72;
      rig.lidR.scale.y = 0.72;
      rig.lidL.rotation.z = 0.28;
      rig.lidR.rotation.z = -0.28;
    } else {
      rig.lidL.visible = false;
      rig.lidR.visible = false;
    }
  }

  if (rig.browL && rig.browR) {
    let liftL = 0, liftR = 0, tiltL = 0, tiltR = 0;
    if (expr === 'shocked' || expr === 'surprised') {
      liftL = liftR = 0.026;
      tiltL = 0.20; tiltR = -0.20;
    } else if (expr === 'angry' || expr === 'determined') {
      liftL = liftR = -0.008;
      tiltL = -0.42; tiltR = 0.42;
    } else if (expr === 'sad' || expr === 'crying' || expr === 'embarrassed') {
      liftL = liftR = 0.008;
      tiltL = 0.34; tiltR = -0.34;
    } else if (expr === 'curious') {
      liftL = 0.020; liftR = -0.005;
      tiltL = 0.16; tiltR = 0.0;
    } else {
      const bounce = Math.max(0, Math.sin(tSec * 6.0 + aIdx) * 0.008);
      liftL = liftR = 0.010 + bounce;
      tiltL = 0.12; tiltR = -0.12;
    }
    rig.browL.position.y = rig.browBaseY + liftL;
    rig.browR.position.y = rig.browBaseY + liftR;
    rig.browL.rotation.z = Math.PI / 2 + tiltL;
    rig.browR.rotation.z = Math.PI / 2 + tiltR;
  }

  if (rig.isBlankFace && rig.mouthGroup && rig.mouthOpenCavity && rig.mouthSmile) {
    const isLaughing = (expr === 'laughing' || expr === 'excited');
    const isShocked = (expr === 'shocked' || expr === 'surprised');
    const isSad = (expr === 'sad' || expr === 'crying');
    const isAngry = (expr === 'angry' || expr === 'determined');

    let targetOpen = 0.0;
    if (isShocked) {
      targetOpen = 0.46 + Math.sin(tSec * 5.5) * 0.07;
    } else if (isLaughing) {
      targetOpen = 0.52 + Math.abs(Math.sin(tSec * 10.5 + aIdx)) * 0.24;
    } else if (isSpeaking && mouthVal > 0.06) {
      const gated = clamp((mouthVal - 0.06) * 1.12, 0.0, 1.0);
      targetOpen = Math.pow(gated, 0.78) * 0.74;
    }

    const alphaOpen = targetOpen > (rig.smoothOpen || 0.0) ? 0.36 : 0.24;
    rig.smoothOpen = (rig.smoothOpen || 0.0) + (targetOpen - (rig.smoothOpen || 0.0)) * alphaOpen;

    const syllableMod = Math.sin(tSec * 10.2 + aIdx * 1.7) * 0.15 + 0.08;
    const targetWidth = isShocked ? 0.76 : (isLaughing ? 1.12 : clamp(0.88 + syllableMod * clamp(mouthVal, 0.2, 1.0), 0.78, 1.16));
    rig.smoothWidth = (rig.smoothWidth || 1.0) + (targetWidth - (rig.smoothWidth || 1.0)) * 0.30;

    if (rig.smoothOpen > 0.075) {
      rig.mouthSmile.visible = false;
      rig.mouthOpenCavity.visible = true;
      const openH = clamp(0.08 + rig.smoothOpen * 0.72, 0.08, 0.76);
      rig.mouthOpenCavity.scale.set(rig.smoothWidth, openH, 0.34);
      if (rig.lipRim) {
        rig.lipRim.visible = true;
        rig.lipRim.scale.set(rig.smoothWidth * 1.02, clamp(0.18 + openH * 0.92, 0.18, 0.80), 0.42);
      }
      if (rig.upperTeeth) {
        rig.upperTeeth.visible = (openH > 0.22);
        rig.upperTeeth.position.y = 0.008 + openH * 0.007;
      }
    } else {
      rig.mouthOpenCavity.visible = false;
      if (rig.lipRim) rig.lipRim.visible = false;
      if (rig.upperTeeth) rig.upperTeeth.visible = false;
      if (isSad || isAngry) {
        rig.mouthSmile.visible = true;
        rig.mouthSmile.rotation.z = 0;
        rig.mouthSmile.position.y = -0.008;
      } else {
        rig.mouthSmile.visible = rig.isBlankFace || expr === 'happy' || expr === 'proud';
        rig.mouthSmile.rotation.z = Math.PI;
        rig.mouthSmile.position.y = 0.005;
      }
    }
  }

  if (rig.blushL && rig.blushR) {
    const showBlush = (expr === 'happy' || expr === 'laughing' || expr === 'embarrassed' || expr === 'excited');
    rig.blushL.visible = showBlush;
    rig.blushR.visible = showBlush;
  }

  if (rig.tearGroup) {
    const isCrying = (expr === 'crying');
    rig.tearGroup.visible = isCrying;
    if (isCrying) {
      const dropOff = (tSec * 1.4) % 0.08;
      rig.tearGroup.position.y = -dropOff;
    }
  }
}

export function applySafeHeadAndSpinePose(entry, activePhase, tSec, aIdx, isSpeaking, mouthVal, fps = 60, uPhase = 0.5, customMotionProfiles = null) {
  if (!entry.wrapper) return;

  const act = String(activePhase.action || '').trim().toLowerCase().replace(/[\s-]+/g, '_');
  const mProf = (customMotionProfiles && customMotionProfiles[act]) || GENERATED_MOTION_PROFILES[act] || null;

  // Eye/head leads first, torso follows behind with natural biomechanical lag
  const headLeadSpeed = mProf?.head_lead_speed ?? 7.5;
  const torsoFollowSpeed = mProf?.torso_follow_speed ?? 4.8;
  const dtHeadLerp = 1.0 - Math.exp(-headLeadSpeed / Math.max(24, fps));
  const dtSpineLerp = 1.0 - Math.exp(-torsoFollowSpeed / Math.max(24, fps));

  if (entry.spineBone && entry.spineRestQuat && !entry.isQuadOrBird) {
    const breathAmp = mProf?.breath_amp ?? 0.020;
    const swayAmp = mProf?.sway_amp ?? 0.012;
    const breathTilt = Math.sin(tSec * 2.0 + aIdx * 1.1) * breathAmp;
    const breathSwayZ = Math.cos(tSec * 1.25 + aIdx * 0.7) * swayAmp;
    const pTilt = activePhase.spine_tilt_x || 0.0;
    const mTilt = mProf?.spine_tilt_x || 0.0;
    const baseTilt = Math.abs(pTilt) > Math.abs(mTilt) ? pTilt : mTilt;
    const rawTilt = clamp(baseTilt, -0.18, 0.38);
    entry.smoothSpineTilt = (entry.smoothSpineTilt || 0.0) + (rawTilt - (entry.smoothSpineTilt || 0.0)) * dtSpineLerp;
    const finalPitch = clamp(entry.smoothSpineTilt + breathTilt, -0.20, 0.40);

    if (Math.abs(finalPitch) > 0.002 || Math.abs(breathSwayZ) > 0.002) {
      entry.wrapper.updateMatrixWorld(true);
      const qWrap = new THREE.Quaternion();
      entry.wrapper.getWorldQuaternion(qWrap);
      const qPar = new THREE.Quaternion();
      if (entry.spineBone.parent) entry.spineBone.parent.getWorldQuaternion(qPar);

      const qDeltaW = new THREE.Quaternion().setFromEuler(new THREE.Euler(finalPitch, 0, breathSwayZ));
      const qWorldRot = qWrap.clone().multiply(qDeltaW).multiply(qWrap.clone().invert());
      const qLocalRot = qPar.clone().invert().multiply(qWorldRot).multiply(qPar);
      const targetS = qLocalRot.multiply(entry.spineBone.quaternion);
      const aDiff = targetS.angleTo(entry.spineRestQuat);
      if (aDiff > 0.44) {
        targetS.copy(entry.spineRestQuat).slerp(targetS, 0.44 / aDiff);
      }
      entry.spineBone.quaternion.copy(targetS);
    }
  }

  // Subtle organic secondary upper-arm / shoulder life when stationary
  const animMode = activePhase.anim_mode || 'idle';
  if (!entry.isQuadOrBird && (animMode === 'idle' || animMode === 'wave' || animMode === 'interact' || animMode === 'cheer')) {
    const posture = mProf?.arm_posture || 'neutral';
    let pitchL = Math.sin(tSec * 1.45 + aIdx * 1.3) * 0.025;
    let pitchR = Math.sin(tSec * 1.45 + aIdx * 1.3 + 0.4) * 0.025;
    let flareZ = 0.0;
    if (posture === 'alert_raised') {
      pitchL -= 0.10;
      pitchR -= 0.08;
      flareZ = 0.06;
    } else if (posture === 'reach_forward') {
      pitchL -= 0.12;
      pitchR -= 0.14;
    } else if (posture === 'recoil_guard') {
      pitchL -= 0.09;
      pitchR -= 0.09;
      flareZ = 0.08;
    }
    const qOffL = new THREE.Quaternion().setFromEuler(new THREE.Euler(pitchL, 0, flareZ));
    const qOffR = new THREE.Quaternion().setFromEuler(new THREE.Euler(pitchR, 0, -flareZ));
    if (entry.upperArmL && entry.upperArmLRestQuat) {
      const candL = entry.upperArmL.quaternion.clone().multiply(qOffL);
      if (candL.angleTo(entry.upperArmLRestQuat) <= 0.42) entry.upperArmL.quaternion.copy(candL);
    }
    if (entry.upperArmR && entry.upperArmRRestQuat) {
      const candR = entry.upperArmR.quaternion.clone().multiply(qOffR);
      if (candR.angleTo(entry.upperArmRRestQuat) <= 0.42) entry.upperArmR.quaternion.copy(candR);
    }
  }

  if (entry.headBone && entry.headRestQuat) {
    // Softly tether clip-driven head rotation toward bind rest so neck never over-rotates before expression offset
    const clipAngle = entry.headBone.quaternion.angleTo(entry.headRestQuat);
    if (clipAngle > 0.28) {
      entry.headBone.quaternion.copy(entry.headRestQuat).slerp(entry.headBone.quaternion, 0.28 / clipAngle);
    }

    const dampQuad = entry.isQuadOrBird ? 0.50 : 1.0;

    // Purposeful eased bell-curve gesture (ONLY shakes head or nods during explicit beat window, then settles calmly!)
    let gestureYaw = Math.sin(tSec * 1.05 + aIdx * 1.9) * 0.020;
    let gesturePitch = Math.sin(tSec * 1.55 + aIdx * 0.7) * 0.014;
    const gType = mProf?.gesture_type || 'none';
    const gAmp = mProf?.gesture_amp ?? 0.0;
    const gCycles = Math.max(1.0, mProf?.gesture_cycles ?? 2.0);

    if (gType === 'shake_no' || act === 'shake_head_no' || (activePhase.head_yaw_osc || 0.0) >= 0.20) {
      if (uPhase >= 0.14 && uPhase <= 0.76) {
        const uG = (uPhase - 0.14) / 0.62;
        const env = Math.sin(uG * Math.PI);
        const amp = Math.min(0.22, gAmp || activePhase.head_yaw_osc || 0.20);
        gestureYaw = env * Math.sin(uG * Math.PI * gCycles * 1.5) * amp;
      } else {
        gestureYaw = 0.0;
      }
    } else if (gType === 'curious_glance' || (activePhase.head_yaw_osc && activePhase.head_yaw_osc > 0.01)) {
      const env = Math.sin(clamp(uPhase, 0, 1) * Math.PI);
      const amp = Math.min(0.10, gAmp || activePhase.head_yaw_osc || 0.07);
      gestureYaw = env * Math.sin(clamp(uPhase, 0, 1) * Math.PI * 2.0) * amp;
    }

    if (gType === 'nod_yes' || act === 'listen_nod' || act === 'give_or_share' || (activePhase.head_nod_osc || 0.0) >= 0.08) {
      if (uPhase >= 0.10 && uPhase <= 0.74) {
        const uN = (uPhase - 0.10) / 0.64;
        const envN = Math.sin(uN * Math.PI);
        const ampN = Math.min(0.11, gAmp || activePhase.head_nod_osc || 0.09);
        gesturePitch += envN * Math.sin(uN * Math.PI * gCycles * 1.5) * ampN;
      }
    } else if (gType === 'laugh_bounce') {
      const envL = Math.sin(clamp(uPhase, 0, 1) * Math.PI);
      gesturePitch += envL * Math.abs(Math.sin(tSec * 6.5 + aIdx)) * Math.min(0.08, gAmp || 0.06);
    } else if (gType === 'recoil_snap') {
      if (uPhase < 0.25) {
        const uR = uPhase / 0.25;
        gesturePitch -= Math.sin(uR * Math.PI) * Math.min(0.12, gAmp || 0.09);
      }
    }

    // Subtle organic vocal chin inflection when speaking (never metronome bobblehead oscillation!)
    if (isSpeaking) {
      gesturePitch += clamp((mouthVal - 0.32) * 0.055, -0.015, 0.045);
    }

    const baseHeadPitch = mProf?.head_pitch ?? (activePhase.head_pitch || 0.0);
    const rawPitch = clamp((baseHeadPitch + gesturePitch) * dampQuad, -0.15, 0.15);
    const rawYaw = clamp(gestureYaw * dampQuad, -0.23, 0.23);
    const curTilt = (activePhase.expression === 'curious') ? 0.065 : (mProf?.head_roll_bias ?? 0.0);
    const rawRoll = clamp(curTilt * dampQuad, -0.08, 0.08);

    // Smooth across phase transitions with head-leading rate -> ZERO 1-frame snap!
    entry.smoothHeadPitch = (entry.smoothHeadPitch || 0.0) + (rawPitch - (entry.smoothHeadPitch || 0.0)) * dtHeadLerp;
    entry.smoothHeadYaw = (entry.smoothHeadYaw || 0.0) + (rawYaw - (entry.smoothHeadYaw || 0.0)) * dtHeadLerp;
    entry.smoothHeadRoll = (entry.smoothHeadRoll || 0.0) + (rawRoll - (entry.smoothHeadRoll || 0.0)) * dtHeadLerp;

    entry.wrapper.updateMatrixWorld(true);
    const qWrap = new THREE.Quaternion();
    entry.wrapper.getWorldQuaternion(qWrap);
    const qPar = new THREE.Quaternion();
    if (entry.headBone.parent) entry.headBone.parent.getWorldQuaternion(qPar);

    const qWrapDelta = new THREE.Quaternion().setFromEuler(
      new THREE.Euler(entry.smoothHeadPitch, entry.smoothHeadYaw, entry.smoothHeadRoll, 'YXZ')
    );
    const qWorldDelta = qWrap.clone().multiply(qWrapDelta).multiply(qWrap.clone().invert());
    const qLocalDelta = qPar.clone().invert().multiply(qWorldDelta).multiply(qPar);

    const targetQ = qLocalDelta.multiply(entry.headBone.quaternion);
    const totalAngle = targetQ.angleTo(entry.headRestQuat);
    const maxHeadAngle = entry.isQuadOrBird ? 0.24 : 0.32;
    if (totalAngle > maxHeadAngle) {
      targetQ.copy(entry.headRestQuat).slerp(targetQ, maxHeadAngle / totalAngle);
    }
    entry.headBone.quaternion.copy(targetQ);
  }
}
