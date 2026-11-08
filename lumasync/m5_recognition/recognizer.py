"""M5 live recognition: AudioFrame in, MusicContext out.

Fast path / slow path: `process()` runs on every tick and must stay cheap (it only copies the
block into a rolling buffer and returns the latest result). Matching takes several ms, so it runs
on a background worker thread about once a second, over the last ~8 s of audio. A slow match can
therefore never delay a beat flash. -> decisions/109-m5-recognition-confidence-and-schedule.md

M5 reports honest, raw evidence: the latest match and its confidence. It does NOT smooth or
hold results. Deciding when a song is "really" playing (hysteresis) is M4's job, because M4 is
where the cost of a wrong decision (a wrong colour palette) is felt.
-> decisions/113-superposition-song-state-and-transitions.md
"""
from __future__ import annotations

import os
import threading
import time
from typing import Optional

import numpy as np

from lumasync.audiofile import load_audio
from lumasync.contract import BLOCK_SIZE, SAMPLE_RATE, AudioFrame, MusicContext

from .fingerprint import FingerprintIndex, MatchResult
from .mood import MoodEstimator


def _loader(path: str):
    return load_audio(path, SAMPLE_RATE, mono=True), SAMPLE_RATE


def build_index(songs: list[tuple[str, str]], directory: Optional[str] = None, progress=None) -> FingerprintIndex:
    """songs: [(song_id, audio_path)]. Saves to `directory` if given."""
    songs = [(sid, p) for sid, p in songs if p and os.path.exists(p)]
    idx = FingerprintIndex.build(songs, _loader, progress)
    if directory:
        idx.save(directory)
    return idx


class RecognitionModule:
    def __init__(
        self,
        index: Optional[FingerprintIndex] = None,
        query_s: float = 8.0,
        min_query_s: float = 3.0,
        interval_s: float = 1.0,
        report_threshold: float = 0.2,
        async_match: bool = True,
        sample_rate: int = SAMPLE_RATE,
    ):
        self.index = index
        self.sr = sample_rate
        self.query_n = int(query_s * sample_rate)
        self.min_n = int(min_query_s * sample_rate)
        self.interval = interval_s
        self.report_threshold = report_threshold
        self.async_match = async_match
        self.mood = MoodEstimator()
        self._lock = threading.Lock()
        self._busy = False
        self.reset()

    # ------------------------------------------------------------------ control
    def reset(self) -> None:
        """Forget the buffered audio (call when the input source changes)."""
        with self._lock:
            self.generation = getattr(self, "generation", 0) + 1   # results from before a reset are dropped
            self.buf = np.zeros(int(self.query_n * 1.25), dtype=np.float32)
            self.filled = 0
            self.last_match_t = -1e9
            self.result = MatchResult(None, 0.0)
            self.result_t = 0.0
            self.matches = 0
            self.match_ms = 0.0
        self.mood.reset()

    def set_index(self, index: Optional[FingerprintIndex]) -> None:
        with self._lock:
            self.index = index
            self.result = MatchResult(None, 0.0)

    # ------------------------------------------------------------------ per tick
    def process(self, frame: AudioFrame) -> MusicContext:
        x = frame.samples
        n = len(x)
        self.buf[:-n] = self.buf[n:]
        self.buf[-n:] = x
        self.filled = min(self.filled + n, len(self.buf))

        if (
            self.index is not None
            and self.filled >= self.min_n
            and frame.t - self.last_match_t >= self.interval
            and not self._busy
        ):
            self.last_match_t = frame.t
            clip = self.buf[-min(self.filled, self.query_n):].copy()
            if self.async_match:
                self._busy = True
                threading.Thread(target=self._match, args=(clip, frame.t, self.generation), daemon=True).start()
            else:
                self._match(clip, frame.t, self.generation)

        valence, arousal = self.mood.process(frame)
        r = self.result
        sid = r.song_id if r.confidence >= self.report_threshold else None
        return MusicContext(
            t=frame.t,
            song_id=sid,
            song_confidence=round(r.confidence, 3) if sid else 0.0,
            valence=valence,
            arousal=arousal,
        )

    def _match(self, clip: np.ndarray, t: float, generation: int) -> None:
        try:
            idx = self.index
            if idx is None:
                return
            if float(np.sqrt(np.mean(clip ** 2))) < 1e-4:  # silence: nothing to recognise
                res = MatchResult(None, 0.0)
            else:
                t0 = time.perf_counter()
                res = idx.match(clip, self.sr)
                self.match_ms = (time.perf_counter() - t0) * 1000
            # The match describes audio that ended at time t; the song kept playing since.
            res.offset_s = round(res.offset_s + len(clip) / self.sr, 2)
            with self._lock:
                if generation != self.generation:
                    return
                self.result, self.result_t = res, t
                self.matches += 1
        finally:
            self._busy = False

    def status(self) -> dict:
        r = self.result
        return {
            "indexed_songs": len(self.index.song_ids) if self.index else 0,
            "index_hashes": int(len(self.index.hashes)) if self.index else 0,
            "last_song": r.song_id,
            "last_confidence": round(r.confidence, 2),
            "last_score": r.score,
            "runner_up_score": r.second,
            "song_position_s": r.offset_s if r.song_id else None,
            "match_ms": round(self.match_ms, 1),
            "matches": self.matches,
            "buffer_s": round(self.filled / self.sr, 1),
            "mood_model": self.mood.label,
        }
