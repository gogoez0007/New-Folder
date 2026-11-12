"""
Auto-generated Object Core Module: `Smartphone` (`handphone`).
Synthesized autonomously by `MetaCoreSynthesizer` (zero hardcode!).
"""

from core.object_knowledge_core import OBJECT_KNOWLEDGE_BASE, ObjectAnatomySpec

SPEC = ObjectAnatomySpec.model_validate({
  "object_id": "handphone",
  "display_name": "Smartphone",
  "category": "furniture_mechanism",
  "builder_key": "generated_builder",
  "real_anatomy_parts": [
    "Phone_Frame",
    "Phone_Screen",
    "Bottom_Bar",
    "Camera_Bump",
    "Lens_1",
    "Lens_2",
    "Lens_3",
    "Flash"
  ],
  "typical_dimensions_m": [
    0.075,
    0.01,
    0.15
  ],
  "default_height_m": 0.3,
  "surface_finish": "latex_glossy",
  "motion_behavior": "static",
  "placement_layer": "ground",
  "silhouette_notes": "Sleek rectangular slab with rounded corners, prominent glowing screen, and a distinct rear triple camera bump.",
  "aliases": [
    "handphone",
    "smartphone",
    "mobile phone",
    "cell phone"
  ],
  "composite_parts": [
    {
      "part_name": "Phone_Frame",
      "shape": "box",
      "size": [
        0.075,
        0.01,
        0.15
      ],
      "offset": [
        0.0,
        0.925,
        0.0
      ],
      "rotation": [
        0.0,
        0.0,
        0.0
      ],
      "color": "#2C3E50",
      "finish": "painted_metal"
    },
    {
      "part_name": "Phone_Screen",
      "shape": "box",
      "size": [
        0.07,
        0.001,
        0.14
      ],
      "offset": [
        0.0,
        0.925,
        0.0045
      ],
      "rotation": [
        0.0,
        0.0,
        0.0
      ],
      "color": "#3498DB",
      "finish": "glass_facade"
    },
    {
      "part_name": "Bottom_Bar",
      "shape": "box",
      "size": [
        0.06,
        0.001,
        0.005
      ],
      "offset": [
        0.0,
        0.8575,
        0.0045
      ],
      "rotation": [
        0.0,
        0.0,
        0.0
      ],
      "color": "#1C2833",
      "finish": "painted_metal"
    },
    {
      "part_name": "Camera_Bump",
      "shape": "box",
      "size": [
        0.03,
        0.002,
        0.04
      ],
      "offset": [
        -0.0125,
        0.97,
        -0.006
      ],
      "rotation": [
        0.0,
        0.0,
        0.0
      ],
      "color": "#1C2833",
      "finish": "brushed_chrome"
    },
    {
      "part_name": "Lens_1",
      "shape": "cylinder",
      "size": [
        0.008,
        0.001
      ],
      "offset": [
        -0.0125,
        0.9775,
        -0.0075
      ],
      "rotation": [
        1.5708,
        0.0,
        0.0
      ],
      "color": "#000000",
      "finish": "glass_facade"
    },
    {
      "part_name": "Lens_2",
      "shape": "cylinder",
      "size": [
        0.008,
        0.001
      ],
      "offset": [
        -0.0125,
        0.97,
        -0.0075
      ],
      "rotation": [
        1.5708,
        0.0,
        0.0
      ],
      "color": "#000000",
      "finish": "glass_facade"
    },
    {
      "part_name": "Lens_3",
      "shape": "cylinder",
      "size": [
        0.008,
        0.001
      ],
      "offset": [
        -0.0125,
        0.9625,
        -0.0075
      ],
      "rotation": [
        1.5708,
        0.0,
        0.0
      ],
      "color": "#000000",
      "finish": "glass_facade"
    },
    {
      "part_name": "Flash",
      "shape": "sphere",
      "size": [
        0.003
      ],
      "offset": [
        -0.0025,
        0.9775,
        -0.0075
      ],
      "rotation": [
        0.0,
        0.0,
        0.0
      ],
      "color": "#FFFFCC",
      "finish": "latex_glossy"
    }
  ]
})


def register() -> ObjectAnatomySpec:
    """Register `handphone` into the live Object Knowledge Base."""
    OBJECT_KNOWLEDGE_BASE[SPEC.object_id] = SPEC
    return SPEC
