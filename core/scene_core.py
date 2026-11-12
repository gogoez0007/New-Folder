"""
Core 2: Data-Driven 3D Scene Choreography & Motion/Expression Knowledge Engine (`core/scene_core.py`).

Translates each reference-mirrored `Scene` (from `AnalystWriterAgent`), `BackgroundStorySpec` (Core 3),
and `CharacterRoster` (Core 1) into a grounded, expressive 3D choreography graph (`SceneDirectingSpec`):
- Built-in Knowledge Base (`MOTION_KNOWLEDGE_BASE` & `EXPRESSION_KNOWLEDGE_BASE`) covering 21 grounded
  physical actions (`walk_casual`, `run_urgent`, `sneak_tiptoe`, `talk_explain`, `listen_nod`,
  `shake_head_no`, `interact_use_prop`, `pick_up_inspect`, `give_or_share`, `push_or_block`,
  `recoil_surprise`, `sit_floor_relax`, `sit_chair_or_bench`, `lie_down_exhausted`, `sad_cry_slump`,
  `plead_camera_help`, `point_discover`, `laugh_giggle`, `cheer_celebrate`, `dance_groove`,
  `jump_obstacle_or_joy`) and 12 facial/postural expressions.
- ZERO constant jumping: `jump_arc_height` is strictly `0.0` for all grounded actions, and is only
  used when a scene in the reference video explicitly involves jumping (`jump_obstacle_or_joy`).
- Dynamic spatial blocking (`spatial_pattern`) and camera framing (`camera_shot_style`) mirroring
  the reference video scene-by-scene without hardcoding.
"""

import math
import re
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field

from core.background_story_core import BackgroundStorySpec, EnvironmentPropSpec
from core.character_core import CharacterRoster


AnimModeType = Literal[
    "walk",
    "run",
    "sneak",
    "interact",
    "pickup",
    "sit_floor",
    "sit_chair",
    "lie_down",
    "wave",
    "cheer",
    "dance",
    "idle",
    "jump",
    "pet_walk",
    "pet_run",
    "fly",
]

ExpressionType = str

EmoteBubbleType = Literal["!", "?", "heart", "broken_heart", "star", "help", "music"]

FxTriggerType = Literal["water_splash", "magic_spawn_ring", "confetti_burst", "dust_puff"]


# ==============================================================================
# KNOWLEDGE BASE: 21 GROUNDED PHYSICAL ACTIONS & POSTURAL KINEMATICS
# ==============================================================================
MOTION_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "walk_casual": {
        "anim_mode": "walk",
        "is_locomotion": True,
        "spine_tilt_x": 0.02,
        "head_pitch": 0.0,
        "head_yaw_osc": 0.0,
        "head_nod_osc": 0.0,
        "y_offset": 0.0,
        "jump_arc": 0.0,
    },
    "run_urgent": {
        "anim_mode": "run",
        "is_locomotion": True,
        "spine_tilt_x": 0.10,
        "head_pitch": -0.03,
        "head_yaw_osc": 0.0,
        "head_nod_osc": 0.0,
        "y_offset": 0.0,
        "jump_arc": 0.0,
    },
    "sneak_tiptoe": {
        "anim_mode": "sneak",
        "is_locomotion": True,
        "spine_tilt_x": 0.14,
        "head_pitch": 0.05,
        "head_yaw_osc": 0.10,
        "head_nod_osc": 0.0,
        "y_offset": -0.04,
        "jump_arc": 0.0,
    },
    "talk_explain": {
        "anim_mode": "wave",
        "is_locomotion": False,
        "spine_tilt_x": 0.0,
        "head_pitch": 0.0,
        "head_yaw_osc": 0.0,
        "head_nod_osc": 0.06,
        "y_offset": 0.0,
        "jump_arc": 0.0,
    },
    "listen_nod": {
        "anim_mode": "idle",
        "is_locomotion": False,
        "spine_tilt_x": 0.02,
        "head_pitch": 0.03,
        "head_yaw_osc": 0.0,
        "head_nod_osc": 0.12,
        "y_offset": 0.0,
        "jump_arc": 0.0,
    },
    "shake_head_no": {
        "anim_mode": "interact",
        "is_locomotion": False,
        "spine_tilt_x": -0.04,
        "head_pitch": 0.0,
        "head_yaw_osc": 0.24,
        "head_nod_osc": 0.0,
        "y_offset": 0.0,
        "jump_arc": 0.0,
    },
    "interact_use_prop": {
        "anim_mode": "interact",
        "is_locomotion": False,
        "spine_tilt_x": 0.04,
        "head_pitch": 0.06,
        "head_yaw_osc": 0.0,
        "head_nod_osc": 0.0,
        "y_offset": 0.0,
        "jump_arc": 0.0,
    },
    "pick_up_inspect": {
        "anim_mode": "pickup",
        "is_locomotion": False,
        "spine_tilt_x": 0.0,
        "head_pitch": 0.08,
        "head_yaw_osc": 0.05,
        "head_nod_osc": 0.0,
        "y_offset": 0.0,
        "jump_arc": 0.0,
    },
    "give_or_share": {
        "anim_mode": "interact",
        "is_locomotion": False,
        "spine_tilt_x": 0.04,
        "head_pitch": 0.02,
        "head_yaw_osc": 0.0,
        "head_nod_osc": 0.08,
        "y_offset": 0.0,
        "jump_arc": 0.0,
        "emote": "heart",
    },
    "push_or_block": {
        "anim_mode": "interact",
        "is_locomotion": False,
        "spine_tilt_x": 0.07,
        "head_pitch": -0.02,
        "head_yaw_osc": 0.0,
        "head_nod_osc": 0.0,
        "y_offset": 0.0,
        "jump_arc": 0.0,
        "emote": "!",
    },
    "recoil_surprise": {
        "anim_mode": "wave",
        "is_locomotion": False,
        "spine_tilt_x": -0.06,
        "head_pitch": -0.09,
        "head_yaw_osc": 0.0,
        "head_nod_osc": 0.0,
        "y_offset": 0.0,
        "jump_arc": 0.0,
        "emote": "!",
    },
    "sit_floor_relax": {
        "anim_mode": "sit_floor",
        "is_locomotion": False,
        "spine_tilt_x": -0.03,
        "head_pitch": 0.0,
        "head_yaw_osc": 0.0,
        "head_nod_osc": 0.0,
        "y_offset": -0.18,
        "jump_arc": 0.0,
    },
    "sit_chair_or_bench": {
        "anim_mode": "sit_chair",
        "is_locomotion": False,
        "spine_tilt_x": 0.0,
        "head_pitch": 0.0,
        "head_yaw_osc": 0.0,
        "head_nod_osc": 0.0,
        "y_offset": -0.02,
        "jump_arc": 0.0,
    },
    "lie_down_exhausted": {
        "anim_mode": "lie_down",
        "is_locomotion": False,
        "spine_tilt_x": 0.0,
        "head_pitch": 0.0,
        "head_yaw_osc": 0.0,
        "head_nod_osc": 0.0,
        "y_offset": 0.0,
        "jump_arc": 0.0,
    },
    "sad_cry_slump": {
        "anim_mode": "idle",
        "is_locomotion": False,
        "spine_tilt_x": 0.09,
        "head_pitch": 0.14,
        "head_yaw_osc": 0.0,
        "head_nod_osc": 0.0,
        "y_offset": 0.0,
        "jump_arc": 0.0,
        "emote": "broken_heart",
    },
    "plead_camera_help": {
        "anim_mode": "wave",
        "is_locomotion": False,
        "spine_tilt_x": 0.05,
        "head_pitch": -0.04,
        "head_yaw_osc": 0.0,
        "head_nod_osc": 0.06,
        "y_offset": 0.0,
        "jump_arc": 0.0,
        "emote": "help",
    },
    "point_discover": {
        "anim_mode": "interact",
        "is_locomotion": False,
        "spine_tilt_x": 0.04,
        "head_pitch": -0.05,
        "head_yaw_osc": 0.06,
        "head_nod_osc": 0.0,
        "y_offset": 0.0,
        "jump_arc": 0.0,
        "emote": "?",
    },
    "laugh_giggle": {
        "anim_mode": "cheer",
        "is_locomotion": False,
        "spine_tilt_x": -0.05,
        "head_pitch": -0.07,
        "head_yaw_osc": 0.0,
        "head_nod_osc": 0.08,
        "y_offset": 0.0,
        "jump_arc": 0.0,
    },
    "cheer_celebrate": {
        "anim_mode": "cheer",
        "is_locomotion": False,
        "spine_tilt_x": -0.04,
        "head_pitch": -0.06,
        "head_yaw_osc": 0.0,
        "head_nod_osc": 0.06,
        "y_offset": 0.0,
        "jump_arc": 0.0,
        "emote": "star",
    },
    "dance_groove": {
        "anim_mode": "dance",
        "is_locomotion": False,
        "spine_tilt_x": 0.0,
        "head_pitch": 0.0,
        "head_yaw_osc": 0.22,
        "head_nod_osc": 0.18,
        "y_offset": 0.0,
        "jump_arc": 0.0,
        "emote": "music",
    },
    "jump_obstacle_or_joy": {
        "anim_mode": "jump",
        "is_locomotion": True,
        "spine_tilt_x": -0.05,
        "head_pitch": -0.10,
        "head_yaw_osc": 0.0,
        "head_nod_osc": 0.0,
        "y_offset": 0.0,
        "jump_arc": 0.48,
        "emote": "star",
    },
}

