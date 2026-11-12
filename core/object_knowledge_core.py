"""
Core 5: Extensible Real-World Object & Prop Knowledge Engine (`core/object_knowledge_core.py`).

Defines rich semantic, anatomical, material, and physical motion knowledge for 36+ real-world
3D objects (cumulus clouds, latex balloons with teardrop necks & curled ribbons, aerodynamic
commercial jetliners, telescoping hydraulic barber lift chairs, veined heart-shaped tropical leaves,
hollow oak trunks, pinched sausage chains, golden art-deco skyscrapers, sports balls, street lamps,
etc.) plus a data-driven recipe resolver so future objects can be added declaratively and rendered
with realistic silhouettes instead of crude single boxes/spheres.
"""

import re
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


ObjectCategory = Literal[
    "nature_sky",
    "nature_flora",
    "city_architecture",
    "vehicles_flight",
    "furniture_mechanism",
    "food_kitchen",
    "party_prank",
    "water_beach",
    "sports_games",
    "fantasy_scifi",
]

MotionBehavior = Literal[
    "static",
    "buoyant_float",
    "wind_sway",
    "air_cruise",
    "hydraulic_lift",
    "water_bob",
    "portal_spin",
    "flame_flicker",
    "ground_drive",
]

SurfaceFinish = Literal[
    "latex_glossy",
    "fluffy_matte",
    "brushed_chrome",
    "painted_metal",
    "organic_bark",
    "waxy_foliage",
    "glass_facade",
    "glazed_food",
    "matte_wood",
    "ceramic",
    "fabric",
]


class ObjectPartRecipe(BaseModel):
    """Data-driven sub-part recipe used by the generic Three.js assembler for extensible props."""
    part_name: str
    shape: Literal["sphere", "cylinder", "cone", "box", "torus", "capsule", "ring", "lathe_vase"]
    size: List[float] = Field(default_factory=lambda: [0.3, 0.3, 0.3])
    offset: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    rotation: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    color: Optional[str] = None
    finish: SurfaceFinish = "painted_metal"


class ObjectAnatomySpec(BaseModel):
    """Complete real-world geometric, material, and kinetic knowledge for one 3D object type."""
    object_id: str
    display_name: str
    category: ObjectCategory
    builder_key: str
    real_anatomy_parts: List[str]
    typical_dimensions_m: List[float]  # [width, height, depth]
    default_height_m: float
    surface_finish: SurfaceFinish
    motion_behavior: MotionBehavior = "static"
    placement_layer: Literal["ground", "tabletop", "elevated", "sky", "backdrop"] = "ground"
    silhouette_notes: str = ""
    aliases: List[str] = Field(default_factory=list)
    composite_parts: List[ObjectPartRecipe] = Field(default_factory=list)


