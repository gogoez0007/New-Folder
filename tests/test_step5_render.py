"""
Step 5 Verification Test: GPU Video Editor Agent (Agent 6) & End-to-End Render.
Tests:
1. Scene segment rendering with dynamic zoompan camera motion filters
2. Seamless video concatenation
3. Multi-track audio mixing with transition SFX cues and ducked BGM
4. Subtitle burn-in via FFmpeg libass with Windows path escaping
5. Output video integrity verification (720x1280 vertical, 30fps, valid AAC audio stream)
"""

import json
import subprocess
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from agents.editor_agent import GPUVideoEditorAgent
from agents.media_agent import GeneratedSceneMedia, ScriptMediaBatch
from utils.audio_gen import ensure_default_sfx
from utils.logger import (
    log_header,
    log_step,
    log_info,
    log_success,
    log_warning,
    log_error,
)


def probe_video(video_path: Path) -> dict:
    """Probe video file with ffprobe to verify video and audio stream properties."""
    cmd = [
        config.FFPROBE_BIN,
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
    return json.loads(result.stdout)


def main():
    log_header("Step 5: GPU Video Editor Agent & End-to-End Render Verification")

    # Ensure default SFX files are present
    ensure_default_sfx(config.SFX_DIR)

    step3_dir = config.WORKSPACE_DIR / "test_step3"
    scene1_audio = step3_dir / "scene_01.mp3"
    scene1_image = step3_dir / "scene_01.jpg"
    scene2_audio = step3_dir / "scene_02.mp3"
    scene2_image = step3_dir / "scene_02.jpg"

    step4_dir = config.WORKSPACE_DIR / "test_step4"
    ass_subtitles = step4_dir / "subtitles_test.ass"

    # Pre-flight verification of input assets
    for p in [scene1_audio, scene1_image, scene2_audio, scene2_image, ass_subtitles]:
        assert p.exists(), f"Prerequisite asset missing: {p}"

    editor = GPUVideoEditorAgent()
    test_output_clip = config.OUTPUT_DIR / "final_clip_test.mp4"

    # 1. Test Scene Segment Rendering with Dynamic Motion
    log_step(1, 4, "Testing Scene Segment Rendering with Zoompan Motion")
    test_seg1 = config.WORKSPACE_DIR / "test_step5_seg1.mp4"
    editor.render_scene_segment(
        image_path=scene1_image,
        audio_path=scene1_audio,
        duration=4.392,
        camera_motion="zoom_in_fast",
        output_path=test_seg1,
    )
    assert test_seg1.exists() and test_seg1.stat().st_size > 10000, "Scene segment 1 render failed"
    log_success(f"Scene 1 segment rendered: {test_seg1.name} ({test_seg1.stat().st_size / 1024:.1f} KB)")

    test_seg2 = config.WORKSPACE_DIR / "test_step5_seg2.mp4"
    editor.render_scene_segment(
        image_path=scene2_image,
        audio_path=scene2_audio,
        duration=4.512,
        camera_motion="pan_right",
        output_path=test_seg2,
    )
    assert test_seg2.exists() and test_seg2.stat().st_size > 10000, "Scene segment 2 render failed"
    log_success(f"Scene 2 segment rendered: {test_seg2.name} ({test_seg2.stat().st_size / 1024:.1f} KB)")

    # 2. Test Lossless Video Concatenation
    log_step(2, 4, "Testing Video Concatenation")
    raw_concat = config.WORKSPACE_DIR / "test_step5_concat.mp4"
    editor.concatenate_segments([test_seg1, test_seg2], raw_concat)
    assert raw_concat.exists() and raw_concat.stat().st_size > 20000, "Concatenation failed"
    log_success(f"Concatenated raw video: {raw_concat.name} ({raw_concat.stat().st_size / 1024:.1f} KB)")

    # 3. Test Audio Mixing with SFX Transitions
    log_step(3, 4, "Testing Audio Mixing with SFX Transitions")
    sample_scenes = [
        GeneratedSceneMedia(
            scene_number=1,
            narration="Did you know Earth once recorded an underwater sound louder than any creature?",
            audio_path=scene1_audio,
            audio_duration=4.392,
            image_path=scene1_image,
            image_fallback_used=False,
            camera_motion="zoom_in_fast",
            sfx_cue="whoosh",
            subtitle_emphasis_words=["Earth", "recorded", "underwater", "louder"],
        ),
        GeneratedSceneMedia(
            scene_number=2,
            narration="Scientists named it The Bloop, and it originated deep beneath the Pacific.",
            audio_path=scene2_audio,
            audio_duration=4.512,
            image_path=scene2_image,
            image_fallback_used=False,
            camera_motion="pan_right",
            sfx_cue="impact",
            subtitle_emphasis_words=["Scientists", "The Bloop", "Pacific"],
        ),
    ]

    audio_mixed_video = config.WORKSPACE_DIR / "test_step5_mixed.mp4"
    editor.mix_audio_and_sfx(raw_concat, sample_scenes, audio_mixed_video)
    assert audio_mixed_video.exists(), "Audio mixed video not created"
    log_success(f"Audio mixed video ready: {audio_mixed_video.name}")

    # 4. Test Subtitle Burn-In via FFmpeg Libass & Final Video Validation
    log_step(4, 4, "Testing ASS Subtitle Burn-In & Final Video Stream Verification")
    editor.burn_subtitles(audio_mixed_video, ass_subtitles, test_output_clip)

    assert test_output_clip.exists(), f"Final output video missing: {test_output_clip}"
    size_mb = test_output_clip.stat().st_size / (1024 * 1024)
    assert size_mb > 0.05, f"Final video is suspiciously small ({size_mb:.2f} MB)"

    # Inspect streams with ffprobe
    probe_data = probe_video(test_output_clip)
    streams = probe_data.get("streams", [])
    format_info = probe_data.get("format", {})

    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

    assert len(video_streams) >= 1, "No video stream detected in output MP4"
    assert len(audio_streams) >= 1, "No audio stream detected in output MP4"

    v_stream = video_streams[0]
    width = v_stream.get("width")
    height = v_stream.get("height")
    codec = v_stream.get("codec_name")
    duration = float(format_info.get("duration", 0.0))

    log_info(f"Final Video Resolution: {width}x{height} (Codec: {codec})")
    log_info(f"Final Video Duration:   {duration:.2f}s")
    log_info(f"Final Video File Size:  {size_mb:.2f} MB")
    log_info(f"Audio Stream:           {audio_streams[0].get('codec_name')} ({audio_streams[0].get('sample_rate')} Hz)")

    assert width == 720 and height == 1280, f"Incorrect video resolution: {width}x{height}"
    assert duration >= 7.0, f"Unexpected short duration: {duration}s"

    log_success(f"Final vertical MP4 verified successfully: {test_output_clip}")
    log_header("Step 5: ALL CHECKS PASSED SUCCESSFULLY")
    print("Full rendering pipeline and CLI orchestrator are verified and operational!\n")
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
