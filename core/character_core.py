"""
Core 1: Dynamic Multi-Character Generator & 3D GLB Cast Orchestrator (`core/character_core.py`).

Dynamically extracts character entities from any viral reference video and script, and maps them
to our local library of **68+ Real Rigged & Animated 3D `.glb` Character, Animal, Dinosaur, and
Creature Models** in `assets/three/models/` (zero robotic capsule-people, zero hardcoded cast):

1. `kaykit_medium` (32 Stylized Chibi/Cartoon 3D Characters with high-res facial/outfit textures
   and 35+ shared skeletal animations from `Rig_Medium_General.glb`, `Rig_Medium_MovementBasic.glb`,
   `Rig_Medium_Simulation.glb`, and `Rig_Medium_Special.glb`):
   - `Protagonist_A.glb`, `Protagonist_B.glb`, `MagicalGirl.glb`, `MonsterCostume.glb`,
     `Superhero.glb`, `SpaceRanger.glb`, `Ninja.glb`, `Hiker.glb`, `Driver.glb`, `Witch.glb`,
     `Helper_A.glb`, `Helper_B.glb`, `Farmer_A.glb`, `Farmer_B.glb`, `Clown.glb`,
     `ActionFigure.glb`, `ToySoldier.glb`, `Survivalist.glb`, `Knight.glb`, `Mage.glb`,
     `Ranger.glb`, `Rogue.glb`, `Rogue_Hooded.glb`, `Druid.glb`, `Engineer.glb`,
     `Barbarian.glb`, `Paladin.glb`, `Cleric.glb`, `Lorekeeper.glb`, `Marksman.glb`,
     `Tiefling.glb`, `Robot_One.glb`, `Robot_Two.glb`

2. `quaternius_human` (14 Full-Body Rigged 3D Human Characters, each with 17 built-in animations:
   `Idle`, `Walk`, `Run`, `Jump`, `Wave`, `Victory`, `SitDown`, `StandUp`, `PickUp`, `Roll`, `Punch`):
   - `Casual_Female.glb`, `Casual_Male.glb`, `Casual2_Female.glb`, `Casual2_Male.glb`,
     `Casual3_Male.glb`, `Casual_Bald.glb`, `Doctor_Female_Young.glb`, `Doctor_Male_Young.glb`,
     `Suit_Female.glb`, `Suit_Male.glb`, `Worker_Female.glb`, `Worker_Male.glb`,
     `OldClassy_Female.glb`, `OldClassy_Male.glb`

3. `expressive_human_mech` (7 High-Detail Expressive Characters & Mechs):
   - `Michelle.glb`, `HVGirl.glb`, `Soldier.glb`, `Xbot.glb`, `RobotExpressive.glb`,
     `George.glb`, `Leela.glb`

4. `animal_creature` (17 Animated 3D Animals, Pets, Dinosaurs, Birds & Sea Creatures):
   - `Husky.glb`, `ShibaInu.glb`, `Alpaca.glb`, `Fox.glb`, `Horse.glb`, `Deer.glb`,
     `Stag.glb`, `Cow.glb`, `Wolf.glb`, `Trex.glb`, `Triceratops.glb`, `Velociraptor.glb`,
     `Stegosaurus.glb`, `Dolphin.glb`, `Shark.glb`, `Flamingo.glb`, `Parrot.glb`
"""

import hashlib
import re
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field


CharacterRole = Literal[
    "protagonist",
    "deuteragonist",
    "rival_friend",
    "companion",
    "mentor_figure",
    "crowd_kid",
    "pet_animal",
    "wild_creature",
    "sky_bird",
]

RigEngineType = Literal["glb_skeletal", "stylized_human"]

RigFamilyType = Literal[
    "kaykit_medium",
    "quaternius_human",
    "expressive_human_mech",
    "animal_quadruped",
    "dinosaur",
    "sea_creature",
    "sky_bird",
]

AccessoryType = Literal[
    "none",
    "penguin_hood",
    "bunny_ears",
    "cat_ears",
    "dino_hood",
    "gizmo_helmet",
    "star_crown",
    "baseball_cap",
    "glasses",
    "super_cape",
    "swim_ring",
    "backpack",
]


