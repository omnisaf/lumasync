r"""The feature stream: the ONLY thing modules share.

Every module reads and writes these types and nothing else from other modules.
That is what lets five people build in parallel: you can test your module
against fake or recorded data in this format without waiting for anybody.

Data flow (one "tick" per audio block, ~43 per second at 1024 samples / 44.1 kHz):

    microphone / line-in
          |
      [M1 Audio Signal Processing]  -> AudioFrame -------------------.
          |                \                                      |
      [M3 Rhythm & Tempo]   [M5 Music Recognition & Mood]         | (bands, rms)
          |  RhythmState         |  MusicContext                  |
          \_______________________/_______________________________/
                     |
      [M4 Superposition Engine]  (+ live controls, + song presets from the library)
                     |  LightIntent
      [M2 Lighting Control & Output]  -> DMX cable / virtual preview / (later) sACN, LED strip

Changing anything in this file changes every module.
Rule: changes go through a pull request that every module owner approves.
Adding a NEW optional field (with a default) is cheap. Renaming or removing one is not.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

CONTRACT_VERSION = "0.1.0"

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024  # samples per tick -> ~23 ms


# ---------- M1 -> M3, M5 ----------
@dataclass
class AudioFrame:
    t: float                    # seconds since the stream started
    samples: np.ndarray         # mono float32, length BLOCK_SIZE, range -1..1
    sample_rate: int = SAMPLE_RATE
    rms: float = 0.0            # loudness of this block, 0..1
    bands: dict[str, float] = field(default_factory=dict)
    # normalised 0..1 energy per band, keys: "sub", "bass", "low_mid", "mid", "high_mid", "high"
    spectrum: Optional[np.ndarray] = None   # magnitude spectrum (rfft), for modules that want it
    centroid_hz: float = 0.0    # spectral centroid = "brightness" of the sound
    flux: float = 0.0           # spectral flux = how much the spectrum changed since last block


# ---------- M3 -> M4 ----------
@dataclass
class RhythmState:
    t: float
    bpm: float = 0.0            # 0 = not locked yet
    beat: bool = False          # True on the tick a beat lands
    beat_phase: float = 0.0     # 0..1 position between beats (0 = on the beat)
    onset: float = 0.0          # transient strength this tick, 0..1
    energy_trend: float = 0.0   # -1..1, falling vs rising energy (build-ups / drops)
    drop: bool = False          # True on the tick a drop is detected
    confidence: float = 0.0     # 0..1, how sure the tempo estimate is


# ---------- M5 -> M4 ----------
@dataclass
class MusicContext:
    t: float
    song_id: Optional[str] = None       # id in the song library, None = unknown song
    song_confidence: float = 0.0        # 0..1
    valence: Optional[float] = None     # -1..1 (sad .. happy); None = no estimate
    arousal: Optional[float] = None     # -1..1 (calm .. intense); None = no estimate


# ---------- live controls (UI / MIDI later) -> M4 ----------
@dataclass
class LiveControls:
    master: float = 1.0          # 0..1 overall brightness
    reactivity: float = 0.7      # 0..1 how hard lights follow the audio
    preset_blend: float = 0.8    # 0..1 how much a recognised song's preset overrides the live show
    strobe_enabled: bool = False
    blackout: bool = False
    manual_song_id: Optional[str] = None  # manual "this song is playing" override (backup to recognition)
    look: str = "auto"           # base-layer look: "auto", "pulse", "bands", "chase" (decisions/120)


# ---------- M4 -> M2 ----------
@dataclass
class FixtureIntent:
    rgb: tuple[float, float, float] = (0.0, 0.0, 0.0)  # 0..1 each
    dimmer: float = 0.0          # 0..1
    strobe: float = 0.0          # 0 = off, 0..1 = strobe rate


@dataclass
class LightIntent:
    """Rig-agnostic: says WHAT the light should look like, never which DMX channel.
    M2 maps this to real channels using a fixture patch file."""
    t: float
    fixtures: list[FixtureIntent] = field(default_factory=list)  # one per logical fixture / group
    source: str = ""             # human-readable: which layers produced this (for the UI + debugging)


# ---------- the song library (pre-planned layer) ----------
@dataclass
class SongPreset:
    song_id: str
    title: str
    artist: str = ""
    palette: list[str] = field(default_factory=lambda: ["#ff0040", "#4000ff"])  # 2-3 hex colours
    energy: float = 0.7          # 0..1 how hard lights react for this song
    strobe: bool = False
    blend: Optional[float] = None  # per-song override of LiveControls.preset_blend; None = use live value
    audio_file: Optional[str] = None  # path used to build the fingerprint
