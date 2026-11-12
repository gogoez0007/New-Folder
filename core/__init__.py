"""
Dynamic 3D Animation Core Architecture (`core/`):
1. `CharacterCore` (`core/character_core.py`): Dynamic multi-character cast generator (8-10 characters per clip)
2. `SceneCore` (`core/scene_core.py`): Dynamic multi-character 3D scene choreography & camera director
3. `BackgroundStoryCore` (`core/background_story_core.py`): Dynamic background story, world lore & 3D biome builder
4. `AutoGeneratorCore` (`core/auto_generator_core.py`): Autonomous orchestrator & Three.js WebGL GPU renderer
"""

from core.background_story_core import BackgroundStoryCore, BackgroundStorySpec
from core.character_core import CharacterCore, CharacterRoster, CharacterSpec
from core.scene_core import SceneCore, SceneDirectingSpec
from core.auto_generator_core import AutoGeneratorCore
from core.meta_core_synthesizer import MetaCoreSynthesizer
from core.expression_knowledge_core import ExpressionLearningCore
from core.physics_scene_validator import PhysicsSceneValidatorCore
from core.natural_motion_core import NaturalMotionCore

__all__ = [
    "BackgroundStoryCore",
    "BackgroundStorySpec",
    "CharacterCore",
    "CharacterRoster",
    "CharacterSpec",
    "SceneCore",
    "SceneDirectingSpec",
    "AutoGeneratorCore",
    "MetaCoreSynthesizer",
    "ExpressionLearningCore",
    "PhysicsSceneValidatorCore",
    "NaturalMotionCore",
]

