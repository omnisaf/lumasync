"""LumaSync runner. Wires the five modules together through the contract only, measures the
latency of every stage, and serves the web UI at http://localhost:8765.

    .venv/bin/python -m lumasync.app                                   # demo track through speakers
    .venv/bin/python -m lumasync.app --source file --file library/audio/demo_neon_drive.wav
    .venv/bin/python -m lumasync.app --source mic --device 1           # mic / line-in
    .venv/bin/python -m lumasync.app --no-dmx --mute --duration 30     # headless check

Threads (decisions/101-app-threading-model.md):
    audio thread   (PortAudio callback or a clock) -> puts blocks in a small queue
    engine thread  M1 -> M3 -> M5 -> M4 -> M2, one tick per block, measures each stage
    M5 worker      fingerprint matching, ~1 per second, never blocks a tick
    DMX thread     sends the latest universe at a steady 30 frames/s
    main thread    asyncio web server: page + WebSocket (decisions/102-app-ui-transport.md)

This file is the only place that imports more than one module. No module imports another.
"""
from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json
import math
import os
import queue
import signal
import sys
import threading
import time
import webbrowser
from collections import deque
from typing import Optional

import numpy as np

from lumasync import library as lib
from lumasync.contract import BLOCK_SIZE, CONTRACT_VERSION, SAMPLE_RATE, LiveControls, MusicContext, RhythmState
from lumasync.m1_audio import AudioAnalyzer, FileSource, MicSource, SilenceSource, list_input_devices
from lumasync.m2_lighting import DmxOutput, LightingController, VirtualOutput
from lumasync.m3_rhythm import RhythmTracker
from lumasync.m4_superposition import LOOKS, SuperpositionEngine
from lumasync.m5_recognition import FingerprintIndex, RecognitionModule, build_index

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
BLOCK_MS = BLOCK_SIZE / SAMPLE_RATE * 1000


def log(msg: str) -> None:
    print(time.strftime("%H:%M:%S"), msg, flush=True)


class StageTimer:
    """Per-stage latency: running average and worst case over the last ~2 s."""

    def __init__(self, names: list[str]):
        self.names = names
        self.avg = {n: 0.0 for n in names}
        self.recent = {n: deque(maxlen=90) for n in names}

    def add(self, name: str, ms: float) -> None:
        self.avg[name] += 0.05 * (ms - self.avg[name])
        self.recent[name].append(ms)

    def snapshot(self) -> dict:
        return {n: {"avg": round(self.avg[n], 3), "max": round(max(self.recent[n]) if self.recent[n] else 0.0, 3)}
                for n in self.names}


