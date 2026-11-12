"""
Step 1 Verification Test: Environment, Schemas, Hardware & Scaffolding.
Validates:
1. Python dependencies importability
2. Pydantic schema serialization and validation rules
3. FFmpeg binary resolution and h264_nvenc encoder availability
4. PyTorch / CUDA GPU detection and memory allocation/cleanup
5. Synthetic audio SFX generator out-of-the-box readiness
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import (
    log_header,
    log_step,
    log_info,
    log_success,
    log_warning,
    log_error,
)
from utils.audio_gen import ensure_default_sfx
import config
from schemas import Scene, VideoScript, ViralBlueprint, ProductionBatch


def test_dependencies():
    """Verify all critical libraries can be imported cleanly."""
    log_step(1, 5, "Verifying Python Dependencies")
    modules = [
        ("pydantic", "Pydantic"),
        ("dotenv", "python-dotenv"),
        ("google.genai", "Google GenAI SDK"),
        ("yt_dlp", "yt-dlp"),
        ("edge_tts", "edge-tts"),
        ("faster_whisper", "faster-whisper"),
        ("torch", "PyTorch"),
        ("requests", "Requests"),
        ("numpy", "NumPy"),
        ("PIL", "Pillow"),
    ]

    missing = []
    for mod_name, label in modules:
        try:
            __import__(mod_name)
            log_info(f"Loaded {label} successfully.")
        except ImportError as e:
            missing.append((label, str(e)))
            log_error(f"Failed to import {label}: {e}")

    assert not missing, f"Missing required dependencies: {[m[0] for m in missing]}"
    log_success("All core dependencies imported successfully.")


def test_pydantic_schemas():
    """Verify schema construction, validation constraints, and JSON round-tripping."""
    log_step(2, 5, "Validating Pydantic Schemas & Serialization")

    sample_scene = Scene(
        scene_number=1,
        narration="Nobody talks about the dark secret behind this ancient discovery.",
        duration_target=2.8,
        image_prompt="Cinematic shot of ancient glowing ruins in deep misty jungle, vertical 9:16 composition, 8k render",
        camera_motion="zoom_in_fast",
        sfx_cue="whoosh",
        subtitle_emphasis_words=["dark", "secret", "ancient"],
    )

    sample_blueprint = ViralBlueprint(
        hook_strategy="Intense pattern interrupt using high curiosity gap and sound cue within 1.5 seconds.",
        scene_cut_frequency_seconds=2.5,
        pacing_and_rhythm="Rapid staccato cadence with dramatic sub-bass drops.",
        visual_style="Dark cinematic hyperrealism, high-contrast chiaroscuro lighting.",
        narrative_arc="Hook -> Intriguing mystery -> Escalation -> Shocking revelation -> CTA",
        retention_tactics=[
            "Micro-cliffhanger before 5s",
            "Dynamic zoompan motion on every cut",
            "Word-by-word highlighted subtitles",
        ],
    )

    sample_script = VideoScript(
        clip_index=1,
        title="The Ancient Mystery Nobody Talks About #Shorts #History",
        hook_text="Nobody talks about the dark secret behind this ancient discovery.",
        target_niche="Mysteries & Ancient History",
        language="en",
        scenes=[
            sample_scene,
            Scene(
                scene_number=2,
                narration="Deep beneath the temple, explorers found a sealed stone chamber.",
                duration_target=2.6,
                image_prompt="Archaeologists holding torches inside an ominous stone chamber, vertical 9:16",
                camera_motion="pan_right",
                sfx_cue="impact",
                subtitle_emphasis_words=["deep", "temple", "chamber"],
            ),
            Scene(
                scene_number=3,
                narration="And what was carved on the wall changed human history forever.",
                duration_target=3.0,
                image_prompt="Glowing celestial glyphs carved into granite wall, vertical 9:16 cinematic",
                camera_motion="zoom_in_slow",
                sfx_cue="whoosh",
                subtitle_emphasis_words=["carved", "changed", "history"],
            ),
        ],
        estimated_duration=8.4,
    )

    sample_batch = ProductionBatch(
        reference_title="Mind Blowing Historical Discovery #shorts",
        reference_duration_seconds=28.5,
        viral_blueprint=sample_blueprint,
        generated_scripts=[
            sample_script,
            VideoScript(
                clip_index=2,
                title="The Lost City Under the Ocean #Shorts #Mystery",
                hook_text="Scientists just found something at the bottom of the Mariana Trench.",
                target_niche="Mysteries & Ancient History",
                language="en",
                scenes=[
                    Scene(
                        scene_number=1,
                        narration="Scientists just found something at the bottom of the Mariana Trench.",
                        duration_target=2.5,
                        image_prompt="Deep submarine lights illuminating underwater monolithic structures, vertical 9:16",
                        camera_motion="zoom_in_fast",
                        sfx_cue="impact",
                        subtitle_emphasis_words=["scientists", "bottom", "trench"],
                    ),
                    Scene(
                        scene_number=2,
                        narration="It wasn't a natural rock formation.",
                        duration_target=2.4,
                        image_prompt="Ancient underwater doorway made of metal alloy, vertical 9:16",
                        camera_motion="pan_left",
                        sfx_cue="whoosh",
                        subtitle_emphasis_words=["natural", "doorway"],
                    ),
                    Scene(
                        scene_number=3,
                        narration="And sonar detected an active pulsing frequency.",
                        duration_target=2.8,
                        image_prompt="Bioluminescent sonar pulse radiating through deep blue water, vertical 9:16",
                        camera_motion="zoom_in_slow",
                        sfx_cue="beep",
                        subtitle_emphasis_words=["sonar", "pulsing", "frequency"],
                    ),
                ],
                estimated_duration=7.7,
            ),
        ],
    )

    # Test serialization to JSON
    json_output = sample_batch.model_dump_json(indent=2)
    assert len(json_output) > 200, "Serialized JSON output is too short"
    log_info(f"ProductionBatch JSON successfully serialized ({len(json_output)} bytes).")

    # Test round-trip deserialization
    recovered_batch = ProductionBatch.model_validate_json(json_output)
    assert recovered_batch.reference_title == sample_batch.reference_title
    assert len(recovered_batch.generated_scripts) == 2
    assert recovered_batch.generated_scripts[0].scenes[0].camera_motion == "zoom_in_fast"
    log_success("Pydantic schema validation & serialization round-trip passed.")


def test_ffmpeg_and_nvenc():
    """Verify FFmpeg installation and h264_nvenc hardware acceleration."""
    log_step(3, 5, "Verifying FFmpeg & NVIDIA NVENC Acceleration")

    log_info(f"Resolved FFmpeg binary: {config.FFMPEG_BIN}")
    log_info(f"Resolved FFprobe binary: {config.FFPROBE_BIN}")

    nvenc_supported = config.check_nvenc_support()
    log_info(f"h264_nvenc encoder available: {nvenc_supported}")

    active_codec = config.get_active_encoder()
    log_info(f"Selected video encoder: {active_codec}")

    assert nvenc_supported, (
        "h264_nvenc is required for hardware accelerated encoding on NVIDIA RTX. "
        "Verify NVIDIA graphics drivers and FFmpeg build."
    )
    assert active_codec == "h264_nvenc"
    log_success("FFmpeg and h264_nvenc hardware encoder verified successfully.")


def test_cuda_hardware():
    """Verify GPU detection, ctranslate2 CUDA engine for faster-whisper, and VRAM management."""
    log_step(4, 5, "Verifying NVIDIA GPU & CUDA Acceleration")

    cuda_info = config.check_cuda_support()
    log_info(f"CUDA Status: {cuda_info}")

    assert cuda_info["cuda_available"], "NVIDIA GPU / CUDA acceleration is not detected."
    device_name = cuda_info.get("device_name", "NVIDIA GPU")
    log_info(f"Detected GPU Hardware: {device_name}")

    # Verify ctranslate2 CUDA capabilities for faster-whisper
    import ctranslate2
    c2_count = ctranslate2.get_cuda_device_count()
    assert c2_count > 0, "ctranslate2 did not detect any CUDA devices"
    supported_types = ctranslate2.get_supported_compute_types("cuda")
    log_info(f"ctranslate2 CUDA devices: {c2_count}")
    log_info(f"ctranslate2 supported compute types: {supported_types}")
    assert "int8" in supported_types, "int8 compute type not supported on CUDA"

    # Verify VRAM cleanup protocol via garbage collection
    import gc
    gc.collect()

    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            log_info("torch.cuda cache cleared.")
    except Exception:
        pass

    log_success(f"NVIDIA GPU verified on {device_name} with ctranslate2 CUDA (int8) ready.")



def test_sfx_generation():
    """Verify synthetic sound effect generation produces valid audio files."""
    log_step(5, 5, "Verifying Synthetic SFX Generator")

    sfx_files = ensure_default_sfx(config.SFX_DIR)
    log_info(f"Default SFX files in {config.SFX_DIR}:")
    for f in config.SFX_DIR.glob("*.wav"):
        size_kb = f.stat().st_size / 1024
        log_info(f"   - {f.name} ({size_kb:.1f} KB)")
        assert f.stat().st_size > 500, f"SFX file {f.name} is suspiciously small ({f.stat().st_size} bytes)"

    expected_sfx = ["whoosh.wav", "pop.wav", "beep.wav", "impact.wav"]
    for name in expected_sfx:
        expected_path = config.SFX_DIR / name
        assert expected_path.is_file(), f"Expected SFX file not found: {name}"

    log_success("All synthetic SFX files generated and verified.")


def main():
    log_header("Step 1: Environment, Hardware & Scaffolding Verification")
    try:
        test_dependencies()
        test_pydantic_schemas()
        test_ffmpeg_and_nvenc()
        test_cuda_hardware()
        test_sfx_generation()

        log_header("Step 1: ALL CHECKS PASSED SUCCESSFULLY")
        print("\nReady to proceed to Step 2.\n")
        return 0
    except AssertionError as e:
        log_error(f"Assertion failed: {e}")
        return 1
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
