"""
Trend Scout Agent (Agent 1) - US Tier-1 High-Retention Viral Scouter.
Downloads reference YouTube Shorts using yt-dlp with strict US filtering:
- Searches top-performing US viral storytelling Shorts
- Filters for 18–58s duration and strictly English ASCII titles
- Prioritizes high view-count viral benchmarks (>= 100K+ views)
- Supports direct YouTube Shorts URLs for manual reference ingestion
"""

import json
import os
import re
import shutil
import subprocess
import unicodedata
import urllib.parse
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List

import yt_dlp

import config
from utils.logger import log_info, log_success, log_warning, log_error
from utils.history import (
    is_video_processed,
    is_video_title_processed,
    normalize_video_title,
    record_processed_video,
    get_processed_video_ids,
)
from utils.video_check import (
    probe_media,
    get_video_stream,
    is_universally_playable,
    verify_video_file,
)


# Non-English / Indonesian stopword blocklist to prevent foreign spam
NON_ENGLISH_BLOCKLIST = {
    "tahukah", "kamu", "fakta", "menarik", "kucing", "anjing", "bisa", "adalah", "yang",
    "dan", "di", "dari", "ini", "itu", "untuk", "dengan", "saya", "kita", "mereka",
    "banget", "viral", "lucu", "ngakak", "bocah", "tidur", "semu", "kambing", "kota",
    "bukan", "hanya", "sudah", "akan", "lagi", "jadi", "lebih", "dunia", "rahasia",
    "terbaru", "misteri", "hewan", "pengetahuan", "ilmiah", "alam",
    "meri", "mujhe", "bhalu", "aur", "hain", "rakshabandhan", "cmfacts", "bhoot",
    "chintu", "chinki", "patang", "raaz", "duniya", "khatam", "kar", "raha", "hai",
    "malam", "siang", "pani", "puri", "madhu", "zoya", "badal",
}

# Off-format blocklist split cleanly:
# - HARD_NON_KIDS_BLOCKLIST checked against full corpus (title + description + tags)
# - OFF_FORMAT_BLOCKLIST checked strictly against title (so harmless YouTube tags like 'gameplay' or 'surprise' don't drop clean 3D stories)
OFF_FORMAT_BLOCKLIST = (
    "reunion", "homecoming", "wedding", "proposal", "ceremony",
    "gamers", "gameplay", "fortnite", "minecraft", "roblox", "workout", "gym", "phonk",
    "gta", "spiderman", "spider-man", "horror", "demon", "zombie", "zombies", "reaper",
    "creative photography", "electric outlet", "electrical outlet", "guessthesong",
    "vijaythalapathy", "slideshow", "tutorial", "blender course", "how to make",
    "voice actor", "behind the scenes", "movie detail", "italian version", "facts",
    "2d animation", "2d cartoon", "flipaclip", "stickman", "gacha",
    "titanic", "axolotl", "platypus", "turkey", "baby chicks", "mother's love",
    "compilation", "try not to",
)
HARD_NON_KIDS_BLOCKLIST = (
    "reunion", "homecoming", "wedding", "proposal", "fortnite", "minecraft", "roblox",
    "gta", "nextbots", "skibidi", "horror", "demon", "zombie", "zombies", "reaper",
    "spiderman", "spider-man", "guessthesong", "vijaythalapathy", "creative photography",
    "blender course", "how to make", "voice actor", "behind the scenes", "italian version",
)


def sanitize_title_filename(title: str, max_len: int = 80) -> str:
    """Convert a YouTube Short title into a clean Windows-safe filename matching the title."""
    norm = unicodedata.normalize("NFKD", title or "").encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"#\S+", "", norm).strip()
    cleaned = re.sub(r"[^a-zA-Z0-9 _\-]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ._-")
    if len(cleaned) < 4:
        cleaned = re.sub(r"[^a-zA-Z0-9 _\-]+", " ", norm or "Trending_Short")
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ._-") or "Trending_Short"
    return cleaned[:max_len].strip(" ._-")


