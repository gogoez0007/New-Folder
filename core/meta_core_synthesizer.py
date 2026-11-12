"""
Core 6: Autonomous Meta-Core Generator (`core/meta_core_synthesizer.py`).

When a trending reference video introduces an object not yet present in `OBJECT_KNOWLEDGE_BASE`
(for example: `handphone` / `smartphone`, `microphone`, `camera`, `pizza_box`, `scooter`, etc.),
this Meta-Core dynamically synthesizes BOTH:
  1. A real persistent Python Object Core module (`core/generated_objects/<id>_core.py`), AND
  2. An executable Three.js ES module builder (`assets/three/generated/custom_objects.js`),
and registers it immediately into `OBJECT_KNOWLEDGE_BASE` without any hardcoding.
"""

import json
import pprint
import re
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from google import genai
from google.genai import types

import config
from core.object_knowledge_core import (
    OBJECT_KNOWLEDGE_BASE,
    MotionBehavior,
    ObjectAnatomySpec,
    ObjectCategory,
    ObjectPartRecipe,
    SurfaceFinish,
    resolve_exact_or_alias_knowledge,
)
from core.generated_objects import load_all_generated_objects
from utils.logger import log_info, log_success, log_warning


class SynthesizedObjectBlueprint(BaseModel):
    """Structured LLM blueprint describing how to build an unseen 3D object anatomically."""
    object_id: str
    display_name: str
    category: ObjectCategory = "party_prank"
    surface_finish: SurfaceFinish = "painted_metal"
    motion_behavior: MotionBehavior = "static"
    typical_dimensions_m: List[float] = Field(default_factory=lambda: [0.6, 0.8, 0.4])
    silhouette_notes: str = ""
    aliases: List[str] = Field(default_factory=list)
    composite_parts: List[ObjectPartRecipe] = Field(default_factory=list)