OBJECT_KNOWLEDGE_BASE: Dict[str, ObjectAnatomySpec] = {
    "cumulus_cloud": ObjectAnatomySpec(
        object_id="cumulus_cloud",
        display_name="Fluffy Cumulus Cloud",
        category="nature_sky",
        builder_key="cumulus_cloud",
        real_anatomy_parts=[
            "flat_condensation_base",
            "central_billowing_dome",
            "lateral_cotton_puffs",
            "warm_sunlit_crown",
        ],
        typical_dimensions_m=[3.2, 1.3, 1.8],
        default_height_m=1.3,
        surface_finish="fluffy_matte",
        motion_behavior="wind_sway",
        placement_layer="sky",
        silhouette_notes="Soft rounded overlapping cotton billows atop a broad flat cloud base; bright pure white with subtle cool underside shading.",
        aliases=["cloud", "clouds", "sky_cloud", "awan"],
    ),
    "balloon_bundle_red": ObjectAnatomySpec(
        object_id="balloon_bundle_red",
        display_name="Red Latex Balloon Cluster",
        category="party_prank",
        builder_key="latex_balloon_cluster",
        real_anatomy_parts=[
            "lathe_teardrop_latex_crown",
            "tapered_balloon_neck",
            "tied_rubber_lip_knot",
            "curled_ribbon_tube_string",
            "specular_clearcoat_highlight",
        ],
        typical_dimensions_m=[0.75, 1.35, 0.55],
        default_height_m=1.35,
        surface_finish="latex_glossy",
        motion_behavior="buoyant_float",
        placement_layer="elevated",
        silhouette_notes="Real pear-teardrop latex contour (never a plain rigid sphere on a stick!) with pinched tied knot and gentle sinuous curved string.",
        aliases=["red_balloon", "balloon", "balloons", "balon"],
    ),
    "balloon_bunch": ObjectAnatomySpec(
        object_id="balloon_bunch",
        display_name="Festive Multi-Color Latex Balloon Bouquet",
        category="party_prank",
        builder_key="latex_balloon_cluster",
        real_anatomy_parts=[
            "lathe_teardrop_envelopes",
            "tied_knots",
            "converging_curled_strings",
        ],
        typical_dimensions_m=[0.95, 1.95, 0.75],
        default_height_m=1.95,
        surface_finish="latex_glossy",
        motion_behavior="buoyant_float",
        placement_layer="ground",
        silhouette_notes="Staggered bouquet of glossy teardrop latex balloons tethered by curved ribbons.",
        aliases=["party_balloons", "balloon_bouquet"],
    ),
    "flying_airplane": ObjectAnatomySpec(
        object_id="flying_airplane",
        display_name="Commercial Jet Airliner",
        category="vehicles_flight",
        builder_key="airliner_jet",
        real_anatomy_parts=[
            "aerodynamic_radome_nose",
            "cylindrical_pressurized_fuselage",
            "cockpit_windshield_visormask",
            "cabin_window_strip",
            "swept_main_wings_with_winglets",
            "twin_underwing_turbofan_nacelles",
            "swept_vertical_tail_fin",
            "horizontal_tail_stabilizers",
        ],
        typical_dimensions_m=[4.2, 1.15, 3.8],
        default_height_m=1.15,
        surface_finish="painted_metal",
        motion_behavior="air_cruise",
        placement_layer="sky",
        silhouette_notes="Streamlined tapered fuselage, swept-back airfoil wings with upturned winglets, under-wing jet turbines, and clean empennage.",
        aliases=["airplane", "plane", "jet", "airliner", "pesawat"],
    ),
    "hydraulic_lift_chair": ObjectAnatomySpec(
        object_id="hydraulic_lift_chair",
        display_name="Hydraulic Telescoping Lift Chair",
        category="furniture_mechanism",
        builder_key="hydraulic_lift_chair",
        real_anatomy_parts=[
            "heavy_steel_base_plate",
            "pivoted_foot_pump_pedal",
            "two_stage_chrome_hydraulic_cylinder",
            "wide_upholstered_seat_cushion",
            "contoured_backrest_and_headrest",
            "chrome_outer_armrests",
        ],
        typical_dimensions_m=[1.05, 1.25, 0.95],
        default_height_m=1.25,
        surface_finish="brushed_chrome",
        motion_behavior="hydraulic_lift",
        placement_layer="ground",
        silhouette_notes="Wide leather barber/salon swivel chair (>0.78m seat clearance so arms never clip armrests) mounted over a two-stage chrome telescopic piston & foot pedal.",
        aliases=["lift_chair", "barber_chair", "hydraulic_chair", "elevator_chair"],
    ),
    "skyscraper_city": ObjectAnatomySpec(
        object_id="skyscraper_city",
        display_name="Golden Art-Deco Skyscraper Skyline",
        category="city_architecture",
        builder_key="golden_skyline",
        real_anatomy_parts=[
            "podium_lobby_bases",
            "stepped_tower_setbacks",
            "illuminated_curtain_wall_windows",
            "rooftop_crown_parapets",
            "spire_antennas",
        ],
        typical_dimensions_m=[16.0, 24.0, 10.0],
        default_height_m=22.0,
        surface_finish="glass_facade",
        motion_behavior="static",
        placement_layer="backdrop",
        silhouette_notes="Multi-tiered golden glass towers with architectural setbacks, rooftop crowns, and dense illuminated window rows.",
        aliases=["skyscrapers", "city_buildings", "golden_towers"],
    ),
    "hollow_tree_trunk": ObjectAnatomySpec(
        object_id="hollow_tree_trunk",
        display_name="Hollow Ancient Oak Tree",
        category="nature_flora",
        builder_key="hollow_oak_tree",
        real_anatomy_parts=[
            "flared_root_buttresses",
            "textured_bark_trunk",
            "arched_bark_rimmed_hollow_cavity",
            "billowing_multi_puff_leaf_canopy",
        ],
        typical_dimensions_m=[3.2, 4.4, 3.0],
        default_height_m=4.4,
        surface_finish="organic_bark",
        motion_behavior="wind_sway",
        placement_layer="ground",
        silhouette_notes="Root-flared tree trunk with recessed dark hollow nook framed by thick bark lip and lush multi-sphere foliage crown.",
        aliases=["hollow_tree", "tree_hole", "tree_trunk"],
    ),
    "oak_tree": ObjectAnatomySpec(
        object_id="oak_tree",
        display_name="Lush Forest Oak Tree",
        category="nature_flora",
        builder_key="stylized_forest_tree",
        real_anatomy_parts=[
            "flared_root_base",
            "branching_tapered_trunk",
            "layered_foliage_clusters",
        ],
        typical_dimensions_m=[2.2, 3.6, 2.2],
        default_height_m=3.6,
        surface_finish="organic_bark",
        motion_behavior="wind_sway",
        placement_layer="ground",
        silhouette_notes="Clean organic trunk with forked limbs and multi-puff rounded canopy; zero jagged flat strips.",
        aliases=["tree", "forest_tree", "pine_tree", "palm_tree", "pohon", "large_tree_trunk", "tree_trunk"],
    ),
    "jungle_giant_leaf": ObjectAnatomySpec(
        object_id="jungle_giant_leaf",
        display_name="Tropical Giant Elephant-Ear Leaf",
        category="nature_flora",
        builder_key="tropical_giant_leaf",
        real_anatomy_parts=[
            "heart_lobed_leaf_blade",
            "tapered_midrib_vein",
            "angled_lateral_veins",
            "curved_petiole_stem",
        ],
        typical_dimensions_m=[2.1, 0.14, 1.5],
        default_height_m=0.14,
        surface_finish="waxy_foliage",
        motion_behavior="static",
        placement_layer="ground",
        silhouette_notes="Pointed heart-shaped tropical leaf silhouette with arched surface, central midrib, lateral veins, and stem.",
        aliases=["giant_leaf", "leaf", "daun"],
    ),
    "sausage_prop": ObjectAnatomySpec(
        object_id="sausage_prop",
        display_name="Glazed Link Sausage Chain on Plate",
        category="food_kitchen",
        builder_key="sausage_on_plate",
        real_anatomy_parts=[
            "rimmed_ceramic_plate",
            "pinched_casing_links",
            "twisted_link_ends",
            "glossy_cooked_glaze",
        ],
        typical_dimensions_m=[0.64, 0.16, 0.64],
        default_height_m=0.16,
        surface_finish="glazed_food",
        motion_behavior="static",
        placement_layer="ground",
        silhouette_notes="Curved chain of plump pinched cartoon sausages resting neatly on a contoured white ceramic plate.",
        aliases=["sausage", "sausages", "hotdog", "sosis"],
    ),
    "ocean_water_plane": ObjectAnatomySpec(
        object_id="ocean_water_plane",
        display_name="Sunlit Ocean Water Surface",
        category="water_beach",
        builder_key="ocean_water_plane",
        real_anatomy_parts=["translucent_water_sheet", "foam_shore_bands"],
        typical_dimensions_m=[50.0, 0.2, 26.0],
        default_height_m=0.2,
        surface_finish="glass_facade",
        motion_behavior="water_bob",
        placement_layer="ground",
        silhouette_notes="Reflective sky-blue translucent water surface.",
        aliases=["ocean", "sea", "water"],
    ),
    "soccer_ball": ObjectAnatomySpec(
        object_id="soccer_ball",
        display_name="Classic Soccer Ball",
        category="sports_games",
        builder_key="soccer_ball",
        real_anatomy_parts=["icosahedral_panel_sphere", "pentagon_patch_texture"],
        typical_dimensions_m=[0.32, 0.32, 0.32],
        default_height_m=0.32,
        surface_finish="latex_glossy",
        motion_behavior="water_bob",
        placement_layer="ground",
        silhouette_notes="High-contrast black-and-white patterned paneled football.",
        aliases=["football", "soccer", "ball", "bola"],
    ),
    "street_lamp": ObjectAnatomySpec(
        object_id="street_lamp",
        display_name="Ornate City Street Lamp",
        category="city_architecture",
        builder_key="composite_recipe",
        real_anatomy_parts=["cast_iron_plinth", "tapered_post", "curved_arm", "glowing_lantern_globe"],
        typical_dimensions_m=[0.5, 3.2, 0.6],
        default_height_m=3.2,
        surface_finish="painted_metal",
        motion_behavior="static",
        placement_layer="ground",
        silhouette_notes="Classic lamppost with tapered column, curved bracket, and warm glowing lantern head.",
        aliases=["lamppost", "lamp_post", "streetlight"],
        composite_parts=[
            ObjectPartRecipe(part_name="plinth", shape="cylinder", size=[0.18, 0.35, 0.14], offset=[0, 0.175, 0], color="#1e293b", finish="painted_metal"),
            ObjectPartRecipe(part_name="pole", shape="cylinder", size=[0.06, 2.75, 0.08], offset=[0, 1.55, 0], color="#334155", finish="painted_metal"),
            ObjectPartRecipe(part_name="arm", shape="box", size=[0.42, 0.07, 0.07], offset=[0.18, 2.90, 0], color="#334155", finish="painted_metal"),
            ObjectPartRecipe(part_name="globe", shape="sphere", size=[0.18, 0.22, 0.18], offset=[0.36, 2.76, 0], color="#fef08a", finish="glass_facade"),
        ],
    ),
    "hot_air_balloon": ObjectAnatomySpec(
        object_id="hot_air_balloon",
        display_name="Striped Hot Air Balloon",
        category="vehicles_flight",
        builder_key="composite_recipe",
        real_anatomy_parts=["teardrop_envelope", "suspension_cables", "woven_wicker_basket"],
        typical_dimensions_m=[2.2, 3.4, 2.2],
        default_height_m=3.4,
        surface_finish="fabric",
        motion_behavior="buoyant_float",
        placement_layer="sky",
        silhouette_notes="Large colorful balloon envelope suspending a woven wicker gondola.",
        aliases=["air_balloon", "balon_udara"],
        composite_parts=[
            ObjectPartRecipe(part_name="envelope", shape="sphere", size=[1.05, 1.35, 1.05], offset=[0, 2.15, 0], color="#ef4444", finish="fabric"),
            ObjectPartRecipe(part_name="crown_band", shape="torus", size=[0.96, 0.12, 0.96], offset=[0, 2.15, 0], rotation=[1.57, 0, 0], color="#facc15", finish="fabric"),
            ObjectPartRecipe(part_name="burner_collar", shape="cone", size=[0.45, 0.55, 0.45], offset=[0, 1.0, 0], rotation=[3.14, 0, 0], color="#f97316", finish="fabric"),
            ObjectPartRecipe(part_name="basket", shape="box", size=[0.55, 0.42, 0.55], offset=[0, 0.25, 0], color="#92400e", finish="matte_wood"),
        ],
    ),
}

