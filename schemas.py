"""
Pydantic schemas for the Multi-Agent YouTube Shorts Cloner (`schemas.py`).
Supports exact scene-by-scene reference video mirroring (matching scene count, narration/dialogue,
props, grounded physical actions, facial expressions, spatial blocking, camera framing, and SFX).
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


WorldBiomeLiteral = Literal[
    "golden_city",
    "lush_forest",
    "indoor_room",
    "stone_maze",
    "waterpark_pool",
    "school_courtyard",
    "city_playground",
    "magic_carnival",
    "jungle_safari",
    "futuristic_lab",
    "beach_island",
    "cozy_village",
]

ScenePropLiteral = Literal[
    "skyscraper_city",
    "hydraulic_lift_chair",
    "flying_airplane",
    "hollow_tree_trunk",
    "jungle_giant_leaf",
    "balloon_bundle_red",
    "sausage_prop",
    "giant_cockroach",
    "cooking_pot",
    "cleaning_broom",
    "computer_desk",
    "stone_maze_walls",
    "laser_beam",
    "hero_shield",
    "angry_bull",
    "camouflage_bush",
    "strength_orb",
    "ocean_water_plane",
    "inflatable_pool",
    "water_slide",
    "cage_trap",
    "mystery_table",
    "treasure_chest",
    "park_bench",
    "race_finish_arch",
    "magic_portal",
    "control_pedestal",
    "gift_box_pile",
    "obstacle_hurdle",
    "campfire_ring",
    "stage_podium",
    "bridge_span",
    "book_and_coin_stacks",
    "color_archways",
    "color_cubes",
    "trophy_display",
    "bouncer_pad",
    "water_boat",
    "moving_car",
    "beach_umbrella",
    "balloon_bunch",
    "skateboard",
    "sofa_couch",
]

CharacterArchetypeLiteral = Literal[
    "small_cute_creature",
    "large_goofy_creature",
    "tiny_prank_critter",
    "suited_executive",
    "sporty_athlete",
    "hero_boy",
    "hero_girl",
    "villain_boss",
    "robot_assistant",
    "elder_mentor",
    "pet_dog",
]

PhysicalActionLiteral = Literal[
    "walk_casual",
    "run_urgent",
    "sneak_tiptoe",
    "talk_explain",
    "listen_nod",
    "shake_head_no",
    "interact_use_prop",
    "pick_up_inspect",
    "give_or_share",
    "push_or_block",
    "recoil_surprise",
    "sit_floor_relax",
    "sit_chair_or_bench",
    "lie_down_exhausted",
    "sad_cry_slump",
    "plead_camera_help",
    "point_discover",
    "laugh_giggle",
    "cheer_celebrate",
    "dance_groove",
    "jump_obstacle_or_joy",
]

FacialExpressionLiteral = Literal[
    "happy",
    "excited",
    "curious",
    "surprised",
    "shocked",
    "sad",
    "crying",
    "angry",
    "determined",
    "embarrassed",
    "proud",
    "laughing",
]

SpatialPatternLiteral = Literal[
    "approach_center",
    "left_to_right_travel",
    "right_to_left_travel",
    "face_to_face_dialogue",
    "chase_pursuit",
    "gather_around_prop",
    "step_back_recoil",
    "walk_to_camera",
    "side_by_side_walk",
    "stationary_focus",
]

CameraShotStyleLiteral = Literal[
    "wide_establishing",
    "medium_two_shot",
    "close_up_reaction",
    "over_shoulder",
    "tracking_side",
    "low_angle_hero",
    "high_angle_overview",
]

SfxCueLiteral = Literal[
    "whoosh",
    "pop",
    "beep",
    "impact",
    "splash",
    "boing",
    "magic_chime",
    "cheer_fanfare",
    "sad_trombone",
    "gasp_shock",
    "footsteps",
    "laugh_giggle",
    "none",
]


class Scene(BaseModel):
    """Individual scene storyboard and narration segment mirroring a scene from the reference video."""
    scene_number: int = Field(
        ...,
        description="Sequential index of the scene starting from 1"
    )
    narration: str = Field(
        ...,
        description="Spoken narration/dialogue matching this scene of the reference video (with swapped character names)."
    )
    duration_target: float = Field(
        default=3.2,
        description="Target duration in seconds matching the reference scene duration."
    )
    ref_scene_action_summary: str = Field(
        default="",
        description="Exact description of what physically happens in this scene of the reference video."
    )
    world_biome: Optional[WorldBiomeLiteral] = Field(
        default=None,
        description="3D environment setting matching the reference video."
    )
    scene_props: List[str] = Field(
        default_factory=list,
        description="Specific 3D props/objects visible or interacted with in this scene (prefer canonical IDs like giant_cockroach, cooking_pot, cleaning_broom, computer_desk, stone_maze_walls, laser_beam, hero_shield, angry_bull, camouflage_bush, strength_orb, balloon_bundle_red, hollow_tree_trunk, etc., or clear snake_case names)."
    )
    lead_action: str = Field(
        default="talk_explain",
        description="Grounded physical action of lead character (e.g. walk_casual, run_urgent, sneak_tiptoe, talk_explain, listen_nod, shake_head_no, interact_use_prop, pick_up_inspect, recoil_surprise, sit_chair_or_bench, cheer_celebrate, or a clear snake_case action)."
    )
    lead_expression: str = Field(
        default="happy",
        description="Facial expression of lead character matching the reference frame (e.g. happy, excited, curious, surprised, shocked, sad, crying, angry, determined, smirking, winking, chewing, sleepy_yawn, panicked, disgusted)."
    )
    partner_action: str = Field(
        default="listen_nod",
        description="Grounded physical action of partner character in this scene."
    )
    partner_expression: str = Field(
        default="curious",
        description="Facial expression of partner character matching the reference frame."
    )
    spatial_pattern: SpatialPatternLiteral = Field(
        default="face_to_face_dialogue",
        description="Spatial blocking/movement pattern of the characters in this scene."
    )
    camera_shot_style: CameraShotStyleLiteral = Field(
        default="medium_two_shot",
        description="3D camera framing style matching this scene of the reference video."
    )
    scene_staging_mode: Literal[
        "general",
        "table_challenge_front",
        "course_climb_progression",
        "chase_corridor",
        "elevated_vantage",
    ] = Field(
        default="general",
        description="Structural 3D scene staging layout matching the reference composition: 'table_challenge_front' (characters behind foreground dining/challenge table facing food/objects on table toward camera), 'course_climb_progression' (character climbing stairs/platforms/blocks along course), 'elevated_vantage' (on wall/lift/tree), 'chase_corridor', or 'general'."
    )
    focus_character: Literal["both", "lead", "partner"] = Field(
        default="both",
        description="Which character(s) the camera frames in this scene ('lead', 'partner', or 'both')."
    )
    lead_elevation_m: float = Field(
        default=0.0,
        description="Vertical elevation of lead character in meters (0.0 on ground, 2.0-12.0 when rising up pole/sky)."
    )
    partner_elevation_m: float = Field(
        default=0.0,
        description="Vertical elevation of partner character in meters (0.0 on ground, 2.0-12.0 when rising up pole/sky)."
    )
    image_prompt: str = Field(
        default="",
        description="Detailed visual description of the scene."
    )
    archival_search_query: str = Field(
        default="",
        description="2-6 word search query for matching 3D animation clip."
    )
    source_video_index: int = Field(
        default=1,
        description="Index (1-based) of the reference video this scene mirrors (1 for Clip 1, 2 for Clip 2)."
    )
    source_start_sec: float = Field(
        default=0.0,
        description="Start timestamp in seconds within the reference video for this scene."
    )
    source_end_sec: float = Field(
        default=3.0,
        description="End timestamp in seconds within the reference video for this scene."
    )
    secondary_start_sec: float = Field(
        default=1.5,
        description="Mid-scene cut timestamp in seconds within the reference video."
    )
    camera_motion: Literal["zoom_in_fast", "zoom_in_slow", "pan_right", "pan_left", "static"] = Field(
        default="zoom_in_slow",
        description="Camera motion filter: zoom_in_fast, zoom_in_slow, pan_right, pan_left, static"
    )
    sfx_cue: Optional[SfxCueLiteral] = Field(
        default="whoosh",
        description="Sound effect cue matching the action in this scene."
    )
    subtitle_emphasis_words: List[str] = Field(
        default_factory=list,
        description="Keywords in narration to emphasize with bold highlight styling"
    )
    is_outro_epilogue: bool = Field(
        default=False,
        description="True ONLY for the dedicated 1-2 second closing cliffhanger segment appended AFTER all main story scenes."
    )


class CastMemberSchema(BaseModel):
    """Exact character slot extracted from the reference video and mapped to a replacement 3D character."""
    name: str = Field(..., description="New swapped character name (e.g., Leo, Milo, Rex, Coco)")
    archetype: CharacterArchetypeLiteral = Field(
        ...,
        description="Visual character archetype matching the role/species in the reference video"
    )
    role: Literal["protagonist", "deuteragonist", "companion"] = Field(
        default="protagonist",
        description="Narrative role in the clip"
    )


class VideoScript(BaseModel):
    """Complete script and scene breakdown mirroring a trending reference Short with new characters."""
    clip_index: int = Field(
        ...,
        description="Index of this clip (1 for Reference Video #1, 2 for Reference Video #2)"
    )
    title: str = Field(
        ...,
        description="Click-worthy vertical video title with 2-3 viral hashtags (e.g. #shorts)"
    )
    hook_text: str = Field(
        ...,
        description="The opening 0-3 second hook line"
    )
    target_niche: str = Field(
        ...,
        description="Niche or topic category for this script"
    )
    language: str = Field(
        default="en",
        description="Spoken language code"
    )
    cast_roles: List[CastMemberSchema] = Field(
        default_factory=list,
        description="Exact list of 2 to 4 story characters present in the reference video (do NOT invent extra characters)"
    )
    has_background_crowd: bool = Field(
        default=False,
        description="True ONLY if the reference video literally has a large crowd/audience of background bystanders"
    )
    scenes: List[Scene] = Field(
        ...,
        description="Ordered list of scenes mirroring every scene of the corresponding reference video"
    )
    estimated_duration: float = Field(
        default=30.0,
        description="Estimated total duration in seconds"
    )
    youtube_seo_title: str = Field(
        default="",
        description="Catchy, high-CTR YouTube title (< 85 chars) with curiosity hook, emoji & #shorts"
    )
    thumbnail_headline: str = Field(
        default="",
        description="Bold 2 to 4 word ALL-CAPS cover thumbnail headline (e.g. 'PRICKLY CACTUS PRANK!', 'WHO CLIMBS IT?!')"
    )
    youtube_description: str = Field(
        default="",
        description="Engaging 2-3 sentence YouTube Shorts description inviting viewer comments, likes & subscribes with 3-5 hashtags."
    )
    trending_tags: List[str] = Field(
        default_factory=list,
        description="12 to 16 high-volume trending & topic-specific YouTube search tags (lowercase, no # symbol, e.g. '3d animation', 'funny shorts', 'cartoon prank')."
    )
    cliffhanger_hook: str = Field(
        default="",
        description="Short 3 to 6 word creative curiosity/cliffhanger sentence spoken in the dedicated 1-2s closing epilogue segment AFTER the main scenes (e.g. 'What should Leo do next?!', 'Wait for Toby Part Two!') - MUST vary creatively across clips!"
    )
    cliffhanger_badge_text: str = Field(
        default="",
        description="Punchy 3-6 word ALL-CAPS outro curiosity teaser banner tailored to this story (e.g. 'WHAT HAPPENS NEXT?!', 'WHAT SHOULD COCO DO?!')."
    )
    outro_vfx_style: Literal[
        "portal_vortex_zoom",
        "iris_freeze_question",
        "shockwave_spark_spin",
        "shatter_flash_glint",
    ] = Field(
        default="portal_vortex_zoom",
        description="Distinct visual closing VFX animation style for the final cliffhanger scene."
    )


class ViralBlueprint(BaseModel):
    """Deconstructed viral mechanics from the reference videos."""
    concept_formula: str = Field(
        default="",
        description="Scene-by-scene structural breakdown of the reference videos."
    )
    hook_strategy: str = Field(
        ...,
        description="Breakdown of the opening 3 seconds"
    )
    scene_cut_frequency_seconds: float = Field(
        default=2.5,
        description="Average cut speed in seconds between visual transitions"
    )
    pacing_and_rhythm: str = Field(
        ...,
        description="Cadence and rhythm description"
    )
    visual_style: str = Field(
        ...,
        description="Visual aesthetic"
    )
    narrative_arc: str = Field(
        ...,
        description="Storytelling structure"
    )
    retention_tactics: List[str] = Field(
        default_factory=list,
        description="Key retention tactics identified"
    )


class ProductionBatch(BaseModel):
    """Full production plan containing reference analysis and 2 mirrored scripts."""
    reference_title: Optional[str] = Field(
        default=None,
        description="Title of original reference YouTube Short"
    )
    reference_duration_seconds: Optional[float] = Field(
        default=None,
        description="Duration of the reference video in seconds"
    )
    viral_blueprint: ViralBlueprint = Field(
        ...,
        description="Extracted viral blueprint and structural parameters"
    )
    generated_scripts: List[VideoScript] = Field(
        ...,
        description="Scripts mirroring Reference Video #1 and Reference Video #2 scene-by-scene with replaced characters"
    )
