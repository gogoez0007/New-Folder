"""
Core 7: Autonomous Facial Expression Learning Core (`core/expression_knowledge_core.py`).

Learns FACS (Facial Action Coding System) parameters for any unseen facial expression
spotted in a trending reference video (for example: `smirking`, `winking`, `chewing`,
`sleepy_yawn`, `panicked`, `disgusted`, `confused_squint`, `evil_grin`) and generates:
  1. Persistent Python expression core scripts (`core/generated_expressions/<expr>_expr.py`), AND
  2. Runtime Three.js FACS expression map (`assets/three/generated/custom_expressions.js`)
executed directly inside `assets/three/face_rig.js`.
"""

import json
import pprint
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from google import genai
from google.genai import types

import config
from core.scene_core import EXPRESSION_KNOWLEDGE_BASE
from core.generated_expressions import load_all_generated_expressions
from utils.logger import log_info, log_success, log_warning


class FacialAUBlueprint(BaseModel):
    """Structured Facial Action Coding System profile for any learned facial expression."""
    expression_id: str
    display_name: str
    brow_lift: float = Field(default=0.01, description="Vertical brow offset in meters (-0.015 furrowed to +0.028 raised)")
    brow_asymmetry: float = Field(default=1.0, description="Asymmetry multiplier between left/right brows (1.0 symmetric, -0.5 cocked brow)")
    brow_tilt_l: float = Field(default=0.10, description="Left brow tilt angle in rad (negative angry, positive sad/surprised)")
    brow_tilt_r: float = Field(default=-0.10, description="Right brow tilt angle in rad")
    eyelid_close_l: float = Field(default=0.0, description="Left upper eyelid closure 0.0 open to 1.0 wink/closed")
    eyelid_close_r: float = Field(default=0.0, description="Right upper eyelid closure 0.0 open to 1.0 closed")
    mouth_open: float = Field(default=0.0, description="Base mouth opening 0.0 closed to 1.0 wide open")
    mouth_width: float = Field(default=1.0, description="Mouth horizontal width scale 0.6 to 1.4")
    mouth_curve: float = Field(default=0.35, description="Smile (>0) vs frown (<0) curve in [-1.0, 1.0]")
    smirk_skew: float = Field(default=0.0, description="Sideways smirk offset in [-1.0, 1.0]")
    chew_hz: float = Field(default=0.0, description="Jaw chewing/quiver frequency Hz (0 if still)")
    blush: bool = False
    tears: bool = False
    eye_scale_y: float = Field(default=1.0, description="Sclera vertical scale hint")
    notes: str = ""