# Register standard interactive props so lookup always returns rich structured knowledge
_STANDARD_PROP_DEFS = [
    ("inflatable_pool", "Backyard Inflatable Pool", "water_beach", "inflatable_pool", ["ribbed_vinyl_rings", "water_basin", "owner_emblem"], [1.85, 0.48, 1.85], "latex_glossy", "water_bob", ["pool"]),
    ("water_slide", "Waterpark Slide", "water_beach", "water_slide", ["ladder_tower", "curved_chute", "canopy_roof"], [1.4, 2.8, 2.8], "latex_glossy", "static", ["slide"]),
    ("cage_trap", "Steel Bar Cage Trap", "fantasy_scifi", "cage_trap", ["steel_base", "vertical_prison_bars", "padlock_hasp"], [1.15, 1.5, 1.15], "brushed_chrome", "static", ["cage"]),
    ("mystery_table", "Cloche Banquet Table", "food_kitchen", "mystery_table", ["draped_tablecloth", "turned_legs", "silver_serving_cloche"], [1.55, 1.1, 0.85], "ceramic", "static", ["mystery_table", "banquet_cloche", "cloche"]),
    ("treasure_chest", "Golden Pirated Treasure Chest", "fantasy_scifi", "treasure_chest", ["oak_chest_box", "brass_straps", "vaulted_lid", "gold_ingot_pile"], [1.0, 0.72, 0.68], "matte_wood", "static", ["chest", "treasure"]),
    ("park_bench", "Slatted Timber Park Bench", "city_architecture", "park_bench", ["cast_legs", "wooden_seat_slats", "slatted_backrest"], [1.55, 0.88, 0.65], "matte_wood", "static", ["bench"]),
    ("race_finish_arch", "Checkered Race Finish Arch", "sports_games", "race_finish_arch", ["side_pylons", "checkered_banner_beam"], [3.1, 2.25, 0.45], "painted_metal", "static", ["finish_arch", "finish_line"]),
    ("magic_portal", "Swirling Magic Portal Ring", "fantasy_scifi", "magic_portal", ["stone_pedestal", "runic_torus_frame", "energy_vortex_disc"], [2.2, 2.5, 0.55], "glass_facade", "portal_spin", ["portal"]),
    ("control_pedestal", "Interactive Control Console", "furniture_mechanism", "control_pedestal", ["tapered_column", "angled_desk_top", "dome_push_buttons"], [0.55, 1.1, 0.55], "painted_metal", "static", ["pedestal", "button_console"]),
    ("gift_box_pile", "Ribbon-Wrapped Gift Box Stack", "party_prank", "gift_box_pile", ["cardboard_cubes", "satin_ribbon_crosses", "top_bow"], [1.1, 0.95, 0.9], "fabric", "static", ["gift", "present"]),
    ("obstacle_hurdle", "Track Obstacle Hurdle", "sports_games", "obstacle_hurdle", ["side_feet", "vertical_posts", "striped_top_bar"], [1.6, 0.95, 0.45], "painted_metal", "static", ["hurdle"]),
    ("campfire_ring", "Stone Ring Campfire", "nature_flora", "campfire_ring", ["cobblestone_circle", "crossed_firewood_logs", "layered_flames"], [1.1, 0.65, 1.1], "organic_bark", "flame_flicker", ["campfire", "fire"]),
    ("stage_podium", "Champion Awards Podium", "sports_games", "stage_podium", ["tiered_123_steps", "gold_trim"], [2.1, 0.85, 0.9], "painted_metal", "static", ["podium"]),
    ("bridge_span", "Wooden Plank Bridge Span", "city_architecture", "bridge_span", ["arched_deck_planks", "rope_handrail_posts"], [2.4, 0.95, 1.4], "matte_wood", "static", ["bridge"]),
    ("book_and_coin_stacks", "Hardcover Books & Gold Coins", "fantasy_scifi", "book_and_coin_stacks", ["bound_book_volumes", "gold_coin_cylinders"], [1.6, 0.85, 1.0], "matte_wood", "static", ["books", "coins"]),
    ("color_archways", "Triple Colored Doorway Arches", "city_architecture", "color_archways", ["masonry_pillars", "arched_portals", "lintel_beam"], [4.0, 1.45, 0.7], "matte_wood", "static", ["arches"]),
    ("color_cubes", "GiantToy Color Cubes & Gem", "party_prank", "color_cubes", ["beveled_color_blocks", "floating_heart_crystal"], [2.2, 0.65, 0.8], "latex_glossy", "portal_spin", ["cubes"]),
    ("trophy_display", "Golden Championship Trophy Pedestal", "sports_games", "trophy_display", ["marble_plinth", "fluted_stem", "gilded_chalice_bowl", "twin_handles"], [0.75, 1.35, 0.75], "brushed_chrome", "static", ["trophy"]),
    ("beach_umbrella", "Striped Beach Parasol Umbrella", "water_beach", "carousel_umbrella", ["wooden_pole", "ribbed_scallop_canopy"], [2.2, 2.2, 2.2], "fabric", "wind_sway", ["umbrella"]),
    ("carousel_tent", "Striped Carnival Circus Tent", "party_prank", "carousel_umbrella", ["center_mast", "scalloped_conical_bigtop"], [2.4, 2.4, 2.4], "fabric", "wind_sway", ["tent", "carnival_tent"]),
    ("ground_plaza_ring", "Checkered Plaza Medallion", "city_architecture", "ground_plaza_ring", ["outer_curb_ring", "center_medallion"], [1.7, 0.04, 1.7], "ceramic", "static", ["plaza_ring"]),
    # Interior / Prank / Puzzle / Action Viral Prop Knowledge
    ("giant_cockroach", "Giant Cartoon Cockroach", "party_prank", "giant_cockroach", ["segmented_carapace", "pronotum_shield", "twin_sweeping_antennae", "six_jointed_legs"], [0.68, 0.42, 0.95], "latex_glossy", "water_bob", ["cockroach", "bug", "roach", "insect", "kecoa"]),
    ("cooking_pot", "Brushed Stainless Stockpot", "food_kitchen", "cooking_pot", ["cylindrical_steel_pot", "rolled_rim", "twin_loop_handles", "domed_lid_knob"], [0.58, 0.48, 0.58], "brushed_chrome", "static", ["pot", "silver pot", "pan", "kettle", "panci"]),
    ("cleaning_broom", "Long-Handled Floor Broom", "furniture_mechanism", "cleaning_broom", ["painted_handle_pole", "angled_cap_shroud", "sweeping_bristle_bundle"], [0.46, 1.45, 0.18], "matte_wood", "static", ["broom", "mop", "sapu"]),
    ("computer_desk", "Gaming PC Desk & Chair", "furniture_mechanism", "computer_desk", ["oak_tabletop", "widescreen_game_monitor", "keyboard_mouse_pad", "ergonomic_gaming_chair"], [1.65, 1.45, 1.15], "matte_wood", "static", ["computer", "desk", "monitor", "computer_monitor", "gaming pc", "laptop", "pc", "komputer"]),
    ("stone_maze_walls", "Carved Stone Labyrinth Walls", "city_architecture", "stone_maze_walls", ["stone_masonry_blocks", "corridor_pillars", "mossy_mortar_cap"], [6.8, 1.85, 5.4], "ceramic", "static", ["maze", "labyrinth", "maze walls", "stone walls", "labirin"]),
    ("laser_beam", "Glowing Sci-Fi Laser Barrier", "fantasy_scifi", "laser_beam", ["turret_emitter", "incandescent_core_ray", "additive_plasma_aura"], [3.6, 0.55, 0.55], "glass_facade", "portal_spin", ["laser", "laser beam", "red laser", "blue laser", "beam"]),
    ("hero_shield", "Concentric Star Superhero Shield", "sports_games", "hero_shield", ["domed_alloy_disc", "concentric_rings", "five_point_star_emblem"], [0.88, 0.88, 0.22], "brushed_chrome", "water_bob", ["shield", "hero shield", "captain shield", "perisai"]),
    ("angry_bull", "Horned Guardian Bull Prop", "fantasy_scifi", "angry_bull", ["muscular_shoulders", "broad_snout", "gold_nose_ring", "curved_ivory_horns", "glowing_eyes"], [1.15, 1.25, 1.05], "painted_metal", "static", ["bull", "banteng", "minotaur", "beast"]),
    ("camouflage_bush", "Dense Leafy Camouflage Bush", "nature_flora", "camouflage_bush", ["layered_leaf_clusters", "branch_tuck_base"], [1.45, 1.15, 1.35], "waxy_foliage", "wind_sway", ["bush", "bushes", "camouflage", "shrub", "semak"]),
    ("strength_orb", "Glowing Strength Power-Up Orb", "fantasy_scifi", "strength_orb", ["holographic_cyan_halo", "floating_gold_dumbbell_core"], [0.75, 0.95, 0.75], "glass_facade", "portal_spin", ["strength", "power-up", "powerup", "muscle", "orb"]),
    # Musical Staircase, Dessert, Street Brick Wall, Folding Patio Chair, Pickup Truck & Drumstick Props
    ("musical_staircase", "Rainbow Musical Staircase Steps", "city_architecture", "musical_staircase", ["rainbow_ascending_piano_steps", "letter_block_risers", "platform_top"], [3.6, 1.85, 1.2], "latex_glossy", "static", ["colored_steps", "musical_steps", "staircase", "rainbow_stairs", "letter_blocks", "step_blocks", "piano_stairs"]),
    ("musical_note", "Floating 3D Musical Note", "party_prank", "musical_note", ["glossy_notehead", "vertical_stem", "curved_flag"], [0.55, 0.85, 0.35], "latex_glossy", "wind_sway", ["musical_note", "musical_note_hearts", "music_note", "high_note", "note"]),
    ("macarons", "Floating Pastel French Macarons", "food_kitchen", "macarons", ["domed_almond_shells", "creamy_filling_band"], [1.45, 0.45, 0.65], "glazed_food", "wind_sway", ["macaron", "macarons", "macaroons"]),
    ("giant_turkey_leg", "Glazed Giant Turkey Drumstick", "food_kitchen", "giant_turkey_leg", ["roasted_meat_bulb", "caramel_glaze", "white_leg_bone", "twin_knuckles"], [0.65, 0.45, 0.95], "glazed_food", "static", ["giant_turkey_leg", "turkey_leg", "giant_meat", "meat_leg", "drumstick", "roast_meat", "meat"]),
    ("folding_chair", "Outdoor Patio Folding Chair", "furniture_mechanism", "folding_chair", ["tubular_aluminum_legs", "slatted_canvas_seat", "tilted_backrest"], [0.65, 0.88, 0.68], "painted_metal", "static", ["folding_chair", "lawn_chair", "patio_chair", "camping_chair"]),
    ("brick_wall", "Red Clay Brick Courtyard Wall", "city_architecture", "brick_wall", ["terracotta_masonry_courses", "mortar_joints", "stone_coping_cap"], [3.4, 1.98, 0.65], "ceramic", "static", ["brick_wall", "red_brick_wall", "courtyard_wall"]),
    ("pickup_truck", "Black Open-Bed Pickup Truck", "vehicles_flight", "pickup_truck", ["gloss_cab_hood", "tinted_windshield", "open_cargo_truck_bed", "four_wheels"], [3.4, 1.48, 1.65], "painted_metal", "static", ["pickup_truck", "truck_bed", "black_truck", "truck"]),
]

