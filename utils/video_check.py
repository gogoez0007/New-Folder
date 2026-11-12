"""
Video integrity verification helpers.

Used by the Scout (reference download) and the Editor (final render) so that
the pipeline FAILS LOUDLY instead of reporting success on a file that:
  - has no video stream (audio-only),
  - uses a codec most players cannot show (e.g. AV1 / VP9 inside .mp4),
  - uses a non-standard pixel format (yuv444p / yuvj420p),
  - or decodes to black / near-black frames.
"""

import io
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageStat

import config


def probe_media(path: Path) -> Dict[str, Any]:
    """Return ffprobe JSON (format + streams) for a media file."""
    cmd = [
        config.FFPROBE_BIN, "-v", "error",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {Path(path).name}: {result.stderr.strip()[:300]}")
    return json.loads(result.stdout or "{}")


def get_video_stream(probe: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for s in probe.get("streams", []):
        # Skip embedded cover-art pictures, which are reported as video streams
        if s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic"):
            return s
    return None


def get_audio_stream(probe: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for s in probe.get("streams", []):
        if s.get("codec_type") == "audio":
            return s
    return None


def is_universally_playable(vstream: Optional[Dict[str, Any]]) -> bool:
    """H.264 + yuv420p is the only combo every player (Windows, phones, browsers, YouTube) handles."""
    return bool(vstream) and vstream.get("codec_name") == "h264" and vstream.get("pix_fmt") == "yuv420p"


def sample_frame_brightness(path: Path, duration: float, samples: int = 3) -> List[float]:
    """Decode a few frames and return their mean luma (0..255)."""
    values: List[float] = []
    duration = max(duration, 0.5)
    for i in range(1, samples + 1):
        ts = duration * i / (samples + 1)
        cmd = [
            config.FFMPEG_BIN, "-v", "error",
            "-ss", f"{ts:.3f}", "-i", str(path),
            "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-",
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        if result.returncode != 0 or not result.stdout:
            continue
        with Image.open(io.BytesIO(result.stdout)) as frame:
            values.append(float(ImageStat.Stat(frame.convert("L")).mean[0]))
    return values


def verify_video_file(
    path: Path,
    require_audio: bool = True,
    min_brightness: float = 12.0,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Full integrity check. Returns (ok, human_readable_report, details).
    """
    path = Path(path)
    if not path.exists() or path.stat().st_size < 10_000:
        return False, f"{path.name}: file missing or too small", {}

    probe = probe_media(path)
    vstream = get_video_stream(probe)
    astream = get_audio_stream(probe)
    duration = float(probe.get("format", {}).get("duration") or 0.0)

    details = {
        "video_codec": vstream.get("codec_name") if vstream else None,
        "pix_fmt": vstream.get("pix_fmt") if vstream else None,
        "width": vstream.get("width") if vstream else None,
        "height": vstream.get("height") if vstream else None,
        "audio_codec": astream.get("codec_name") if astream else None,
        "duration": duration,
    }

    if vstream is None:
        return False, f"{path.name}: NO VIDEO STREAM (audio only)", details
    if not is_universally_playable(vstream):
        return False, (
            f"{path.name}: video is {details['video_codec']}/{details['pix_fmt']} "
            f"(not H.264/yuv420p, many players show no picture)"
        ), details
    if require_audio and astream is None:
        return False, f"{path.name}: NO AUDIO STREAM", details

    brightness = sample_frame_brightness(path, duration)
    details["frame_brightness"] = [round(b, 1) for b in brightness]
    if not brightness:
        return False, f"{path.name}: frames could not be decoded", details
    if max(brightness) < min_brightness:
        return False, (
            f"{path.name}: frames are black/near-black (mean luma {details['frame_brightness']})"
        ), details

    return True, (
        f"{path.name}: OK {details['width']}x{details['height']} "
        f"{details['video_codec']}/{details['pix_fmt']} + {details['audio_codec']}, "
        f"{duration:.1f}s, luma {details['frame_brightness']}"
    ), details

