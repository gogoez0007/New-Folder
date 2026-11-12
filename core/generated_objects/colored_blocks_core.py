"""
Auto-generated Object Core Module: `Colorful Block Stairs` (`colored_blocks`).
Synthesized autonomously by `MetaCoreSynthesizer` (zero hardcode!).
"""

from core.object_knowledge_core import OBJECT_KNOWLEDGE_BASE, ObjectAnatomySpec

SPEC = ObjectAnatomySpec.model_validate({ 'object_id': 'colored_blocks',
  'display_name': 'Colorful Block Stairs',
  'category': 'sports_games',
  'builder_key': 'generated_builder',
  'real_anatomy_parts': [ 'bottom_step',
                          'second_step',
                          'third_step',
                          'fourth_step',
                          'top_step'],
  'typical_dimensions_m': [1.0, 1.0, 1.6],
  'default_height_m': 1.0,
  'surface_finish': 'latex_glossy',
  'motion_behavior': 'static',
  'placement_layer': 'ground',
  'silhouette_notes': 'A series of vibrant, rectangular blocks stacked and '
                      'offset to form a climbable staircase, with a playful, '
                      'cartoon aesthetic. Each step is a distinct, bright '
                      'color.',
  'aliases': [ 'colored_blocks',
               'colored blocks',
               'musical_stairs',
               'vibrant_steps',
               'playground_blocks'],
  'composite_parts': [ { 'part_name': 'bottom_step',
                         'shape': 'box',
                         'size': [1.0, 0.2, 0.4],
                         'offset': [0.0, 0.1, 0.2],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#FF0000',
                         'finish': 'latex_glossy'},
                       { 'part_name': 'second_step',
                         'shape': 'box',
                         'size': [0.9, 0.2, 0.4],
                         'offset': [0.0, 0.3, -0.2],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#0000FF',
                         'finish': 'latex_glossy'},
                       { 'part_name': 'third_step',
                         'shape': 'box',
                         'size': [0.8, 0.2, 0.4],
                         'offset': [0.0, 0.5, -0.6],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#00FF00',
                         'finish': 'latex_glossy'},
                       { 'part_name': 'fourth_step',
                         'shape': 'box',
                         'size': [0.7, 0.2, 0.4],
                         'offset': [0.0, 0.7, -1.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#FFFF00',
                         'finish': 'latex_glossy'},
                       { 'part_name': 'top_step',
                         'shape': 'box',
                         'size': [0.6, 0.2, 0.4],
                         'offset': [0.0, 0.9, -1.4],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#800080',
                         'finish': 'latex_glossy'}]})


def register() -> ObjectAnatomySpec:
    """Register `colored_blocks` into the live Object Knowledge Base."""
    OBJECT_KNOWLEDGE_BASE[SPEC.object_id] = SPEC
    return SPEC
