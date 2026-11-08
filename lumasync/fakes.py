"""Fake and synthetic data for every contract type, so each module can be tested alone.

Nothing here imports a module (m1..m5). It only uses the contract and numpy/scipy, so:
  - M3 and M5 can be tested with AudioFrames made here, without M1;
  - M4 can be driven with fake RhythmState / MusicContext / LiveControls, without M1, M3 or M5;
  - M2 can be driven with fake LightIntents, without anything upstream.

Audio generators:
  click_track(bpm, seconds)            - a click on every beat at a known tempo
  synth_song(style, seconds, seed)     - short synthetic "songs" used as demo tracks
                                          (styles: neon_drive 128 BPM, slow_bloom 92 BPM,
                                           breakbeat_140 140 BPM, or "random" for an unknown track)
Feature-stream generators:
  audio_frames_from_samples(x)         - a small reference analyser (NOT M1; simpler, no AGC)
  fake_audio_frames(bpm, seconds)      - AudioFrames with flux spikes and bass on each beat
  fake_rhythm_states(bpm, seconds)     - a perfect beat clock, optional drop
  fake_music_contexts(script, seconds) - scripted recognition results over time
  fake_light_intent(n, t)              - a rainbow LightIntent for M2
"""
from __future__ import annotations

import math
from typing import Iterable, Optional

import numpy as np

from lumasync.contract import (
    BLOCK_SIZE,
    SAMPLE_RATE,
    AudioFrame,
    FixtureIntent,
    LightIntent,
    MusicContext,
    RhythmState,
)

SR = SAMPLE_RATE
TICK = BLOCK_SIZE / SAMPLE_RATE
BAND_NAMES = ["sub", "bass", "low_mid", "mid", "high_mid", "high"]


# =====================================================================================
# Audio synthesis helpers
# =====================================================================================
def _env(n: int, attack: float, decay: float, sr: int = SR) -> np.ndarray:
    t = np.arange(n) / sr
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-np.maximum(t - attack, 0) / max(decay, 1e-4))


def _lowpass(x: np.ndarray, cutoff: float, sr: int = SR) -> np.ndarray:
    from scipy.signal import butter, lfilter

    b, a = butter(2, min(cutoff / (sr / 2), 0.99))
    return lfilter(b, a, x)


def _highpass(x: np.ndarray, cutoff: float, sr: int = SR) -> np.ndarray:
    from scipy.signal import butter, lfilter

    b, a = butter(2, min(cutoff / (sr / 2), 0.99), btype="high")
    return lfilter(b, a, x)


def kick(sr: int = SR, length: float = 0.4, f_end: float = 45.0, sweep: float = 110.0,
         decay: float = 0.18, seed: int = 1) -> np.ndarray:
    n = int(length * sr)
    t = np.arange(n) / sr
    f = f_end + sweep * np.exp(-t / 0.04)              # pitch sweep (f_end + sweep) -> f_end Hz
    ph = 2 * np.pi * np.cumsum(f) / sr
    body = np.sin(ph) * np.exp(-t / decay)
    click = np.random.default_rng(seed).standard_normal(n) * np.exp(-t / 0.003) * 0.3
    return (body + click).astype(np.float32)


def snare(sr: int = SR, length: float = 0.25, seed: int = 2) -> np.ndarray:
    n = int(length * sr)
    t = np.arange(n) / sr
    noise = _highpass(np.random.default_rng(seed).standard_normal(n), 1200) * np.exp(-t / 0.06)
    tone = np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.05)
    return (0.6 * noise + 0.5 * tone).astype(np.float32)


def hat(sr: int = SR, length: float = 0.06, seed: int = 3) -> np.ndarray:
    n = int(length * sr)
    t = np.arange(n) / sr
    noise = _highpass(np.random.default_rng(seed).standard_normal(n), 7000)
    return (noise * np.exp(-t / (length / 4))).astype(np.float32)


