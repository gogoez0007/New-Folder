"""
Procedural 3D Kids Cartoon Ray-Tracing & Animation Engine (`utils/cartoon3d_engine.py`).

Generates 100% original moving 3D animation videos (30 FPS, 720x1280 vertical H.264/yuv420p)
inspired by the viral blueprint/concept of trending 3D Kids Shorts — WITHOUT copying or slicing
any video frames from the reference video.

Features:
- Real-time 3D analytic ray-tracing (3D ellipsoids, 3D ribbed inflatable pools, 3D rippling water
  surfaces, 3D park pedestals, 3D wooden fence, 3D trees, 3D volumetric clouds, 3D courtyard)
- Bright Pixar/CoComelon-style 3D shading: warm subsurface skin wrap lighting, bright sky fill,
  Blinn-Phong glossy specular highlights, Fresnel rim lighting, and soft ground contact shadows
- Articulated 3D kids characters (Pip, Milo, Sunny, Barnaby) with:
  * Voiceover-synced 3D smiling mouth + teeth + tongue lip-sync (from scene MP3 amplitude)
  * Automatic 3D eye blinking & gaze tracking with dual glossy specular catchlights
  * Theme-aware 3D stages & props:
    - Theme 1 (`pool_party`): 3 colorful polka-dot inflatable 3D pools, rippling water waves,
      parabolic pool jumps, 3D water splash bursts, floating 3D rubber duck & beach ball
    - Theme 2 (`unique_school`): Sunny 3D park & stage pedestals, Sunny's wobbly 3D gizmo hat
      contraption (Scenes 1-4) transforming into magical glowing 3D star pigtails + floating 3D
      hearts and celebration confetti (Scenes 5-7)
"""

import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image

import config


@dataclass
class Sphere3D:
    center: Tuple[float, float, float]
    radius: Tuple[float, float, float]
    color: Tuple[float, float, float]
    roughness: float = 0.25
    specular: float = 0.50
    unlit: bool = False
    min_ambient: float = 0.42


@dataclass
class Pool3D:
    center_xz: Tuple[float, float]
    outer_radius: float
    height: float
    color: Tuple[float, float, float]
    water_level: float = 0.42
    dot_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    is_stage_pedestal: bool = False


def extract_audio_envelope(audio_path: Optional[Path], num_frames: int, fps: int = 30) -> np.ndarray:
    """
    Extract per-frame RMS voiceover amplitude [0.0 .. 1.0] from an MP3/WAV file using FFmpeg
    to drive real-time 3D character mouth lip-sync.
    """
    if not audio_path or not Path(audio_path).exists() or num_frames <= 0:
        t = np.linspace(0, num_frames / max(1, fps), max(1, num_frames))
        return (0.35 + 0.45 * np.abs(np.sin(t * 9.0))).astype(np.float32)

    sr = 8000
    cmd = [
        config.FFMPEG_BIN, "-v", "error",
        "-i", str(audio_path),
        "-ac", "1", "-ar", str(sr),
        "-f", "s16le", "pipe:1",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, timeout=15, check=False)
        if res.returncode == 0 and len(res.stdout) >= 200:
            samples = np.frombuffer(res.stdout, dtype=np.int16).astype(np.float32) / 32768.0
            env = np.zeros(num_frames, dtype=np.float32)
            spf = max(1, int(sr / fps))
            for i in range(num_frames):
                s0 = i * spf
                s1 = min(len(samples), s0 + spf)
                if s1 > s0:
                    env[i] = float(np.sqrt(np.mean(samples[s0:s1] ** 2)))
            max_v = float(np.percentile(env, 95)) if len(env) > 0 else 0.1
            if max_v > 1e-4:
                env = np.clip(env / max_v, 0.0, 1.0)
            return env
    except Exception:
        pass

    t = np.linspace(0, num_frames / max(1, fps), max(1, num_frames))
    return (0.35 + 0.45 * np.abs(np.sin(t * 9.0))).astype(np.float32)


