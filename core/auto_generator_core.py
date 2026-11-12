"""
Core 4: Autonomous 3D GLB Animation Orchestrator (`core/auto_generator_core.py`).

Connects:
1. `CharacterCore` (Core 1 — dynamic 11-character cast mapped to 68+ rigged `.glb` characters & creatures)
2. `SceneCore` (Core 2 — 3D scene choreography, skeletal action mapping & 2-cut camera trajectories)
3. `BackgroundStoryCore` (Core 3 — world biome, 7-beat story arc & real `.glb` environment props)

Renders 100% ORIGINAL 3D animation from scratch via Three.js WebGL GPU (`assets/three/stage3d.html`)
using the 92 local `.glb` models in `assets/three/models/` — zero video editing/slicing from
the reference video.
"""

import http.server
import io
import json
import shutil
import subprocess
import tempfile
import threading
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

import config
from core.background_story_core import BackgroundStoryCore, BackgroundStorySpec
from core.character_core import CharacterCore, CharacterRoster
from core.expression_knowledge_core import ExpressionLearningCore
from core.meta_core_synthesizer import MetaCoreSynthesizer
from core.natural_motion_core import NaturalMotionCore
from core.physics_scene_validator import PhysicsSceneValidatorCore
from core.scene_core import SceneCore, SceneDirectingSpec
from schemas import Scene
from utils.logger import log_info, log_success, log_warning