# ==============================================================================
# KNOWLEDGE BASE: 12 FACIAL & POSTURAL EXPRESSIONS
# ==============================================================================
EXPRESSION_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "happy": {"brow_angle": 0.0, "eye_scale_y": 1.0, "mouth_curve": 0.6, "blush": True, "tears": False},
    "excited": {"brow_angle": -0.15, "eye_scale_y": 1.18, "mouth_curve": 0.85, "blush": True, "tears": False},
    "curious": {"brow_angle": -0.22, "eye_scale_y": 1.12, "mouth_curve": 0.1, "blush": False, "tears": False},
    "surprised": {"brow_angle": -0.30, "eye_scale_y": 1.28, "mouth_curve": -0.1, "blush": False, "tears": False},
    "shocked": {"brow_angle": -0.35, "eye_scale_y": 1.35, "mouth_curve": -0.3, "blush": False, "tears": False},
    "sad": {"brow_angle": 0.32, "eye_scale_y": 0.78, "mouth_curve": -0.65, "blush": False, "tears": False},
    "crying": {"brow_angle": 0.38, "eye_scale_y": 0.65, "mouth_curve": -0.85, "blush": False, "tears": True},
    "angry": {"brow_angle": -0.42, "eye_scale_y": 0.82, "mouth_curve": -0.55, "blush": False, "tears": False},
    "determined": {"brow_angle": -0.28, "eye_scale_y": 0.92, "mouth_curve": 0.25, "blush": False, "tears": False},
    "embarrassed": {"brow_angle": 0.22, "eye_scale_y": 0.85, "mouth_curve": -0.2, "blush": True, "tears": False},
    "proud": {"brow_angle": -0.12, "eye_scale_y": 0.95, "mouth_curve": 0.75, "blush": True, "tears": False},
    "laughing": {"brow_angle": -0.18, "eye_scale_y": 0.45, "mouth_curve": 1.0, "blush": True, "tears": False},
}


class ActorPhaseSpec(BaseModel):
    """A single time-bounded grounded acting phase within a scene."""
    start_ratio: float = 0.0
    end_ratio: float = 1.0
    from_pos: Tuple[float, float, float]
    to_pos: Tuple[float, float, float]
    jump_arc_height: float = 0.0
    anim_mode: AnimModeType = "idle"
    action: str = "talk_explain"
    expression: ExpressionType = "happy"
    spine_tilt_x: float = 0.0
    head_pitch: float = 0.0
    head_yaw_osc: float = 0.08
    head_nod_osc: float = 0.08
    y_offset: float = 0.0
    look_at: Optional[Tuple[float, float, float]] = None
    in_pool: bool = False
    emote_bubble: Optional[EmoteBubbleType] = None
    fx_trigger: Optional[FxTriggerType] = None


class ActorPlacementSpec(BaseModel):
    """3D choreography & multi-phase motion timeline for one character in a scene."""
    char_id: str
    start_pos: Tuple[float, float, float]
    end_pos: Tuple[float, float, float]
    look_at_target: Optional[Tuple[float, float, float]] = None
    action: str = "talk_explain"
    expression: ExpressionType = "happy"
    is_speaking: bool = False
    in_pool: bool = False
    collision_radius: float = 0.42
    phases: List[ActorPhaseSpec] = Field(default_factory=list)


class CameraShotSpec(BaseModel):
    """3D camera trajectory for a single shot within a scene."""
    shot_index: int
    start_ratio: float
    end_ratio: float
    cam_start: Tuple[float, float, float]
    cam_end: Tuple[float, float, float]
    look_start: Tuple[float, float, float]
    look_end: Tuple[float, float, float]
    fov_deg: float = 50.0


class SceneDirectingSpec(BaseModel):
    """Complete 3D scene choreography for all characters, stations, HUD overlays, and cameras."""
    scene_number: int
    duration: float
    narration: str
    scene_template: str = "face_to_face_dialogue"
    beat_type: str
    emotional_tone: str
    show_hero_station: bool = False
    hud_mode: Literal["none", "help_like_cta", "like_subscribe_cta", "finale_banner"] = "none"
    is_cliffhanger_finale: bool = False
    cliffhanger_badge_text: str = ""
    outro_vfx_style: str = "portal_vortex_zoom"
    expression_kb: Dict[str, Dict[str, Any]] = Field(default_factory=lambda: EXPRESSION_KNOWLEDGE_BASE)
    actors: List[ActorPlacementSpec] = Field(default_factory=list)
    camera_shots: List[CameraShotSpec] = Field(default_factory=list)


