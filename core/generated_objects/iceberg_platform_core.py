"""
Auto-generated Object Core Module: `Floating Iceberg Platform` (`iceberg_platform`).
Synthesized autonomously by `MetaCoreSynthesizer` (zero hardcode!).
"""

from core.object_knowledge_core import OBJECT_KNOWLEDGE_BASE, ObjectAnatomySpec

SPEC = ObjectAnatomySpec.model_validate({ 'object_id': 'iceberg_platform',
  'display_name': 'Floating Iceberg Platform',
  'category': 'water_beach',
  'builder_key': 'generated_builder',
  'real_anatomy_parts': [ 'main_ice_body',
                          'upper_peak_north',
                          'upper_peak_south',
                          'submerged_hull_base',
                          'ice_shelf_extension'],
  'typical_dimensions_m': [1.2, 0.9, 1.2],
  'default_height_m': 0.9,
  'surface_finish': 'ceramic',
  'motion_behavior': 'water_bob',
  'placement_layer': 'ground',
  'silhouette_notes': 'A jagged, multi-tiered chunk of floating glacial ice '
                      'featuring a flat top surface for jumping and a '
                      'partially submerged uneven hull.',
  'aliases': [ 'iceberg_platform',
               'iceberg platform',
               'ice_floe',
               'glacier_chunk',
               'floating_ice'],
  'composite_parts': [ { 'part_name': 'main_ice_body',
                         'shape': 'box',
                         'size': [1.2, 0.5, 1.2],
                         'offset': [0.0, 0.25, 0.0],
                         'rotation': [0.0, 0.2, 0.0],
                         'color': '#e0f7fa',
                         'finish': 'ceramic'},
                       { 'part_name': 'upper_peak_north',
                         'shape': 'cone',
                         'size': [0.6, 0.4, 0.6],
                         'offset': [0.2, 0.7, -0.2],
                         'rotation': [0.1, 0.0, 0.1],
                         'color': '#b2ebf2',
                         'finish': 'ceramic'},
                       { 'part_name': 'upper_peak_south',
                         'shape': 'cone',
                         'size': [0.5, 0.5, 0.5],
                         'offset': [-0.3, 0.75, 0.2],
                         'rotation': [-0.1, 0.0, -0.2],
                         'color': '#ffffff',
                         'finish': 'ceramic'},
                       { 'part_name': 'submerged_hull_base',
                         'shape': 'cylinder',
                         'size': [1.0, 0.3, 1.0],
                         'offset': [0.0, -0.15, 0.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#80deea',
                         'finish': 'ceramic'},
                       { 'part_name': 'ice_shelf_extension',
                         'shape': 'box',
                         'size': [0.7, 0.2, 0.7],
                         'offset': [-0.3, 0.1, -0.3],
                         'rotation': [0.0, 0.5, 0.0],
                         'color': '#e0f7fa',
                         'finish': 'ceramic'}]})


def register() -> ObjectAnatomySpec:
    """Register `iceberg_platform` into the live Object Knowledge Base."""
    OBJECT_KNOWLEDGE_BASE[SPEC.object_id] = SPEC
    return SPEC
