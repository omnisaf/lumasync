# 116 — Three reactive looks (pulse, bands, chase) plus "auto", which picks by section and crossfades

- **Status:** proposed — prototype default, team to confirm
- **Module:** M4 Superposition of Inputs and Latency Optimization
- **Decided by:** first prototype build · **Date:** 2026-11-08
- **Code:** `SuperpositionEngine._render`, `_auto_look`

## Context

The base layer needs a few distinct ways to turn music into light. A "look" here is a rule that gives
each fixture a colour (from the current palette) and a drive value 0–1.

## Options considered

1. **One look.** Simplest; gets boring within a song.
2. **A few hand-written looks + an automatic chooser (chosen).** Variety with little code; each is easy
   to explain and test.
3. **A generative/learned show.** Interesting add-on later (the vision doc's "AI-drafted show").

## What the prototype does and why

- **pulse:** all fixtures flash on the beat (envelope `exp(−4 × phase)`, shifted early by the beat lead),
  plus 25 % bass. Even/odd fixtures use neighbouring palette colours; colours step each bar (4 beats).
  Above 165 BPM it pulses every other beat (keeps under the flash cap). Without a tempo lock, it follows
  onsets.
- **bands:** fixtures map to frequency bands, mirrored (centre = bass, edges = highs); brightness = band
  level with 20 ms attack and 180 ms release smoothing (so it shimmers instead of flickering, which also
  keeps the flash cap quiet); colours run along the palette gradient.
- **chase:** a bright spot moves one fixture per beat (two per beat if energy is high and tempo < 140);
  colours rotate with the beat; 15 % bass underneath. Without tempo, it steps on onsets.
- **auto (default):** no tempo → bands; within 16 beats after a drop → chase; falling energy
  (breakdown) → bands; otherwise pulse. A choice is held at least 4 s and changes on a beat. Looks
  crossfade over 0.8 s (here an output blend is fine: both looks share the palette and beat clock).

## What would change our mind / how to test it

- Watch a full recorded set with auto on. If looks change more than every ~15 s on average, or a drop
  is missed, tune the rules. If the cap shows HOLDING often, the look is too flashy for the cap.

## Open questions for the module owner

- Fixture position: looks assume fixtures in a line, in patch order. Should the patch give positions
  (left/right, height) so chases and band layouts follow the real stage?
- Blinders (white only) at the venue: separate "accent-only" group?

## Owner's reasoning (when confirmed)

> (to be written by the M4 owner in their own words)
