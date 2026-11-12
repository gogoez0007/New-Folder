"""
Step 2 Verification Test: Real YouTube Short Intake, Visual Contact Sheet,
Whisper Audio Analysis & Multimodal Gemini Viral Deconstruction.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from PIL import Image

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from agents.scout_agent import TrendScoutAgent
from agents.analyst_writer_agent import AnalystWriterAgent
from agents.subtitle_agent import SubtitleAgent
from schemas import ProductionBatch
from utils.logger import (
    log_header,
    log_step,
    log_info,
    log_success,
    log_warning,
    log_error,
)


def extract_visual_contact_sheet(
    video_path: Path,
    output_image_path: Path,
    duration: float,
    grid_cols: int = 3,
    grid_rows: int = 3,
) -> Path:
    """
    Extract evenly spaced frames across the video and stitch them into a 3x3 contact sheet.
    Enables visual verification of actual video frames.
    """
    output_image_path.parent.mkdir(parents=True, exist_ok=True)
    total_frames = grid_cols * grid_rows
    temp_dir = output_image_path.parent / "temp_contact_frames"
    temp_dir.mkdir(parents=True, exist_ok=True)

    log_info(f"Extracting {total_frames} frames from '{video_path.name}' across {duration:.1f}s...")

    frame_paths = []
    # Calculate sample timestamps
    timestamps = [duration * (i + 0.5) / total_frames for i in range(total_frames)]

    for idx, t in enumerate(timestamps):
        frame_file = temp_dir / f"frame_{idx:02d}.jpg"
        cmd = [
            config.FFMPEG_BIN,
            "-y",
            "-ss", f"{t:.3f}",
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(frame_file),
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=15)
            if frame_file.exists():
                frame_paths.append(frame_file)
        except Exception as e:
            log_warning(f"Could not extract frame at t={t:.2f}s: {e}")

    if not frame_paths:
        raise RuntimeError("Failed to extract any visual frames for contact sheet.")

    # Thumbnail size per cell (vertical 9:16)
    cell_w, cell_h = 240, 426
    canvas_w = cell_w * grid_cols
    canvas_h = cell_h * grid_rows

    contact_canvas = Image.new("RGB", (canvas_w, canvas_h), color=(15, 15, 18))

    for idx, fpath in enumerate(frame_paths):
        row = idx // grid_cols
        col = idx % grid_cols
        with Image.open(fpath) as img:
            thumb = img.convert("RGB").resize((cell_w, cell_h), Image.Resampling.LANCZOS)
            contact_canvas.paste(thumb, (col * cell_w, row * cell_h))

    contact_canvas.save(str(output_image_path), "JPEG", quality=92)

    # Clean up temp frames
    for f in frame_paths:
        f.unlink(missing_ok=True)
    temp_dir.rmdir()

    log_success(
        f"Visual contact sheet generated ({canvas_w}x{canvas_h}): {output_image_path.name} "
        f"({output_image_path.stat().st_size / 1024:.1f} KB)"
    )
    return output_image_path


def analyze_reference_audio_whisper(
    video_path: Path,
    output_json_path: Path,
    title: str,
    duration: float,
    url: Optional[str] = None,
) -> dict:
    """
    Run Whisper word-level transcription on the reference video's audio track.
    Saves structured transcript and timing analysis into JSON.
    """
    log_info(f"Extracting & transcribing audio track from '{video_path.name}' via Whisper...")
    subtitle_agent = SubtitleAgent()
    words = subtitle_agent.transcribe_with_word_timestamps(video_path, language=None)

    full_text = " ".join(w.word for w in words)
    analysis_data = {
        "title": title,
        "duration_seconds": duration,
        "source_url": url,
        "total_words": len(words),
        "full_transcript": full_text,
        "word_timings": [
            {"word": w.word, "start": round(w.start, 2), "end": round(w.end, 2)}
            for w in words
        ],
    }

    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(analysis_data, indent=2, ensure_ascii=False), encoding="utf-8")
    log_success(
        f"Reference audio analysis saved: {output_json_path.name} "
        f"({len(words)} words transcribed)"
    )
    return analysis_data


def main():
    log_header("Step 2: Real YouTube Short Intake, Visual Contact Sheet & Multimodal AI")

    # -------------------------------------------------------------------------
    # 1. Download REAL YouTube Short using Auto-Trend Search
    # -------------------------------------------------------------------------
    log_step(1, 4, "Auto-Searching & Downloading Real YouTube Short")
    scout = TrendScoutAgent()
    target_search_niche = "fakta unik sains"

    scout_result = scout.scout(niche=target_search_niche)

    log_info(f"Scout Title:    {scout_result.title}")
    log_info(f"Scout Duration: {scout_result.duration:.2f}s")
    log_info(f"Scout Views:    {scout_result.view_count:,}" if scout_result.view_count else "Scout Views: N/A")
    log_info(f"Scout URL:      {scout_result.url}")
    log_info(f"Scout File:     {scout_result.video_path}")

    assert scout_result.video_path.exists(), "Reference video does not exist on disk"
    assert scout_result.video_path.stat().st_size > 500000, (
        f"Reference video is suspiciously small ({scout_result.video_path.stat().st_size} bytes). "
        "Expected real video file."
    )
    log_success(f"Real YouTube Short verified on disk: {scout_result.video_path.name} ({scout_result.video_path.stat().st_size / (1024 * 1024):.2f} MB)")

    # -------------------------------------------------------------------------
    # 2. Visual Contact Sheet Extraction (9-frame grid)
    # -------------------------------------------------------------------------
    log_step(2, 4, "Extracting Visual Contact Sheet (9 Frames)")
    contact_sheet_path = config.WORKSPACE_DIR / "ref_contact_sheet.jpg"
    extract_visual_contact_sheet(
        video_path=scout_result.video_path,
        output_image_path=contact_sheet_path,
        duration=scout_result.duration,
        grid_cols=3,
        grid_rows=3,
    )
    assert contact_sheet_path.exists(), "Contact sheet was not created"
    assert contact_sheet_path.stat().st_size > 15000, "Contact sheet is suspiciously small"

    # -------------------------------------------------------------------------
    # 3. Whisper Audio Analysis & Transcript Extraction
    # -------------------------------------------------------------------------
    log_step(3, 4, "Analyzing Reference Audio & Speech Timestamps via Whisper")
    ref_analysis_path = config.WORKSPACE_DIR / "ref_analysis.json"
    audio_analysis = analyze_reference_audio_whisper(
        video_path=scout_result.video_path,
        output_json_path=ref_analysis_path,
        title=scout_result.title,
        duration=scout_result.duration,
        url=scout_result.url,
    )
    assert ref_analysis_path.exists(), "ref_analysis.json was not created"
    assert len(audio_analysis.get("full_transcript", "")) > 10, "Transcript is empty"
    log_info(f"Sample Transcript: \"{audio_analysis['full_transcript'][:120]}...\"")

    # -------------------------------------------------------------------------
    # 4. Multimodal Vision & Audio Analysis via Gemini API
    # -------------------------------------------------------------------------
    log_step(4, 4, "Performing Multimodal Viral Blueprint Analysis via Gemini API")
    analyst = AnalystWriterAgent()
    batch = analyst.analyze_and_generate(
        video_path=scout_result.video_path,
        target_niche="Fakta Unik & Misteri Sains Populer",
        clip_count=2,
        language="id",
        reference_title=scout_result.title,
        reference_duration=scout_result.duration,
    )

    # Validate output plan
    assert isinstance(batch, ProductionBatch), "Output is not an instance of ProductionBatch"
    assert len(batch.generated_scripts) == 2, f"Expected 2 generated scripts, got {len(batch.generated_scripts)}"
    assert (config.WORKSPACE_DIR / "production_plan.json").exists(), "production_plan.json missing in workspace"
    assert (config.OUTPUT_DIR / "production_plan.json").exists(), "production_plan.json missing in output"

    log_header("Step 2: REAL SHORT INTAKE & MULTIMODAL ANALYSIS PASSED")
    print(f"[*] Reference Video:        {scout_result.video_path}")
    print(f"[*] Visual Contact Sheet:   {contact_sheet_path}")
    print(f"[*] Speech Analysis JSON:   {ref_analysis_path}")
    print(f"[*] Production Plan JSON:   {config.OUTPUT_DIR / 'production_plan.json'}\n")
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