def find_headless_browser() -> str:
    """Locate Google Chrome or Microsoft Edge on Windows for GPU WebGL 3D rendering."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    found = shutil.which("chrome") or shutil.which("msedge")
    if found:
        return found
    raise FileNotFoundError("Neither Google Chrome nor Microsoft Edge was found for Three.js WebGL rendering.")


def extract_audio_envelope(audio_path: Optional[Path], fps: int, total_frames: int) -> List[float]:
    """Extract smoothly gated, peak-normalized RMS voiceover envelope per frame for natural 60FPS lip-sync."""
    if not audio_path or not audio_path.exists():
        return [0.0] * total_frames
    try:
        cmd = [
            config.FFMPEG_BIN, "-v", "error",
            "-i", str(audio_path),
            "-ac", "1", "-ar", "8000",
            "-af", "highpass=f=180,lowpass=f=3400",
            "-f", "s16le", "pipe:1",
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=10, check=False)
        if res.returncode != 0 or not res.stdout:
            return [0.0] * total_frames
        samples = np.frombuffer(res.stdout, dtype=np.int16).astype(np.float32) / 32768.0
        if len(samples) < 100:
            return [0.0] * total_frames
        spf = max(1, int(8000 / fps))
        raw_rms = []
        for f in range(total_frames):
            chunk = samples[f * spf:(f + 1) * spf]
            rms = float(np.sqrt(np.mean(chunk * chunk))) if len(chunk) > 0 else 0.0
            raw_rms.append(rms)
        arr = np.array(raw_rms, dtype=np.float32)
        p95 = float(np.percentile(arr, 95)) if len(arr) > 0 else 0.15
        denom = max(0.06, p95)
        env: List[float] = []
        smooth_val = 0.0
        for r in raw_rms:
            norm = min(1.0, max(0.0, (r / denom - 0.10) / 0.90))
            alpha = 0.48 if norm > smooth_val else 0.30
            smooth_val = smooth_val + (norm - smooth_val) * alpha
            env.append(round(smooth_val, 3))
        return env
    except Exception:
        return [0.0] * total_frames


class AutoGeneratorCore:
    """
    Master autonomous orchestrator connecting:
    1. `CharacterCore` (Core 1 — 68+ rigged `.glb` characters, animals, dinosaurs & birds)
    2. `SceneCore` (Core 2 — multi-character 3D choreography & 2-cut dynamic camera work)
    3. `BackgroundStoryCore` (Core 3 — world biome & real `.glb` buildings, houses, trees, vehicles)
    To render 100% original 3D animation videos via Three.js WebGL.
    """

    def __init__(self):
        self.meta_synthesizer = MetaCoreSynthesizer()
        self.expression_core = ExpressionLearningCore()
        self.natural_motion_core = NaturalMotionCore()
        self.physics_validator = PhysicsSceneValidatorCore()
        self.story_core = BackgroundStoryCore()
        self.character_core = CharacterCore()
        self.scene_core = SceneCore()
        self._clip_cache: Dict[int, Tuple[BackgroundStorySpec, CharacterRoster]] = {}
        self.three_dir = config.BASE_DIR / "assets" / "three"
        self.browser_bin = find_headless_browser()

    def prepare_clip_cores(
        self,
        clip_index: int,
        script_title: str,
        hook_text: str,
        target_niche: str,
        scenes: List[Scene],
        viral_formula: str = "",
        cast_specs: Optional[List] = None,
        has_background_crowd: bool = False,
    ) -> Tuple[BackgroundStorySpec, CharacterRoster]:
        """
        Automatically synthesize any unseen Object/Expression/Motion cores first,
        then build Story/World + Character Roster + Physics AABB annotations.
        """
        if clip_index in self._clip_cache:
            return self._clip_cache[clip_index]

        # Autonomous Meta-Core synthesis BEFORE world construction (handles unseen objects/expressions/actions!)
        self.meta_synthesizer.ensure_objects_for_scenes(scenes)
        learned_exprs = self.expression_core.ensure_expressions_for_scenes(scenes)
        learned_motions = self.natural_motion_core.ensure_motions_for_scenes(scenes)

        narrations = [s.narration for s in scenes]
        prompts = [s.image_prompt for s in scenes]

        story_spec = self.story_core.generate_background_story(
            script_title=script_title,
            hook_text=hook_text,
            target_niche=target_niche,
            scene_narrations=narrations,
            viral_formula=viral_formula,
            clip_index=clip_index,
            scenes=scenes,
        )
        story_spec.expression_profiles = learned_exprs
        story_spec.motion_profiles = learned_motions
        self.physics_validator.annotate_prop_aabbs(story_spec)

        roster_spec = self.character_core.generate_roster(
            script_title=script_title,
            scene_narrations=narrations,
            scene_prompts=prompts,
            biome=story_spec.world_biome,
            clip_index=clip_index,
            min_characters=2,
            cast_specs=cast_specs,
            has_background_crowd=has_background_crowd,
        )

        clip_dir = config.WORKSPACE_DIR / f"clip_{clip_index:02d}"
        clip_dir.mkdir(parents=True, exist_ok=True)
        plan_path = clip_dir / "core_world_plan.json"
        plan_path.write_text(
            json.dumps(
                {
                    "background_story": story_spec.model_dump(),
                    "character_roster": roster_spec.model_dump(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        log_info(
            f"[AutoGeneratorCore] Clip #{clip_index}: Generated biome='{story_spec.world_biome}' "
            f"& {len(roster_spec.characters)} GLB character specs -> {plan_path.name}"
        )

        self._clip_cache[clip_index] = (story_spec, roster_spec)
        return story_spec, roster_spec

    def render_scene_threejs(
        self,
        scene: Scene,
        duration: float,
        scene_dir: Path,
        clip_index: int = 1,
        audio_path: Optional[Path] = None,
        story_spec: Optional[BackgroundStorySpec] = None,
        roster_spec: Optional[CharacterRoster] = None,
        scene_spec: Optional[SceneDirectingSpec] = None,
    ) -> Tuple[Path, Path, List[str]]:
        """
        Render a 100% original 30-FPS 3D Full HD (1080x1920) animation scene using Three.js WebGL GPU
        (`stage3d.html` + `cinema_gpu.js`) and our local `.glb` models in `assets/three/models/`.
        """
        scene_dir.mkdir(parents=True, exist_ok=True)
        num = scene.scene_number

        if story_spec is None or roster_spec is None:
            story_spec, roster_spec = self.prepare_clip_cores(
                clip_index=clip_index,
                script_title=f"Clip {clip_index}",
                hook_text=scene.narration,
                target_niche=config.DEFAULT_NICHE,
                scenes=[scene],
            )

        if scene_spec is None:
            scene_spec = self.scene_core.build_scene_directing(
                scene_number=num,
                duration=duration,
                narration=scene.narration,
                story=story_spec,
                roster=roster_spec,
                total_scenes=max(6, len(story_spec.beats)),
                scene_obj=scene,
            )
            self.physics_validator.validate_and_repair_clip([scene], story_spec, [scene_spec])

        fps = config.VIDEO_FPS
        total_frames = max(24, int(round(duration * fps)))
        audio_env = extract_audio_envelope(audio_path, fps=fps, total_frames=total_frames)

        payload_dict = {
            "story": story_spec.model_dump(),
            "roster": roster_spec.model_dump(),
            "sceneSpec": scene_spec.model_dump(),
            "objectKnowledge": getattr(story_spec, "object_knowledge", {}) or {},
            "expressionProfiles": getattr(story_spec, "expression_profiles", {}) or {},
            "motionProfiles": getattr(story_spec, "motion_profiles", {}) or {},
            "audioEnv": audio_env,
            "fps": fps,
            "width": config.VIDEO_WIDTH,
            "height": config.VIDEO_HEIGHT,
        }
        payload_bytes = json.dumps(payload_dict).encode("utf-8")

        output_mp4 = scene_dir / f"scene_{num:02d}_anim.mp4"
        thumb_jpg = scene_dir / f"scene_{num:02d}_shot1.jpg"

        encode_cmd = [
            config.FFMPEG_BIN, "-y", "-v", "error",
            "-f", "image2pipe",
            "-vcodec", "png",
            "-r", str(fps),
            "-i", "pipe:0",
            "-vf", f"scale={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT}:flags=lanczos:out_range=tv:out_color_matrix=bt709,format=yuv420p",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "6",
            "-g", "15",
            "-pix_fmt", "yuv420p",
            "-color_range", "tv",
            "-colorspace", "bt709",
            "-color_primaries", "bt709",
            "-color_trc", "bt709",
            "-profile:v", "high",
            "-movflags", "+faststart",
            "-an",
            str(output_mp4),
        ]

        state = {"frames": 0, "error": None, "thumb_saved": False}
        three_root = self.three_dir

        for attempt in range(3):
            enc_proc = subprocess.Popen(encode_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            done_event = threading.Event()
            state = {"frames": 0, "error": None, "thumb_saved": False}

            class ThreeRenderHandler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=str(three_root), **kwargs)

                def log_message(self, format, *args):
                    pass

                def do_GET(self):
                    parsed = urllib.parse.urlparse(self.path)
                    if parsed.path == "/payload.json":
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(payload_bytes)))
                        self.end_headers()
                        self.wfile.write(payload_bytes)
                        return
                    return super().do_GET()

                def do_POST(self):
                    parsed = urllib.parse.urlparse(self.path)
                    length = int(self.headers.get("Content-Length", "0"))
                    body = self.rfile.read(length) if length > 0 else b""

                    if parsed.path == "/frame":
                        if enc_proc.stdin:
                            try:
                                enc_proc.stdin.write(body)
                            except BrokenPipeError:
                                pass
                        state["frames"] += 1
                        if not state["thumb_saved"] and state["frames"] == max(1, int(total_frames * 0.56)):
                            try:
                                with Image.open(io.BytesIO(body)) as im:
                                    im.convert("RGB").save(thumb_jpg, "JPEG", quality=96)
                            except Exception:
                                thumb_jpg.write_bytes(body)
                            state["thumb_saved"] = True
                        self.send_response(200)
                        self.end_headers()
                        return

                    if parsed.path == "/done":
                        self.send_response(200)
                        self.end_headers()
                        done_event.set()
                        return

                    if parsed.path == "/error":
                        state["error"] = body.decode("utf-8", errors="replace")
                        self.send_response(200)
                        self.end_headers()
                        done_event.set()
                        return

                    self.send_response(404)
                    self.end_headers()

            httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), ThreeRenderHandler)
            port = httpd.server_address[1]
            server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            server_thread.start()

            stage_url = f"http://127.0.0.1:{port}/stage3d.html"
            browser_proc = None
            tmp_profile = tempfile.mkdtemp(prefix="three_glb_profile_")
            try:
                browser_cmd = [
                    self.browser_bin,
                    "--headless=new",
                    "--use-gl=angle",
                    "--use-angle=d3d11",
                    "--enable-webgl",
                    "--enable-gpu-rasterization",
                    "--ignore-gpu-blocklist",
                    "--disable-gpu-sandbox",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-background-timer-throttling",
                    "--disable-renderer-backgrounding",
                    f"--user-data-dir={tmp_profile}",
                    f"--window-size={config.VIDEO_WIDTH},{config.VIDEO_HEIGHT}",
                    stage_url,
                ]
                browser_proc = subprocess.Popen(
                    browser_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                done_event.wait(timeout=max(140.0, duration * 32.0))
            finally:
                if browser_proc and browser_proc.poll() is None:
                    try:
                        browser_proc.kill()
                        browser_proc.wait(timeout=5)
                    except Exception:
                        pass
                shutil.rmtree(tmp_profile, ignore_errors=True)
                httpd.shutdown()
                httpd.server_close()
                if enc_proc.stdin:
                    try:
                        enc_proc.stdin.close()
                    except Exception:
                        pass
                enc_proc.wait(timeout=15)

            if state["frames"] >= int(total_frames * 0.95):
                break
            log_warning(
                f"[AutoGeneratorCore] Scene #{num} attempt {attempt + 1} rendered {state['frames']}/{total_frames} frames; retrying..."
            )

        if state["error"]:
            log_warning(f"[AutoGeneratorCore] Scene #{num} WebGL error: {state['error']}")

        if not thumb_jpg.exists() and output_mp4.exists():
            subprocess.run(
                [
                    config.FFMPEG_BIN, "-y", "-v", "error",
                    "-ss", "0.4", "-i", str(output_mp4),
                    "-frames:v", "1", str(thumb_jpg),
                ],
                check=False,
            )

        lead_models = [c.glb_model for c in roster_spec.characters[:4]]
        log_success(
            f"[AutoGeneratorCore] Scene #{num} 100% 3D GLB rendered -> {output_mp4.name} "
            f"({state['frames']}/{total_frames} frames, biome={story_spec.world_biome}, "
            f"template={scene_spec.scene_template}, cast={lead_models})"
        )
        return output_mp4, thumb_jpg, [str(thumb_jpg)]