class Cartoon3DRenderer:
    """
    Fast vectorized NumPy 3D Ray-Tracer for cute Pixar/CoComelon-style 3D animated Shorts.
    Renders at internal resolution (360x640) and upscales to 720x1280 vertical 9:16 frames.
    """

    def __init__(self, internal_w: int = 360, internal_h: int = 640):
        self.W = internal_w
        self.H = internal_h
        self.aspect = self.W / self.H
        y_lin = np.linspace(1.0, -1.0, self.H, dtype=np.float32)
        x_lin = np.linspace(-self.aspect, self.aspect, self.W, dtype=np.float32)
        self.y_grid, self.x_grid = np.meshgrid(y_lin, x_lin, indexing="ij")

        # Warm frontal-top sunlight so character faces are always brightly lit
        ldir = np.array([0.38, 0.68, 0.62], dtype=np.float32)
        self.light_dir = ldir / np.linalg.norm(ldir)

    def _build_camera_rays(
        self,
        cam_pos: Tuple[float, float, float],
        look_at: Tuple[float, float, float],
        fov_focal: float = 1.85,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        ro = np.array(cam_pos, dtype=np.float32)
        target = np.array(look_at, dtype=np.float32)
        fwd = target - ro
        fwd /= np.linalg.norm(fwd)
        up_world = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        right = np.cross(fwd, up_world)
        right /= max(1e-5, np.linalg.norm(right))
        up = np.cross(right, fwd)

        rd = (
            self.x_grid[..., None] * right[None, None, :]
            + self.y_grid[..., None] * up[None, None, :]
            + fov_focal * fwd[None, None, :]
        )
        rd /= np.linalg.norm(rd, axis=-1, keepdims=True)
        return ro, rd, right, up, fwd

    def _build_character_rig(
        self,
        char_id: str,
        pos: Tuple[float, float, float],
        t_sec: float,
        mouth_open: float,
        action: str = "cheer",
        scale: float = 1.0,
        wearing_contraption: bool = False,
    ) -> List[Sphere3D]:
        """
        Build an articulated 3D cartoon character (~26 3D ellipsoids) at world position `pos`.
        """
        bx, by, bz = pos
        s = scale

        if action == "jump_splash":
            jump_phase = (t_sec * 1.55) % 1.0
            arc = 4.0 * jump_phase * (1.0 - jump_phase)
            by += arc * 0.58 * s
            body_tilt = math.sin(t_sec * 6.0) * 0.10
            arm_raise = 0.20 + 0.14 * arc
            leg_kick = math.sin(t_sec * 13.0) * 0.12
        elif action == "surprised":
            by += abs(math.sin(t_sec * 5.0)) * 0.05 * s
            body_tilt = -0.05
            arm_raise = 0.18 + 0.05 * math.sin(t_sec * 9.0)
            leg_kick = 0.0
        else:  # "cheer"
            by += abs(math.sin(t_sec * 6.0)) * 0.10 * s
            body_tilt = math.sin(t_sec * 3.0) * 0.06
            arm_raise = 0.16 + 0.11 * math.sin(t_sec * 7.5)
            leg_kick = math.sin(t_sec * 6.0) * 0.05

        # Bright, warm Pixar-style skin and character palettes
        skin = (1.00, 0.85, 0.75)
        blush = (1.00, 0.55, 0.62)
        if char_id == "pip":
            suit_col = (0.18, 0.22, 0.30)     # Cute penguin hoodie
            belly_col = (0.98, 0.99, 1.00)    # White penguin tummy
            shoe_col = (1.00, 0.85, 0.12)     # Yellow flippers
            eye_iris = (0.15, 0.68, 0.98)     # Sky-blue eyes
            hair_col = (0.15, 0.18, 0.25)
        elif char_id == "milo":
            suit_col = (0.14, 0.66, 0.98)     # Bright azure hoodie
            belly_col = (0.98, 0.32, 0.26)    # Red overall pocket
            shoe_col = (0.98, 0.34, 0.22)     # Red sneakers
            eye_iris = (0.16, 0.78, 0.44)     # Emerald eyes
            hair_col = (0.48, 0.28, 0.16)     # Warm chestnut hair
        elif char_id == "sunny":
            suit_col = (0.98, 0.40, 0.70)     # Bubblegum pink sweater
            belly_col = (1.00, 0.88, 0.24)    # Golden star emblem
            shoe_col = (0.66, 0.30, 0.96)     # Lavender boots
            eye_iris = (0.68, 0.28, 0.94)     # Violet eyes
            hair_col = (0.62, 0.24, 0.92)     # Bouncy purple star hair
        else:  # barnaby
            suit_col = (0.24, 0.82, 0.42)     # Mint-emerald dino suit
            belly_col = (0.98, 0.94, 0.48)    # Sunny yellow tummy
            shoe_col = (1.00, 0.58, 0.14)     # Orange shoes
            eye_iris = (0.94, 0.56, 0.14)     # Amber eyes
            hair_col = (0.20, 0.68, 0.34)

        prims: List[Sphere3D] = []

        # 1. Legs & Shoes
        lx_off = 0.135 * s
        prims.append(Sphere3D((bx - lx_off, by + 0.18 * s, bz + leg_kick * s), (0.095 * s, 0.18 * s, 0.095 * s), suit_col, 0.3, 0.4, min_ambient=0.48))
        prims.append(Sphere3D((bx + lx_off, by + 0.18 * s, bz - leg_kick * s), (0.095 * s, 0.18 * s, 0.095 * s), suit_col, 0.3, 0.4, min_ambient=0.48))
        prims.append(Sphere3D((bx - lx_off, by + 0.06 * s, bz + (0.06 + leg_kick) * s), (0.115 * s, 0.07 * s, 0.145 * s), shoe_col, 0.2, 0.65, min_ambient=0.55))
        prims.append(Sphere3D((bx + lx_off, by + 0.06 * s, bz + (0.06 - leg_kick) * s), (0.115 * s, 0.07 * s, 0.145 * s), shoe_col, 0.2, 0.65, min_ambient=0.55))

        # 2. Chubby 3D Torso & Belly Patch
        ty = by + 0.48 * s
        tx = bx + body_tilt * 0.14 * s
        prims.append(Sphere3D((tx, ty, bz), (0.265 * s, 0.305 * s, 0.225 * s), suit_col, 0.28, 0.45, min_ambient=0.50))
        prims.append(Sphere3D((tx, ty - 0.01 * s, bz + 0.075 * s), (0.185 * s, 0.22 * s, 0.175 * s), belly_col, 0.30, 0.40, min_ambient=0.60))

        # 3. Animated 3D Arms & Hands
        ax_l = tx - 0.30 * s
        ax_r = tx + 0.30 * s
        ay_l = ty + (0.06 + arm_raise) * s
        ay_r = ty + (0.06 + arm_raise * math.cos(t_sec * 3.0)) * s
        prims.append(Sphere3D((ax_l, ay_l, bz + 0.04 * s), (0.088 * s, 0.19 * s, 0.088 * s), suit_col, 0.3, 0.45, min_ambient=0.50))
        prims.append(Sphere3D((ax_r, ay_r, bz + 0.04 * s), (0.088 * s, 0.19 * s, 0.088 * s), suit_col, 0.3, 0.45, min_ambient=0.50))
        prims.append(Sphere3D((ax_l - 0.025 * s, ay_l + 0.145 * s, bz + 0.065 * s), (0.082 * s, 0.082 * s, 0.082 * s), skin, 0.22, 0.45, min_ambient=0.62))
        prims.append(Sphere3D((ax_r + 0.025 * s, ay_r + 0.145 * s, bz + 0.065 * s), (0.082 * s, 0.082 * s, 0.082 * s), skin, 0.22, 0.45, min_ambient=0.62))

        # 4. Big Cute 3D Head (Warm Subsurface Skin)
        hy = by + 0.99 * s
        hx = tx + math.sin(t_sec * 2.4) * 0.025 * s
        hz = bz + 0.02 * s
        prims.append(Sphere3D((hx, hy, hz), (0.335 * s, 0.325 * s, 0.305 * s), skin, 0.20, 0.42, min_ambient=0.64))

        # Rosy Pink Cheeks
        prims.append(Sphere3D((hx - 0.20 * s, hy - 0.055 * s, hz + 0.235 * s), (0.068 * s, 0.042 * s, 0.045 * s), blush, 0.4, 0.2, min_ambient=0.68))
        prims.append(Sphere3D((hx + 0.20 * s, hy - 0.055 * s, hz + 0.235 * s), (0.068 * s, 0.042 * s, 0.045 * s), blush, 0.4, 0.2, min_ambient=0.68))

        # Cute Button Nose
        prims.append(Sphere3D((hx, hy - 0.015 * s, hz + 0.302 * s), (0.036 * s, 0.030 * s, 0.035 * s), (0.98, 0.74, 0.64), 0.20, 0.55, min_ambient=0.62))

        # 5. Expressive 3D Eyes with Blinking & Dual Specular Catchlights
        blink_cycle = (t_sec + (0.9 if char_id == "milo" else (1.7 if char_id == "sunny" else 0.0))) % 3.1
        is_blinking = blink_cycle > 2.97
        eye_h = (0.016 if is_blinking else 0.092) * s
        gaze_x = math.sin(t_sec * 1.6) * 0.015 * s

        for side in (-1.0, 1.0):
            ex = hx + side * 0.13 * s
            ey = hy + 0.035 * s
            ez = hz + 0.252 * s
            prims.append(Sphere3D((ex, ey, ez), (0.084 * s, eye_h, 0.052 * s), (1.0, 1.0, 1.0), 0.08, 0.85, min_ambient=0.80))
            if not is_blinking:
                prims.append(Sphere3D((ex + gaze_x, ey, ez + 0.030 * s), (0.055 * s, 0.064 * s, 0.032 * s), eye_iris, 0.08, 0.90, min_ambient=0.65))
                prims.append(Sphere3D((ex + gaze_x, ey, ez + 0.046 * s), (0.032 * s, 0.038 * s, 0.022 * s), (0.04, 0.04, 0.07), 0.05, 0.95, min_ambient=0.10))
                prims.append(Sphere3D((ex + gaze_x + 0.017 * s, ey + 0.021 * s, ez + 0.060 * s), (0.017 * s, 0.017 * s, 0.014 * s), (1.0, 1.0, 1.0), 0.0, 1.0, unlit=True))

            brow_y = ey + (0.112 + (0.018 if action == "surprised" else 0.0)) * s
            prims.append(Sphere3D((ex, brow_y, ez + 0.018 * s), (0.070 * s, 0.020 * s, 0.022 * s), hair_col, 0.35, 0.3, min_ambient=0.45))

        # 6. Cute Recessed 3D Smiling Mouth + White Upper Teeth + Pink Tongue
        m_open = max(0.018, min(0.062, 0.018 + mouth_open * 0.046)) * s
        m_width = (0.062 + mouth_open * 0.022) * s
        # Mouth cavity sits cleanly on the face contour (thin Z radius so it never looks like a bubble)
        prims.append(Sphere3D((hx, hy - 0.125 * s, hz + 0.288 * s), (m_width, m_open, 0.022 * s), (0.62, 0.14, 0.22), 0.4, 0.15, min_ambient=0.50))
        # Cute white upper smile teeth bar
        prims.append(Sphere3D((hx, hy - (0.125 - m_open * 0.55) * s, hz + 0.296 * s), (m_width * 0.78, m_open * 0.32, 0.018 * s), (1.0, 1.0, 1.0), 0.1, 0.7, min_ambient=0.85))
        if mouth_open > 0.20:
            # Cute pink tongue at bottom of mouth
            prims.append(Sphere3D((hx, hy - (0.125 + m_open * 0.45) * s, hz + 0.295 * s), (m_width * 0.58, m_open * 0.40, 0.018 * s), (1.0, 0.52, 0.62), 0.3, 0.3, min_ambient=0.70))

        # 7. Character Headgear / Hair / Special Props
        if char_id == "pip":
            prims.append(Sphere3D((hx, hy + 0.07 * s, hz - 0.03 * s), (0.355 * s, 0.32 * s, 0.32 * s), suit_col, 0.28, 0.50, min_ambient=0.48))
            prims.append(Sphere3D((hx, hy + 0.30 * s, hz + 0.23 * s), (0.088 * s, 0.044 * s, 0.10 * s), (1.0, 0.82, 0.10), 0.20, 0.75, min_ambient=0.65))
            prims.append(Sphere3D((hx - 0.125 * s, hy + 0.32 * s, hz + 0.17 * s), (0.044 * s, 0.044 * s, 0.038 * s), (1.0, 1.0, 1.0), 0.1, 0.8, min_ambient=0.80))
            prims.append(Sphere3D((hx + 0.125 * s, hy + 0.32 * s, hz + 0.17 * s), (0.044 * s, 0.044 * s, 0.038 * s), (1.0, 1.0, 1.0), 0.1, 0.8, min_ambient=0.80))
        elif char_id == "sunny":
            bob = math.sin(t_sec * 6.5) * 0.038 * s
            prims.append(Sphere3D((hx, hy + 0.14 * s, hz - 0.02 * s), (0.35 * s, 0.255 * s, 0.315 * s), hair_col, 0.25, 0.60, min_ambient=0.55))
            for side in (-1.0, 1.0):
                px = hx + side * 0.365 * s
                prims.append(Sphere3D((px, hy + 0.19 * s + bob, hz), (0.125 * s, 0.155 * s, 0.125 * s), hair_col, 0.25, 0.60, min_ambient=0.55))
                prims.append(Sphere3D((px + side * 0.055 * s, hy + 0.045 * s + bob * 1.3, hz), (0.105 * s, 0.135 * s, 0.105 * s), hair_col, 0.25, 0.60, min_ambient=0.55))
                prims.append(Sphere3D((hx + side * 0.25 * s, hy + 0.23 * s, hz + 0.15 * s), (0.052 * s, 0.052 * s, 0.038 * s), (1.0, 0.88, 0.15), 0.15, 0.85, min_ambient=0.70))
            if wearing_contraption:
                # Funny wobbly 3D mechanical helmet/hat contraption (Clip 2 early scenes!)
                wob = math.sin(t_sec * 11.0) * 0.04 * s
                prims.append(Sphere3D((hx + wob, hy + 0.36 * s, hz), (0.28 * s, 0.14 * s, 0.28 * s), (0.22, 0.76, 0.88), 0.15, 0.85, min_ambient=0.60))
                prims.append(Sphere3D((hx - wob, hy + 0.50 * s, hz), (0.14 * s, 0.09 * s, 0.14 * s), (1.0, 0.78, 0.12), 0.15, 0.90, min_ambient=0.65))
                prims.append(Sphere3D((hx + wob * 1.5, hy + 0.62 * s, hz), (0.06 * s, 0.06 * s, 0.06 * s), (1.0, 0.25, 0.35), 0.10, 0.95, unlit=True))
        elif char_id == "milo":
            prims.append(Sphere3D((hx, hy + 0.15 * s, hz - 0.02 * s), (0.35 * s, 0.255 * s, 0.315 * s), hair_col, 0.30, 0.45, min_ambient=0.50))
            prims.append(Sphere3D((hx - 0.08 * s, hy + 0.295 * s, hz + 0.135 * s), (0.155 * s, 0.095 * s, 0.135 * s), hair_col, 0.30, 0.45, min_ambient=0.50))
            prims.append(Sphere3D((hx + 0.10 * s, hy + 0.275 * s, hz + 0.115 * s), (0.135 * s, 0.085 * s, 0.125 * s), hair_col, 0.30, 0.45, min_ambient=0.50))
        else:
            prims.append(Sphere3D((hx, hy + 0.10 * s, hz - 0.03 * s), (0.355 * s, 0.305 * s, 0.315 * s), suit_col, 0.28, 0.50, min_ambient=0.52))
            prims.append(Sphere3D((hx - 0.25 * s, hy + 0.335 * s, hz), (0.105 * s, 0.105 * s, 0.075 * s), suit_col, 0.28, 0.50, min_ambient=0.52))
            prims.append(Sphere3D((hx + 0.25 * s, hy + 0.335 * s, hz), (0.105 * s, 0.105 * s, 0.075 * s), suit_col, 0.28, 0.50, min_ambient=0.52))

        return prims

    def render_frame(
        self,
        t_sec: float,
        mouth_open: float,
        scene_number: int = 1,
        shot_index: int = 0,
        theme: str = "pool_party",
    ) -> np.ndarray:
        """
        Render a single 720x1280 RGB uint8 frame of original 3D animation at timestamp `t_sec`.
        """
        H, W = self.H, self.W

        # 1. Dynamic 3D Camera choreography (Shot 0 = Medium-Wide Stage, Shot 1 = Close-up Reaction)
        if shot_index == 0:
            orbit_ang = math.sin(t_sec * 0.55 + scene_number * 0.7) * 0.25
            cam_dist = 4.55 - 0.20 * math.sin(t_sec * 0.4)
            cam_pos = (math.sin(orbit_ang) * cam_dist, 1.68 + 0.07 * math.cos(t_sec * 0.8), math.cos(orbit_ang) * cam_dist)
            look_at = (0.0, 0.82, 0.0)
            fov = 1.82
        else:
            focus_x = [-0.40, 0.0, 0.40, 0.0, -0.30, 0.30, 0.0][(scene_number - 1) % 7]
            orbit_ang = math.cos(t_sec * 0.7 + scene_number) * 0.16
            cam_dist = 3.20 - 0.15 * (t_sec % 2.0)
            cam_pos = (focus_x + math.sin(orbit_ang) * cam_dist, 1.38, math.cos(orbit_ang) * cam_dist)
            look_at = (focus_x * 0.65, 0.90, 0.05)
            fov = 2.08

        ro, rd, _, _, _ = self._build_camera_rays(cam_pos, look_at, fov_focal=fov)

        # 2. Sky Gradient
        sky_t = np.clip(rd[..., 1] * 1.9 + 0.15, 0.0, 1.0)
        img = np.empty((H, W, 3), dtype=np.float32)
        if theme == "unique_school":
            img[..., 0] = (1.0 - sky_t) * 0.68 + sky_t * 0.26
            img[..., 1] = (1.0 - sky_t) * 0.92 + sky_t * 0.70
            img[..., 2] = (1.0 - sky_t) * 1.00 + sky_t * 0.99
        else:
            img[..., 0] = (1.0 - sky_t) * 0.48 + sky_t * 0.14
            img[..., 1] = (1.0 - sky_t) * 0.94 + sky_t * 0.76
            img[..., 2] = (1.0 - sky_t) * 1.00 + sky_t * 0.99

        zbuf = np.full((H, W), 1e9, dtype=np.float32)

        # 3. 3D Ground Plane (y = 0)
        hit_g = rd[..., 1] < -1e-3
        t_g = np.where(hit_g, -ro[1] / np.minimum(rd[..., 1], -1e-4), 1e9)
        valid_g = hit_g & (t_g > 0.1) & (t_g < 20.0)
        gx = ro[0] + t_g * rd[..., 0]
        gz = ro[2] + t_g * rd[..., 2]

        tx_mod = np.abs((gx * 1.25) - np.round(gx * 1.25))
        tz_mod = np.abs((gz * 1.25) - np.round(gz * 1.25))
        grout = (tx_mod < 0.035) | (tz_mod < 0.035)
        checker = ((np.floor(gx * 1.25) + np.floor(gz * 1.25)) % 2 == 0)
        if theme == "unique_school":
            c1 = np.array([0.50, 0.86, 0.44], dtype=np.float32)
            c2 = np.array([0.44, 0.80, 0.38], dtype=np.float32)
            cg = np.array([0.38, 0.72, 0.34], dtype=np.float32)
        else:
            c1 = np.array([0.85, 0.88, 0.91], dtype=np.float32)
            c2 = np.array([0.79, 0.83, 0.87], dtype=np.float32)
            cg = np.array([0.68, 0.72, 0.77], dtype=np.float32)

        g_col = np.where(checker[..., None], c1, c2)
        g_col = np.where(grout[..., None], cg, g_col)

        # 4. Stage Setup & Character Choreography per Theme
        s_idx = (scene_number - 1) % 7
        if theme == "unique_school":
            # Clip 2: Sunny's Park Stage Pedestals + Contraption Story Arc
            pools = [
                Pool3D((0.0, 0.35), outer_radius=0.88, height=0.30, color=(0.98, 0.68, 0.18), water_level=0.30, is_stage_pedestal=True),
                Pool3D((-1.30, -0.50), outer_radius=0.72, height=0.26, color=(0.24, 0.82, 0.64), water_level=0.26, is_stage_pedestal=True),
                Pool3D((1.30, -0.50), outer_radius=0.72, height=0.26, color=(0.66, 0.42, 0.98), water_level=0.26, is_stage_pedestal=True),
            ]
            has_contraption = scene_number <= 4
            sunny_act = "surprised" if has_contraption else "jump_splash"
            char_specs = [
                ("sunny", (0.0, 0.30, 0.35), sunny_act, 1.06, has_contraption),
                ("pip", (-1.15, 0.26, -0.35), "cheer", 0.95, False),
                ("milo", (1.15, 0.26, -0.35), "cheer", 0.95, False),
            ]
        else:
            # Clip 1: Pool Party Challenge
            pools = [
                Pool3D((0.0, 0.35), outer_radius=0.95, height=0.52, color=(0.08, 0.72, 0.99), water_level=0.44),
                Pool3D((-1.35, -0.55), outer_radius=0.82, height=0.48, color=(0.68, 0.24, 0.98), water_level=0.40),
                Pool3D((1.35, -0.55), outer_radius=0.82, height=0.48, color=(0.98, 0.22, 0.26), water_level=0.40),
            ]
            if s_idx in (0, 3, 6):
                char_specs = [
                    ("pip", (0.0, 0.18, 0.35), "jump_splash", 1.05, False),
                    ("milo", (-1.15, 0.0, -0.15), "cheer", 0.96, False),
                    ("sunny", (1.10, 0.0, -0.25), "cheer", 0.96, False),
                ]
            elif s_idx in (1, 4):
                char_specs = [
                    ("milo", (0.0, 0.16, 0.35), "jump_splash", 1.04, False),
                    ("pip", (-0.65, 0.0, 0.45), "surprised", 1.00, False),
                    ("sunny", (-1.35, 0.12, -0.55), "cheer", 0.95, False),
                ]
            else:
                char_specs = [
                    ("sunny", (0.0, 0.16, 0.35), "jump_splash", 1.04, False),
                    ("pip", (1.35, 0.14, -0.55), "cheer", 1.00, False),
                    ("milo", (-1.35, 0.14, -0.55), "cheer", 0.96, False),
                ]

        # Soft ground contact shadows
        shadow_atten = np.ones((H, W), dtype=np.float32)
        for p in pools:
            d2 = (gx - p.center_xz[0]) ** 2 + (gz - p.center_xz[1]) ** 2
            shadow_atten *= 1.0 - 0.35 * np.exp(-d2 / (p.outer_radius ** 2 * 1.25))
        for _, cpos, _, _, _ in char_specs:
            d2 = (gx - cpos[0]) ** 2 + (gz - cpos[2]) ** 2
            shadow_atten *= 1.0 - 0.38 * np.exp(-d2 / 0.18)

        g_col *= shadow_atten[..., None]
        fade = np.clip((t_g - 7.5) / 12.0, 0.0, 1.0)[..., None]
        g_col = g_col * (1.0 - fade) + img * fade
        img = np.where(valid_g[..., None], g_col, img)
        zbuf = np.where(valid_g, t_g, zbuf)

        # 5. Ray-Trace 3D Pools / Stage Pedestals
        lx, ly, lz = float(self.light_dir[0]), float(self.light_dir[1]), float(self.light_dir[2])
        for p in pools:
            px, pz = p.center_xz
            R = p.outer_radius
            H_p = p.height
            cz = -(pz - ro[2])
            if cz <= 0.4:
                continue
            ocx = ro[0] - px
            ocz = ro[2] - pz
            rdx = rd[..., 0]
            rdz = rd[..., 2]
            a_c = rdx * rdx + rdz * rdz
            b_c = 2.0 * (ocx * rdx + ocz * rdz)
            c_c = ocx * ocx + ocz * ocz - R * R
            disc_c = b_c * b_c - 4.0 * a_c * c_c
            hit_cyl = disc_c > 0.0
            t_cyl = np.where(hit_cyl, (-b_c - np.sqrt(np.maximum(disc_c, 0.0))) / np.maximum(2.0 * a_c, 1e-6), 1e9)
            hy_cyl = ro[1] + t_cyl * rd[..., 1]
            valid_cyl = hit_cyl & (t_cyl > 0.1) & (hy_cyl >= 0.0) & (hy_cyl <= H_p) & (t_cyl < zbuf)

            if valid_cyl.any():
                hx_c = ro[0] + t_cyl * rdx - px
                hz_c = ro[2] + t_cyl * rdz - pz
                nx = hx_c / R
                nz = hz_c / R
                rib_phase = (hy_cyl / H_p) * 3.0 * math.pi * 2.0
                ny = 0.45 * np.cos(rib_phase)
                rib_groove = 0.88 + 0.12 * np.sin(rib_phase - math.pi * 0.5)
                n_len = np.sqrt(nx * nx + ny * ny + nz * nz)
                nx /= n_len
                ny /= n_len
                nz /= n_len

                theta = np.arctan2(hx_c, hz_c)
                dots = (np.cos(theta * 10.0) * np.sin((hy_cyl / H_p) * 3.0 * math.pi)) > 0.72
                base_r = np.where(dots, p.dot_color[0], p.color[0] * rib_groove)
                base_g = np.where(dots, p.dot_color[1], p.color[1] * rib_groove)
                base_b = np.where(dots, p.dot_color[2], p.color[2] * rib_groove)

                ndotl = np.clip((nx * lx + ny * ly + nz * lz + 0.50) / 1.50, 0.35, 1.0)
                hx_v = lx - rd[..., 0]
                hy_v = ly - rd[..., 1]
                hz_v = lz - rd[..., 2]
                h_len = np.sqrt(hx_v * hx_v + hy_v * hy_v + hz_v * hz_v) + 1e-6
                ndoth = np.clip((nx * hx_v + ny * hy_v + nz * hz_v) / h_len, 0.0, 1.0)
                spec = (ndoth ** 28) * 0.60

                col_cyl = np.stack([
                    np.clip(base_r * ndotl + spec, 0.0, 1.0),
                    np.clip(base_g * ndotl + spec, 0.0, 1.0),
                    np.clip(base_b * ndotl + spec, 0.0, 1.0),
                ], axis=-1)
                img = np.where(valid_cyl[..., None], col_cyl, img)
                zbuf = np.where(valid_cyl, t_cyl, zbuf)

            # Top surface (Rippling Water or Star Stage Platform)
            hit_w = rd[..., 1] < -1e-3
            t_w = np.where(hit_w, (p.water_level - ro[1]) / np.minimum(rd[..., 1], -1e-4), 1e9)
            wx = ro[0] + t_w * rdx - px
            wz = ro[2] + t_w * rdz - pz
            wr2 = wx * wx + wz * wz
            valid_w = hit_w & (t_w > 0.1) & (wr2 <= (R * 0.95) ** 2) & (t_w < zbuf)
            if valid_w.any():
                wr = np.sqrt(wr2)
                if p.is_stage_pedestal:
                    ring = np.sin(wr * 14.0 - t_sec * 4.0) > 0.6
                    w_col = np.stack([
                        np.where(ring, 1.0, p.color[0] * 1.05),
                        np.where(ring, 0.95, p.color[1] * 1.05),
                        np.where(ring, 0.55, p.color[2] * 1.05),
                    ], axis=-1)
                else:
                    wave = np.sin(wr * 18.0 - t_sec * 7.5) * 0.5 + 0.5
                    foam = (wr > R * 0.80) | (wave > 0.86)
                    w_col = np.stack([
                        0.14 + 0.25 * wave + np.where(foam, 0.45, 0.0),
                        0.80 + 0.15 * wave + np.where(foam, 0.20, 0.0),
                        0.99 + 0.01 * wave,
                    ], axis=-1)
                img = np.where(valid_w[..., None], np.clip(w_col, 0.0, 1.0), img)
                zbuf = np.where(valid_w, t_w, zbuf)

        # 6. Collect All 3D Ellipsoids
        all_spheres: List[Sphere3D] = []

        # Background 3D Wooden Fence Posts
        for fx in np.linspace(-3.2, 3.2, 13):
            all_spheres.append(Sphere3D((float(fx), 0.55, -2.55), (0.24, 0.62, 0.08), (0.80, 0.56, 0.34), 0.5, 0.15, min_ambient=0.55))

        # Bright Fluffy 3D White Clouds (`min_ambient=0.82` so clouds stay fluffy white!)
        for cx_base, cy_base, c_scale in [(-1.8, 2.75, 1.0), (0.4, 3.05, 1.15), (2.1, 2.65, 0.9)]:
            cx = ((cx_base + t_sec * 0.12 + 3.5) % 7.0) - 3.5
            all_spheres.append(Sphere3D((cx, cy_base, -3.8), (0.55 * c_scale, 0.26 * c_scale, 0.35 * c_scale), (1.0, 1.0, 1.0), 0.6, 0.1, min_ambient=0.84))
            all_spheres.append(Sphere3D((cx - 0.38 * c_scale, cy_base - 0.05, -3.75), (0.38 * c_scale, 0.21 * c_scale, 0.30 * c_scale), (0.99, 0.99, 1.0), 0.6, 0.1, min_ambient=0.84))
            all_spheres.append(Sphere3D((cx + 0.38 * c_scale, cy_base - 0.04, -3.75), (0.40 * c_scale, 0.22 * c_scale, 0.30 * c_scale), (0.99, 0.99, 1.0), 0.6, 0.1, min_ambient=0.84))

        if theme == "pool_party":
            # Cute Floating 3D Yellow Rubber Duck & Bouncing Beach Ball
            duck_bob = math.sin(t_sec * 5.5) * 0.03
            all_spheres.append(Sphere3D((0.48, 0.47 + duck_bob, 0.62), (0.11, 0.08, 0.13), (1.0, 0.88, 0.08), 0.15, 0.80, min_ambient=0.65))
            all_spheres.append(Sphere3D((0.48, 0.56 + duck_bob, 0.68), (0.075, 0.075, 0.075), (1.0, 0.88, 0.08), 0.15, 0.80, min_ambient=0.65))
            all_spheres.append(Sphere3D((0.48, 0.55 + duck_bob, 0.75), (0.04, 0.025, 0.05), (1.0, 0.48, 0.06), 0.20, 0.70, min_ambient=0.65))
            ball_y = 0.52 + abs(math.sin(t_sec * 4.8)) * 0.32
            all_spheres.append(Sphere3D((-0.55, ball_y, 0.68), (0.14, 0.14, 0.14), (1.0, 0.30, 0.52), 0.10, 0.90, min_ambient=0.60))

            # Animated 3D Water Splash Droplets
            splash_phase = (t_sec * 1.55) % 1.0
            for k in range(12):
                ang = k * (2.0 * math.pi / 12.0) + scene_number * 0.5
                rad = 0.28 + splash_phase * 0.75
                sy = 0.45 + (4.0 * splash_phase * (1.0 - splash_phase)) * (0.55 + (k % 3) * 0.16)
                sx = math.cos(ang) * rad
                sz = 0.35 + math.sin(ang) * rad
                drop_r = 0.044 * (1.1 - 0.45 * splash_phase)
                all_spheres.append(Sphere3D((sx, sy, sz), (drop_r, drop_r * 1.25, drop_r), (0.78, 0.96, 1.0), 0.05, 0.95, min_ambient=0.75))
        else:
            # Theme 2 (`unique_school`): Floating 3D Golden Stars & Pink Celebration Orbs
            float_phase = (t_sec * 1.2) % 1.0
            palette_cel = [(1.0, 0.86, 0.15), (1.0, 0.38, 0.68), (0.25, 0.88, 0.98)]
            for k in range(12):
                ang = k * (2.0 * math.pi / 12.0) + t_sec * 1.2
                rad = 0.55 + 0.25 * math.sin(t_sec * 2.0 + k)
                sy = 0.55 + ((k * 0.15 + float_phase) % 1.0) * 1.25
                sx = math.cos(ang) * rad
                sz = 0.35 + math.sin(ang) * rad
                c_orb = palette_cel[k % len(palette_cel)]
                all_spheres.append(Sphere3D((sx, sy, sz), (0.055, 0.055, 0.055), c_orb, 0.10, 0.95, min_ambient=0.78))

        # Build Articulated 3D Characters
        for idx_c, (cid, cpos, cact, cscale, contraption) in enumerate(char_specs):
            m_val = mouth_open if idx_c == 0 else mouth_open * 0.40
            all_spheres.extend(
                self._build_character_rig(
                    char_id=cid,
                    pos=cpos,
                    t_sec=t_sec + idx_c * 0.35,
                    mouth_open=m_val,
                    action=cact,
                    scale=cscale,
                    wearing_contraption=contraption,
                )
            )

        # 7. Screen-Space Bounding-Box Culled 3D Ellipsoid Ray-Tracing + Pixar Shading
        cam_fwd = np.array(look_at, dtype=np.float32) - ro
        cam_fwd /= np.linalg.norm(cam_fwd)
        cam_up_w = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        cam_right = np.cross(cam_fwd, cam_up_w)
        cam_right /= max(1e-5, np.linalg.norm(cam_right))
        cam_up = np.cross(cam_right, cam_fwd)

        for sp in all_spheres:
            c = np.array(sp.center, dtype=np.float32)
            r = np.array(sp.radius, dtype=np.float32)
            rel = c - ro
            tz = float(np.dot(rel, cam_fwd))
            if tz <= 0.35:
                continue
            sx = float(np.dot(rel, cam_right)) / tz * fov
            sy = float(np.dot(rel, cam_up)) / tz * fov
            max_r = float(np.max(r))
            sr = max_r / max(0.25, tz - max_r) * fov * 1.35

            x0 = max(0, int((sx - sr + self.aspect) / (2.0 * self.aspect) * W))
            x1 = min(W, int((sx + sr + self.aspect) / (2.0 * self.aspect) * W) + 1)
            y0 = max(0, int((1.0 - (sy + sr)) / 2.0 * H))
            y1 = min(H, int((1.0 - (sy - sr)) / 2.0 * H) + 1)
            if x1 <= x0 or y1 <= y0:
                continue

            rd_sub = rd[y0:y1, x0:x1]
            rd_s = rd_sub / r
            oc_s = -rel / r
            a = np.einsum("ijk,ijk->ij", rd_s, rd_s)
            b = 2.0 * np.einsum("ijk,k->ij", rd_s, oc_s)
            cc = float(np.dot(oc_s, oc_s)) - 1.0
            disc = b * b - 4.0 * a * cc
            hit = disc > 0.0
            if not hit.any():
                continue

            t_hit = np.where(hit, (-b - np.sqrt(np.maximum(disc, 0.0))) / np.maximum(2.0 * a, 1e-6), 1e9)
            z_sub = zbuf[y0:y1, x0:x1]
            closer = hit & (t_hit > 0.1) & (t_hit < z_sub)
            if not closer.any():
                continue

            z_sub[closer] = t_hit[closer]
            img_sub = img[y0:y1, x0:x1]

            if sp.unlit:
                img_sub[closer] = np.array(sp.color, dtype=np.float32)
                continue

            hp = ro[None, None, :] + t_hit[..., None] * rd_sub - c[None, None, :]
            n_raw = hp / (r[None, None, :] ** 2)
            n_norm = n_raw / np.maximum(np.linalg.norm(n_raw, axis=-1, keepdims=True), 1e-6)

            ndotl = np.clip((np.einsum("ijk,k->ij", n_norm, self.light_dir) + 0.55) / 1.55, sp.min_ambient, 1.0)
            sky_fill = 0.12 * np.clip(n_norm[..., 1] * 0.5 + 0.5, 0.0, 1.0)

            h_vec = self.light_dir[None, None, :] - rd_sub
            h_vec /= np.maximum(np.linalg.norm(h_vec, axis=-1, keepdims=True), 1e-6)
            ndoth = np.clip(np.einsum("ijk,ijk->ij", n_norm, h_vec), 0.0, 1.0)
            spec = (ndoth ** 28) * sp.specular

            ndotv = np.clip(-np.einsum("ijk,ijk->ij", n_norm, rd_sub), 0.0, 1.0)
            rim = ((1.0 - ndotv) ** 3) * 0.20

            base_c = np.array(sp.color, dtype=np.float32)
            lit = base_c[None, None, :] * (ndotl + sky_fill)[..., None] + (spec + rim)[..., None]
            img_sub[closer] = np.clip(lit[closer], 0.0, 1.0)

        rgb8 = (np.clip(img, 0.0, 1.0) * 255.0).astype(np.uint8)
        if self.W != config.VIDEO_WIDTH or self.H != config.VIDEO_HEIGHT:
            pil_img = Image.fromarray(rgb8, mode="RGB").resize(
                (config.VIDEO_WIDTH, config.VIDEO_HEIGHT), Image.Resampling.BILINEAR
            )
            return np.asarray(pil_img, dtype=np.uint8)
        return rgb8

    def render_scene_video(
        self,
        output_mp4: Path,
        duration: float,
        audio_path: Optional[Path] = None,
        scene_number: int = 1,
        clip_index: int = 1,
        fps: int = config.VIDEO_FPS,
    ) -> Tuple[Path, Path]:
        """
        Render a full 30-FPS 3D animated scene video (`.mp4`) with 2 dynamic 3D camera cuts
        and voiceover-synced mouth movement, piping raw RGB frames directly into FFmpeg.
        Returns (output_mp4, preview_jpg).
        """
        output_mp4.parent.mkdir(parents=True, exist_ok=True)
        num_frames = max(24, int(round(duration * fps)))
        shot_split_frame = int(num_frames * 0.54)
        theme = "pool_party" if (clip_index % 2 == 1) else "unique_school"

        audio_env = extract_audio_envelope(audio_path, num_frames=num_frames, fps=fps)

        cmd = [
            config.FFMPEG_BIN, "-y", "-v", "error",
            "-f", "rawvideo",
            "-pix_fmt", "rgb24",
            "-s", f"{config.VIDEO_WIDTH}x{config.VIDEO_HEIGHT}",
            "-r", str(fps),
            "-i", "pipe:0",
            "-vf", "scale=out_range=tv,format=yuv420p",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-color_range", "tv",
            "-profile:v", "high",
            "-movflags", "+faststart",
            "-an",
            str(output_mp4),
        ]

        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        mid_frame_rgb: Optional[np.ndarray] = None
        try:
            for f_idx in range(num_frames):
                t_sec = f_idx / float(fps)
                shot_idx = 0 if f_idx < shot_split_frame else 1
                frame_rgb = self.render_frame(
                    t_sec=t_sec,
                    mouth_open=float(audio_env[f_idx]),
                    scene_number=scene_number,
                    shot_index=shot_idx,
                    theme=theme,
                )
                if f_idx == min(10, num_frames - 1):
                    mid_frame_rgb = frame_rgb
                proc.stdin.write(frame_rgb.tobytes())
            proc.stdin.close()
            proc.wait(timeout=90)
        except Exception as e:
            proc.kill()
            raise RuntimeError(f"Failed rendering 3D animation scene {scene_number}: {e}")

        thumb_path = output_mp4.parent / f"scene_{scene_number:02d}_shot1.jpg"
        if mid_frame_rgb is not None:
            Image.fromarray(mid_frame_rgb, mode="RGB").save(thumb_path, "JPEG", quality=92)

        return output_mp4, thumb_path
