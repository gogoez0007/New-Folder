"""
Downloader & Inventory Manager for Local 3D `.glb` Character, Animal, and Environment Asset Library.
Downloads 75+ rigged, animated, zero-Draco `.glb` models into `assets/three/models/`.
"""

import concurrent.futures
import json
import struct
import urllib.parse
import urllib.request
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent / "assets" / "three" / "models"

KAYKIT_BASE = "https://raw.githubusercontent.com/GeorgeQLe/assets-kaykit-3d-characters/main/"
QUAT_BASE = "https://raw.githubusercontent.com/trebeljahr/quaternius-showcase/main/public/glb/"
GHOST_BASE = "https://raw.githubusercontent.com/Yametech12/ghostname-3d-assets/main/models/"
THREE_BASE = "https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/gltf/"
BABYLON_BASE = "https://raw.githubusercontent.com/BabylonJS/Assets/master/meshes/"

ASSET_MANIFEST = {
    # --- 1. KayKit Shared Animation Rigs (35+ skeletal animations for all KayKit characters) ---
    "Rig_Medium_General.glb": KAYKIT_BASE + "assets/kaykit/character-animations-1.1/Animations/gltf/Rig_Medium/Rig_Medium_General.glb",
    "Rig_Medium_MovementBasic.glb": KAYKIT_BASE + "assets/kaykit/character-animations-1.1/Animations/gltf/Rig_Medium/Rig_Medium_MovementBasic.glb",
    "Rig_Medium_Simulation.glb": KAYKIT_BASE + "assets/kaykit/character-animations-1.1/Animations/gltf/Rig_Medium/Rig_Medium_Simulation.glb",
    "Rig_Medium_Special.glb": KAYKIT_BASE + "assets/kaykit/character-animations-1.1/Animations/gltf/Rig_Medium/Rig_Medium_Special.glb",

    # --- 2. KayKit Stylized Chibi/Cartoon 3D Characters (30 distinct rigged characters!) ---
    "Protagonist_A.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-5/10 - April 2025 - Protagonists/characters/Protagonist_A.glb",
    "Protagonist_B.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-5/10 - April 2025 - Protagonists/characters/Protagonist_B.glb",
    "MagicalGirl.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-6/11 - May 2026 - Magical Girl/characters/MagicalGirl.glb",
    "MonsterCostume.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-4/3 - September 2023 - Monster Costume/character/gltf/MonsterCostume.glb",
    "Superhero.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-5/2 - August 2024 - Superhero/characters/Superhero.glb",
    "SpaceRanger.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-4/7 - January 2024 - Space Ranger/character/SpaceRanger.glb",
    "Ninja.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-4/8 - February 2024 - Ninja/character/Ninja.glb",
    "Hiker.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-5/11 - May 2025 - Hiker/characters/Hiker.glb",
    "Driver.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-4/2 - August 2023 - Driver/character/gltf/Driver.glb",
    "Witch.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-5/5 - November 2024 - Witch/characters/Witch.glb",
    "Helper_A.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-5/6 - December 2024 - Helpers/characters/Helper_A.glb",
    "Helper_B.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-5/6 - December 2024 - Helpers/characters/Helper_B.glb",
    "Farmer_A.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-6/12 - June 2026 - Farmers/characters/Farmer_A.glb",
    "Farmer_B.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-6/12 - June 2026 - Farmers/characters/Farmer_B.glb",
    "Clown.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-4/11 - May 2024 - Clown/characters/Clown.glb",
    "ActionFigure.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-4/6 - December 2023 - Action Figure/character/gltf/ActionFigure.glb",
    "ToySoldier.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-6/6 - December 2025 - Toy Soldier/characters/ToySoldier.glb",
    "Survivalist.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-4/9 - March 2024 - Survivalist/character/Survivalist.glb",
    "Knight.glb": KAYKIT_BASE + "assets/kaykit/adventurers-2.0/Characters/gltf/Knight.glb",
    "Mage.glb": KAYKIT_BASE + "assets/kaykit/adventurers-2.0/Characters/gltf/Mage.glb",
    "Ranger.glb": KAYKIT_BASE + "assets/kaykit/adventurers-2.0/Characters/gltf/Ranger.glb",
    "Rogue.glb": KAYKIT_BASE + "assets/kaykit/adventurers-2.0/Characters/gltf/Rogue.glb",
    "Rogue_Hooded.glb": KAYKIT_BASE + "assets/kaykit/adventurers-2.0/Characters/gltf/Rogue_Hooded.glb",
    "Druid.glb": KAYKIT_BASE + "assets/kaykit/adventurers-2.0/Characters/gltf/Druid.glb",
    "Engineer.glb": KAYKIT_BASE + "assets/kaykit/adventurers-2.0/Characters/gltf/Engineer.glb",
    "Barbarian.glb": KAYKIT_BASE + "assets/kaykit/adventurers-2.0/Characters/gltf/Barbarian.glb",
    "Paladin.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-4/10 - April 2024 - Paladin/characters/gltf/Paladin.glb",
    "Cleric.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-6/3 - September 2025 - Cleric/characters/Cleric.glb",
    "Lorekeeper.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-6/1 - July 2025 - Lorekeeper/characters/Lorekeeper.glb",
    "Marksman.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-6/10 - April 2026 - Marksman/characters/Marksman.glb",
    "Tiefling.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-5/12 - June 2025 - Tiefling/characters/Tiefling.glb",
    "Robot_One.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-4/12 - June 2024 - Robot/characters/Robot_One.glb",
    "Robot_Two.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-4/12 - June 2024 - Robot/characters/Robot_Two.glb",

    # --- 3. Quaternius / Ghostname Rigged Animated Humans (14 characters w/ 17 built-in animations each!) ---
    "Casual_Female.glb": GHOST_BASE + "Casual_Female.glb",
    "Casual_Male.glb": GHOST_BASE + "Casual_Male.glb",
    "Casual2_Female.glb": GHOST_BASE + "Casual2_Female.glb",
    "Casual2_Male.glb": GHOST_BASE + "Casual2_Male.glb",
    "Casual3_Male.glb": GHOST_BASE + "Casual3_Male.glb",
    "Casual_Bald.glb": GHOST_BASE + "Casual_Bald.glb",
    "Doctor_Female_Young.glb": GHOST_BASE + "Doctor_Female_Young.glb",
    "Doctor_Male_Young.glb": GHOST_BASE + "Doctor_Male_Young.glb",
    "Suit_Female.glb": GHOST_BASE + "Suit_Female.glb",
    "Suit_Male.glb": GHOST_BASE + "Suit_Male.glb",
    "Worker_Female.glb": GHOST_BASE + "Worker_Female.glb",
    "Worker_Male.glb": GHOST_BASE + "Worker_Male.glb",
    "OldClassy_Female.glb": GHOST_BASE + "OldClassy_Female.glb",
    "OldClassy_Male.glb": GHOST_BASE + "OldClassy_Male.glb",

    # --- 4. BabylonJS & Three.js & Mech Animated Characters ---
    "HVGirl.glb": BABYLON_BASE + "HVGirl.glb",
    "Xbot.glb": THREE_BASE + "Xbot.glb",
    "George.glb": QUAT_BASE + "mech_pack/George.glb",
    "Leela.glb": QUAT_BASE + "mech_pack/Leela.glb",

    # --- 5. Animated 3D Animals, Pets, Dinosaurs & Sea Creatures ---
    "Alpaca.glb": QUAT_BASE + "animals_pack/Alpaca.glb",
    "Husky.glb": QUAT_BASE + "animals_pack/Husky.glb",
    "ShibaInu.glb": QUAT_BASE + "animals_pack/ShibaInu.glb",
    "Stag.glb": QUAT_BASE + "animals_pack/Stag.glb",
    "Cow.glb": QUAT_BASE + "animals_pack/Cow.glb",
    "Deer.glb": QUAT_BASE + "animals_pack/Deer.glb",
    "Wolf.glb": QUAT_BASE + "animals_pack/Wolf.glb",
    "Trex.glb": QUAT_BASE + "dinosaurs_pack/Trex.glb",
    "Triceratops.glb": QUAT_BASE + "dinosaurs_pack/Triceratops.glb",
    "Velociraptor.glb": QUAT_BASE + "dinosaurs_pack/Velociraptor.glb",
    "Stegosaurus.glb": QUAT_BASE + "dinosaurs_pack/Stegosaurus.glb",
    "Dolphin.glb": QUAT_BASE + "fish_pack/Dolphin.glb",
    "Shark.glb": QUAT_BASE + "fish_pack/Shark.glb",

    # --- 6. 3D Environment Buildings, Houses, Trees, Clouds, Vehicles & Props ---
    "House1.glb": QUAT_BASE + "buildings_pack_2/House1.glb",
    "House2.glb": QUAT_BASE + "buildings_pack_2/House2.glb",
    "Building1_Large.glb": QUAT_BASE + "buildings_pack_2/Building1_Large.glb",
    "Building1_Small.glb": QUAT_BASE + "buildings_pack_2/Building1_Small.glb",
    "Building2_Small.glb": QUAT_BASE + "buildings_pack_2/Building2_Small.glb",
    "Tree1.glb": QUAT_BASE + "simple_nature_pack/Tree1.glb",
    "Tree2.glb": QUAT_BASE + "simple_nature_pack/Tree2.glb",
    "Tree3.glb": QUAT_BASE + "simple_nature_pack/Tree3.glb",
    "Tree4.glb": QUAT_BASE + "simple_nature_pack/Tree4.glb",
    "Bush1.glb": QUAT_BASE + "simple_nature_pack/Bush1.glb",
    "Rock1.glb": QUAT_BASE + "simple_nature_pack/Rock1.glb",
    "Cloud1.glb": QUAT_BASE + "platformer_pack/Cloud1.glb",
    "Cloud2.glb": QUAT_BASE + "platformer_pack/Cloud2.glb",
    "Cloud3.glb": QUAT_BASE + "platformer_pack/Cloud3.glb",
    "Bouncer.glb": QUAT_BASE + "platformer_game_pack/Bouncer.glb",
    "Boat.glb": QUAT_BASE + "ships_pack/Boat.glb",
    "car.glb": KAYKIT_BASE + "assets/kaykit/mystery-monthly-series-4/2 - August 2023 - Driver/assets/gltf/car.glb",
}


def _safe_url(raw_url: str) -> str:
    parts = urllib.parse.urlsplit(raw_url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, urllib.parse.quote(parts.path), parts.query, parts.fragment))


def download_one(item):
    filename, raw_url = item
    target = MODELS_DIR / filename
    if target.exists() and target.stat().st_size > 5000:
        return filename, target.stat().st_size, "cached"
    url = _safe_url(raw_url)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    target.write_bytes(data)
    return filename, len(data), "downloaded"


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {len(ASSET_MANIFEST)} 3D GLB assets to {MODELS_DIR} ...")
    ok_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(download_one, it): it[0] for it in ASSET_MANIFEST.items()}
        for fut in concurrent.futures.as_completed(futures):
            fname = futures[fut]
            try:
                _, sz, status = fut.result()
                ok_count += 1
            except Exception as exc:
                print(f"  [ERR] {fname}: {exc}")

    all_glbs = sorted(MODELS_DIR.glob("*.glb"))
    total_mb = sum(p.stat().st_size for p in all_glbs) / (1024 * 1024)
    print(f"Done! {len(all_glbs)} total .glb models in {MODELS_DIR} ({total_mb:.2f} MB)")


if __name__ == "__main__":
    main()

