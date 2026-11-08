"""M5 mood estimate: PLACEHOLDER HEURISTIC, not machine learning.

This exists only so the rest of the chain has a valence/arousal signal to use and show.
It is meant to be REPLACED by a trained model (planned: regression on the DEAM dataset,
"Database for Emotional Analysis in Music", which has per-second valence/arousal labels).
Keep the same interface: `process(frame) -> (valence, arousal)`, each -1..1 or None.

What the heuristic does (all smoothed over ~5 s, because mood changes slowly):
  arousal (calm .. intense): louder, busier (more spectral flux) and brighter (higher centroid)
                             music reads as more intense. This is a well-known correlation.
  valence (sad .. happy):    brighter timbre and a busier high end read as "happier". This is a
                             weak correlation; real valence needs harmony (major/minor) and a
                             trained model. Treat this number as a demo signal only.
See decisions/110-m5-mood-placeholder.md.
"""
from __future__ import annotations

import math
from typing import Optional

from lumasync.contract import BLOCK_SIZE, SAMPLE_RATE, AudioFrame

IS_PLACEHOLDER = True


class MoodEstimator:
    label = "placeholder heuristic (replace with trained DEAM model)"

    def __init__(self, tau_s: float = 5.0, frame_rate: float = SAMPLE_RATE / BLOCK_SIZE):
        self.a = 1.0 - math.exp(-1.0 / (tau_s * frame_rate))
        self.reset()

    def reset(self) -> None:
        self.level = -60.0
        self.flux = 0.0
        self.centroid = 1500.0
        self.high = 0.0
        self.active = 0

    def process(self, frame: AudioFrame) -> tuple[Optional[float], Optional[float]]:
        lvl = 20 * math.log10(frame.rms + 1e-9)
        if lvl < -55:  # silence: no estimate rather than a made-up one
            self.active = max(0, self.active - 2)
            if self.active == 0:
                return None, None
        else:
            self.active = min(self.active + 1, 1000)
        a = self.a
        self.level += a * (max(lvl, -60) - self.level)
        self.flux += a * (frame.flux - self.flux)
        self.centroid += a * (frame.centroid_hz - self.centroid)
        self.high += a * (frame.bands.get("high", 0.0) - self.high)
        if self.active < 40:  # under ~1 s of sound: not enough to say anything
            return None, None
        loud = (self.level + 40) / 30            # -40 dBFS -> 0, -10 dBFS -> 1
        busy = math.tanh(self.flux * 8)
        bright = math.tanh((self.centroid - 1500) / 1500)
        arousal = math.tanh(1.2 * (0.5 * loud + 0.35 * busy + 0.15 * bright) * 2 - 1.0)
        valence = math.tanh(0.8 * bright + 0.4 * (self.high - 0.5))
        return round(valence, 3), round(arousal, 3)
