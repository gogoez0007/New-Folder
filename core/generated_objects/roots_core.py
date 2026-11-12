"""
Auto-generated Object Core Module: `Cave Roots` (`roots`).
Synthesized autonomously by `MetaCoreSynthesizer` (zero hardcode!).
"""

from core.object_knowledge_core import OBJECT_KNOWLEDGE_BASE, ObjectAnatomySpec

SPEC = ObjectAnatomySpec.model_validate({ 'object_id': 'roots',
  'display_name': 'Cave Roots',
  'category': 'nature_flora',
  'builder_key': 'generated_builder',
  'real_anatomy_parts': [ 'root_main_1',
                          'root_main_2',
                          'root_branch_1',
                          'root_branch_2',
                          'root_tendril_1'],
  'typical_dimensions_m': [0.8, 1.2, 0.8],
  'default_height_m': 1.2,
  'surface_finish': 'organic_bark',
  'motion_behavior': 'static',
  'placement_layer': 'ground',
  'silhouette_notes': 'A collection of gnarled, intertwining cave roots '
                      'hanging downwards from a tunnel ceiling or protruding '
                      'from walls.',
  'aliases': ['roots', 'tunnel_roots', 'cave_vines', 'hanging_roots'],
  'composite_parts': [ { 'part_name': 'root_main_1',
                         'shape': 'cylinder',
                         'size': [0.08, 1.2, 0.08],
                         'offset': [0.1, 0.6, -0.1],
                         'rotation': [0.1, 0.0, -0.2],
                         'color': '#4a3525',
                         'finish': 'organic_bark'},
                       { 'part_name': 'root_main_2',
                         'shape': 'cylinder',
                         'size': [0.06, 1.0, 0.06],
                         'offset': [-0.2, 0.7, 0.15],
                         'rotation': [-0.15, 0.0, 0.25],
                         'color': '#3d2a1c',
                         'finish': 'organic_bark'},
                       { 'part_name': 'root_branch_1',
                         'shape': 'capsule',
                         'size': [0.05, 0.6, 0.05],
                         'offset': [0.2, 0.4, -0.05],
                         'rotation': [0.4, 0.2, 0.5],
                         'color': '#523b2a',
                         'finish': 'organic_bark'},
                       { 'part_name': 'root_branch_2',
                         'shape': 'capsule',
                         'size': [0.04, 0.5, 0.04],
                         'offset': [-0.1, 0.5, 0.2],
                         'rotation': [-0.3, -0.4, -0.2],
                         'color': '#3d2a1c',
                         'finish': 'organic_bark'},
                       { 'part_name': 'root_tendril_1',
                         'shape': 'cone',
                         'size': [0.03, 0.4, 0.03],
                         'offset': [0.0, 0.2, -0.2],
                         'rotation': [0.2, 0.1, -0.1],
                         'color': '#2c1e14',
                         'finish': 'organic_bark'}]})


def register() -> ObjectAnatomySpec:
    """Register `roots` into the live Object Knowledge Base."""
    OBJECT_KNOWLEDGE_BASE[SPEC.object_id] = SPEC
    return SPEC