def tone(freq: float, dur: float, wave: str = "saw", sr: int = SR, attack: float = 0.005,
         decay: float = 0.3, cutoff: Optional[float] = None, detune: float = 0.0) -> np.ndarray:
    n = int(dur * sr)
    t = np.arange(n) / sr
    out = np.zeros(n)
    for d in ([0.0] if detune == 0 else [-detune, 0.0, detune]):
        f = freq * (1 + d)
        ph = (f * t) % 1.0
        if wave == "saw":
            out += 2 * ph - 1
        elif wave == "square":
            out += np.where(ph < 0.5, 1.0, -1.0)
        elif wave == "tri":
            out += 4 * np.abs(ph - 0.5) - 1
        else:
            out += np.sin(2 * np.pi * f * t)
    out /= 1 if detune == 0 else 3
    if cutoff:
        out = _lowpass(out, cutoff, sr)
    return (out * _env(n, attack, decay, sr)).astype(np.float32)


def _add(buf: np.ndarray, sig: np.ndarray, at_s: float, gain: float = 1.0) -> None:
    i = int(at_s * SR)
    if i >= len(buf):
        return
    k = min(len(sig), len(buf) - i)
    buf[i:i + k] += gain * sig[:k]


def midi_hz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def click_track(bpm: float, seconds: float, sr: int = SR, offset_s: float = 0.0) -> np.ndarray:
    """A short click (1 ms noise burst + 1 kHz blip) on every beat. Known tempo for tests."""
    out = np.zeros(int(seconds * sr), dtype=np.float32)
    n = int(0.03 * sr)
    t = np.arange(n) / sr
    c = (np.sin(2 * np.pi * 1000 * t) + np.random.default_rng(0).standard_normal(n) * 0.5) * np.exp(-t / 0.006)
    period = 60.0 / bpm
    k = 0
    while offset_s + k * period < seconds:
        _add(out, c.astype(np.float32), offset_s + k * period, 0.6)
        k += 1
    return out


def click_times(bpm: float, seconds: float, offset_s: float = 0.0) -> np.ndarray:
    period = 60.0 / bpm
    return np.arange(offset_s, seconds, period)


# =====================================================================================
# Synthetic songs (demo library + "unknown" tracks for recognition tests)
# =====================================================================================
STYLES = {
    # bpm, root midi note, scale degrees, lead wave, sections (start_s, name)
    "neon_drive": dict(bpm=128, root=45, scale=[0, 3, 5, 7, 10], lead="saw",
                       sections=[(0, "intro"), (7.5, "full"), (22.5, "break"), (30, "drop")]),
    "slow_bloom": dict(bpm=92, root=50, scale=[0, 2, 4, 7, 9], lead="tri",
                       sections=[(0, "intro"), (5.2, "full"), (26, "break"), (31.3, "full")]),
    "breakbeat_140": dict(bpm=140, root=40, scale=[0, 3, 5, 6, 7, 10], lead="square",
                          sections=[(0, "full"), (17.1, "break"), (24, "drop")]),
}


