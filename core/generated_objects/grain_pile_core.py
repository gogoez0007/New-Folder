"""
Auto-generated Object Core Module: `Pile of Grains` (`grain_pile`).
Synthesized autonomously by `MetaCoreSynthesizer` (zero hardcode!).
"""

from core.object_knowledge_core import OBJECT_KNOWLEDGE_BASE, ObjectAnatomySpec

SPEC = ObjectAnatomySpec.model_validate({ 'object_id': 'grain_pile',
  'display_name': 'Pile of Grains',
  'category': 'nature_flora',
  'builder_key': 'generated_builder',
  'real_anatomy_parts': [ 'base_mound',
                          'grain_kernel_1',
                          'grain_kernel_2',
                          'grain_kernel_3',
                          'grain_kernel_4',
                          'grain_kernel_5'],
  'typical_dimensions_m': [0.4, 0.25, 0.4],
  'default_height_m': 0.3,
  'surface_finish': 'matte_wood',
  'motion_behavior': 'static',
  'placement_layer': 'ground',
  'silhouette_notes': 'A mounded cluster of individual golden-yellow wheat '
                      'grains forming a natural organic heap.',
  'aliases': [ 'grain_pile',
               'grain pile',
               'wheat_pile',
               'heap_of_corn',
               'barn_grain'],
  'composite_parts': [ { 'part_name': 'base_mound',
                         'shape': 'cone',
                         'size': [0.38, 0.22, 0.38],
                         'offset': [0.0, 0.11, 0.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#e3b74a',
                         'finish': 'matte_wood'},
                       { 'part_name': 'grain_kernel_1',
                         'shape': 'capsule',
                         'size': [0.03, 0.06, 0.03],
                         'offset': [0.08, 0.05, 0.1],
                         'rotation': [0.2, 0.5, 1.1],
                         'color': '#f2cc59',
                         'finish': 'matte_wood'},
                       { 'part_name': 'grain_kernel_2',
                         'shape': 'capsule',
                         'size': [0.03, 0.06, 0.03],
                         'offset': [-0.1, 0.08, 0.05],
                         'rotation': [-0.5, 0.2, 0.4],
                         'color': '#d9a436',
                         'finish': 'matte_wood'},
                       { 'part_name': 'grain_kernel_3',
                         'shape': 'capsule',
                         'size': [0.03, 0.06, 0.03],
                         'offset': [0.02, 0.15, -0.09],
                         'rotation': [1.2, -0.3, 0.1],
                         'color': '#f5d269',
                         'finish': 'matte_wood'},
                       { 'part_name': 'grain_kernel_4',
                         'shape': 'capsule',
                         'size': [0.03, 0.06, 0.03],
                         'offset': [-0.07, 0.12, -0.06],
                         'rotation': [-0.8, 1.1, -0.5],
                         'color': '#e8bd4c',
                         'finish': 'matte_wood'},
                       { 'part_name': 'grain_kernel_5',
                         'shape': 'capsule',
                         'size': [0.03, 0.06, 0.03],
                         'offset': [0.12, 0.07, -0.04],
                         'rotation': [0.1, -1.2, 0.8],
                         'color': '#f0c451',
                         'finish': 'matte_wood'}]})


def register() -> ObjectAnatomySpec:
    """Register `grain_pile` into the live Object Knowledge Base."""
    OBJECT_KNOWLEDGE_BASE[SPEC.object_id] = SPEC
    return SPEC
