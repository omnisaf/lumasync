"""M2 outputs: where a DMX universe goes.

DmxOutput     FTDI USB-to-DMX cable (e.g. DSD TECH SH-RS09B). Own thread, steady ~30 frames/s,
              always sends the LATEST universe (never a queue of old ones). If no cable is
              found it keeps running and checks again every 2 s, so the cable can be plugged in
              mid-demo. If the cable is pulled out it goes back to searching. Never crashes the app.
              Send logic follows tools/dmx_test.py: 250 000 baud, 8 data bits, no parity,
              2 stop bits; break by holding the line low (break_condition) >= 88 us, then
              mark-after-break >= 8 us, then start code 0 + 512 channel bytes.
              -> decisions/119-lighting-dmx-output-thread.md
VirtualOutput The on-screen preview (the web UI draws it). Always on.
SacnOutput    STUB. sACN (E1.31) = DMX sent inside network packets, for the planned ESP32 node.
"""
from __future__ import annotations

import glob
import threading
import time
from typing import Optional

FRAME_BYTES = 513
WIRE_MS = (0.000092 + 0.000012 + FRAME_BYTES * 0.000044) * 1000   # break + MAB + 513 slots x 44 us


def find_dmx_ports() -> list[str]:
    """Only USB-serial adapters. Bluetooth serial ports (speakers etc.) are never opened."""
    return sorted(glob.glob("/dev/cu.usbserial*") + glob.glob("/dev/ttyUSB*"))


class DmxOutput:
    def __init__(self, enabled: bool = True, port: Optional[str] = None, fps: float = 30.0,
                 break_mode: str = "flag", rescan_s: float = 2.0):
        self.enabled = enabled
        self.port_hint = port
        self.fps = fps
        self.break_mode = break_mode
        self.rescan_s = rescan_s
        self.ser = None
        self.port: Optional[str] = None
        self._frame = bytearray(FRAME_BYTES)
        self._frame_t = time.perf_counter()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.frames_sent = 0
        self.errors = 0
        self.last_error: Optional[str] = None
        self.age_ms = 0.0          # how old the newest universe was when it went out
        self.send_ms = 0.0         # time spent writing one frame
        self.state = "disabled" if not enabled else "searching"

    # -------------------------------------------------------------- api
    def start(self) -> None:
        if not self.enabled or self._thread:
            return
        self._thread = threading.Thread(target=self._run, name="dmx-output", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._close(blackout=True)

    def set_frame(self, universe: bytearray, produced_at: Optional[float] = None) -> None:
        with self._lock:
            self._frame = bytearray(universe)
            self._frame_t = produced_at or time.perf_counter()

    # -------------------------------------------------------------- thread
    def _open(self) -> bool:
        ports = [self.port_hint] if self.port_hint else find_dmx_ports()
        for p in ports:
            try:
                import serial

                self.ser = serial.Serial(p, baudrate=250000, bytesize=8, parity="N", stopbits=2,
                                         write_timeout=0.5)
                self.port = p
                self.state = "connected"
                self.last_error = None
                return True
            except Exception as e:
                self.last_error = f"{p}: {e}"
        self.state = "searching"
        return False

    def _close(self, blackout: bool = False) -> None:
        if self.ser is None:
            return
        try:
            if blackout:
                for _ in range(3):
                    self._send(bytearray(FRAME_BYTES))
                    time.sleep(1 / self.fps)
            self.ser.close()
        except Exception:
            pass
        self.ser = None
        self.port = None

    def _send(self, frame: bytearray) -> None:
        ser = self.ser
        if self.break_mode == "flag":
            ser.break_condition = True
            time.sleep(0.0002)
            ser.break_condition = False
            time.sleep(0.00002)
        else:  # "baud": a slow 0x00 looks like a break on the wire
            ser.baudrate = 76800
            ser.write(b"\x00")
            ser.flush()
            ser.baudrate = 250000
        ser.write(frame)
        ser.flush()

    def _run(self) -> None:
        period = 1.0 / self.fps
        nxt = time.perf_counter()
        while not self._stop.is_set():
            if self.ser is None:
                if not self._open():
                    self._stop.wait(self.rescan_s)
                    nxt = time.perf_counter()
                    continue
            with self._lock:
                frame, t_made = bytes(self._frame), self._frame_t
            try:
                t0 = time.perf_counter()
                self.age_ms = (t0 - t_made) * 1000
                self._send(bytearray(frame))
                self.send_ms = (time.perf_counter() - t0) * 1000
                self.frames_sent += 1
            except Exception as e:  # cable pulled out, etc.
                self.errors += 1
                self.last_error = str(e)
                self._close()
                self.state = "searching"
                continue
            nxt += period
            delay = nxt - time.perf_counter()
            if delay > 0:
                self._stop.wait(delay)
            else:
                nxt = time.perf_counter()

    def status(self) -> dict:
        return {
            "state": self.state,
            "port": self.port,
            "fps": self.fps,
            "frames_sent": self.frames_sent,
            "errors": self.errors,
            "last_error": self.last_error,
            "age_ms": round(self.age_ms, 1),
            "send_ms": round(self.send_ms, 1),
            "wire_ms": round(WIRE_MS, 1),
        }


class VirtualOutput:
    """Keeps the latest preview + universe for the UI. Thread-safe enough for a snapshot read."""

    def __init__(self):
        self.preview: list[dict] = []
        self.universe = bytearray(FRAME_BYTES)

    def write(self, preview: list[dict], universe: bytearray) -> None:
        self.preview = preview
        self.universe = universe


class SacnOutput:
    """STUB for sACN (ANSI E1.31): DMX universes in UDP multicast packets, port 5568.
    Planned for the ESP32 DMX node and WLED LED strips. Not implemented in the prototype.
    A real version would build the E1.31 root/framing/DMP layers and send at a steady rate."""

    def __init__(self, universe: int = 1, destination: Optional[str] = None):
        self.universe = universe
        self.destination = destination

    def start(self) -> None:
        raise NotImplementedError("sACN output is planned (ESP32 node); use DMX or the preview for now")

    def set_frame(self, universe: bytearray, produced_at: Optional[float] = None) -> None:
        raise NotImplementedError

    def status(self) -> dict:
        return {"state": "not implemented"}
