"""
Auto-generated Object Core Module: `Dirt Tunnel Entrance` (`dirt_tunnel`).
Synthesized autonomously by `MetaCoreSynthesizer` (zero hardcode!).
"""

from core.object_knowledge_core import OBJECT_KNOWLEDGE_BASE, ObjectAnatomySpec

SPEC = ObjectAnatomySpec.model_validate({ 'object_id': 'dirt_tunnel',
  'display_name': 'Dirt Tunnel Entrance',
  'category': 'nature_flora',
  'builder_key': 'generated_builder',
  'real_anatomy_parts': [ 'earth_mound_base',
                          'tunnel_interior',
                          'tunnel_rim_top',
                          'grass_tuft_left',
                          'grass_tuft_right',
                          'exposed_rock_top'],
  'typical_dimensions_m': [1.2, 1.2, 1.5],
  'default_height_m': 1.2,
  'surface_finish': 'organic_bark',
  'motion_behavior': 'static',
  'placement_layer': 'ground',
  'silhouette_notes': 'A cylindrical hollow subterranean burrow dug into '
                      'earthy mounds, featuring a dark interior tube and '
                      'reinforced soil rim.',
  'aliases': [ 'dirt_tunnel',
               'dirt tunnel',
               'earth_burrow',
               'ground_tunnel',
               'mud_hole'],
  'composite_parts': [ { 'part_name': 'earth_mound_base',
                         'shape': 'box',
                         'size': [1.4, 0.8, 1.6],
                         'offset': [0.0, 0.4, 0.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#5c4033',
                         'finish': 'organic_bark'},
                       { 'part_name': 'tunnel_interior',
                         'shape': 'cylinder',
                         'size': [0.8, 1.4, 0.8],
                         'offset': [0.0, 0.6, -0.2],
                         'rotation': [1.5708, 0.0, 0.0],
                         'color': '#1a110b',
                         'finish': 'fluffy_matte'},
                       { 'part_name': 'tunnel_rim_top',
                         'shape': 'torus',
                         'size': [0.9, 0.15, 0.15],
                         'offset': [0.0, 0.9, 0.45],
                         'rotation': [1.5708, 0.0, 0.0],
                         'color': '#6e4734',
                         'finish': 'organic_bark'},
                       { 'part_name': 'grass_tuft_left',
                         'shape': 'cone',
                         'size': [0.15, 0.3, 0.15],
                         'offset': [-0.7, 0.85, 0.5],
                         'rotation': [0.0, 0.0, -0.3],
                         'color': '#4c9a2a',
                         'finish': 'waxy_foliage'},
                       { 'part_name': 'grass_tuft_right',
                         'shape': 'cone',
                         'size': [0.18, 0.35, 0.18],
                         'offset': [0.68, 0.85, 0.48],
                         'rotation': [0.0, 0.0, 0.25],
                         'color': '#4c9a2a',
                         'finish': 'waxy_foliage'},
                       { 'part_name': 'exposed_rock_top',
                         'shape': 'sphere',
                         'size': [0.25, 0.2, 0.2],
                         'offset': [0.45, 0.95, 0.3],
                         'rotation': [0.2, 0.5, 0.1],
                         'color': '#8c8c8c',
                         'finish': 'ceramic'}]})


def register() -> ObjectAnatomySpec:
    """Register `dirt_tunnel` into the live Object Knowledge Base."""
    OBJECT_KNOWLEDGE_BASE[SPEC.object_id] = SPEC
    return SPEC
