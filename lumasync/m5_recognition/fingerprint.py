"""M5 audio fingerprinting: landmark (peak-pair) hashing, the method behind Shazam
(A. Wang, "An Industrial-Strength Audio Search Algorithm", ISMIR 2003) and the open-source Dejavu.

Idea in plain words:
  1. Make a spectrogram (a picture of which frequencies are loud at each moment).
  2. Keep only the "peaks": points louder than everything near them. Peaks survive noise,
     EQ and a cheap speaker, because they are the loudest things around.
  3. Pair each peak (the "anchor") with a few peaks just after it. Each pair becomes a hash:
     (anchor frequency, target frequency, time gap). Pairs are far more specific than single peaks.
  4. Index: hash -> (song, time of the anchor in the song).
  5. To match a clip: look up its hashes, and for each hit compute
     offset = (time in song) - (time in clip). For the right song, many hits share ONE offset
     (the clip lines up with the song at one position). Random hits scatter over many offsets.
     The score is the size of the biggest same-offset pile, counted in distinct moments of the
     clip (so one chord with many harmonics counts once, not dozens of times).

Parameters (see decisions/108-m5-fingerprint-parameters.md):
  11 025 Hz audio, 1024-point FFT (93 ms), hop 256 (23 ms), peak neighbourhood +-8 frames x +-15 bins,
  peaks above 150 Hz only, up to 30 peaks per second, fan-out 10, time gap 1..63 frames, hash = 9 + 9 + 6 = 24 bits.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

FP_SR = 11025
N_FFT = 1024
HOP = 256
PEAK_T = 8            # neighbourhood half-size in frames
PEAK_F = 15           # neighbourhood half-size in frequency bins
PEAKS_PER_S = 30
MIN_DB_ABOVE_MEDIAN = 10.0
FAN_OUT = 10
DT_MAX = 63           # 6 bits
F_BITS = 9            # bins 0..511
MIN_BIN = 14          # ignore peaks below ~150 Hz: kick drums are near-identical across tracks
STOP_HASH_COUNT = 200  # hashes that appear more often than this in the index carry no information
FRAME_S = HOP / FP_SR


def to_fp_rate(x: np.ndarray, sr: int) -> np.ndarray:
    """Mono float audio at any rate -> FP_SR."""
    from math import gcd

    from scipy.signal import resample_poly

    x = np.asarray(x, dtype=np.float32)
    if x.ndim > 1:
        x = x.mean(axis=1)
    if sr == FP_SR:
        return x
    g = gcd(int(sr), FP_SR)
    return resample_poly(x, FP_SR // g, int(sr) // g).astype(np.float32)


def spectrogram_db(x: np.ndarray) -> np.ndarray:
    """(frames, bins) magnitude in dB. Bins limited to 0..511 (0..5.5 kHz)."""
    if len(x) < N_FFT:
        return np.zeros((0, 2 ** F_BITS))
    frames = np.lib.stride_tricks.sliding_window_view(x, N_FFT)[::HOP]
    win = np.hanning(N_FFT).astype(np.float32)
    mag = np.abs(np.fft.rfft(frames * win, axis=1))[:, : 2 ** F_BITS]
    return 20 * np.log10(mag + 1e-6)


def find_peaks(S: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Local maxima of the spectrogram -> (frame indices, bin indices), sorted by time."""
    from scipy.ndimage import maximum_filter

    if S.size == 0:
        return np.zeros(0, int), np.zeros(0, int)
    mf = maximum_filter(S, size=(2 * PEAK_T + 1, 2 * PEAK_F + 1), mode="constant", cval=-1e9)
    thr = max(np.median(S) + MIN_DB_ABOVE_MEDIAN, S.max() - 70.0)
    mask = (S == mf) & (S > thr)
    mask[:, :MIN_BIN] = False  # ignore kick-drum / rumble region (see MIN_BIN)
    t, f = np.nonzero(mask)
    budget = max(1, int(PEAKS_PER_S * S.shape[0] * FRAME_S))
    if len(t) > budget:
        keep = np.argsort(S[t, f])[-budget:]
        t, f = t[keep], f[keep]
    order = np.lexsort((f, t))
    return t[order], f[order]