class Engine:
    STAGES = ["queue", "m1", "m3", "m5", "m4", "m2"]

    def __init__(self, args):
        self.args = args
        self.library = lib.SongLibrary()
        lib.ensure_demo_audio(log)

        self.m1 = AudioAnalyzer()
        self.m3 = RhythmTracker()
        self.m5 = RecognitionModule(index=FingerprintIndex.load(lib.INDEX_DIR))
        self.m2 = LightingController.from_files(args.patch) if args.patch else LightingController.from_files()
        self.m4 = SuperpositionEngine(n_fixtures=self.m2.n_fixtures, presets=self.library.presets(),
                                      lead_s=args.lead_ms / 1000.0)
        self.dmx = DmxOutput(enabled=args.dmx, port=args.dmx_port, break_mode=args.break_mode)
        self.virtual = VirtualOutput()
        for w in self.m2.warnings[:3]:
            log(f"[m2] {w}")

        self.controls = LiveControls()
        self.q: queue.Queue = queue.Queue(maxsize=8)
        self.pending: queue.Queue = queue.Queue()   # work that must run on the engine thread
        self.source = None
        self.source_gen = 0
        self.source_opening: Optional[str] = None
        self.source_error: Optional[str] = None
        self.samples_seen = 0
        self.dropped = 0
        self.timer = StageTimer(self.STAGES)
        self.tick_ms = deque(maxlen=200)
        self.lock = threading.Lock()
        self.latest: dict = {}
        self.ticks = 0
        self.fps_t0, self.fps_n, self.fps = time.perf_counter(), 0, 0.0
        self.index_job = {"running": False, "progress": 0.0, "message": "", "error": None}
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="engine", daemon=True)
        self.drops_seen = 0

        if self._index_stale():
            self.start_fingerprinting(reason="index missing or out of date")

    # ------------------------------------------------------------------ lifecycle
    def start(self) -> None:
        self.dmx.start()
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self.source_gen += 1          # a source still opening is stopped as soon as it opens
        if self.source:
            try:
                self.source.stop()
            except Exception:
                pass
        self._thread.join(timeout=2.0)
        self.dmx.stop()

    # ------------------------------------------------------------------ sources
    def _on_block(self, samples: np.ndarray, t_capture: float) -> None:
        try:
            self.q.put_nowait((samples, t_capture))
        except queue.Full:  # engine fell behind: drop the OLDEST block, keep latency low
            try:
                self.q.get_nowait()
                self.dropped += 1
            except queue.Empty:
                pass
            self.q.put_nowait((samples, t_capture))

    def set_source(self, kind: str, device: Optional[int] = None, path: Optional[str] = None,
                   play: bool = True, wait: bool = False) -> None:
        """Switch input. Returns at once: opening a device can block (on macOS, the first mic open
        waits for the user to answer the microphone-permission dialog). Until the new source is
        open, the engine keeps ticking on silence, so the UI and lights never freeze."""
        self.source_gen += 1
        gen = self.source_gen
        old, self.source = self.source, None
        if old:
            try:
                old.stop()
            except Exception as e:
                log(f"[m1] stopping source: {e}")
        while not self.q.empty():
            try:
                self.q.get_nowait()
            except queue.Empty:
                break
        # a new source is a new stream: rhythm and recognition must not mix old and new audio.
        # Resets run ON the engine thread (before its next tick): only one thread ever touches a module.
        self.call_on_engine(lambda: (self.m1.reset(), self.m3.reset(), self.m5.reset()))
        self.source_error = None
        self.source_opening = f"opening {kind}..." + (" (if macOS asks for microphone access, click Allow)" if kind == "mic" else "")

        def open_source():
            src = None
            try:
                if kind == "mic":
                    src = MicSource(self._on_block, device=device)
                elif kind == "file":
                    p = lib.resolve(path)
                    if not p or not os.path.exists(p):
                        raise FileNotFoundError(f"audio file not found: {path}")
                    src = FileSource(self._on_block, p, play=play, loop=True)
                else:
                    src = SilenceSource(self._on_block)
                src.start()
            except Exception as e:
                if gen == self.source_gen:
                    self.source_error = f"{kind}: {e}"
                    self.source_opening = None
                log(f"[m1] could not start {kind} source ({e}); running on silence")
                return
            if gen != self.source_gen:      # a newer switch happened while this one was opening
                src.stop()
                return
            self.source = src
            self.source_opening = None
            log(f"[m1] source -> {src.info()}")

        t = threading.Thread(target=open_source, name=f"open-{kind}", daemon=True)
        t.start()
        if wait:
            t.join(timeout=10)

    # ------------------------------------------------------------------ fingerprints
    def _index_stale(self) -> bool:
        idx = self.m5.index
        songs = self.library.fingerprint_list()
        if not songs:
            return False
        if idx is None:
            return True
        return any(not idx.is_current(sid, p) for sid, p in songs) or set(idx.song_ids) != {s for s, _ in songs}

    def start_fingerprinting(self, reason: str = "requested") -> bool:
        if self.index_job["running"]:
            return False
        songs = self.library.fingerprint_list()
        self.index_job = {"running": True, "progress": 0.0, "message": f"starting ({reason})", "error": None}
        log(f"[m5] building fingerprint index for {len(songs)} songs ({reason})")

        def progress(i, n, sid):
            self.index_job["progress"] = i / max(n, 1)
            self.index_job["message"] = f"{i}/{n} {sid}"

        def job():
            t0 = time.perf_counter()
            try:
                idx = build_index(songs, lib.INDEX_DIR, progress)
                self.m5.set_index(idx)
                msg = f"indexed {len(idx.song_ids)} songs, {len(idx.hashes)} hashes in {time.perf_counter() - t0:.1f} s"
                self.index_job.update(running=False, progress=1.0, message=msg)
                log(f"[m5] {msg}")
            except Exception as e:
                self.index_job.update(running=False, error=str(e), message="failed")
                log(f"[m5] fingerprinting failed: {e}")

        threading.Thread(target=job, name="fingerprint-build", daemon=True).start()
        return True

    # ------------------------------------------------------------------ the tick
    def _run(self) -> None:
        silence = np.zeros(BLOCK_SIZE, dtype=np.float32)
        while not self._stop.is_set():
            try:
                samples, t_cap = self.q.get(timeout=BLOCK_MS / 1000 * 1.5)
            except queue.Empty:  # source stalled or died: keep the show ticking on silence
                samples, t_cap = silence, time.perf_counter()
            try:
                self.tick(samples, t_cap)
            except Exception as e:  # one bad tick must never stop the show
                log(f"[engine] tick error: {e!r}")

    def call_on_engine(self, fn) -> None:
        self.pending.put(fn)

    def tick(self, samples: np.ndarray, t_capture: Optional[float] = None) -> dict:
        while not self.pending.empty():
            try:
                self.pending.get_nowait()()
            except queue.Empty:
                break
        p = time.perf_counter
        t0 = p()
        t = self.samples_seen / SAMPLE_RATE
        self.samples_seen += len(samples)
        controls = self.controls

        frame = self.m1.process(samples, t)
        t1 = p()
        rhythm: RhythmState = self.m3.process(frame)
        t2 = p()
        music: MusicContext = self.m5.process(frame)
        t3 = p()
        intent = self.m4.process(frame, rhythm, music, controls)
        t4 = p()
        universe = self.m2.process(intent)
        self.dmx.set_frame(universe, produced_at=p())
        preview = self.m2.preview(intent)
        self.virtual.write(preview, universe)
        t5 = p()

        tm = self.timer
        tm.add("queue", ((t0 - t_capture) * 1000) if t_capture else 0.0)
        tm.add("m1", (t1 - t0) * 1000)
        tm.add("m3", (t2 - t1) * 1000)
        tm.add("m5", (t3 - t2) * 1000)
        tm.add("m4", (t4 - t3) * 1000)
        tm.add("m2", (t5 - t4) * 1000)
        self.tick_ms.append((t5 - t0) * 1000)
        if rhythm.drop:
            self.drops_seen += 1

        self.ticks += 1
        self.fps_n += 1
        now = p()
        if now - self.fps_t0 >= 1.0:
            self.fps = self.fps_n / (now - self.fps_t0)
            self.fps_t0, self.fps_n = now, 0
        with self.lock:
            self.latest = {"frame": frame, "rhythm": rhythm, "music": music, "intent": intent,
                           "preview": preview, "universe": universe}
        return self.latest

    # ------------------------------------------------------------------ commands from the UI
    def update_controls(self, values: dict) -> None:
        cur = dataclasses.asdict(self.controls)
        for k, v in values.items():
            if k not in cur:
                continue
            if k in ("master", "reactivity", "preset_blend"):
                v = float(min(max(float(v), 0.0), 1.0))
            elif k in ("strobe_enabled", "blackout"):
                v = bool(v)
            elif k == "manual_song_id":
                v = v or None
            elif k == "look":
                v = v if v in LOOKS else "auto"
            cur[k] = v
        self.controls = LiveControls(**cur)   # swap the whole object: the engine never sees half an update

    def reload_library(self) -> None:
        self.library.load()
        self.m4.set_presets(self.library.presets())

    # ------------------------------------------------------------------ state for the UI
    def latency(self) -> dict:
        s = self.timer.snapshot()
        info = self.source.info() if self.source else {}
        dev = info.get("device_latency_ms") or 0.0
        dmx = self.dmx.status()
        dmx_on = dmx["state"] == "connected"
        out_wait = 1000.0 / self.dmx.fps / 2  # on average a universe waits half a frame period
        wire = dmx["wire_ms"]
        proc = sum(s[k]["avg"] for k in ("m1", "m3", "m5", "m4", "m2"))
        q = s["queue"]["avg"]
        if info.get("kind") == "file":
            # the pipeline sees each block as it is handed to the speakers, which play it `dev` ms later
            sound_to_light = q + proc + out_wait + wire - dev
            capture = 0.0
        else:
            capture = BLOCK_MS + dev
            sound_to_light = capture + q + proc + out_wait + wire
        stages = [
            ("capture (block + device)", round(capture, 2)),
            ("queue wait", round(q, 2)),
            ("M1 audio", s["m1"]["avg"]),
            ("M3 rhythm", s["m3"]["avg"]),
            ("M5 recognition (per tick)", s["m5"]["avg"]),
            ("M4 superposition", s["m4"]["avg"]),
            ("M2 mapping", s["m2"]["avg"]),
            ("DMX frame wait (avg)", round(out_wait, 1)),
            ("DMX wire time", wire),
        ]
        return {
            "stages": stages,
            "max": {k: v["max"] for k, v in s.items()},
            "processing_ms": round(proc, 2),
            "tick_max_ms": round(max(self.tick_ms) if self.tick_ms else 0.0, 2),
            "sound_to_light_ms": round(sound_to_light, 1),
            "beat_lead_ms": round(self.m4.lead_s * 1000),
            "dmx_connected": dmx_on,
            "m5_match_ms": self.m5.match_ms,
        }

    def state(self) -> dict:
        with self.lock:
            L = dict(self.latest)
        if not L:
            return {"type": "state", "ready": False}
        f, r, m = L["frame"], L["rhythm"], L["music"]
        spec = f.spectrum
        if spec is not None and len(spec) > 64:
            edges = np.unique(np.geomspace(2, len(spec) - 1, 49).astype(int))
            sb = np.maximum.reduceat(spec, edges)[:-1]
            spec_db = np.clip((20 * np.log10(sb + 1e-9) + 80) / 80, 0, 1)
            spectrum = [round(float(v), 3) for v in spec_db]
        else:
            spectrum = []
        m3s, m4s, m5s = self.m3.status(), self.m4.status(), self.m5.status()
        presets = self.m4.presets
        title = lambda sid: presets[sid].title if sid in presets else None
        src = self.source.info() if self.source else {"kind": "silence", "name": "no input yet"}
        if self.source_opening:
            src = {**src, "opening": self.source_opening}
        rms_db = 20 * math.log10(f.rms + 1e-9)
        lat = self.latency()
        dmx = self.dmx.status()
        modules = {
            "m1": {"ok": rms_db > -70, "summary": f"{rms_db:.0f} dBFS · centroid {f.centroid_hz:.0f} Hz",
                   "ms": self.timer.avg["m1"]},
            "m3": {"ok": r.bpm > 0, "summary": (f"{r.bpm:.1f} BPM · conf {r.confidence:.2f}" if r.bpm else "listening for a beat"),
                   "ms": self.timer.avg["m3"]},
            "m5": {"ok": m.song_id is not None,
                   "summary": (f"{title(m.song_id) or m.song_id} · {m.song_confidence:.2f}" if m.song_id else
                               f"no match · {m5s['indexed_songs']} songs indexed"),
                   "ms": self.timer.avg["m5"]},
            "m4": {"ok": True, "summary": f"{m4s.get('look')} · preset w {m4s.get('preset_weight', 0):.2f}"
                   + (" · SAFETY CAP" if m4s.get("safety_cap_engaged") else ""), "ms": self.timer.avg["m4"]},
            "m2": {"ok": True, "summary": ("DMX " + dmx["state"] + (f" {dmx['port']}" if dmx["port"] else "")
                                           if self.dmx.enabled else "DMX off · preview only"), "ms": self.timer.avg["m2"]},
        }
        return {
            "type": "state",
            "ready": True,
            "t": round(f.t, 3),
            "fps": round(self.fps, 1),
            "fixtures": L["preview"],
            "intent_source": L["intent"].source,
            "audio": {"rms_db": round(rms_db, 1), "bands": {k: round(v, 3) for k, v in f.bands.items()},
                      "centroid": round(f.centroid_hz), "flux": round(f.flux, 4), "spectrum": spectrum},
            "rhythm": {"bpm": r.bpm, "confidence": round(r.confidence, 2), "phase": round(r.beat_phase, 3),
                       "onset": round(r.onset, 2), "trend": round(r.energy_trend, 2), "beats": m3s["beats"],
                       "onsets": m3s["onsets"], "drops": m3s["drops"], "raw_bpm": m3s["raw_bpm"]},
            "music": {"song_id": m.song_id, "title": title(m.song_id), "confidence": m.song_confidence,
                      "valence": m.valence, "arousal": m.arousal, "detail": m5s},
            "m4": {**m4s, "song_goal_title": title(m4s.get("song_goal")), "preset_title": title(m4s.get("preset_song"))},
            "controls": dataclasses.asdict(self.controls),
            "latency": lat,
            "modules": modules,
            "source": {**src, "error": self.source_error or src.get("error")},
            "dmx": dmx,
            "universe": list(L["universe"][1:73]),
            "index": dict(self.index_job),
            "dropped_blocks": self.dropped,
        }

    def hello(self) -> dict:
        idx = self.m5.index
        return {
            "type": "hello",
            "contract_version": CONTRACT_VERSION,
            "looks": list(LOOKS),
            "devices": list_input_devices(),
            "library": self.library.as_json(),
            "fingerprinted": {s["song_id"]: bool(idx and idx.is_current(s["song_id"], lib.resolve(s.get("audio_file"))))
                              for s in self.library.songs},
            "audio_files": self.library.audio_files(),
            "patch": self.m2.describe(),
            "patch_warnings": self.m2.warnings,
        }