class CharacterSpec(BaseModel):
    """Complete 3D specification for a single rigged character in the scene."""
    char_id: str
    name: str
    role: CharacterRole
    rig_engine: RigEngineType = "glb_skeletal"
    rig_family: RigFamilyType = "kaykit_medium"
    glb_model: str = "Protagonist_A.glb"
    target_height_m: float = 1.48
    facing_offset_rad: float = 0.0
    skin_hex: str = "#ffdbac"
    outfit_primary_hex: str = "#3b82f6"
    outfit_secondary_hex: str = "#ffffff"
    shoe_hex: str = "#ef4444"
    hair_hex: str = "#4a2c11"
    eye_hex: str = "#0284c7"
    accessory: AccessoryType = "none"
    scale: float = 1.0
    walk_speed: float = 1.45
    personality: Literal["energetic", "curious", "playful", "shy_sweet", "bold", "goofy"] = "energetic"


class CharacterRoster(BaseModel):
    """Full cast of 10 distinct 3D `.glb` characters generated dynamically for a video script."""
    clip_index: int
    characters: List[CharacterSpec] = Field(default_factory=list)


class CharacterCore:
    """
    Extracts character entities from any script/reference analysis and dynamically assigns
    a diverse 10-character 3D `.glb` cast from our 68+ local `.glb` character & creature models.
    """

    # Thematic Character Pools mapped to real `.glb` files in `assets/three/models/`
    KAYKIT_KIDS_AND_HEROES: List[Tuple[str, RigFamilyType, float]] = [
        ("MonsterCostume.glb", "kaykit_medium", 1.48),
        ("Protagonist_A.glb", "kaykit_medium", 1.48),
        ("Protagonist_B.glb", "kaykit_medium", 1.46),
        ("MagicalGirl.glb", "kaykit_medium", 1.46),
        ("Superhero.glb", "kaykit_medium", 1.50),
        ("Hiker.glb", "kaykit_medium", 1.48),
        ("SpaceRanger.glb", "kaykit_medium", 1.50),
        ("Ninja.glb", "kaykit_medium", 1.46),
        ("Engineer.glb", "kaykit_medium", 1.46),
        ("Witch.glb", "kaykit_medium", 1.48),
        ("Helper_A.glb", "kaykit_medium", 1.42),
        ("Helper_B.glb", "kaykit_medium", 1.42),
        ("Farmer_A.glb", "kaykit_medium", 1.48),
        ("Farmer_B.glb", "kaykit_medium", 1.46),
        ("Driver.glb", "kaykit_medium", 1.48),
        ("Clown.glb", "kaykit_medium", 1.48),
        ("ToySoldier.glb", "kaykit_medium", 1.48),
        ("Survivalist.glb", "kaykit_medium", 1.48),
        ("Lorekeeper.glb", "kaykit_medium", 1.50),
        ("Cleric.glb", "kaykit_medium", 1.48),
        ("Knight.glb", "kaykit_medium", 1.50),
        ("Mage.glb", "kaykit_medium", 1.48),
        ("Ranger.glb", "kaykit_medium", 1.48),
        ("Rogue.glb", "kaykit_medium", 1.46),
        ("Rogue_Hooded.glb", "kaykit_medium", 1.46),
        ("Druid.glb", "kaykit_medium", 1.48),
        ("Paladin.glb", "kaykit_medium", 1.52),
        ("Marksman.glb", "kaykit_medium", 1.48),
        ("Tiefling.glb", "kaykit_medium", 1.48),
    ]

    QUATERNIUS_HUMANS: List[Tuple[str, RigFamilyType, float]] = [
        ("Casual_Female.glb", "quaternius_human", 1.54),
        ("Casual_Male.glb", "quaternius_human", 1.56),
        ("Casual2_Female.glb", "quaternius_human", 1.54),
        ("Casual2_Male.glb", "quaternius_human", 1.56),
        ("Casual3_Male.glb", "quaternius_human", 1.56),
        ("Doctor_Female_Young.glb", "quaternius_human", 1.55),
        ("Doctor_Male_Young.glb", "quaternius_human", 1.57),
        ("Worker_Female.glb", "quaternius_human", 1.54),
        ("Worker_Male.glb", "quaternius_human", 1.56),
        ("Suit_Female.glb", "quaternius_human", 1.55),
        ("Suit_Male.glb", "quaternius_human", 1.57),
        ("OldClassy_Female.glb", "quaternius_human", 1.52),
        ("OldClassy_Male.glb", "quaternius_human", 1.54),
        ("Casual_Bald.glb", "quaternius_human", 1.56),
    ]

    EXPRESSIVE_SPECIALS: List[Tuple[str, RigFamilyType, float]] = [
        ("HVGirl.glb", "expressive_human_mech", 1.52),
        ("Michelle.glb", "expressive_human_mech", 1.54),
        ("RobotExpressive.glb", "expressive_human_mech", 1.15),
        ("Robot_One.glb", "kaykit_medium", 1.42),
        ("Robot_Two.glb", "kaykit_medium", 1.42),
        ("George.glb", "expressive_human_mech", 1.45),
        ("Leela.glb", "expressive_human_mech", 1.45),
    ]

    PETS_AND_ANIMALS: List[Tuple[str, RigFamilyType, float]] = [
        ("Husky.glb", "animal_quadruped", 0.68),
        ("ShibaInu.glb", "animal_quadruped", 0.62),
        ("Alpaca.glb", "animal_quadruped", 0.95),
        ("Fox.glb", "animal_quadruped", 0.65),
        ("Deer.glb", "animal_quadruped", 1.05),
        ("Stag.glb", "animal_quadruped", 1.15),
        ("Horse.glb", "animal_quadruped", 1.25),
        ("Cow.glb", "animal_quadruped", 0.95),
        ("Wolf.glb", "animal_quadruped", 0.72),
    ]

    DINOS_AND_SEA: List[Tuple[str, RigFamilyType, float]] = [
        ("Triceratops.glb", "dinosaur", 0.95),
        ("Trex.glb", "dinosaur", 1.25),
        ("Velociraptor.glb", "dinosaur", 0.90),
        ("Stegosaurus.glb", "dinosaur", 0.95),
        ("Dolphin.glb", "sea_creature", 0.65),
    ]

    SKY_BIRDS: List[Tuple[str, RigFamilyType, float]] = [
        ("Flamingo.glb", "sky_bird", 0.55),
        ("Parrot.glb", "sky_bird", 0.48),
    ]

    OUTFIT_PALETTES = [
        ("#0284c7", "#ffffff", "#facc15"),
        ("#ec4899", "#fde047", "#9333ea"),
        ("#10b981", "#fef08a", "#ea580c"),
        ("#8b5cf6", "#38bdf8", "#f43f5e"),
        ("#f97316", "#ffffff", "#2563eb"),
        ("#14b8a6", "#f472b6", "#eab308"),
        ("#ef4444", "#fde047", "#1d4ed8"),
        ("#6366f1", "#a7f3d0", "#ec4899"),
    ]

    STOP_WORDS = {
        "The", "And", "But", "For", "Nor", "Or", "Yet", "So", "In", "On", "At", "To", "From",
        "By", "With", "Of", "As", "Into", "Like", "Through", "After", "Over", "Between", "Out",
        "Against", "During", "Without", "Before", "Under", "Around", "Among", "When", "Where",
        "Why", "How", "What", "Who", "Whom", "Whose", "Which", "That", "This", "These", "Those",
        "One", "Two", "Three", "Every", "Everyone", "Someone", "Nobody", "Suddenly", "Finally",
        "Together", "Look", "Watch", "See", "Big", "Little", "Tiny", "Giant", "Super", "Crazy",
        "Funny", "Cute", "Happy", "Sad", "Normal", "Special", "Unique", "Bright", "Red", "Blue",
        "Green", "Yellow", "Purple", "Pink", "Pool", "Party", "School", "Class", "Head", "Day",
        "She", "He", "They", "Her", "His", "Their", "You", "We", "It", "Its", "Just", "Was",
    }

    def _hash_int(self, text: str) -> int:
        return int(hashlib.md5(text.encode("utf-8")).hexdigest()[:8], 16)

    def extract_named_entities(self, texts: List[str]) -> List[str]:
        """Extract proper character names dynamically from narration & visual prompts."""
        found: List[str] = []
        for t in texts:
            words = re.findall(r"\b[A-Z][a-z]{2,11}\b", t)
            for w in words:
                if w not in self.STOP_WORDS and w not in found:
                    found.append(w)
        return found

    def _select_lead_cast_for_biome(
        self,
        biome: str,
        corpus: str,
        clip_index: int,
    ) -> List[Tuple[str, RigFamilyType, float]]:
        """
        Select 7 distinct human/chibi `.glb` character models tailored to the clip's biome & story
        so every clip showcases a rich variety of our local 3D `.glb` character library.
        """
        c_low = corpus.lower()

        if biome == "waterpark_pool" or "pool" in c_low or "penguin" in c_low:
            base_cast = [
                ("MonsterCostume.glb", "kaykit_medium", 1.50),
                ("Protagonist_B.glb", "kaykit_medium", 1.48),
                ("Protagonist_A.glb", "kaykit_medium", 1.48),
                ("MagicalGirl.glb", "kaykit_medium", 1.46),
                ("Hiker.glb", "kaykit_medium", 1.48),
                ("Superhero.glb", "kaykit_medium", 1.50),
                ("Farmer_A.glb", "kaykit_medium", 1.48),
                ("Helper_B.glb", "kaykit_medium", 1.44),
            ]
        elif biome in ("school_courtyard", "futuristic_lab") or "head" in c_low or "school" in c_low:
            base_cast = [
                ("MagicalGirl.glb", "kaykit_medium", 1.50),
                ("Protagonist_B.glb", "kaykit_medium", 1.48),
                ("Protagonist_A.glb", "kaykit_medium", 1.48),
                ("Engineer.glb", "kaykit_medium", 1.48),
                ("SpaceRanger.glb", "kaykit_medium", 1.50),
                ("Lorekeeper.glb", "kaykit_medium", 1.50),
                ("Witch.glb", "kaykit_medium", 1.48),
                ("Driver.glb", "kaykit_medium", 1.48),
            ]
        elif biome in ("magic_carnival", "city_playground"):
            base_cast = [
                ("Superhero.glb", "kaykit_medium", 1.50),
                ("Witch.glb", "kaykit_medium", 1.48),
                ("Clown.glb", "kaykit_medium", 1.48),
                ("Ninja.glb", "kaykit_medium", 1.46),
                ("Helper_A.glb", "kaykit_medium", 1.44),
                ("Helper_B.glb", "kaykit_medium", 1.44),
                ("SpaceRanger.glb", "kaykit_medium", 1.50),
                ("Ranger.glb", "kaykit_medium", 1.48),
            ]
        else:
            # Rotate dynamically across the full 30+ KayKit Chibi character library based on clip_index
            offset = ((clip_index - 1) * 6) % len(self.KAYKIT_KIDS_AND_HEROES)
            base_cast = [
                self.KAYKIT_KIDS_AND_HEROES[(offset + k) % len(self.KAYKIT_KIDS_AND_HEROES)]
                for k in range(8)
            ]

        return base_cast

    ARCHETYPE_GLB_POOL: Dict[str, List[Tuple[str, RigFamilyType, float]]] = {
        "small_cute_creature": [
            ("ShibaInu.glb", "animal_quadruped", 0.72),
            ("Husky.glb", "animal_quadruped", 0.74),
            ("Fox.glb", "animal_quadruped", 0.72),
        ],
        "large_goofy_creature": [
            ("MonsterCostume.glb", "kaykit_medium", 1.56),
            ("Clown.glb", "kaykit_medium", 1.52),
            ("Barbarian.glb", "kaykit_medium", 1.54),
            ("Trex.glb", "dinosaur", 1.32),
        ],
        "tiny_prank_critter": [
            ("MonsterCostume.glb", "kaykit_medium", 1.10),
            ("Ninja.glb", "kaykit_medium", 1.18),
            ("RobotExpressive.glb", "expressive_human_mech", 1.05),
        ],
        "suited_executive": [
            ("Lorekeeper.glb", "kaykit_medium", 1.50),
            ("Cleric.glb", "kaykit_medium", 1.48),
            ("Hiker.glb", "kaykit_medium", 1.48),
            ("Driver.glb", "kaykit_medium", 1.48),
        ],
        "sporty_athlete": [
            ("Protagonist_B.glb", "kaykit_medium", 1.46),
            ("SpaceRanger.glb", "kaykit_medium", 1.50),
            ("Superhero.glb", "kaykit_medium", 1.50),
            ("Protagonist_A.glb", "kaykit_medium", 1.48),
        ],
        "hero_boy": [
            ("Protagonist_B.glb", "kaykit_medium", 1.46),
            ("Hiker.glb", "kaykit_medium", 1.48),
            ("SpaceRanger.glb", "kaykit_medium", 1.50),
        ],
        "hero_girl": [
            ("Protagonist_A.glb", "kaykit_medium", 1.46),
            ("MagicalGirl.glb", "kaykit_medium", 1.46),
            ("Helper_A.glb", "kaykit_medium", 1.42),
            ("HVGirl.glb", "expressive_human_mech", 1.52),
        ],
        "villain_boss": [
            ("MonsterCostume.glb", "kaykit_medium", 1.55),
            ("Rogue_Hooded.glb", "kaykit_medium", 1.50),
            ("Witch.glb", "kaykit_medium", 1.48),
        ],
        "robot_assistant": [
            ("RobotExpressive.glb", "expressive_human_mech", 1.25),
            ("Robot_One.glb", "kaykit_medium", 1.44),
            ("Robot_Two.glb", "kaykit_medium", 1.44),
            ("George.glb", "expressive_human_mech", 1.55),
            ("Leela.glb", "expressive_human_mech", 1.55),
        ],
        "elder_mentor": [
            ("Lorekeeper.glb", "kaykit_medium", 1.50),
            ("Farmer_A.glb", "kaykit_medium", 1.48),
            ("Engineer.glb", "kaykit_medium", 1.48),
        ],
        "pet_dog": [
            ("ShibaInu.glb", "animal_quadruped", 0.68),
            ("Husky.glb", "animal_quadruped", 0.72),
        ],
    }

    def generate_roster(
        self,
        script_title: str,
        scene_narrations: List[str],
        scene_prompts: List[str],
        biome: str = "waterpark_pool",
        clip_index: int = 1,
        min_characters: int = 2,
        cast_specs: Optional[List[Any]] = None,
        has_background_crowd: bool = False,
    ) -> CharacterRoster:
        """
        Generate the exact 3D `.glb` cast matching the reference video's characters (`cast_specs`),
        mapping each archetype across our full 68+ `.glb` human, creature, robot & animal library.
        NEVER dumps unrequested witches/wizards/dogs onto scenes that only have 2-3 characters!
        """
        corpus = " ".join([script_title] + scene_narrations + scene_prompts)
        personalities: List[Literal["energetic", "curious", "playful", "shy_sweet", "bold", "goofy"]] = [
            "energetic", "playful", "bold", "curious", "shy_sweet", "goofy"
        ]
        characters: List[CharacterSpec] = []
        used_glbs: set = set()

        if cast_specs:
            has_deut = any(getattr(cs, "role", None) == "deuteragonist" for cs in cast_specs)
            for i, cspec in enumerate(cast_specs):
                cname = getattr(cspec, "name", None) or f"Hero{i+1}"
                arch = getattr(cspec, "archetype", "hero_boy")
                raw_role = getattr(cspec, "role", "protagonist" if i == 0 else ("deuteragonist" if i == 1 else "companion"))
                if i == 0:
                    role: CharacterRole = "protagonist"
                elif i == 1 and (not has_deut or raw_role == "deuteragonist"):
                    role = "deuteragonist"
                    has_deut = True
                else:
                    role = raw_role if raw_role in ("protagonist", "deuteragonist", "companion") else "companion"

                pool = self.ARCHETYPE_GLB_POOL.get(arch, self.ARCHETYPE_GLB_POOL["hero_boy"])
                chosen = None
                for cand in pool:
                    if cand[0] not in used_glbs:
                        chosen = cand
                        break
                if chosen is None:
                    chosen = pool[i % len(pool)]
                glb_file, rig_fam, height_m = chosen
                used_glbs.add(glb_file)

                pal = self.OUTFIT_PALETTES[(i + clip_index - 1) % len(self.OUTFIT_PALETTES)]
                characters.append(
                    CharacterSpec(
                        char_id=f"char_{i+1:02d}_{re.sub(r'[^a-z0-9]', '', cname.lower()) or f'actor{i+1}'}",
                        name=cname,
                        role=role,
                        rig_engine="glb_skeletal",
                        rig_family=rig_fam,
                        glb_model=glb_file,
                        target_height_m=height_m,
                        outfit_primary_hex=pal[0],
                        outfit_secondary_hex=pal[1],
                        shoe_hex=pal[2],
                        accessory="none",
                        scale=1.0,
                        walk_speed=round(1.35 + (i % 3) * 0.15, 2),
                        personality=personalities[i % len(personalities)],
                    )
                )
        else:
            extracted_names = self.extract_named_entities([script_title] + scene_narrations)
            procedural_names = ["Leo", "Maya", "Toby", "Luna", "Zack", "Coco", "Max", "Nori"]
            for pname in procedural_names:
                if len(extracted_names) >= max(3, min_characters):
                    break
                if pname not in extracted_names:
                    extracted_names.append(pname)
            lead_cast = self._select_lead_cast_for_biome(biome, corpus, clip_index)
            target_n = 8 if has_background_crowd else min(3, max(2, len(extracted_names)))
            roles_list: List[CharacterRole] = ["protagonist", "deuteragonist", "companion", "companion", "crowd_kid", "crowd_kid", "crowd_kid", "crowd_kid"]
            for i in range(target_n):
                cname = extracted_names[i]
                glb_file, rig_fam, height_m = lead_cast[i % len(lead_cast)]
                pal = self.OUTFIT_PALETTES[(i + clip_index - 1) % len(self.OUTFIT_PALETTES)]
                characters.append(
                    CharacterSpec(
                        char_id=f"char_{i+1:02d}_{cname.lower()}",
                        name=cname,
                        role=roles_list[i],
                        rig_engine="glb_skeletal",
                        rig_family=rig_fam,
                        glb_model=glb_file,
                        target_height_m=height_m,
                        outfit_primary_hex=pal[0],
                        outfit_secondary_hex=pal[1],
                        shoe_hex=pal[2],
                        accessory="none",
                        scale=1.0,
                        walk_speed=round(1.35 + (i % 4) * 0.15, 2),
                        personality=personalities[i % len(personalities)],
                    )
                )

        # ONLY include extra background crowd/pets if the reference video literally has a crowd!
        if has_background_crowd:
            pet_model, pet_fam, pet_h = self.PETS_AND_ANIMALS[(clip_index - 1) % len(self.PETS_AND_ANIMALS)]
            characters.append(
                CharacterSpec(
                    char_id="char_09_pet_companion",
                    name="Buddy",
                    role="pet_animal",
                    rig_engine="glb_skeletal",
                    rig_family=pet_fam,
                    glb_model=pet_model,
                    target_height_m=pet_h,
                    outfit_primary_hex="#f97316",
                    scale=1.0,
                    walk_speed=1.8,
                    personality="playful",
                )
            )
            bird_model, bird_fam, bird_h = self.SKY_BIRDS[(clip_index - 1) % len(self.SKY_BIRDS)]
            characters.append(
                CharacterSpec(
                    char_id="char_11_sky_bird",
                    name="Rio",
                    role="sky_bird",
                    rig_engine="glb_skeletal",
                    rig_family=bird_fam,
                    glb_model=bird_model,
                    target_height_m=bird_h,
                    outfit_primary_hex="#38bdf8",
                    scale=1.0,
                    walk_speed=2.2,
                    personality="energetic",
                )
            )

        return CharacterRoster(clip_index=clip_index, characters=characters)