def hashes_from_peaks(t: np.ndarray, f: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Pair each anchor with the next FAN_OUT peaks in time. Returns (hashes uint32, anchor frames)."""
    hs, ts = [], []
    for k in range(1, FAN_OUT + 1):
        if len(t) <= k:
            break
        dt = t[k:] - t[:-k]
        ok = (dt >= 1) & (dt <= DT_MAX)
        f1, f2 = f[:-k][ok], f[k:][ok]
        h = (f1.astype(np.uint32) << (F_BITS + 6)) | (f2.astype(np.uint32) << 6) | dt[ok].astype(np.uint32)
        hs.append(h)
        ts.append(t[:-k][ok])
    if not hs:
        return np.zeros(0, np.uint32), np.zeros(0, np.int32)
    return np.concatenate(hs), np.concatenate(ts).astype(np.int32)


def fingerprint(x_fp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Audio already at FP_SR -> (hashes, anchor frames)."""
    t, f = find_peaks(spectrogram_db(x_fp))
    return hashes_from_peaks(t, f)


@dataclass
class MatchResult:
    song_id: Optional[str]
    confidence: float
    offset_s: float = 0.0        # where in the song the clip starts
    score: int = 0               # biggest same-offset pile for the best song
    second: int = 0              # same, for the runner-up song
    query_hashes: int = 0
    scores: dict = field(default_factory=dict)


def confidence_from_scores(best: int, second: int, noise_floor: int = 8, scale: float = 8.0,
                           runner_up_factor: float = 1.5) -> float:
    """Turn raw pile sizes into 0..1.

    The best song's pile must clear BOTH the pile size random coincidences reach (noise_floor)
    and 1.5x the runner-up song's pile. Shared drum samples or a similar tempo can give a wrong
    song a modest pile; requiring a margin over the runner-up keeps those low.
    Calibrated on synthetic tracks in decisions/109-m5-recognition-confidence-and-schedule.md.
    """
    margin = best - max(runner_up_factor * second, noise_floor)
    return float(np.clip(1.0 - np.exp(-margin / scale), 0.0, 1.0)) if margin > 0 else 0.0


class FingerprintIndex:
    """hash -> (song, anchor frame), stored as three sorted numpy arrays (fast, simple, one file)."""

    def __init__(self):
        self.song_ids: list[str] = []
        self.meta: dict[str, dict] = {}
        self.hashes = np.zeros(0, np.uint32)
        self.song_idx = np.zeros(0, np.uint16)
        self.offsets = np.zeros(0, np.int32)

    # ---------------------------------------------------------------- build
    @staticmethod
    def file_signature(path: str) -> dict:
        if not os.path.exists(path):  # in-memory audio (tests)
            return {"file": path, "size": None, "mtime": None}
        st = os.stat(path)
        return {"file": path, "size": st.st_size, "mtime": int(st.st_mtime)}

    def is_current(self, song_id: str, path: Optional[str]) -> bool:
        if not path or song_id not in self.meta or not os.path.exists(path):
            return False
        m, s = self.meta[song_id], self.file_signature(path)
        return m.get("size") == s["size"] and m.get("mtime") == s["mtime"] and m.get("file") == s["file"]

    @classmethod
    def build(cls, songs: list[tuple[str, str]], loader: Callable[[str], tuple[np.ndarray, int]],
              progress: Optional[Callable[[int, int, str], None]] = None) -> "FingerprintIndex":
        """songs: [(song_id, audio_path)]. loader(path) -> (mono samples, sample rate)."""
        idx = cls()
        H, S, O = [], [], []
        for i, (sid, path) in enumerate(songs):
            if progress:
                progress(i, len(songs), sid)
            x, sr = loader(path)
            x = to_fp_rate(x, sr)
            h, t = fingerprint(x)
            idx.song_ids.append(sid)
            idx.meta[sid] = {**cls.file_signature(path), "hashes": int(len(h)),
                             "duration_s": round(len(x) / FP_SR, 1)}
            H.append(h)
            S.append(np.full(len(h), i, np.uint16))
            O.append(t)
        if progress:
            progress(len(songs), len(songs), "")
        if H:
            h, s, o = np.concatenate(H), np.concatenate(S), np.concatenate(O)
            order = np.argsort(h, kind="stable")
            idx.hashes, idx.song_idx, idx.offsets = h[order], s[order], o[order]
        return idx

    # ---------------------------------------------------------------- disk
    def save(self, directory: str) -> None:
        os.makedirs(directory, exist_ok=True)
        np.savez_compressed(os.path.join(directory, "fingerprints.npz"),
                            hashes=self.hashes, song_idx=self.song_idx, offsets=self.offsets)
        with open(os.path.join(directory, "fingerprints.json"), "w") as fh:
            json.dump({"song_ids": self.song_ids, "meta": self.meta,
                       "params": {"sr": FP_SR, "n_fft": N_FFT, "hop": HOP, "fan_out": FAN_OUT}}, fh, indent=2)

    @classmethod
    def load(cls, directory: str) -> Optional["FingerprintIndex"]:
        npz = os.path.join(directory, "fingerprints.npz")
        js = os.path.join(directory, "fingerprints.json")
        if not (os.path.exists(npz) and os.path.exists(js)):
            return None
        idx = cls()
        with open(js) as fh:
            m = json.load(fh)
        idx.song_ids, idx.meta = m["song_ids"], m["meta"]
        d = np.load(npz)
        idx.hashes, idx.song_idx, idx.offsets = d["hashes"], d["song_idx"], d["offsets"]
        return idx

    # ---------------------------------------------------------------- match
    def match(self, x: np.ndarray, sr: int) -> MatchResult:
        q = to_fp_rate(x, sr)
        qh, qt = fingerprint(q)
        if len(qh) == 0 or len(self.hashes) == 0:
            return MatchResult(None, 0.0, query_hashes=int(len(qh)))
        left = np.searchsorted(self.hashes, qh, "left")
        right = np.searchsorted(self.hashes, qh, "right")
        counts = right - left
        counts[counts > STOP_HASH_COUNT] = 0
        total = int(counts.sum())
        if total == 0:
            return MatchResult(None, 0.0, query_hashes=int(len(qh)))
        # expand every (query hash, index hit) pair without a Python loop
        q_of_hit = np.repeat(np.arange(len(qh)), counts)
        starts = np.repeat(left, counts)
        within = np.arange(total) - np.repeat(np.cumsum(counts) - counts, counts)
        db = starts + within
        song = self.song_idx[db].astype(np.int64)
        off = self.offsets[db].astype(np.int64) - qt[q_of_hit]
        key = song * (1 << 24) + (off + (1 << 23))
        # One vote per distinct query MOMENT (anchor frame) per (song, offset). A single loud
        # chord has many harmonics, so it can cast dozens of hash votes from one instant; a true
        # match agrees at many different instants. Counting moments removes that false pile.
        moment = np.unique(key * 4096 + qt[q_of_hit].astype(np.int64))
        ukey, ucount = np.unique(moment // 4096, return_counts=True)
        # allow +-1 frame: the clip's frames are not aligned with the song's frames
        smooth = ucount.copy()
        for d in (-1, 1):
            j = np.searchsorted(ukey, ukey + d)
            hit = (j < len(ukey)) & (ukey[np.minimum(j, len(ukey) - 1)] == ukey + d)
            smooth[hit] += ucount[j[hit]]
        usong = ukey >> 24
        uoff = (ukey & ((1 << 24) - 1)) - (1 << 23)
        best_per_song = {}
        for s in np.unique(usong):
            m = usong == s
            k = int(np.argmax(smooth[m]))
            best_per_song[int(s)] = (int(smooth[m][k]), int(uoff[m][k]))
        ranked = sorted(best_per_song.items(), key=lambda kv: -kv[1][0])
        (bs, (bscore, boff)) = ranked[0]
        second = ranked[1][1][0] if len(ranked) > 1 else 0
        conf = confidence_from_scores(bscore, second)
        return MatchResult(
            song_id=self.song_ids[bs] if conf > 0 else None,
            confidence=conf,
            offset_s=round(boff * FRAME_S, 2),
            score=bscore,
            second=second,
            query_hashes=int(len(qh)),
            scores={self.song_ids[s]: v[0] for s, v in ranked[:5]},
        )
