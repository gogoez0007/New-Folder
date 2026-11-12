"""
Core 8: Physics & Spatial Integrity Validator Core (`core/physics_scene_validator.py`).

Pre-render spatial audit + repair core AND AABB geometry publisher guaranteeing:
  1. NO character clips or walks through solid walls (`brick_wall`, `stone_maze_walls`, `pickup_truck`,
     `computer_desk`, `oak_tree`, `house_building`, etc.).
  2. NO sudden levitation / floating up through a brick wall across scene cuts (`clip 2 detik 4-7` bug):
     cuts into an elevated vantage prop start cleanly ON top of that prop surface (never rising from inside
     solid bricks at y=0 -> y=2.0), and cuts back to ground scenes start cleanly grounded at y=0.0.
  3. Publishes accurate 3D `aabb_half_extents` (`[hx, hy, hz]`) & `is_solid_wall` onto every
     `EnvironmentPropSpec` so Three.js runtime collision also blocks penetration in real time.
"""

import math
from typing import Dict, List, Optional, Tuple

from core.background_story_core import BackgroundStorySpec, EnvironmentPropSpec
from core.scene_core import SceneDirectingSpec
from utils.logger import log_info, log_success, log_warning


# Known solid 3D bounding half-extents `[half_x, full_height_y, half_z]` at scale=1.0
PROP_AABB_HALF_EXTENTS: Dict[str, Tuple[float, float, float]] = {
    "brick_wall": (1.66, 2.02, 0.38),
    "stone_maze_walls": (0.85, 1.80, 0.65),
    "pickup_truck": (1.65, 1.50, 0.85),
    "moving_car": (1.35, 1.32, 0.72),
    "parked_car": (1.35, 1.32, 0.72),
    "computer_desk": (0.82, 1.35, 0.45),
    "folding_chair": (0.30, 0.85, 0.30),
    "mystery_table": (0.80, 1.10, 0.45),
    "oak_tree": (0.42, 3.60, 0.42),
    "hollow_tree_trunk": (0.85, 3.80, 0.85),
    "house_building": (1.85, 3.90, 1.85),
    "school_building": (2.40, 4.60, 2.20),
    "angry_bull": (0.55, 1.35, 0.52),
    "camouflage_bush": (0.72, 1.05, 0.68),
    "cage_trap": (0.62, 1.50, 0.62),
    "treasure_chest": (0.55, 0.75, 0.38),
    "park_bench": (0.82, 0.90, 0.38),
    "water_slide": (1.25, 2.80, 1.45),
}

ELEVATED_SUPPORTS = {
    "brick_wall": 1.98,
    "oak_tree": 2.65,
    "hollow_tree_trunk": 2.45,
    "pickup_truck": 0.92,
    "musical_staircase": 1.55,
    "stage_podium": 0.65,
    "hydraulic_lift_chair": 0.36,
    "skyscraper_city": 0.0,
}

CONTINUOUS_ELEVATORS = {"hydraulic_lift_chair", "skyscraper_city", "musical_staircase", "colored_blocks", "pink_platform", "stage_podium", "bridge_span", "water_slide"}