class MetaCoreSynthesizer:
    """
    Meta-Core responsible for autonomously generating new Object Core scripts (`.py` + `.js`)
    whenever an unknown object is encountered in a trending reference video.
    """

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or config.GEMINI_API_KEY
        self.client = genai.Client(api_key=key) if key else None
        self.py_out_dir = Path(config.BASE_DIR) / "core" / "generated_objects"
        self.js_out_file = Path(config.BASE_DIR) / "assets" / "three" / "generated" / "custom_objects.js"
        self.py_out_dir.mkdir(parents=True, exist_ok=True)
        self.js_out_file.parent.mkdir(parents=True, exist_ok=True)
        self._bootstrap_existing()

    def _bootstrap_existing(self) -> None:
        """Load previously synthesized Python object cores into `OBJECT_KNOWLEDGE_BASE`."""
        loaded = load_all_generated_objects()
        for oid, spec in loaded.items():
            if oid not in OBJECT_KNOWLEDGE_BASE:
                OBJECT_KNOWLEDGE_BASE[oid] = spec

    @staticmethod
    def _normalize_id(prop_name: str) -> str:
        clean = re.sub(r"[^a-zA-Z0-9]+", "_", (prop_name or "object").strip().lower()).strip("_")
        return clean or "custom_object"

    def _synthesize_via_gemini(self, clean_id: str, scene_context: str) -> Optional[ObjectAnatomySpec]:
        """Ask Gemini to design multi-part 3D real-world anatomy for an unseen prop."""
        if not self.client:
            return None
        prompt = f"""
You are a Senior 3D Technical Artist & Procedural Geometry Engineer designing a Three.js asset for a vertical cartoon 3D animation.
An unseen prop `{clean_id}` appeared in the reference video context:
\"\"\"{scene_context}\"\"\"

Design an unmistakable, realistic multi-part 3D composite object (between 4 and 9 parts) using shapes from:
`box`, `cylinder`, `sphere`, `cone`, `torus`, `capsule`.

CRITICAL COORDINATE RULES:
- Ground rests at y=0. All bottom parts start cleanly >= 0.0 (or handheld elevation ~0.85m if it is a small handheld item like `handphone`/`smartphone`/`camera`/`microphone`). Tabletop foods/cakes/plants should rest cleanly with bottom at y=0.0 so they can be placed atop a table surface!
- Sizes `[sx, sy, sz]` are in meters cleanly scaled so the hero object is readable in vertical 9:16 portrait shots (~0.45m–1.2m silhouette).
- For phones (`handphone`/`smartphone`), include a sleek frame (`box`), glowing vibrant screen front face (`glass_facade` or `latex_glossy`), bottom speaker/button bar, and rear triple camera bump + lenses!
- Never make a lazy 1-box blob; use contrasting realistic hex colors and appropriate finishes (`latex_glossy`, `brushed_chrome`, `painted_metal`, `glass_facade`, `matte_wood`, `glazed_food`, `fabric`, `ceramic`, `organic_bark`, `waxy_foliage`).
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
                        response_schema=SynthesizedObjectBlueprint,
                        temperature=0.35,
                    ),
                )
                bp = resp.parsed if hasattr(resp, "parsed") and isinstance(resp.parsed, SynthesizedObjectBlueprint) else SynthesizedObjectBlueprint.model_validate_json(resp.text)
                if bp.composite_parts:
                    return ObjectAnatomySpec(
                        object_id=clean_id,
                        display_name=bp.display_name or clean_id.replace("_", " ").title(),
                        category=bp.category,
                        builder_key="generated_builder",
                        real_anatomy_parts=[p.part_name for p in bp.composite_parts],
                        typical_dimensions_m=bp.typical_dimensions_m or [0.7, 1.0, 0.4],
                        default_height_m=max(0.3, float((bp.typical_dimensions_m or [0.7, 1.0, 0.4])[1])),
                        surface_finish=bp.surface_finish,
                        motion_behavior=bp.motion_behavior,
                        placement_layer="ground",
                        silhouette_notes=bp.silhouette_notes or f"AI-synthesized multi-part 3D core for '{clean_id}'.",
                        aliases=list(dict.fromkeys([clean_id, clean_id.replace("_", " "), *bp.aliases])),
                        composite_parts=bp.composite_parts,
                    )
            except Exception as err:
                log_warning(f"[MetaCoreSynthesizer] Gemini object synth ({mname}) skipped: {err}")
        return None

    def _semantic_anatomy_fallback(self, clean_id: str, scene_context: str) -> ObjectAnatomySpec:
        """Offline multi-part anatomical fallback when LLM is unreachable."""
        low = f"{clean_id} {scene_context}".lower().replace("_", " ")
        parts: List[ObjectPartRecipe]
        cat: ObjectCategory = "furniture_mechanism"
        fin: SurfaceFinish = "painted_metal"

        if any(w in low for w in ("handphone", "smartphone", "phone", "iphone", "hp", "cellphone", "tablet", "ipad")):
            cat, fin = "sports_games", "brushed_chrome"
            parts = [
                ObjectPartRecipe(part_name="titanium_chassis", shape="box", size=[0.46, 0.88, 0.055], offset=[0, 1.02, 0], color="#1e293b", finish="brushed_chrome"),
                ObjectPartRecipe(part_name="glowing_screen", shape="box", size=[0.40, 0.78, 0.020], offset=[0, 1.02, 0.025], color="#38bdf8", finish="glass_facade"),
                ObjectPartRecipe(part_name="app_banner_card", shape="box", size=[0.30, 0.16, 0.015], offset=[0, 1.20, 0.036], color="#facc15", finish="latex_glossy"),
                ObjectPartRecipe(part_name="app_chat_bubble", shape="box", size=[0.26, 0.12, 0.015], offset=[-0.04, 0.94, 0.036], color="#22c55e", finish="latex_glossy"),
                ObjectPartRecipe(part_name="dynamic_island", shape="capsule", size=[0.022, 0.08, 0.02], offset=[0, 1.37, 0.036], rotation=[0, 0, 1.57], color="#020617", finish="latex_glossy"),
                ObjectPartRecipe(part_name="camera_island", shape="box", size=[0.18, 0.18, 0.025], offset=[-0.10, 1.30, -0.035], color="#0f172a", finish="painted_metal"),
                ObjectPartRecipe(part_name="lens_top", shape="cylinder", size=[0.04, 0.03, 0.04], offset=[-0.13, 1.34, -0.05], rotation=[1.57, 0, 0], color="#0ea5e9", finish="glass_facade"),
                ObjectPartRecipe(part_name="lens_bot", shape="cylinder", size=[0.04, 0.03, 0.04], offset=[-0.07, 1.25, -0.05], rotation=[1.57, 0, 0], color="#0ea5e9", finish="glass_facade"),
            ]
        elif any(w in low for w in ("microphone", "mic", "podcast")):
            cat, fin = "sports_games", "brushed_chrome"
            parts = [
                ObjectPartRecipe(part_name="weighted_base", shape="cylinder", size=[0.24, 0.06, 0.24], offset=[0, 0.03, 0], color="#1e293b", finish="painted_metal"),
                ObjectPartRecipe(part_name="stand_shaft", shape="cylinder", size=[0.025, 0.98, 0.025], offset=[0, 0.54, 0], color="#cbd5e1", finish="brushed_chrome"),
                ObjectPartRecipe(part_name="mic_handle", shape="cylinder", size=[0.04, 0.22, 0.05], offset=[0, 1.06, 0.04], rotation=[0.4, 0, 0], color="#0f172a", finish="painted_metal"),
                ObjectPartRecipe(part_name="mesh_capsule_head", shape="sphere", size=[0.11, 0.13, 0.11], offset=[0, 1.18, 0.08], color="#94a3b8", finish="brushed_chrome"),
            ]
        elif any(w in low for w in ("camera", "vlog", "tripod")):
            cat, fin = "vehicles_flight", "painted_metal"
            parts = [
                ObjectPartRecipe(part_name="tripod_leg_l", shape="cylinder", size=[0.025, 0.72, 0.025], offset=[-0.22, 0.34, 0], rotation=[0, 0, -0.32], color="#334155", finish="brushed_chrome"),
                ObjectPartRecipe(part_name="tripod_leg_r", shape="cylinder", size=[0.025, 0.72, 0.025], offset=[0.22, 0.34, 0], rotation=[0, 0, 0.32], color="#334155", finish="brushed_chrome"),
                ObjectPartRecipe(part_name="body_shell", shape="box", size=[0.52, 0.34, 0.26], offset=[0, 0.85, 0], color="#1e293b", finish="painted_metal"),
                ObjectPartRecipe(part_name="lens_barrel", shape="cylinder", size=[0.14, 0.22, 0.14], offset=[0, 0.85, 0.20], rotation=[1.57, 0, 0], color="#475569", finish="brushed_chrome"),
                ObjectPartRecipe(part_name="lens_glass", shape="sphere", size=[0.11, 0.11, 0.06], offset=[0, 0.85, 0.30], color="#38bdf8", finish="glass_facade"),
            ]
        elif any(w in low for w in ("wooden table", "dining table", "wood table", "challenge table")):
            cat, fin = "furniture_mechanism", "matte_wood"
            parts = [
                ObjectPartRecipe(part_name="oak_tabletop", shape="box", size=[2.15, 0.08, 0.98], offset=[0, 0.74, 0], color="#c28e5c", finish="matte_wood"),
                ObjectPartRecipe(part_name="apron_beam", shape="box", size=[1.96, 0.08, 0.84], offset=[0, 0.67, 0], color="#926038", finish="matte_wood"),
                ObjectPartRecipe(part_name="leg_fl", shape="box", size=[0.09, 0.72, 0.09], offset=[-0.92, 0.36, 0.36], color="#854d27", finish="matte_wood"),
                ObjectPartRecipe(part_name="leg_fr", shape="box", size=[0.09, 0.72, 0.09], offset=[0.92, 0.36, 0.36], color="#854d27", finish="matte_wood"),
                ObjectPartRecipe(part_name="leg_bl", shape="box", size=[0.09, 0.72, 0.09], offset=[-0.92, 0.36, -0.36], color="#854d27", finish="matte_wood"),
                ObjectPartRecipe(part_name="leg_br", shape="box", size=[0.09, 0.72, 0.09], offset=[0.92, 0.36, -0.36], color="#854d27", finish="matte_wood"),
            ]
        elif any(w in low for w in ("cake", "strawberry cake", "frosting", "pastry")):
            cat, fin = "food_kitchen", "glazed_food"
            if any(w in low for w in ("smash", "splat", "crush", "mess")):
                parts = [
                    ObjectPartRecipe(part_name="cake_platter", shape="cylinder", size=[0.30, 0.03, 0.30], offset=[0, 0.015, 0], color="#f8fafc", finish="ceramic"),
                    ObjectPartRecipe(part_name="cream_splat_base", shape="cylinder", size=[0.26, 0.07, 0.26], offset=[0, 0.06, 0], color="#fff1f2", finish="glazed_food"),
                    ObjectPartRecipe(part_name="jam_splash_l", shape="sphere", size=[0.11, 0.04, 0.11], offset=[-0.10, 0.08, 0.08], color="#e11d48", finish="glazed_food"),
                    ObjectPartRecipe(part_name="jam_splash_r", shape="sphere", size=[0.10, 0.04, 0.10], offset=[0.11, 0.08, -0.05], color="#fb7185", finish="glazed_food"),
                    ObjectPartRecipe(part_name="berry_1", shape="sphere", size=[0.045, 0.055, 0.045], offset=[-0.04, 0.11, 0.04], color="#dc2626", finish="glazed_food"),
                    ObjectPartRecipe(part_name="berry_2", shape="sphere", size=[0.042, 0.05, 0.042], offset=[0.08, 0.10, 0.07], color="#dc2626", finish="glazed_food"),
                ]
            else:
                parts = [
                    ObjectPartRecipe(part_name="cake_platter", shape="cylinder", size=[0.28, 0.03, 0.28], offset=[0, 0.015, 0], color="#f8fafc", finish="ceramic"),
                    ObjectPartRecipe(part_name="sponge_tier", shape="cylinder", size=[0.23, 0.20, 0.23], offset=[0, 0.13, 0], color="#fff7ed", finish="glazed_food"),
                    ObjectPartRecipe(part_name="cream_crown", shape="torus", size=[0.18, 0.038, 0.038], offset=[0, 0.24, 0], rotation=[1.57, 0, 0], color="#ffffff", finish="glazed_food"),
                    ObjectPartRecipe(part_name="strawberry_c", shape="cone", size=[0.048, 0.08, 0.048], offset=[0, 0.28, 0], color="#dc2626", finish="glazed_food"),
                    ObjectPartRecipe(part_name="strawberry_l", shape="cone", size=[0.044, 0.075, 0.044], offset=[-0.10, 0.27, 0.05], color="#ef4444", finish="glazed_food"),
                    ObjectPartRecipe(part_name="strawberry_r", shape="cone", size=[0.044, 0.075, 0.044], offset=[0.10, 0.27, 0.05], color="#ef4444", finish="glazed_food"),
                    ObjectPartRecipe(part_name="strawberry_b", shape="cone", size=[0.044, 0.075, 0.044], offset=[0.0, 0.27, -0.10], color="#e11d48", finish="glazed_food"),
                ]
        elif any(w in low for w in ("ice cream", "cone", "gelato", "sundae")):
            cat, fin = "food_kitchen", "glazed_food"
            if any(w in low for w in ("smash", "splat", "spill", "melt")):
                parts = [
                    ObjectPartRecipe(part_name="cream_puddle_a", shape="cylinder", size=[0.24, 0.04, 0.22], offset=[0, 0.02, 0.03], color="#fffbeb", finish="glazed_food"),
                    ObjectPartRecipe(part_name="cream_puddle_b", shape="sphere", size=[0.12, 0.05, 0.10], offset=[-0.09, 0.04, 0.06], color="#fbcfe8", finish="glazed_food"),
                    ObjectPartRecipe(part_name="fallen_cone_1", shape="cone", size=[0.065, 0.20, 0.065], offset=[-0.14, 0.06, -0.02], rotation=[1.45, 0.2, 0.6], color="#d97706", finish="matte_wood"),
                    ObjectPartRecipe(part_name="fallen_cone_2", shape="cone", size=[0.065, 0.20, 0.065], offset=[0.16, 0.06, 0.04], rotation=[-1.40, -0.3, -0.5], color="#b45309", finish="matte_wood"),
                ]
            else:
                parts = [
                    ObjectPartRecipe(part_name="waffle_cone_1", shape="cone", size=[0.068, 0.24, 0.068], offset=[-0.22, 0.12, 0], color="#d97706", finish="matte_wood"),
                    ObjectPartRecipe(part_name="scoop_1", shape="sphere", size=[0.072, 0.072, 0.072], offset=[-0.22, 0.25, 0], color="#fffbeb", finish="glazed_food"),
                    ObjectPartRecipe(part_name="waffle_cone_2", shape="cone", size=[0.068, 0.24, 0.068], offset=[-0.07, 0.12, 0.03], color="#d97706", finish="matte_wood"),
                    ObjectPartRecipe(part_name="scoop_2", shape="sphere", size=[0.072, 0.072, 0.072], offset=[-0.07, 0.25, 0.03], color="#fbcfe8", finish="glazed_food"),
                    ObjectPartRecipe(part_name="waffle_cone_3", shape="cone", size=[0.068, 0.24, 0.068], offset=[0.08, 0.12, 0.0], color="#d97706", finish="matte_wood"),
                    ObjectPartRecipe(part_name="scoop_3", shape="sphere", size=[0.072, 0.072, 0.072], offset=[0.08, 0.25, 0.0], color="#bbf7d0", finish="glazed_food"),
                    ObjectPartRecipe(part_name="waffle_cone_4", shape="cone", size=[0.068, 0.24, 0.068], offset=[0.23, 0.12, 0.02], color="#d97706", finish="matte_wood"),
                    ObjectPartRecipe(part_name="scoop_4", shape="sphere", size=[0.072, 0.072, 0.072], offset=[0.23, 0.25, 0.02], color="#fef08a", finish="glazed_food"),
                ]
        elif any(w in low for w in ("cactus", "succulent", "prickly", "pot plant")):
            cat, fin = "nature_flora", "waxy_foliage"
            parts = [
                ObjectPartRecipe(part_name="ceramic_pot", shape="cylinder", size=[0.16, 0.16, 0.13], offset=[0, 0.08, 0], color="#475569", finish="ceramic"),
                ObjectPartRecipe(part_name="pot_soil", shape="cylinder", size=[0.145, 0.02, 0.145], offset=[0, 0.165, 0], color="#451a03", finish="matte_wood"),
                ObjectPartRecipe(part_name="cactus_globe", shape="sphere", size=[0.135, 0.16, 0.135], offset=[0, 0.28, 0], color="#16a34a", finish="waxy_foliage"),
                ObjectPartRecipe(part_name="cactus_arm_l", shape="capsule", size=[0.045, 0.10, 0.045], offset=[-0.12, 0.30, 0], rotation=[0, 0, 0.55], color="#22c55e", finish="waxy_foliage"),
                ObjectPartRecipe(part_name="cactus_arm_r", shape="capsule", size=[0.042, 0.09, 0.042], offset=[0.12, 0.28, 0], rotation=[0, 0, -0.55], color="#22c55e", finish="waxy_foliage"),
                ObjectPartRecipe(part_name="cactus_spine_top", shape="cone", size=[0.025, 0.055, 0.025], offset=[0, 0.44, 0], color="#fef08a", finish="waxy_foliage"),
                ObjectPartRecipe(part_name="cactus_spine_f", shape="cone", size=[0.018, 0.045, 0.018], offset=[0.04, 0.31, 0.12], rotation=[1.2, 0, 0], color="#fef9c3", finish="waxy_foliage"),
                ObjectPartRecipe(part_name="cactus_spine_l", shape="cone", size=[0.018, 0.045, 0.018], offset=[-0.09, 0.32, 0.08], rotation=[0.9, 0, 0.6], color="#fef9c3", finish="waxy_foliage"),
            ]
        elif any(w in low for w in ("cracker", "wafer", "biscuit", "toast", "cookie")):
            cat, fin = "food_kitchen", "glazed_food"
            parts = [
                ObjectPartRecipe(part_name="biscuit_base", shape="box", size=[0.22, 0.05, 0.22], offset=[0, 0.025, 0], color="#d97706", finish="matte_wood"),
                ObjectPartRecipe(part_name="biscuit_mid", shape="box", size=[0.20, 0.05, 0.20], offset=[0.01, 0.075, -0.01], color="#f59e0b", finish="matte_wood"),
                ObjectPartRecipe(part_name="biscuit_top", shape="box", size=[0.20, 0.05, 0.20], offset=[-0.01, 0.125, 0.01], color="#fbbf24", finish="matte_wood"),
            ]
        elif any(w in low for w in ("platform", "deck", "stage")):
            cat, fin = "city_architecture", "latex_glossy"
            parts = [
                ObjectPartRecipe(part_name="deck_slab", shape="box", size=[2.1, 0.22, 1.45], offset=[0, 1.04, 0], color="#f472b6", finish="latex_glossy"),
                ObjectPartRecipe(part_name="deck_trim", shape="box", size=[2.18, 0.08, 1.52], offset=[0, 1.15, 0], color="#f9a8d4", finish="latex_glossy"),
                ObjectPartRecipe(part_name="pillar_l", shape="cylinder", size=[0.12, 0.96, 0.12], offset=[-0.82, 0.48, 0], color="#e2e8f0", finish="ceramic"),
                ObjectPartRecipe(part_name="pillar_r", shape="cylinder", size=[0.12, 0.96, 0.12], offset=[0.82, 0.48, 0], color="#e2e8f0", finish="ceramic"),
            ]
        elif any(w in low for w in ("block", "step", "stair", "cube")):
            cat, fin = "sports_games", "latex_glossy"
            parts = [
                ObjectPartRecipe(part_name="block_1", shape="box", size=[0.52, 0.35, 0.65], offset=[-0.75, 0.175, 0], color="#ef4444", finish="latex_glossy"),
                ObjectPartRecipe(part_name="block_2", shape="box", size=[0.52, 0.70, 0.65], offset=[-0.22, 0.35, 0], color="#3b82f6", finish="latex_glossy"),
                ObjectPartRecipe(part_name="block_3", shape="box", size=[0.52, 1.05, 0.65], offset=[0.31, 0.525, 0], color="#facc15", finish="latex_glossy"),
                ObjectPartRecipe(part_name="block_4", shape="box", size=[0.52, 1.40, 0.65], offset=[0.84, 0.70, 0], color="#22c55e", finish="latex_glossy"),
            ]
        elif any(w in low for w in ("candy", "sweet", "lollipop", "gummy", "heart")):
            cat, fin = "party_prank", "latex_glossy"
            parts = [
                ObjectPartRecipe(part_name="candy_1", shape="sphere", size=[0.11, 0.11, 0.11], offset=[-0.24, 0.45, 0.05], color="#f43f5e", finish="latex_glossy"),
                ObjectPartRecipe(part_name="candy_2", shape="sphere", size=[0.10, 0.10, 0.10], offset=[0.0, 0.62, -0.04], color="#a855f7", finish="latex_glossy"),
                ObjectPartRecipe(part_name="candy_3", shape="sphere", size=[0.11, 0.11, 0.11], offset=[0.24, 0.50, 0.06], color="#38bdf8", finish="latex_glossy"),
            ]
        else:
            parts = [
                ObjectPartRecipe(part_name="prop_base", shape="cylinder", size=[0.26, 0.08, 0.26], offset=[0, 0.04, 0], color="#f8fafc", finish="ceramic"),
                ObjectPartRecipe(part_name="prop_body", shape="box", size=[0.32, 0.22, 0.32], offset=[0, 0.19, 0], color="#f59e0b", finish="latex_glossy"),
                ObjectPartRecipe(part_name="prop_accent", shape="sphere", size=[0.11, 0.11, 0.11], offset=[0, 0.36, 0], color="#ef4444", finish="latex_glossy"),
            ]

        return ObjectAnatomySpec(
            object_id=clean_id,
            display_name=clean_id.replace("_", " ").title(),
            category=cat,
            builder_key="generated_builder",
            real_anatomy_parts=[p.part_name for p in parts],
            typical_dimensions_m=[0.7, 1.0, 0.5],
            default_height_m=1.0,
            surface_finish=fin,
            motion_behavior="wind_sway" if "phone" in low else "static",
            placement_layer="ground",
            silhouette_notes=f"Generated real-world multi-part core for '{clean_id}'.",
            aliases=[clean_id, clean_id.replace("_", " ")],
            composite_parts=parts,
        )

    def _write_python_object_core(self, spec: ObjectAnatomySpec) -> Path:
        """Persist a real standalone Python Object Core script (`*_core.py`)."""
        mod_path = self.py_out_dir / f"{spec.object_id}_core.py"
        spec_repr = pprint.pformat(spec.model_dump(), indent=2, sort_dicts=False)
        code = f'''"""