# ======================================================================================
# Web server: one port serves the page (plain HTTP GET) and the WebSocket (/ws).
# ======================================================================================
class WebServer:
    def __init__(self, engine: Engine, host: str, port: int):
        self.engine = engine
        self.host, self.port = host, port
        self.clients: set = set()

    def _page(self, name: str):
        from websockets.datastructures import Headers
        from websockets.http11 import Response

        path = os.path.join(WEB_DIR, name)
        with open(path, "rb") as fh:
            body = fh.read()
        ctype = "text/html; charset=utf-8" if name.endswith(".html") else "application/octet-stream"
        return Response(200, "OK", Headers([("Content-Type", ctype), ("Cache-Control", "no-store"),
                                            ("Content-Length", str(len(body)))]), body)

    def process_request(self, connection, request):
        path = request.path.split("?")[0]
        if path == "/ws":
            return None  # continue with the WebSocket handshake
        if path in ("/", "/index.html"):
            return self._page("index.html")
        if path == "/api/state":
            from websockets.datastructures import Headers
            from websockets.http11 import Response

            body = json.dumps(self.engine.state(), default=_json_default).encode()
            return Response(200, "OK", Headers([("Content-Type", "application/json"),
                                                ("Content-Length", str(len(body)))]), body)
        return connection.respond(404, "Not found\n")

    async def handler(self, ws):
        self.clients.add(ws)
        try:
            await ws.send(json.dumps(self.engine.hello(), default=_json_default))
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                    reply = await asyncio.get_running_loop().run_in_executor(None, self.handle, msg)
                    if reply:
                        await self.send_all(reply)
                except Exception as e:
                    await ws.send(json.dumps({"type": "error", "message": str(e)}))
        finally:
            self.clients.discard(ws)

    def handle(self, msg: dict) -> Optional[dict]:
        e = self.engine
        cmd = msg.get("cmd")
        if cmd == "controls":
            e.update_controls(msg.get("values", {}))
        elif cmd == "select_song":
            e.update_controls({"manual_song_id": msg.get("song_id")})
        elif cmd == "source":
            kind = msg.get("kind", "silence")
            dev = msg.get("device")
            e.set_source(kind, device=None if dev in (None, "", -1) else int(dev), path=msg.get("path"),
                         play=bool(msg.get("play", True)))
        elif cmd == "save_song":
            sid = e.library.upsert(msg.get("song", {}))
            e.reload_library()
            log(f"[library] saved {sid}")
            return e.hello()
        elif cmd == "delete_song":
            e.library.delete(msg.get("song_id"))
            e.reload_library()
            return e.hello()
        elif cmd == "fingerprint":
            e.start_fingerprinting()
        elif cmd == "refresh":
            return e.hello()
        return None

    async def send_all(self, payload: dict) -> None:
        from websockets.asyncio.server import broadcast

        broadcast(set(self.clients), json.dumps(payload, default=_json_default))

    async def state_loop(self, hz: float = 30.0):
        from websockets.asyncio.server import broadcast

        was_running = False
        while True:
            await asyncio.sleep(1.0 / hz)
            if self.clients:
                broadcast(set(self.clients), json.dumps(self.engine.state(), default=_json_default))
            running = self.engine.index_job["running"]
            if was_running and not running and self.clients:   # index finished: refresh library ticks
                await self.send_all(self.engine.hello())
            was_running = running

    async def run(self, stop: asyncio.Event):
        from websockets.asyncio.server import serve

        async with serve(self.handler, self.host, self.port, process_request=self.process_request,
                         max_size=2 ** 20, ping_interval=20):
            task = asyncio.create_task(self.state_loop())
            await stop.wait()
            task.cancel()


