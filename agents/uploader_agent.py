"""
YouTube Data API v3 Auto-Uploader Agent (`agents/uploader_agent.py`).

Handles:
1. OAuth 2.0 Desktop flow (`credentials/client_secrets.json`) + silent refresh token persistence (`credentials/youtube_token.json`).
2. Channel health verification (`channels.list(mine=True)`).
3. Resumable upload of vertical 9:16 Shorts (`videos.insert`) with full US-targeted English metadata,
   non-Kids RPM setting (`selfDeclaredMadeForKids=False`), <=500-char trending tags, and optimal
   US Prime Time scheduling (`status.publishAt` in UTC, graceful fallback to Private on unverified apps).
4. Optional thumbnail setting & SHA-256 deduplication so clips are never uploaded twice.
"""

import json
import random
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.auth.exceptions import RefreshError, TransportError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

import config
from utils.history import (
    get_reserved_publish_slots_utc,
    is_clip_already_uploaded,
    record_uploaded_clip,
)
from utils.logger import log_error, log_info, log_success, log_warning
from utils.us_scheduler import compute_next_us_prime_slots


RETRIABLE_STATUS_CODES = {500, 502, 503, 504}


def _trim_tags_under_500_chars(raw_tags: List[str]) -> List[str]:
    """Ensure tag list obeys YouTube Studio's 500-character combined budget."""
    clean: List[str] = []
    total = 0
    for tg in raw_tags:
        t = re.sub(r"\s+", " ", (tg or "").strip().lstrip("#")).strip()
        if not t or t in clean or len(t) > 60:
            continue
        # YouTube counts quotes/commas roughly per tag length + 2
        cost = len(t) + (3 if " " in t else 1)
        if total + cost > 460:
            break
        clean.append(t)
        total += cost
    return clean


