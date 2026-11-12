"""
Central Configuration for Shorts Cloner Agent.
Handles environment variables, paths, model settings, and hardware detection.
"""

import os
import shutil
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv(override=True)

# -----------------------------------------------------------------------------
# Base Directories
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR / "workspace"
OUTPUT_DIR = BASE_DIR / "output"
SAVED_CLIPS_DIR = OUTPUT_DIR / "saved_clips"
ASSETS_DIR = BASE_DIR / "assets"
SFX_DIR = ASSETS_DIR / "sfx"
BGM_DIR = ASSETS_DIR / "bgm"
TESTS_DIR = BASE_DIR / "tests"

# Ensure all critical working directories exist
for directory in [WORKSPACE_DIR, OUTPUT_DIR, SAVED_CLIPS_DIR, ASSETS_DIR, SFX_DIR, BGM_DIR, TESTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# Gemini AI Configuration
# -----------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
raw_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
# Normalize model name aliases
if raw_model == "gemini-3.0-flash":
    MODEL_ID = "gemini-3-flash-preview"
else:
    MODEL_ID = raw_model
FALLBACK_MODEL_ID = "gemini-3-flash-preview"

# -----------------------------------------------------------------------------
# Target Audience & Niche Defaults (US / Tier-1 Kids 3D Animation Market)
# -----------------------------------------------------------------------------
DEFAULT_LANGUAGE = "en"
LANGUAGE_NAME = "English (US)"
LANGUAGE = "English (US)"
DEFAULT_NICHE = "Cute 3D Animated Kids Stories & Funny Cartoon Adventures"

# Benchmark curated search queries for viral 3D animated Shorts
US_TREND_QUERIES = [
    "3d animation short story #shorts",
    "cute 3d cartoon animation #shorts",
    "funny 3d animated shorts #shorts",
    "pixar style 3d animation #shorts",
    "kids 3d animation moral story #shorts",
    "cgi 3d animated short #shorts",
]

# Strict "trending this day / week" thresholds for auto-scouted reference Shorts.
MIN_REFERENCE_VIEWS = int(os.getenv("MIN_REFERENCE_VIEWS", "1000000"))
ABSOLUTE_MIN_REFERENCE_VIEWS = int(os.getenv("ABSOLUTE_MIN_REFERENCE_VIEWS", "50000"))
MAX_REFERENCE_AGE_DAYS = int(os.getenv("MAX_REFERENCE_AGE_DAYS", "7"))
REFERENCES_DIR = OUTPUT_DIR / "references"
REFERENCE_MIN_DURATION = 15
REFERENCE_MAX_DURATION = 60

# Keywords identifying 3D animation / cartoon / kids storytelling Shorts
NICHE_RELEVANCE_KEYWORDS = [
    "3d", "animation", "animated", "cartoon", "pixar", "disney", "cgi", "blender",
    "cute", "kids", "little", "tiny", "baby", "friend", "friends", "rescue", "save",
    "pool", "challenge", "funny", "magic", "monster", "angel", "hero", "adventure",
    "puppy", "kitten", "cat", "dog", "bear", "bunny", "finger", "pencil", "toy",
    "robot", "story", "short", "shorts", "normal", "mocked", "rejected", "rumi",
]

US_SHORTS_HASHTAGS = [
    "3danimation",
    "3dcartoon",
    "kidsanimation",
    "cuteanimation",
    "animatedshorts",
    "cgianimation",
    "funnyanimation",
]

# -----------------------------------------------------------------------------
# Voice & Audio Settings
# -----------------------------------------------------------------------------
# Default: en-US-AnaNeural (cheerful, expressive American kids storyteller)
VOICE = os.getenv("DEFAULT_VOICE", "en-US-AnaNeural")
DEFAULT_VOICE = VOICE
VOICE_RATE = os.getenv("DEFAULT_VOICE_RATE", "+18%")
DEFAULT_VOICE_RATE = VOICE_RATE


# -----------------------------------------------------------------------------
# Subtitles & Whisper Settings
# -----------------------------------------------------------------------------
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "small")
DEVICE = os.getenv("DEVICE", "cuda")
COMPUTE_TYPE = os.getenv("COMPUTE_TYPE", "int8")


# -----------------------------------------------------------------------------
# Video & Rendering Settings
# -----------------------------------------------------------------------------
VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1080"))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1920"))
VIDEO_FPS = int(os.getenv("VIDEO_FPS", "30"))
RENDER_WORKERS = int(os.getenv("RENDER_WORKERS", "5"))
FFMPEG_CODEC = os.getenv("FFMPEG_CODEC", "h264_nvenc")
FALLBACK_FFMPEG_CODEC = "libx264"

HISTORY_LOG_FILE = WORKSPACE_DIR / "history_log.json"
OUTPUT_HISTORY_LOG_FILE = OUTPUT_DIR / "history_log.json"

