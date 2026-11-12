"""
CUDA Word-Level Subtitle Agent (Agent 5).
Handles:
1. Concatenating scene audio tracks into master audio
2. Transcribing audio using faster-whisper with word-level timestamps on CUDA (int8)
3. Generating modern Shorts-styled .ass subtitle file with word-by-word active pop-up highlights
4. Strict VRAM cleanup protocol immediately after transcription
5. Windows-safe path escaping helper for FFmpeg ass filter
"""

import gc
import os
import re
import site
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# -----------------------------------------------------------------------------
# Windows CUDA & PyAV Compatibility Hooks
# -----------------------------------------------------------------------------
def _configure_windows_cuda_dlls():
    """Ensure Windows can locate nvidia-cublas and nvidia-cudnn DLLs."""
    try:
        search_dirs = []
        for sp in site.getsitepackages():
            nvidia_root = Path(sp) / "nvidia"
            if nvidia_root.is_dir():
                for sub in ["cublas", "cudnn", "cuda_nvrtc", "cuda_runtime"]:
                    bin_dir = nvidia_root / sub / "bin"
                    if bin_dir.is_dir():
                        search_dirs.append(str(bin_dir))

        for d in search_dirs:
            try:
                os.add_dll_directory(d)
            except Exception:
                pass
            os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass


def _patch_pyav_compatibility():
    """Patch PyAV open() for compatibility with faster-whisper on PyAV 19+."""
    try:
        import av
        if not hasattr(av, "_patched_for_whisper"):
            _orig_open = av.open

            def _safe_open(*args, **kwargs):
                kwargs.pop("metadata_errors", None)
                return _orig_open(*args, **kwargs)

            av.open = _safe_open
            av._patched_for_whisper = True
    except Exception:
        pass


_configure_windows_cuda_dlls()
_patch_pyav_compatibility()

import config
from utils.logger import (
    log_info,
    log_success,
    log_warning,
    log_error,
)


@dataclass
class WordTiming:
    word: str
    start: float
    end: float


def escape_ass_path_for_ffmpeg(ass_path: Path) -> str:
    """
    Format Windows file path for FFmpeg filtergraph:
    Replaces backslashes with forward slashes and escapes drive letter colons.
    e.g., 'D:\\workspace\\subtitles.ass' -> 'D\\:/workspace/subtitles.ass'
    """
    clean_path = str(ass_path.resolve()).replace("\\", "/")
    # Escape colon after drive letter (e.g. C: -> C\:)
    if len(clean_path) >= 2 and clean_path[1] == ":":
        clean_path = clean_path[0] + "\\:" + clean_path[2:]
    return clean_path


def format_ass_timestamp(seconds: float) -> str:
    """Convert float seconds to ASS format: H:MM:SS.cc (centiseconds)."""
    if seconds < 0:
        seconds = 0.0
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis == 100:
        secs += 1
        centis = 0
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"


