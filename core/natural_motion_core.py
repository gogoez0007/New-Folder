"""
Core 9: Natural Biomechanical Motion Core (`core/natural_motion_core.py`).

Encodes organic character animation kinematics (anticipation, ease-in/ease-out bell gestures,
eye/head-leads-torso overlap, asymmetric calm breathing, and procedural shoulder/arm posture)
and dynamically generates new Python (`core/generated_motions/<id>_motion.py`) & JavaScript
(`assets/three/generated/custom_motions.js`) motion profiles for any unseen reference actions.
"""

import json
import pprint
import re
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from google import genai
from google.genai import types

import config
from core.generated_motions import load_all_generated_motions
from utils.logger import log_info, log_success, log_warning


ArmPostureLiteral = Literal["neutral", "alert_raised", "reach_forward", "hands_hips", "recoil_guard"]
GestureCurveLiteral = Literal["none", "nod_yes", "shake_no", "curious_glance", "laugh_bounce", "recoil_snap"]


class NaturalMotionProfile(BaseModel):
    """Biomechanical natural motion rule driving smooth 60FPS WebGL kinematics."""
    action_id: str
    display_name: str
    anim_mode: str = "idle"
    spine_tilt_x: float = 0.0
    breath_amp: float = 0.020
    sway_amp: float = 0.012
    head_pitch: float = 0.0
    head_lead_speed: float = 7.5
    torso_follow_speed: float = 4.8
    body_turn_speed: float = 4.5
    gesture_type: GestureCurveLiteral = "none"
    gesture_amp: float = 0.0
    gesture_cycles: float = 2.0
    arm_posture: ArmPostureLiteral = "neutral"
    head_roll_bias: float = 0.0
    notes: str = ""


BUILTIN_NATURAL_MOTIONS: Dict[str, Dict[str, Any]] = {
    "walk_casual": {"display_name": "Casual Walk", "anim_mode": "walk", "spine_tilt_x": 0.025, "gesture_type": "none", "arm_posture": "neutral"},
    "run_urgent": {"display_name": "Urgent Run", "anim_mode": "run", "spine_tilt_x": 0.11, "head_pitch": -0.04, "gesture_type": "none", "arm_posture": "reach_forward"},
    "sneak_tiptoe": {"display_name": "Sneaky Tiptoe", "anim_mode": "sneak", "spine_tilt_x": 0.14, "head_pitch": 0.05, "gesture_type": "curious_glance", "gesture_amp": 0.09, "gesture_cycles": 1.5, "arm_posture": "alert_raised"},
    "talk_explain": {"display_name": "Natural Talking", "anim_mode": "wave", "spine_tilt_x": 0.01, "gesture_type": "nod_yes", "gesture_amp": 0.05, "gesture_cycles": 1.5, "arm_posture": "neutral"},
    "listen_nod": {"display_name": "Attentive Listen & Nod", "anim_mode": "idle", "spine_tilt_x": 0.02, "gesture_type": "nod_yes", "gesture_amp": 0.10, "gesture_cycles": 2.0, "arm_posture": "neutral"},
    "shake_head_no": {"display_name": "Natural Head Shake No", "anim_mode": "interact", "spine_tilt_x": -0.03, "gesture_type": "shake_no", "gesture_amp": 0.22, "gesture_cycles": 2.0, "arm_posture": "recoil_guard"},
    "interact_use_prop": {"display_name": "Use Prop", "anim_mode": "interact", "spine_tilt_x": 0.05, "head_pitch": 0.05, "gesture_type": "none", "arm_posture": "reach_forward"},
    "pick_up_inspect": {"display_name": "Pick Up & Inspect", "anim_mode": "pickup", "spine_tilt_x": 0.06, "head_pitch": 0.08, "gesture_type": "curious_glance", "gesture_amp": 0.06, "gesture_cycles": 1.0, "arm_posture": "reach_forward"},
    "give_or_share": {"display_name": "Give or Share", "anim_mode": "interact", "spine_tilt_x": 0.04, "gesture_type": "nod_yes", "gesture_amp": 0.07, "gesture_cycles": 1.5, "arm_posture": "reach_forward"},
    "push_or_block": {"display_name": "Push or Block", "anim_mode": "interact", "spine_tilt_x": 0.08, "head_pitch": -0.02, "gesture_type": "none", "arm_posture": "recoil_guard"},
    "recoil_surprise": {"display_name": "Startled Recoil", "anim_mode": "wave", "spine_tilt_x": -0.07, "head_pitch": -0.09, "gesture_type": "recoil_snap", "gesture_amp": 0.08, "gesture_cycles": 1.0, "arm_posture": "recoil_guard"},
    "sit_floor_relax": {"display_name": "Sit Relaxed", "anim_mode": "sit_floor", "spine_tilt_x": -0.03, "gesture_type": "none", "arm_posture": "neutral"},
    "sit_chair_or_bench": {"display_name": "Sit in Chair", "anim_mode": "sit_chair", "spine_tilt_x": 0.0, "gesture_type": "none", "arm_posture": "neutral"},
    "lie_down_exhausted": {"display_name": "Lie Down Rest", "anim_mode": "lie_down", "spine_tilt_x": 0.0, "breath_amp": 0.028, "gesture_type": "none", "arm_posture": "neutral"},
    "sad_cry_slump": {"display_name": "Sad Slump", "anim_mode": "idle", "spine_tilt_x": 0.10, "head_pitch": 0.14, "gesture_type": "none", "arm_posture": "neutral"},
    "plead_camera_help": {"display_name": "Plead Help", "anim_mode": "wave", "spine_tilt_x": 0.05, "head_pitch": -0.04, "gesture_type": "nod_yes", "gesture_amp": 0.06, "gesture_cycles": 1.5, "arm_posture": "alert_raised"},
    "point_discover": {"display_name": "Point & Discover", "anim_mode": "interact", "spine_tilt_x": 0.04, "head_pitch": -0.04, "gesture_type": "curious_glance", "gesture_amp": 0.06, "gesture_cycles": 1.0, "head_roll_bias": 0.05, "arm_posture": "reach_forward"},
    "laugh_giggle": {"display_name": "Happy Laugh", "anim_mode": "cheer", "spine_tilt_x": -0.06, "head_pitch": -0.06, "gesture_type": "laugh_bounce", "gesture_amp": 0.07, "gesture_cycles": 2.5, "arm_posture": "alert_raised"},
    "cheer_celebrate": {"display_name": "Cheer Celebrate", "anim_mode": "cheer", "spine_tilt_x": -0.05, "head_pitch": -0.06, "gesture_type": "laugh_bounce", "gesture_amp": 0.05, "gesture_cycles": 2.0, "arm_posture": "alert_raised"},
    "dance_groove": {"display_name": "Dance Groove", "anim_mode": "dance", "spine_tilt_x": 0.0, "sway_amp": 0.028, "gesture_type": "laugh_bounce", "gesture_amp": 0.06, "gesture_cycles": 2.5, "arm_posture": "alert_raised"},
    "jump_obstacle_or_joy": {"display_name": "Jump Leap", "anim_mode": "jump", "spine_tilt_x": -0.04, "head_pitch": -0.08, "gesture_type": "none", "arm_posture": "alert_raised"},
}


