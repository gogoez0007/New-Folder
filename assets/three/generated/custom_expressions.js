/**
 * Auto-generated FACS Expression Profiles maintained dynamically by `core/expression_knowledge_core.py`.
 */
export const GENERATED_EXPRESSION_PROFILES = {
  "disgusted": {
    "expression_id": "disgusted",
    "display_name": "Disgusted",
    "brow_lift": -0.01,
    "brow_asymmetry": 1.0,
    "brow_tilt_l": -0.32,
    "brow_tilt_r": 0.22,
    "eyelid_close_l": 0.55,
    "eyelid_close_r": 0.35,
    "mouth_open": 0.0,
    "mouth_width": 1.0,
    "mouth_curve": -0.75,
    "smirk_skew": -0.5,
    "chew_hz": 0.0,
    "blush": false,
    "tears": false,
    "eye_scale_y": 1.0,
    "notes": "Cringe squint with asymmetric frown."
  },
  "panicked": {
    "expression_id": "panicked",
    "display_name": "Panicked Reaction",
    "brow_lift": 0.024,
    "brow_asymmetry": 1.0,
    "brow_tilt_l": 0.25,
    "brow_tilt_r": 0.25,
    "eyelid_close_l": 0.0,
    "eyelid_close_r": 0.0,
    "mouth_open": 0.75,
    "mouth_width": 1.1,
    "mouth_curve": -0.5,
    "smirk_skew": 0.0,
    "chew_hz": 0.0,
    "blush": false,
    "tears": false,
    "eye_scale_y": 1.25,
    "notes": "Startled and panicked expression observing an unexpected cactus on the table with wide eyes and open mouth."
  },
  "scared": {
    "expression_id": "scared",
    "display_name": "Startled Fear",
    "brow_lift": 0.024,
    "brow_asymmetry": 1.0,
    "brow_tilt_l": 0.28,
    "brow_tilt_r": 0.28,
    "eyelid_close_l": 0.05,
    "eyelid_close_r": 0.05,
    "mouth_open": 0.85,
    "mouth_width": 1.15,
    "mouth_curve": -0.4,
    "smirk_skew": 0.0,
    "chew_hz": 3.0,
    "blush": false,
    "tears": true,
    "eye_scale_y": 1.3,
    "notes": "Expression reflects intense sudden fear and alertness as Toby leaps onto ice"
  },
  "smirking": {
    "expression_id": "smirking",
    "display_name": "Sly Mischievous Smirk",
    "brow_lift": -0.005,
    "brow_asymmetry": -0.3,
    "brow_tilt_l": -0.15,
    "brow_tilt_r": 0.05,
    "eyelid_close_l": 0.2,
    "eyelid_close_r": 0.05,
    "mouth_open": 0.01,
    "mouth_width": 1.05,
    "mouth_curve": 0.4,
    "smirk_skew": 0.7,
    "chew_hz": 0.0,
    "blush": false,
    "tears": false,
    "eye_scale_y": 1.0,
    "notes": "Character displays a sly and mischievous smirk, with one side of the mouth slightly raised and a subtle narrowing of the eyes, particularly on the opposite side of the mouth's raise."
  }
};

export function applyGeneratedFaceExpression(rig, profile, tSec, mouthVal, isSpeaking) {
  if (!rig || !profile) return false;
  const browLift = profile.brow_lift ?? 0.01;
  const browTiltL = profile.brow_tilt_l ?? 0.08;
  const browTiltR = profile.brow_tilt_r ?? -0.08;
  if (rig.browL && rig.browR) {
    rig.browL.position.y = rig.browBaseY + browLift;
    rig.browR.position.y = rig.browBaseY + browLift * (profile.brow_asymmetry ?? 1.0);
    rig.browL.rotation.z = Math.PI / 2 + browTiltL;
    rig.browR.rotation.z = Math.PI / 2 + browTiltR;
  }
  const lidCloseL = profile.eyelid_close_l ?? 0.0;
  const lidCloseR = profile.eyelid_close_r ?? 0.0;
  if (rig.lidL && rig.lidR) {
    rig.lidL.visible = lidCloseL > 0.05;
    rig.lidR.visible = lidCloseR > 0.05;
    if (rig.lidL.visible) rig.lidL.scale.y = 0.6 + lidCloseL * 1.4;
    if (rig.lidR.visible) rig.lidR.scale.y = 0.6 + lidCloseR * 1.4;
  }
  const mouthTarget = Math.max((profile.mouth_open ?? 0.0) * 0.65, isSpeaking ? Math.pow(Math.max(0, (mouthVal - 0.06) * 1.12), 0.78) * 0.78 : 0.0);
  rig.smoothOpen = (rig.smoothOpen ?? 0.0) + (mouthTarget - (rig.smoothOpen ?? 0.0)) * (mouthTarget > (rig.smoothOpen ?? 0.0) ? 0.36 : 0.24);
  const chewOsc = profile.chew_hz ? (0.75 + Math.abs(Math.sin(tSec * profile.chew_hz * 3.14159)) * 0.45) : 1.0;
  const openAmt = Math.min(0.88, rig.smoothOpen * chewOsc);
  if (rig.isBlankFace && rig.mouthOpenCavity && rig.mouthSmile) {
    if (openAmt > 0.07) {
      rig.mouthSmile.visible = false;
      rig.mouthOpenCavity.visible = true;
      const wBase = profile.mouth_width ?? 1.0;
      const vowelMod = 0.88 + Math.sin(tSec * 9.5 + (profile.brow_lift ?? 0) * 50) * 0.16;
      rig.mouthOpenCavity.scale.set(wBase * vowelMod, Math.max(0.08, openAmt * 0.76), 0.34);
      if (rig.lipRim) {
        rig.lipRim.visible = true;
        rig.lipRim.scale.set(wBase * vowelMod, Math.max(0.18, openAmt * 0.78), 0.42);
      }
      if (rig.upperTeeth) rig.upperTeeth.visible = openAmt > 0.18;
    } else {
      rig.mouthOpenCavity.visible = false;
      if (rig.lipRim) rig.lipRim.visible = false;
      if (rig.upperTeeth) rig.upperTeeth.visible = false;
      rig.mouthSmile.visible = rig.isBlankFace || Math.abs(profile.mouth_curve ?? 0) > 0.28;
      rig.mouthSmile.rotation.z = (profile.mouth_curve ?? 0.3) >= 0 ? Math.PI : 0.0;
      rig.mouthSmile.position.x = (profile.smirk_skew ?? 0.0) * 0.015;
    }
  }
  if (rig.blushL && rig.blushR) {
    const showB = Boolean(profile.blush);
    rig.blushL.visible = showB;
    rig.blushR.visible = showB;
  }
  if (rig.tearGroup) {
    rig.tearGroup.visible = Boolean(profile.tears);
    if (rig.tearGroup.visible) {
      rig.tearGroup.position.y = -((tSec * 1.4) % 0.08);
    }
  }
  return true;
}