for oid, dname, cat, bkey, parts, dims, fin, mot, als in _STANDARD_PROP_DEFS:
    OBJECT_KNOWLEDGE_BASE[oid] = ObjectAnatomySpec(
        object_id=oid,
        display_name=dname,
        category=cat,  # type: ignore[arg-type]
        builder_key=bkey,
        real_anatomy_parts=parts,
        typical_dimensions_m=dims,
        default_height_m=dims[1],
        surface_finish=fin,  # type: ignore[arg-type]
        motion_behavior=mot,  # type: ignore[arg-type]
        silhouette_notes=f"{dname}: built with anatomical parts ({', '.join(parts)}).",
        aliases=als,
    )

# Declarative everyday composite objects
OBJECT_KNOWLEDGE_BASE["skateboard"] = ObjectAnatomySpec(
    object_id="skateboard",
    display_name="Trick Stunt Skateboard",
    category="sports_games",
    builder_key="composite_recipe",
    real_anatomy_parts=["maple_deck", "kick_tails", "aluminum_trucks", "urethane_wheels"],
    typical_dimensions_m=[0.85, 0.16, 0.28],
    default_height_m=0.16,
    surface_finish="matte_wood",
    silhouette_notes="Curved skateboard deck atop dual metal trucks and four glossy urethane wheels.",
    aliases=["skate", "board"],
    composite_parts=[
        ObjectPartRecipe(part_name="deck", shape="box", size=[0.82, 0.04, 0.26], offset=[0, 0.10, 0], color="#ef4444", finish="painted_metal"),
        ObjectPartRecipe(part_name="wheel_fl", shape="cylinder", size=[0.045, 0.04, 0.045], offset=[0.28, 0.045, 0.12], rotation=[1.57, 0, 0], color="#facc15", finish="latex_glossy"),
        ObjectPartRecipe(part_name="wheel_fr", shape="cylinder", size=[0.045, 0.04, 0.045], offset=[0.28, 0.045, -0.12], rotation=[1.57, 0, 0], color="#facc15", finish="latex_glossy"),
        ObjectPartRecipe(part_name="wheel_rl", shape="cylinder", size=[0.045, 0.04, 0.045], offset=[-0.28, 0.045, 0.12], rotation=[1.57, 0, 0], color="#facc15", finish="latex_glossy"),
        ObjectPartRecipe(part_name="wheel_rr", shape="cylinder", size=[0.045, 0.04, 0.045], offset=[-0.28, 0.045, -0.12], rotation=[1.57, 0, 0], color="#facc15", finish="latex_glossy"),
    ],
)
OBJECT_KNOWLEDGE_BASE["sofa_couch"] = ObjectAnatomySpec(
    object_id="sofa_couch",
    display_name="Plush Living Room Sofa",
    category="furniture_mechanism",
    builder_key="composite_recipe",
    real_anatomy_parts=["padded_seat_cushions", "high_backrest", "rolled_armrests"],
    typical_dimensions_m=[1.85, 0.85, 0.85],
    default_height_m=0.85,
    surface_finish="fabric",
    silhouette_notes="Plush upholstered 2-seat sofa with high padded backrest and chunky twin armrests.",
    aliases=["sofa", "couch", "armchair"],
    composite_parts=[
        ObjectPartRecipe(part_name="base", shape="box", size=[1.75, 0.34, 0.78], offset=[0, 0.22, 0], color="#3b82f6", finish="fabric"),
        ObjectPartRecipe(part_name="backrest", shape="box", size=[1.75, 0.54, 0.22], offset=[0, 0.56, -0.28], color="#2563eb", finish="fabric"),
        ObjectPartRecipe(part_name="arm_l", shape="box", size=[0.22, 0.44, 0.82], offset=[-0.82, 0.34, 0], color="#1d4ed8", finish="fabric"),
        ObjectPartRecipe(part_name="arm_r", shape="box", size=[0.22, 0.44, 0.82], offset=[0.82, 0.34, 0], color="#1d4ed8", finish="fabric"),
    ],
)


