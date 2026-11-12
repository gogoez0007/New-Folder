"""
Core 3: Dynamic Background Story, Biome & 27-Prop 3D World Engine (`core/background_story_core.py`).

Deconstructs any trending reference video or script into a complete, non-hardcoded
`BackgroundStorySpec` describing:
- The 3D world biome (`waterpark_pool`, `school_courtyard`, `magic_carnival`, `jungle_safari`,
  `city_playground`, `futuristic_lab`, `beach_island`, `cozy_village`)
- 27 supported 3D properties (`.glb` buildings/trees/cars/boats/bouncers + procedural 3D interactive
  props: `inflatable_pool`, `water_slide`, `cage_trap`, `mystery_table`, `treasure_chest`,
  `park_bench`, `race_finish_arch`, `magic_portal`, `control_pedestal`, `gift_box_pile`,
  `obstacle_hurdle`, `campfire_ring`, `stage_podium`, etc.) dynamically spawned from the reference
  video's `scene_props`!
"""

import re
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field

from core.object_knowledge_core import OBJECT_KNOWLEDGE_BASE, export_knowledge_for_props, resolve_object_knowledge


WorldBiome = Literal[
    "golden_city",
    "lush_forest",
    "indoor_room",
    "stone_maze",
    "waterpark_pool",
    "school_courtyard",
    "magic_carnival",
    "jungle_safari",
    "city_playground",
    "futuristic_lab",
    "beach_island",
    "cozy_village",
]

PropTypeLiteral = str


class EnvironmentPropSpec(BaseModel):
    """A 3D architectural or interactive prop placed in the world with collision bounds."""
    prop_type: PropTypeLiteral
    glb_model: Optional[str] = None
    target_height_m: float = 2.5
    position: Tuple[float, float, float]
    scale: float = 1.0
    rotation_y: float = 0.0
    collision_radius: float = 0.0
    is_pool: bool = False
    station_id: Optional[str] = None
    owner_role: Optional[str] = None
    spawn_on_finale: bool = False
    active_scenes: Optional[List[int]] = None
    primary_color: str = "#22b8cf"
    secondary_color: str = "#ffffff"
    aabb_half_extents: Optional[Tuple[float, float, float]] = None
    is_solid_wall: bool = False


class StoryBeatSpec(BaseModel):
    """A single narrative beat in the background story arc."""
    beat_index: int
    beat_type: Literal["hook_setup", "inciting_incident", "rising_challenge", "twist_complication", "clever_turn", "climax_action", "joyful_payoff"]
    summary: str
    emotional_tone: Literal["curious", "excited", "chaotic_funny", "surprised", "empathetic", "triumphant", "celebratory"]
    environment_intensity: float = Field(default=0.6, description="0.0 calm to 1.0 high energy motion")


class BackgroundStorySpec(BaseModel):
    """Complete background story and 3D world specification generated dynamically per clip."""
    story_id: str
    title: str
    premise_summary: str
    central_conflict: str
    moral_or_payoff: str
    world_biome: WorldBiome
    time_of_day: Literal["sunny_morning", "bright_noon", "golden_sunset", "magical_twilight"] = "sunny_morning"
    sky_top_hex: str = "#1ca3ec"
    sky_horizon_hex: str = "#a5f3fc"
    ground_primary_hex: str = "#e2e8f0"
    ground_secondary_hex: str = "#cbd5e1"
    floor_pattern: Literal["checker_tiles", "grass_meadow", "plaza_blocks", "sand_beach", "sci_fi_grid", "golden_plaza", "wood_planks", "maze_sand"] = "checker_tiles"
    fence_style: Literal["wood_picket", "stone_cliff", "playground_rail", "lab_barrier", "beach_ocean", "none"] = "none"
    environment_fx_style: Literal["water_ripples_and_breeze", "drifting_leaves_and_driving_car", "carnival_bunting_and_confetti"] = "water_ripples_and_breeze"
    props: List[EnvironmentPropSpec] = Field(default_factory=list)
    beats: List[StoryBeatSpec] = Field(default_factory=list)
    object_knowledge: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    expression_profiles: Dict[str, Any] = Field(default_factory=dict)
    motion_profiles: Dict[str, Any] = Field(default_factory=dict)