Auto-generated Object Core Module: `{spec.display_name}` (`{spec.object_id}`).
Synthesized autonomously by `MetaCoreSynthesizer` (zero hardcode!).
"""

from core.object_knowledge_core import OBJECT_KNOWLEDGE_BASE, ObjectAnatomySpec

SPEC = ObjectAnatomySpec.model_validate({spec_repr})


def register() -> ObjectAnatomySpec:
    """Register `{spec.object_id}` into the live Object Knowledge Base."""
    OBJECT_KNOWLEDGE_BASE[SPEC.object_id] = SPEC
    return SPEC
'''
        mod_path.write_text(code, encoding="utf-8")
        return mod_path

    def _rebuild_js_runtime_builders(self) -> Path:
        """Regenerate `assets/three/generated/custom_objects.js` with all auto-generated 3D builders."""
        all_specs: Dict[str, ObjectAnatomySpec] = {}
        for oid, spec in OBJECT_KNOWLEDGE_BASE.items():
            if spec.builder_key == "generated_builder" or (self.py_out_dir / f"{oid}_core.py").exists():
                all_specs[oid] = spec

        builder_blocks: List[str] = []
        spec_map: Dict[str, dict] = {}
        for oid, spec in sorted(all_specs.items()):
            spec_map[oid] = spec.model_dump()
            parts_lines = []
            for p in spec.composite_parts:
                sx, sy, sz = (p.size + [0.3, 0.3, 0.3])[:3]
                ox, oy, oz = (p.offset + [0.0, 0.0, 0.0])[:3]
                rx, ry, rz = (p.rotation + [0.0, 0.0, 0.0])[:3]
                col = p.color or "#f8fafc"
                fin = p.finish or spec.surface_finish
                if p.shape == "sphere":
                    geo_expr = f"new THREE.SphereGeometry({sx}, 20, 16)"
                elif p.shape == "cylinder":
                    geo_expr = f"new THREE.CylinderGeometry({sx}, {sz}, {sy}, 18)"
                elif p.shape == "cone":
                    geo_expr = f"new THREE.ConeGeometry({sx}, {sy}, 18)"
                elif p.shape == "torus":
                    geo_expr = f"new THREE.TorusGeometry({sx}, {sy}, 12, 24)"
                elif p.shape == "capsule":
                    geo_expr = f"new THREE.CapsuleGeometry({sx}, {sy}, 8, 12)"
                else:
                    geo_expr = f"new THREE.BoxGeometry({sx}, {sy}, {sz})"
                parts_lines.append(
                    f"    {{\n"
                    f"      const m = new THREE.Mesh({geo_expr}, makeMat('{col}', '{fin}'));\n"
                    f"      m.position.set({ox}, {oy}, {oz});\n"
                    f"      m.rotation.set({rx}, {ry}, {rz});\n"
                    f"      m.castShadow = true; m.receiveShadow = true;\n"
                    f"      g.add(m);\n"
                    f"    }}"
                )
            block = (
                f"  '{oid}': function(THREE, makeMat) {{\n"
                f"    const g = new THREE.Group();\n"
                + "\n".join(parts_lines)
                + "\n    return g;\n  },"
            )
            builder_blocks.append(block)

        js_src = (
            "/**\n"
            " * Auto-generated 3D Object Builders maintained dynamically by `core/meta_core_synthesizer.py`.\n"
            " */\n"
            "export const GENERATED_OBJECT_SPECS = " + json.dumps(spec_map, indent=2) + ";\n\n"
            "export const GENERATED_OBJECT_BUILDERS = {\n"
            + "\n".join(builder_blocks)
            + "\n};\n"
        )
        self.js_out_file.write_text(js_src, encoding="utf-8")
        return self.js_out_file

    def ensure_object_core(self, prop_name: str, scene_context: str = "") -> ObjectAnatomySpec:
        """
        Ensure `prop_name` has a real 3D Object Core (`OBJECT_KNOWLEDGE_BASE` entry + generated script).
        If unseen, autonomously synthesizes and writes `<id>_core.py` + `custom_objects.js`.
        """
        existing = resolve_exact_or_alias_knowledge(prop_name)
        if existing is not None:
            return existing

        clean_id = self._normalize_id(prop_name)
        log_info(f"[MetaCoreSynthesizer] Unseen object detected: '{prop_name}' -> synthesizing new Object Core script...")
        spec = self._synthesize_via_gemini(clean_id, scene_context)
        if spec is None:
            spec = self._semantic_anatomy_fallback(clean_id, scene_context)

        OBJECT_KNOWLEDGE_BASE[clean_id] = spec
        py_file = self._write_python_object_core(spec)
        js_file = self._rebuild_js_runtime_builders()
        log_success(f"[MetaCoreSynthesizer] Auto-created '{py_file.name}' + updated '{js_file.name}' for '{clean_id}' ({len(spec.composite_parts)} parts)")
        return spec

    def ensure_objects_for_scenes(self, scenes: List) -> Dict[str, ObjectAnatomySpec]:
        """Scan every scene in a clip script and synthesize cores for any unseen object props."""
        synthesized: Dict[str, ObjectAnatomySpec] = {}
        for sc in scenes or []:
            ctx = f"{getattr(sc, 'narration', '')} | {getattr(sc, 'ref_scene_action_summary', '')} | {getattr(sc, 'image_prompt', '')}"
            for raw_prop in (getattr(sc, "scene_props", None) or []):
                spec = self.ensure_object_core(str(raw_prop), scene_context=ctx)
                synthesized[spec.object_id] = spec
        return synthesized

