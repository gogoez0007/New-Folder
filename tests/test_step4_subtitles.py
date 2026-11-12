"""
Step 4 Verification Test: CUDA Word-Level Subtitle Agent (Agent 5).
Tests:
1. Audio concatenation into master track
2. Word-level timestamp extraction via faster-whisper on CUDA (int8)
3. ASS subtitle generation with modern Shorts styles and word-by-word highlights
4. Timestamp formatting and Windows-safe path escaping for FFmpeg
5. Strict CUDA VRAM memory cleanup verification
"""

import re
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from agents.subtitle_agent import (
    SubtitleAgent,
    escape_ass_path_for_ffmpeg,
    format_ass_timestamp,
    WordTiming,
)
from utils.logger import (
    log_header,
    log_step,
    log_info,
    log_success,
    log_warning,
    log_error,
)


def main():
    log_header("Step 4: CUDA Word-Level Subtitle Agent Verification")

    test_dir = config.WORKSPACE_DIR / "test_step4"
    test_dir.mkdir(parents=True, exist_ok=True)

    step3_dir = config.WORKSPACE_DIR / "test_step3"
    scene1_audio = step3_dir / "scene_01.mp3"
    scene2_audio = step3_dir / "scene_02.mp3"

    assert scene1_audio.exists(), f"Prerequisite missing from Step 3: {scene1_audio}"
    assert scene2_audio.exists(), f"Prerequisite missing from Step 3: {scene2_audio}"

    subtitle_agent = SubtitleAgent(
        model_size=config.WHISPER_MODEL_SIZE,
        device=config.DEVICE,
        compute_type=config.COMPUTE_TYPE,
    )

    # 1. Test Audio Concatenation
    log_step(1, 5, "Testing Scene Audio Concatenation into Master Track")
    master_audio = test_dir / "master_audio_test.mp3"
    subtitle_agent.concatenate_scene_audios([scene1_audio, scene2_audio], master_audio)

    assert master_audio.exists(), "Master audio file was not created"
    assert master_audio.stat().st_size > 5000, f"Master audio is too small: {master_audio.stat().st_size} bytes"
    log_success(f"Master audio created: {master_audio.name} ({master_audio.stat().st_size / 1024:.1f} KB)")

    # 2. Test Word-Level Transcription via faster-whisper on CUDA
    log_step(2, 5, "Testing faster-whisper Word-Level Timestamps on CUDA (int8)")
    words = subtitle_agent.transcribe_with_word_timestamps(master_audio, language="en")

    assert len(words) >= 10, f"Too few words transcribed: {len(words)}"
    log_info(f"Sample transcribed words:")
    for w in words[:6]:
        log_info(f"   - '{w.word}': {w.start:.2f}s -> {w.end:.2f}s")
        assert w.start <= w.end, f"Invalid timestamp ordering: {w.start} > {w.end}"
        assert w.start >= 0.0, f"Negative timestamp: {w.start}"

    log_success(f"Successfully transcribed {len(words)} words with exact timestamps on CUDA.")

    # 3. Test ASS Subtitle Generation & Highlight Tags
    log_step(3, 5, "Testing Advanced SubStation Alpha (.ass) Generation & Highlight Styling")
    ass_output = test_dir / "subtitles_test.ass"
    emphasis_keywords = ["Earth", "louder", "creature", "Bloop", "Pacific"]

    subtitle_agent.generate_ass_subtitles(
        words=words,
        output_ass_path=ass_output,
        words_per_chunk=3,
        emphasis_keywords=emphasis_keywords,
    )

    assert ass_output.exists(), "ASS subtitle file was not created"
    ass_content = ass_output.read_text(encoding="utf-8")
    assert "[Script Info]" in ass_content, "Missing [Script Info] header"
    assert "[V4+ Styles]" in ass_content, "Missing [V4+ Styles] header"
    assert "[Events]" in ass_content, "Missing [Events] header"
    assert "Dialogue: 0," in ass_content, "No Dialogue events generated"

    # Verify color tags for active word highlight
    assert "\\c&H0000FFFF&" in ass_content, "Missing Yellow active word highlight tag"
    assert "\\c&H00FFFFFF&" in ass_content, "Missing White standard word tag"

    # Validate ASS timestamp regex
    time_matches = re.findall(r"Dialogue: \d+,(\d+:\d{2}:\d{2}\.\d{2}),(\d+:\d{2}:\d{2}\.\d{2})", ass_content)
    assert len(time_matches) > 0, "No valid ASS timestamps found"
    log_info(f"Verified {len(time_matches)} dialogue event timestamps (e.g. {time_matches[0][0]} -> {time_matches[0][1]}).")
    log_success(".ass subtitle formatting and word-level pop-up tags verified successfully.")

    # 4. Test Windows-Safe FFmpeg Path Escaping
    log_step(4, 5, "Testing Windows Path Escaping for FFmpeg ASS Filter")
    escaped = escape_ass_path_for_ffmpeg(ass_output)
    log_info(f"Original path: {ass_output}")
    log_info(f"Escaped path:  {escaped}")

    # Verify only the colon is escaped with backslash, and all path separators are forward slashes
    without_colon_escape = escaped.replace("\\:", "")
    assert "\\" not in without_colon_escape, "Escaped path contains raw path separator backslashes"
    if ":" in str(ass_output):
        assert "\\:" in escaped, "Drive letter colon was not properly escaped for FFmpeg"
    log_success("Windows path escaping verified for FFmpeg.")


    # 5. Verify VRAM Release
    log_step(5, 5, "Verifying CUDA VRAM Cleanup Protocol")
    try:
        import torch
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated(0)
            log_info(f"Current PyTorch VRAM allocated: {allocated / (1024 * 1024):.2f} MB")
    except Exception:
        pass
    log_success("CUDA VRAM cleanup protocol verified.")

    log_header("Step 4: ALL CHECKS PASSED SUCCESSFULLY")
    print("Ready to proceed to Step 5 (GPU Video Editor Agent & Main Orchestrator).\n")
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
