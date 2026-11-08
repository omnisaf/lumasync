# 109 — Recognition confidence needs a margin over noise and the runner-up; matching runs once a second off the fast path

- **Status:** proposed — prototype default, team to confirm
- **Module:** M5 Machine Learning: Mood (+ music recognition)
- **Decided by:** first prototype build · **Date:** 2026-11-08

## Context

The raw match result is a "pile size": how many moments of the clip line up with one song at one
time offset. M4 needs a 0–1 confidence it can threshold, and an unknown song must stay near zero.

## Options considered

1. **Raw pile size with a fixed threshold.** Simple. Depends on clip length and song density.
2. **Ratio best / runner-up.** Ignores the absolute size; two tiny piles can give a big ratio.
3. **Margin over both** a noise floor and the runner-up song, through a saturating curve.

## What the prototype does and why

Option 3: `confidence = 1 − exp(−(best − max(1.5 × runner_up, 8)) / 8)`, or 0 if negative.
M5 reports `song_id` only when confidence ≥ 0.2.

Calibration (synthetic library of 3 songs, `tests/test_m5_recognition.py` and offline runs):

| Clip (8 s) | Pile size | Confidence |
|---|---|---|
| Clean / file playback | 300–1000 | 1.00 |
| 10 dB SNR noise | 20–50 | 0.7–1.0 |
| 5 dB SNR + reverb + speaker band-limit | 13–137 | 0.45–1.0 |
| 40 unknown synthetic tracks | ≤ 7 | 0.00 (no false accepts) |

Before two fixes (ignore < 150 Hz; one vote per clip moment), unknown tracks reached confidence
0.86, because identical drum samples and identical synth chords in different synthetic songs produced
big false piles. Real songs share samples too (the same 909 kick in many house tracks), so both fixes
are kept.

**Schedule:** `process()` only buffers audio (about 0.1 ms per tick). Every 1 s, once 3 s are buffered,
a worker thread matches the last 8 s. First recognition in the app: 3.4 s after start, confidence 0.93.

**M5 reports raw evidence; it does not hold or smooth.** Deciding "this song is really playing"
(hysteresis) is done in M4 (113), where the cost of a wrong decision is felt.

## What would change our mind / how to test it

- Recalibrate on real songs through a real room. If unknown real songs reach > 0.3, raise the noise
  floor; if real matches stay below 0.5, lower it or lengthen the clip.

## Open questions for the module owner

- **Module name (team decision, not decided here):** song recognition currently lives in module 5,
  which the proposal names "Machine Learning: Mood and Crowd-Energy Estimation". The team may rename it
  "Machine Learning: Music Recognition and Mood Estimation". Recognition could also be argued to belong
  elsewhere. This record leaves the choice to the team.
- Should M5 also report the position in the song (the match already knows it, shown in the UI)? That
  would allow timed cues (an add-on) but needs a new optional contract field.

## Owner's reasoning (when confirmed)

> (to be written by the M5 owner in their own words)
