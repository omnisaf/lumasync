# 110 — Mood (valence, arousal) is a labelled placeholder heuristic until a trained model replaces it

- **Status:** proposed — prototype default, team to confirm
- **Module:** M5 Machine Learning: Mood (+ music recognition)
- **Decided by:** first prototype build · **Date:** 2026-11-08

## Context

`MusicContext` has `valence` (sad ↔ happy) and `arousal` (calm ↔ intense), each −1..1 or `None`.
M4 and the UI need something flowing through those fields now; the real model is the M5 owner's work.

## Options considered

1. **Leave them `None`.** Honest; M4's mood path is then never exercised.
2. **A simple heuristic, clearly labelled.** Exercises the path; risks being mistaken for the result.
3. **Train a quick model now** on DEAM (Database for Emotional Analysis in Music: ~1800 songs with
   per-second valence/arousal labels). Real, but it is the M5 owner's design to make.

## What the prototype does and why

Option 2, labelled everywhere (`IS_PLACEHOLDER = True`, the UI note, this record). Smoothed over ~5 s:
arousal from loudness, flux (busy-ness) and centroid (brightness), which correlate with arousal in the
literature; valence from brightness only, which is a weak cue. Returns `None` in silence and for the
first second. M4 uses mood only to nudge the default ("house") palette when no preset is active: warm
hues for positive valence, cool for negative, more saturated for higher arousal.

## What would change our mind / how to test it

- Replace with a regression model trained on DEAM features. Keep the interface
  `process(frame) -> (valence, arousal)`. Report error against DEAM test labels, then check it live from
  a mic: per the vision doc, mood joins the baseline only if it works live from a mic.

## Open questions for the module owner

- Which features can be computed live within the 23 ms tick, versus once a second on the slow path?

## Owner's reasoning (when confirmed)

> (to be written by the M5 owner in their own words)
