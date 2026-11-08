"""M1 audio sources: where blocks of samples come from.

Every source calls `on_block(samples, capture_time)` once per block of BLOCK_SIZE mono float32
samples, at real-time pace, from its own thread. `capture_time` is time.perf_counter() when the
block became available, so the app can measure how long a block waits before it is analysed.

- MicSource:     microphone or line-in through sounddevice (PortAudio). Device selectable.
- FileSource:    plays a file through the speakers AND feeds the same blocks to the pipeline,
                 so the lights follow exactly what is heard. Works with no live audio at all.
                 If there is no output device (or play=False) it paces itself with a clock.
- SilenceSource: zeros at real-time pace, so the show keeps ticking (idle glow) with no input.

See decisions/103-m1-audio-sources.md.
"""
from __future__ import annotations

import os
import threading
import time
from typing import Callable, Optional

import numpy as np

from lumasync.audiofile import load_audio
from lumasync.contract import BLOCK_SIZE, SAMPLE_RATE

OnBlock = Callable[[np.ndarray, float], None]


def list_input_devices() -> list[dict]:
    """Input-capable devices, for the UI's device picker."""
    try:
        import sounddevice as sd

        devs = sd.query_devices()
        default_in = sd.default.device[0] if sd.default.device else None
    except Exception as e:  # PortAudio missing or broken: the app still runs on file/silence
        return [{"index": -1, "name": f"(audio unavailable: {e})", "channels": 0, "default": False}]
    out = []
    for i, d in enumerate(devs):
        if d["max_input_channels"] > 0:
            out.append(
                {
                    "index": i,
                    "name": d["name"],
                    "channels": int(d["max_input_channels"]),
                    "default": i == default_in,
                }
            )
    return out


class _Paced:
    """Calls `step()` every block period from a thread, on a drift-free schedule."""

    def __init__(self, step: Callable[[], bool], period: float):
        self.step = step
        self.period = period
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="audio-pacer", daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread.is_alive() and threading.current_thread() is not self._thread:
            self._thread.join(timeout=1.0)

    def _run(self):
        nxt = time.perf_counter()
        while not self._stop.is_set():
            if not self.step():
                return
            nxt += self.period
            delay = nxt - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
            elif delay < -0.5:  # fell far behind (laptop slept): resync instead of bursting
                nxt = time.perf_counter()


class BlockSource:
    kind = "none"

    def __init__(self, on_block: OnBlock):
        self.on_block = on_block
        self.error: Optional[str] = None

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def info(self) -> dict:
        return {"kind": self.kind, "error": self.error}


class SilenceSource(BlockSource):
    kind = "silence"

    def __init__(self, on_block: OnBlock):
        super().__init__(on_block)
        self._zeros = np.zeros(BLOCK_SIZE, dtype=np.float32)
        self._pacer = _Paced(self._step, BLOCK_SIZE / SAMPLE_RATE)

    def _step(self) -> bool:
        self.on_block(self._zeros, time.perf_counter())
        return True

    def start(self):
        self._pacer.start()

    def stop(self):
        self._pacer.stop()


class MicSource(BlockSource):
    """Mic or line-in. Stereo inputs are mixed to mono (line-in from a mixer is usually stereo)."""

    kind = "mic"

    def __init__(self, on_block: OnBlock, device: Optional[int] = None):
        super().__init__(on_block)
        self.device = device
        self.stream = None
        self.name = "default input"
        self.overflows = 0

    def start(self):
        import sounddevice as sd

        dev = sd.query_devices(self.device, "input")
        self.name = dev["name"]
        channels = max(1, min(2, int(dev["max_input_channels"])))

        def cb(indata, frames, time_info, status):
            if status.input_overflow:
                self.overflows += 1
            mono = indata.mean(axis=1) if indata.shape[1] > 1 else indata[:, 0]
            self.on_block(mono.astype(np.float32, copy=True), time.perf_counter())

        self.stream = sd.InputStream(
            device=self.device,
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            channels=channels,
            dtype="float32",
            latency="low",
            callback=cb,
        )
        self.stream.start()

    def stop(self):
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            finally:
                self.stream = None

    def info(self) -> dict:
        lat = None
        if self.stream is not None:
            try:
                lat = round(float(self.stream.latency) * 1000, 1)
            except Exception:
                pass
        return {
            "kind": self.kind,
            "device": self.device,
            "name": self.name,
            "device_latency_ms": lat,
            "overflows": self.overflows,
            "error": self.error,
        }


