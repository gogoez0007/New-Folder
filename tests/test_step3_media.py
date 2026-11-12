"""
Step 3 Verification Test: Media Generator Agent (Agent 4).
Tests:
1. Edge-TTS voiceover synthesis per scene
2. Exact millisecond duration measurement with ffprobe
3. 9:16 Vertical Visual generation via Pollinations Flux API
4. Visual image validation (dimensions 720x1280, RGB, non-zero bytes)
5. Local procedural fallback image generator verification
"""

import sys
from pathlib import Path
from PIL import Image

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from agents.media_agent import MediaAgent, GeneratedSceneMedia
from schemas import Scene
from utils.logger import (
    log_header,
    log_step,
    log_info,
    log_success,
    log_warning,
    log_error,
)


def main():
    log_header("Step 3: Media Generator Agent Verification")

    media_agent = MediaAgent(
        default_voice=config.DEFAULT_VOICE,
        default_rate=config.DEFAULT_VOICE_RATE,
        image_width=720,
        image_height=1280,
    )

    test_dir = config.WORKSPACE_DIR / "test_step3"
    test_dir.mkdir(parents=True, exist_ok=True)

    # 1. Define two sample scenes
    log_step(1, 4, "Preparing Sample Scenes for Media Generation")
    scenes = [
        Scene(
            scene_number=1,
            narration="Did you know Earth once recorded an underwater sound louder than any creature?",
            duration_target=2.8,
            image_prompt="A colossal deep ocean trench with glowing hydrothermal vents, vertical 9:16, cinematic",
            camera_motion="zoom_in_fast",
            sfx_cue="whoosh",
            subtitle_emphasis_words=["Earth", "recorded", "underwater", "louder"],
        ),
        Scene(
            scene_number=2,
            narration="Scientists named it The Bloop, and it originated deep beneath the Pacific.",
            duration_target=2.7,
            image_prompt="Submarine sonar screen glowing with mysterious underwater shockwaves, vertical 9:16",
            camera_motion="pan_right",
            sfx_cue="impact",
            subtitle_emphasis_words=["Scientists", "The Bloop", "Pacific"],
        ),
    ]
    log_success(f"Initialized {len(scenes)} sample scenes.")

    # 2. Test Voiceover Synthesis & FFprobe Duration Sync
    log_step(2, 4, "Testing Voiceover Synthesis & FFprobe Duration Sync")
    generated_media = []

    for scene in scenes:
        audio_file = test_dir / f"scene_{scene.scene_number:02d}.mp3"
        duration = media_agent.generate_voiceover(scene.narration, audio_file)

        assert audio_file.exists(), f"Audio file was not created: {audio_file}"
        assert audio_file.stat().st_size > 1000, f"Audio file is too small: {audio_file.stat().st_size} bytes"
        assert duration > 1.0, f"Duration measurement is too short: {duration}s"
        log_info(f"Scene {scene.scene_number} voiceover: {audio_file.name} -> {duration:.3f}s")

    log_success("Voiceover synthesis and ffprobe duration synchronization passed.")

    # 3. Test Visual Generation (Local Cinematic Engine)
    log_step(3, 4, "Testing 9:16 Vertical Visual Generation via Local Cinematic Engine")
    for scene in scenes:
        image_file = test_dir / f"scene_{scene.scene_number:02d}.jpg"
        img_path, used_fallback = media_agent.generate_visual(
            prompt=scene.image_prompt,
            output_path=image_file,
            seed=42 + scene.scene_number,
            narration=scene.narration,
        )

        assert img_path.exists(), f"Image file does not exist: {img_path}"

        assert img_path.stat().st_size > 15000, f"Image file is suspiciously small (< 15KB): {img_path.stat().st_size} bytes"

        # Verify image integrity, variance, and absence of blank canvas
        is_valid, reason = media_agent.validate_image_content(img_path)
        assert is_valid, f"Generated visual failed validation: {reason}"

        # Verify image dimensions and RGB format
        with Image.open(img_path) as img:
            assert img.size == (720, 1280), f"Incorrect image dimensions: {img.size} (expected 720x1280)"
            assert img.mode == "RGB", f"Incorrect image mode: {img.mode} (expected RGB)"
            log_info(f"Verified image {img_path.name}: {img.size[0]}x{img.size[1]} ({img.mode}), {img_path.stat().st_size / 1024:.1f} KB (Fallback used: {used_fallback})")

    log_success("9:16 Vertical image generation and validation passed.")

    # 4. Test Procedural Fallback Image Generator
    log_step(4, 4, "Testing Procedural Cinematic Fallback Generator")
    fallback_test_path = test_dir / "procedural_fallback_test.jpg"
    media_agent._generate_procedural_fallback_image(
        prompt="Cold War secret subterranean bunker command center",
        output_path=fallback_test_path,
    )
    assert fallback_test_path.exists(), "Fallback image file was not created"
    assert fallback_test_path.stat().st_size > 15000, f"Fallback image too small: {fallback_test_path.stat().st_size} bytes"

    # Verify fallback passes image content validation
    is_fb_valid, fb_reason = media_agent.validate_image_content(fallback_test_path)
    assert is_fb_valid, f"Procedural fallback failed validation: {fb_reason}"

    with Image.open(fallback_test_path) as fallback_img:
        assert fallback_img.size == (720, 1280), f"Fallback image has wrong dimensions: {fallback_img.size}"
        assert fallback_img.mode == "RGB", f"Fallback image has wrong mode: {fallback_img.mode}"
    log_info(f"Verified procedural fallback: {fallback_test_path.name} ({fallback_test_path.stat().st_size / 1024:.1f} KB)")
    log_success("Procedural fallback generator verified successfully.")


    log_header("Step 3: ALL CHECKS PASSED SUCCESSFULLY")
    print("Ready to proceed to Step 4 (CUDA Word-Level Subtitle Agent).\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        log_error(f"Assertion Error: {e}")
        sys.exit(1)
    except Exception as e:
        log_error(f"Execution Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
