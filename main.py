"""
Shorts Cloner Multi-Agent Orchestrator (CLI Entrypoint).
Analyzes a reference viral YouTube Short and automatically generates 2 to 4 original,
high-retention vertical 9:16 videos (.mp4) in a user-defined niche.
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path
from typing import List, Optional

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from agents.uploader_agent import YouTubeUploaderAgent
from utils.logger import (
    log_header,
    log_step,
    log_info,
    log_success,
    log_warning,
    log_error,
)


def run_pipeline(
    reference_source: str,
    target_niche: str,
    clip_count: int = 2,
    language: str = "en",
    voice: str = config.DEFAULT_VOICE,
    rate: str = config.DEFAULT_VOICE_RATE,
    auto_upload: bool = False,
    privacy_mode: str = config.YOUTUBE_UPLOAD_PRIVACY,
    us_slots: Optional[List[str]] = None,
    made_for_kids: bool = config.YOUTUBE_DEFAULT_MADE_FOR_KIDS,
    non_interactive: bool = False,
    cleanup_workspace: bool = False,
):
    """Execute the end-to-end multi-agent video generation pipeline."""
    from agents.scout_agent import TrendScoutAgent
    from agents.analyst_writer_agent import AnalystWriterAgent
    from agents.media_agent import MediaAgent
    from agents.subtitle_agent import SubtitleAgent
    from agents.editor_agent import GPUVideoEditorAgent
    from agents.thumbnail_agent import ThumbnailAndSeoAgent
    from utils.audio_gen import ensure_default_sfx

    start_total_time = time.time()
    log_header("Viral YouTube Shorts Cloner - Multi-Agent AI Pipeline")
    log_info(f"Reference Source: {reference_source}")
    log_info(f"Target Niche:     {target_niche}")
    log_info(f"Clip Count:       {clip_count}")
    log_info(f"Language / Voice: {language} / {voice} ({rate})")
    log_info(f"Active Codec:     {config.get_active_encoder()}")

    # Validate YouTube OAuth upfront BEFORE spending several minutes rendering GPU 3D scenes
    uploader = None
    if auto_upload:
        uploader = YouTubeUploaderAgent()
        uploader.get_credentials(interactive=not non_interactive, open_browser=not non_interactive)
        log_success("Pre-flight check: YouTube OAuth credentials valid & ready for auto-upload.")

    # Ensure default SFX are ready in assets/sfx
    ensure_default_sfx(config.SFX_DIR)

    # -------------------------------------------------------------------------
    # Step 1: Trend Scout Agent (Download Viral 3D Animation Pool)
    # -------------------------------------------------------------------------
    log_step(1, 5, "Trend Scout Agent: Ingesting Viral 3D Animation Videos")
    scout_agent = TrendScoutAgent(config.WORKSPACE_DIR)
    scout_pool = scout_agent.scout_animation_pool(
        source=reference_source,
        niche=target_niche,
        count=clip_count,
    )
    scout_result = scout_pool[0]
    source_video_paths = [r.video_path for r in scout_pool]
    source_video_durations = [r.duration for r in scout_pool]
    source_video_titles = [r.title for r in scout_pool]
    for idx, sr in enumerate(scout_pool, 1):
        log_success(
            f"Viral 3D Animation #{idx} ready: '{sr.title}' ({sr.duration:.1f}s, {sr.view_count or 0:,} views) -> {sr.video_path.name}"
        )


    # -------------------------------------------------------------------------
    # Step 2: Viral Analyst & Scriptwriter Agent (Multimodal Vision AI)
    # -------------------------------------------------------------------------
    log_step(2, 5, "Viral Analyst Agent: Multimodal 3D Animation Deconstruction & Kids Scriptwriting")
    analyst_agent = AnalystWriterAgent()
    production_batch = analyst_agent.analyze_and_generate(
        video_path=scout_result.video_path,
        target_niche=target_niche,
        clip_count=clip_count,
        language=language,
        reference_title=scout_result.title,
        reference_duration=scout_result.duration,
        video_paths=source_video_paths,
        video_durations=source_video_durations,
        reference_titles=source_video_titles,
    )

    # -------------------------------------------------------------------------
    # Initialize Downstream Agents
    # -------------------------------------------------------------------------
    media_agent = MediaAgent(default_voice=voice, default_rate=rate)
    subtitle_agent = SubtitleAgent()
    editor_agent = GPUVideoEditorAgent()
    thumb_agent = ThumbnailAndSeoAgent()

    final_rendered_clips = []
    youtube_metas = []

    # -------------------------------------------------------------------------
    # Steps 3, 4, 5 per Generated Clip
    # -------------------------------------------------------------------------
    for script in production_batch.generated_scripts:
        clip_idx = script.clip_index
        clip_title = script.title
        log_header(f"Producing Clip #{clip_idx}: \"{clip_title}\"")

        # Step 3: Media Generator Agent
        log_step(3, 5, f"[Clip #{clip_idx}] Generating Kids Voiceovers & Moving 3D Animation Cuts")
        media_batch = media_agent.generate_clip_media(
            script=script,
            base_dir=config.WORKSPACE_DIR,
            voice=voice,
            rate=rate,
            blueprint=production_batch.viral_blueprint,
            source_videos=source_video_paths,
        )

        # Step 4: Word-Level Subtitle Agent
        log_step(4, 5, f"[Clip #{clip_idx}] Transcribing Words on CUDA & Styling ASS Subtitles")
        clip_dir = config.WORKSPACE_DIR / f"clip_{clip_idx:02d}"
        scene_audios = [sc.audio_path for sc in media_batch.scenes]

        # Collect emphasis words & narration prompt for exact character names
        all_emphasis = []
        for sc in script.scenes:
            all_emphasis.extend(sc.subtitle_emphasis_words)
        clip_prompt = " ".join(sc.narration for sc in script.scenes)

        # Build SEO package early so thumbnail_headline drives the 0.0-2.35s HookBanner overlay
        meta = thumb_agent.generate_clip_package(script=script, clip_dir=clip_dir)

        ass_path = subtitle_agent.process_clip_subtitles(
            scene_audio_files=scene_audios,
            output_dir=clip_dir,
            clip_index=clip_idx,
            language=language,
            emphasis_keywords=all_emphasis,
            initial_prompt=clip_prompt,
            hook_headline=meta.get("thumbnail_headline") or script.thumbnail_headline or script.hook_text,
        )

        # Step 5: GPU Video Assembler Agent
        log_step(5, 5, f"[Clip #{clip_idx}] Rendering Video with Motion, SFX, & Subtitle Burn-In")
        output_clip_file = config.OUTPUT_DIR / f"final_clip_{clip_idx}.mp4"
        editor_agent.render_complete_clip(
            media_batch=media_batch,
            ass_subtitle_path=ass_path,
            output_final_mp4=output_clip_file,
        )

        youtube_metas.append(meta)
        final_rendered_clips.append(output_clip_file)

    upload_pack_md = thumb_agent.write_upload_pack_markdown(youtube_metas)

    upload_results = []
    if auto_upload:
        log_header("AUTO-UPLOADING SHORTS TO YOUTUBE (US HIGH-RPM PRIME TIME)")
        uploader = uploader or YouTubeUploaderAgent()
        clip_pairs = []
        for idx_pos, clip_path in enumerate(final_rendered_clips):
            meta = youtube_metas[idx_pos]
            thumb_p = Path(meta.get("thumbnail_shorts_path", "")) if meta.get("thumbnail_shorts_path") else None
            clip_pairs.append((clip_path, meta, thumb_p))
        upload_results = uploader.upload_output_batch(
            clip_pairs=clip_pairs,
            privacy_mode=privacy_mode,
            made_for_kids=made_for_kids,
            slots_et=us_slots,
            interactive=not non_interactive,
        )
        if cleanup_workspace and upload_results:
            for cdir in config.WORKSPACE_DIR.glob("clip_*"):
                if cdir.is_dir():
                    shutil.rmtree(cdir, ignore_errors=True)
            log_info("Cleaned temporary workspace clip render folders after successful upload.")

    # -------------------------------------------------------------------------
    # Pipeline Completion Summary
    # -------------------------------------------------------------------------
    total_elapsed = time.time() - start_total_time
    log_header("ALL VIDEO CLIPS GENERATED SUCCESSFULLY")
    print(f"[*] Total Execution Time: {total_elapsed:.1f}s ({total_elapsed / 60:.2f} mins)")
    print(f"[*] Production Plan:     {config.OUTPUT_DIR / 'production_plan.json'}")
    print(f"[*] Upload Pack & Tags:  {upload_pack_md}")
    print("[*] Generated Videos:")
    for clip_path in final_rendered_clips:
        size_mb = clip_path.stat().st_size / (1024 * 1024)
        print(f"    -> {clip_path.name} ({size_mb:.2f} MB): {clip_path}")
    if upload_results:
        print("[*] YouTube Uploads:")
        for ur in upload_results:
            saved_p = ur.get("archived_mp4_path") or "N/A"
            print(
                f"    -> Clip #{ur.get('clip_index')}: {ur.get('url')} | "
                f"status={ur.get('privacy_status')} | US={ur.get('publish_at_et') or 'N/A'} | "
                f"WIB={ur.get('publish_at_wib') or 'N/A'} | saved={saved_p}"
            )
    print("\nVideos are ready for YouTube Shorts!\n")


def run_upload_only(
    privacy_mode: str = config.YOUTUBE_UPLOAD_PRIVACY,
    us_slots: Optional[List[str]] = None,
    made_for_kids: bool = config.YOUTUBE_DEFAULT_MADE_FOR_KIDS,
    non_interactive: bool = False,
):
    """Upload already-rendered Shorts from `output/` using their `*_youtube_meta.json` metadata."""
    meta_files = sorted(config.OUTPUT_DIR.glob("clip_*_youtube_meta.json"))
    if not meta_files:
        raise FileNotFoundError(f"No clip_*_youtube_meta.json files found in {config.OUTPUT_DIR}")

    clip_pairs = []
    for mf in meta_files:
        meta = json.loads(mf.read_text(encoding="utf-8"))
        idx = int(meta.get("clip_index") or 1)
        mp4_path = config.OUTPUT_DIR / f"final_clip_{idx}.mp4"
        thumb_path = Path(meta.get("thumbnail_shorts_path") or (config.OUTPUT_DIR / f"clip_{idx}_thumbnail_shorts.jpg"))
        if mp4_path.exists():
            clip_pairs.append((mp4_path, meta, thumb_path if thumb_path.exists() else None))
    if not clip_pairs:
        raise FileNotFoundError(f"No rendered final_clip_*.mp4 files found in {config.OUTPUT_DIR}")

    uploader = YouTubeUploaderAgent()
    results = uploader.upload_output_batch(
        clip_pairs=clip_pairs,
        privacy_mode=privacy_mode,
        made_for_kids=made_for_kids,
        slots_et=us_slots,
        interactive=not non_interactive,
    )
    for ur in results:
        print(
            f"[UPLOAD] Clip #{ur.get('clip_index')}: {ur.get('url')} | "
            f"status={ur.get('privacy_status')} | US={ur.get('publish_at_et') or 'N/A'} | "
            f"WIB={ur.get('publish_at_wib') or 'N/A'}"
        )
    return results


def parse_args():
    parser = argparse.ArgumentParser(
        description="Clone trending YouTube Shorts into fresh 3D Shorts & auto-upload at US high-RPM prime hours."
    )
    parser.add_argument(
        "reference",
        nargs="?",
        default=None,
        help="YouTube Short URL or local .mp4 reference video path (leave empty for auto-scouting).",
    )
    parser.add_argument(
        "--niche",
        default=config.DEFAULT_NICHE,
        help="Target niche or topic category for the generated scripts.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=2,
        choices=[2, 3, 4],
        help="Number of unique vertical videos to produce (2 to 4). Default: 2.",
    )
    parser.add_argument(
        "--language",
        default=config.DEFAULT_LANGUAGE,
        help="Spoken language code (e.g. 'en' for English).",
    )
    parser.add_argument(
        "--voice",
        default=config.DEFAULT_VOICE,
        help="Edge-TTS voice (e.g. en-US-AnaNeural).",
    )
    parser.add_argument(
        "--rate",
        default=config.DEFAULT_VOICE_RATE,
        help="Voice rate modifier (e.g. +8%%, +12%%).",
    )
    parser.add_argument(
        "--auto-scout",
        action="store_true",
        help="Force auto-trend scouting even if local reference exists.",
    )
    parser.add_argument(
        "--auto-upload",
        action="store_true",
        help="Automatically upload generated Shorts to YouTube at upcoming US Prime Time slots.",
    )
    parser.add_argument(
        "--upload-only",
        action="store_true",
        help="Upload existing rendered clips in output/ without regenerating videos.",
    )
    parser.add_argument(
        "--auth-only",
        action="store_true",
        help="Run YouTube OAuth 2.0 consent once, save credentials/youtube_token.json, and verify channel.",
    )
    parser.add_argument(
        "--check-auth",
        action="store_true",
        help="Non-interactively verify live YouTube OAuth token health (exit 0=OK, 2=expired/re-auth required).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output for --check-auth.",
    )
    parser.add_argument(
        "--privacy",
        default=config.YOUTUBE_UPLOAD_PRIVACY,
        choices=["scheduled", "private", "unlisted", "public"],
        help="YouTube upload publish mode (default: scheduled for US Prime Time).",
    )
    parser.add_argument(
        "--us-slots",
        default=None,
        help="Comma-separated US Eastern HH:MM publish times (default: 08:00,12:30,16:30,20:00).",
    )
    parser.add_argument(
        "--made-for-kids",
        action="store_true",
        default=config.YOUTUBE_DEFAULT_MADE_FOR_KIDS,
        help="Mark uploads as Made For Kids (disabled by default to preserve RPM & comments).",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Never launch interactive browser auth (fail cleanly for scheduled cron runs if token expired).",
    )
    parser.add_argument(
        "--cleanup-workspace",
        action="store_true",
        help="Delete temporary workspace/clip_* render directories after successful auto-upload.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    slots_list = [s.strip() for s in args.us_slots.split(",") if s.strip()] if args.us_slots else None

    if args.check_auth:
        try:
            uploader = YouTubeUploaderAgent()
            status = uploader.check_auth_status()
            if args.json:
                print(json.dumps(status, ensure_ascii=False))
            else:
                state_tag = "NEEDS_AUTH" if status["needs_auth"] else "OK"
                print(f"[{state_tag}] ({status['reason']}) {status['message']}")
            sys.exit(2 if status["needs_auth"] else 0)
        except Exception as e:
            err_payload = {"ok": False, "needs_auth": True, "reason": "check_error", "message": str(e)}
            if args.json:
                print(json.dumps(err_payload, ensure_ascii=False))
            else:
                log_error(f"Auth status check failed: {e}")
            sys.exit(2)

    if args.auth_only:
        try:
            uploader = YouTubeUploaderAgent()
            ch = uploader.verify_channel(interactive=True, open_browser=True, timeout_seconds=None)
            print(f"[AUTH OK] Channel='{ch['title']}' ({ch['channel_id']}) | Country={ch['country']}")
            sys.exit(0)
        except Exception as e:
            log_error(f"YouTube OAuth failed: {e}")
            sys.exit(1)

    if args.upload_only:
        try:
            run_upload_only(
                privacy_mode=args.privacy,
                us_slots=slots_list,
                made_for_kids=args.made_for_kids,
                non_interactive=args.non_interactive,
            )
            sys.exit(0)
        except Exception as e:
            log_error(f"Upload failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    # Determine reference source
    if args.auto_scout or not args.reference:
        log_info(f"Auto-trend scouting top viral US Shorts for niche: '{args.niche}'...")
        ref_source = args.niche
    else:
        parts = [p.strip() for p in str(args.reference).split(",") if p.strip()]
        has_local_multi = parts and all(Path(p).exists() for p in parts)
        if not str(args.reference).startswith("http") and not has_local_multi:
            log_info(f"No local reference file found at '{args.reference}'. Auto-scouting niche: '{args.niche}'...")
            ref_source = args.niche
        else:
            ref_source = args.reference

    try:
        run_pipeline(
            reference_source=ref_source,
            target_niche=args.niche,
            clip_count=args.count,
            language=args.language,
            voice=args.voice,
            rate=args.rate,
            auto_upload=args.auto_upload,
            privacy_mode=args.privacy,
            us_slots=slots_list,
            made_for_kids=args.made_for_kids,
            non_interactive=args.non_interactive,
            cleanup_workspace=args.cleanup_workspace,
        )
    except Exception as e:
        log_error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