OBJECT_KNOWLEDGE_BASE["branch_stick"] = ObjectAnatomySpec(
    object_id="branch_stick",
    display_name="Leafy Tree Branch Stick",
    category="nature_flora",
    builder_key="composite_recipe",
    real_anatomy_parts=["wooden_branch", "leaf_twig"],
    typical_dimensions_m=[0.95, 0.25, 0.25],
    default_height_m=0.25,
    surface_finish="organic_bark",
    silhouette_notes="Slender brown wooden tree branch with small green leaf cluster.",
    aliases=["branch", "stick", "poking_stick", "twig"],
    composite_parts=[
        ObjectPartRecipe(part_name="twig", shape="cylinder", size=[0.04, 1.15, 0.05], offset=[0, 1.25, 0], rotation=[0.4, 0, 1.25], color="#78350f", finish="organic_bark"),
        ObjectPartRecipe(part_name="leaf", shape="sphere", size=[0.14, 0.14, 0.14], offset=[0.45, 1.45, 0], color="#22c55e", finish="waxy_foliage"),
    ],
)


def synthesize_dynamic_object_recipe(prop_name_or_hint: str) -> ObjectAnatomySpec:
    """
    Zero-hardcode extensible fallback: synthesizes a multi-part composite 3D recipe
    for ANY unseen object name using semantic token heuristics so novel props never vanish.
    """
    clean_id = re.sub(r"[\s\-]+", "_", (prop_name_or_hint or "mystery_prop").strip().lower())
    low = clean_id.replace("_", " ")
    color = "#3b82f6"
    finish: SurfaceFinish = "painted_metal"
    if any(w in low for w in ("gold", "coin", "trophy", "crown", "yellow", "banana", "Cheese")):
        color, finish = "#facc15", "brushed_chrome"
    elif any(w in low for w in ("red", "fire", "apple", "strawberry", "ruby")):
        color, finish = "#ef4444", "latex_glossy"
    elif any(w in low for w in ("green", "leaf", "plant", "frog", "slime")):
        color, finish = "#22c55e", "waxy_foliage"
    elif any(w in low for w in ("wood", "crate", "door", "fence", "stick", "log")):
        color, finish = "#92400e", "matte_wood"
    elif any(w in low for w in ("steel", "metal", "iron", "silver", "robot")):
        color, finish = "#cbd5e1", "brushed_chrome"
    elif any(w in low for w in ("glow", "crystal", "diamond", "gem", "magic", "neon")):
        color, finish = "#38bdf8", "glass_facade"

    # Token-smart semantic geometry rather than a generic blue capsule totem
    if any(w in low for w in ("step", "stair", "block", "cube", "platform")):
        parts = [
            ObjectPartRecipe(part_name="step1", shape="box", size=[0.55, 0.28, 0.65], offset=[-0.55, 0.14, 0], color="#ef4444", finish="latex_glossy"),
            ObjectPartRecipe(part_name="step2", shape="box", size=[0.55, 0.56, 0.65], offset=[0.0, 0.28, 0], color="#facc15", finish="latex_glossy"),
            ObjectPartRecipe(part_name="step3", shape="box", size=[0.55, 0.84, 0.65], offset=[0.55, 0.42, 0], color="#22c55e", finish="latex_glossy"),
        ]
    elif any(w in low for w in ("wall", "barrier", "brick", "fence")):
        parts = [
            ObjectPartRecipe(part_name="wall_body", shape="box", size=[2.8, 1.65, 0.42], offset=[0, 0.825, 0], color="#b91c1c", finish="ceramic"),
            ObjectPartRecipe(part_name="coping", shape="box", size=[2.9, 0.12, 0.48], offset=[0, 1.70, 0], color="#cbd5e1", finish="ceramic"),
        ]
    elif any(w in low for w in ("car", "truck", "van", "bus", "vehicle")):
        parts = [
            ObjectPartRecipe(part_name="chassis", shape="box", size=[2.2, 0.55, 1.05], offset=[0, 0.50, 0], color="#1e293b", finish="painted_metal"),
            ObjectPartRecipe(part_name="cabin", shape="box", size=[1.15, 0.52, 0.98], offset=[-0.35, 1.00, 0], color="#0f172a", finish="glass_facade"),
        ]
    else:
        parts = [
            ObjectPartRecipe(part_name="crate", shape="box", size=[0.56, 0.46, 0.56], offset=[0, 0.23, 0], color="#b45309", finish="matte_wood"),
            ObjectPartRecipe(part_name="lid", shape="box", size=[0.60, 0.08, 0.60], offset=[0, 0.49, 0], color=color, finish=finish),
        ]

    return ObjectAnatomySpec(
        object_id=clean_id,
        display_name=clean_id.replace("_", " ").title(),
        category="party_prank",
        builder_key="composite_recipe",
        real_anatomy_parts=["base_structure", "primary_body", "top_detail"],
        typical_dimensions_m=[0.75, 0.85, 0.75],
        default_height_m=0.85,
        surface_finish=finish,
        motion_behavior="static",
        silhouette_notes=f"Synthesized multi-part 3D silhouette for '{clean_id}'.",
        aliases=[low],
        composite_parts=parts,
    )


