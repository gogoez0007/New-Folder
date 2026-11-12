"""
Auto-generated Object Core Module: `Pile of Grain Seeds` (`grain_seeds`).
Synthesized autonomously by `MetaCoreSynthesizer` (zero hardcode!).
"""

from core.object_knowledge_core import OBJECT_KNOWLEDGE_BASE, ObjectAnatomySpec

SPEC = ObjectAnatomySpec.model_validate({ 'object_id': 'grain_seeds',
  'display_name': 'Pile of Grain Seeds',
  'category': 'nature_flora',
  'builder_key': 'generated_builder',
  'real_anatomy_parts': [ 'seed_mound_base',
                          'seed_kernel_1',
                          'seed_kernel_2',
                          'seed_kernel_3',
                          'seed_kernel_4',
                          'seed_kernel_5'],
  'typical_dimensions_m': [0.4, 0.15, 0.4],
  'default_height_m': 0.3,
  'surface_finish': 'matte_wood',
  'motion_behavior': 'static',
  'placement_layer': 'ground',
  'silhouette_notes': 'A mounded pile of organic golden-brown seeds resting on '
                      'the ground for feeding chicks.',
  'aliases': [ 'grain_seeds',
               'grain seeds',
               'bird seeds',
               'feed pile',
               'corn kernels'],
  'composite_parts': [ { 'part_name': 'seed_mound_base',
                         'shape': 'sphere',
                         'size': [0.35, 0.12, 0.35],
                         'offset': [0.0, 0.06, 0.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#d4a373',
                         'finish': 'matte_wood'},
                       { 'part_name': 'seed_kernel_1',
                         'shape': 'capsule',
                         'size': [0.04, 0.08, 0.04],
                         'offset': [0.08, 0.1, 0.05],
                         'rotation': [0.2, 0.5, 1.1],
                         'color': '#e9edc9',
                         'finish': 'glazed_food'},
                       { 'part_name': 'seed_kernel_2',
                         'shape': 'capsule',
                         'size': [0.04, 0.08, 0.04],
                         'offset': [-0.09, 0.09, -0.06],
                         'rotation': [-0.4, 0.8, 0.2],
                         'color': '#ccd5ae',
                         'finish': 'glazed_food'},
                       { 'part_name': 'seed_kernel_3',
                         'shape': 'capsule',
                         'size': [0.04, 0.08, 0.04],
                         'offset': [0.03, 0.12, -0.1],
                         'rotation': [1.2, -0.2, 0.4],
                         'color': '#fefae0',
                         'finish': 'glazed_food'},
                       { 'part_name': 'seed_kernel_4',
                         'shape': 'capsule',
                         'size': [0.04, 0.08, 0.04],
                         'offset': [-0.05, 0.11, 0.08],
                         'rotation': [0.5, -1.1, 0.3],
                         'color': '#faedcd',
                         'finish': 'glazed_food'},
                       { 'part_name': 'seed_kernel_5',
                         'shape': 'capsule',
                         'size': [0.03, 0.07, 0.03],
                         'offset': [0.12, 0.07, -0.02],
                         'rotation': [0.8, 0.4, -0.7],
                         'color': '#d4a373',
                         'finish': 'glazed_food'}]})


def register() -> ObjectAnatomySpec:
    """Register `grain_seeds` into the live Object Knowledge Base."""
    OBJECT_KNOWLEDGE_BASE[SPEC.object_id] = SPEC
    return SPEC
