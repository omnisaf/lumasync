# 107 — energy_trend from fast vs slow loudness averages; drop = loudness and bass return together

- **Status:** proposed — prototype default, team to confirm
- **Module:** M3 Rhythm, Tempo and Transient Detection
- **Decided by:** first prototype build · **Date:** 2026-11-08

## Context

Build-ups and drops are the biggest moments in dance music. M4 uses `energy_trend` to pick calmer
looks in breakdowns and `drop` to cut to a new look or fire an accent.

## Options considered

1. **Hand-made rule on loudness and bass** (below). Cheap, explainable, tuned on few examples.
2. **Novelty detection** on a self-similarity matrix (Foote 2000): finds section changes in general,
   needs several seconds of look-ahead.
3. **A trained classifier** on labelled drops. Best in principle; needs a dataset nobody has yet.

## What the prototype does and why

Option 1.
- `energy_trend = tanh((L_1.5s − L_8s) / 6 dB)`, where L_τ is loudness (dBFS) averaged with time
  constant τ. Positive = getting louder (build-up), negative = falling (breakdown).
- `drop` fires when, all at once: the 0.2 s loudness is 3 dB above the 3 s loudness; the bass band's
  fast average jumps 0.35 above its 3 s average and is above 0.55; there has been at least 6 s of
  non-silent audio (so the start of a song is not a "drop"); and the last drop was ≥ 8 s ago.

Measured on the demo tracks: Neon Drive drop at 30.0 s detected at 30.1 s; Slow Bloom's return from
its break at 31.3 s detected at 31.4 s, plus one extra "drop" at 6.7 s when its bass first enters
(arguably right). Breakbeat 140's return at 24 s was missed.

## What would change our mind / how to test it

- Label drops in 20 real tracks by hand; measure hits and false alarms. If false alarms happen more than
  once per track, raise the thresholds or require a preceding build-up (`energy_trend` > 0.3).

## Open questions for the module owner

- Should a build-up (riser) be its own output, so M4 can ramp intensity before the drop?

## Owner's reasoning (when confirmed)

> (to be written by the M3 owner in their own words)