def resolve_exact_or_alias_knowledge(prop_name_or_hint: str) -> Optional[ObjectAnatomySpec]:
    """
    Look up real-world object knowledge by exact `prop_type`, alias, or whole-word match.
    Returns `None` if genuinely unseen so `MetaCoreSynthesizer` can generate a real persistent core.
    """
    if not prop_name_or_hint:
        return None
    norm = re.sub(r"[\s\-]+", "_", prop_name_or_hint.strip().lower())
    if norm in OBJECT_KNOWLEDGE_BASE:
        return OBJECT_KNOWLEDGE_BASE[norm]
    for spec in OBJECT_KNOWLEDGE_BASE.values():
        if norm in [a.lower() for a in spec.aliases]:
            return spec
    for spec in OBJECT_KNOWLEDGE_BASE.values():
        if any(re.search(r"\b" + re.escape(a.replace("_", " ")) + r"\b", prop_name_or_hint.lower()) for a in [spec.object_id, *spec.aliases]):
            return spec
    return None


def resolve_object_knowledge(prop_name_or_hint: str) -> Optional[ObjectAnatomySpec]:
    """
    Look up real-world object knowledge by exact `prop_type`, alias, or normalized token match,
    synthesizing a semantic multi-part recipe dynamically for any unseen custom prop.
    """
    found = resolve_exact_or_alias_knowledge(prop_name_or_hint)
    if found is not None:
        return found
    norm = re.sub(r"[\s\-]+", "_", (prop_name_or_hint or "").strip().lower())
    return synthesize_dynamic_object_recipe(norm)


def export_knowledge_for_props(prop_types: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Export compact JSON-serializable knowledge recipes for Three.js `object_library.js`,
    always including `cumulus_cloud` & `oak_tree` plus all active scene props.
    """
    wanted = list(dict.fromkeys(["cumulus_cloud", "oak_tree", *prop_types]))
    manifest: Dict[str, Dict[str, Any]] = {}
    for pt in wanted:
        spec = resolve_object_knowledge(pt)
        if spec:
            manifest[pt] = spec.model_dump()
    return manifest

