"""
Auto-generated Object Core Module: `Baby Mice Nest` (`baby_mice`).
Synthesized autonomously by `MetaCoreSynthesizer` (zero hardcode!).
"""

from core.object_knowledge_core import OBJECT_KNOWLEDGE_BASE, ObjectAnatomySpec

SPEC = ObjectAnatomySpec.model_validate({ 'object_id': 'baby_mice',
  'display_name': 'Baby Mice Nest',
  'category': 'nature_flora',
  'builder_key': 'generated_builder',
  'real_anatomy_parts': [ 'nest_base',
                          'mouse_1_body',
                          'mouse_2_body',
                          'mouse_3_body',
                          'mouse_1_head',
                          'mouse_2_head'],
  'typical_dimensions_m': [0.3, 0.15, 0.3],
  'default_height_m': 0.3,
  'surface_finish': 'fluffy_matte',
  'motion_behavior': 'static',
  'placement_layer': 'ground',
  'silhouette_notes': 'A cluster of three small, rounded mouse bodies huddled '
                      'together in a soft, organic mound shape.',
  'aliases': ['baby_mice', 'baby mice', 'mouse_nest', 'baby_mice_cluster'],
  'composite_parts': [ { 'part_name': 'nest_base',
                         'shape': 'cylinder',
                         'size': [0.3, 0.05, 0.3],
                         'offset': [0.0, 0.025, 0.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#8B4513',
                         'finish': 'fluffy_matte'},
                       { 'part_name': 'mouse_1_body',
                         'shape': 'capsule',
                         'size': [0.08, 0.12, 0.08],
                         'offset': [0.05, 0.1, 0.0],
                         'rotation': [0.0, 0.0, 1.57],
                         'color': '#A9A9A9',
                         'finish': 'fluffy_matte'},
                       { 'part_name': 'mouse_2_body',
                         'shape': 'capsule',
                         'size': [0.08, 0.12, 0.08],
                         'offset': [-0.05, 0.1, 0.05],
                         'rotation': [0.5, 0.0, 1.57],
                         'color': '#D3D3D3',
                         'finish': 'fluffy_matte'},
                       { 'part_name': 'mouse_3_body',
                         'shape': 'capsule',
                         'size': [0.08, 0.12, 0.08],
                         'offset': [0.0, 0.1, -0.05],
                         'rotation': [-0.5, 0.0, 1.57],
                         'color': '#808080',
                         'finish': 'fluffy_matte'},
                       { 'part_name': 'mouse_1_head',
                         'shape': 'sphere',
                         'size': [0.04, 0.04, 0.04],
                         'offset': [0.1, 0.12, 0.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#A9A9A9',
                         'finish': 'fluffy_matte'},
                       { 'part_name': 'mouse_2_head',
                         'shape': 'sphere',
                         'size': [0.04, 0.04, 0.04],
                         'offset': [-0.1, 0.12, 0.05],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#D3D3D3',
                         'finish': 'fluffy_matte'}]})


def register() -> ObjectAnatomySpec:
    """Register `baby_mice` into the live Object Knowledge Base."""
    OBJECT_KNOWLEDGE_BASE[SPEC.object_id] = SPEC
    return SPEC