def synth_song(style: str = "neon_drive", seconds: float = 40.0, seed: int = 0,
               bpm: Optional[float] = None) -> np.ndarray:
    """A deterministic synthetic song. Same (style, seconds, seed) -> same samples.

    style "random" makes a track with a random tempo, key and melody (used as an
    "unknown song" that is NOT in the library).
    """
    rng = np.random.default_rng(seed)
    if style == "random":
        cfg = dict(bpm=float(rng.uniform(95, 135)), root=int(rng.integers(38, 50)),
                   scale=[0, 2, 3, 5, 7, 8, 10], lead=str(rng.choice(["saw", "square", "tri"])),
                   sections=[(0, "full"), (seconds * 0.6, "break"), (seconds * 0.75, "drop")])
    else:
        cfg = dict(STYLES[style])
    if bpm:
        cfg["bpm"] = bpm
    beat = 60.0 / cfg["bpm"]
    root, scale = cfg["root"], cfg["scale"]
    out = np.zeros(int(seconds * SR) + SR, dtype=np.float64)

    # each song gets its own drum tuning, as real tracks do
    K = kick(f_end=float(rng.uniform(40, 60)), sweep=float(rng.uniform(80, 140)),
             decay=float(rng.uniform(0.12, 0.25)), seed=seed + 1)
    S = snare(seed=seed + 2)
    H = hat(seed=seed + 3)
    OH = hat(length=0.2, seed=seed + 4)

    def section_at(t):
        name = cfg["sections"][0][1]
        for s, nm in cfg["sections"]:
            if t >= s:
                name = nm
        return name

    # chord progression (scale-degree roots), 1 chord per bar
    prog = [0, 3, 4, 2] if seed % 2 == 0 else [0, 5, 3, 4]
    melody = rng.integers(0, len(scale), size=64)
    n_beats = int(seconds / beat) + 1
    for b in range(n_beats):
        t = b * beat
        sec = section_at(t)
        bar = b // 4
        pos = b % 4
        deg = prog[bar % len(prog)] % len(scale)
        chord_root = root + scale[deg]
        drums = sec in ("full", "drop", "intro")
        if style == "breakbeat_140" or (style == "random" and seed % 3 == 0):
            if drums:
                if pos in (0, 2):
                    _add(out, K, t, 0.9)
                if pos == 2:
                    _add(out, K, t + beat * 0.5, 0.45)   # ghost kick on the "and" of 3
                if pos in (1, 3):
                    _add(out, S, t, 0.6)
                for s16 in range(4):
                    _add(out, H, t + s16 * beat / 4, 0.12 + 0.08 * (s16 % 2 == 0))
        elif style == "slow_bloom":
            if drums:
                if pos in (0, 2):
                    _add(out, K, t, 0.7)
                if pos in (1, 3):
                    _add(out, S, t, 0.4)
                for e in range(2):
                    _add(out, H, t + e * beat / 2, 0.08)
        else:  # four-on-the-floor
            if drums:
                _add(out, K, t, 0.95)
                _add(out, OH, t + beat / 2, 0.15)
                if pos in (1, 3) and sec != "intro":
                    _add(out, S, t, 0.35)
        # bass line on off-beats (not in breaks / intro)
        if sec in ("full", "drop"):
            bn = tone(midi_hz(chord_root - 12), beat * 0.45, "saw", cutoff=400, decay=0.15)
            _add(out, bn, t + beat / 2, 0.35)
        # pad: whole bar, every section
        if pos == 0:
            for iv in (0, 3 if 3 in scale else 4, 7):
                pad = tone(midi_hz(chord_root + 12 + iv), beat * 4, "saw", attack=0.3,
                           decay=beat * 3, cutoff=1500, detune=0.004)
                _add(out, pad, t, 0.07 if sec != "break" else 0.11)
        # lead melody, 8th notes in drop / full
        if sec in ("drop", "full") or (sec == "break" and pos % 2 == 0):
            for e in range(2):
                m = root + 24 + scale[melody[(b * 2 + e) % len(melody)]]
                ln = tone(midi_hz(m), beat * 0.4, cfg["lead"], cutoff=4000, decay=0.12)
                _add(out, ln, t + e * beat / 2, 0.10 if sec != "break" else 0.07)
    out = out[: int(seconds * SR)]
    peak = np.max(np.abs(out)) + 1e-9
    return (0.8 * out / peak).astype(np.float32)


# =====================================================================================
# Feature-stream fakes
# =====================================================================================
class ReferenceAnalyzer:
    """Minimal, independent feature extractor (hop 1024, Hann 2048). NOT M1's analyser:
    no AGC, fixed dB scaling. Exists so M3/M5 tests do not depend on M1."""

    EDGES = [(20, 60), (60, 250), (250, 500), (500, 2000), (2000, 4000), (4000, 16000)]

    def __init__(self, sr: int = SR):
        self.sr = sr
        self.win = np.hanning(2 * BLOCK_SIZE)
        self.freqs = np.fft.rfftfreq(2 * BLOCK_SIZE, 1 / sr)
        self.bins = [np.where((self.freqs >= lo) & (self.freqs < hi))[0] for lo, hi in self.EDGES]
        self.buf = np.zeros(2 * BLOCK_SIZE)
        self.prev = None

    def process(self, block: np.ndarray, t: float) -> AudioFrame:
        n = len(block)
        self.buf[:-n] = self.buf[n:]
        self.buf[-n:] = block
        mag = np.abs(np.fft.rfft(self.buf * self.win)) * 2 / self.win.sum()
        lm = np.log1p(1000 * mag)
        flux = 0.0 if self.prev is None else float(np.maximum(lm - self.prev, 0).mean())
        self.prev = lm
        bands = {}
        for name, b in zip(BAND_NAMES, self.bins):
            db = 10 * np.log10((mag[b] ** 2).sum() + 1e-12)
            bands[name] = float(np.clip((db + 60) / 60, 0, 1))
        tot = mag.sum()
        return AudioFrame(t=t, samples=block.astype(np.float32), rms=float(np.sqrt(np.mean(block ** 2))),
                          bands=bands, spectrum=mag,
                          centroid_hz=float((self.freqs * mag).sum() / tot) if tot > 1e-9 else 0.0,
                          flux=flux)


