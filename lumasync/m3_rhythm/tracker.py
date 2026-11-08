"""M3 rhythm: AudioFrame in, RhythmState out. Standard, simple algorithms, all causal
(they only look at the past, so they add no look-ahead delay).

1. Onsets (a drum hit or note start). The onset detection function (ODF) is M1's spectral flux.
   A tick is an onset when the flux is above an adaptive threshold
   (median + k * mean absolute deviation of the last 0.5 s) and at least 100 ms after the
   previous onset. The median tracks the local "busy-ness", so quiet and loud passages both work.
   -> decisions/105-m3-onset-detection.md

2. Tempo. Every 0.5 s, autocorrelate the last 8 s of the ODF (compare the signal with a delayed
   copy of itself; it lines up best when the delay equals the beat period). Score each period in
   70-180 BPM with a gentle preference for ~120 BPM (a tempo "prior", to pick 128 over 64 or 256),
   refine to sub-frame precision with parabolic interpolation on 2x/4x the period, then smooth.
   -> decisions/106-m3-tempo-and-beat-tracking.md

3. Beat phase. Slide a comb (a pulse train at the beat period) over the recent ODF; the offset
   with the most energy is where the beats are. A phase-locked loop (PLL: a predictor that keeps
   ticking at the tempo and is nudged toward each new measurement) emits `beat` on the predicted
   tick, so beats keep coming through short quiet gaps.

4. energy_trend and drop. Fast vs slow running averages of loudness; a drop is a sudden return
   of loudness and bass after a quieter section.
   -> decisions/107-m3-energy-trend-and-drop.md
"""
from __future__ import annotations

import math
from collections import deque

import numpy as np

from lumasync.contract import BLOCK_SIZE, SAMPLE_RATE, AudioFrame, RhythmState


def _ema_coef(tau_s: float, dt: float) -> float:
    """Smoothing coefficient for an exponential moving average with time constant tau."""
    return 1.0 - math.exp(-dt / tau_s)


def _parabolic(y: np.ndarray, i: int) -> float:
    """Sub-sample peak position from the peak bin and its two neighbours."""
    if i <= 0 or i >= len(y) - 1:
        return float(i)
    a, b, c = y[i - 1], y[i], y[i + 1]
    den = a - 2 * b + c
    if den >= 0:  # not a peak shape
        return float(i)
    return i + 0.5 * (a - c) / den


