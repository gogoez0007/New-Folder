"""
Auto-generated Object Core Module: `Rustic Wooden Barn Wall` (`wooden_wall`).
Synthesized autonomously by `MetaCoreSynthesizer` (zero hardcode!).
"""

from core.object_knowledge_core import OBJECT_KNOWLEDGE_BASE, ObjectAnatomySpec

SPEC = ObjectAnatomySpec.model_validate({ 'object_id': 'wooden_wall',
  'display_name': 'Rustic Wooden Barn Wall',
  'category': 'city_architecture',
  'builder_key': 'generated_builder',
  'real_anatomy_parts': [ 'plank_left',
                          'plank_center',
                          'plank_right',
                          'support_beam_top',
                          'support_beam_bottom',
                          'mouse_hole_rim'],
  'typical_dimensions_m': [1.2, 1.5, 0.2],
  'default_height_m': 1.5,
  'surface_finish': 'matte_wood',
  'motion_behavior': 'static',
  'placement_layer': 'ground',
  'silhouette_notes': 'A rustic barn wall made of several vertical wooden '
                      'planks, featuring a small circular mouse hole near the '
                      'bottom corner.',
  'aliases': [ 'wooden_wall',
               'wooden wall',
               'barn_wall',
               'wooden_partition',
               'mouse_hole_wall'],
  'composite_parts': [ { 'part_name': 'plank_left',
                         'shape': 'box',
                         'size': [0.35, 1.5, 0.08],
                         'offset': [-0.38, 0.75, 0.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#8B5A2B',
                         'finish': 'matte_wood'},
                       { 'part_name': 'plank_center',
                         'shape': 'box',
                         'size': [0.35, 1.5, 0.08],
                         'offset': [0.0, 0.75, 0.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#A0522D',
                         'finish': 'matte_wood'},
                       { 'part_name': 'plank_right',
                         'shape': 'box',
                         'size': [0.35, 1.5, 0.08],
                         'offset': [0.38, 0.75, 0.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#8B4513',
                         'finish': 'matte_wood'},
                       { 'part_name': 'support_beam_top',
                         'shape': 'box',
                         'size': [1.2, 0.12, 0.12],
                         'offset': [0.0, 1.4, 0.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#5C3A21',
                         'finish': 'matte_wood'},
                       { 'part_name': 'support_beam_bottom',
                         'shape': 'box',
                         'size': [1.2, 0.12, 0.12],
                         'offset': [0.0, 0.1, 0.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#5C3A21',
                         'finish': 'matte_wood'},
                       { 'part_name': 'mouse_hole_rim',
                         'shape': 'torus',
                         'size': [0.1, 0.02, 16.0],
                         'offset': [-0.3, 0.25, 0.05],
                         'rotation': [0.0, 1.57, 0.0],
                         'color': '#3D2314',
                         'finish': 'matte_wood'}]})


def register() -> ObjectAnatomySpec:
    """Register `wooden_wall` into the live Object Knowledge Base."""
    OBJECT_KNOWLEDGE_BASE[SPEC.object_id] = SPEC
    return SPEC
