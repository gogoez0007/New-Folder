"""
Auto-generated Object Core Module: `Rustic Barn Mouse Hole` (`mouse_hole`).
Synthesized autonomously by `MetaCoreSynthesizer` (zero hardcode!).
"""

from core.object_knowledge_core import OBJECT_KNOWLEDGE_BASE, ObjectAnatomySpec

SPEC = ObjectAnatomySpec.model_validate({ 'object_id': 'mouse_hole',
  'display_name': 'Rustic Barn Mouse Hole',
  'category': 'city_architecture',
  'builder_key': 'generated_builder',
  'real_anatomy_parts': [ 'base_wall_panel',
                          'arch_entrance_recess',
                          'arch_top_dome',
                          'floor_threshold',
                          'left_grain_crumb',
                          'right_grain_crumb'],
  'typical_dimensions_m': [0.35, 0.4, 0.15],
  'default_height_m': 0.4,
  'surface_finish': 'matte_wood',
  'motion_behavior': 'static',
  'placement_layer': 'ground',
  'silhouette_notes': 'An arched recessed aperture cut into a weathered wooden '
                      'plank wall, complete with subtle interior shadow depth '
                      'and grain details.',
  'aliases': [ 'mouse_hole',
               'mouse hole',
               'rodent entrance',
               'barn wall hole',
               'milo doorway'],
  'composite_parts': [ { 'part_name': 'base_wall_panel',
                         'shape': 'box',
                         'size': [0.45, 0.5, 0.08],
                         'offset': [0.0, 0.25, 0.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#6e472c',
                         'finish': 'matte_wood'},
                       { 'part_name': 'arch_entrance_recess',
                         'shape': 'box',
                         'size': [0.12, 0.16, 0.05],
                         'offset': [0.0, 0.12, 0.02],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#1f140c',
                         'finish': 'matte_wood'},
                       { 'part_name': 'arch_top_dome',
                         'shape': 'sphere',
                         'size': [0.12, 0.08, 0.05],
                         'offset': [0.0, 0.2, 0.02],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#1f140c',
                         'finish': 'fluffy_matte'},
                       { 'part_name': 'floor_threshold',
                         'shape': 'box',
                         'size': [0.14, 0.02, 0.06],
                         'offset': [0.0, 0.04, 0.03],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#52331d',
                         'finish': 'matte_wood'},
                       { 'part_name': 'left_grain_crumb',
                         'shape': 'sphere',
                         'size': [0.02, 0.02, 0.02],
                         'offset': [-0.06, 0.01, 0.08],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#d4a373',
                         'finish': 'glazed_food'},
                       { 'part_name': 'right_grain_crumb',
                         'shape': 'capsule',
                         'size': [0.015, 0.03, 0.015],
                         'offset': [0.07, 0.015, 0.07],
                         'rotation': [0.2, 0.5, 0.1],
                         'color': '#faedcd',
                         'finish': 'glazed_food'}]})


def register() -> ObjectAnatomySpec:
    """Register `mouse_hole` into the live Object Knowledge Base."""
    OBJECT_KNOWLEDGE_BASE[SPEC.object_id] = SPEC
    return SPEC
