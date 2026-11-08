"""M1 feature extraction: one block of samples in, one AudioFrame out.

Steps per block (1024 samples, ~23 ms):
  1. Slide the block into a 2048-sample window (50 % overlap) and apply a Hann window
     (a smooth taper that stops the block edges smearing energy across the spectrum).
  2. FFT -> magnitude spectrum, scaled so a full-scale sine reads 1.0 in its bin.
  3. Six band energies in dB, then adaptive normalisation (AGC) to 0..1 per band.
  4. Spectral centroid (the "centre of mass" of the spectrum, in Hz = brightness).
  5. Spectral flux on a log-compressed spectrum (how much louder each bin got since the
     last block; only increases count, so it spikes on drum hits). M3 uses this for onsets.

See decisions/104-m1-features-and-agc.md for why each choice was made.
"""
from __future__ import annotations

import numpy as np

from lumasync.contract import BLOCK_SIZE, SAMPLE_RATE, AudioFrame

# name, low Hz, high Hz. Edges follow common live-sound practice (sub / kick / body / vocals / presence / air).
BANDS: list[tuple[str, float, float]] = [
    ("sub", 20, 60),
    ("bass", 60, 250),
    ("low_mid", 250, 500),
    ("mid", 500, 2000),
    ("high_mid", 2000, 4000),
    ("high", 4000, 16000),
]
BAND_NAMES = [b[0] for b in BANDS]


class AudioAnalyzer:
    """Stateful: keeps the previous half-window, the previous spectrum and the AGC trackers."""

    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        block_size: int = BLOCK_SIZE,
        fft_size: int = 2048,
        agc_release_db_per_s: float = 1.5,   # how fast a band's "loudest recently" level falls
        floor_rise_db_per_s: float = 0.5,    # how fast a band's "quiet level" creeps up
        min_range_db: float = 24.0,          # never map fewer than this many dB onto 0..1
        min_peak_db: float = -50.0,          # AGC never treats anything quieter than this as "loud"
        gate_db: float = -70.0,              # block RMS below this (dBFS) = silence -> bands 0
        flux_compression: float = 1000.0,    # log(1 + C*|X|) compression before flux
    ):
        self.sr = sample_rate
        self.n = block_size
        self.fft_size = fft_size
        self.window = np.hanning(fft_size).astype(np.float32)
        self.scale = 2.0 / self.window.sum()
        self.freqs = np.fft.rfftfreq(fft_size, 1.0 / sample_rate)
        self.band_bins = [
            np.where((self.freqs >= lo) & (self.freqs < hi))[0] for _, lo, hi in BANDS
        ]
        self.agc_release = agc_release_db_per_s
        self.floor_rise = floor_rise_db_per_s
        self.min_range = min_range_db
        self.min_peak = min_peak_db
        self.gate_db = gate_db
        self.flux_c = flux_compression
        self.dt = block_size / sample_rate
        self.reset()

    def reset(self) -> None:
        self.buf = np.zeros(self.fft_size, dtype=np.float32)
        self.prev_log = None
        self.peak_db = np.full(len(BANDS), self.min_peak)
        self.floor_db = np.full(len(BANDS), -80.0)

    def process(self, samples: np.ndarray, t: float) -> AudioFrame:
        x = np.asarray(samples, dtype=np.float32).reshape(-1)
        n = len(x)
        self.buf[:-n] = self.buf[n:]
        self.buf[-n:] = x

        mag = np.abs(np.fft.rfft(self.buf * self.window)) * self.scale
        power = mag * mag

        rms = float(np.sqrt(np.mean(x * x))) if n else 0.0
        rms_db = 20 * np.log10(rms + 1e-9)

        band_db = np.array([10 * np.log10(power[b].sum() + 1e-12) for b in self.band_bins])
        bands = self._agc(band_db, gated=rms_db < self.gate_db)

        total = mag.sum()
        centroid = float((self.freqs * mag).sum() / total) if total > 1e-6 else 0.0

        log_mag = np.log1p(self.flux_c * mag)
        if self.prev_log is None:
            flux = 0.0
        else:
            diff = log_mag - self.prev_log
            flux = float(np.maximum(diff, 0.0).mean())
        self.prev_log = log_mag

        return AudioFrame(
            t=t,
            samples=x,
            sample_rate=self.sr,
            rms=min(1.0, rms),
            bands={name: float(v) for name, v in zip(BAND_NAMES, bands)},
            spectrum=mag,
            centroid_hz=centroid,
            flux=flux,
        )

    def _agc(self, band_db: np.ndarray, gated: bool) -> np.ndarray:
        """Adaptive normalisation: map each band between its recent quiet level and recent peak.

        peak: jumps up instantly, falls slowly (agc_release dB/s), never below min_peak_db.
        floor: drops quickly toward quiet moments, rises slowly (floor_rise dB/s).
        The window is at least min_range_db wide so steady noise is not blown up to full scale.
        """
        dt = self.dt
        if not gated:
            self.peak_db = np.maximum(band_db, self.peak_db - self.agc_release * dt)
            self.peak_db = np.maximum(self.peak_db, self.min_peak)
            falling = band_db < self.floor_db
            self.floor_db = np.where(
                falling,
                self.floor_db + 0.3 * (band_db - self.floor_db),
                self.floor_db + self.floor_rise * dt,
            )
            self.floor_db = np.minimum(self.floor_db, self.peak_db - self.min_range)
        if gated:
            return np.zeros(len(band_db))
        rng = np.maximum(self.peak_db - self.floor_db, self.min_range)
        lo = self.peak_db - rng
        return np.clip((band_db - lo) / rng, 0.0, 1.0)

    def status(self) -> dict:
        return {
            "fft_size": self.fft_size,
            "agc_peak_db": [round(float(v), 1) for v in self.peak_db],
        }