def is_clean_english_title(title: str) -> bool:
    """Validate that title is predominantly Latin/English, free of non-English stopwords, and not just hashtags."""
    if not title or len(title.strip()) < 5:
        return False

    # Reject titles that are ONLY hashtags (e.g. '#rakshabandhan', '#cmfacts_999')
    non_tag = re.sub(r"#\S+", "", title)
    non_tag_words = re.findall(r"[a-zA-Z]{2,}", non_tag)
    if len(non_tag_words) < 2:
        return False

    # Check against non-English / Indonesian / Hinglish stopwords
    words = re.findall(r"[a-zA-Z]+", title.lower())
    if not words:
        return False
    for w in words:
        if w in NON_ENGLISH_BLOCKLIST:
            return False

    # Check for non-Latin characters (Chinese, Cyrillic, Arabic, Devanagari, etc.)
    latin_letters = sum(1 for c in title if 'a' <= c.lower() <= 'z')
    total_letters = sum(1 for c in title if c.isalpha())
    if total_letters > 0 and (latin_letters / total_letters) < 0.90:
        return False

    return True


@dataclass
class ScoutResult:
    video_path: Path
    title: str
    duration: float
    view_count: Optional[int] = None
    uploader: Optional[str] = None
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TrendScoutAgent:
    """Agent responsible for sourcing, auto-searching, downloading, and inspecting reference Shorts."""

    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = Path(workspace_dir or config.WORKSPACE_DIR)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def _probe_local_video(self, video_path: Path) -> Dict[str, Any]:
        """Use ffprobe to extract video duration, dimensions, and stream info."""
        cmd = [
            config.FFPROBE_BIN,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
            data = json.loads(result.stdout)
            format_info = data.get("format", {})
            duration = float(format_info.get("duration", 0.0))
            return {"duration": duration, "format": format_info, "streams": data.get("streams", [])}
        except Exception as e:
            log_warning(f"ffprobe metadata extraction failed: {e}. Defaulting duration to 30.0s.")
            return {"duration": 30.0, "format": {}, "streams": []}

    def _normalize_to_mp4(self, source_path: Path, target_path: Path) -> Path:
        """
        Guarantee a universally playable H.264 (yuv420p) + AAC MP4 that contains a REAL video stream.
        YouTube often serves AV1/VP9 inside .mp4; stream-copying those produced a reference file that
        plays audio but shows NO PICTURE in most Windows players. We now re-encode whenever needed
        and verify the result.
        """
        probe = probe_media(source_path)
        vstream = get_video_stream(probe)
        if vstream is None:
            raise RuntimeError(f"Downloaded file has NO video stream (audio-only): {source_path.name}")

        if is_universally_playable(vstream):
            v_args = ["-c:v", "copy"]
        else:
            log_info(
                f"Re-encoding reference from {vstream.get('codec_name')}/{vstream.get('pix_fmt')} "
                f"to H.264/yuv420p so it actually shows a picture in every player..."
            )
            v_args = ["-vf", "scale=out_range=tv,format=yuv420p", "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                      "-pix_fmt", "yuv420p", "-color_range", "tv", "-profile:v", "high"]

        tmp_target = target_path.with_name(target_path.stem + "_tmp.mp4")
        cmd = [
            config.FFMPEG_BIN, "-y",
            "-i", str(source_path),
            "-map", "0:v:0", "-map", "0:a:0?",
            *v_args,
            "-c:a", "aac", "-b:a", "160k",
            "-movflags", "+faststart",
            str(tmp_target),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"Reference normalization failed: {result.stderr[-400:]}")
        os.replace(tmp_target, target_path)

        ok, report, _ = verify_video_file(target_path, require_audio=False, min_brightness=5.0)
        if not ok:
            raise RuntimeError(f"Reference video failed verification: {report}")
        log_success(f"Reference verified -> {report}")
        return target_path

    def inspect_local(self, file_path: str, preserve_name: bool = False) -> ScoutResult:
        """Inspect and prepare a local reference video file."""
        src = Path(file_path).resolve()
        if not src.exists():
            raise FileNotFoundError(f"Local reference video does not exist: {file_path}")

        if preserve_name:
            ref_dir = self.workspace_dir / "references"
            ref_dir.mkdir(parents=True, exist_ok=True)
            target_mp4 = ref_dir / src.name
        else:
            target_mp4 = self.workspace_dir / "reference_video.mp4"
        if src.resolve() != target_mp4.resolve():
            shutil.copy2(src, target_mp4)

        probe = self._probe_local_video(target_mp4)
        title = src.stem.replace("_", " ")

        log_success(f"Local reference video loaded: {target_mp4.name} ({probe['duration']:.1f}s)")
        return ScoutResult(
            video_path=target_mp4,
            title=title,
            duration=probe["duration"],
            view_count=100000,
            uploader="Local Reference",
            url=str(src),
            metadata=probe,
        )

    def download_short(self, url: str, target_path: Optional[Path] = None) -> ScoutResult:
        """Download reference YouTube Short using yt-dlp into target_path (defaults to workspace/reference_video.mp4)."""
        log_info(f"Downloading YouTube Short from URL: {url}")
        final_target = Path(target_path) if target_path else (self.workspace_dir / "reference_video.mp4")
        final_target.parent.mkdir(parents=True, exist_ok=True)
        target_template = str(final_target.parent / f"{final_target.stem}_raw.%(ext)s")

        ydl_opts = {
            "ffmpeg_location": config.FFMPEG_BIN,
            # Prefer H.264 (avc1) streams. The old selector `bestvideo[height<=720][ext=mp4]`
            # picked AV1 (av01) streams in an .mp4 container -> "no picture" in most players,
            # and `height<=720` on a VERTICAL Short meant a tiny 404x720 video.
            "format": (
                "bestvideo[vcodec^=avc1][height<=1920]+bestaudio[ext=m4a]/"
                "bestvideo[vcodec^=avc1]+bestaudio/"
                "best[vcodec^=avc1]/"
                "bestvideo+bestaudio/best"
            ),
            "outtmpl": target_template,
            "merge_output_format": "mp4",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "ignoreerrors": False,
            "geo_bypass_country": "US",
            "js_runtimes": {"node": {}},
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info is None:
                    raise RuntimeError(f"yt-dlp could not retrieve information for URL: {url}")

                downloaded_file = Path(ydl.prepare_filename(info))
                if not downloaded_file.exists():
                    mp4_candidate = downloaded_file.with_suffix(".mp4")
                    if mp4_candidate.exists():
                        downloaded_file = mp4_candidate

                self._normalize_to_mp4(downloaded_file, final_target)

                # Remove intermediate download file if different
                if downloaded_file.resolve() != final_target.resolve() and downloaded_file.exists():
                    downloaded_file.unlink(missing_ok=True)

                title = info.get("title", "Reference Short")
                duration = float(info.get("duration", 0.0))
                view_count = info.get("view_count")
                uploader = info.get("uploader", "Unknown")
                vid_id = info.get("id") or url

                if target_path is None:
                    safe_dir = self.workspace_dir / "references"
                    safe_dir.mkdir(parents=True, exist_ok=True)
                    named_file = safe_dir / (sanitize_title_filename(title) + ".mp4")
                    if named_file.resolve() != final_target.resolve():
                        shutil.move(str(final_target), str(named_file))
                        final_target = named_file
                    out_ref_dir = getattr(config, "REFERENCES_DIR", config.OUTPUT_DIR / "references")
                    out_ref_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(final_target, out_ref_dir / final_target.name)

                # Record in persistent history log to prevent duplicate downloads
                record_processed_video(
                    video_id=vid_id,
                    title=title,
                    duration=duration,
                    views=view_count,
                )

                log_success(
                    f"Successfully downloaded Short: '{title}' ({duration:.1f}s, {view_count or 0:,} views)"
                )
                return ScoutResult(
                    video_path=final_target,
                    title=title,
                    duration=duration,
                    view_count=view_count,
                    uploader=uploader,
                    url=url,
                    metadata=info,
                )
        except Exception as e:
            log_error(f"Failed to download reference Short: {e}")
            raise

    # ------------------------------------------------------------------
    # Viral reference discovery
    # ------------------------------------------------------------------
    @staticmethod
    def _relevance_score(title: str) -> int:
        """How many niche keywords appear in the title (0 = off-niche)."""
        t = (title or "").lower()
        return sum(1 for kw in config.NICHE_RELEVANCE_KEYWORDS if kw in t)

    def _collect_search_candidates(self, niche: str, processed_ids: set) -> List[dict]:
        """
        Collect trending viral Short candidates uploaded TODAY or THIS WEEK (`<= 7 days`):
          1. YouTube Search filtered by Short (<4m) + Upload Date = TODAY (`sp=CAMSBAgCGAE%3D`) & THIS WEEK (`sp=CAMSBAgDGAE%3D`) sorted by Views
          2. Upload Date = This Week sorted by Relevance/Trending (`sp=EgIYAQ%3D%3D` / `sp=CAISBAgDGAE%3D`)
          3. Fallback recent niche ytsearch queries
        """
        sources: List[str] = [
            # Upload date: TODAY + Short + Sort by View count (`sp=CAMSBAgCGAE=`) — omit %23shorts so YT doesn't hide Shorts shelf!
            "https://www.youtube.com/results?search_query=3d+animation+funny+challenge&sp=CAMSBAgCGAE%3D",
            "https://www.youtube.com/results?search_query=3d+animation+funny+prank&sp=CAMSBAgCGAE%3D",
            "https://www.youtube.com/results?search_query=funny+3d+cartoon+skit&sp=CAMSBAgCGAE%3D",
            "https://www.youtube.com/results?search_query=funny+3d+animation&sp=CAMSBAgCGAE%3D",
            # Upload date: THIS WEEK + Short + Sort by View count (`sp=CAMSBAgDGAE=`)
            "https://www.youtube.com/results?search_query=3d+animation+funny+challenge&sp=CAMSBAgDGAE%3D",
            "https://www.youtube.com/results?search_query=3d+animation+funny+prank&sp=CAMSBAgDGAE%3D",
            "https://www.youtube.com/results?search_query=funny+3d+animation&sp=CAMSBAgDGAE%3D",
            "https://www.youtube.com/results?search_query=3d+animated+comedy+short&sp=CAMSBAgDGAE%3D",
            "https://www.youtube.com/results?search_query=3d+cartoon+obstacle+challenge&sp=CAMSBAgDGAE%3D",
            "https://www.youtube.com/results?search_query=kids+3d+cartoon&sp=CAMSBAgDGAE%3D",
            "https://www.youtube.com/results?search_query=3d+cartoon+adventure&sp=CAMSBAgDGAE%3D",
        ]

        opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "ignoreerrors": True,
            "geo_bypass_country": "US",
            "playlistend": 40,
            "js_runtimes": {"node": {}},
        }

        candidates: List[dict] = []
        seen: set = set()
        for src in sources:
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    res = ydl.extract_info(src, download=False)
            except Exception as err:
                log_warning(f"Search failed ({src[:90]}): {err}")
                continue

            feed_tier = 0 if "sp=CAMSBAgC" in src else (1 if "sp=CAMSBAgD" in src else 2)
            for e in (res or {}).get("entries") or []:
                if not e:
                    continue
                vid = e.get("id")
                if not vid or vid in seen or vid in processed_ids or is_video_processed(vid):
                    continue
                seen.add(vid)

                title = (e.get("title") or "").strip()
                if title and is_video_title_processed(title):
                    continue
                dur = e.get("duration")
                if dur is not None and not (config.REFERENCE_MIN_DURATION <= dur <= config.REFERENCE_MAX_DURATION):
                    continue
                if title and not is_clean_english_title(title):
                    continue
                e["_feed_tier"] = feed_tier
                candidates.append(e)
        return candidates

    def _verify_candidate(self, vid: str, title: str, min_views: int) -> Optional[dict]:
        """Fetch FULL metadata and confirm the candidate is really viral, recent, vertical, English, on-niche and Short-length."""
        if is_video_processed(vid):
            log_info(f"   Skipped already-used reference video ID: {vid}")
            return None
        if title and is_video_title_processed(title):
            log_info(f"   Skipped already-used reference title: {title[:50]}")
            return None
        url = f"https://www.youtube.com/watch?v={vid}"
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
            "geo_bypass_country": "US",
            "js_runtimes": {"node": {}},
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as err:
            log_warning(f"   Could not verify '{(title or vid)[:50]}': {err}")
            return None
        if not info:
            return None

        real_title = (info.get("title") or title or "").strip()
        if is_video_title_processed(real_title):
            log_info(f"   Rejected '{real_title[:50]}': already processed earlier (duplicate title)")
            return None
        desc = (info.get("description") or "")[:500]
        tags_str = " ".join(info.get("tags") or [])
        corpus = f"{real_title} {desc} {tags_str}"

        views = info.get("view_count") or 0
        dur = info.get("duration") or 0
        w, h = info.get("width"), info.get("height")
        upload_date = info.get("upload_date") or ""

        reasons = []
        if not is_clean_english_title(real_title):
            reasons.append("non-English/invalid title")
        if any(bad in real_title.lower() for bad in OFF_FORMAT_BLOCKLIST) or any(bad in corpus.lower() for bad in HARD_NON_KIDS_BLOCKLIST):
            reasons.append("off-format/non-kids")
        anim_markers = ("3d", "animat", "cartoon", "pixar", "cgi", "blender", "disney")
        if not any(m in corpus.lower() for m in anim_markers):
            reasons.append("not animation/3d")
        if self._relevance_score(real_title) < 1 and self._relevance_score(corpus) < 2:
            reasons.append("off-niche")
        if views < min_views:
            reasons.append(f"only {views:,} views (< {min_views:,})")
        if not (config.REFERENCE_MIN_DURATION <= dur <= config.REFERENCE_MAX_DURATION):
            reasons.append(f"duration {dur}s (need {config.REFERENCE_MIN_DURATION}-{config.REFERENCE_MAX_DURATION}s)")
        if w and h and w >= h:
            reasons.append(f"not vertical ({w}x{h})")

        # Enforce STRICT "di hari/minggu ini" recency window (default <= 7 days!)
        max_age = getattr(config, "MAX_REFERENCE_AGE_DAYS", 7)
        if upload_date and len(upload_date) == 8:
            try:
                up_dt = datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=timezone.utc)
                age_days = max(0, (datetime.now(timezone.utc) - up_dt).days)
                info["_age_days"] = age_days
                if age_days > max_age:
                    reasons.append(f"not today/this week ({age_days}d old > {max_age}d)")
            except Exception:
                pass
        else:
            reasons.append("missing upload_date")

        if reasons:
            log_info(f"   Rejected '{real_title[:50]}': {', '.join(reasons)}")
            return None
        return info

    def scout_animation_pool(
        self,
        source: Optional[str] = None,
        niche: Optional[str] = None,
        count: int = 2,
    ) -> List[ScoutResult]:
        """
        Download `count` distinct trending THIS-DAY / THIS-WEEK (`<= 7d`) 3D animation Shorts,
        saving each file cleanly named after its real trending video title into:
          - `workspace/references/<Video_Title>.mp4`
          - `output/references/<Video_Title>.mp4`
        """
        results: List[ScoutResult] = []
        ws_ref_dir = self.workspace_dir / "references"
        ws_ref_dir.mkdir(parents=True, exist_ok=True)
        out_ref_dir = getattr(config, "REFERENCES_DIR", config.OUTPUT_DIR / "references")
        out_ref_dir.mkdir(parents=True, exist_ok=True)

        if source:
            for item in [s.strip() for s in str(source).split(",") if s.strip()]:
                if item.startswith("http://") or item.startswith("https://"):
                    results.append(self.download_short(item))
                elif os.path.exists(item):
                    results.append(self.inspect_local(item, preserve_name=True))
            if len(results) >= count:
                return results[:count]

        effective_niche = niche or source or config.DEFAULT_NICHE
        log_info(f"Auto-scouting {count} TRENDING THIS WEEK (<= {getattr(config, 'MAX_REFERENCE_AGE_DAYS', 7)}d) 3D Animation Shorts for niche: '{effective_niche}'...")

        processed_ids = set(get_processed_video_ids() or [])
        candidates = self._collect_search_candidates(effective_niche, processed_ids)
        candidates.sort(
            key=lambda c: (
                c.get("_feed_tier", 2),
                -(c.get("view_count") or 0),
                -self._relevance_score(c.get("title", "")),
            )
        )
        log_info(f"Collected {len(candidates)} today/this-week Short candidate(s).")

        thresholds = sorted({config.MIN_REFERENCE_VIEWS, 250_000, config.ABSOLUTE_MIN_REFERENCE_VIEWS, 15_000}, reverse=True)
        tried: set = {r.metadata.get("id") for r in results if r.metadata and r.metadata.get("id")}
        chosen_norm_titles: set = {
            normalize_video_title(r.title) for r in results if r.title
        }

        verified_pool: List[dict] = []
        for min_views in thresholds:
            if len(results) + len(verified_pool) >= count:
                break
            pool = [
                c for c in candidates
                if c["id"] not in tried and (c.get("view_count") is None or c.get("view_count") >= min_views)
            ]
            log_info(f"This-Week Trending Tier >= {min_views:,} views: {len(pool)} candidate(s)")
            for c in pool[:140]:
                if len(results) + len(verified_pool) >= count + 3:
                    break
                tried.add(c["id"])
                info = self._verify_candidate(c["id"], c.get("title", ""), min_views)
                if not info:
                    continue
                n_title = normalize_video_title(info.get("title", ""))
                if n_title and n_title in chosen_norm_titles:
                    continue
                chosen_norm_titles.add(n_title)
                verified_pool.append(info)

        # Rank strictly by freshness bucket (0-2d today/yesterday first, then 3-7d this week) + highest views!
        verified_pool.sort(
            key=lambda i: (
                0 if (i.get("_age_days") or 99) <= 2 else 1,
                -(i.get("view_count") or 0),
                i.get("_age_days") or 99,
            )
        )

        for info in verified_pool:
            if len(results) >= count:
                break
            vid_id = info.get("id")
            real_title = info.get("title") or f"Trending_Short_{vid_id}"
            safe_fname = sanitize_title_filename(real_title) + ".mp4"
            target_file = ws_ref_dir / safe_fname
            if target_file.exists():
                target_file = ws_ref_dir / f"{sanitize_title_filename(real_title)}_{vid_id}.mp4"
            video_url = info.get("webpage_url") or f"https://www.youtube.com/watch?v={vid_id}"
            slot_idx = len(results) + 1
            age_days = info.get("_age_days")
            age_str = f"{age_days}d ago (TODAY)" if age_days == 0 else (f"{age_days}d ago (THIS WEEK)" if age_days is not None else "")
            log_info(
                f"Selected Trending Short #{slot_idx}: '{real_title}' "
                f"({info.get('view_count', 0):,} views, {age_str}) -> Saving as '{target_file.name}'"
            )
            try:
                res = self.download_short(video_url, target_path=target_file)
                out_copy = out_ref_dir / target_file.name
                shutil.copy2(target_file, out_copy)
                log_success(f"Saved reference video matching title -> {out_copy}")
                results.append(res)
            except Exception as e:
                log_warning(f"Download/verification failed for candidate: {e}. Trying next...")

        if len(results) < count:
            log_warning(f"Found {len(results)}/{count} viral candidates in primary scan; checking unfiltered recent Shorts...")

        if not results:
            raise RuntimeError(
                f"No viral 3D Animation Shorts found for '{effective_niche}'."
            )
        return results

    def search_and_download_trending_short(self, niche: Optional[str] = None) -> ScoutResult:
        """
        Auto-Trend Search (US market) with STRICT viral rules:
          1. Search results sorted by view count (plus a relevance-ordered pool).
          2. Title must be English AND on-niche (NICHE_RELEVANCE_KEYWORDS).
          3. Full metadata re-check: views >= threshold, 15-60s, vertical, English.
          4. Thresholds: MIN_REFERENCE_VIEWS first, then ABSOLUTE_MIN_REFERENCE_VIEWS.
             There is NO fallback to low-view videos: if nothing qualifies we stop with an error.
          5. Already-processed video IDs are always skipped.
        """
        effective_niche = niche or config.DEFAULT_NICHE
        log_info(f"Auto-trend scouting VIRAL US Shorts for niche: '{effective_niche}'...")

        processed_ids = set(get_processed_video_ids() or [])
        if processed_ids:
            log_info(f"Duplicate prevention: {len(processed_ids)} previously processed reference IDs excluded.")

        candidates = self._collect_search_candidates(effective_niche, processed_ids)
        candidates.sort(
            key=lambda c: (c.get("view_count") or 0, self._relevance_score(c.get("title", ""))),
            reverse=True,
        )
        log_info(f"Collected {len(candidates)} on-niche English Short candidates.")

        thresholds = sorted({config.MIN_REFERENCE_VIEWS, config.ABSOLUTE_MIN_REFERENCE_VIEWS}, reverse=True)
        tried: set = set()
        for min_views in thresholds:
            pool = [
                c for c in candidates
                if c["id"] not in tried and (c.get("view_count") is None or c["view_count"] >= min_views)
            ]
            log_info(f"Viral tier >= {min_views:,} views: {len(pool)} candidate(s)")
            for idx, c in enumerate(pool[:5], 1):
                vc = c.get("view_count")
                log_info(f"   [{idx}] {c.get('title', '')[:60]} ({c.get('duration')}s, "
                         f"{f'{vc:,}' if vc else '?'} views)")

            for c in pool[:10]:
                tried.add(c["id"])
                info = self._verify_candidate(c["id"], c.get("title", ""), min_views)
                if not info:
                    continue
                video_url = info.get("webpage_url") or f"https://www.youtube.com/watch?v={c['id']}"
                log_info(f"Selected viral reference: '{info.get('title')}' "
                         f"({info.get('view_count', 0):,} views) -> {video_url}")
                try:
                    return self.download_short(video_url)
                except Exception as e:
                    log_warning(f"Download/verification failed for this candidate: {e}. Trying next...")

        raise RuntimeError(
            f"No viral (>= {config.ABSOLUTE_MIN_REFERENCE_VIEWS:,} views), on-niche, vertical English Short "
            f"found for '{effective_niche}'. Pass a specific Short directly: python main.py <youtube_shorts_url>"
        )

    def scout(
        self,
        source: Optional[str] = None,
        niche: Optional[str] = None,
        use_dummy: bool = False,
    ) -> ScoutResult:
        """
        Universal entrypoint:
        - If use_dummy is True and source exists locally, loads it.
        - If source is a direct URL, downloads that URL.
        - If source is an existing local file, loads that file.
        - Otherwise auto-searches top-performing viral US Shorts in the niche.
        """
        if use_dummy and source and os.path.exists(source):
            return self.inspect_local(source)

        if source and (source.startswith("http://") or source.startswith("https://")):
            return self.download_short(source)

        if source and os.path.exists(source):
            return self.inspect_local(source)

        # Auto-trend search for US niche
        target_niche = niche or source or config.DEFAULT_NICHE
        return self.search_and_download_trending_short(target_niche)
