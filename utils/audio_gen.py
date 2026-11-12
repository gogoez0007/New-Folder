"""
Synthetic Audio SFX & BGM Generator (`utils/audio_gen.py`).
Generates 12 clean, royalty-free Sound Effects (.wav) and loopable BGM tracks using numpy
so every scene action (walk, run, splash, surprise gasp, sad moment, magic reveal, cheer,
impact, pop, whoosh, laugh) has synchronized sound effects.
"""

import wave
from pathlib import Path
from typing import List
import numpy as np


def _write_wav(filepath: Path, samples: np.ndarray, sample_rate: int = 44100):
    """Write 16-bit mono PCM WAV file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    clamped = np.clip(samples, -1.0, 1.0)
    int16_samples = (clamped * 32767).astype(np.int16)

    with wave.open(str(filepath), "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(int16_samples.tobytes())


def generate_whoosh_sfx(filepath: Path, duration: float = 0.35, sample_rate: int = 44100) -> Path:
    num_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, num_samples, endpoint=False)
    center = 0.45 * duration
    width = 0.15 * duration
    envelope = np.exp(-0.5 * ((t - center) / width) ** 2)
    rng = np.random.default_rng(42)
    noise = rng.uniform(-1.0, 1.0, num_samples)
    freq = 200 + 600 * envelope
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    tonal = 0.4 * np.sin(phase)
    combined = (0.6 * noise + tonal) * envelope
    fade_len = int(sample_rate * 0.02)
    combined[:fade_len] *= np.linspace(0, 1, fade_len)
    combined[-fade_len:] *= np.linspace(1, 0, fade_len)
    max_amp = np.max(np.abs(combined))
    if max_amp > 0:
        combined = combined / max_amp * 0.85
    _write_wav(filepath, combined, sample_rate)
    return filepath


def generate_pop_sfx(filepath: Path, duration: float = 0.09, sample_rate: int = 44100) -> Path:
    num_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, num_samples, endpoint=False)
    freq = 900 * np.exp(-t * 30) + 250
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    envelope = np.exp(-t * 45)
    samples = np.sin(phase) * envelope
    max_amp = np.max(np.abs(samples))
    if max_amp > 0:
        samples = samples / max_amp * 0.80
    _write_wav(filepath, samples, sample_rate)
    return filepath


def generate_beep_sfx(filepath: Path, duration: float = 0.12, sample_rate: int = 44100) -> Path:
    num_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, num_samples, endpoint=False)
    freq = 1050.0
    envelope = np.ones_like(t)
    attack_samples = int(0.01 * sample_rate)
    decay_samples = int(0.04 * sample_rate)
    envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    envelope[-decay_samples:] = np.linspace(1, 0, decay_samples)
    samples = 0.65 * np.sin(2 * np.pi * freq * t) * envelope
    _write_wav(filepath, samples, sample_rate)
    return filepath


def generate_impact_sfx(filepath: Path, duration: float = 0.48, sample_rate: int = 44100) -> Path:
    num_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, num_samples, endpoint=False)
    freq = 85 * np.exp(-t * 6) + 40
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    envelope = np.exp(-t * 7)
    sub_bass = np.sin(phase) * envelope
    click_len = int(0.006 * sample_rate)
    rng = np.random.default_rng(7)
    click = np.zeros(num_samples)
    click[:click_len] = rng.uniform(-0.35, 0.35, click_len) * np.linspace(1, 0, click_len)
    combined = sub_bass + click
    max_amp = np.max(np.abs(combined))
    if max_amp > 0:
        combined = combined / max_amp * 0.90
    _write_wav(filepath, combined, sample_rate)
    return filepath


def generate_splash_sfx(filepath: Path, duration: float = 0.55, sample_rate: int = 44100) -> Path:
    """Water splash sound using band-modulated noise burst + bubble chirps."""
    num_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, num_samples, endpoint=False)
    rng = np.random.default_rng(101)
    noise = rng.normal(0, 1, num_samples)
    env = (1.0 - np.exp(-t * 65.0)) * np.exp(-t * 5.5)
    bubble_freq = 320 + 480 * np.sin(2 * np.pi * 18 * t)
    bubbles = 0.35 * np.sin(2 * np.pi * np.cumsum(bubble_freq) / sample_rate) * np.exp(-t * 6.5)
    combined = (0.65 * noise * env) + bubbles
    max_amp = np.max(np.abs(combined))
    if max_amp > 0:
        combined = combined / max_amp * 0.85
    _write_wav(filepath, combined, sample_rate)
    return filepath


def generate_boing_sfx(filepath: Path, duration: float = 0.42, sample_rate: int = 44100) -> Path:
    """Cartoon spring/bounce boing sound."""
    num_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, num_samples, endpoint=False)
    freq = 220 + 260 * (t / duration) + 55 * np.sin(2 * np.pi * 24 * t)
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    env = np.exp(-t * 5.5)
    samples = (0.75 * np.sin(phase) + 0.25 * np.sin(2 * phase)) * env
    max_amp = np.max(np.abs(samples))
    if max_amp > 0:
        samples = samples / max_amp * 0.82
    _write_wav(filepath, samples, sample_rate)
    return filepath


def generate_magic_chime_sfx(filepath: Path, duration: float = 0.65, sample_rate: int = 44100) -> Path:
    """Sparkling ascending arpeggio chime for discoveries & magical reveals."""
    num_samples = int(duration * sample_rate)
    samples = np.zeros(num_samples, dtype=np.float32)
    notes = [523.25, 659.25, 783.99, 1046.50, 1318.51, 1567.98]
    for idx, freq in enumerate(notes):
        start = int(idx * 0.065 * sample_rate)
        if start >= num_samples:
            break
        length = num_samples - start
        t = np.linspace(0, length / sample_rate, length, endpoint=False)
        env = np.exp(-t * 8.0)
        tone = (0.6 * np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 2 * t)) * env
        samples[start:] += tone.astype(np.float32)
    max_amp = float(np.max(np.abs(samples)))
    if max_amp > 0:
        samples = samples / max_amp * 0.80
    _write_wav(filepath, samples, sample_rate)
    return filepath


def generate_cheer_fanfare_sfx(filepath: Path, duration: float = 0.70, sample_rate: int = 44100) -> Path:
    """Bright celebratory major triad fanfare."""
    num_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, num_samples, endpoint=False)
    freqs = [523.25, 659.25, 783.99, 1046.50]
    env = (1.0 - np.exp(-t * 50.0)) * np.exp(-t * 3.5)
    chord = sum(np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) for f in freqs)
    samples = chord * env
    max_amp = np.max(np.abs(samples))
    if max_amp > 0:
        samples = samples / max_amp * 0.82
    _write_wav(filepath, samples, sample_rate)
    return filepath


def generate_sad_trombone_sfx(filepath: Path, duration: float = 0.75, sample_rate: int = 44100) -> Path:
    """Comedic descending sad notes for setbacks or sad moments."""
    num_samples = int(duration * sample_rate)
    samples = np.zeros(num_samples, dtype=np.float32)
    notes = [(0.0, 0.22, 392.0), (0.22, 0.44, 369.99), (0.44, 0.75, 349.23)]
    for s_sec, e_sec, freq in notes:
        s_idx = int(s_sec * sample_rate)
        e_idx = min(num_samples, int(e_sec * sample_rate))
        length = e_idx - s_idx
        if length <= 0:
            continue
        t = np.linspace(0, length / sample_rate, length, endpoint=False)
        f_curve = freq * (1.0 - 0.06 * (t / max(0.01, e_sec - s_sec)))
        phase = 2 * np.pi * np.cumsum(f_curve) / sample_rate
        env = np.exp(-t * 4.0)
        samples[s_idx:e_idx] += ((0.7 * np.sin(phase) + 0.3 * np.sin(2 * phase)) * env).astype(np.float32)
    max_amp = float(np.max(np.abs(samples)))
    if max_amp > 0:
        samples = samples / max_amp * 0.80
    _write_wav(filepath, samples, sample_rate)
    return filepath


def generate_gasp_shock_sfx(filepath: Path, duration: float = 0.35, sample_rate: int = 44100) -> Path:
    """Dramatic surprise sting."""
    num_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, num_samples, endpoint=False)
    freq = 440 + 440 * np.exp(-t * 14)
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    env = np.exp(-t * 8.0)
    samples = (np.sin(phase) + 0.5 * np.sin(1.5 * phase)) * env
    max_amp = np.max(np.abs(samples))
    if max_amp > 0:
        samples = samples / max_amp * 0.82
    _write_wav(filepath, samples, sample_rate)
    return filepath


def generate_footsteps_sfx(filepath: Path, duration: float = 0.50, sample_rate: int = 44100) -> Path:
    """Light rhythmic cartoon footsteps."""
    num_samples = int(duration * sample_rate)
    samples = np.zeros(num_samples, dtype=np.float32)
    for step_idx in range(4):
        s_idx = int(step_idx * 0.12 * sample_rate)
        length = min(int(0.06 * sample_rate), num_samples - s_idx)
        if length <= 0:
            break
        t = np.linspace(0, length / sample_rate, length, endpoint=False)
        freq = 180 if step_idx % 2 == 0 else 210
        tap = np.sin(2 * np.pi * freq * t) * np.exp(-t * 55.0)
        samples[s_idx:s_idx + length] += tap.astype(np.float32)
    max_amp = float(np.max(np.abs(samples)))
    if max_amp > 0:
        samples = samples / max_amp * 0.75
    _write_wav(filepath, samples, sample_rate)
    return filepath


def generate_laugh_giggle_sfx(filepath: Path, duration: float = 0.48, sample_rate: int = 44100) -> Path:
    """Playful bouncy giggle notes."""
    num_samples = int(duration * sample_rate)
    samples = np.zeros(num_samples, dtype=np.float32)
    freqs = [587.33, 659.25, 783.99, 880.0]
    for i, f in enumerate(freqs):
        s_idx = int(i * 0.10 * sample_rate)
        length = min(int(0.09 * sample_rate), num_samples - s_idx)
        if length <= 0:
            break
        t = np.linspace(0, length / sample_rate, length, endpoint=False)
        chirp = np.sin(2 * np.pi * (f + 120 * t) * t) * np.exp(-t * 28.0)
        samples[s_idx:s_idx + length] += chirp.astype(np.float32)
    max_amp = float(np.max(np.abs(samples)))
    if max_amp > 0:
        samples = samples / max_amp * 0.78
    _write_wav(filepath, samples, sample_rate)
    return filepath


def _synthesize_bgm_track(
    filepath: Path,
    melody_hz: List[float],
    bass_hz: List[float],
    bpm: float = 120.0,
    timbre: str = "marimba",
    chord_root_hz: float = 261.63,
    duration: float = 16.0,
    sample_rate: int = 44100,
) -> Path:
    """Synthesize a rich multi-instrument cartoon/cinematic loopable BGM track."""
    num_samples = int(duration * sample_rate)
    samples = np.zeros(num_samples, dtype=np.float32)
    step_sec = 60.0 / (bpm * 2.0)  # eighth-note groove
    step_samples = max(1, int(step_sec * sample_rate))
    total_steps = int(duration / step_sec)
    rng = np.random.default_rng(int(bpm) + len(melody_hz))

    # Optional subtle warm harmonic pad underneath for dreamy/cozy tracks
    if timbre in ("bells", "ukulele"):
        t_full = np.linspace(0, duration, num_samples, endpoint=False)
        pad = (
            0.09 * np.sin(2 * np.pi * chord_root_hz * t_full)
            + 0.06 * np.sin(2 * np.pi * (chord_root_hz * 1.25) * t_full)
            + 0.05 * np.sin(2 * np.pi * (chord_root_hz * 1.50) * t_full)
        )
        samples += pad.astype(np.float32)

    for step in range(total_steps):
        start = step * step_samples
        gate = 1.8 if timbre in ("bells", "ukulele") else (0.85 if timbre == "pizzicato" else 1.25)
        end = min(num_samples, start + int(step_samples * gate))
        length = end - start
        if length <= 0:
            break
        t = np.linspace(0, length / sample_rate, length, endpoint=False)
        f = melody_hz[step % len(melody_hz)]
        note = np.zeros(length, dtype=np.float32)

        if f > 0:
            if timbre == "pizzicato":
                env = np.exp(-t * 16.0) * (1.0 - np.exp(-t * 280.0))
                note += ((0.70 * np.sin(2 * np.pi * f * t) + 0.28 * np.sin(4 * np.pi * f * t)) * env).astype(np.float32)
            elif timbre == "arcade":
                env = np.exp(-t * 11.0) * (1.0 - np.exp(-t * 420.0))
                sq = np.tanh(2.2 * np.sin(2 * np.pi * f * t))
                note += ((0.42 * sq + 0.35 * np.sin(4 * np.pi * f * t)) * env).astype(np.float32)
            elif timbre == "ukulele":
                env = np.exp(-t * 6.5) * (1.0 - np.exp(-t * 220.0))
                strum = (
                    0.50 * np.sin(2 * np.pi * f * t)
                    + 0.32 * np.sin(2 * np.pi * (f * 1.25) * t)
                    + 0.22 * np.sin(2 * np.pi * (f * 1.5) * t)
                )
                note += (strum * env).astype(np.float32)
            elif timbre == "bells":
                env = np.exp(-t * 4.8) * (1.0 - np.exp(-t * 350.0))
                note += ((0.60 * np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * (f * 3.0) * t)) * env).astype(np.float32)
            else:  # marimba / xylophone
                env = np.exp(-t * 10.5) * (1.0 - np.exp(-t * 260.0))
                note += ((0.65 * np.sin(2 * np.pi * f * t) + 0.22 * np.sin(2 * np.pi * (f * 4.0) * t)) * env).astype(np.float32)

        if step % 2 == 0 and bass_hz:
            bf = bass_hz[(step // 2) % len(bass_hz)]
            if bf > 0:
                b_env = np.exp(-t * (6.0 if timbre != "pizzicato" else 11.0)) * (1.0 - np.exp(-t * 180.0))
                note += (0.42 * np.sin(2 * np.pi * bf * t) * b_env).astype(np.float32)

        # Crisp percussion groove (offbeat shaker / hi-hat on odd steps, kick thump on beat 0/4)
        if step % 4 == 0:
            k_len = min(length, int(0.08 * sample_rate))
            tk = np.linspace(0, k_len / sample_rate, k_len, endpoint=False)
            note[:k_len] += (0.30 * np.sin(2 * np.pi * (120 * np.exp(-tk * 25) + 45) * tk) * np.exp(-tk * 22)).astype(np.float32)
        elif step % 2 == 1 and timbre in ("arcade", "xylophone", "ukulele"):
            h_len = min(length, int(0.035 * sample_rate))
            th = np.linspace(0, h_len / sample_rate, h_len, endpoint=False)
            note[:h_len] += (0.09 * rng.uniform(-1.0, 1.0, h_len) * np.exp(-th * 90)).astype(np.float32)

        samples[start:end] += note

    # Smooth 40ms loop seam crossfade
    fade = min(int(0.04 * sample_rate), num_samples // 8)
    samples[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
    samples[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)

    max_amp = float(np.max(np.abs(samples)))
    if max_amp > 0:
        samples = samples / max_amp * 0.56
    _write_wav(filepath, samples, sample_rate)
    return filepath


def generate_kids_upbeat_bgm(filepath: Path, duration: float = 16.0, sample_rate: int = 44100) -> Path:
    melody = [523.25, 659.25, 783.99, 659.25, 698.46, 880.0, 1046.5, 880.0, 523.25, 587.33, 659.25, 783.99, 698.46, 659.25, 587.33, 523.25]
    bass = [261.63, 196.00, 174.61, 196.00]
    return _synthesize_bgm_track(filepath, melody, bass, bpm=122.0, timbre="marimba", duration=duration, sample_rate=sample_rate)


def ensure_default_sfx(sfx_dir: Path) -> List[Path]:
    """Ensure all 12 sound effects and 6 varied mood-driven BGM tracks exist."""
    sfx_dir.mkdir(parents=True, exist_ok=True)
    generated = []

    sfx_map = {
        "whoosh.wav": generate_whoosh_sfx,
        "pop.wav": generate_pop_sfx,
        "beep.wav": generate_beep_sfx,
        "impact.wav": generate_impact_sfx,
        "splash.wav": generate_splash_sfx,
        "boing.wav": generate_boing_sfx,
        "magic_chime.wav": generate_magic_chime_sfx,
        "cheer_fanfare.wav": generate_cheer_fanfare_sfx,
        "sad_trombone.wav": generate_sad_trombone_sfx,
        "gasp_shock.wav": generate_gasp_shock_sfx,
        "footsteps.wav": generate_footsteps_sfx,
        "laugh_giggle.wav": generate_laugh_giggle_sfx,
    }

    for filename, generator in sfx_map.items():
        file_path = sfx_dir / filename
        if not file_path.exists():
            generator(file_path)
            generated.append(file_path)

    bgm_dir = sfx_dir.parent / "bgm"
    bgm_dir.mkdir(parents=True, exist_ok=True)

    bgm_catalog = {
        "kids_upbeat_marimba.wav": (
            [523.25, 659.25, 783.99, 659.25, 698.46, 880.0, 1046.5, 880.0, 523.25, 587.33, 659.25, 783.99, 698.46, 659.25, 587.33, 523.25],
            [261.63, 196.00, 174.61, 196.00], 122.0, "marimba", 261.63,
        ),
        "sneaky_pizzicato_mystery.wav": (
            [440.0, 0.0, 523.25, 493.88, 440.0, 0.0, 659.25, 587.33, 523.25, 493.88, 440.0, 0.0, 415.30, 440.0, 493.88, 329.63],
            [110.0, 130.81, 146.83, 164.81], 112.0, "pizzicato", 220.0,
        ),
        "arcade_hero_quest.wav": (
            [392.0, 493.88, 587.33, 783.99, 659.25, 587.33, 493.88, 587.33, 440.0, 523.25, 659.25, 880.0, 783.99, 659.25, 587.33, 493.88],
            [196.0, 196.0, 220.0, 146.83], 138.0, "arcade", 196.0,
        ),
        "cozy_ukulele_sunshine.wav": (
            [392.0, 493.88, 587.33, 493.88, 440.0, 523.25, 659.25, 523.25, 392.0, 493.88, 659.25, 587.33, 440.0, 587.33, 493.88, 392.0],
            [196.0, 164.81, 130.81, 146.83], 108.0, "ukulele", 196.0,
        ),
        "comedy_chaotic_chase.wav": (
            [587.33, 622.25, 659.25, 783.99, 659.25, 587.33, 523.25, 587.33, 698.46, 739.99, 783.99, 880.0, 783.99, 698.46, 659.25, 587.33],
            [146.83, 220.0, 174.61, 196.0], 146.0, "marimba", 293.66,
        ),
        "magical_wonder_bells.wav": (
            [698.46, 880.0, 1046.5, 987.77, 880.0, 783.99, 698.46, 659.25, 587.33, 698.46, 880.0, 1174.66, 1046.5, 987.77, 880.0, 783.99],
            [174.61, 196.0, 220.0, 196.0], 98.0, "bells", 174.61,
        ),
    }

    for b_name, (mel, bas, bpm, tim, root) in bgm_catalog.items():
        bf = bgm_dir / b_name
        if not bf.exists():
            _synthesize_bgm_track(bf, mel, bas, bpm=bpm, timbre=tim, chord_root_hz=root)
            generated.append(bf)

    return generated