class SceneCore:
    """
    Data-Driven 3D Choreography Engine with Anti-Repetition Variator & 360-Degree Camera Directing.
    Directly compiles each reference-mirrored `Scene` (`lead_action`, `partner_action`,
    `lead_expression`, `partner_expression`, `spatial_pattern`, `camera_shot_style`, `scene_props`)
    into grounded, visually distinct 3D scenes with zero repeated static angles or positions.
    """

    def __init__(self):
        self._clip_scene_history: Dict[str, List[Dict[str, Any]]] = {}

    CAMERA_ROTATION = [
        "wide_establishing",
        "close_up_reaction",
        "over_shoulder",
        "low_angle_hero",
        "high_angle_overview",
        "tracking_side",
        "medium_two_shot",
    ]
    SPATIAL_ROTATION = [
        "approach_center",
        "left_to_right_travel",
        "gather_around_prop",
        "step_back_recoil",
        "walk_to_camera",
        "side_by_side_walk",
        "right_to_left_travel",
        "face_to_face_dialogue",
    ]
    ALT_ACTIONS = [
        "point_discover",
        "talk_explain",
        "walk_casual",
        "pick_up_inspect",
        "recoil_surprise",
        "interact_use_prop",
        "cheer_celebrate",
    ]
    STAGE_ZONES: List[Tuple[float, float]] = [
        (0.0, 0.0),      # Zone 0: center stage
        (-1.45, -0.55),  # Zone 1: left grove
        (1.45, -0.55),   # Zone 2: right grove
        (0.0, 1.15),     # Zone 3: close foreground
        (0.0, -1.45),    # Zone 4: deep panorama vista
    ]

    def _build_phase_from_kb(
        self,
        start_ratio: float,
        end_ratio: float,
        from_pos: Tuple[float, float, float],
        to_pos: Tuple[float, float, float],
        action_key: str,
        expression: ExpressionType = "happy",
        look_at: Optional[Tuple[float, float, float]] = None,
        in_pool: bool = False,
        override_emote: Optional[EmoteBubbleType] = None,
        fx_trigger: Optional[FxTriggerType] = None,
    ) -> ActorPhaseSpec:
        learned_motions = {}
        try:
            from core.generated_motions import load_all_generated_motions
            learned_motions = load_all_generated_motions()
        except Exception:
            learned_motions = {}

        if action_key in MOTION_KNOWLEDGE_BASE:
            kb = MOTION_KNOWLEDGE_BASE[action_key]
        elif action_key in learned_motions:
            lm = learned_motions[action_key]
            kb = {
                "anim_mode": lm.get("anim_mode", "idle"),
                "spine_tilt_x": float(lm.get("spine_tilt_x", 0.0)),
                "head_pitch": float(lm.get("head_pitch", 0.0)),
                "head_yaw_osc": float(lm.get("gesture_amp", 0.06)) if lm.get("gesture_type") in ("shake_no", "curious_glance") else 0.04,
                "head_nod_osc": float(lm.get("gesture_amp", 0.06)) if lm.get("gesture_type") in ("nod_yes", "laugh_bounce") else 0.04,
                "jump_arc": 0.45 if lm.get("anim_mode") == "jump" else 0.0,
                "y_offset": 0.0,
                "emote": None,
            }
        else:
            kb = MOTION_KNOWLEDGE_BASE["talk_explain"]
        dist = math.hypot(to_pos[0] - from_pos[0], to_pos[2] - from_pos[2])

        # Determine anim_mode: if moving significantly (> 0.35m), use walk/run/sneak/jump;
        # if stationary (< 0.35m), NEVER play walk/run in place!
        if dist >= 0.35 and kb["anim_mode"] not in ("walk", "run", "sneak", "jump"):
            anim_mode: AnimModeType = "run" if dist >= 1.8 else "walk"
        elif dist < 0.25 and kb["anim_mode"] in ("walk", "run", "sneak"):
            anim_mode = "wave" if expression in ("excited", "happy") else "idle"
        else:
            anim_mode = kb["anim_mode"]

        emote = override_emote or kb.get("emote")
        return ActorPhaseSpec(
            start_ratio=start_ratio,
            end_ratio=end_ratio,
            from_pos=from_pos,
            to_pos=to_pos,
            jump_arc_height=float(kb.get("jump_arc", 0.0)),
            anim_mode=anim_mode,
            action=action_key,
            expression=expression,
            spine_tilt_x=float(kb.get("spine_tilt_x", 0.0)),
            head_pitch=float(kb.get("head_pitch", 0.0)),
            head_yaw_osc=float(kb.get("head_yaw_osc", 0.08)),
            head_nod_osc=float(kb.get("head_nod_osc", 0.08)),
            y_offset=float(kb.get("y_offset", 0.0)),
            look_at=look_at,
            in_pool=in_pool,
            emote_bubble=emote,
            fx_trigger=fx_trigger,
        )

    def _infer_scene_semantics_if_default(self, scene_obj: Any, scene_number: int, total_scenes: int, narration: str) -> dict:
        """
        Read structured fields from `scene_obj` (populated by Gemini from the reference video),
        and enrich with keyword semantics if any field was left at default.
        """
        n_low = (narration or "").lower()
        lead_act = getattr(scene_obj, "lead_action", None) or "talk_explain"
        if str(lead_act).strip().lower() in ("none", ""):
            lead_act = "talk_explain"
        lead_expr: ExpressionType = getattr(scene_obj, "lead_expression", None) or "happy"
        if str(lead_expr).strip().lower() in ("none", ""):
            lead_expr = "neutral"
        part_act = getattr(scene_obj, "partner_action", None) or "idle"
        if str(part_act).strip().lower() in ("none", ""):
            part_act = "idle"
        part_expr: ExpressionType = getattr(scene_obj, "partner_expression", None) or "curious"
        if str(part_expr).strip().lower() in ("none", ""):
            part_expr = "neutral"
        spatial = getattr(scene_obj, "spatial_pattern", None) or "face_to_face_dialogue"
        cam_style = getattr(scene_obj, "camera_shot_style", None) or "medium_two_shot"

        # If lead_action was left at default "talk_explain", refine from narration keywords
        if lead_act == "talk_explain":
            if any(w in n_low for w in ["faster", "race", "sprint", "rush", "hurry", "chased", "ran"]):
                lead_act = "run_urgent"
                spatial = "left_to_right_travel" if scene_number % 2 == 1 else "right_to_left_travel"
            elif any(w in n_low for w in ["walk", "stroll", "came", "arrived", "went"]):
                lead_act = "walk_casual"
                spatial = "approach_center"
            elif any(w in n_low for w in ["trapped", "cage", "stuck", "help", "please"]):
                lead_act = "plead_camera_help" if "help" in n_low else "sad_cry_slump"
                lead_expr = "sad"
            elif any(w in n_low for w in ["sad", "cried", "faded", "ran out", "gone", "lost", "alone"]):
                lead_act = "sad_cry_slump"
                lead_expr = "sad"
            elif any(w in n_low for w in ["sour", "shock", "popped", "exploded", "poof", "wait", "uh oh", "uncomfortable"]):
                lead_act = "recoil_surprise"
                lead_expr = "shocked"
                spatial = "step_back_recoil"
            elif any(w in n_low for w in ["shared", "gave", "recharged", "helped", "saved", "free"]):
                lead_act = "give_or_share"
                part_act = "cheer_celebrate"
                lead_expr = "proud"
                part_expr = "excited"
                spatial = "face_to_face_dialogue"
            elif any(w in n_low for w in ["tried", "button", "cloche", "opened", "took", "bite", "contraption"]):
                lead_act = "interact_use_prop"
                lead_expr = "curious"
                spatial = "gather_around_prop"
            elif any(w in n_low for w in ["celebrated", "together", "party", "won", "superpower", "yay"]):
                lead_act = "dance_groove" if scene_number % 2 == 0 else "cheer_celebrate"
                part_act = "cheer_celebrate"
                lead_expr = "laughing"
                part_expr = "excited"
            elif any(w in n_low for w in ["jump", "leaped", "hopped", "dived"]):
                lead_act = "jump_obstacle_or_joy"
                lead_expr = "excited"

        # Vary spatial_pattern across scenes if left at default so scenes never look static/identical
        if spatial == "face_to_face_dialogue":
            varied_patterns = [
                "approach_center",
                "gather_around_prop",
                "face_to_face_dialogue",
                "left_to_right_travel",
                "step_back_recoil",
                "walk_to_camera",
                "side_by_side_walk",
            ]
            spatial = varied_patterns[(scene_number - 1) % len(varied_patterns)]

        if cam_style == "medium_two_shot":
            varied_cams = [
                "wide_establishing",
                "medium_two_shot",
                "tracking_side",
                "close_up_reaction",
                "over_shoulder",
                "low_angle_hero",
                "high_angle_overview",
            ]
            cam_style = varied_cams[(scene_number - 1) % len(varied_cams)]

        return {
            "lead_action": lead_act,
            "lead_expression": lead_expr,
            "partner_action": part_act,
            "partner_expression": part_expr,
            "spatial_pattern": spatial,
            "camera_shot_style": cam_style,
        }

    def build_scene_directing(
        self,
        scene_number: int,
        duration: float,
        narration: str,
        story: BackgroundStorySpec,
        roster: CharacterRoster,
        total_scenes: Optional[int] = None,
        total_main_scenes: Optional[int] = None,
        scene_obj: Optional[Any] = None,
        cliffhanger_badge_text: str = "",
        outro_vfx_style: str = "",
    ) -> SceneDirectingSpec:
        n_total = total_scenes or max(6, len(story.beats))
        is_outro_epilogue = bool(getattr(scene_obj, "is_outro_epilogue", False))
        n_main = total_main_scenes or ((n_total - 1) if is_outro_epilogue else n_total)
        beat_idx = min(scene_number - 1, max(0, len(story.beats) - 1))
        beat = story.beats[beat_idx] if story.beats else None
        beat_type = beat.beat_type if beat else "rising_challenge"
        tone = beat.emotional_tone if beat else "excited"

        sem = self._infer_scene_semantics_if_default(scene_obj, scene_number, n_total, narration)
        lead_act = sem["lead_action"]
        lead_expr: ExpressionType = sem["lead_expression"]
        part_act = sem["partner_action"]
        part_expr: ExpressionType = sem["partner_expression"]
        spatial = sem["spatial_pattern"]
        cam_style = sem["camera_shot_style"]
        focus_char = getattr(scene_obj, "focus_character", "both") or "both"

        hist = self._clip_scene_history.setdefault(story.story_id, [])
        if scene_number == 1:
            hist.clear()
        prev = hist[-1] if hist else {}

        # Vertical Elevation Engine: honor explicit Gemini heights (`lead_elevation_m`, `partner_elevation_m`),
        # with strict whole-word keyword fallback only when drop words are absent, transitioning smoothly!
        scene_text = f"{narration} {getattr(scene_obj, 'ref_scene_action_summary', '')}".lower()
        raw_l_elev = float(getattr(scene_obj, "lead_elevation_m", 0.0) or 0.0)
        raw_p_elev = float(getattr(scene_obj, "partner_elevation_m", 0.0) or 0.0)
        scene_prop_list = getattr(scene_obj, "scene_props", None) or []
        has_elev_prop = ("hydraulic_lift_chair" in scene_prop_list) or ("golden_city" in (story.world_biome or ""))
        if raw_p_elev == 0.0 and raw_l_elev == 0.0 and has_elev_prop:
            if any(re.search(r"\b" + re.escape(w) + r"\b", scene_text) for w in ("drop", "drops", "plunge", "retract", "retracts", "going down", "splash", "water", "landed")):
                raw_p_elev = 0.0
            elif any(re.search(r"\b" + re.escape(w) + r"\b", scene_text) for w in ("moon", "airplane", "plane", "above the clouds", "highest")):
                raw_p_elev = 9.5
            elif any(re.search(r"\b" + re.escape(w) + r"\b", scene_text) for w in ("top of", "sky", "buildings", "tower")):
                raw_p_elev = 6.0
            elif any(re.search(r"\b" + re.escape(w) + r"\b", scene_text) for w in ("higher", "ascend", "ascends", "rising", "lifting")):
                raw_p_elev = 2.8

        prev_props = set(prev.get("scene_props", [])) if prev else set()
        curr_props = set(scene_prop_list)
        continuous_elev = ("hydraulic_lift_chair" in curr_props or "hydraulic_lift_chair" in prev_props or "golden_city" in (story.world_biome or ""))
        prev_l_elev = float(prev.get("lead_elev", raw_l_elev)) if (prev and continuous_elev) else raw_l_elev
        prev_p_elev = float(prev.get("partner_elev", raw_p_elev)) if (prev and continuous_elev) else raw_p_elev
        l_y0, l_y1, l_y2 = prev_l_elev, round((prev_l_elev + raw_l_elev) * 0.5, 2), raw_l_elev
        p_y0, p_y1, p_y2 = prev_p_elev, round((prev_p_elev + raw_p_elev) * 0.5, 2), raw_p_elev

        # Light anti-repetition guard: ONLY nudge camera angle if adjacent scene uses exact same shot AND elevation didn't change
        if prev and cam_style == prev.get("camera_shot_style") and abs(raw_p_elev - prev_p_elev) < 0.4:
            cam_idx = (self.CAMERA_ROTATION.index(cam_style) + 1) % len(self.CAMERA_ROTATION) if cam_style in self.CAMERA_ROTATION else (scene_number % len(self.CAMERA_ROTATION))
            cam_style = self.CAMERA_ROTATION[cam_idx]

        hist.append({
            "scene_number": scene_number,
            "camera_shot_style": cam_style,
            "spatial_pattern": spatial,
            "lead_action": lead_act,
            "lead_elev": raw_l_elev,
            "partner_elev": raw_p_elev,
            "scene_props": list(curr_props),
        })

        is_water = (story.world_biome == "waterpark_pool")
        show_hero_station = (scene_number >= n_main)
        hud_mode: Literal["none", "help_like_cta", "like_subscribe_cta", "finale_banner"] = (
            "help_like_cta"
            if (not is_outro_epilogue and lead_act == "plead_camera_help")
            else "none"
        )

        # Anchor Partner onto hydraulic_lift_chair if present OR elevated (`raw_p_elev > 0.25`)
        has_lift = ("hydraulic_lift_chair" in scene_prop_list) or (raw_p_elev > 0.25) or (prev_p_elev > 0.25)
        has_desk = ("computer_desk" in scene_prop_list)
        staging_mode = getattr(scene_obj, "scene_staging_mode", None) or "general"
        if staging_mode == "general":
            if "wooden_table" in scene_prop_list or (
                any(w in scene_text for w in ("table", "cake", "cracker", "cone", "cactus"))
                and any(w in scene_text for w in ("leans", "lean", "pushed", "smashed", "faces", "sees", "disgusted", "all over"))
            ):
                staging_mode = "table_challenge_front"
            elif any(p in scene_prop_list for p in ("musical_staircase", "colored_blocks", "pink_platform")) or any(
                w in scene_text for w in ("stairs", "staircase", "platform", "misses a step", "climb")
            ):
                staging_mode = "course_climb_progression"

        lead_tilt_override: Optional[float] = None
        lead_head_override: Optional[float] = None
        lead_look_override: Optional[Tuple[float, float, float]] = None

        if staging_mode == "table_challenge_front":
            # Focal character sits/stands directly BEHIND the foreground challenge table (`z = -0.32`),
            # facing `+Z` over the tabletop food/cactus (`(0.0, 0.78, 0.30)`) toward camera!
            lead_look_override = (0.0, 0.88, 1.85)
            is_slam = any(w in scene_text for w in ("pushed", "push", "slam", "smash", "smashes")) or (part_act == "push_or_block")
            is_disgusted_recoil = any(w in scene_text for w in ("disgusted", "all over", "recoil", "horrified")) or (lead_expr == "disgusted")
            if is_slam:
                l_p0, l_p1, l_p2 = (-0.04, 0.0, -0.32), (-0.04, 0.0, -0.26), (-0.04, 0.0, -0.34)
                p_p0, p_p1, p_p2 = (0.58, 0.0, -0.42), (0.30, 0.0, -0.38), (0.28, 0.0, -0.38)
                l_first_act = "interact_use_prop"
                p_first_act = "push_or_block"
                lead_tilt_override = 0.36
                lead_head_override = 0.22
            elif is_disgusted_recoil:
                l_p0, l_p1, l_p2 = (-0.04, 0.0, -0.34), (-0.04, 0.0, -0.44), (-0.04, 0.0, -0.46)
                p_p0, p_p1, p_p2 = (2.45, 0.0, -1.95), (2.45, 0.0, -1.95), (2.45, 0.0, -1.95)
                l_first_act = "recoil_surprise"
                p_first_act = "idle"
                lead_tilt_override = -0.10
                lead_head_override = -0.04
            else:
                # Leaning forward inspecting/facing crackers, ice cream cones, strawberry cake, or cactus on the table
                l_p0, l_p1, l_p2 = (-0.04, 0.0, -0.38), (-0.04, 0.0, -0.30), (-0.04, 0.0, -0.30)
                p_p0, p_p1, p_p2 = (2.45, 0.0, -1.95), (2.45, 0.0, -1.95), (2.45, 0.0, -1.95)
                l_first_act = "interact_use_prop" if lead_act in ("talk_explain", "listen_nod") else lead_act
                p_first_act = "idle"
                lead_tilt_override = 0.22
                lead_head_override = 0.14
        elif staging_mode == "course_climb_progression":
            has_plat = "pink_platform" in scene_prop_list
            is_climb = any(w in scene_text for w in ("climb", "runs up", "tries to climb", "step")) and not any(w in scene_text for w in ("falls", "fall", "pops", "lands"))
            is_fall = any(w in scene_text for w in ("misses", "falls", "fall", "pops"))
            if has_plat and not is_climb and not is_fall:
                l_p0, l_p1, l_p2 = (0.75, max(l_y0, 1.15), -0.15), (1.15, max(l_y1, 1.15), -0.15), (1.15, max(l_y2, 1.15), -0.15)
                p_p0, p_p1, p_p2 = (-1.45, 0.0, 0.35), (-1.45, 0.0, 0.35), (-1.45, 0.0, 0.35)
                l_first_act = "walk_casual" if "walk" in scene_text else lead_act
                p_first_act = "idle"
                lead_look_override = (0.65, 1.15, 2.5)
            elif is_climb:
                l_p0, l_p1, l_p2 = (-1.15, 0.18, -0.12), (-0.20, 0.72, -0.12), (0.65, 1.25, -0.12)
                p_p0, p_p1, p_p2 = (-1.75, 0.0, 0.45), (-1.65, 0.0, 0.45), (-1.65, 0.0, 0.45)
                l_first_act = "run_urgent" if lead_act == "run_urgent" else "walk_casual"
                p_first_act = "idle"
                lead_look_override = (1.6, 1.5, -0.10)
            elif is_fall:
                l_p0, l_p1, l_p2 = (0.35, 1.05, -0.10), (0.20, 0.55, 0.15), (0.05, 0.0, 0.35)
                p_p0, p_p1, p_p2 = (-1.55, 0.0, 0.35), (-1.55, 0.0, 0.35), (-1.55, 0.0, 0.35)
                l_first_act = "recoil_surprise"
                p_first_act = "idle"
                lead_look_override = (0.0, 0.85, 2.2)
            else:
                # Landing on musical step & dancing / jumping for joy
                step_y = 0.72 if "musical step" in scene_text else max(l_y1, 0.36)
                l_p0, l_p1, l_p2 = (-0.10, step_y, -0.10), (0.05, step_y, -0.10), (0.05, step_y, -0.10)
                p_p0, p_p1, p_p2 = (-1.55, 0.0, 0.35), (-1.45, 0.0, 0.35), (-1.45, 0.0, 0.35)
                l_first_act = lead_act
                p_first_act = "cheer_celebrate" if scene_number == n_total else "idle"
                lead_look_override = (0.05, step_y + 0.8, 2.4)
        elif has_lift:
            if scene_number == 1 and lead_act == "walk_casual":
                l_p0 = (-1.15, l_y0, 0.35)
                l_p1 = (-0.52, l_y1, 0.25)
                l_p2 = (-0.52, l_y2, 0.25)
                l_first_act = "walk_casual"
            else:
                l_p0 = (-0.65, l_y0, 0.25)
                l_p1 = (-0.60, l_y1, 0.25)
                l_p2 = (-0.60, l_y2, 0.25)
                l_first_act = lead_act
            p_p0 = (0.55, p_y0, 0.20)
            p_p1 = (0.55, p_y1, 0.20)
            p_p2 = (0.55, p_y2, 0.20)
            if raw_p_elev >= 0.5 and "hydraulic_lift_chair" in scene_prop_list:
                part_act = "sit_chair_or_bench"
                p_first_act = "sit_chair_or_bench"
            elif raw_p_elev >= 0.5 and "brick_wall" in scene_prop_list:
                part_act = "interact_use_prop"
                p_first_act = "interact_use_prop"
            else:
                p_first_act = part_act
        elif has_desk and (lead_act == "sit_chair_or_bench" or "caught" in scene_text or "playing" in scene_text):
            # Sit lead cleanly in 3/4 view in angled gaming chair (`computer_desk` at (-0.42, 0, -0.78), rotY=0.68), friend walks up on right!
            l_p0, l_p1, l_p2 = (-0.07, l_y0, -0.34), (-0.07, l_y1, -0.34), (-0.07, l_y2, -0.34)
            p_p0, p_p1, p_p2 = (0.98, p_y0, 0.42), (0.68, p_y1, 0.22), (0.68, p_y2, 0.22)
            l_first_act = lead_act
            p_first_act = "walk_casual" if part_act not in ("laugh_giggle", "sad_cry_slump") else part_act
        elif spatial == "left_to_right_travel":
            l_p0, l_p1, l_p2 = (-1.15, l_y0, 0.30), (0.0, l_y1, 0.30), (1.05, l_y2, 0.30)
            p_p0, p_p1, p_p2 = (-1.65, p_y0, -0.30), (-0.65, p_y1, -0.30), (0.45, p_y2, -0.30)
            l_first_act = "run_urgent" if lead_act == "run_urgent" else "walk_casual"
            p_first_act = "run_urgent" if lead_act == "run_urgent" else "walk_casual"
        elif spatial == "right_to_left_travel":
            l_p0, l_p1, l_p2 = (1.15, l_y0, 0.30), (0.0, l_y1, 0.30), (-1.05, l_y2, 0.30)
            p_p0, p_p1, p_p2 = (1.65, p_y0, -0.30), (0.65, p_y1, -0.30), (-0.45, p_y2, -0.30)
            l_first_act = "run_urgent" if lead_act == "run_urgent" else "walk_casual"
            p_first_act = "run_urgent" if lead_act == "run_urgent" else "walk_casual"
        elif spatial == "chase_pursuit":
            l_p0, l_p1, l_p2 = (-1.15, l_y0, 0.35), (0.15, l_y1, 0.25), (1.15, l_y2, 0.35)
            p_p0, p_p1, p_p2 = (-1.75, p_y0, 0.35), (-0.60, p_y1, 0.25), (0.55, p_y2, 0.35)
            l_first_act = "run_urgent"
            p_first_act = "run_urgent"
        elif spatial == "gather_around_prop":
            l_p0, l_p1, l_p2 = (-1.05, l_y0, 0.35), (-0.55, l_y1, -0.15), (-0.55, l_y2, -0.15)
            p_p0, p_p1, p_p2 = (1.05, p_y0, 0.35), (0.55, p_y1, -0.15), (0.55, p_y2, -0.15)
            l_first_act = "walk_casual"
            p_first_act = "walk_casual"
        elif spatial == "step_back_recoil":
            l_p0, l_p1, l_p2 = (-0.25, l_y0, 0.15), (-0.30, l_y1, 0.15), (-0.95, l_y2, 0.85)
            p_p0, p_p1, p_p2 = (0.75, p_y0, 0.15), (0.58, p_y1, 0.25), (0.58, p_y2, 0.25)
            l_first_act = "interact_use_prop"
            p_first_act = "point_discover"
        elif spatial == "walk_to_camera":
            l_p0, l_p1, l_p2 = (-0.45, l_y0, -0.45), (-0.45, l_y1, 1.35), (-0.45, l_y2, 1.35)
            p_p0, p_p1, p_p2 = (0.75, p_y0, -0.65), (0.65, p_y1, 0.65), (0.65, p_y2, 0.65)
            l_first_act = "walk_casual"
            p_first_act = "walk_casual"
        elif spatial == "side_by_side_walk":
            l_p0, l_p1, l_p2 = (-0.55, l_y0, -0.85), (-0.55, l_y1, 0.55), (-0.55, l_y2, 0.75)
            p_p0, p_p1, p_p2 = (0.55, p_y0, -0.85), (0.55, p_y1, 0.55), (0.55, p_y2, 0.75)
            l_first_act = "walk_casual"
            p_first_act = "walk_casual"
        elif spatial == "approach_center":
            l_p0, l_p1, l_p2 = (-1.55, l_y0, 0.45), (-0.55, l_y1, 0.30), (-0.55, l_y2, 0.30)
            p_p0, p_p1, p_p2 = (1.55, p_y0, 0.45), (0.55, p_y1, 0.30), (0.55, p_y2, 0.30)
            l_first_act = "walk_casual"
            p_first_act = "walk_casual"
        elif "hollow_tree_trunk" in scene_prop_list and any(w in scene_text for w in ("hide", "hiding", "peek", "tree")):
            # Frame Lead & Partner right alongside the hollow ancient oak tree!
            l_p0, l_p1, l_p2 = (-1.15, l_y0, 0.20), (-0.95, l_y1, 0.20), (-0.95, l_y2, 0.20)
            p_p0, p_p1, p_p2 = (-0.25, p_y0, 0.28), (-0.25, p_y1, 0.28), (-0.25, p_y2, 0.28)
            l_first_act = lead_act
            p_first_act = part_act
        else:
            # face_to_face_dialogue / stationary_focus
            l_p0, l_p1, l_p2 = (-0.60, l_y0, 0.25), (-0.55, l_y1, 0.25), (-0.55, l_y2, 0.25)
            p_p0, p_p1, p_p2 = (0.60, p_y0, 0.25), (0.55, p_y1, 0.25), (0.55, p_y2, 0.25)
            l_first_act = lead_act
            p_first_act = part_act

        # Enforce stationary coordinates when sitting/lying
        if lead_act in ("sit_chair_or_bench", "sit_floor_relax", "lie_down_exhausted"):
            l_p0 = (l_p1[0], l_y0, l_p1[2])
            l_p2 = (l_p1[0], l_y2, l_p1[2])
            l_first_act = lead_act
        if part_act in ("sit_chair_or_bench", "sit_floor_relax", "lie_down_exhausted") or has_lift:
            p_p0 = (p_p1[0], p_y0, p_p1[2])
            p_p2 = (p_p1[0], p_y2, p_p1[2])
            p_first_act = part_act

        if is_outro_epilogue and prev and "l_end_pos" in prev:
            l_p0 = l_p1 = l_p2 = prev["l_end_pos"]
            p_p0 = p_p1 = p_p2 = prev.get("p_end_pos", p_p2)
            l_first_act = lead_act
            p_first_act = "listen_nod"
            lead_look_override = prev.get("lead_look") or (l_p2[0], round(l_p2[1] + 0.92, 2), round(l_p2[2] + 2.45, 2))
            if staging_mode == "table_challenge_front":
                lead_tilt_override = 0.08
                lead_head_override = 0.06

        hist[-1]["l_end_pos"] = l_p2
        hist[-1]["p_end_pos"] = p_p2
        hist[-1]["lead_look"] = lead_look_override

        scene_lead_idx = 0
        scene_part_idx = 1 if len(roster.characters) > 1 else -1
        non_bird_indices = [i for i, c in enumerate(roster.characters) if c.role != "sky_bird"]
        if len(non_bird_indices) > 2 and not has_lift:
            mentions = []
            for i in non_bird_indices:
                cname = (roster.characters[i].name or "").strip().lower()
                if cname:
                    m = re.search(r"\b" + re.escape(cname) + r"\b", scene_text)
                    if m:
                        mentions.append((m.start(), i))
            mentions.sort(key=lambda x: x[0])
            ordered_ids = [i for _, i in mentions]
            if len(ordered_ids) >= 2:
                scene_lead_idx, scene_part_idx = ordered_ids[0], ordered_ids[1]
            elif len(ordered_ids) == 1:
                scene_lead_idx = ordered_ids[0]
                for i in non_bird_indices:
                    if i != scene_lead_idx:
                        scene_part_idx = i
                        break

        actors: List[ActorPlacementSpec] = []
        for idx, ch in enumerate(roster.characters):
            cid = ch.char_id

            # 1. SKY BIRD (only when acting as background ambient bird)
            if ch.role == "sky_bird" and idx not in (scene_lead_idx, scene_part_idx):
                b0 = (-3.6, 2.95, -2.1) if scene_number % 2 == 0 else (3.6, 2.95, -1.7)
                b1 = (3.6, 3.05, -1.7) if scene_number % 2 == 0 else (-3.6, 3.05, -2.1)
                actors.append(
                    ActorPlacementSpec(
                        char_id=cid,
                        start_pos=b0,
                        end_pos=b1,
                        action="fly",
                        collision_radius=0.0,
                        phases=[
                            ActorPhaseSpec(
                                start_ratio=0.0,
                                end_ratio=1.0,
                                from_pos=b0,
                                to_pos=b1,
                                anim_mode="fly",
                                action="fly",
                            )
                        ],
                    )
                )
                continue

            # 2. PETS & CREATURES (only when acting as background animal, zero jumping!)
            if ch.role in ("pet_animal", "wild_creature") and idx not in (scene_lead_idx, scene_part_idx):
                if ch.role == "pet_animal":
                    pa = (-2.15, 0.0, 2.20) if scene_number % 2 == 1 else (2.15, 0.0, 2.20)
                    pb = (0.65, 0.0, 2.20) if scene_number % 2 == 1 else (-0.65, 0.0, 2.20)
                else:
                    pa = (2.25, 0.0, -2.85) if scene_number % 2 == 1 else (-2.25, 0.0, -2.85)
                    pb = (-0.75, 0.0, -2.85) if scene_number % 2 == 1 else (0.75, 0.0, -2.85)

                actors.append(
                    ActorPlacementSpec(
                        char_id=cid,
                        start_pos=pa,
                        end_pos=pb,
                        action="pet_walk",
                        collision_radius=0.42,
                        phases=[
                            ActorPhaseSpec(
                                start_ratio=0.0,
                                end_ratio=0.65,
                                from_pos=pa,
                                to_pos=pb,
                                anim_mode="pet_walk",
                                action="pet_walk",
                            ),
                            ActorPhaseSpec(
                                start_ratio=0.65,
                                end_ratio=1.0,
                                from_pos=pb,
                                to_pos=pb,
                                anim_mode="idle",
                                action="listen_nod",
                                look_at=(0.0, 0.8, 0.35),
                            ),
                        ],
                    )
                )
                continue

            # 3. ACTIVE SCENE LEAD
            if idx == scene_lead_idx:
                fx_trig: Optional[FxTriggerType] = None
                scene_prop_list = getattr(scene_obj, "scene_props", None) or []
                if lead_act in ("cheer_celebrate", "dance_groove") and scene_number == n_total:
                    fx_trig = "confetti_burst"
                elif is_water and lead_act == "jump_obstacle_or_joy":
                    fx_trig = "water_splash"
                elif "magic_portal" in scene_prop_list:
                    fx_trig = "magic_spawn_ring"
                elif lead_act in ("recoil_surprise", "run_urgent") and (scene_number % 3 == 1):
                    fx_trig = "dust_puff"

                l_ph0 = self._build_phase_from_kb(
                    start_ratio=0.0,
                    end_ratio=0.45,
                    from_pos=l_p0,
                    to_pos=l_p1,
                    action_key=l_first_act,
                    expression=lead_expr,
                    look_at=lead_look_override or ((-0.42, 0.0, -0.78) if has_desk else p_p1),
                    override_emote="?" if is_outro_epilogue else None,
                    fx_trigger="magic_spawn_ring" if is_outro_epilogue else None,
                )
                l_ph1 = self._build_phase_from_kb(
                    start_ratio=0.45,
                    end_ratio=1.0,
                    from_pos=l_p1,
                    to_pos=l_p2,
                    action_key=lead_act,
                    expression=lead_expr,
                    look_at=lead_look_override or ((l_p2[0], 1.0, 4.5) if spatial == "walk_to_camera" else p_p2),
                    override_emote="?" if is_outro_epilogue else None,
                    fx_trigger=fx_trig,
                )
                if lead_tilt_override is not None:
                    l_ph0.spine_tilt_x = round(lead_tilt_override * 0.45, 3)
                    l_ph1.spine_tilt_x = lead_tilt_override
                if lead_head_override is not None:
                    l_ph0.head_pitch = round(lead_head_override * 0.45, 3)
                    l_ph1.head_pitch = lead_head_override
                l_phases = [l_ph0, l_ph1]

                lead_speaks = True if is_outro_epilogue else (
                    (
                        staging_mode not in ("table_challenge_front", "course_climb_progression")
                        and lead_act in ("talk_explain", "plead_camera_help", "laugh_giggle", "cheer_celebrate")
                    ) or (lead_act in ("talk_explain", "plead_camera_help"))
                )
                if not is_outro_epilogue and staging_mode == "table_challenge_front" and part_act == "push_or_block":
                    lead_speaks = False

                actors.append(
                    ActorPlacementSpec(
                        char_id=cid,
                        start_pos=l_p0,
                        end_pos=l_p2,
                        look_at_target=lead_look_override or p_p2,
                        action=lead_act,
                        expression=lead_expr,
                        is_speaking=lead_speaks,
                        collision_radius=0.44,
                        phases=l_phases,
                    )
                )
                continue

            # 4. ACTIVE SCENE PARTNER
            if idx == scene_part_idx:
                p_phases = [
                    self._build_phase_from_kb(
                        start_ratio=0.0,
                        end_ratio=0.45,
                        from_pos=p_p0,
                        to_pos=p_p1,
                        action_key=p_first_act,
                        expression=part_expr,
                        look_at=l_p1,
                    ),
                    self._build_phase_from_kb(
                        start_ratio=0.45,
                        end_ratio=1.0,
                        from_pos=p_p1,
                        to_pos=p_p2,
                        action_key=part_act,
                        expression=part_expr,
                        look_at=l_p2,
                    ),
                ]
                part_speaks = part_act in ("talk_explain", "plead_camera_help", "laugh_giggle", "cheer_celebrate")
                actors.append(
                    ActorPlacementSpec(
                        char_id=cid,
                        start_pos=p_p0,
                        end_pos=p_p2,
                        look_at_target=l_p2,
                        action=part_act,
                        expression=part_expr,
                        is_speaking=part_speaks,
                        collision_radius=0.42,
                        phases=p_phases,
                    )
                )
                continue

            # 5. RIVAL / COMPANIONS / SUPPORTING CAST (Background spectators stepped off center lane!)
            slot = idx - 2 if idx >= 2 else idx
            ring_coords = (
                [(-3.4, -2.5), (3.4, -2.5), (-3.8, -2.6), (3.8, -2.6)]
                if staging_mode == "table_challenge_front"
                else [
                    (-2.35, -1.65),
                    (2.35, -1.65),
                    (-2.95, -2.35),
                    (-0.95, -2.45),
                    (0.95, -2.45),
                    (2.95, -2.35),
                ]
            )
            bx, bz = ring_coords[slot % len(ring_coords)]
            walk_dx = 0.55 if (slot + scene_number) % 2 == 0 else -0.55
            bx_end = round(bx + walk_dx, 2)

            support_acts = ["listen_nod", "talk_explain", "point_discover", "sit_floor_relax", "cheer_celebrate"]
            s_act = "cheer_celebrate" if scene_number == n_total else support_acts[(slot + scene_number) % len(support_acts)]
            s_expr: ExpressionType = "excited" if scene_number == n_total else "happy"

            c_phases = [
                self._build_phase_from_kb(
                    start_ratio=0.0,
                    end_ratio=0.48,
                    from_pos=(bx, 0.0, bz),
                    to_pos=(bx_end, 0.0, bz) if s_act != "sit_floor_relax" else (bx, 0.0, bz),
                    action_key="walk_casual" if s_act != "sit_floor_relax" else "sit_floor_relax",
                    expression=s_expr,
                    look_at=l_p1,
                ),
                self._build_phase_from_kb(
                    start_ratio=0.48,
                    end_ratio=1.0,
                    from_pos=(bx_end, 0.0, bz) if s_act != "sit_floor_relax" else (bx, 0.0, bz),
                    to_pos=(bx_end, 0.0, bz) if s_act != "sit_floor_relax" else (bx, 0.0, bz),
                    action_key=s_act,
                    expression=s_expr,
                    look_at=l_p2,
                ),
            ]
            actors.append(
                ActorPlacementSpec(
                    char_id=cid,
                    start_pos=(bx, 0.0, bz),
                    end_pos=(bx_end, 0.0, bz),
                    look_at_target=l_p2,
                    action=s_act,
                    expression=s_expr,
                    collision_radius=0.38,
                    phases=c_phases,
                )
            )

        # --- 360-DEGREE CINEMATIC CAMERA ENGINE (tracks actual start -> mid -> end actor coordinates in 9:16 frame!) ---
        if has_lift and prev_p_elev >= 4.0 and raw_p_elev == 0.0:
            tgt0 = (0.0, 1.25, 0.22)
            tgt1 = (0.0, 0.80, 0.22)
            tgt2 = (0.0, 0.35, 0.22)
            fx0, fy0, fz0 = tgt0
            fx1, fy1, fz1 = tgt1
            fx2, fy2, fz2 = tgt2
        elif focus_char == "partner" or raw_p_elev >= 2.0:
            tgt0, tgt1, tgt2 = p_p0, p_p1, p_p2
            fx0, fy0, fz0 = p_p0
            fx1, fy1, fz1 = p_p1
            fx2, fy2, fz2 = p_p2
        elif focus_char == "lead":
            tgt0, tgt1, tgt2 = l_p0, l_p1, l_p2
            fx0, fy0, fz0 = l_p0
            fx1, fy1, fz1 = l_p1
            fx2, fy2, fz2 = l_p2
        else:
            tgt0 = ((l_p0[0] + p_p0[0]) * 0.5, (l_p0[1] + p_p0[1]) * 0.5, (l_p0[2] + p_p0[2]) * 0.5)
            tgt1 = ((l_p1[0] + p_p1[0]) * 0.5, (l_p1[1] + p_p1[1]) * 0.5, (l_p1[2] + p_p1[2]) * 0.5)
            tgt2 = ((l_p2[0] + p_p2[0]) * 0.5, (l_p2[1] + p_p2[1]) * 0.5, (l_p2[2] + p_p2[2]) * 0.5)
            fx0, fy0, fz0 = tgt0
            fx1, fy1, fz1 = tgt1
            fx2, fy2, fz2 = tgt2

        mid_x0, mid_y0, mid_z0 = round(tgt0[0], 2), round(tgt0[1] + 0.88, 2), round(tgt0[2], 2)
        mid_x1, mid_y1, mid_z1 = round(tgt1[0], 2), round(tgt1[1] + 0.88, 2), round(tgt1[2], 2)
        mid_x2, mid_y2, mid_z2 = round(tgt2[0], 2), round(tgt2[1] + 0.88, 2), round(tgt2[2], 2)
        side_sign = 1.0 if scene_number % 2 == 1 else -1.0

        if staging_mode == "table_challenge_front":
            # Crisp front portrait framing: foreground table + food/cake/cactus + unobstructed character face & upper torso!
            c1_s = (round(0.26 * side_sign, 2), 1.56, 2.26)
            c1_e = (round(-0.18 * side_sign, 2), 1.52, 2.16)
            look0 = (0.0, 0.96, 0.08)
            look1 = (0.0, 0.95, 0.10)
            fov1, fov2 = 47.0, 44.0
            c2_angle = side_sign * 0.20
            c2_rad, c2_h = 2.12, 1.50
            mid_x1, mid_y1, mid_z1 = 0.0, 0.96, 0.08
            mid_x2, mid_y2, mid_z2 = 0.0, 0.96, 0.08
            fx1, fy1, fz1 = 0.0, 0.04, 0.05
            fx2, fy2, fz2 = 0.0, 0.04, 0.05
        elif staging_mode == "course_climb_progression":
            c1_s = (round(mid_x0 + 0.55 * side_sign, 2), round(mid_y0 + 1.15, 2), round(mid_z0 + 4.35, 2))
            c1_e = (round(mid_x1 + 0.85 * side_sign, 2), round(mid_y1 + 1.05, 2), round(mid_z1 + 4.05, 2))
            look0 = (round(mid_x0 * 0.7, 2), round(mid_y0, 2), -0.10)
            look1 = (round(mid_x1 * 0.7, 2), round(mid_y1, 2), -0.10)
            fov1, fov2 = 54.0, 50.0
            c2_angle = side_sign * 0.42
            c2_rad, c2_h = 4.15, 1.85
        elif cam_style == "close_up_reaction":
            if focus_char == "both":
                # Keep BOTH actors safely inside 9:16 portrait crop during close-up reactions
                c1_s = (round(mid_x0 + side_sign * 0.85, 2), round(mid_y0 + 0.45, 2), round(mid_z0 + 3.45, 2))
                c1_e = (round(mid_x1 - side_sign * 0.65, 2), round(mid_y1 + 0.42, 2), round(mid_z1 + 3.25, 2))
                look0 = (mid_x0, round(mid_y0 + 0.08, 2), mid_z0)
                look1 = (mid_x1, round(mid_y1 + 0.08, 2), mid_z1)
                fov1, fov2 = 52.0, 48.0
                c2_angle = side_sign * 0.52
                c2_rad, c2_h = 3.55, 1.38
            else:
                c1_s = (round(fx0 + side_sign * 0.65, 2), round(fy0 + 1.32, 2), round(fz0 + 2.55, 2))
                c1_e = (round(fx1 - side_sign * 0.45, 2), round(fy1 + 1.28, 2), round(fz1 + 2.45, 2))
                look0 = (round(fx0, 2), round(fy0 + 0.96, 2), round(fz0, 2))
                look1 = (round(fx1, 2), round(fy1 + 0.96, 2), round(fz1, 2))
                fov1, fov2 = 46.0, 44.0
                c2_angle = side_sign * 0.58
                c2_rad, c2_h = 2.95, 1.32
        elif cam_style == "wide_establishing":
            c1_s = (round(mid_x0 - 1.95 * side_sign, 2), round(mid_y0 + 1.75, 2), round(mid_z0 + 5.65, 2))
            c1_e = (round(mid_x1 + 1.25 * side_sign, 2), round(mid_y1 + 1.45, 2), round(mid_z1 + 5.15, 2))
            look0 = (mid_x0, mid_y0, round(mid_z0 - 0.35, 2))
            look1 = (mid_x1, mid_y1, round(mid_z1 - 0.35, 2))
            fov1, fov2 = 58.0, 52.0
            c2_angle = -side_sign * 0.55
            c2_rad, c2_h = 4.85, 1.65
        elif cam_style == "high_angle_overview":
            c1_s = (round(mid_x0 + 1.85 * side_sign, 2), round(mid_y0 + 3.15, 2), round(mid_z0 + 4.15, 2))
            c1_e = (round(mid_x1 - 1.25 * side_sign, 2), round(mid_y1 + 2.65, 2), round(mid_z1 + 3.85, 2))
            look0 = (mid_x0, round(mid_y0 * 0.90, 2), round(mid_z0 - 0.20, 2))
            look1 = (mid_x1, round(mid_y1 * 0.92, 2), round(mid_z1 - 0.20, 2))
            fov1, fov2 = 55.0, 50.0
            c2_angle = side_sign * 0.58
            c2_rad, c2_h = 4.35, 2.05
        elif cam_style == "low_angle_hero":
            c1_s = (round(mid_x0 - 1.15 * side_sign, 2), round(max(0.45, mid_y0 - 0.45), 2), round(mid_z0 + 4.15, 2))
            c1_e = (round(mid_x1 + 1.05 * side_sign, 2), round(max(0.55, mid_y1 - 0.35), 2), round(mid_z1 + 3.85, 2))
            look0 = (mid_x0, round(mid_y0 + 0.35, 2), mid_z0)
            look1 = (mid_x1, round(mid_y1 + 0.42, 2), mid_z1)
            fov1, fov2 = 54.0, 50.0
            c2_angle = -side_sign * 0.52
            c2_rad, c2_h = 3.95, 0.88
        elif cam_style == "over_shoulder":
            c1_s = (round(mid_x0 + 2.15 * side_sign, 2), round(mid_y0 + 0.55, 2), round(mid_z0 + 2.85, 2))
            c1_e = (round(mid_x1 + 1.75 * side_sign, 2), round(mid_y1 + 0.48, 2), round(mid_z1 + 3.05, 2))
            look0 = (mid_x0, mid_y0, mid_z0)
            look1 = (mid_x1, mid_y1, mid_z1)
            fov1, fov2 = 50.0, 46.0
            c2_angle = -side_sign * 0.68
            c2_rad, c2_h = 3.75, 1.45
        elif cam_style == "tracking_side":
            c1_s = (round(mid_x0 - 1.15, 2), round(mid_y0 + 0.62, 2), round(mid_z0 + 4.35, 2))
            c1_e = (round(mid_x1 + 1.05, 2), round(mid_y1 + 0.55, 2), round(mid_z1 + 4.25, 2))
            look0 = (mid_x0, mid_y0, mid_z0)
            look1 = (mid_x1, mid_y1, mid_z1)
            fov1, fov2 = 54.0, 50.0
            c2_angle = side_sign * 0.62
            c2_rad, c2_h = 4.25, 1.55
        else:
            # medium_two_shot
            c1_s = (round(mid_x0 - 1.25 * side_sign, 2), round(mid_y0 + 0.72, 2), round(mid_z0 + 4.45, 2))
            c1_e = (round(mid_x1 + 1.05 * side_sign, 2), round(mid_y1 + 0.65, 2), round(mid_z1 + 4.15, 2))
            look0 = (mid_x0, mid_y0, mid_z0)
            look1 = (mid_x1, mid_y1, mid_z1)
            fov1, fov2 = 52.0, 48.0
            c2_angle = -side_sign * 0.58
            c2_rad, c2_h = 3.95, 1.45

        c2_s = (round(mid_x1 + math.sin(c2_angle) * c2_rad, 2), round(mid_y1 - 0.88 + c2_h, 2), round(mid_z1 + math.cos(c2_angle) * c2_rad, 2))
        c2_e = (round(mid_x2 + math.sin(c2_angle * 0.45) * (c2_rad - 0.35), 2), round(mid_y2 - 0.88 + c2_h * 0.94, 2), round(mid_z2 + math.cos(c2_angle * 0.45) * (c2_rad - 0.35), 2))
        look_c2_s = (round(fx1, 2), round(fy1 + 0.95, 2), round(fz1, 2)) if focus_char != "both" else (mid_x1, mid_y1, mid_z1)
        look_c2_e = (round(fx2, 2), round(fy2 + 0.95, 2), round(fz2, 2)) if focus_char != "both" else (mid_x2, mid_y2, mid_z2)

        is_cliffhanger_finale = is_outro_epilogue
        styles_pool = ["portal_vortex_zoom", "iris_freeze_question", "shockwave_spark_spin", "shatter_flash_glint"]
        resolved_outro = outro_vfx_style if outro_vfx_style in styles_pool else styles_pool[(scene_number + len(narration)) % len(styles_pool)]
        resolved_badge = cliffhanger_badge_text.strip()
        if is_cliffhanger_finale:
            if not resolved_badge:
                words = [w for w in re.sub(r"[^\w\s]", "", narration).split() if len(w) > 2]
                resolved_badge = ("WHAT HAPPENS TO " + words[-1].upper() + "?!") if words else "WHAT HAPPENS NEXT?!"
            # Seamless 1-2s continuous dramatic dolly push-in keeping focal character centered above subtitles & badge
            out_look = (0.0, 0.84, 0.08) if staging_mode == "table_challenge_front" else (round(fx2, 2), round(fy2 + 0.76, 2), round(fz2, 2))
            if staging_mode == "table_challenge_front":
                c_out0 = (round(0.20 * side_sign, 2), 1.46, 2.14)
                c_out1 = (round(0.06 * side_sign, 2), 1.38, 1.98)
                c_out2 = (round(-0.08 * side_sign, 2), 1.32, 1.82)
            else:
                c_out0 = (round(out_look[0] + 0.30 * side_sign, 2), round(out_look[1] + 0.22, 2), round(out_look[2] + 2.95, 2))
                c_out1 = (round(out_look[0] + 0.08 * side_sign, 2), round(out_look[1] + 0.16, 2), round(out_look[2] + 2.58, 2))
                c_out2 = (round(out_look[0] - 0.12 * side_sign, 2), round(out_look[1] + 0.12, 2), round(out_look[2] + 2.24, 2))
            camera_shots = [
                CameraShotSpec(
                    shot_index=0,
                    start_ratio=0.0,
                    end_ratio=0.50,
                    cam_start=c_out0,
                    cam_end=c_out1,
                    look_start=out_look,
                    look_end=out_look,
                    fov_deg=46.0,
                ),
                CameraShotSpec(
                    shot_index=1,
                    start_ratio=0.50,
                    end_ratio=1.0,
                    cam_start=c_out1,
                    cam_end=c_out2,
                    look_start=out_look,
                    look_end=out_look,
                    fov_deg=39.0,
                ),
            ]
        else:
            camera_shots = [
                CameraShotSpec(
                    shot_index=0,
                    start_ratio=0.0,
                    end_ratio=0.52,
                    cam_start=c1_s,
                    cam_end=c1_e,
                    look_start=look0,
                    look_end=look1,
                    fov_deg=fov1,
                ),
                CameraShotSpec(
                    shot_index=1,
                    start_ratio=0.52,
                    end_ratio=1.0,
                    cam_start=c2_s,
                    cam_end=c2_e,
                    look_start=look_c2_s,
                    look_end=look_c2_e,
                    fov_deg=fov2,
                ),
            ]

        return SceneDirectingSpec(
            scene_number=scene_number,
            duration=round(duration, 2),
            narration=narration,
            scene_template=f"{spatial}__{lead_act}",
            beat_type=beat_type,
            emotional_tone=tone,
            show_hero_station=show_hero_station,
            hud_mode=hud_mode,
            is_cliffhanger_finale=is_cliffhanger_finale,
            cliffhanger_badge_text=resolved_badge if is_cliffhanger_finale else "",
            outro_vfx_style=resolved_outro if is_cliffhanger_finale else "portal_vortex_zoom",
            actors=actors,
            camera_shots=camera_shots,
        )
