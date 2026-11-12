"""
Real visual sourcing for scenes (replaces the text-on-gradient cards).

Sources (all free, no API key):
  1. Pollinations Flux      -> cinematic AI image generated from the scene's image_prompt
  2. Wikimedia Commons      -> REAL archival photographs of the documented subject
Every image is validated (must contain real detail, not a blank / blob placeholder),
composed into a 720x1280 vertical frame and given a consistent cinematic grade.
"""

import io
import random
import time
import urllib.parse
from pathlib import Path
from typing import List, Optional

import numpy as np
import requests
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageStat

import config
from utils.logger import log_info, log_warning

USER_AGENT = "anyvidsz-shorts-factory/1.0 (YouTube channel anyvidsz; local research tool)"
WIKI_API = "https://commons.wikimedia.org/w/api.php"
WIKI_BAD_TITLE_WORDS = (
    "logo", "icon", "flag", "coat of arms", "signature", "seal of", "emblem", "diagram",
    "chart", "graph", "svg", "stamp", "map of", "map ", "locator", "insignia", "pdf", "page ",
    "3d model", "render", "drawing", "sketch", "cartoon", "badge", "patch", "ribbon", "medal",
)

_last_pollinations_call = 0.0
_pollinations_cooldown_until = 0.0


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def has_real_detail(img: Image.Image) -> bool:
    """Reject blank canvases, flat gradients and simple blob/circle placeholders."""
    gray = img.convert("L").resize((256, 456))
    std = ImageStat.Stat(gray).stddev[0]
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edge_mean = ImageStat.Stat(edges).mean[0]
    colors = len(np.unique(np.asarray(img.convert("RGB").resize((64, 64))).reshape(-1, 3), axis=0))
    # Calibrated: real AI/archival photos -> std 24-77, edges 5.3-24.6; old red text card -> 16.1 / 4.28;
    # blurred blob placeholder -> 6.2 / 0.77. Colour floor is low so black & white archival photos still pass.
    return std >= 18.0 and edge_mean >= 4.6 and colors >= 120


# ---------------------------------------------------------------------------
# Composition & grading
# ---------------------------------------------------------------------------
def compose_vertical(img: Image.Image, width: int = config.VIDEO_WIDTH, height: int = config.VIDEO_HEIGHT) -> Image.Image:
    """
    Turn any photo into a full 9:16 frame.
    - Portrait-ish images are cover-cropped edge to edge.
    - Landscape archival photos get the classic viral-Shorts treatment: blurred, darkened full-bleed
      copy as background + the sharp photo large in the centre.
    """
    img = ImageOps.exif_transpose(img).convert("RGB")
    target_ratio = width / height
    ratio = img.width / img.height

    if ratio <= target_ratio * 1.25:
        return ImageOps.fit(img, (width, height), Image.Resampling.LANCZOS)

    bg = ImageOps.fit(img, (width, height), Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(28))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)

    # Foreground: fill ~58% of the height, crop the sides if wider than the frame
    fg_h = int(height * 0.58)
    fg_w = int(fg_h * ratio)
    fg = img.resize((fg_w, fg_h), Image.Resampling.LANCZOS)
    if fg_w > width:
        left = (fg_w - width) // 2
        fg = fg.crop((left, 0, left + width, fg_h))
    x = (width - fg.width) // 2
    y = (height - fg.height) // 2
    bg.paste(fg, (x, y))
    return bg


