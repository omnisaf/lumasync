# 118 — Colour channels get sRGB → linear; the dimmer gets a 2.2 gamma

- **Status:** proposed — prototype default, team to confirm
- **Module:** M2 Real-Time Adaptive Lighting Control and LED Interface
- **Decided by:** first prototype build · **Date:** 2026-11-08

## Context

M4 sends colours as screen colours (sRGB, like `#ff8000`) and a dimmer where 0.5 should *look* half as
bright. LEDs are driven linearly: DMX 128 gives about half the light, which looks much brighter than half.

## Options considered

1. **Send values straight through.** Colours look washed out and fades look like they jump at the bottom.
2. **Gamma on everything.** Better, but mixes up two jobs (colour accuracy and brightness feel).
3. **Linearise the colour (sRGB → linear light), gamma 2.2 on the dimmer (chosen).** Colour ratios match
   the screen preview; fades look even.

## What the prototype does and why

Option 3. Fixtures with a dimmer channel: colour channels = linear colour × 255, dimmer = dimmer^2.2 × 255.
Fixtures without one: colour channels = linear colour × dimmer^2.2 × 255. Tests check exact bytes
(e.g. 0.5 dimmer → 55; sRGB 0.5 → 55).

## What would change our mind / how to test it

- Fade a fixture from 0 to full over 5 s next to the UI preview. If the bottom of the fade still jumps,
  the fixture already applies its own curve: set `dimmer_gamma` to 1.0 in its profile.
- Hold the same orange on the screen and the par. If they differ a lot, add per-profile colour
  calibration (LED primaries differ from screen primaries).

## Open questions for the module owner

- Does the LPC1818 have its own dimmer curve setting in the menu?

## Owner's reasoning (when confirmed)

> (to be written by the M2 owner in their own words)
