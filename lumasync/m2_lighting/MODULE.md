# Module 2 — Real-Time Adaptive Lighting Control and LED Interface

**Owner:** Mo · **Folder:** `lumasync/m2_lighting/` · **Decision records:** 300–399

## The question this module answers

**How does "what the light should look like" become real light, on whatever rig is plugged in?**

## Inputs and outputs (contract terms)

- **In:** `LightIntent` from module 4. A list of `FixtureIntent`, one per light or group, each
  with `rgb` (0–1 each), `dimmer` (0–1) and `strobe` (0 = off, up to 1 = fastest). Plus `source`,
  a label of which layers made it. It never says which DMX channel.
- **Uses:** a **patch file**: each light's profile (what its channels do), mode, and start
  address.
- **Out:** DMX frames (512 channel values, 0–255) sent through the USB-DMX cable; the on-screen
  virtual preview; later **sACN** (DMX over a network) to an ESP32 node and WLED LED strips.

## What the prototype does now

A first-draft patch and output driver: maps each `FixtureIntent` onto channels from a patch file,
and sends frames to the cable or to the preview. See the code for details. Wiring and DMX basics:
[docs/HARDWARE.md](../../docs/HARDWARE.md).

## The core engineering challenge (report-worthy)

**One abstract look, any rig, steady timing.**

- **Colour mapping.** `LightIntent` speaks RGB. The LPC1818 has red, green, blue, lime, amber and
  UV. How do you make "warm red" on six emitters? Blinders are white only. How does an RGB intent
  land on them? This is colour science plus calibration (measure it, with a phone camera or a
  light meter).
- **Rescaling to any rig.** A patch file and fixture profiles (Open Fixture Library JSON) instead
  of hard-coded channels. Later: spatial layout, so a "sweep left to right" works on any rig.
- **Timing.** The FTDI cable makes the laptop do the timing, so frames can jitter (uneven gaps,
  seen as shimmering fades). Measure frame rate and jitter under load. Decide when to move to the
  ESP32 node.
- **Fixture quirks.** LPC1818 channel 9 must stay at 0–50 or the light runs its own programs.
  Possible address overlap in 11-channel mode.
- **Output drivers as plug-ins.** USB serial now, sACN later, same patch.

## Safety

Module 4 applies the flash-rate cap (no more than 3 flashes per second) to the combined output.
This module must translate `strobe` faithfully and **never add flashing of its own**. Whether to
add a second, output-side guard here is an open decision.
([decisions/006](../../decisions/006-flash-rate-cap.md))

## How to test it alone

- Fake `LightIntent` streams from `lumasync/fakes.py` → virtual preview. No audio needed.
- `tools/dmx_test.py walk` on a real light to learn its channel map, then write its profile.
- Fake `LightIntent` → the real Resonnce rig. Check the far end of the chain for flicker.
- Measure: frames per second, jitter, and delay from intent to visible light (for example, a
  slow-motion phone video of a light and an on-screen marker).

## Suggested Dec 10 target

Fake `LightIntent` drives real Resonnce lights over the cable. LPC1818 and blinder profiles
written. Patch file format chosen. Frame timing measured on the cable.

## Open decisions for the owner

1. Patch file format: a subset of Open Fixture Library JSON, or our own.
2. RGB → multi-emitter colour mapping (simple rule, lookup table, or calibrated model).
3. Strobe: use the light's own strobe channel, or flash the dimmer from software?
4. When to switch from the cable to the ESP32 + sACN node.
5. LED strip for the expo mini rig: which strip, how many LEDs, how to patch it.

## Starting references

- ANSI E1.11-2024 (DMX512-A) · ANSI E1.31-2025 (sACN) · Art-Net 4 specification.
- Open Fixture Library (https://open-fixture-library.org) · `esp_dmx` · WLED.
- Worldsemi WS2812B datasheet (in our proposal).
- Zlatev et al., "Design and research of a sound-to-RGB smart acoustic device," *MTI*, 2023.
- Full DMX research: [docs/research/dmx-path.md](../../docs/research/dmx-path.md).
