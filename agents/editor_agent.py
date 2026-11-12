"""
GPU Video Editor Agent (Agent 6).
Renders vertical 9:16 Shorts (720x1280 @ 30fps) with:
1. Dynamic zoompan camera motion per scene (zoom_in_fast, zoom_in_slow, pan_right, pan_left, static)
2. Hardware accelerated video encoding (h264_nvenc with seamless libx264 fallback)
3. Lossless scene concatenation
4. Audio mixing: SFX cues triggered at scene cuts + ducked BGM (-18dB)
5. Burned-in word-level pop-up subtitles via FFmpeg libass filter
"""

import math
import os
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import config
from agents.media_agent import GeneratedSceneMedia, ScriptMediaBatch
from agents.subtitle_agent import escape_ass_path_for_ffmpeg
from utils.video_check import verify_video_file
from utils.logger import (
    log_info,
    log_success,
    log_warning,
    log_error,
)


def get_zoompan_filter(motion: str, duration: float, fps: int = config.VIDEO_FPS, width: int = config.VIDEO_WIDTH, height: int = config.VIDEO_HEIGHT) -> str:
    """
    Generate mathematically smooth zoompan filter expressions for vertical 9:16 video.
    """
    d_frames = max(30, int(round(duration * fps)))
    # Work on a 2x canvas so zoom/pan is smooth (zoompan on a small source jitters),
    # and force the exact 9:16 aspect so the image is never stretched.
    cw, ch = width * 2, height * 2
    prescale = (
        f"scale={cw}:{ch}:force_original_aspect_ratio=increase:out_range=tv,"
        f"crop={cw}:{ch},setsar=1,format=yuv420p,"
    )

    motion_lower = (motion or "zoom_in_slow").lower()
    if motion_lower == "zoom_in_fast":
        expr = f"z='min(zoom+0.0035,1.25)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    elif motion_lower == "pan_right":
        expr = f"z='1.12':x='(on/{d_frames})*(iw-iw/zoom)':y='ih/2-(ih/zoom/2)'"
    elif motion_lower == "pan_left":
        expr = f"z='1.12':x='(1-on/{d_frames})*(iw-iw/zoom)':y='ih/2-(ih/zoom/2)'"
    elif motion_lower == "static":
        expr = f"z='1.0':x='0':y='0'"
    else:  # zoom_in_slow default
        expr = f"z='min(zoom+0.0015,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"

    return f"{prescale}zoompan={expr}:d={d_frames}:s={width}x{height}:fps={fps},scale=out_range=tv,format=yuv420p"


# Encoder settings that every player (Windows Media Player / Films & TV, phones,
# browsers, YouTube) can decode: H.264 High profile@L4.2, 8-bit 4:2:0 BT.709 TV range, moov atom at front.
COMPAT_VIDEO_ARGS = [
    "-pix_fmt", "yuv420p",
    "-color_range", "tv",
    "-colorspace", "bt709",
    "-color_primaries", "bt709",
    "-color_trc", "bt709",
    "-profile:v", "high",
    "-level:v", "4.2",
    "-movflags", "+faststart",
]
COMPAT_AUDIO_ARGS = ["-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2"]