def cinematic_grade(img: Image.Image, seed: int = 0) -> Image.Image:
    """Consistent documentary grade: contrast, slightly muted colour, vignette, fine film grain."""
    img = ImageEnhance.Contrast(img).enhance(1.12)
    img = ImageEnhance.Color(img).enhance(0.88)

    arr = np.asarray(img).astype(np.float32)
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    vignette = np.clip(1.0 - 0.35 * np.clip(dist - 0.55, 0, None) ** 1.4, 0.55, 1.0)
    arr *= vignette[..., None]

    rng = np.random.default_rng(seed)
    arr += rng.normal(0, 3.0, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def punch_in_variant(img: Image.Image, zoom: float = 1.45, focus: str = "center") -> Image.Image:
    """Tighter crop of an existing frame (used as an extra 'cut' when no other source is available)."""
    w, h = img.size
    cw, ch = int(w / zoom), int(h / zoom)
    offsets = {"center": (0.5, 0.45), "top": (0.5, 0.3), "bottom": (0.5, 0.65), "left": (0.35, 0.5), "right": (0.65, 0.5)}
    fx, fy = offsets.get(focus, (0.5, 0.5))
    left = int(max(0, min(w - cw, fx * w - cw / 2)))
    top = int(max(0, min(h - ch, fy * h - ch / 2)))
    return img.crop((left, top, left + cw, top + ch)).resize((w, h), Image.Resampling.LANCZOS)


def save_frame(img: Image.Image, path: Path, seed: int = 0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    cinematic_grade(img, seed).save(str(path), "JPEG", quality=93)
    return path


# ---------------------------------------------------------------------------
# Pollinations (AI)
# ---------------------------------------------------------------------------
def fetch_pollinations(prompt: str, seed: int, style_hint: str = "", max_attempts: int = 2, allow_wait_on_429: bool = False) -> Optional[Image.Image]:
    """Generate a cinematic image. Respects the free-tier rate limit and validates the result."""
    global _last_pollinations_call, _pollinations_cooldown_until

    now = time.time()
    if now < _pollinations_cooldown_until and not allow_wait_on_429:
        return None

    full_prompt = (
        "Cinematic documentary film still, ultra-realistic, photorealistic, dramatic lighting, "
        f"{prompt}. {style_hint}".strip()
    )[:900]
    url = config.POLLINATIONS_FLUX_URL_TEMPLATE.format(
        prompt=urllib.parse.quote(full_prompt),
        width=config.VIDEO_WIDTH,
        height=config.VIDEO_HEIGHT,
        seed=seed,
    )

    for attempt in range(1, max_attempts + 1):
        wait = max(
            config.POLLINATIONS_MIN_INTERVAL - (time.time() - _last_pollinations_call),
            _pollinations_cooldown_until - time.time() if allow_wait_on_429 else 0.0,
        )
        if wait > 0:
            time.sleep(min(wait, 46.0))
        _last_pollinations_call = time.time()
        try:
            r = requests.get(url, timeout=45, headers={"User-Agent": USER_AGENT})
        except Exception as e:
            log_warning(f"Pollinations attempt {attempt} error: {e}")
            continue

        if r.status_code in (402, 429, 503, 502, 500):
            _pollinations_cooldown_until = time.time() + 46.0
            if not allow_wait_on_429 or attempt == max_attempts:
                log_info(f"Pollinations rate-limited (HTTP {r.status_code}); using archival photography for this cut.")
                return None
            log_warning(f"Pollinations rate-limited (HTTP {r.status_code}), waiting 45s...")
            continue
        if not r.ok or not r.headers.get("content-type", "").startswith("image"):
            log_warning(f"Pollinations returned HTTP {r.status_code} ({r.headers.get('content-type')})")
            continue

        try:
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
        except Exception:
            continue
        # Remove the small "pollinations.ai" watermark at the bottom-right corner
        img = img.crop((0, 0, img.width, int(img.height * 0.94)))
        if not has_real_detail(img):
            log_warning("Pollinations image rejected (blank / placeholder). Retrying with new seed...")
            url = url.replace(f"seed={seed}", f"seed={seed + 1000 * attempt}")
            continue
        return img
    return None


# ---------------------------------------------------------------------------
# Wikimedia Commons (real archival photos)
# ---------------------------------------------------------------------------
def search_wikimedia(query: str, limit: int = 6) -> List[dict]:
    if not query or not query.strip():
        return []
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"{query} filetype:bitmap",
        "gsrnamespace": 6,
        "gsrlimit": 15,
        "prop": "imageinfo",
        "iiprop": "url|size|mime",
        "iiurlwidth": 1280,
    }
    try:
        r = requests.get(WIKI_API, params=params, headers={"User-Agent": USER_AGENT}, timeout=30)
        pages = (r.json().get("query") or {}).get("pages", {})
    except Exception as e:
        log_warning(f"Wikimedia search failed for '{query}': {e}")
        return []

    results = []
    for p in sorted(pages.values(), key=lambda x: x.get("index", 0)):
        info = (p.get("imageinfo") or [{}])[0]
        title = p.get("title", "")
        t_low = title.lower()
        if info.get("mime") not in ("image/jpeg", "image/png"):
            continue
        if (info.get("width") or 0) < 500 or (info.get("height") or 0) < 350:
            continue
        if any(bad in t_low for bad in WIKI_BAD_TITLE_WORDS):
            continue
        results.append({"title": title, "url": info.get("thumburl") or info.get("url")})
        if len(results) >= limit:
            break
    return results


def fetch_image_url(url: str) -> Optional[Image.Image]:
    try:
        r = requests.get(url, timeout=45, headers={"User-Agent": USER_AGENT})
        if not r.ok:
            return None
        img = Image.open(io.BytesIO(r.content)).convert("RGB")
        return img if has_real_detail(img) else None
    except Exception:
        return None
