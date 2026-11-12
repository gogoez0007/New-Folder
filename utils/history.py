"""
History Manager Utility for Shorts Cloner Pipeline.
Tracks processed YouTube video IDs and topic titles in a persistent JSON log
to guarantee duplicate prevention (ensuring 100% unique daily reference videos and scripts).
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

import config
from utils.logger import log_info, log_success, log_warning


DEFAULT_HISTORY_FILE = config.WORKSPACE_DIR / "history_log.json"
MIRROR_HISTORY_FILE = config.OUTPUT_DIR / "history_log.json"


def _init_default_structure() -> Dict[str, Any]:
    return {
        "version": "1.0",
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "processed_video_ids": {},
        "processed_topics": [],
        "uploaded_clips": {},
    }


def load_history() -> Dict[str, Any]:
    """
    Load history log from workspace or output directory.
    If neither exists, returns a new initialized structure.
    """
    history_file = DEFAULT_HISTORY_FILE
    if not history_file.exists() and MIRROR_HISTORY_FILE.exists():
        history_file = MIRROR_HISTORY_FILE

    if history_file.exists():
        try:
            data = json.loads(history_file.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "processed_video_ids" in data:
                return data
        except Exception as e:
            log_warning(f"Could not parse history log ({e}). Initializing fresh structure.")

    return _init_default_structure()


def save_history(history: Dict[str, Any]) -> None:
    """Save history log to both workspace and output directories."""
    history["last_updated"] = datetime.now(timezone.utc).isoformat()
    json_str = json.dumps(history, indent=2, ensure_ascii=False)

    for path in [DEFAULT_HISTORY_FILE, MIRROR_HISTORY_FILE]:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json_str, encoding="utf-8")
        except Exception as e:
            log_warning(f"Failed to write history file to {path}: {e}")


def normalize_video_title(title: str) -> str:
    """Normalize a YouTube title to alphanumeric words (stripping hashtags & emojis) for dedup."""
    if not title:
        return ""
    cleaned = re.sub(r"#\w+", "", title.lower())
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
    return " ".join(cleaned.split())


def is_video_processed(video_id: str) -> bool:
    """Check if a YouTube video ID has already been processed."""
    if not video_id:
        return False
    history = load_history()
    return video_id in history.get("processed_video_ids", {})


def is_video_title_processed(title: str) -> bool:
    """Check if a normalized reference title has already been processed (catches re-uploads)."""
    norm = normalize_video_title(title)
    if len(norm) < 8:
        return False
    history = load_history()
    for meta in history.get("processed_video_ids", {}).values():
        existing_norm = normalize_video_title(meta.get("title", ""))
        if not existing_norm:
            continue
        if norm == existing_norm or (len(norm) >= 14 and (norm in existing_norm or existing_norm in norm)):
            return True
    return False


def get_processed_video_ids() -> Set[str]:
    """Return a set of all processed YouTube video IDs."""
    history = load_history()
    return set(history.get("processed_video_ids", {}).keys())


def record_processed_video(
    video_id: str,
    title: str,
    duration: float = 0.0,
    views: Optional[int] = None,
) -> None:
    """Record a processed YouTube video ID and title in the history log."""
    if not video_id:
        return

    history = load_history()
    history.setdefault("processed_video_ids", {})[video_id] = {
        "title": title,
        "duration": duration,
        "views": views or 0,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
    save_history(history)
    log_info(f"Recorded reference video in history: [{video_id}] {title[:40]}")


def get_processed_topics() -> List[str]:
    """Return a list of processed script titles/topics for exclusion prompts."""
    history = load_history()
    topics = []
    for item in history.get("processed_topics", []):
        t = item.get("title") or item.get("topic")
        if t:
            topics.append(t)
    return topics


def is_topic_processed(title_or_topic: str) -> bool:
    """Check if a topic or title has already been generated."""
    if not title_or_topic:
        return False
    norm = title_or_topic.strip().lower()
    for existing in get_processed_topics():
        if norm in existing.lower() or existing.lower() in norm:
            return True
    return False


def record_processed_topic(title: str, niche: str = "", clip_index: int = 1) -> None:
    """Record a generated script topic into history."""
    if not title:
        return

    history = load_history()
    history.setdefault("processed_topics", []).append({
        "title": title,
        "niche": niche,
        "clip_index": clip_index,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    })
    save_history(history)
    log_info(f"Recorded generated topic in history: \"{title[:45]}\"")


def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 hex digest of a rendered video file in chunks."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_clip_already_uploaded(mp4_path: Path) -> Optional[Dict[str, Any]]:
    """Return existing upload record if this exact MP4 SHA-256 was already uploaded."""
    if not mp4_path.exists():
        return None
    sha = compute_file_sha256(mp4_path)
    history = load_history()
    rec = history.get("uploaded_clips", {}).get(sha)
    return rec if isinstance(rec, dict) and rec.get("youtube_video_id") else None


def get_reserved_publish_slots_utc() -> Set[str]:
    """Return set of UTC ISO publishAt timestamps already reserved by scheduled uploads."""
    history = load_history()
    slots: Set[str] = set()
    for rec in history.get("uploaded_clips", {}).values():
        if isinstance(rec, dict) and rec.get("publish_at_utc"):
            slots.add(str(rec["publish_at_utc"]))
    return slots


def record_uploaded_clip(
    mp4_path: Path,
    youtube_video_id: str,
    title: str,
    privacy_status: str,
    publish_at_utc: Optional[str] = None,
    publish_at_et: Optional[str] = None,
    publish_at_wib: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Persist successful YouTube upload metadata for dedup & slot collision avoidance."""
    sha = compute_file_sha256(mp4_path) if mp4_path.exists() else mp4_path.name
    entry = {
        "youtube_video_id": youtube_video_id,
        "url": f"https://www.youtube.com/shorts/{youtube_video_id}",
        "studio_url": f"https://studio.youtube.com/video/{youtube_video_id}/edit",
        "title": title,
        "file_name": mp4_path.name,
        "file_sha256": sha,
        "privacy_status": privacy_status,
        "publish_at_utc": publish_at_utc or "",
        "publish_at_et": publish_at_et or "",
        "publish_at_wib": publish_at_wib or "",
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        entry.update({k: v for k, v in extra.items() if v is not None})
    history = load_history()
    history.setdefault("uploaded_clips", {})[sha] = entry
    save_history(history)
    log_success(f"Recorded YouTube upload [{youtube_video_id}] in history_log.json")
    return entry