class NaturalMotionCore:
    """
    Learns, persists, and exports natural human/cartoon biomechanical motion rules
    so every action has smooth anticipation, head-lead torso overlap, and zero robotic jitter.
    """

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or config.GEMINI_API_KEY
        self.client = genai.Client(api_key=key) if key else None
        self.py_out_dir = Path(config.BASE_DIR) / "core" / "generated_motions"
        self.js_out_file = Path(config.BASE_DIR) / "assets" / "three" / "generated" / "custom_motions.js"
        self.py_out_dir.mkdir(parents=True, exist_ok=True)
        self.js_out_file.parent.mkdir(parents=True, exist_ok=True)
        self.profiles: Dict[str, Dict[str, Any]] = {
            k: NaturalMotionProfile(action_id=k, **v).model_dump()
            for k, v in BUILTIN_NATURAL_MOTIONS.items()
        }
        self._bootstrap_existing()

    def _bootstrap_existing(self) -> None:
        for aid, prof in load_all_generated_motions().items():
            self.profiles[aid] = prof

    @staticmethod
    def _normalize_id(act: str) -> str:
        return re.sub(r"[^a-zA-Z0-9]+", "_", (act or "idle").strip().lower()).strip("_") or "talk_explain"

    def _learn_via_gemini(self, clean_id: str, context: str) -> Optional[NaturalMotionProfile]:
        if not self.client:
            return None
        prompt = f"""
You are a Senior Character Animator specializing in Disney/Pixar natural body mechanics.
Design a natural smooth motion profile for unseen physical action `{clean_id}` seen in:
\"\"\"{context}\"\"\"

Output subtle realistic radians/rates (NEVER fast bobblehead shaking!):
- `anim_mode`: one of `idle`, `walk`, `run`, `sneak`, `interact`, `pickup`, `sit_floor`, `sit_chair`, `lie_down`, `cheer`, `dance`, `wave`, `jump`
- `spine_tilt_x`: -0.10..0.14 rad
- `gesture_type`: `none`, `nod_yes`, `shake_no`, `curious_glance`, `laugh_bounce`, or `recoil_snap`
- `gesture_amp`: 0.0..0.22 rad max (subtle & lifelike!)
- `arm_posture`: `neutral`, `alert_raised`, `reach_forward`, `hands_hips`, `recoil_guard`
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
                        response_schema=NaturalMotionProfile,
                        temperature=0.25,
                    ),
                )
                bp = resp.parsed if hasattr(resp, "parsed") and isinstance(resp.parsed, NaturalMotionProfile) else NaturalMotionProfile.model_validate_json(resp.text)
                bp.action_id = clean_id
                bp.head_lead_speed = max(5.5, min(11.0, float(bp.head_lead_speed))) if bp.head_lead_speed >= 3.0 else 7.5
                bp.torso_follow_speed = max(3.5, min(7.5, float(bp.torso_follow_speed))) if bp.torso_follow_speed >= 2.0 else 4.8
                bp.body_turn_speed = max(3.5, min(7.5, float(bp.body_turn_speed))) if bp.body_turn_speed >= 2.0 else 4.5
                bp.spine_tilt_x = max(-0.14, min(0.14, float(bp.spine_tilt_x)))
                bp.head_pitch = max(-0.15, min(0.15, float(bp.head_pitch)))
                bp.gesture_amp = max(0.0, min(0.22, float(bp.gesture_amp)))
                return bp
            except Exception as err:
                log_warning(f"[NaturalMotionCore] Gemini synth ({mname}) skipped: {err}")
        return None

    def _semantic_motion_fallback(self, clean_id: str, context: str) -> NaturalMotionProfile:
        low = f"{clean_id} {context}".lower().replace("_", " ")
        if any(w in low for w in ("shake", "no", "deny", "refuse")):
            return NaturalMotionProfile(action_id=clean_id, display_name=clean_id.replace("_", " ").title(), anim_mode="interact", gesture_type="shake_no", gesture_amp=0.22, gesture_cycles=2.0, arm_posture="recoil_guard")
        if any(w in low for w in ("selfie", "phone", "hold", "record", "film", "eat", "poke")):
            return NaturalMotionProfile(action_id=clean_id, display_name=clean_id.replace("_", " ").title(), anim_mode="interact", spine_tilt_x=0.04, head_pitch=0.04, gesture_type="curious_glance", gesture_amp=0.05, gesture_cycles=1.0, arm_posture="reach_forward")
        if any(w in low for w in ("peek", "look", "spy", "watch", "stalk")):
            return NaturalMotionProfile(action_id=clean_id, display_name=clean_id.replace("_", " ").title(), anim_mode="idle", spine_tilt_x=0.10, head_pitch=0.06, gesture_type="curious_glance", gesture_amp=0.07, gesture_cycles=1.0, arm_posture="neutral")
        return NaturalMotionProfile(action_id=clean_id, display_name=clean_id.replace("_", " ").title(), anim_mode="idle", spine_tilt_x=0.02, arm_posture="neutral")

    def _write_python_motion_core(self, prof: NaturalMotionProfile) -> Path:
        py_file = self.py_out_dir / f"{prof.action_id}_motion.py"
        prof_repr = pprint.pformat(prof.model_dump(), indent=2, sort_dicts=False)
        code = f'''"""
