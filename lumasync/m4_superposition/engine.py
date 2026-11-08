"""M4 Superposition engine: combines every layer into one LightIntent per tick.

Order of operations (each step can only use what the steps above produced):

  1. Song layer      SongSelector picks the active preset (recognition with hysteresis, or the
                     manual pick); PresetLayer fades its parameters in/out.       [layers.py]
  2. Base layer      The reactive show from audio + rhythm. ALWAYS runs, so a mic alone is a
                     full show. A missing input counts as zero, never as an error.
  3. Modulation      The preset steers the base layer, it does not replace it:
                       palette = OKLab blend(house palette, preset palette, w)
                       depth   = reactivity x energy factor (energy 0.5 = neutral)
                     w = preset weight = fade envelope x blend (per-song blend, else live slider).
  4. Look            pulse / bands / chase, or auto (picks by section). Looks crossfade.
  5. Accents         software "strobe" hits on drops / big onsets, only if strobe is enabled.
  6. Live controls   master (scales), blackout (snaps to dark; fades back in over 0.5 s).
  7. SAFETY CAP      max 3 flashes / s per fixture and for the rig. Last step: nothing after it
                     can raise brightness, and nothing before it can get around it. [safety.py]

FixtureIntent.strobe is always 0: hardware strobe rates are unmeasured, so all strobe-like
effects are made in software (step 5) where step 7 can see and cap them.

Decision records: 111 (blending model), 112 (colour space), 113 (song state), 114 (safety cap),
115 (latency budget), 116 (looks).
"""
from __future__ import annotations

import math
from typing import Optional

import numpy as np

from lumasync.contract import (
    AudioFrame,
    FixtureIntent,
    LightIntent,
    LiveControls,
    MusicContext,
    RhythmState,
    SongPreset,
)

from .colour import fixture_colour, lerp, oklch_to_oklab, palette_at, srgb_to_oklab
from .layers import PresetLayer, SongSelector, smoothstep
from .safety import RigFlashLimiter

LOOKS = ("auto", "pulse", "bands", "chase")
BAND_ORDER = ["sub", "bass", "low_mid", "mid", "high_mid", "high"]
WHITE = srgb_to_oklab(np.ones(3))


def _ema(prev: float, x: float, tau: float, dt: float) -> float:
    return prev + (1 - math.exp(-dt / tau)) * (x - prev)