class ExpressionLearningCore:
    """
    Learns facial expressions dynamically from reference descriptions and persists
    reusable `.py` + `.js` facial mimic generation scripts.
    """

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or config.GEMINI_API_KEY
        self.client = genai.Client(api_key=key) if key else None
        self.py_out_dir = Path(config.BASE_DIR) / "core" / "generated_expressions"
        self.js_out_file = Path(config.BASE_DIR) / "assets" / "three" / "generated" / "custom_expressions.js"
        self.py_out_dir.mkdir(parents=True, exist_ok=True)
        self.js_out_file.parent.mkdir(parents=True, exist_ok=True)
        self.learned_profiles: Dict[str, Dict[str, Any]] = {}
        self._bootstrap_existing()

    def _bootstrap_existing(self) -> None:
        loaded = load_all_generated_expressions()
        self.learned_profiles.update(loaded)
        for eid, prof in loaded.items():
            if eid not in EXPRESSION_KNOWLEDGE_BASE:
                EXPRESSION_KNOWLEDGE_BASE[eid] = prof

    @staticmethod
    def _normalize_id(expr: str) -> str:
        clean = re.sub(r"[^a-zA-Z0-9]+", "_", (expr or "happy").strip().lower()).strip("_")
        return clean or "happy"

    def _learn_via_gemini(self, clean_id: str, context: str) -> Optional[FacialAUBlueprint]:
        if not self.client:
            return None
        prompt = f"""
You are a Pixar Facial Rigger & FACS (Facial Action Coding System) specialist.
Learn and parameterize the unseen facial expression `{clean_id}` observed in this video scene context:
\"\"\"{context}\"\"\"

Output clean physical facial parameters:
- `brow_lift` (-0.014 furrowed .. +0.028 startled high), `brow_tilt_l` / `brow_tilt_r` (-0.45 fierce V .. +0.35 puppy-dog worried)
- `eyelid_close_l` / `eyelid_close_r` (0.0 wide open .. 0.45 sleepy/squint .. 1.0 winking/shut)
- `mouth_open` (0.0 closed .. 0.95 screaming O), `mouth_curve` (-0.8 frown .. +0.9 broad smile), `smirk_skew` (-0.8..+0.8)
- `chew_hz` (2.0..3.5 only if eating/chewing/chattering, otherwise 0.0)
- `blush` and `tears` booleans.
"""
        tried = set()
        for mname in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite-preview", "gemini-3-flash-preview"]:
            if not mname or mname in tried:
                continue
            tried.add(mname)
            try:
                resp = self.client.models.generate_content(
                    model=mname,
                    contents=[prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=FacialAUBlueprint,
                        temperature=0.25,
                    ),
                )
                bp = resp.parsed if hasattr(resp, "parsed") and isinstance(resp.parsed, FacialAUBlueprint) else FacialAUBlueprint.model_validate_json(resp.text)
                bp.expression_id = clean_id
                return bp
            except Exception as err:
                log_warning(f"[ExpressionLearningCore] Gemini synth ({mname}) skipped: {err}")
        return None

    def _semantic_facs_fallback(self, clean_id: str, context: str) -> FacialAUBlueprint:
        low = f"{clean_id} {context}".lower().replace("_", " ")
        if any(w in low for w in ("smirk", "mischiev", "sneaky", "evil", "sly", "grin")):
            return FacialAUBlueprint(expression_id=clean_id, display_name=clean_id.replace("_", " ").title(), brow_lift=0.015, brow_asymmetry=-0.4, brow_tilt_l=0.18, brow_tilt_r=-0.28, mouth_curve=0.65, smirk_skew=0.75, notes="Mischievous cocked-brow smirk.")
        if any(w in low for w in ("wink", "flirt", "blink")):
            return FacialAUBlueprint(expression_id=clean_id, display_name=clean_id.replace("_", " ").title(), brow_lift=0.014, eyelid_close_l=0.0, eyelid_close_r=0.95, mouth_curve=0.80, smirk_skew=0.35, blush=True, notes="Playful one-eye wink with smile.")
        if any(w in low for w in ("chew", "eat", "bite", "yum", "nom", "delicious", "hungry")):
            return FacialAUBlueprint(expression_id=clean_id, display_name=clean_id.replace("_", " ").title(), brow_lift=0.012, eyelid_close_l=0.25, eyelid_close_r=0.25, mouth_open=0.52, mouth_width=1.15, mouth_curve=0.70, chew_hz=2.8, blush=True, notes="Happy chewing motion with closed content eyes.")
        if any(w in low for w in ("sleep", "yawn", "tired", "exhaust", "nap", "groggy")):
            return FacialAUBlueprint(expression_id=clean_id, display_name=clean_id.replace("_", " ").title(), brow_lift=-0.004, eyelid_close_l=0.72, eyelid_close_r=0.72, mouth_open=0.62, mouth_width=0.88, mouth_curve=-0.1, notes="Drowsy drooping eyelids and yawn.")
        if any(w in low for w in ("panic", "scream", "terrified", "scared", "fear", "horrif")):
            return FacialAUBlueprint(expression_id=clean_id, display_name=clean_id.replace("_", " ").title(), brow_lift=0.028, brow_tilt_l=0.25, brow_tilt_r=-0.25, mouth_open=0.95, mouth_width=0.92, mouth_curve=-0.6, chew_hz=4.5, notes="High-tension startled scream.")
        if any(w in low for w in ("disgust", "eww", "gross", "yuck", "cringe", "stink")):
            return FacialAUBlueprint(expression_id=clean_id, display_name=clean_id.replace("_", " ").title(), brow_lift=-0.010, brow_tilt_l=-0.32, brow_tilt_r=0.22, eyelid_close_l=0.55, eyelid_close_r=0.35, mouth_curve=-0.75, smirk_skew=-0.5, notes="Cringe squint with asymmetric frown.")
        if any(w in low for w in ("confus", "squint", "puzzle", "doubt", "hmm")):
            return FacialAUBlueprint(expression_id=clean_id, display_name=clean_id.replace("_", " ").title(), brow_lift=0.018, brow_asymmetry=-0.6, brow_tilt_l=0.22, brow_tilt_r=-0.28, eyelid_close_l=0.0, eyelid_close_r=0.38, mouth_curve=-0.2, smirk_skew=0.3, notes="Puzzled eyebrow raise with slight squint.")
        return FacialAUBlueprint(expression_id=clean_id, display_name=clean_id.replace("_", " ").title(), brow_lift=0.012, mouth_curve=0.55, blush=True, notes=f"Learned gentle expression for '{clean_id}'.")

    def _write_python_expression_core(self, bp: FacialAUBlueprint) -> Path:
        py_file = self.py_out_dir / f"{bp.expression_id}_expr.py"
        prof_repr = pprint.pformat(bp.model_dump(), indent=2, sort_dicts=False)
        code = f'''"""
Auto-generated Facial Expression Core: `{bp.display_name}` (`{bp.expression_id}`).
Synthesized autonomously by `ExpressionLearningCore`.
"""

EXPRESSION_PROFILE = {prof_repr}
'''
        py_file.write_text(code, encoding="utf-8")
        return py_file

    def _rebuild_js_expressions_runtime(self) -> Path:
        all_profs: Dict[str, Any] = {}
        for k, v in sorted(self.learned_profiles.items()):
            all_profs[k] = v

        existing_body = """
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
"""
        js_src = (
            "/**\n"
            " * Auto-generated FACS Expression Profiles maintained dynamically by `core/expression_knowledge_core.py`.\n"
            " */\n"
            "export const GENERATED_EXPRESSION_PROFILES = " + json.dumps(all_profs, indent=2) + ";\n"
            + existing_body
        )
        self.js_out_file.write_text(js_src, encoding="utf-8")
        return self.js_out_file

    def ensure_expression_core(self, expr_name: str, context: str = "") -> Dict[str, Any]:
        clean_id = self._normalize_id(expr_name)
        if clean_id in ("none", "neutral", "normal", "calm"):
            return EXPRESSION_KNOWLEDGE_BASE["happy"]
        if clean_id in EXPRESSION_KNOWLEDGE_BASE:
            return EXPRESSION_KNOWLEDGE_BASE[clean_id]
        if clean_id in self.learned_profiles:
            return self.learned_profiles[clean_id]

        log_info(f"[ExpressionLearningCore] New unseen expression '{expr_name}' -> learning FACS mimicry & writing core script...")
        bp = self._learn_via_gemini(clean_id, context) or self._semantic_facs_fallback(clean_id, context)
        prof = bp.model_dump()
        self.learned_profiles[clean_id] = prof
        EXPRESSION_KNOWLEDGE_BASE[clean_id] = prof
        py_file = self._write_python_expression_core(bp)
        js_file = self._rebuild_js_expressions_runtime()
        log_success(f"[ExpressionLearningCore] Generated '{py_file.name}' & updated '{js_file.name}' for expression '{clean_id}'")
        return prof

    def ensure_expressions_for_scenes(self, scenes: List) -> Dict[str, Any]:
        out: Dict[str, Any] = dict(self.learned_profiles)
        for sc in scenes or []:
            ctx = f"{getattr(sc, 'narration', '')} | {getattr(sc, 'ref_scene_action_summary', '')}"
            for attr in ("lead_expression", "partner_expression"):
                ex = getattr(sc, attr, None)
                if ex:
                    cid = self._normalize_id(str(ex))
                    prof = self.ensure_expression_core(cid, context=ctx)
                    if cid in self.learned_profiles or "brow_lift" in prof:
                        out[cid] = prof
        return out

