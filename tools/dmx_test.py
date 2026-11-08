#!/usr/bin/env python3
"""DMX cable test. No audio, no app. Only: can the laptop make a light move?

Hardware: DSD TECH SH-RS09B (FTDI USB -> DMX, 3-pin XLR).
Chain:    laptop -> cable -> light 1 DMX IN -> light 1 DMX OUT -> light 2 IN ...
          120 ohm terminator in the last light's DMX OUT.

Usage (from the repo root):
    .venv/bin/python tools/dmx_test.py ports            # find the cable
    .venv/bin/python tools/dmx_test.py blink            # ALL channels full / off, 1 s each
    .venv/bin/python tools/dmx_test.py walk --start 1 --count 12
                                                       # one channel at a time -> learn the channel map
    .venv/bin/python tools/dmx_test.py set 1=255 2=255  # hold values (Ctrl+C to stop)

If nothing moves:
  1. Light menu: DMX mode on (not auto/sound mode). Note its address (e.g. A001 / d001).
  2. Try --break-mode baud  (other way to make the DMX "break" signal).
  3. Unplug/replug the cable. Run `ports` again.
  4. Some fixtures need a master dimmer channel up first: add --hold 1=255.
"""
import argparse
import glob
import sys
import time

try:
    import serial
except ImportError:
    sys.exit("pyserial missing. Run: .venv/bin/pip install pyserial")

FPS = 30  # DMX frames per second. Real consoles do ~40; 30 is safe for a dumb FTDI cable.


def find_ports():
    return sorted(glob.glob("/dev/cu.usbserial*") + glob.glob("/dev/ttyUSB*") + glob.glob("COM*"))


class DMX:
    def __init__(self, port, break_mode="flag"):
        self.break_mode = break_mode
        self.ser = serial.Serial(port, baudrate=250000, bytesize=8, parity="N", stopbits=2)
        self.frame = bytearray(513)  # byte 0 = start code (0), bytes 1..512 = channels

    def set(self, ch, val):
        if 1 <= ch <= 512:
            self.frame[ch] = max(0, min(255, int(val)))

    def send(self):
        if self.break_mode == "flag":
            self.ser.break_condition = True
            time.sleep(0.0002)   # break >= 88 us
            self.ser.break_condition = False
            time.sleep(0.00002)  # mark-after-break >= 8 us
        else:  # "baud": send one 0x00 slowly -> looks like a break on the wire
            self.ser.baudrate = 76800
            self.ser.write(b"\x00")
            self.ser.flush()
            self.ser.baudrate = 250000
        self.ser.write(self.frame)
        self.ser.flush()

    def hold(self, seconds):
        end = time.time() + seconds
        while time.time() < end:
            self.send()
            time.sleep(1 / FPS)

    def blackout(self):
        self.frame = bytearray(513)
        self.hold(0.3)


def parse_pairs(pairs):
    out = {}
    for p in pairs or []:
        ch, val = p.split("=")
        out[int(ch)] = int(val)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["ports", "blink", "walk", "set"])
    ap.add_argument("values", nargs="*", help="for `set`: CH=VAL pairs")
    ap.add_argument("--port", help="serial port (default: first /dev/cu.usbserial*)")
    ap.add_argument("--start", type=int, default=1, help="walk: first channel")
    ap.add_argument("--count", type=int, default=12, help="walk: how many channels")
    ap.add_argument("--step", type=float, default=1.5, help="walk: seconds per channel")
    ap.add_argument("--hold", nargs="*", help="CH=VAL kept on during blink/walk (e.g. 1=255 master dimmer)")
    ap.add_argument("--break-mode", choices=["flag", "baud"], default="flag")
    a = ap.parse_args()

    ports = find_ports()
    if a.cmd == "ports":
        print("\n".join(ports) if ports else "No USB serial port found. Is the cable plugged in?")
        return
    port = a.port or (ports[0] if ports else None)
    if not port:
        sys.exit("No USB serial port found. Plug the cable in, then run: tools/dmx_test.py ports")

    print(f"Port: {port}   break mode: {a.break_mode}   Ctrl+C to stop")
    dmx = DMX(port, a.break_mode)
    held = parse_pairs(a.hold)

    def apply_held():
        for ch, v in held.items():
            dmx.set(ch, v)

    try:
        if a.cmd == "blink":
            while True:
                print("ALL ON")
                dmx.frame = bytearray([0] + [255] * 512)
                dmx.hold(1)
                print("all off")
                dmx.frame = bytearray(513)
                apply_held()
                dmx.hold(1)
        elif a.cmd == "walk":
            while True:
                for ch in range(a.start, a.start + a.count):
                    dmx.frame = bytearray(513)
                    apply_held()
                    dmx.set(ch, 255)
                    print(f"channel {ch} = 255   <- write down what the light does")
                    dmx.hold(a.step)
                print("-- loop --")
        elif a.cmd == "set":
            for ch, v in parse_pairs(a.values).items():
                dmx.set(ch, v)
            print("Holding. Ctrl+C to stop.")
            while True:
                dmx.hold(1)
    except KeyboardInterrupt:
        print("\nBlackout.")
        dmx.blackout()


if __name__ == "__main__":
    main()