def blocks(x: np.ndarray) -> Iterable[tuple[float, np.ndarray]]:
    """Split samples into (t, block) pairs of BLOCK_SIZE (last partial block dropped)."""
    for i in range(0, len(x) - BLOCK_SIZE + 1, BLOCK_SIZE):
        yield i / SR, x[i:i + BLOCK_SIZE]


def audio_frames_from_samples(x: np.ndarray) -> list[AudioFrame]:
    an = ReferenceAnalyzer()
    return [an.process(b, t) for t, b in blocks(x)]


def fake_audio_frames(bpm: float = 128.0, seconds: float = 20.0, noise: float = 0.02,
                      seed: int = 0) -> list[AudioFrame]:
    """AudioFrames without any audio: flux and bass spike on each beat, decay between."""
    rng = np.random.default_rng(seed)
    period = 60.0 / bpm
    out = []
    n = int(seconds / TICK)
    for i in range(n):
        t = i * TICK
        ph = (t % period) / period
        hit = math.exp(-ph * period / 0.05)
        on_beat = ph * period < TICK
        flux = (0.5 if on_beat else 0.0) + abs(rng.normal(0, noise))
        bass = 0.2 + 0.8 * hit
        bands = {"sub": bass, "bass": bass, "low_mid": 0.4, "mid": 0.5,
                 "high_mid": 0.3 + 0.2 * rng.random(), "high": 0.3 + 0.3 * rng.random()}
        out.append(AudioFrame(t=t, samples=np.zeros(BLOCK_SIZE, np.float32), rms=0.1 + 0.2 * hit,
                              bands=bands, centroid_hz=1500 + 500 * rng.random(), flux=flux))
    return out


def fake_rhythm_states(bpm: float = 128.0, seconds: float = 20.0, drop_at: Optional[float] = None,
                       locked_after: float = 0.0) -> list[RhythmState]:
    period = 60.0 / bpm
    out = []
    last_beat = -1
    for i in range(int(seconds / TICK)):
        t = i * TICK
        k = int(t / period)
        beat = k != last_beat
        last_beat = k
        locked = t >= locked_after
        drop = drop_at is not None and abs(t - drop_at) < TICK / 2
        out.append(RhythmState(t=t, bpm=bpm if locked else 0.0, beat=beat and locked,
                               beat_phase=(t % period) / period if locked else 0.0,
                               onset=0.9 if beat else 0.0, energy_trend=0.0, drop=drop,
                               confidence=0.8 if locked else 0.0))
    return out


def fake_music_contexts(script: list[tuple[float, Optional[str], float]], seconds: float,
                        valence: Optional[float] = None, arousal: Optional[float] = None) -> list[MusicContext]:
    """script: [(t_start, song_id, confidence), ...] - each entry holds until the next."""
    out = []
    for i in range(int(seconds / TICK)):
        t = i * TICK
        sid, conf = None, 0.0
        for ts, s, c in script:
            if t >= ts:
                sid, conf = s, c
        out.append(MusicContext(t=t, song_id=sid, song_confidence=conf, valence=valence, arousal=arousal))
    return out


def fake_light_intent(n: int = 8, t: float = 0.0) -> LightIntent:
    import colorsys

    fx = []
    for i in range(n):
        r, g, b = colorsys.hsv_to_rgb((i / n + t * 0.1) % 1.0, 1.0, 1.0)
        fx.append(FixtureIntent(rgb=(r, g, b), dimmer=1.0, strobe=0.0))
    return LightIntent(t=t, fixtures=fx, source="fake")
