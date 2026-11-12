"""Auto-generated Natural Motion Cores synthesized dynamically by `NaturalMotionCore`."""
import importlib
from pathlib import Path
from typing import Dict, Any

GENERATED_MOTION_REGISTRY: Dict[str, Dict[str, Any]] = {}

def load_all_generated_motions() -> Dict[str, Dict[str, Any]]:
    pkg_dir = Path(__file__).resolve().parent
    for py_file in sorted(pkg_dir.glob("*_motion.py")):
        mod_name = f"core.generated_motions.{py_file.stem}"
        try:
            mod = importlib.import_module(mod_name)
            if hasattr(mod, "MOTION_PROFILE"):
                prof = dict(mod.MOTION_PROFILE)
                GENERATED_MOTION_REGISTRY[prof["action_id"]] = prof
        except Exception:
            pass
    return GENERATED_MOTION_REGISTRY