class SubtitleAgent:
    """Agent responsible for word-level transcription and ASS subtitle styling."""

    def __init__(
        self,
        model_size: str = config.WHISPER_MODEL_SIZE,
        device: str = config.DEVICE,
        compute_type: str = config.COMPUTE_TYPE,
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type

    def concatenate_scene_audios(self, audio_files: List[Path], output_path: Path) -> Path:
        """
        Concatenate individual scene audio files into a single master audio track using FFmpeg.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not audio_files:
            raise ValueError("No audio files provided for concatenation.")

        concat_list_file = output_path.parent / "concat_audio_list.txt"
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for audio in audio_files:
                resolved = str(audio.resolve()).replace("\\", "/")
                f.write(f"file '{resolved}'\n")

        cmd = [
            config.FFMPEG_BIN,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file),
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            str(output_path),
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=30)
            concat_list_file.unlink(missing_ok=True)
            log_success(f"Concatenated {len(audio_files)} scene audios -> {output_path.name}")
            return output_path
        except subprocess.CalledProcessError as e:
            log_error(f"FFmpeg audio concatenation failed: {e.stderr.decode('utf-8', errors='ignore')}")
            raise

    def transcribe_with_word_timestamps(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        initial_prompt: Optional[str] = None,
    ) -> List[WordTiming]:
        """
        Run faster-whisper on CUDA (int8) with word_timestamps=True.
        Immediately frees CUDA VRAM after completion.
        """
        _configure_windows_cuda_dlls()
        _patch_pyav_compatibility()

        from faster_whisper import WhisperModel

        log_info(
            f"Loading Whisper '{self.model_size}' on {self.device} ({self.compute_type}) for word-level sync..."
        )

        model = None
        words: List[WordTiming] = []

        try:
            try:
                model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                )
            except Exception as e:
                log_warning(f"CUDA faster-whisper load failed ({e}). Falling back to CPU.")
                model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8",
                )

            log_info(f"Transcribing audio with word timestamps: {audio_path.name}")
            try:
                segments, info = model.transcribe(
                    str(audio_path),
                    word_timestamps=True,
                    language=language if language and language != "auto" else None,
                    initial_prompt=initial_prompt or None,
                )
                for segment in segments:
                    if not segment.words:
                        continue
                    for w in segment.words:
                        clean_word = w.word.strip()
                        if clean_word:
                            words.append(WordTiming(word=clean_word, start=w.start, end=w.end))
            except Exception as e:
                log_warning(f"CUDA transcription encountered error: {e}. Retrying on CPU fallback...")
                del model
                gc.collect()
                model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
                segments, info = model.transcribe(
                    str(audio_path),
                    word_timestamps=True,
                    language=language if language and language != "auto" else None,
                    initial_prompt=initial_prompt or None,
                )
                for segment in segments:
                    if not segment.words:
                        continue
                    for w in segment.words:
                        clean_word = w.word.strip()
                        if clean_word:
                            words.append(WordTiming(word=clean_word, start=w.start, end=w.end))

            log_success(
                f"Transcribed {len(words)} words ({getattr(info, 'language', 'en')})"
            )
            return words

        finally:
            # STRICT VRAM CLEANUP PROTOCOL
            if model is not None:
                del model
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass
            log_info("Whisper model unloaded and CUDA VRAM freed.")

    def generate_ass_subtitles(
        self,
        words: List[WordTiming],
        output_ass_path: Path,
        words_per_chunk: int = 2,
        emphasis_keywords: Optional[List[str]] = None,
        hook_headline: Optional[str] = None,
    ) -> Path:
        """
        Generate Advanced SubStation Alpha (.ass) subtitle file styled for modern vertical shorts:
        - Instant 0.0-2.4s upper hook banner (`Style: HookBanner`) stopping the thumb-scroll
        - Snappy 2-word lower-third captions safely above Shorts UI & below character faces
        - Word-by-word active pop-up highlights synchronized to exact timestamps
        """
        output_ass_path.parent.mkdir(parents=True, exist_ok=True)
        emphasis_set = set(k.lower().strip() for k in (emphasis_keywords or []))

        s_fac = config.VIDEO_HEIGHT / 1280.0
        f_sz = int(round(50 * s_fac))
        hook_sz = int(round(54 * s_fac))
        out_px = round(5.0 * s_fac, 1)
        shd_px = round(2.5 * s_fac, 1)
        m_lr = int(round(40 * s_fac))
        m_v = int(round(285 * s_fac))
        hook_mv = int(round(145 * s_fac))

        # Modern Shorts ASS Header (Resolution-scaled cleanly to 1080x1920 Full HD or 720x1280)
        ass_header = f"""[Script Info]
Title: Viral Shorts High Retention Subtitles
ScriptType: v4.00+
WrapStyle: 2
PlayResX: {config.VIDEO_WIDTH}
PlayResY: {config.VIDEO_HEIGHT}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Impact,{f_sz},&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,{round(1.5 * s_fac, 1)},0,1,{out_px},{shd_px},2,{m_lr},{m_lr},{m_v},1
Style: HookBanner,Impact,{hook_sz},&H0000FFFF,&H00FFFFFF,&H00000000,&HC0000000,-1,0,0,0,100,100,{round(2.0 * s_fac, 1)},0,1,{round(6.0 * s_fac, 1)},{shd_px},8,{m_lr},{m_lr},{hook_mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []

        # Frame-0 visual curiosity hook overlay (first 2.35s catches scroll-past viewers)
        clean_hook = re.sub(r"[\r\n{}]+", " ", (hook_headline or "").strip())
        if clean_hook:
            hook_upper = clean_hook.upper()[:42]
            events.append(
                f"Dialogue: 1,0:00:00.00,0:00:02.35,HookBanner,,0,0,0,,{{\\fad(80,180)}}{hook_upper}"
            )

        # Group words into small punchy chunks (2-4 words per line)
        for chunk_start in range(0, len(words), words_per_chunk):
            chunk = words[chunk_start : chunk_start + words_per_chunk]
            if not chunk:
                continue

            for active_idx, active_word in enumerate(chunk):
                start_str = format_ass_timestamp(active_word.start)
                end_str = format_ass_timestamp(active_word.end)

                formatted_words = []
                for i, w in enumerate(chunk):
                    raw_text = w.word.upper()
                    clean_lookup = re.sub(r"[^\w]", "", w.word).lower()

                    if i == active_idx:
                        # Highlight active word in Yellow (&H0000FFFF) with slight pop scale
                        if clean_lookup in emphasis_set:
                            # Super emphasis: Neon Green (&H0000FF00)
                            color_tag = "{\\c&H0000FF00&\\fscx112\\fscy112}"
                        else:
                            # Standard active pop: Bright Yellow (&H0000FFFF)
                            color_tag = "{\\c&H0000FFFF&\\fscx108\\fscy108}"
                        formatted_words.append(f"{color_tag}{raw_text}{{\\rDefault}}")
                    else:
                        # Inactive words in White (&H00FFFFFF)
                        formatted_words.append(f"{{\\c&H00FFFFFF&}}{raw_text}")

                dialogue_line = " ".join(formatted_words)
                event_line = (
                    f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{dialogue_line}"
                )
                events.append(event_line)

        full_content = ass_header + "\n".join(events) + "\n"
        output_ass_path.write_text(full_content, encoding="utf-8")
        log_success(f"Generated dynamic .ass subtitle file ({len(events)} events) -> {output_ass_path.name}")
        return output_ass_path

    def process_clip_subtitles(
        self,
        scene_audio_files: List[Path],
        output_dir: Path,
        clip_index: int,
        language: str = "en",
        emphasis_keywords: Optional[List[str]] = None,
        initial_prompt: Optional[str] = None,
        hook_headline: Optional[str] = None,
    ) -> Path:
        """Complete subtitle workflow: concatenate scene audios, transcribe words, and generate ASS subtitles."""
        output_dir.mkdir(parents=True, exist_ok=True)
        master_audio = output_dir / f"master_audio_clip_{clip_index:02d}.mp3"
        ass_output = output_dir / f"subtitles_clip_{clip_index:02d}.ass"

        # 1. Concatenate scene audios
        self.concatenate_scene_audios(scene_audio_files, master_audio)

        # 2. Transcribe with word timestamps
        words = self.transcribe_with_word_timestamps(
            master_audio,
            language=language,
            initial_prompt=initial_prompt,
        )

        # 3. Generate ASS file
        self.generate_ass_subtitles(
            words=words,
            output_ass_path=ass_output,
            words_per_chunk=2,
            emphasis_keywords=emphasis_keywords,
            hook_headline=hook_headline,
        )

        return ass_output