class FileSource(BlockSource):
    kind = "file"

    def __init__(
        self,
        on_block: OnBlock,
        path: str,
        play: bool = True,
        loop: bool = True,
        gain: float = 0.8,
        audio: Optional[np.ndarray] = None,
    ):
        super().__init__(on_block)
        self.path = path
        self.play = play
        self.loop = loop
        self.gain = gain
        self.audio = audio if audio is not None else load_audio(path, SAMPLE_RATE, mono=False)
        if self.audio.ndim == 1:
            self.audio = self.audio[:, None]
        self.mono = self.audio.mean(axis=1).astype(np.float32)
        self.pos = 0
        self.stream = None
        self.pacer: Optional[_Paced] = None
        self.finished = False
        self.output = "none"

    @property
    def duration(self) -> float:
        return len(self.mono) / SAMPLE_RATE

    def _next(self):
        """Next block as (stereo, mono). Loops or pads with zeros at the end."""
        n = BLOCK_SIZE
        end = self.pos + n
        if end <= len(self.mono):
            st, mo = self.audio[self.pos:end], self.mono[self.pos:end]
            self.pos = end
            return st, mo
        st = np.zeros((n, self.audio.shape[1]), dtype=np.float32)
        mo = np.zeros(n, dtype=np.float32)
        k = len(self.mono) - self.pos
        if k > 0:
            st[:k], mo[:k] = self.audio[self.pos:], self.mono[self.pos:]
        if self.loop:
            rest = n - max(k, 0)
            st[max(k, 0):] = self.audio[:rest]
            mo[max(k, 0):] = self.mono[:rest]
            self.pos = rest
        else:
            self.pos = len(self.mono)
            self.finished = True
        return st, mo

    def start(self):
        if self.play:
            try:
                self._start_output()
                return
            except Exception as e:  # no speakers / device busy: still run the pipeline
                self.error = f"playback unavailable ({e}); running silently"
        self.output = "clock (muted)"
        self.pacer = _Paced(self._step_silent, BLOCK_SIZE / SAMPLE_RATE)
        self.pacer.start()

    def _step_silent(self) -> bool:
        _, mono = self._next()
        self.on_block(mono.copy(), time.perf_counter())
        return True

    def _start_output(self):
        import sounddevice as sd

        dev = sd.query_devices(None, "output")
        ch = max(1, min(int(dev["max_output_channels"]), 2))

        def cb(outdata, frames, time_info, status):
            st, mono = self._next()
            if ch == 1:
                outdata[:, 0] = mono * self.gain
            elif st.shape[1] == 1:
                outdata[:] = np.repeat(st, ch, axis=1) * self.gain
            else:
                outdata[:] = st[:, :ch] * self.gain
            # The block is handed to the speaker now; the pipeline sees the same samples.
            self.on_block(mono.copy(), time.perf_counter())

        self.stream = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            channels=ch,
            dtype="float32",
            latency="low",
            callback=cb,
        )
        self.stream.start()
        self.output = dev["name"]

    def stop(self):
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            finally:
                self.stream = None
        if self.pacer is not None:
            self.pacer.stop()
            self.pacer = None

    def info(self) -> dict:
        lat = None
        if self.stream is not None:
            try:
                lat = round(float(self.stream.latency) * 1000, 1)
            except Exception:
                pass
        return {
            "kind": self.kind,
            "path": self.path,
            "name": os.path.basename(self.path),
            "position_s": round(self.pos / SAMPLE_RATE, 1),
            "duration_s": round(self.duration, 1),
            "output": self.output,
            "device_latency_ms": lat,
            "error": self.error,
        }