def _json_default(o):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (bytes, bytearray)):
        return list(o)
    return str(o)


def status_line(e: Engine) -> str:
    s = e.state()
    if not s.get("ready"):
        return "waiting for audio..."
    r, m, lat = s["rhythm"], s["music"], s["latency"]
    song = f"{m['song_id']} ({m['confidence']:.2f})" if m["song_id"] else "-"
    return (f"t={s['t']:6.1f}s fps={s['fps']:4.1f} src={s['source'].get('kind')} rms={s['audio']['rms_db']:5.1f}dB "
            f"bpm={r['bpm']:6.2f} conf={r['confidence']:.2f} beats={r['beats']} drops={r['drops']} "
            f"song={song} m4={s['m4'].get('song_state')}/{s['m4'].get('look')} w={s['m4'].get('preset_weight')} "
            f"proc={lat['processing_ms']:.2f}ms sound->light~{lat['sound_to_light_ms']}ms dmx={s['dmx']['state']}")


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="LumaSync: music-reactive DMX lighting")
    ap.add_argument("--source", choices=["file", "mic", "silence"], default="file")
    ap.add_argument("--file", default=None, help="audio file for --source file (default: first library song)")
    ap.add_argument("--device", type=int, default=None, help="input device index for --source mic")
    ap.add_argument("--mute", action="store_true", help="file source: do not play through the speakers")
    ap.add_argument("--dmx", dest="dmx", action="store_true", default=True, help="send DMX if a cable is found (default)")
    ap.add_argument("--no-dmx", dest="dmx", action="store_false", help="preview only, never open a serial port")
    ap.add_argument("--dmx-port", default=None)
    ap.add_argument("--break-mode", choices=["flag", "baud"], default="flag")
    ap.add_argument("--patch", default=None, help="patch file (default lumasync/m2_lighting/patch.json)")
    ap.add_argument("--lead-ms", type=float, default=40.0, help="fire beat pulses this many ms early")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--open", dest="open", action="store_true", help="open the UI in the browser")
    ap.add_argument("--no-open", dest="open", action="store_false", help="do not open the browser")
    ap.add_argument("--duration", type=float, default=0.0, help="stop after N seconds (0 = run until Ctrl+C)")
    ap.add_argument("--log-every", type=float, default=5.0, help="print a status line every N s (0 = off)")
    ap.add_argument("--list-devices", action="store_true")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.list_devices:
        for d in list_input_devices():
            print(f"{d['index']:3d}  {d['name']}  ({d['channels']} ch){'  [default]' if d['default'] else ''}")
        return 0
    engine = Engine(args)
    path = args.file
    if args.source == "file" and not path:
        songs = engine.library.fingerprint_list()
        path = songs[0][1] if songs else None
    engine.start()
    engine.set_source(args.source, device=args.device, path=path, play=not args.mute)

    url = f"http://{'localhost' if args.host in ('127.0.0.1', '0.0.0.0') else args.host}:{args.port}"
    log(f"LumaSync running. Open {url}   (Ctrl+C to stop)")
    if args.open:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    async def runner():
        stop = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, stop.set)
            except NotImplementedError:
                pass
        if args.duration > 0:
            loop.call_later(args.duration, stop.set)

        async def ticker():
            while args.log_every > 0:
                await asyncio.sleep(args.log_every)
                log(status_line(engine))

        tk = asyncio.create_task(ticker())
        try:
            await WebServer(engine, args.host, args.port).run(stop)
        finally:
            tk.cancel()

    try:
        asyncio.run(runner())
    except OSError as e:
        log(f"could not start the web server on port {args.port}: {e}. Is LumaSync already running? Try --port 8766")
        engine.stop()
        return 1
    finally:
        log("stopping...")
        engine.stop()
        log("stopped." + (" DMX blacked out." if engine.dmx.state == "connected" or engine.dmx.frames_sent else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