Auto-generated Natural Motion Core: `{prof.display_name}` (`{prof.action_id}`).
Synthesized autonomously by `NaturalMotionCore`.
"""

MOTION_PROFILE = {prof_repr}
'''
        py_file.write_text(code, encoding="utf-8")
        return py_file

    def _rebuild_js_motions_runtime(self) -> Path:
        custom = {k: v for k, v in sorted(self.profiles.items()) if k not in BUILTIN_NATURAL_MOTIONS or (self.py_out_dir / f"{k}_motion.py").exists()}
        js_src = (
            "/**\n"
            " * Auto-generated Natural Motion Kinetics maintained dynamically by `core/natural_motion_core.py`.\n"
            " */\n"
            "export const GENERATED_MOTION_PROFILES = " + json.dumps(custom, indent=2) + ";\n"
        )
        self.js_out_file.write_text(js_src, encoding="utf-8")
        return self.js_out_file

    def ensure_motion_core(self, action_name: str, context: str = "") -> Dict[str, Any]:
        clean_id = self._normalize_id(action_name)
        if clean_id in ("none", "idle", "wait", "watch"):
            return NaturalMotionProfile(action_id="idle", display_name="Idle Calm", anim_mode="idle").model_dump()
        if clean_id in self.profiles:
            return self.profiles[clean_id]

        log_info(f"[NaturalMotionCore] New unseen action '{action_name}' -> learning natural biomechanics & writing core script...")
        bp = self._learn_via_gemini(clean_id, context) or self._semantic_motion_fallback(clean_id, context)
        prof = bp.model_dump()
        self.profiles[clean_id] = prof
        py_file = self._write_python_motion_core(bp)
        js_file = self._rebuild_js_motions_runtime()
        log_success(f"[NaturalMotionCore] Generated '{py_file.name}' & updated '{js_file.name}' for action '{clean_id}'")
        return prof

    def ensure_motions_for_scenes(self, scenes: List) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = dict(self.profiles)
        for sc in scenes or []:
            ctx = f"{getattr(sc, 'narration', '')} | {getattr(sc, 'ref_scene_action_summary', '')}"
            for attr in ("lead_action", "partner_action"):
                act = getattr(sc, attr, None)
                if act:
                    p = self.ensure_motion_core(str(act), context=ctx)
                    out[self._normalize_id(str(act))] = p
        return out