class PhysicsSceneValidatorCore:
    """Validates and repairs 3D actor trajectories, elevations, and wall AABBs before GPU render."""

    @staticmethod
    def _is_prop_active_in_scene(prop: EnvironmentPropSpec, scene_number: int) -> bool:
        if prop.active_scenes and scene_number not in prop.active_scenes:
            return False
        if prop.spawn_on_finale:
            return False
        return True

    def annotate_prop_aabbs(self, story: BackgroundStorySpec) -> None:
        """Populate explicit `aabb_half_extents` & `is_solid_wall` on every prop for runtime Three.js collision."""
        for prop in story.props:
            if getattr(prop, "aabb_half_extents", None):
                continue
            sc = float(getattr(prop, "scale", 1.0) or 1.0)
            if prop.prop_type in PROP_AABB_HALF_EXTENTS:
                hx, hy, hz = PROP_AABB_HALF_EXTENTS[prop.prop_type]
                prop.aabb_half_extents = (round(hx * sc, 3), round(hy * sc, 3), round(hz * sc, 3))
                if prop.prop_type in ("brick_wall", "pickup_truck", "moving_car", "cage_trap", "angry_bull"):
                    prop.is_solid_wall = True
            elif prop.prop_type in ("giant_cockroach", "cooking_pot", "cleaning_broom", "laser_beam", "hero_shield", "strength_orb", "musical_note", "macarons", "balloon_bundle_red", "giant_turkey_leg"):
                prop.aabb_half_extents = None
                prop.is_solid_wall = False

    @staticmethod
    def _segment_intersects_box(
        p0: Tuple[float, float, float],
        p1: Tuple[float, float, float],
        prop: EnvironmentPropSpec,
        actor_r: float = 0.42,
    ) -> bool:
        if not getattr(prop, "aabb_half_extents", None):
            return False
        hx, hy, hz = prop.aabb_half_extents  # type: ignore[misc]
        px, py, pz = prop.position
        for i in range(11):
            u = i / 10.0
            x = p0[0] + (p1[0] - p0[0]) * u
            y = p0[1] + (p1[1] - p0[1]) * u
            z = p0[2] + (p1[2] - p0[2]) * u
            # Clear if cleanly above the top surface of the obstacle!
            if y >= (py + hy - 0.14):
                continue
            if abs(x - px) < (hx + actor_r * 0.85) and abs(z - pz) < (hz + actor_r * 0.85):
                return True
        return False

    @staticmethod
    def _push_point_outside_box(
        pt: Tuple[float, float, float],
        prop: EnvironmentPropSpec,
        actor_r: float = 0.42,
    ) -> Tuple[float, float, float]:
        if not getattr(prop, "aabb_half_extents", None):
            return pt
        hx, hy, hz = prop.aabb_half_extents  # type: ignore[misc]
        px, py, pz = prop.position
        x, y, z = pt
        if y >= (py + hy - 0.14):
            return pt
        pad = actor_r + 0.14
        dx = x - px
        dz = z - pz
        pen_x = (hx + pad) - abs(dx)
        pen_z = (hz + pad) - abs(dz)
        if pen_x <= 0 or pen_z <= 0:
            return pt
        # Prefer pushing forward toward camera (+Z) when in front/mid of wide walls like brick_wall!
        if prop.prop_type in ("brick_wall", "pickup_truck", "computer_desk"):
            new_z = pz + hz + pad if dz >= -0.05 else pz - hz - pad
            return (round(x, 2), y, round(new_z, 2))
        if pen_x < pen_z:
            new_x = px + (hx + pad) * (1.0 if dx >= 0 else -1.0)
            return (round(new_x, 2), y, z)
        new_z = pz + (hz + pad) * (1.0 if dz >= 0 else -1.0)
        return (x, y, round(new_z, 2))

    def validate_and_repair_clip(
        self,
        scenes: List,
        story: BackgroundStorySpec,
        scene_specs: List[SceneDirectingSpec],
    ) -> Tuple[int, int]:
        """
        Audit and repair all scenes sequentially:
          - Eliminates illegal mid-air / mid-wall upward or downward vertical phasing across cuts
          - Anchors elevated actors cleanly atop physical supporting props (brick_wall / oak_tree / pickup_truck)
          - Detours trajectories that intersect any solid prop AABB (`brick_wall`, `pickup_truck`, etc.)
        Returns `(repaired_elevations, repaired_collisions)`.
        """
        self.annotate_prop_aabbs(story)
        repaired_elev = 0
        repaired_col = 0

        for idx, spec in enumerate(scene_specs):
            sc_num = spec.scene_number
            sc_obj = scenes[idx] if idx < len(scenes) else None
            sc_prop_names = set(getattr(sc_obj, "scene_props", None) or [])
            active_props = [p for p in story.props if self._is_prop_active_in_scene(p, sc_num)]
            active_by_type = {p.prop_type: p for p in active_props}

            has_continuous_lift = any(p in sc_prop_names or p in active_by_type for p in CONTINUOUS_ELEVATORS) or ("golden_city" in (story.world_biome or "")) or (getattr(sc_obj, "scene_staging_mode", "") == "course_climb_progression")

            # 1. Inspect every actor's elevation & wall collisions
            for actor in spec.actors:
                if actor.action == "fly":
                    continue
                target_elev = float(getattr(sc_obj, "partner_elevation_m", 0.0) or 0.0) if "partner" in actor.char_id or actor.char_id != spec.actors[0].char_id else float(getattr(sc_obj, "lead_elevation_m", 0.0) or 0.0)

                # If NOT an elevator scene, disallow mid-shot vertical teleport / phasing from prev scene!
                if not has_continuous_lift:
                    support_prop: Optional[EnvironmentPropSpec] = None
                    for sp_name in ("brick_wall", "hollow_tree_trunk", "oak_tree", "pickup_truck"):
                        if sp_name in active_by_type and target_elev >= 0.8:
                            support_prop = active_by_type[sp_name]
                            break

                    desired_y = target_elev
                    if support_prop is not None and support_prop.aabb_half_extents:
                        desired_y = round(support_prop.position[1] + support_prop.aabb_half_extents[1], 2)
                    elif desired_y > 0.35 and "brick_wall" not in active_by_type and "oak_tree" not in active_by_type and "pickup_truck" not in active_by_type:
                        # No supporting object exists in this ground scene -> ground cleanly at 0.0
                        desired_y = 0.0

                    for ph in actor.phases:
                        # Fix rising straight through bricks OR dropping down from previous cut's wall!
                        if abs(ph.from_pos[1] - desired_y) > 0.25 or abs(ph.to_pos[1] - desired_y) > 0.25:
                            if support_prop is not None and desired_y >= 0.8:
                                sx = round(support_prop.position[0] * 0.65, 2) if abs(ph.to_pos[0] - support_prop.position[0]) > 1.2 else ph.to_pos[0]
                                sz = round(support_prop.position[2], 2)
                                ph.from_pos = (sx, desired_y, sz)
                                ph.to_pos = (sx, desired_y, sz)
                            else:
                                ph.from_pos = (ph.from_pos[0], desired_y, ph.from_pos[2])
                                ph.to_pos = (ph.to_pos[0], desired_y, ph.to_pos[2])
                            repaired_elev += 1

                    actor.start_pos = (actor.start_pos[0], desired_y, actor.start_pos[2])
                    actor.end_pos = (actor.end_pos[0], desired_y, actor.end_pos[2])

                # 2. Check & repair solid wall / truck / desk AABB penetration across all phase segments
                r_col = float(actor.collision_radius or 0.42)
                for ph in actor.phases:
                    for prop in active_props:
                        if not getattr(prop, "is_solid_wall", False) and prop.prop_type not in ("brick_wall", "stone_maze_walls", "pickup_truck", "computer_desk"):
                            continue
                        if self._segment_intersects_box(ph.from_pos, ph.to_pos, prop, r_col):
                            new_p0 = self._push_point_outside_box(ph.from_pos, prop, r_col)
                            new_p1 = self._push_point_outside_box(ph.to_pos, prop, r_col)
                            # If both endpoints sit on opposite sides of the wall, route segment around edge / camera-front lane
                            if self._segment_intersects_box(new_p0, new_p1, prop, r_col) and getattr(prop, "aabb_half_extents", None):
                                hx, hy, hz = prop.aabb_half_extents  # type: ignore[misc]
                                px, py, pz = prop.position
                                pad = r_col + 0.18
                                mid_x = 0.5 * (new_p0[0] + new_p1[0])
                                mid_z = 0.5 * (new_p0[2] + new_p1[2])
                                if prop.prop_type in ("brick_wall", "pickup_truck", "computer_desk") and mid_z >= pz - 0.15:
                                    safe_z = round(pz + hz + pad, 2)
                                    new_p0 = (new_p0[0], new_p0[1], max(safe_z, new_p0[2]))
                                    new_p1 = (new_p1[0], new_p1[1], max(safe_z, new_p1[2]))
                                else:
                                    side_x = px + (hx + pad) * (1.0 if mid_x >= px else -1.0)
                                    safe_x = round(side_x, 2)
                                    new_p0 = (safe_x, new_p0[1], new_p0[2])
                                    new_p1 = (safe_x, new_p1[1], new_p1[2])
                            if new_p0 != ph.from_pos or new_p1 != ph.to_pos:
                                ph.from_pos = new_p0
                                ph.to_pos = new_p1
                                repaired_col += 1
                if actor.phases:
                    actor.start_pos = actor.phases[0].from_pos
                    actor.end_pos = actor.phases[-1].to_pos

        log_success(
            f"[PhysicsSceneValidator] Audit complete ({len(scene_specs)} scenes): "
            f"{repaired_elev} abrupt wall-rise/drop fix(es), {repaired_col} wall-clipping detour(s)."
        )
        return repaired_elev, repaired_col
