"""
Auto-generated Object Core Module: `Sunset Sky Ocean Horizon` (`sunset_sky`).
Synthesized autonomously by `MetaCoreSynthesizer` (zero hardcode!).
"""

from core.object_knowledge_core import OBJECT_KNOWLEDGE_BASE, ObjectAnatomySpec

SPEC = ObjectAnatomySpec.model_validate({ 'object_id': 'sunset_sky',
  'display_name': 'Sunset Sky Ocean Horizon',
  'category': 'nature_sky',
  'builder_key': 'generated_builder',
  'real_anatomy_parts': [ 'ocean_base',
                          'horizon_glow',
                          'sun_disc',
                          'lower_sky_band',
                          'mid_sky_band',
                          'upper_sky_band'],
  'typical_dimensions_m': [1.5, 1.0, 0.2],
  'default_height_m': 1.0,
  'surface_finish': 'latex_glossy',
  'motion_behavior': 'water_bob',
  'placement_layer': 'ground',
  'silhouette_notes': 'A dramatic layered sunset sky over a calm ocean horizon '
                      'featuring a glowing sun and atmospheric gradient bands.',
  'aliases': [ 'sunset_sky',
               'sunset sky',
               'sunset_horizon',
               'ocean_sunset_backdrop',
               'dramatic_sky'],
  'composite_parts': [ { 'part_name': 'ocean_base',
                         'shape': 'box',
                         'size': [1.5, 0.2, 0.2],
                         'offset': [0.0, 0.1, 0.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#1b263b',
                         'finish': 'latex_glossy'},
                       { 'part_name': 'horizon_glow',
                         'shape': 'box',
                         'size': [1.5, 0.1, 0.18],
                         'offset': [0.0, 0.25, 0.0],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#ff7700',
                         'finish': 'latex_glossy'},
                       { 'part_name': 'sun_disc',
                         'shape': 'sphere',
                         'size': [0.3, 0.3, 0.3],
                         'offset': [0.0, 0.4, -0.05],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#ffcc00',
                         'finish': 'latex_glossy'},
                       { 'part_name': 'lower_sky_band',
                         'shape': 'box',
                         'size': [1.5, 0.25, 0.15],
                         'offset': [0.0, 0.45, -0.1],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#d90429',
                         'finish': 'latex_glossy'},
                       { 'part_name': 'mid_sky_band',
                         'shape': 'box',
                         'size': [1.5, 0.25, 0.15],
                         'offset': [0.0, 0.7, -0.1],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#7209b7',
                         'finish': 'latex_glossy'},
                       { 'part_name': 'upper_sky_band',
                         'shape': 'box',
                         'size': [1.5, 0.2, 0.15],
                         'offset': [0.0, 0.9, -0.1],
                         'rotation': [0.0, 0.0, 0.0],
                         'color': '#3a0ca3',
                         'finish': 'latex_glossy'}]})


def register() -> ObjectAnatomySpec:
    """Register `sunset_sky` into the live Object Knowledge Base."""
    OBJECT_KNOWLEDGE_BASE[SPEC.object_id] = SPEC
    return SPEC
