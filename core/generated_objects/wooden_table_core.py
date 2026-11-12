"""
Auto-generated Object Core Module: `Classic Wooden Table` (`wooden_table`).
Synthesized autonomously by `MetaCoreSynthesizer` (zero hardcode!).
"""

from core.object_knowledge_core import OBJECT_KNOWLEDGE_BASE, ObjectAnatomySpec

SPEC = ObjectAnatomySpec.model_validate({ 'object_id': 'wooden_table',
  'display_name': 'Classic Wooden Table',
  'category': 'furniture_mechanism',
  'builder_key': 'generated_builder',
  'real_anatomy_parts': [ 'tabletop',
                          'leg_front_left',
                          'leg_front_right',
                          'leg_back_left',
                          'leg_back_right'],
  'typical_dimensions_m': [1.2, 0.75, 0.8],
  'default_height_m': 0.75,
  'surface_finish': 'matte_wood',
  'motion_behavior': 'static',
  'placement_layer': 'ground',
  'silhouette_notes': 'A sturdy rectangular dining table with four cylindrical '
                      'legs supporting a thick wooden top plank.',
  'aliases': [ 'wooden_table',
               'wooden table',
               'dining_table',
               'kitchen_table',
               'table'],
  'composite_parts': [ { 'part_name': 'tabletop',
                         'shape': 'box',
                         'size': [1.2, 0.08, 0.8],
                         'offset': [0.0, 0.71, 0.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#8B5A2B',
                         'finish': 'matte_wood'},
                       { 'part_name': 'leg_front_left',
                         'shape': 'cylinder',
                         'size': [0.06, 0.71, 0.06],
                         'offset': [-0.52, 0.355, 0.32],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#5C3A21',
                         'finish': 'matte_wood'},
                       { 'part_name': 'leg_front_right',
                         'shape': 'cylinder',
                         'size': [0.06, 0.71, 0.06],
                         'offset': [0.52, 0.355, 0.32],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#5C3A21',
                         'finish': 'matte_wood'},
                       { 'part_name': 'leg_back_left',
                         'shape': 'cylinder',
                         'size': [0.06, 0.71, 0.06],
                         'offset': [-0.52, 0.355, -0.32],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#5C3A21',
                         'finish': 'matte_wood'},
                       { 'part_name': 'leg_back_right',
                         'shape': 'cylinder',
                         'size': [0.06, 0.71, 0.06],
                         'offset': [0.52, 0.355, -0.32],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#5C3A21',
                         'finish': 'matte_wood'}]})


def register() -> ObjectAnatomySpec:
    """Register `wooden_table` into the live Object Knowledge Base."""
    OBJECT_KNOWLEDGE_BASE[SPEC.object_id] = SPEC
    return SPEC
