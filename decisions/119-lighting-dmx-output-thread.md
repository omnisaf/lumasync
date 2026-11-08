# 119 — DMX goes out from its own thread at a steady 30 fps, latest frame only, and survives a missing cable

- **Status:** proposed — prototype default, team to confirm
- **Module:** M2 Real-Time Adaptive Lighting Control and LED Interface
- **Decided by:** first prototype build · **Date:** 2026-11-08
- **Code:** `lumasync/m2_lighting/outputs.py`

## Context

DMX must be resent continuously (lights expect frames ~30–44 times a second), with steady timing:
jitter shows up as shimmering. The FTDI cable is "dumb": the laptop makes all the timing. For the demo,
the cable may or may not be plugged in, and may be plugged in mid-demo.

## Options considered

1. **Send a frame from the engine tick.** No thread, but frames would follow the audio rate (43/s) and
   any engine delay.
2. **Own thread at a fixed rate, sending the latest universe (chosen).**
3. **Hand timing to hardware** (ESP32 node with sACN, docs/research/dmx-path.md). Best timing; not built.

## What the prototype does and why

Option 2, reusing the send logic of `tools/dmx_test.py`: 250 000 baud, 8N2; break by holding the line
low (`break_condition`) ≥ 88 µs (200 µs used), mark-after-break ≥ 8 µs, start code 0 + 512 bytes;
`--break-mode baud` as the fallback. 30 fps.

- The engine calls `set_frame()`; the thread always sends the **newest** universe (no backlog), and
  records how old it was (`age_ms`).
- **No cable:** state "searching", rescan every 2 s. Only `/dev/cu.usbserial*` (and Linux
  `/dev/ttyUSB*`) are ever opened, never Bluetooth serial ports (this Mac has several).
- **Cable pulled:** the error is caught, the port closed, back to searching. The app never crashes.
- **On exit:** three blackout frames.
- `--no-dmx` never opens a port. `VirtualOutput` feeds the UI preview and the 72-channel DMX monitor.
- `SacnOutput` is a stub for the ESP32 node.

Verified: the app ran 45 s with DMX enabled and no cable: state "searching", 0 frames, no errors in the
show. Not yet verified with the cable and real lights.

## What would change our mind / how to test it

- With the cable and a light: run the app and `tools/dmx_test.py` side by side; if the app flickers and
  the tool does not, the GIL (decision 101) is delaying the thread: move DMX to its own process.
- Measure frame spacing (timestamp each send): jitter above ~5 ms → consider the ESP32/sACN path sooner.

## Open questions for the module owner

- Send only the channels in use (112 for the venue) for ~5 ms frames? Some fixtures need full frames.

## Owner's reasoning (when confirmed)

> (to be written by the M2 owner in their own words)