class RhythmTracker:
    def __init__(
        self,
        frame_rate: float = SAMPLE_RATE / BLOCK_SIZE,
        min_bpm: float = 70.0,
        max_bpm: float = 180.0,
        window_s: float = 8.0,
        update_s: float = 0.5,
        min_history_s: float = 4.0,
        prior_bpm: float = 120.0,
        prior_octaves: float = 0.7,
        onset_k: float = 2.5,
        onset_min_gap_s: float = 0.10,
        lock_confidence: float = 0.15,
        pll_gain: float = 0.5,
    ):
        self.fr = frame_rate
        self.dt = 1.0 / frame_rate
        self.min_bpm, self.max_bpm = min_bpm, max_bpm
        self.W = int(round(window_s * frame_rate))
        self.update_every = max(1, int(round(update_s * frame_rate)))
        self.min_history = int(round(min_history_s * frame_rate))
        self.prior_bpm = prior_bpm
        self.prior_oct = prior_octaves
        self.onset_k = onset_k
        self.onset_gap = onset_min_gap_s
        self.lock_conf = lock_confidence
        self.pll_gain = pll_gain
        self._smooth = np.hanning(7)[1:-1] / np.hanning(7)[1:-1].sum()
        self.reset()

    # ------------------------------------------------------------------ state
    def reset(self) -> None:
        self.n = 0
        self.recent = deque(maxlen=max(5, int(0.5 * self.fr)))   # flux, last 0.5 s
        self.env = np.zeros(self.W)                                # ODF history, oldest first
        self.flux_peak = 1e-6
        self.last_onset_t = -1e9
        # tempo
        self.bpm = 0.0
        self.conf = 0.0
        self.raw_history: deque = deque(maxlen=6)
        self.disagree = 0
        self.no_estimate = 0
        # beat PLL
        self.next_beat_t = None
        self.last_beat_t = None
        self.beat_count = 0
        # loudness trackers (dB) and drop detection
        self.lvl_fast = self.lvl_mid = self.lvl_slow = self.lvl_trend_fast = -80.0
        self.bass_fast = self.bass_slow = 0.0
        self.active_s = 0.0
        self.quiet_s = 0.0
        self.last_drop_t = -1e9
        self.drop_count = 0
        self.onset_count = 0

    # ------------------------------------------------------------------ main
    def process(self, frame: AudioFrame) -> RhythmState:
        t = frame.t
        self.n += 1
        flux = float(frame.flux)

        onset = self._onset(t, flux)
        self._tempo_and_phase(t)
        beat, phase = self._beat(t)
        trend, drop = self._energy(t, frame)

        return RhythmState(
            t=t,
            bpm=round(self.bpm, 2),
            beat=beat,
            beat_phase=phase,
            onset=onset,
            energy_trend=trend,
            drop=drop,
            confidence=float(np.clip(self.conf, 0, 1)) if self.bpm > 0 else 0.0,
        )

    # ------------------------------------------------------------------ 1. onsets
    def _onset(self, t: float, flux: float) -> float:
        if len(self.recent) >= 3:
            arr = np.fromiter(self.recent, float)
            med = float(np.median(arr))
            mad = float(np.mean(np.abs(arr - med)))
        else:
            med, mad = flux, 0.0
        thr = med + self.onset_k * mad + 1e-4
        self.flux_peak = max(flux, self.flux_peak * math.exp(-self.dt / 2.0))

        # ODF used for tempo: flux above the local median (half-wave rectified)
        odf = max(0.0, flux - med)
        self.env[:-1] = self.env[1:]
        self.env[-1] = odf
        self.recent.append(flux)

        if flux > thr and (t - self.last_onset_t) >= self.onset_gap and flux > 0.01:
            self.last_onset_t = t
            self.onset_count += 1
            return float(np.clip((flux - thr) / max(self.flux_peak - thr, 1e-6), 0.05, 1.0))
        return 0.0

    # ------------------------------------------------------------------ 2+3. tempo, phase
    def _tempo_and_phase(self, t: float) -> None:
        if self.n < self.min_history or self.n % self.update_every:
            return
        est = self.estimate_tempo(self.env[-min(self.n, self.W):])
        if est is None:
            self.no_estimate += 1
            self.conf *= 0.7
            if self.no_estimate * self.update_every * self.dt > 3.0:  # ~3 s of nothing: unlock
                self.bpm, self.next_beat_t = 0.0, None
                self.raw_history.clear()
            return
        self.no_estimate = 0
        raw_bpm, conf = est
        self.raw_history.append(raw_bpm)
        self.conf = 0.7 * self.conf + 0.3 * conf

        if self.bpm == 0.0:
            if conf >= self.lock_conf and len(self.raw_history) >= 2:
                last2 = list(self.raw_history)[-2:]
                if abs(last2[0] - last2[1]) / last2[1] < 0.03:
                    self.bpm = float(np.mean(last2))
        else:
            ratio = raw_bpm / self.bpm
            if abs(ratio - 1) < 0.04:
                self.bpm += 0.3 * (raw_bpm - self.bpm)
                self.disagree = 0
            elif abs(ratio - 2) < 0.08 or abs(ratio - 0.5) < 0.02:
                # Octave guard: double or half the locked tempo is the same pulse heard at another
                # level (e.g. hi-hat 8th notes). Keep the lock instead of jumping.
                self.disagree = 0
            else:
                self.disagree += 1
                hist = list(self.raw_history)[-3:]
                if self.disagree >= 3 and (max(hist) - min(hist)) / np.mean(hist) < 0.04:
                    self.bpm = float(np.median(hist))   # tempo really changed
                    self.disagree = 0
            if self.conf < self.lock_conf * 0.3:
                self.bpm, self.next_beat_t = 0.0, None

        if self.bpm > 0:
            self._update_phase(t)

    def estimate_tempo(self, env: np.ndarray):
        """(bpm, confidence) from an ODF history, or None if there is no rhythm in it."""
        # Light smoothing (5-frame Hann, ~100 ms) widens the autocorrelation peaks, so a beat
        # period that falls between two whole frames (e.g. 18.46 frames at 140 BPM) is not missed.
        e = np.convolve(env, self._smooth, mode="same")
        e = e - e.mean()
        N = len(e)
        spec = np.fft.rfft(e, 2 * N)
        ac = np.fft.irfft(spec * np.conj(spec))[:N]
        if ac[0] <= 1e-12:
            return None
        ac = ac / ac[0]
        ac = ac * (N / (N - np.arange(N)))  # unbiased: undo the shrink from fewer overlapping samples
        idx = np.arange(N)

        lag_min = 60 * self.fr / self.max_bpm
        lag_max = min(60 * self.fr / self.min_bpm, (N - 2) / 2)
        if lag_max <= lag_min:
            return None
        lags = np.arange(lag_min, lag_max, 0.25)      # fractional lag grid (quarter frame)
        bpms = 60 * self.fr / lags
        prior = np.exp(-0.5 * (np.log2(bpms / self.prior_bpm) / self.prior_oct) ** 2)
        a1 = np.interp(lags, idx, ac)
        a2 = np.interp(2 * lags, idx, ac)
        score = (a1 + 0.5 * a2) * prior               # a true period also lines up at 2x
        L = float(lags[int(np.argmax(score))])
        peak = float(np.interp(L, idx, ac))
        if peak <= 0.02:
            return None
        # Precision: measuring the period at k times its length divides the error by k.
        for k in (4, 3, 2):
            lo, hi = int(round(k * L - k)), int(round(k * L + k)) + 1
            if hi >= N - 1:
                continue
            pk = lo + int(np.argmax(ac[lo:hi]))
            if 0 < pk < N - 1 and ac[pk] > 0.3 * peak and ac[pk] >= ac[pk - 1] and ac[pk] >= ac[pk + 1]:
                L = _parabolic(ac, pk) / k
                break
        return 60 * self.fr / L, float(np.clip(peak, 0, 1))

    def _update_phase(self, t: float) -> None:
        period_f = 60 * self.fr / self.bpm
        period_s = 60 / self.bpm
        e = self.env[-min(self.n, self.W):]
        N = len(e)
        phis = np.arange(0, period_f, 0.25)
        K = max(1, int((N - 1) / period_f))
        ks = np.arange(K)
        pos = (N - 1) - phis[:, None] - ks[None, :] * period_f
        valid = pos >= 0
        vals = np.interp(np.where(valid, pos, 0), np.arange(N), e) * valid
        score = (vals * (0.85 ** ks)[None, :]).sum(axis=1)
        phi = float(phis[int(np.argmax(score))])
        last_beat = t - phi * self.dt
        measured_next = last_beat + period_s
        while measured_next <= t:
            measured_next += period_s
        if self.next_beat_t is None:
            self.next_beat_t = measured_next
            return
        err = measured_next - self.next_beat_t
        err = (err + period_s / 2) % period_s - period_s / 2   # wrap to [-P/2, P/2)
        self.next_beat_t += self.pll_gain * err

    def _beat(self, t: float):
        if self.bpm <= 0 or self.next_beat_t is None:
            return False, 0.0
        period = 60 / self.bpm
        beat = False
        if t + self.dt / 2 >= self.next_beat_t:
            if self.last_beat_t is None or t - self.last_beat_t > 0.5 * period:
                beat = True
                self.last_beat_t = t
                self.beat_count += 1
            self.next_beat_t += period
            while self.next_beat_t < t:  # far behind (e.g. after a stall): resync
                self.next_beat_t += period
        if self.last_beat_t is None:
            return beat, 0.0
        phase = ((t - self.last_beat_t) / period) % 1.0
        return beat, float(phase)

    # ------------------------------------------------------------------ 4. energy, drop
    def _energy(self, t: float, frame: AudioFrame):
        dt = self.dt
        lvl = max(-80.0, 20 * math.log10(frame.rms + 1e-9))
        self.lvl_fast += _ema_coef(0.2, dt) * (lvl - self.lvl_fast)
        self.lvl_trend_fast += _ema_coef(1.5, dt) * (lvl - self.lvl_trend_fast)
        self.lvl_mid += _ema_coef(3.0, dt) * (lvl - self.lvl_mid)
        self.lvl_slow += _ema_coef(8.0, dt) * (lvl - self.lvl_slow)
        bass = max(frame.bands.get("sub", 0.0), frame.bands.get("bass", 0.0))
        self.bass_fast += _ema_coef(0.15, dt) * (bass - self.bass_fast)
        self.bass_slow += _ema_coef(3.0, dt) * (bass - self.bass_slow)

        if lvl > -50:
            self.active_s += dt
            self.quiet_s = 0.0
        else:
            self.quiet_s += dt
            if self.quiet_s > 2.0:
                self.active_s = 0.0

        trend = math.tanh((self.lvl_trend_fast - self.lvl_slow) / 6.0)
        drop = (
            self.active_s > 6.0
            and self.lvl_fast - self.lvl_mid > 3.0
            and self.bass_fast - self.bass_slow > 0.35
            and self.bass_fast > 0.55
            and t - self.last_drop_t > 8.0
        )
        if drop:
            self.last_drop_t = t
            self.drop_count += 1
        return float(trend), bool(drop)

    def status(self) -> dict:
        return {
            "bpm": round(self.bpm, 1),
            "confidence": round(float(self.conf), 2),
            "locked": self.bpm > 0,
            "beats": self.beat_count,
            "onsets": self.onset_count,
            "drops": self.drop_count,
            "raw_bpm": round(self.raw_history[-1], 1) if self.raw_history else None,
        }