class GPUVideoEditorAgent:
    """Agent responsible for GPU rendering, camera motion, audio mixing, and subtitle burn-in."""

    def __init__(self):
        self.encoder = config.get_active_encoder()
        self._used_bgms: set = set()
        log_info(f"Initialized GPUVideoEditorAgent with preferred encoder: '{self.encoder}'")

    def render_scene_segment(
        self,
        image_path: Path,
        audio_path: Path,
        duration: float,
        camera_motion: str,
        output_path: Path,
        image_paths: Optional[List[Path]] = None,
        motions: Optional[List[str]] = None,
        video_clip_path: Optional[Path] = None,
    ) -> Path:
        """
        Render one scene into a 720x1280 30fps segment.
        - If `video_clip_path` is provided (moving 3D animation video), muxes the moving 3D animation
          with the narration audio (`audio_path`).
        - Otherwise renders still shots with zoompan camera motion.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fps = config.VIDEO_FPS

        encoders_to_try = [self.encoder]
        if config.FALLBACK_FFMPEG_CODEC not in encoders_to_try:
            encoders_to_try.append(config.FALLBACK_FFMPEG_CODEC)

        if video_clip_path and Path(video_clip_path).exists():
            last_error = None
            for enc in encoders_to_try:
                if enc == "h264_nvenc":
                    enc_args = ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "10", "-b:v", "16M", "-maxrate", "24M"]
                else:
                    # Near-lossless intermediate segment so final burn_subtitles master retains full clarity
                    enc_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "6", "-g", "15"]

                cmd = [
                    config.FFMPEG_BIN,
                    "-y",
                    "-i", str(video_clip_path),
                    "-i", str(audio_path),
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-t", f"{duration:.3f}",
                    *enc_args,
                    *COMPAT_VIDEO_ARGS,
                    "-r", str(fps),
                    *COMPAT_AUDIO_ARGS,
                    str(output_path),
                ]
                try:
                    subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=180)
                    if output_path.exists() and output_path.stat().st_size > 5000:
                        return output_path
                except subprocess.CalledProcessError as e:
                    last_error = e.stderr
                    log_warning(f"3D animation mux with {enc} failed: {e.stderr[-300:]}...")
            raise RuntimeError(f"Failed to render 3D animation scene segment {output_path.name}: {last_error}")

        shots = list(image_paths) if image_paths else [image_path]
        shot_motions = list(motions) if motions else [camera_motion]
        while len(shot_motions) < len(shots):
            shot_motions.append(camera_motion)

        total_frames = int(math.ceil(duration * fps)) + 2
        n = len(shots)
        base = total_frames // n
        frame_counts = [base] * n
        frame_counts[-1] += total_frames - base * n

        inputs: List[str] = []
        parts: List[str] = []
        for i, (shot, motion, frames) in enumerate(zip(shots, shot_motions, frame_counts)):
            inputs.extend(["-i", str(shot)])  # single still frame -> zoompan emits exactly `frames` frames
            zp = get_zoompan_filter(motion, frames / fps, fps=fps)
            parts.append(f"[{i}:v]{zp},setsar=1,trim=end_frame={frames},setpts=PTS-STARTPTS[v{i}]")
        concat_in = "".join(f"[v{i}]" for i in range(n))
        parts.append(f"{concat_in}concat=n={n}:v=1:a=0[vout]")
        filter_complex = ";".join(parts)
        audio_index = n

        encoders_to_try = [self.encoder]
        if config.FALLBACK_FFMPEG_CODEC not in encoders_to_try:
            encoders_to_try.append(config.FALLBACK_FFMPEG_CODEC)

        last_error = None
        for enc in encoders_to_try:
            if enc == "h264_nvenc":
                enc_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr", "-cq", "23", "-b:v", "4M", "-maxrate", "6M"]
            else:
                enc_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21"]

            cmd = [
                config.FFMPEG_BIN,
                "-y",
                *inputs,
                "-i", str(audio_path),
                "-filter_complex", filter_complex,
                "-map", "[vout]",
                "-map", f"{audio_index}:a",
                "-t", f"{duration:.3f}",
                *enc_args,
                *COMPAT_VIDEO_ARGS,
                "-r", str(fps),
                *COMPAT_AUDIO_ARGS,
                str(output_path),
            ]

            try:
                subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=180)
                if output_path.exists() and output_path.stat().st_size > 5000:
                    return output_path
            except subprocess.CalledProcessError as e:
                last_error = e.stderr
                log_warning(f"Encoding with {enc} failed: {e.stderr[-300:]}... Retrying with fallback...")

        raise RuntimeError(f"Failed to render scene segment {output_path.name}: {last_error}")

    def concatenate_segments(self, segment_paths: List[Path], output_path: Path) -> Path:
        """Concatenate all scene MP4 segments into a full video without re-encoding."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        concat_txt = output_path.parent / "scenes_concat.txt"

        with open(concat_txt, "w", encoding="utf-8") as f:
            for seg in segment_paths:
                resolved = str(seg.resolve()).replace("\\", "/")
                f.write(f"file '{resolved}'\n")

        cmd = [
            config.FFMPEG_BIN,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            str(output_path),
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=60)
            concat_txt.unlink(missing_ok=True)
            log_success(f"Concatenated {len(segment_paths)} scenes -> {output_path.name}")
            return output_path
        except subprocess.CalledProcessError as e:
            log_error(f"Concatenation failed: {e.stderr}")
            raise

    def mix_audio_and_sfx(
        self,
        video_path: Path,
        scenes: List[GeneratedSceneMedia],
        output_path: Path,
        clip_title: str = "",
        clip_index: int = 1,
    ) -> Path:
        """
        Layer sound effects at scene transition points and mix mood-matched varied BGM
        (strictly avoiding repeating the same backsound track across clips in a batch).
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Collect SFX cues with exact start timestamps
        sfx_inputs = []
        current_time_ms = 0

        for idx, sc in enumerate(scenes):
            if sc.sfx_cue and sc.sfx_cue != "none":
                sfx_candidate = config.SFX_DIR / f"{sc.sfx_cue}.wav"
                if sfx_candidate.exists():
                    sfx_inputs.append((str(sfx_candidate.resolve()), current_time_ms))
            current_time_ms += int(round(sc.audio_duration * 1000))

        # Check BGM and ensure every clip gets a mood-matched, non-repeated track
        bgm_files = sorted(list(config.BGM_DIR.glob("*.mp3")) + list(config.BGM_DIR.glob("*.wav")))
        selected_bgm = None
        if bgm_files:
            unused = [f for f in bgm_files if f.name not in self._used_bgms]
            pool = unused if unused else bgm_files
            if not unused:
                self._used_bgms.clear()

            mood_blob = f"{clip_title} " + " ".join(getattr(s, "narration", "") or "" for s in scenes)
            mlow = mood_blob.lower()
            prefer_names: List[str] = []
            if any(w in mlow for w in ("maze", "laser", "shield", "power", "race", "hero", "fight", "level", "game")):
                prefer_names = ["arcade_hero_quest.wav", "comedy_chaotic_chase.wav"]
            elif any(w in mlow for w in ("prank", "sneak", "secret", "trap", "cockroach", "bug", "trick", "caught", "hide")):
                prefer_names = ["sneaky_pizzicato_mystery.wav", "comedy_chaotic_chase.wav"]
            elif any(w in mlow for w in ("magic", "portal", "wish", "dream", "star", "surprise", "wonder")):
                prefer_names = ["magical_wonder_bells.wav", "cozy_ukulele_sunshine.wav"]
            elif any(w in mlow for w in ("friend", "dog", "cat", "puppy", "forest", "home", "village", "kind")):
                prefer_names = ["cozy_ukulele_sunshine.wav", "kids_upbeat_marimba.wav"]

            by_name = {f.name: f for f in pool}
            for pname in prefer_names:
                if pname in by_name:
                    selected_bgm = by_name[pname]
                    break
            if selected_bgm is None:
                selected_bgm = pool[(max(0, clip_index - 1)) % len(pool)]
            self._used_bgms.add(selected_bgm.name)

        # If no SFX and no BGM, simply copy
        if not sfx_inputs and not selected_bgm:
            log_info("No BGM or SFX found to mix. Keeping master voiceover intact.")
            import shutil
            shutil.copy2(video_path, output_path)
            return output_path

        log_info(
            f"Mixing audio: {len(sfx_inputs)} SFX transitions + "
            f"BGM: {selected_bgm.name if selected_bgm else 'None'}"
        )

        # Build FFmpeg complex filter command
        inputs = ["-i", str(video_path)]
        filter_complex_parts = [
            "[0:a]acompressor=threshold=-18dB:ratio=2.8:attack=5:release=80,volume=1.45[vo]"
        ]
        mix_inputs = ["[vo]"]

        # Add SFX inputs
        input_idx = 1
        for sfx_file, delay_ms in sfx_inputs:
            inputs.extend(["-i", sfx_file])
            filter_complex_parts.append(
                f"[{input_idx}:a]adelay={delay_ms}|{delay_ms},volume=0.72[sfx{input_idx}]"
            )
            mix_inputs.append(f"[sfx{input_idx}]")
            input_idx += 1

        # Add BGM input if available
        if selected_bgm:
            inputs.extend(["-stream_loop", "-1", "-i", str(selected_bgm)])
            filter_complex_parts.append(f"[{input_idx}:a]volume=0.16[bgm]")
            mix_inputs.append("[bgm]")
            input_idx += 1

        # Combine all audio streams WITHOUT normalize=1 (which divides voiceover by N inputs!),
        # then master to broadcast Shorts loudness (-13 LUFS) with a clean brickwall limiter.
        filter_complex_parts.append(
            f"{''.join(mix_inputs)}amix=inputs={len(mix_inputs)}:duration=first:dropout_transition=2:normalize=0[amixed];"
            f"[amixed]loudnorm=I=-13:TP=-1.2:LRA=8,alimiter=limit=0.95[aout]"
        )

        filter_str = ";".join(filter_complex_parts)
        cmd = [
            config.FFMPEG_BIN,
            "-y",
            *inputs,
            "-filter_complex", filter_str,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_path),
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=90)
            log_success(f"Audio mixing completed successfully -> {output_path.name}")
            return output_path
        except subprocess.CalledProcessError as e:
            log_warning(f"Audio mixing failed ({e}). Falling back to unmixed video.")
            import shutil
            shutil.copy2(video_path, output_path)
            return output_path

    def burn_subtitles(
        self,
        video_path: Path,
        ass_path: Path,
        output_path: Path,
    ) -> Path:
        """
        Burn in word-level pop-up .ass subtitles using FFmpeg libass filter.
        Encodes to final vertical video destination with hardware acceleration.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        escaped_ass = escape_ass_path_for_ffmpeg(ass_path)
        log_info(f"Burning subtitles onto video using libass: {ass_path.name}")

        encoders_to_try = [self.encoder]
        if config.FALLBACK_FFMPEG_CODEC not in encoders_to_try:
            encoders_to_try.append(config.FALLBACK_FFMPEG_CODEC)

        last_error = None
        for enc in encoders_to_try:
            if enc == "h264_nvenc":
                enc_args = ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "15", "-b:v", "12M", "-maxrate", "18M", "-bufsize", "24M"]
            else:
                enc_args = [
                    "-c:v", "libx264", "-preset", "slow", "-crf", "14",
                    "-aq-mode", "3", "-bf", "2", "-g", str(config.VIDEO_FPS),
                ]

            cmd = [
                config.FFMPEG_BIN,
                "-y",
                "-i", str(video_path),
                "-vf", f"ass='{escaped_ass}',scale=out_range=tv:out_color_matrix=bt709:flags=lanczos,format=yuv420p",
                *enc_args,
                *COMPAT_VIDEO_ARGS,
                *COMPAT_AUDIO_ARGS,
                str(output_path),
            ]

            try:
                subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=120)
                if output_path.exists() and output_path.stat().st_size > 5000:
                    log_success(f"Subtitles burned in successfully -> {output_path.name} ({output_path.stat().st_size / (1024 * 1024):.2f} MB)")
                    return output_path
            except subprocess.CalledProcessError as e:
                last_error = e.stderr
                log_warning(f"Subtitle burn-in with {enc} failed. Retrying with fallback...")

        raise RuntimeError(f"Subtitle burn-in failed: {last_error}")

    def render_complete_clip(
        self,
        media_batch: ScriptMediaBatch,
        ass_subtitle_path: Path,
        output_final_mp4: Path,
    ) -> Path:
        """
        Complete rendering pipeline for a single vertical video clip:
        1. Render individual scene segments (image + audio + zoompan)
        2. Concatenate scene segments
        3. Mix SFX cues and background music
        4. Burn in ASS word-level highlighted captions
        """
        clip_dir = config.WORKSPACE_DIR / f"clip_{media_batch.clip_index:02d}"
        clip_dir.mkdir(parents=True, exist_ok=True)

        log_info(f"Starting complete render pipeline for Clip #{media_batch.clip_index} (\"{media_batch.title}\")")

        # 1. Render scenes in parallel for maximum throughput
        def _mux_seg(scene):
            seg_out = clip_dir / f"segment_{scene.scene_number:02d}.mp4"
            log_info(
                f"Rendering Scene {scene.scene_number:02d} "
                f"({scene.audio_duration:.2f}s, motion: {scene.camera_motion})..."
            )
            return self.render_scene_segment(
                image_path=scene.image_path,
                audio_path=scene.audio_path,
                duration=scene.audio_duration,
                camera_motion=scene.camera_motion,
                output_path=seg_out,
                image_paths=getattr(scene, "image_paths", None) or None,
                motions=getattr(scene, "shot_motions", None) or None,
                video_clip_path=getattr(scene, "video_clip_path", None) or None,
            )

        max_workers = max(1, min(getattr(config, "RENDER_WORKERS", 3), len(media_batch.scenes)))
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            segment_paths = list(pool.map(_mux_seg, media_batch.scenes))

        # 2. Concatenate
        raw_concat_video = clip_dir / "raw_concatenated.mp4"
        self.concatenate_segments(segment_paths, raw_concat_video)

        # 3. Audio Mixing (SFX + Varied Mood-Matched BGM)
        audio_mixed_video = clip_dir / "audio_mixed.mp4"
        self.mix_audio_and_sfx(
            raw_concat_video,
            media_batch.scenes,
            audio_mixed_video,
            clip_title=media_batch.title,
            clip_index=media_batch.clip_index,
        )

        # 4. Burn subtitles into final output
        self.burn_subtitles(audio_mixed_video, ass_subtitle_path, output_final_mp4)

        # 5. Hard verification: never report success on a file without a visible picture
        ok, report, _ = verify_video_file(output_final_mp4, require_audio=True)
        if not ok:
            raise RuntimeError(f"Final clip failed verification: {report}")
        log_success(f"Verified: {report}")

        log_success(f"FINAL CLIP #{media_batch.clip_index} READY: {output_final_mp4}")
        return output_final_mp4
