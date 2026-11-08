# 004 — DMX output: USB cable first to learn the rig, then an ESP32 node fed by sACN

- **Status:** accepted (September 2026, carried over from our earlier decision record)
- **Module:** M2 (affects M4 through `LightIntent`)
- **Decided by:** the team, from the DMX research · **Date:** 2026-09-24

## Context

We need the laptop to drive real DMX lights (the Resonnce rig) and cheap LED strips, with one code
path, as cheaply as possible. DMX needs steady timing. Full research:
[docs/research/dmx-path.md](../docs/research/dmx-path.md).

## Options

1. **FTDI USB-DMX cable** (about CAD 22). The laptop makes the timing. Not isolated. Can flicker.
2. **ESP32 + isolated M5Stack Unit DMX** (about USD 15), running `esp_dmx`, fed by sACN from the
   laptop. The ESP32 makes the timing. 5 kVrms isolation.
3. **Commercial interface** (DMXking ultraDMX MAX USD 110; Enttec DMX USB Pro about CAD 229). Known
   good. Several times the cost.

Test that tells them apart: a steady 30–44 frames per second with no visible flicker on the far
end of the chain, while the laptop runs the full app.

## Decision

1. **Now:** the FTDI cable, only to learn the rig (each light's mode, address and channel map) and
   for early tests. `tools/dmx_test.py` does this.
2. **The real build:** the ESP32 + isolated Unit DMX node. The laptop always sends **sACN** (DMX
   over a network). A second ESP32 running WLED turns the same packets into LED strip light.
3. **One patch file per rig.** Fixture layouts follow Open Fixture Library profiles. A new rig is a
   new patch file, not new code.
4. Fallback if the DIY node stalls: the ultraDMX MAX.

## Why

Summarised from the research:
- The cheap cable is the fastest way to learn the rig, but its timing depends on how busy the
  laptop is. Good for a diagnostic, not for a show.
- The ESP32 node gives "pro" timing and isolation at clone prices, which fits "cheap and DIY".
- Sending sACN from the laptop means LED strips and DMX lights use the same packets: one code path,
  and the output stays swappable.

## How we'd know we were wrong

- The cable gives clean output at 30 frames/s under full load → the ESP32 node can wait.
- sACN over Wi-Fi drops frames at the venue → go wired (Ethernet or USB) to the node.
- The Unit DMX send/receive direction pin is a problem on the bench → switch transceiver or use
  the ultraDMX MAX.
