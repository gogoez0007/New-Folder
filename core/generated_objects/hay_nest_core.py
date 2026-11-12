"""
Auto-generated Object Core Module: `Hay Nest with Chicks` (`hay_nest`).
Synthesized autonomously by `MetaCoreSynthesizer` (zero hardcode!).
"""

from core.object_knowledge_core import OBJECT_KNOWLEDGE_BASE, ObjectAnatomySpec

SPEC = ObjectAnatomySpec.model_validate({ 'object_id': 'hay_nest',
  'display_name': 'Hay Nest with Chicks',
  'category': 'nature_flora',
  'builder_key': 'generated_builder',
  'real_anatomy_parts': [ 'nest_base',
                          'nest_bottom',
                          'chick_one',
                          'chick_two',
                          'chick_three'],
  'typical_dimensions_m': [0.6, 0.25, 0.6],
  'default_height_m': 0.3,
  'surface_finish': 'fluffy_matte',
  'motion_behavior': 'static',
  'placement_layer': 'ground',
  'silhouette_notes': 'A circular woven nest made of dried straw and hay, '
                      'containing three small soft baby chicks huddled '
                      'together.',
  'aliases': ['hay_nest', 'hay nest', 'bird nest', 'straw nest', 'empty nest'],
  'composite_parts': [ { 'part_name': 'nest_base',
                         'shape': 'torus',
                         'size': [0.6, 0.25, 0.2],
                         'offset': [0.0, 0.12, 0.0],
                         'rotation': [1.57, 0.0, 0.0],
                         'color': '#c49a45',
                         'finish': 'fluffy_matte'},
                       { 'part_name': 'nest_bottom',
                         'shape': 'sphere',
                         'size': [0.55, 0.1, 0.55],
                         'offset': [0.0, 0.05, 0.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#a87d32',
                         'finish': 'fluffy_matte'},
                       { 'part_name': 'chick_one',
                         'shape': 'sphere',
                         'size': [0.12, 0.12, 0.12],
                         'offset': [-0.12, 0.15, 0.08],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#ffea75',
                         'finish': 'fluffy_matte'},
                       { 'part_name': 'chick_two',
                         'shape': 'sphere',
                         'size': [0.13, 0.13, 0.13],
                         'offset': [0.1, 0.16, -0.05],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#fcd658',
                         'finish': 'fluffy_matte'},
                       { 'part_name': 'chick_three',
                         'shape': 'sphere',
                         'size': [0.11, 0.11, 0.11],
                         'offset': [0.0, 0.14, 0.12],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#ffea75',
                         'finish': 'fluffy_matte'}]})


def register() -> ObjectAnatomySpec:
    """Register `hay_nest` into the live Object Knowledge Base."""
    OBJECT_KNOWLEDGE_BASE[SPEC.object_id] = SPEC
    return SPEC