class BackgroundStoryCore:
    """
    Dynamically synthesizes the BackgroundStorySpec and collision-safe 3D `.glb` + procedural
    prop layout from any trending reference video analysis and script scenes.
    """

    BIOME_KEYWORDS: Dict[WorldBiome, List[str]] = {
        "golden_city": ["golden city", "gold city", "skyscraper", "tower", "ceo", "building", "ascend", "lift"],
        "lush_forest": ["caterpillar", "hamster", "leaf", "donkey", "hollow tree", "forest", "woods", "balloon"],
        "indoor_room": ["cockroach", "blue wall", "bedroom", "living room", "minimalist room", "pot", "computer", "gta", "desk", "monitor", "indoor", "room setting", "prank"],
        "stone_maze": ["maze", "labyrinth", "corridor", "laser", "shield", "camouflage", "strength power-up", "tom", "jerry", "bull"],
        "waterpark_pool": ["pool", "swim", "splash", "water", "float", "dive", "slide", "summer", "kolam"],
        "school_courtyard": ["school", "class", "student", "learn", "normal", "kindness", "unique"],
        "magic_carnival": ["magic", "carnival", "circus", "crown", "secret", "festival", "party", "celebrate", "stage", "mystery", "cloche", "treat"],
        "jungle_safari": ["jungle", "animal", "lion", "monkey", "fox", "wild", "nature", "dino", "cage", "trapped"],
        "city_playground": ["park", "playground", "race", "faster", "speed", "swing", "bike", "run", "challenge", "tag"],
        "futuristic_lab": ["robot", "invent", "contraption", "machine", "gadget", "science", "helmet", "space", "energy"],
        "beach_island": ["beach", "ocean", "sand", "island", "wave", "crab", "boat", "treasure", "pirate"],
        "cozy_village": ["home", "house", "family", "town", "village", "neighbor", "garden", "cookie"],
    }

    def infer_biome(self, text_corpus: str, clip_index: int = 1, explicit_biome: Optional[str] = None) -> WorldBiome:
        if explicit_biome and explicit_biome in self.BIOME_KEYWORDS:
            return explicit_biome  # type: ignore
        text_lower = text_corpus.lower()
        scores: Dict[WorldBiome, int] = {b: 0 for b in self.BIOME_KEYWORDS}
        for biome, kw_list in self.BIOME_KEYWORDS.items():
            for kw in kw_list:
                if kw in text_lower:
                    scores[biome] += 2
        best_biome = max(scores, key=lambda k: scores[k])
        if scores[best_biome] == 0:
            all_biomes: List[WorldBiome] = list(self.BIOME_KEYWORDS.keys())
            return all_biomes[(clip_index - 1) % len(all_biomes)]
        return best_biome

    def build_world_props(
        self,
        biome: WorldBiome,
        seed_num: int = 1,
        requested_props: Optional[List[str]] = None,
        prop_scene_map: Optional[Dict[str, List[int]]] = None,
        staging_mode: str = "general",
    ) -> Tuple[dict, List[EnvironmentPropSpec]]:
        """
        Populate a rich, biome-authentic 3D environment with collision bounds and
        per-scene active props extracted from the trending reference video.
        """
        props: List[EnvironmentPropSpec] = []
        requested_props = list(requested_props or [])
        req_set = set(requested_props)
        ps_map = prop_scene_map or {}

        if biome == "waterpark_pool" or "inflatable_pool" in req_set:
            palette = {
                "sky_top_hex": "#0ea5e9",
                "sky_horizon_hex": "#bae6fd",
                "ground_primary_hex": "#f1f5f9",
                "ground_secondary_hex": "#e2e8f0",
                "floor_pattern": "checker_tiles",
                "fence_style": "wood_picket",
                "environment_fx_style": "water_ripples_and_breeze",
            }
            props.extend([
                EnvironmentPropSpec(prop_type="inflatable_pool", station_id="station_1", owner_role="deuteragonist", position=(1.45, 0.0, -1.55), scale=0.88, collision_radius=0.88, is_pool=True, primary_color="#00b4d8", secondary_color="#ffffff"),
                EnvironmentPropSpec(prop_type="inflatable_pool", station_id="station_2", owner_role="rival_friend", position=(-1.45, 0.0, -0.75), scale=0.92, collision_radius=0.92, is_pool=True, primary_color="#9d4edd", secondary_color="#ffffff"),
                EnvironmentPropSpec(prop_type="inflatable_pool", station_id="station_3", owner_role="companion_1", position=(0.85, 0.0, 0.25), scale=0.94, collision_radius=0.94, is_pool=True, primary_color="#ef233c", secondary_color="#ffd166"),
                EnvironmentPropSpec(prop_type="inflatable_pool", station_id="station_hero", owner_role="protagonist", spawn_on_finale=True, position=(-0.35, 0.0, 1.15), scale=0.98, collision_radius=0.98, is_pool=True, primary_color="#1e293b", secondary_color="#facc15"),
                EnvironmentPropSpec(prop_type="water_slide", position=(0.0, 0.0, -4.4), scale=1.18, collision_radius=1.25, primary_color="#ff9f1c", secondary_color="#2ec4b6"),
                EnvironmentPropSpec(prop_type="bouncer_pad", glb_model="Bouncer.glb", target_height_m=0.55, position=(-3.3, 0.0, 0.5), scale=1.0, collision_radius=0.75),
                EnvironmentPropSpec(prop_type="water_boat", glb_model="Boat.glb", target_height_m=0.50, position=(3.3, 0.0, 0.5), scale=1.0, rotation_y=-0.4, collision_radius=0.75),
            ])
        else:
            if biome == "school_courtyard":
                palette = {
                    "sky_top_hex": "#38bdf8",
                    "sky_horizon_hex": "#fef9c3",
                    "ground_primary_hex": "#bbf7d0",
                    "ground_secondary_hex": "#86efac",
                    "floor_pattern": "grass_meadow",
                    "fence_style": "playground_rail",
                    "environment_fx_style": "drifting_leaves_and_driving_car",
                }
                props.extend([
                    EnvironmentPropSpec(prop_type="school_building", glb_model="Building1_Large.glb", target_height_m=4.6, position=(0.0, 0.0, -7.2), scale=1.3, collision_radius=2.2),
                    EnvironmentPropSpec(prop_type="house_building", glb_model="Building1_Small.glb", target_height_m=3.6, position=(-5.2, 0.0, -6.5), scale=1.1, rotation_y=0.3, collision_radius=1.5),
                    EnvironmentPropSpec(prop_type="house_building", glb_model="Building2_Small.glb", target_height_m=3.6, position=(5.2, 0.0, -6.5), scale=1.1, rotation_y=-0.3, collision_radius=1.5),
                    EnvironmentPropSpec(prop_type="moving_car", glb_model="car.glb", target_height_m=1.32, position=(-3.8, 0.0, -4.1), scale=1.0, rotation_y=1.57, collision_radius=1.1),
                ])
            elif biome == "jungle_safari":
                palette = {
                    "sky_top_hex": "#0284c7",
                    "sky_horizon_hex": "#bae6fd",
                    "ground_primary_hex": "#86efac",
                    "ground_secondary_hex": "#4ade80",
                    "floor_pattern": "grass_meadow",
                    "fence_style": "stone_cliff",
                    "environment_fx_style": "drifting_leaves_and_driving_car",
                }
                props.extend([
                    EnvironmentPropSpec(prop_type="nature_rock", glb_model="Rock1.glb", target_height_m=1.6, position=(-4.2, 0.0, -3.5), scale=1.3, collision_radius=0.8),
                    EnvironmentPropSpec(prop_type="nature_rock", glb_model="Rock1.glb", target_height_m=1.8, position=(4.2, 0.0, -3.5), scale=1.4, collision_radius=0.85),
                ])
            elif biome == "city_playground":
                palette = {
                    "sky_top_hex": "#38bdf8",
                    "sky_horizon_hex": "#e0f2fe",
                    "ground_primary_hex": "#f1f5f9",
                    "ground_secondary_hex": "#cbd5e1",
                    "floor_pattern": "plaza_blocks",
                    "fence_style": "playground_rail",
                    "environment_fx_style": "carnival_bunting_and_confetti",
                }
            elif biome == "futuristic_lab":
                palette = {
                    "sky_top_hex": "#1e3a8a",
                    "sky_horizon_hex": "#67e8f9",
                    "ground_primary_hex": "#1e293b",
                    "ground_secondary_hex": "#0f172a",
                    "floor_pattern": "sci_fi_grid",
                    "fence_style": "lab_barrier",
                    "environment_fx_style": "carnival_bunting_and_confetti",
                }
            elif biome == "beach_island":
                palette = {
                    "sky_top_hex": "#0284c7",
                    "sky_horizon_hex": "#bae6fd",
                    "ground_primary_hex": "#fde68a",
                    "ground_secondary_hex": "#fcd34d",
                    "floor_pattern": "sand_beach",
                    "fence_style": "beach_ocean",
                    "environment_fx_style": "water_ripples_and_breeze",
                }
                props.extend([
                    EnvironmentPropSpec(prop_type="water_boat", glb_model="Boat.glb", target_height_m=0.65, position=(3.4, 0.0, -4.6), scale=1.15, rotation_y=-0.6, collision_radius=0.85),
                    EnvironmentPropSpec(prop_type="beach_umbrella", position=(-3.4, 0.0, -2.6), scale=1.1, collision_radius=0.45, primary_color="#ef4444", secondary_color="#ffffff"),
                ])
            elif biome == "golden_city":
                palette = {
                    "sky_top_hex": "#0ea5e9",
                    "sky_horizon_hex": "#bae6fd",
                    "ground_primary_hex": "#eab308",
                    "ground_secondary_hex": "#ca8a04",
                    "floor_pattern": "golden_plaza",
                    "fence_style": "none",
                    "environment_fx_style": "water_ripples_and_breeze",
                }
                if "skyscraper_city" not in req_set:
                    req_set.add("skyscraper_city")
            elif biome == "lush_forest":
                palette = {
                    "sky_top_hex": "#38bdf8",
                    "sky_horizon_hex": "#dcfce7",
                    "ground_primary_hex": "#4ade80",
                    "ground_secondary_hex": "#22c55e",
                    "floor_pattern": "grass_meadow",
                    "fence_style": "none",
                    "environment_fx_style": "drifting_leaves_and_driving_car",
                }
            elif biome == "magic_carnival":
                palette = {
                    "sky_top_hex": "#7c3aed",
                    "sky_horizon_hex": "#fbcfe8",
                    "ground_primary_hex": "#fef3c7",
                    "ground_secondary_hex": "#fde68a",
                    "floor_pattern": "plaza_blocks",
                    "fence_style": "playground_rail",
                    "environment_fx_style": "carnival_bunting_and_confetti",
                }
                props.extend([
                    EnvironmentPropSpec(prop_type="carousel_tent", position=(0.0, 0.0, -6.2), scale=1.8, collision_radius=1.5, primary_color="#ec4899", secondary_color="#fef08a"),
                ])
            elif biome == "indoor_room":
                palette = {
                    "sky_top_hex": "#dbeafe",
                    "sky_horizon_hex": "#eff6ff",
                    "ground_primary_hex": "#d99b66",
                    "ground_secondary_hex": "#b4713c",
                    "floor_pattern": "wood_planks",
                    "fence_style": "none",
                    "environment_fx_style": "carnival_bunting_and_confetti",
                }
            elif biome == "stone_maze":
                palette = {
                    "sky_top_hex": "#38bdf8",
                    "sky_horizon_hex": "#fef08a",
                    "ground_primary_hex": "#facc15",
                    "ground_secondary_hex": "#eab308",
                    "floor_pattern": "maze_sand",
                    "fence_style": "none",
                    "environment_fx_style": "carnival_bunting_and_confetti",
                }
                if "stone_maze_walls" not in req_set:
                    req_set.add("stone_maze_walls")
            else:
                # cozy_village
                palette = {
                    "sky_top_hex": "#0284c7",
                    "sky_horizon_hex": "#fef08a",
                    "ground_primary_hex": "#d9f99d",
                    "ground_secondary_hex": "#bef264",
                    "floor_pattern": "grass_meadow",
                    "fence_style": "wood_picket",
                    "environment_fx_style": "carnival_bunting_and_confetti",
                }
                props.extend([
                    EnvironmentPropSpec(prop_type="house_building", glb_model="House1.glb", target_height_m=3.9, position=(-3.8, 0.0, -6.5), scale=1.25, rotation_y=0.2, collision_radius=1.6),
                    EnvironmentPropSpec(prop_type="house_building", glb_model="House2.glb", target_height_m=3.9, position=(3.8, 0.0, -6.5), scale=1.25, rotation_y=-0.2, collision_radius=1.6),
                ])

            # Dynamically spawn ANY reference-video interactive props (`OBJECT_KNOWLEDGE_BASE` + synthesized unseen props!)
            arch_skip = {"house_building", "school_building", "oak_tree", "pine_tree", "palm_tree", "nature_bush", "nature_rock", "moving_car", "water_boat", "inflatable_pool", "water_slide"}
            interactive_candidates = [p for p in requested_props if p not in arch_skip]
            if biome == "stone_maze" and "stone_maze_walls" not in interactive_candidates:
                interactive_candidates.insert(0, "stone_maze_walls")
            if biome == "golden_city" and "skyscraper_city" not in interactive_candidates:
                interactive_candidates.insert(0, "skyscraper_city")

            feature_coords = {
                "skyscraper_city": (0.0, 0.0, -6.5),
                "hydraulic_lift_chair": (0.55, 0.0, 0.20),
                "flying_airplane": (-3.2, 8.8, -3.8),
                "hollow_tree_trunk": (-1.25, 0.0, -1.05),
                "jungle_giant_leaf": (0.0, 0.0, -0.35),
                "balloon_bundle_red": (-0.35, 0.15, -0.35),
                "sausage_prop": (0.0, 0.0, 0.65),
                "giant_cockroach": (0.0, 1.38, -2.55),
                "cooking_pot": (-0.08, 1.08, -1.78),
                "cleaning_broom": (0.72, 0.0, -1.85),
                "computer_desk": (-0.42, 0.0, -0.78),
                "stone_maze_walls": (0.0, 0.0, -0.95),
                "laser_beam": (0.0, 0.68, -1.35),
                "hero_shield": (0.05, 0.72, -0.35),
                "angry_bull": (0.0, 0.0, -1.65),
                "camouflage_bush": (-0.55, 0.0, -0.55),
                "strength_orb": (0.0, 1.35, -0.65),
                "musical_staircase": (0.0, 0.0, -1.65),
                "musical_note": (1.15, 2.35, -1.55),
                "macarons": (0.0, 2.35, -1.45),
                "giant_turkey_leg": (-0.05, 0.85, -0.25),
                "folding_chair": (-0.55, 0.0, 0.22),
                "brick_wall": (0.55, 0.0, 0.02),
                "pickup_truck": (0.0, 0.0, -2.05),
                "ocean_water_plane": (0.0, 0.02, -4.0),
                "color_archways": (0.0, 0.0, -2.4),
                "bridge_span": (0.0, 0.0, -1.35),
                "book_and_coin_stacks": (0.0, 0.0, -1.55),
                "trophy_display": (0.0, 0.0, -1.85),
                "treasure_chest": (1.65, 0.0, -1.55),
                "color_cubes": (0.0, 0.0, -1.15),
                "cage_trap": (0.0, 0.0, -1.25),
                "mystery_table": (0.0, 0.0, -1.35),
                "race_finish_arch": (0.0, 0.0, -2.2),
            }
            def _measure_prop_bounds(pt: str) -> Tuple[float, float, float]:
                ks = OBJECT_KNOWLEDGE_BASE.get(pt)
                if ks and getattr(ks, "composite_parts", None):
                    ys, xs = [], []
                    for cp in ks.composite_parts:
                        sx, sy, _sz = (cp.size + [0.2, 0.2, 0.2])[:3]
                        ox, oy, _oz = (cp.offset + [0.0, 0.0, 0.0])[:3]
                        hy = sy if cp.shape in ("sphere", "torus") else sy * 0.5
                        hx = sx if cp.shape in ("sphere", "torus", "cylinder", "cone") else sx * 0.5
                        ys.extend([oy - hy, oy + hy])
                        xs.extend([ox - hx, ox + hx])
                    if ys and xs:
                        return min(ys), max(ys), max(0.08, max(xs) - min(xs))
                if ks and getattr(ks, "typical_dimensions_m", None):
                    tw, th, _td = (ks.typical_dimensions_m + [0.5, 0.5, 0.5])[:3]
                    return 0.0, max(0.1, th), max(0.1, tw)
                return 0.0, 0.40, 0.40

            fallback_coords = [
                (0.0, 0.0, -1.45),
                (-1.85, 0.0, -1.25),
                (1.85, 0.0, -1.25),
                (0.0, 0.0, -2.35),
            ]
            is_table_front = (staging_mode == "table_challenge_front") or ("wooden_table" in req_set)
            is_course_climb = (staging_mode == "course_climb_progression") or any(k in req_set for k in ("musical_staircase", "colored_blocks", "pink_platform"))

            table_scale = 0.85
            table_top_y = 0.64
            if is_table_front:
                for cand in interactive_candidates[:12]:
                    if "table" in cand.lower() and cand != "mystery_table":
                        _, t_max_y, _ = _measure_prop_bounds(cand)
                        table_scale = round(min(1.10, max(0.72, 0.64 / max(0.45, t_max_y))), 3)
                        table_top_y = round(t_max_y * table_scale, 3)
                        break

            for idx_p, p_type in enumerate(interactive_candidates[:12]):
                p_low = p_type.lower()
                active_sc = ps_map.get(p_type) or None
                pos = feature_coords.get(p_type, fallback_coords[idx_p % len(fallback_coords)])
                prop_scale = 1.0

                if is_table_front:
                    if p_type == "mystery_table" and "wooden_table" in req_set:
                        continue
                    if "table" in p_low or p_type == "wooden_table":
                        pos = (0.0, 0.0, 0.30)
                        prop_scale = table_scale
                        active_sc = None
                    elif not any(s in p_low for s in ("chair", "desk", "bench", "sofa", "couch")):
                        # Auto-scale ANY tabletop prop via true bounding box so it sits flush on table & never blocks faces!
                        p_min_y, p_max_y, p_span_w = _measure_prop_bounds(p_type)
                        p_span_h = max(0.06, p_max_y - p_min_y)
                        prop_scale = round(min(1.55, max(0.42, min(0.28 / p_span_h, 0.46 / max(0.08, p_span_w)))), 3)
                        pos = (0.0, round(table_top_y - p_min_y * prop_scale, 3), 0.34)
                elif is_course_climb:
                    if any(sk in p_low for sk in ("musical_staircase", "colored_blocks", "stair", "step_blocks")):
                        pos = (-0.25, 0.0, -0.15)
                        active_sc = None
                    elif "platform" in p_low:
                        pos = (1.35, 0.0, -0.15)
                    elif p_type == "balloon_bundle_red":
                        pos = (0.05, 1.45, 0.15)
                    elif any(fk in p_low for fk in ("musical_note", "hearts", "candy_drops", "popped_balloon")):
                        pos = (0.15 if idx_p % 2 == 0 else -0.35, 1.85, -0.15)

                no_collide = is_table_front or is_course_climb or p_type in (
                    "skyscraper_city", "hydraulic_lift_chair", "flying_airplane", "jungle_giant_leaf",
                    "ocean_water_plane", "race_finish_arch", "magic_portal", "bridge_span",
                    "color_archways", "color_cubes", "balloon_bundle_red", "sausage_prop",
                    "giant_cockroach", "cooking_pot", "cleaning_broom", "computer_desk",
                    "stone_maze_walls", "laser_beam", "hero_shield", "camouflage_bush", "strength_orb",
                    "musical_staircase", "musical_note", "macarons", "giant_turkey_leg",
                    "folding_chair", "brick_wall", "pickup_truck",
                )
                if p_type in ("skyscraper_city", "stone_maze_walls"):
                    active_sc = None
                props.append(
                    EnvironmentPropSpec(
                        prop_type=p_type,
                        glb_model="Bouncer.glb" if p_type == "bouncer_pad" else None,
                        position=pos,
                        scale=prop_scale,
                        rotation_y=0.68 if p_type == "computer_desk" else 0.0,
                        collision_radius=0.0 if no_collide else 0.52,
                        active_scenes=active_sc,
                        primary_color="#f59e0b" if idx_p == 0 else ("#ec4899" if idx_p == 1 else "#06b6d4"),
                        secondary_color="#ffffff",
                    )
                )

        # Natural trees & rocks placed cleanly along outer perimeter so they never clip through house roofs
        if biome not in ("golden_city", "futuristic_lab", "indoor_room", "stone_maze"):
            props.extend([
                EnvironmentPropSpec(prop_type="oak_tree", glb_model=None, target_height_m=3.4, position=(-6.3, 0.0, -4.4), scale=1.05, collision_radius=0.58),
                EnvironmentPropSpec(prop_type="oak_tree", glb_model=None, target_height_m=3.6, position=(6.3, 0.0, -4.4), scale=1.05, collision_radius=0.58),
                EnvironmentPropSpec(prop_type="oak_tree", glb_model=None, target_height_m=3.2, position=(-6.5, 0.0, -7.8), scale=1.00, collision_radius=0.55),
                EnvironmentPropSpec(prop_type="oak_tree", glb_model=None, target_height_m=3.2, position=(6.5, 0.0, -7.8), scale=1.00, collision_radius=0.55),
                EnvironmentPropSpec(prop_type="nature_bush", glb_model="Bush1.glb", target_height_m=0.80, position=(-3.9, 0.0, -1.8), scale=1.0, collision_radius=0.55),
                EnvironmentPropSpec(prop_type="nature_rock", glb_model="Rock1.glb", target_height_m=0.70, position=(3.9, 0.0, -1.8), scale=1.0, collision_radius=0.55),
            ])
        if biome in ("magic_carnival", "waterpark_pool"):
            props.extend([
                EnvironmentPropSpec(prop_type="balloon_bunch", position=(-2.9, 0.0, -3.2), scale=1.05, collision_radius=0.35, primary_color="#ff007f"),
                EnvironmentPropSpec(prop_type="balloon_bunch", position=(2.9, 0.0, -3.2), scale=1.05, collision_radius=0.35, primary_color="#00f5d4"),
            ])

        return palette, props

    def generate_background_story(
        self,
        script_title: str,
        hook_text: str,
        target_niche: str,
        scene_narrations: List[str],
        viral_formula: str = "",
        clip_index: int = 1,
        scenes: Optional[List[Any]] = None,
    ) -> BackgroundStorySpec:
        """
        Build a complete `BackgroundStorySpec` from the script and reference video scene analysis.
        """
        explicit_biome = None
        staging_mode = "general"
        requested_props: List[str] = []
        prop_scene_map: Dict[str, List[int]] = {}
        full_scene_blobs: List[str] = []
        if scenes:
            for sc in scenes:
                s_num = int(getattr(sc, "scene_number", 0) or 0)
                wb = getattr(sc, "world_biome", None)
                sm = getattr(sc, "scene_staging_mode", None) or "general"
                s_blob = f"{getattr(sc, 'narration', '')} {getattr(sc, 'ref_scene_action_summary', '')} {getattr(sc, 'image_prompt', '')}".lower()
                full_scene_blobs.append(s_blob)

                if sm in ("table_challenge_front", "course_climb_progression"):
                    staging_mode = sm

                # Explicit scene_props first
                sc_props_resolved: List[str] = list(getattr(sc, "scene_props", None) or [])
                if "computer" in s_blob or "gaming" in s_blob or "monitor" in s_blob or "desk" in s_blob:
                    sc_props_resolved = [p for p in sc_props_resolved if p not in ("hydraulic_lift_chair", "mystery_table")]
                    if "computer_desk" not in sc_props_resolved:
                        sc_props_resolved.append("computer_desk")

                # Per-scene whole-word extraction directly from OBJECT_KNOWLEDGE_BASE aliases (only when not colliding with explicit compound table/food props!)
                for oid, spec in OBJECT_KNOWLEDGE_BASE.items():
                    if oid in ("oak_tree", "pine_tree", "palm_tree", "cumulus_cloud", "street_lamp", "mystery_table"):
                        continue
                    if any(re.search(r"\b" + re.escape(a.lower().replace("_", " ")) + r"\b", s_blob) for a in [oid, *spec.aliases]):
                        if oid not in sc_props_resolved:
                            sc_props_resolved.append(oid)

                # Guard against hallucinated mystery_table & preserve synthesized compound object IDs!
                for raw_sp in sc_props_resolved:
                    kspec = resolve_object_knowledge(raw_sp)
                    sp = kspec.object_id if kspec else raw_sp
                    if sp == "mystery_table" and not any(w in s_blob for w in ("cloche", "mystery table", "silver cover")):
                        continue
                    if sp not in requested_props:
                        requested_props.append(sp)
                    if s_num > 0 and s_num not in prop_scene_map.get(sp, []):
                        prop_scene_map.setdefault(sp, []).append(s_num)

                # Infer staging_mode if LLM omitted it
                if staging_mode == "general":
                    if "wooden_table" in sc_props_resolved or (
                        any(w in s_blob for w in ("wooden table", "on a table", "table"))
                        and any(w in s_blob for w in ("cake", "cracker", "cone", "cactus", "leans", "pushed"))
                    ):
                        staging_mode = "table_challenge_front"
                    elif any(p in sc_props_resolved for p in ("musical_staircase", "colored_blocks", "pink_platform")) or any(
                        w in s_blob for w in ("stairs", "staircase", "platform", "steps")
                    ):
                        staging_mode = "course_climb_progression"

                # Auto-route indoor room & stone maze biomes even if LLM used a legacy outdoor biome name
                if any(w in s_blob for w in ("cockroach", "blue wall", "bedroom", "living room", "computer", "gaming", "gta")):
                    explicit_biome = "indoor_room"
                elif any(w in s_blob for w in ("maze", "labyrinth", "laser beam", "captain america shield")):
                    explicit_biome = "stone_maze"
                elif wb and not explicit_biome:
                    explicit_biome = wb

        full_text = " ".join([script_title, hook_text, target_niche, viral_formula] + scene_narrations + full_scene_blobs)
        if not explicit_biome:
            explicit_biome = None

        biome = self.infer_biome(full_text, clip_index=clip_index, explicit_biome=explicit_biome)
        palette, props = self.build_world_props(biome, seed_num=clip_index, requested_props=requested_props, prop_scene_map=prop_scene_map, staging_mode=staging_mode)

        beat_types: List[Literal["hook_setup", "inciting_incident", "rising_challenge", "twist_complication", "clever_turn", "climax_action", "joyful_payoff"]] = [
            "hook_setup",
            "inciting_incident",
            "rising_challenge",
            "twist_complication",
            "clever_turn",
            "climax_action",
            "joyful_payoff",
        ]
        tones: List[Literal["curious", "excited", "chaotic_funny", "surprised", "empathetic", "triumphant", "celebratory"]] = [
            "excited",
            "curious",
            "chaotic_funny",
            "surprised",
            "empathetic",
            "triumphant",
            "celebratory",
        ]

        beats: List[StoryBeatSpec] = []
        for idx, narr in enumerate(scene_narrations):
            b_type = beat_types[min(idx, len(beat_types) - 1)]
            tone = tones[min(idx, len(tones) - 1)]
            intensity = 0.5 + 0.08 * idx
            beats.append(
                StoryBeatSpec(
                    beat_index=idx + 1,
                    beat_type=b_type,
                    summary=narr,
                    emotional_tone=tone,
                    environment_intensity=min(1.0, round(intensity, 2)),
                )
            )

        return BackgroundStorySpec(
            story_id=f"story_clip_{clip_index:02d}_{biome}",
            title=script_title,
            premise_summary=hook_text,
            central_conflict=viral_formula or f"Characters in {biome} mirror the reference video story.",
            moral_or_payoff=scene_narrations[-1] if scene_narrations else "Everyone celebrates together!",
            world_biome=biome,
            time_of_day="sunny_morning" if clip_index % 2 == 1 else "bright_noon",
            sky_top_hex=palette["sky_top_hex"],
            sky_horizon_hex=palette["sky_horizon_hex"],
            ground_primary_hex=palette["ground_primary_hex"],
            ground_secondary_hex=palette["ground_secondary_hex"],
            floor_pattern=palette.get("floor_pattern", "checker_tiles"),
            fence_style=palette.get("fence_style", "none"),
            environment_fx_style=palette["environment_fx_style"],
            props=props,
            beats=beats,
            object_knowledge=export_knowledge_for_props([p.prop_type for p in props]),
        )
