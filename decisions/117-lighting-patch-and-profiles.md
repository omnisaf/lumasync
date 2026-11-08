# 117 — Rigs are JSON: a patch file (which light, which address) and profiles (what each channel does), all marked unverified

- **Status:** proposed — prototype default, team to confirm
- **Module:** M2 Real-Time Adaptive Lighting Control and LED Interface
- **Decided by:** first prototype build · **Date:** 2026-11-08
- **Files:** `lumasync/m2_lighting/patch.json`, `profiles.json`

## Context

`LightIntent` says what each logical fixture should look like, never which DMX channel. M2 must turn it
into bytes for a real rig, and a new rig should be a new file, not new code. The venue's LPC1818 mode
is not confirmed (docs/research/dmx-path.md).

## Options considered

1. **Hard-code the channel map.** Fast for one light; breaks for any other rig.
2. **Our own small JSON patch + profiles (chosen for now).** Easy to read and edit by hand.
3. **Open Fixture Library (OFL) JSON** (the team's planned format, docs/HARDWARE.md). Standard and
   exportable; more complex, and the LPC1818 is not in OFL yet.

## What the prototype does and why

Option 2, kept close to OFL ideas (a profile = one mode's channel list) so moving to OFL later is a
converter, not a redesign.

- **Patch:** a list of fixtures in M4's order: name, profile, start address (or `null` for preview-only).
  Default: 8 LPC1818 at the venue's addresses 1, 11, … 71.
- **Profiles** (all `verified: false`):
  - `generic_rgb_3ch`, `generic_drgb_4ch`;
  - `betopper_lpc1818_7ch_guess`: dimmer, R, G, B, W?, strobe, program (the default; a first guess);
  - `betopper_lpc1818_7ch_manual`: R, G, B, Lime, Amber, UV, CTO (from manual v6.0; no dimmer);
  - `betopper_lpc1818_11ch_manual`: dimmer, R, G, B, Lime, Amber, UV, strobe, program, speed, CTO.
  The guess and the manual disagree. That is exactly what `tools/dmx_test.py walk` must settle.
- **Safety:** `fixed` channels (strobe, program, speed, and unused colours) are always sent at their
  "off" value, and strobe/program/speed are forced to 0 even if a profile forgets. On the LPC1818,
  program channel values above 50 run built-in programs and ignore us.
- Checks at load: address range within 1–512; overlapping channels and unverified profiles are listed
  as warnings in the log and the UI.

## What would change our mind / how to test it

- Run `tools/dmx_test.py walk --start 1 --count 11` on one LPC1818 and write down each channel. Fix the
  profile, set `verified: true`, and switch the patch to it.
- If a second fixture type arrives (the blinders), writing its profile should take minutes. If it takes
  code changes, the format is wrong.

## Open questions for the module owner

- At the venue's 10-channel spacing, the 11-channel mode overlaps by one channel (see HARDWARE.md).
  Re-address, or use the 7-channel mode?
- Move to OFL format now, or after the first venue session?
- Use the white/amber/lime LEDs (`white_mode: min_rgb` exists but is off)?

## Owner's reasoning (when confirmed)

> (to be written by the M2 owner in their own words)