class YouTubeUploaderAgent:
    """Automates OAuth authentication, channel verification, and US-timed YouTube Shorts uploads."""

    def __init__(
        self,
        client_secrets_file: Optional[Path] = None,
        token_file: Optional[Path] = None,
        scopes: Optional[List[str]] = None,
        archive_dir: Optional[Path] = None,
    ):
        self.client_secrets_file = Path(client_secrets_file or config.YOUTUBE_CLIENT_SECRETS_FILE)
        self.token_file = Path(token_file or config.YOUTUBE_TOKEN_FILE)
        self.auth_state_file = self.token_file.parent / "auth_state.json"
        self.archive_dir = Path(archive_dir or config.SAVED_CLIPS_DIR)
        self.scopes = list(scopes or config.YOUTUBE_SCOPES)
        self._service = None

    @staticmethod
    def _slugify_title(text: str, max_len: int = 44) -> str:
        clean = re.sub(r"#\w+", "", text or "")
        clean = re.sub(r"[^A-Za-z0-9]+", "_", clean).strip("_")
        return (clean[:max_len].strip("_")) or "short_clip"

    def archive_uploaded_clip(
        self,
        mp4_path: Path,
        video_id: str,
        meta: Optional[Dict[str, Any]] = None,
        thumbnail_path: Optional[Path] = None,
        upload_info: Optional[Dict[str, Any]] = None,
        timestamp_local: Optional[datetime] = None,
    ) -> Dict[str, str]:
        """Permanently save uploaded clip, thumbnail, and metadata so future batches never overwrite them."""
        ts = timestamp_local or datetime.now()
        day_dir = self.archive_dir / ts.strftime("%Y-%m-%d")
        day_dir.mkdir(parents=True, exist_ok=True)

        m = meta or {}
        c_idx = int(m.get("clip_index") or 1)
        title = (m.get("youtube_seo_title") or mp4_path.stem).strip()
        slug = self._slugify_title(title)
        stem = f"{ts.strftime('%H%M%S')}_clip{c_idx}_{video_id}_{slug}"

        dst_mp4 = day_dir / f"{stem}.mp4"
        shutil.copy2(mp4_path, dst_mp4)
        saved: Dict[str, str] = {"archived_mp4_path": str(dst_mp4)}

        if thumbnail_path and Path(thumbnail_path).exists():
            dst_thumb = day_dir / f"{stem}_thumb{Path(thumbnail_path).suffix or '.jpg'}"
            shutil.copy2(thumbnail_path, dst_thumb)
            saved["archived_thumbnail_path"] = str(dst_thumb)

        dst_meta = day_dir / f"{stem}_meta.json"
        meta_payload = {
            **m,
            "youtube_upload": {
                **(upload_info or {}),
                "youtube_video_id": video_id,
                **saved,
            },
        }
        dst_meta.write_text(json.dumps(meta_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        saved["archived_meta_path"] = str(dst_meta)
        log_success(f"[YouTubeUploader] Archived permanent clip -> {dst_mp4}")
        return saved

    def has_valid_token(self) -> bool:
        if not self.token_file.exists():
            return False
        try:
            creds = Credentials.from_authorized_user_file(str(self.token_file), self.scopes)
            return bool(creds and (creds.valid or creds.refresh_token))
        except Exception:
            return False

    def get_credentials(
        self,
        interactive: bool = True,
        open_browser: bool = True,
        timeout_seconds: Optional[int] = 180,
    ) -> Credentials:
        """Load, refresh silently, or acquire OAuth 2.0 credentials with persistent refresh token."""
        creds: Optional[Credentials] = None
        if self.token_file.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_file), self.scopes)
            except Exception as err:
                log_warning(f"[YouTubeUploader] Could not read existing token ({err}). Re-authorizing...")
                creds = None

        if creds and creds.valid:
            return creds

        if creds and creds.expired and creds.refresh_token:
            try:
                log_info("[YouTubeUploader] Refreshing OAuth access token silently...")
                creds.refresh(Request())
                self._save_credentials(creds)
                log_success("[YouTubeUploader] OAuth token refreshed cleanly.")
                return creds
            except Exception as err:
                log_warning(f"[YouTubeUploader] Silent token refresh failed: {err}")
                creds = None

        if not interactive:
            raise RuntimeError(
                f"YouTube OAuth token missing or expired at '{self.token_file}'. "
                f"Run 'python main.py --auth-only' once to sign in and save credentials."
            )

        if not self.client_secrets_file.exists():
            raise FileNotFoundError(
                f"Missing Google OAuth client secrets file at '{self.client_secrets_file}'. "
                f"Download OAuth Desktop Client JSON from Google Cloud Console first."
            )

        log_info("[YouTubeUploader] Starting Google OAuth 2.0 Desktop consent flow...")
        flow = InstalledAppFlow.from_client_secrets_file(str(self.client_secrets_file), self.scopes)
        creds = flow.run_local_server(
            host="localhost",
            port=0,
            authorization_prompt_message="OAUTH_AUTH_URL: {url}",
            success_message="YouTube Auto-Uploader authorized! You may close this browser tab.",
            open_browser=open_browser,
            timeout_seconds=timeout_seconds,
            access_type="offline",
            prompt="consent",
        )
        self._save_credentials(creds)
        self._record_interactive_auth_timestamp()
        log_success(f"[YouTubeUploader] Saved persistent OAuth refresh token -> {self.token_file}")
        return creds

    def _save_credentials(self, creds: Credentials) -> None:
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self.token_file.write_text(creds.to_json(), encoding="utf-8")

    def _record_interactive_auth_timestamp(self, granted_at: Optional[datetime] = None) -> None:
        ts = (granted_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
        self.auth_state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "granted_at_utc": ts.isoformat(),
            "token_file": str(self.token_file),
        }
        self.auth_state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def check_auth_status(self) -> Dict[str, Any]:
        """Verify live OAuth refresh health strictly against Google (no timer countdown)."""
        base: Dict[str, Any] = {
            "ok": False,
            "needs_auth": True,
            "reason": "unknown",
            "message": "",
            "token_file": str(self.token_file),
        }

        if not self.token_file.exists():
            base["reason"] = "missing_token"
            base["message"] = f"File token OAuth tidak ditemukan ({self.token_file}). Wajib jalankan auth_youtube.bat."
            return base

        try:
            creds = Credentials.from_authorized_user_file(str(self.token_file), self.scopes)
        except Exception as err:
            base["reason"] = "corrupt_token"
            base["message"] = f"File token OAuth rusak ({err}). Wajib jalankan ulang auth_youtube.bat."
            return base

        if not creds or not creds.refresh_token:
            base["reason"] = "corrupt_token"
            base["message"] = "Refresh token OAuth kosong. Wajib jalankan ulang auth_youtube.bat."
            return base

        # Probe Google token endpoint directly: only trigger when token is truly expired/revoked
        transient_err: Optional[Exception] = None
        for attempt in range(2):
            transient_err = None
            try:
                creds.refresh(Request())
                self._save_credentials(creds)
                break
            except TransportError as err:
                transient_err = err
                if attempt == 0:
                    time.sleep(0.15)
            except RefreshError as err:
                err_l = str(err).lower()
                transient_markers = ("timed out", "connection", "temporarily unavailable", "502", "503", "504")
                if any(m in err_l for m in transient_markers):
                    transient_err = err
                    if attempt == 0:
                        time.sleep(0.15)
                else:
                    base["reason"] = "expired_or_revoked"
                    base["message"] = f"Token OAuth YouTube sudah kedaluwarsa atau dicabut Google ({err}). Wajib jalankan auth_youtube.bat sekarang."
                    return base
            except Exception as err:
                base["reason"] = "expired_or_revoked"
                base["message"] = f"Gagal refresh token OAuth ({err}). Jalankan ulang auth_youtube.bat."
                return base

        if transient_err is not None:
            base["ok"] = True
            base["needs_auth"] = False
            base["reason"] = "offline_network_error"
            base["message"] = f"Jaringan sementara tidak tersedia saat cek watchdog ({transient_err})."
            return base

        base["ok"] = True
        base["needs_auth"] = False
        base["reason"] = "valid"
        base["message"] = "Token YouTube OAuth aktif & valid."
        return base

    def get_service(self, interactive: bool = True, open_browser: bool = True):
        if self._service is None:
            creds = self.get_credentials(interactive=interactive, open_browser=open_browser)
            self._service = build("youtube", "v3", credentials=creds, cache_discovery=False)
        return self._service

    def verify_channel(
        self,
        interactive: bool = True,
        open_browser: bool = True,
        timeout_seconds: Optional[int] = 180,
    ) -> Dict[str, Any]:
        """Inspect authenticated YouTube channel metadata (title, ID, country, language)."""
        creds = self.get_credentials(
            interactive=interactive,
            open_browser=open_browser,
            timeout_seconds=timeout_seconds,
        )
        if self._service is None:
            self._service = build("youtube", "v3", credentials=creds, cache_discovery=False)
        yt = self._service
        resp = yt.channels().list(part="snippet,status,statistics", mine=True).execute()
        items = resp.get("items", [])
        if not items:
            raise RuntimeError(
                "No YouTube channel found on the authorized Google account. "
                "Create a YouTube channel at studio.youtube.com before uploading."
            )
        ch = items[0]
        snip = ch.get("snippet", {})
        stat = ch.get("status", {})
        stats = ch.get("statistics", {})
        info = {
            "channel_id": ch.get("id", ""),
            "title": snip.get("title", ""),
            "country": snip.get("country", "UNSET"),
            "default_language": snip.get("defaultLanguage", "UNSET"),
            "privacy_status": stat.get("privacyStatus", ""),
            "made_for_kids": stat.get("madeForKids"),
            "subscriber_count": stats.get("subscriberCount", "0"),
            "video_count": stats.get("videoCount", "0"),
        }
        log_success(
            f"[YouTubeUploader] Connected Channel: '{info['title']}' ({info['channel_id']}) | "
            f"country={info['country']} lang={info['default_language']} videos={info['video_count']}"
        )
        return info

    @staticmethod
    def _close_media_fd(media: MediaFileUpload) -> None:
        fd = getattr(media, "_fd", None)
        if fd is not None:
            try:
                fd.close()
            except Exception:
                pass

    def _execute_resumable_insert(self, yt, body: Dict[str, Any], mp4_path: Path) -> Dict[str, Any]:
        media = MediaFileUpload(
            str(mp4_path),
            mimetype="video/mp4",
            chunksize=4 * 1024 * 1024,
            resumable=True,
        )
        req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
        try:
            response = None
            retry = 0
            while response is None:
                try:
                    status, response = req.next_chunk()
                    if status:
                        log_info(f"[YouTubeUploader] Uploading {mp4_path.name}: {int(status.progress() * 100)}%")
                except HttpError as e:
                    if e.resp is not None and e.resp.status in RETRIABLE_STATUS_CODES:
                        retry += 1
                        if retry > 5:
                            raise
                        sleep_s = min(32.0, (2 ** retry) + random.uniform(0, 1))
                        log_warning(f"[YouTubeUploader] Transient HTTP {e.resp.status}; retrying in {sleep_s:.1f}s...")
                        time.sleep(sleep_s)
                    else:
                        raise
            return response
        finally:
            self._close_media_fd(media)

    def upload_short(
        self,
        mp4_path: Path,
        meta: Dict[str, Any],
        slot_info: Optional[Dict[str, str]] = None,
        thumbnail_path: Optional[Path] = None,
        privacy_mode: str = "scheduled",
        made_for_kids: bool = False,
        category_id: str = "24",
        interactive: bool = False,
    ) -> Dict[str, Any]:
        """Upload one rendered 9:16 Short with US metadata, tags, and prime-time schedule."""
        mp4_path = Path(mp4_path)
        if not mp4_path.exists():
            raise FileNotFoundError(f"Video file not found for upload: {mp4_path}")

        existing = is_clip_already_uploaded(mp4_path)
        if existing:
            log_info(
                f"[YouTubeUploader] Skipping duplicate upload for {mp4_path.name} -> "
                f"already at {existing.get('url')}"
            )
            return {**existing, "skipped_duplicate": True}

        yt = self.get_service(interactive=interactive, open_browser=interactive)

        raw_title = (meta.get("youtube_seo_title") or f"3D Animated Short #{meta.get('clip_index', 1)} #shorts").strip()
        if "#shorts" not in raw_title.lower() and len(raw_title) <= 92:
            raw_title = f"{raw_title} #shorts"
        title = raw_title[:100]

        desc = (meta.get("youtube_description") or "").strip()
        closing_q = (meta.get("outro_closing_line") or "").strip()
        if closing_q and closing_q.lower() not in desc.lower():
            desc = f"{desc}\n\n👇 {closing_q}".strip()
        if "#shorts" not in desc.lower():
            desc = f"{desc}\n\n#shorts #3danimation #funny".strip()
        description = desc[:5000]

        tags = _trim_tags_under_500_chars(list(meta.get("trending_tags") or []))

        snippet = {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": str(category_id or config.YOUTUBE_CATEGORY_ID),
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en-US",
        }

        publish_at_utc = (slot_info or {}).get("publish_at_utc") or ""
        publish_at_et = (slot_info or {}).get("publish_at_et") or ""
        publish_at_wib = (slot_info or {}).get("publish_at_wib") or ""

        if privacy_mode == "scheduled" and publish_at_utc:
            status_body: Dict[str, Any] = {
                "privacyStatus": "private",
                "publishAt": publish_at_utc,
                "selfDeclaredMadeForKids": bool(made_for_kids),
            }
            effective_mode = "scheduled"
        else:
            pstat = privacy_mode if privacy_mode in ("private", "unlisted", "public") else "private"
            status_body = {
                "privacyStatus": pstat,
                "selfDeclaredMadeForKids": bool(made_for_kids),
            }
            effective_mode = pstat

        body = {"snippet": snippet, "status": status_body}
        log_info(
            f"[YouTubeUploader] Uploading '{title}' ({mp4_path.name}) | mode={effective_mode} "
            f"| ET={publish_at_et or 'N/A'} | WIB={publish_at_wib or 'N/A'}"
        )

        try:
            resp = self._execute_resumable_insert(yt, body, mp4_path)
        except HttpError as err:
            err_txt = str(err)
            # Graceful fallback if unverified API project rejects `publishAt` / `public`
            if ("publishAt" in status_body or status_body.get("privacyStatus") == "public") and err.resp is not None and err.resp.status in (400, 403):
                log_warning(
                    f"[YouTubeUploader] API declined scheduled/public status ({err.resp.status}: {err_txt[:180]}). "
                    f"Retrying as 'private' draft so video + SEO metadata still upload cleanly..."
                )
                status_body = {
                    "privacyStatus": "private",
                    "selfDeclaredMadeForKids": bool(made_for_kids),
                }
                effective_mode = "private_fallback"
                publish_at_utc = ""
                body["status"] = status_body
                resp = self._execute_resumable_insert(yt, body, mp4_path)
            else:
                raise

        video_id = resp.get("id", "")
        if not video_id:
            raise RuntimeError(f"YouTube upload returned no video ID: {resp}")

        actual_privacy = (resp.get("status") or {}).get("privacyStatus", effective_mode)
        log_success(
            f"[YouTubeUploader] UPLOADED -> https://www.youtube.com/shorts/{video_id} "
            f"(privacy={actual_privacy}, ET={publish_at_et or 'immediate'})"
        )

        # Optionally apply vertical thumbnail (non-fatal if restricted on channel/Shorts)
        thumb_status = "skipped"
        if thumbnail_path and Path(thumbnail_path).exists():
            thumb_media = MediaFileUpload(str(thumbnail_path), mimetype="image/jpeg")
            try:
                yt.thumbnails().set(
                    videoId=video_id,
                    media_body=thumb_media,
                ).execute()
                thumb_status = "applied"
                log_success(f"[YouTubeUploader] Thumbnail applied -> {Path(thumbnail_path).name}")
            except HttpError as te:
                thumb_status = f"skipped_api_{te.resp.status if te.resp else 'err'}"
                log_warning(
                    f"[YouTubeUploader] Thumbnail API skipped ({thumb_status}); video upload intact."
                )
            finally:
                self._close_media_fd(thumb_media)

        archive_info = self.archive_uploaded_clip(
            mp4_path=mp4_path,
            video_id=video_id,
            meta={**meta, "youtube_seo_title": title},
            thumbnail_path=thumbnail_path,
            upload_info={
                "privacy_status": actual_privacy,
                "publish_at_utc": publish_at_utc,
                "publish_at_et": publish_at_et,
                "publish_at_wib": publish_at_wib,
                "thumbnail_status": thumb_status,
            },
        )

        record = record_uploaded_clip(
            mp4_path=mp4_path,
            youtube_video_id=video_id,
            title=title,
            privacy_status=actual_privacy,
            publish_at_utc=publish_at_utc,
            publish_at_et=publish_at_et,
            publish_at_wib=publish_at_wib,
            extra=archive_info,
        )
        record["thumbnail_status"] = thumb_status
        record["skipped_duplicate"] = False
        return record

    def upload_output_batch(
        self,
        clip_pairs: List[tuple],
        privacy_mode: str = "scheduled",
        made_for_kids: bool = False,
        category_id: str = "24",
        slots_et: Optional[List[str]] = None,
        interactive: bool = False,
    ) -> List[Dict[str, Any]]:
        """Upload all clips cleanly, assigning distinct future US prime-time slots."""
        pending = []
        results: List[Dict[str, Any]] = []
        for mp4_path, meta, thumb_path in clip_pairs:
            existing = is_clip_already_uploaded(Path(mp4_path))
            if existing:
                log_info(f"[YouTubeUploader] Clip {Path(mp4_path).name} already uploaded -> {existing.get('url')}")
                results.append({**existing, "skipped_duplicate": True, "clip_index": meta.get("clip_index")})
            else:
                pending.append((Path(mp4_path), meta, Path(thumb_path) if thumb_path else None))

        if not pending:
            return results

        reserved = get_reserved_publish_slots_utc()
        slots = (
            compute_next_us_prime_slots(
                count=len(pending),
                tz_name=config.US_TARGET_TIMEZONE,
                slots_et=slots_et or config.US_PRIME_SLOTS_ET,
                reserved_utc_iso=reserved,
            )
            if privacy_mode == "scheduled"
            else [{} for _ in pending]
        )

        # Verify channel once before uploading batch
        self.verify_channel(interactive=interactive, open_browser=interactive)

        for idx, (mp4_path, meta, thumb_path) in enumerate(pending):
            slot = slots[idx] if idx < len(slots) else {}
            res = self.upload_short(
                mp4_path=mp4_path,
                meta=meta,
                slot_info=slot,
                thumbnail_path=thumb_path,
                privacy_mode=privacy_mode,
                made_for_kids=made_for_kids,
                category_id=category_id,
                interactive=interactive,
            )
            res["clip_index"] = meta.get("clip_index")
            results.append(res)

            # Update per-clip JSON metadata cleanly with YouTube URL & schedule info
            c_idx = meta.get("clip_index")
            if c_idx is not None:
                mpath = config.OUTPUT_DIR / f"clip_{c_idx}_youtube_meta.json"
                updated_meta = {**meta, "youtube_upload": res}
                mpath.write_text(json.dumps(updated_meta, indent=2, ensure_ascii=False), encoding="utf-8")

        return results

