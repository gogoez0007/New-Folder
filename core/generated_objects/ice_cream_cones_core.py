"""
Auto-generated Object Core Module: `Ice Cream Cones` (`ice_cream_cones`).
Synthesized autonomously by `MetaCoreSynthesizer` (zero hardcode!).
"""

from core.object_knowledge_core import OBJECT_KNOWLEDGE_BASE, ObjectAnatomySpec

SPEC = ObjectAnatomySpec.model_validate({ 'object_id': 'ice_cream_cones',
  'display_name': 'Ice Cream Cones',
  'category': 'food_kitchen',
  'builder_key': 'generated_builder',
  'real_anatomy_parts': [ 'cone_primary',
                          'cone_secondary',
                          'scoop_pink',
                          'scoop_mint',
                          'scoop_yellow',
                          'topping_cherry'],
  'typical_dimensions_m': [0.35, 0.5, 0.35],
  'default_height_m': 0.5,
  'surface_finish': 'glazed_food',
  'motion_behavior': 'static',
  'placement_layer': 'ground',
  'silhouette_notes': 'A collection of two stacked waffle cones topped with '
                      'colorful cartoon scoops of ice cream and a cherry on '
                      'top.',
  'aliases': [ 'ice_cream_cones',
               'ice cream cones',
               'ice cream',
               'waffle cones',
               'dessert'],
  'composite_parts': [ { 'part_name': 'cone_primary',
                         'shape': 'cone',
                         'size': [0.15, 0.3, 0.15],
                         'offset': [-0.08, 0.15, 0.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#d2a679',
                         'finish': 'matte_wood'},
                       { 'part_name': 'cone_secondary',
                         'shape': 'cone',
                         'size': [0.14, 0.28, 0.14],
                         'offset': [0.08, 0.14, 0.05],
                         'rotation': [0.0, 0.0, -0.15],
                         'color': '#c89b6b',
                         'finish': 'matte_wood'},
                       { 'part_name': 'scoop_pink',
                         'shape': 'sphere',
                         'size': [0.18, 0.18, 0.18],
                         'offset': [-0.08, 0.34, 0.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#ff9ebb',
                         'finish': 'glazed_food'},
                       { 'part_name': 'scoop_mint',
                         'shape': 'sphere',
                         'size': [0.17, 0.17, 0.17],
                         'offset': [0.08, 0.32, 0.05],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#a8e6cf',
                         'finish': 'glazed_food'},
                       { 'part_name': 'scoop_yellow',
                         'shape': 'sphere',
                         'size': [0.15, 0.15, 0.15],
                         'offset': [0.02, 0.45, 0.02],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#ffd3b6',
                         'finish': 'glazed_food'},
                       { 'part_name': 'topping_cherry',
                         'shape': 'sphere',
                         'size': [0.06, 0.06, 0.06],
                         'offset': [0.02, 0.54, 0.02],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#ff3333',
                         'finish': 'latex_glossy'}]})


def register() -> ObjectAnatomySpec:
    """Register `ice_cream_cones` into the live Object Knowledge Base."""
    OBJECT_KNOWLEDGE_BASE[SPEC.object_id] = SPEC
    return SPEC
