"""Auto-generated Object Cores synthesized dynamically by `MetaCoreSynthesizer`."""
import importlib
from pathlib import Path
from typing import Dict, Any

GENERATED_OBJECT_REGISTRY: Dict[str, Any] = {}

def load_all_generated_objects() -> Dict[str, Any]:
    pkg_dir = Path(__file__).resolve().parent
    for py_file in sorted(pkg_dir.glob("*_core.py")):
        mod_name = f"core.generated_objects.{py_file.stem}"
        try:
            mod = importlib.import_module(mod_name)
            if hasattr(mod, "SPEC"):
                spec = mod.SPEC
                GENERATED_OBJECT_REGISTRY[spec.object_id] = spec
        except Exception:
            pass
    return GENERATED_OBJECT_REGISTRY

