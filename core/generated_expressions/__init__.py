"""Auto-generated Facial Expression Cores synthesized dynamically by `ExpressionLearningCore`."""
import importlib
from pathlib import Path
from typing import Dict, Any

GENERATED_EXPRESSION_REGISTRY: Dict[str, Dict[str, Any]] = {}

def load_all_generated_expressions() -> Dict[str, Dict[str, Any]]:
    pkg_dir = Path(__file__).resolve().parent
    for py_file in sorted(pkg_dir.glob("*_expr.py")):
        mod_name = f"core.generated_expressions.{py_file.stem}"
        try:
            mod = importlib.import_module(mod_name)
            if hasattr(mod, "EXPRESSION_PROFILE"):
                prof = dict(mod.EXPRESSION_PROFILE)
                GENERATED_EXPRESSION_REGISTRY[prof["expression_id"]] = prof
        except Exception:
            pass
    return GENERATED_EXPRESSION_REGISTRY

