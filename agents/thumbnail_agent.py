"""
Thumbnail, Title & Trending Tags Generator Agent (`agents/thumbnail_agent.py`).

Creates vertical 9:16 YouTube Shorts thumbnails (`1080x1920`), high-CTR titles,
descriptions, and trending YouTube Studio tags using the cleanest un-subtitled
main-scene climax frames from each rendered 3D clip.
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

import config
from schemas import VideoScript
from utils.logger import log_info, log_success, log_warning


def _load_font(names: Tuple[str, ...], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_dir = Path(r"C:\Windows\Fonts")
    for fname in names:
        fpath = font_dir / fname
        if fpath.exists():
            try:
                return ImageFont.truetype(str(fpath), size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def _draw_outlined_text(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str,
    stroke_fill: str = "#090d16",
    stroke_width: int = 8,
    shadow_offset: int = 7,
    anchor: str = "mm",
) -> None:
    x, y = xy
    if shadow_offset > 0:
        draw.text(
            (x + shadow_offset, y + shadow_offset),
            text,
            font=font,
            fill="#020617",
            stroke_width=stroke_width,
            stroke_fill="#020617",
            anchor=anchor,
        )
    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
        anchor=anchor,
    )


def _wrap_headline_lines(text: str, max_chars_per_line: int = 16) -> List[str]:
    clean = re.sub(r"[^\w\s!?\-',.]", "", (text or "").upper()).strip()
    words = clean.split()
    if not words:
        return ["3D CHALLENGE!"]
    lines: List[str] = []
    cur = ""
    for w in words:
        cand = f"{cur} {w}".strip()
        if len(cand) <= max_chars_per_line or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines[:3]


def _extract_clean_frame(mp4_path: Path, out_jpg: Path, ratio: float = 0.52) -> Optional[Path]:
    """Extract an un-subtitled frame from a scene `_anim.mp4` or clip using FFmpeg."""
    if not mp4_path.exists():
        return None
    try:
        probe = subprocess.run(
            [
                config.FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(mp4_path),
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        dur = float((probe.stdout or "2.5").strip() or 2.5)
        seek_t = max(0.25, min(dur - 0.15, dur * ratio))
        cmd = [
            config.FFMPEG_BIN, "-y", "-v", "error",
            "-ss", f"{seek_t:.2f}",
            "-i", str(mp4_path),
            "-frames:v", "1",
            "-q:v", "2",
            str(out_jpg),
        ]
        subprocess.run(cmd, capture_output=True, timeout=15, check=False)
        if out_jpg.exists() and out_jpg.stat().st_size > 10_000:
            return out_jpg
    except Exception:
        pass
    return None


def _apply_vertical_scrims(img: Image.Image) -> Image.Image:
    """Darken top & bottom bands gently while leaving center characters crystal-bright."""
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    top_band = int(h * 0.23)
    for y in range(top_band):
        alpha = int(195 * (1.0 - y / top_band) ** 1.35)
        od.line([(0, y), (w, y)], fill=(8, 13, 28, alpha))
    bot_start = int(h * 0.79)
    bot_span = max(1, h - bot_start)
    for y in range(bot_start, h):
        alpha = int(190 * ((y - bot_start) / bot_span) ** 1.3)
        od.line([(0, y), (w, y)], fill=(8, 13, 28, alpha))
    merged = Image.alpha_composite(img.convert("RGBA"), overlay)
    return merged.convert("RGB")


class ThumbnailAndSeoAgent:
    """Generates viral YouTube covers/thumbnails, clickable titles, and trending SEO tags."""

    BASE_TRENDING_TAGS = [
        "shorts",
        "youtubeshorts",
        "3danimation",
        "animation",
        "funnyshorts",
        "3dcartoon",
        "viral",
        "trending",
        "comedyshorts",
        "kidsanimation",
        "cartoonchallenge",
        "prank",
        "3dshortfilm",
        "pixarstyle",
        "funnystory",
    ]

    def build_seo_metadata(self, script: VideoScript) -> Dict[str, Any]:
        """Return polished SEO title, thumbnail headline, description, and <=500-char YouTube tags."""
        corpus = " ".join(
            [script.title or "", script.hook_text or ""]
            + [s.narration for s in script.scenes]
            + [p for s in script.scenes for p in (s.scene_props or [])]
        ).lower()

        raw_title = (script.youtube_seo_title or script.title or "").strip()
        if not raw_title or len(raw_title) < 12:
            raw_title = script.title
        if "#shorts" not in raw_title.lower() and len(raw_title) <= 84:
            raw_title = f"{raw_title} #shorts"

        headline = (script.thumbnail_headline or "").strip()
        if not headline:
            if any(w in corpus for w in ("cactus", "prickly")):
                headline = "CACTUS PRANK?!"
            elif any(w in corpus for w in ("cake", "strawberry_cake", "ice_cream")):
                headline = "CAKE SMASH PRANK!"
            elif any(w in corpus for w in ("stair", "musical", "climb")):
                headline = "CAN HE CLIMB?!"
            elif any(w in corpus for w in ("wall", "truck", "lift")):
                headline = "WATCH THIS FALL!"
            else:
                words = [w for w in re.sub(r"[^\w\s]", "", script.hook_text or script.title).split() if len(w) > 2]
                headline = " ".join(words[:3]).upper() + "!"

        desc = (script.youtube_description or "").strip()
        if not desc:
            desc = (
                f"{script.hook_text} Watch what happens next in this funny 3D animated challenge! "
                f"Hit LIKE and SUBSCRIBE for brand new 3D cartoon Shorts every day!\n\n"
                f"#shorts #3danimation #funny #cartoon #viral"
            )

        dynamic_tags: List[str] = []
        topic_candidates = [t.strip().lstrip("#").lower() for t in (script.trending_tags or []) if t.strip()]
        dynamic_tags.extend(topic_candidates)
        if any(w in corpus for w in ("cactus", "prickly", "cake", "ice cream", "waffle")):
            dynamic_tags.extend(["cakechallenge", "cactusprank", "foodchallenge", "try not to laugh", "prankwar"])
        if any(w in corpus for w in ("stair", "musical", "melody", "balloon", "jump")):
            dynamic_tags.extend(["musicalstairs", "obbychallenge", "parkour3d", "funnycartoon", "climbchallenge"])
        for prop in [p for s in script.scenes for p in (s.scene_props or [])]:
            clean_p = prop.replace("_", " ").strip().lower()
            if clean_p and clean_p not in dynamic_tags and len(clean_p) >= 3:
                dynamic_tags.append(clean_p)
        dynamic_tags.extend(self.BASE_TRENDING_TAGS)

        deduped_tags: List[str] = []
        total_len = 0
        for tg in dynamic_tags:
            t_clean = re.sub(r"\s+", " ", tg).strip()
            if not t_clean or t_clean in deduped_tags:
                continue
            add_len = len(t_clean) + (1 if deduped_tags else 0)
            if total_len + add_len > 485:
                break
            deduped_tags.append(t_clean)
            total_len += add_len

        outro_sc = next((s for s in reversed(script.scenes) if getattr(s, "is_outro_epilogue", False)), None)
        outro_line = (outro_sc.narration if outro_sc else (script.cliffhanger_hook or "")).strip()

        return {
            "clip_index": script.clip_index,
            "youtube_seo_title": raw_title,
            "thumbnail_headline": headline,
            "outro_closing_line": outro_line,
            "cliffhanger_badge_text": getattr(script, "cliffhanger_badge_text", "") or "",
            "outro_vfx_style": getattr(script, "outro_vfx_style", "") or "",
            "youtube_description": desc,
            "trending_tags": deduped_tags,
            "youtube_studio_tags_csv": ",".join(deduped_tags),
        }

    def _pick_best_hero_frame(self, script: VideoScript, clip_dir: Path) -> Optional[Path]:
        """Select clean HUD-free un-subtitled peak main-scene frame for vertical 9:16 Shorts thumbnail."""
        tmp_dir = clip_dir / "thumb_candidates"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        main_scenes = [
            s for s in script.scenes if not bool(getattr(s, "is_outro_epilogue", False))
        ] or list(script.scenes)
        n_main = len(main_scenes)
        # Strict HUD-free scenes BEFORE final main scene (`n_main`) where `like_subscribe_cta` activates!
        hud_cutoff = n_main if n_main >= 2 else (n_main + 1)
        clean_candidates = [
            s.scene_number for s in main_scenes
            if s.scene_number < hud_cutoff and getattr(s, "lead_action", "") != "plead_camera_help"
        ]
        if not clean_candidates:
            clean_candidates = [s.scene_number for s in main_scenes[: max(1, n_main - 1)]]
        ordered_indices = sorted(clean_candidates, reverse=True)
        top_clean_idx = ordered_indices[0] if ordered_indices else 1
        best_path: Optional[Path] = None
        best_score = -1.0

        for idx in ordered_indices:
            shot_jpg = clip_dir / f"scene_{idx:02d}_shot1.jpg"
            anim_mp4 = clip_dir / f"scene_{idx:02d}_anim.mp4"
            cand_jpg = tmp_dir / f"cand_{idx:02d}.jpg"
            extracted = shot_jpg if (shot_jpg.exists() and shot_jpg.stat().st_size > 10_000) else _extract_clean_frame(anim_mp4, cand_jpg, ratio=0.55)
            if not extracted:
                continue
            try:
                with Image.open(extracted) as im:
                    edge_stat = im.convert("L").filter(ImageFilter.FIND_EDGES)
                    mean_luma = sum(im.convert("L").getdata()) / (im.width * im.height)
                    edge_energy = sum(edge_stat.getdata()) / (im.width * im.height)
                    climax_bonus = 12.0 if idx == top_clean_idx else 3.0
                    score = edge_energy + climax_bonus - (30.0 if mean_luma < 45 else 0.0)
                    if score > best_score:
                        best_score = score
                        best_path = extracted
            except Exception:
                if best_path is None:
                    best_path = extracted

        return best_path

    def _render_shorts_thumbnail(self, hero_img: Image.Image, headline: str, out_path: Path) -> Path:
        """Render vibrant 1080x1920 (9:16) vertical YouTube Shorts thumbnail with crisp top headline & CTA."""
        W = config.VIDEO_WIDTH if config.VIDEO_WIDTH < config.VIDEO_HEIGHT else 1080
        H = config.VIDEO_HEIGHT if config.VIDEO_WIDTH < config.VIDEO_HEIGHT else 1920
        canvas = hero_img.resize((W, H), Image.Resampling.LANCZOS)
        canvas = ImageEnhance.Color(canvas).enhance(1.24)
        canvas = ImageEnhance.Contrast(canvas).enhance(1.12)
        canvas = _apply_vertical_scrims(canvas)

        draw = ImageDraw.Draw(canvas)

        # Glowing border accent frame
        draw.rectangle([(10, 10), (W - 11, H - 11)], outline="#facc15", width=10)

        # Top badge pill
        pill_font = _load_font(("ariblk.ttf", "arialbd.ttf"), 34)
        draw.rounded_rectangle([(280, 48), (800, 114)], radius=33, fill="#ef4444", outline="#ffffff", width=5)
        _draw_outlined_text(draw, (540, 81), "WAIT FOR THE END!", pill_font, fill="#ffffff", stroke_width=4, shadow_offset=3)

        # Big bold 2-line headline above hero face
        lines = _wrap_headline_lines(headline, max_chars_per_line=14)
        head_size = 94 if len(lines) <= 2 else 78
        head_font = _load_font(("ariblk.ttf", "impact.ttf", "arialbd.ttf"), head_size)
        y_start = 185 if len(lines) <= 2 else 170
        line_gap = 100 if len(lines) <= 2 else 82
        for i, line in enumerate(lines):
            col = "#facc15" if i % 2 == 0 else "#ffffff"
            _draw_outlined_text(draw, (540, y_start + i * line_gap), line, head_font, fill=col, stroke_width=10, shadow_offset=8)

        # Bottom CTA engagement badge
        cta_font = _load_font(("ariblk.ttf", "arialbd.ttf"), 38)
        draw.rounded_rectangle([(195, 1755), (885, 1845)], radius=45, fill="#0f172a", outline="#facc15", width=6)
        _draw_outlined_text(draw, (540, 1800), "LIKE & SUBSCRIBE FOR MORE!", cta_font, fill="#facc15", stroke_width=4, shadow_offset=3)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(out_path, quality=95)
        return out_path

    def generate_clip_package(self, script: VideoScript, clip_dir: Path) -> Dict[str, Any]:
        """Create 1080x1920 vertical Shorts thumbnail, title, description, and trending tags for one clip."""
        meta = self.build_seo_metadata(script)
        idx = script.clip_index
        hero_frame_path = self._pick_best_hero_frame(script, clip_dir)

        # Clean up legacy landscape (1280x720) or duplicate filenames so only 9:16 Shorts thumbnails remain
        for stale_name in (f"clip_{idx}_thumbnail_youtube.jpg", f"clip_{idx}_cover_shorts.jpg"):
            (config.OUTPUT_DIR / stale_name).unlink(missing_ok=True)

        thumb_shorts = config.OUTPUT_DIR / f"clip_{idx}_thumbnail_shorts.jpg"

        if hero_frame_path and hero_frame_path.exists():
            with Image.open(hero_frame_path) as im:
                rgb = im.convert("RGB")
                self._render_shorts_thumbnail(rgb, meta["thumbnail_headline"], thumb_shorts)
            meta["thumbnail_shorts_path"] = str(thumb_shorts)
            meta["thumbnail_dimensions"] = "1080x1920"
            meta["thumbnail_aspect"] = "9:16"
            log_success(f"[ThumbnailAgent] Clip #{idx} YouTube Shorts 9:16 (1080x1920) Thumbnail ready -> {thumb_shorts.name}")
        else:
            log_warning(f"[ThumbnailAgent] Clip #{idx}: no source frame found in {clip_dir}")

        meta_json_path = config.OUTPUT_DIR / f"clip_{idx}_youtube_meta.json"
        meta_json_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        return meta

    def write_upload_pack_markdown(self, metas: List[Dict[str, Any]]) -> Path:
        """Write consolidated copy-paste YouTube Shorts upload sheet (`output/youtube_upload_pack.md`)."""
        md_lines = [
            "# YouTube Shorts Upload Pack — Judul, Thumbnail 9:16 & Trending Tags",
            "",
        ]
        for m in metas:
            idx = m["clip_index"]
            md_lines.extend([
                f"## Clip #{idx}",
                f"- **Judul YouTube Shorts**: `{m['youtube_seo_title']}`",
                f"- **Teks Thumbnail Shorts**: `{m['thumbnail_headline']}`",
                f"- **Kalimat Penutup (1-2s Outro)**: `{m.get('outro_closing_line', '')}`",
                f"- **Efek Penutup**: `{m.get('outro_vfx_style', '')}` · Badge: `{m.get('cliffhanger_badge_text', '')}`",
                f"- **Thumbnail YouTube Shorts (1080x1920 / 9:16)**: `{m.get('thumbnail_shorts_path', '')}`",
                f"- **Trending Tags (CSV untuk YouTube Studio)**:",
                f"```text\n{m['youtube_studio_tags_csv']}\n```",
                f"- **Deskripsi**:",
                f"```text\n{m['youtube_description']}\n```",
                "",
            ])
        out_md = config.OUTPUT_DIR / "youtube_upload_pack.md"
        out_md.write_text("\n".join(md_lines), encoding="utf-8")
        log_success(f"[ThumbnailAgent] YouTube Shorts Upload Pack saved -> {out_md}")
        return out_md