class SuperpositionEngine:
    def __init__(
        self,
        n_fixtures: int = 8,
        presets: Optional[dict[str, SongPreset]] = None,
        lead_s: float = 0.04,
        idle_level: float = 0.55,
        floor_level: float = 0.06,
    ):
        self.n = n_fixtures
        self.presets: dict[str, SongPreset] = dict(presets or {})
        self.lead_s = lead_s            # fire beat pulses this early to hide output latency (115)
        self.idle = idle_level          # brightness when reactivity = 0 (static wash)
        self.floor = floor_level        # lowest brightness while reacting (never fully dark)
        self.reset()

    # ------------------------------------------------------------------ setup
    def reset(self) -> None:
        self.selector = SongSelector()
        self.preset_layer = PresetLayer()
        self.limiter = RigFlashLimiter(self.n)
        self.t_prev: Optional[float] = None
        self.beats = 0
        self.onsets = 0
        self.last_onset_t = -1e9
        self.onset_env = 0.0
        self.band_s = np.zeros(len(BAND_ORDER))
        self.last_drop_t = -1e9
        self.trend = 0.0
        self.look = "pulse"
        self.look_prev: Optional[str] = None
        self.look_t0 = -1e9
        self.look_fade = 0.8
        self.accent = 0.0
        self.accents = 0
        self.blackout_env = 1.0
        self.status_info: dict = {}

    def set_presets(self, presets: dict[str, SongPreset]) -> None:
        self.presets = dict(presets)

    # ------------------------------------------------------------------ main
    def process(self, audio: AudioFrame, rhythm: Optional[RhythmState], music: Optional[MusicContext],
                controls: LiveControls) -> LightIntent:
        t = audio.t
        dt = 0.0232 if self.t_prev is None else float(np.clip(t - self.t_prev, 1e-4, 0.1))
        self.t_prev = t
        rhythm = rhythm or RhythmState(t=t)            # missing input = zero, never an error
        music = music or MusicContext(t=t)

        # ---- 1. song layer
        goal, reason = self.selector.update(t, music, controls.manual_song_id, set(self.presets))
        preset = self.presets.get(goal) if goal else None
        locked = rhythm.bpm > 0
        self.preset_layer.update(t, goal, preset, reason, rhythm.beat, rhythm.drop, locked)
        w = self.preset_layer.weight(controls.preset_blend)

        # ---- 2. base-layer drive signals
        if rhythm.beat:
            self.beats += 1
        if rhythm.onset > 0:
            self.onsets += 1
            self.last_onset_t = t
        self.onset_env = max(rhythm.onset, self.onset_env * math.exp(-dt / 0.15))
        bands = np.array([audio.bands.get(k, 0.0) for k in BAND_ORDER])
        rising = bands > self.band_s
        k_att, k_rel = 1 - math.exp(-dt / 0.02), 1 - math.exp(-dt / 0.18)
        self.band_s += np.where(rising, k_att, k_rel) * (bands - self.band_s)
        if rhythm.drop:
            self.last_drop_t = t
        self.trend = _ema(self.trend, rhythm.energy_trend, 1.0, dt)
        pulse = self._pulse(rhythm, locked)

        # ---- 3. modulation by the preset
        house = self._house_palette(t, music)
        palette = lerp(house, self.preset_layer.palette, w)
        energy = lerp(0.5, self.preset_layer.energy, w)
        depth = float(np.clip(controls.reactivity * (0.4 + 1.2 * energy), 0.0, 1.0))

        # ---- 4. look (with crossfade between looks)
        want = controls.look if controls.look in LOOKS else "auto"
        target = self._auto_look(t, locked, rhythm.bpm) if want == "auto" else want
        if target != self.look and (rhythm.beat or not locked or want != "auto"):
            self.look_prev, self.look, self.look_t0 = self.look, target, t
        cols, drive = self._render(self.look, palette, pulse, rhythm, locked, energy)
        fade = smoothstep((t - self.look_t0) / self.look_fade)
        if self.look_prev and fade < 1.0:
            c0, d0 = self._render(self.look_prev, palette, pulse, rhythm, locked, energy)
            cols, drive = lerp(c0, cols, fade), lerp(d0, drive, fade)
        level = lerp(self.idle, self.floor + (1 - self.floor) * drive, depth)

        # ---- 5. software strobe accents (only if permitted)
        song_active = self.preset_layer.song_id is not None and w > 0.05
        strobe_ok = controls.strobe_enabled and (self.preset_layer.strobe if song_active else True)
        if strobe_ok and (rhythm.drop or (rhythm.onset > 0.85 and energy > 0.6 and self.band_s[1] > 0.7)):
            self.accent = 1.0
            self.accents += 1
        self.accent *= math.exp(-dt / 0.05)
        if self.accent > 0.02 and strobe_ok:
            cols = lerp(cols, np.repeat(WHITE[None, :], self.n, axis=0), self.accent)
            level = np.maximum(level, self.accent)

        # ---- 6. live controls
        if controls.blackout:
            self.blackout_env = 0.0                         # snap: an operator wants dark NOW
        else:
            self.blackout_env = min(1.0, self.blackout_env + dt / 0.5)
        level = level * float(np.clip(controls.master, 0, 1)) * self.blackout_env

        # ---- 7. safety cap (always last)
        level = self.limiter.step(t, np.clip(level, 0, 1))

        fixtures = [
            FixtureIntent(rgb=tuple(float(c) for c in fixture_colour(cols[i])), dimmer=float(level[i]), strobe=0.0)
            for i in range(self.n)
        ]
        layers = ["base:" + self.look]
        if w > 0.01:
            layers.append(f"preset:{self.preset_layer.song_id}@{w:.2f}")
        if self.accent > 0.02:
            layers.append("accent")
        if controls.blackout:
            layers.append("blackout")
        if self.limiter.engaged_last_s:
            layers.append("SAFETY-CAP")
        self.status_info = {
            "look": self.look,
            "look_mode": want,
            "song_goal": goal,
            "song_state": reason,
            "candidate": self.selector.candidate,
            "preset_song": self.preset_layer.song_id,
            "preset_weight": round(w, 2),
            "preset_env": round(self.preset_layer.env, 2),
            "transition": self.preset_layer.last_transition,
            "energy": round(float(energy), 2),
            "depth": round(depth, 2),
            "strobe_permitted": bool(strobe_ok),
            "accents": self.accents,
            "safety_cap_engaged": self.limiter.engaged_last_s,
            "lead_ms": round(self.lead_s * 1000),
            "palette": [self._hex(c) for c in palette],
        }
        return LightIntent(t=t, fixtures=fixtures, source=" + ".join(layers))

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _hex(lab) -> str:
        from .colour import srgb_to_hex

        return srgb_to_hex(fixture_colour(lab))

    def _pulse(self, rhythm: RhythmState, locked: bool) -> float:
        """0..1 beat envelope. Locked: from the beat phase, shifted early by lead_s.
        Not locked: follow onsets instead (still reacts, just not predictively)."""
        if not locked:
            return self.onset_env
        period = 60.0 / rhythm.bpm
        every = 2 if rhythm.bpm > 165 else 1          # very fast tempo: pulse every other beat (cap)
        ph = (rhythm.beat_phase + self.lead_s / period) % 1.0
        if every == 2:
            ph = ((self.beats % 2) + ph) / 2
        return math.exp(-ph * 4.0)

    def _house_palette(self, t: float, music: MusicContext) -> np.ndarray:
        """The default palette when no preset is active: slow hue drift (one turn / 2 min),
        nudged warm/cool by valence and more/less saturated by arousal when mood exists."""
        hue = (t * 3.0) % 360
        chroma = 0.15
        if music.valence is not None:
            warm, cool = 30.0, 250.0
            target = warm if music.valence > 0 else cool
            d = ((target - hue + 180) % 360) - 180
            hue = hue + d * min(abs(music.valence), 1.0) * 0.5
        if music.arousal is not None:
            chroma = 0.11 + 0.06 * (music.arousal + 1) / 2
        return np.array([
            oklch_to_oklab(0.70, chroma, hue),
            oklch_to_oklab(0.66, chroma, hue + 50),
            oklch_to_oklab(0.72, chroma * 0.9, hue + 180),
        ])

    def _auto_look(self, t: float, locked: bool, bpm: float) -> str:
        """Pick a look from the music's state. Holds each choice >= 4 s to avoid flapping."""
        if t - self.look_t0 < 4.0:
            return self.look
        if not locked:
            return "bands"
        if t - self.last_drop_t < 16 * 60.0 / max(bpm, 60):
            return "chase"
        if self.trend < -0.25:
            return "bands"
        return "pulse"

    def _render(self, look: str, palette: np.ndarray, pulse: float, rhythm: RhythmState,
                locked: bool, energy: float) -> tuple[np.ndarray, np.ndarray]:
        """-> (colours (n,3) OKLab, drive (n,) 0..1)."""
        n = self.n
        bass = float(max(self.band_s[0], self.band_s[1]))
        k = len(palette)
        if look == "bands":
            # centre fixtures = low bands, outer fixtures = high bands (mirrored)
            x = np.abs(np.arange(n) - (n - 1) / 2) / max((n - 1) / 2, 1)
            vals = np.interp(x * (len(BAND_ORDER) - 1), np.arange(len(BAND_ORDER)), self.band_s)
            cols = np.array([palette_at(palette, xi) for xi in x])
            return cols, np.clip(vals, 0, 1)
        if look == "chase":
            if locked:
                steps = 2 if energy > 0.75 and rhythm.bpm < 140 else 1
                pos = ((self.beats + rhythm.beat_phase) * steps) % n
                cidx = self.beats
            else:
                pos = float(self.onsets % n)
                cidx = self.onsets
            d = np.abs(np.arange(n) - pos)
            d = np.minimum(d, n - d)
            drive = np.clip(1 - d / 1.3, 0, 1) ** 2 * 0.85 + 0.15 * bass
            cols = np.array([palette[(i + cidx) % k] for i in range(n)])
            return cols, np.clip(drive, 0, 1)
        # pulse (default)
        bar = self.beats // 4
        cols = np.array([palette[(bar + (i % 2)) % k] for i in range(n)])
        drive = np.full(n, 0.75 * pulse + 0.25 * bass)
        return cols, np.clip(drive, 0, 1)

    def status(self) -> dict:
        return dict(self.status_info)