# -----------------------------------------------------------------------------
# YouTube Data API v3 Auto-Upload & High-RPM US Prime Time Scheduling
# -----------------------------------------------------------------------------
CREDENTIALS_DIR = BASE_DIR / "credentials"
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
_raw_client_secrets = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "credentials/client_secrets.json")
_raw_token_file = os.getenv("YOUTUBE_TOKEN_FILE", "credentials/youtube_token.json")
YOUTUBE_CLIENT_SECRETS_FILE = (
    Path(_raw_client_secrets) if Path(_raw_client_secrets).is_absolute() else (BASE_DIR / _raw_client_secrets)
)
YOUTUBE_TOKEN_FILE = (
    Path(_raw_token_file) if Path(_raw_token_file).is_absolute() else (BASE_DIR / _raw_token_file)
)
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]
US_TARGET_TIMEZONE = os.getenv("US_TARGET_TIMEZONE", "America/New_York")
US_PRIME_SLOTS_ET = [
    s.strip()
    for s in os.getenv("US_PRIME_SLOTS_ET", "08:00,12:30,16:30,20:00").split(",")
    if s.strip()
]
YOUTUBE_UPLOAD_PRIVACY = os.getenv("YOUTUBE_UPLOAD_PRIVACY", "scheduled")
YOUTUBE_CATEGORY_ID = os.getenv("YOUTUBE_CATEGORY_ID", "24")
YOUTUBE_DEFAULT_MADE_FOR_KIDS = os.getenv("YOUTUBE_MADE_FOR_KIDS", "false").lower() == "true"

# -----------------------------------------------------------------------------
# Pollinations Flux Visual API
# -----------------------------------------------------------------------------
POLLINATIONS_FLUX_URL_TEMPLATE = (
    "https://image.pollinations.ai/prompt/{prompt}?width={width}&height={height}&seed={seed}&model=flux&nologo=true"
)
# Minimum seconds between Pollinations requests (free tier is rate limited per IP)
POLLINATIONS_MIN_INTERVAL = float(os.getenv("POLLINATIONS_MIN_INTERVAL", "8"))
# Max visual cuts per scene (mirrors the reference cut frequency)
MAX_SHOTS_PER_SCENE = 3




# -----------------------------------------------------------------------------
# Binary Resolution Helpers (FFmpeg / FFprobe)
# -----------------------------------------------------------------------------
def _find_binary(name: str) -> str:
    """Resolve binary location from PATH or common Windows installation paths."""
    # 1. Standard which
    resolved = shutil.which(name)
    if resolved:
        return resolved

    # 2. Check current machine & user PATH from registry if PATH changed during session
    machine_path = os.environ.get("Path", "")
    for part in machine_path.split(";"):
        candidate = Path(part.strip()) / f"{name}.exe"
        if candidate.is_file():
            return str(candidate)

    # 3. Check Local AppData WinGet package folders
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        winget_dir = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
        if winget_dir.exists():
            for exe in winget_dir.rglob(f"{name}.exe"):
                if exe.is_file():
                    return str(exe)

    # Fallback to plain binary name
    return name


FFMPEG_BIN = _find_binary("ffmpeg")
FFPROBE_BIN = _find_binary("ffprobe")


def check_nvenc_support() -> bool:
    """Check if FFmpeg has h264_nvenc encoder that works with the current NVIDIA driver."""
    try:
        proc = subprocess.run(
            [
                FFMPEG_BIN,
                "-y",
                "-f", "lavfi",
                "-i", "color=c=black:s=1080x1920:d=0.2",
                "-pix_fmt", "yuv420p",
                "-c:v", "h264_nvenc",
                "-f", "null",
                "-",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=8,
        )
        return proc.returncode == 0
    except Exception:
        return False



def get_active_encoder() -> str:
    """Return h264_nvenc if supported by GPU/ffmpeg, otherwise fallback to libx264."""
    if check_nvenc_support():
        return FFMPEG_CODEC
    return FALLBACK_FFMPEG_CODEC


def check_cuda_support() -> dict:
    """Inspect GPU, ctranslate2 (faster-whisper CUDA engine), PyTorch, and nvidia-smi status."""
    status = {
        "cuda_available": False,
        "device_count": 0,
        "device_name": None,
        "ctranslate2_cuda": False,
        "supported_compute_types": [],
    }

    # 1. Check ctranslate2 (primary engine for faster-whisper)
    try:
        import ctranslate2

        c2_count = ctranslate2.get_cuda_device_count()
        if c2_count > 0:
            status["cuda_available"] = True
            status["device_count"] = c2_count
            status["ctranslate2_cuda"] = True
            status["supported_compute_types"] = list(
                ctranslate2.get_supported_compute_types("cuda")
            )
    except Exception:
        pass

    # 2. Check PyTorch CUDA if available
    try:
        import torch

        if torch.cuda.is_available():
            status["cuda_available"] = True
            status["torch_cuda"] = True
            status["device_name"] = torch.cuda.get_device_name(0)
    except Exception:
        pass

    # 3. Query nvidia-smi for precise hardware specs
    if not status.get("device_name"):
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                text=True,
                timeout=5,
            ).strip()
            if out:
                status["device_name"] = out
                status["cuda_available"] = True
        except Exception:
            pass

    return status

