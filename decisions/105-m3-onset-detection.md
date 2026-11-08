# 105 — Onsets: spectral flux above a moving median + 2.5 × mean absolute deviation, 100 ms refractory

- **Status:** proposed — prototype default, team to confirm
- **Module:** M3 Rhythm, Tempo and Transient Detection
- **Decided by:** first prototype build · **Date:** 2026-11-08

## Context

An **onset** is the start of a sound: a drum hit or a new note. M4 uses onsets when there is no
steady tempo yet. The detector must work causally (only the past, no waiting for the future), in
loud and quiet passages alike.

## Options considered

1. **Fixed threshold on flux.** Simple. Fails when the music gets busier or quieter.
2. **Adaptive threshold: moving median + k × spread** (Bello et al., 2005, "A tutorial on onset
   detection in music signals"). Follows the local level; the median ignores single spikes.
3. **Peak picking with look-ahead** (wait one block to confirm a local maximum). More precise; adds
   23 ms delay to every onset.

## What the prototype does and why

Option 2, causal: an onset fires when flux > median(last 0.5 s) + 2.5 × mean absolute deviation, and
at least 100 ms after the previous onset (a **refractory period**: one hit should not count twice).
Strength 0–1 = how far above the threshold, relative to the recent flux peak.

The same flux, minus its local median and clipped at zero, is stored as the **onset detection
function** (ODF) used for tempo (106).

## What would change our mind / how to test it

- Use a beat/onset-annotated dataset (e.g. the onset set from Böck et al., or hand-tapped recordings
  of the venue's music). Report F-measure with a ±50 ms window. If F < 0.7 on dance music, try
  band-wise flux or `k` tuning.

## Open questions for the module owner

- Is `k = 2.5` right for a mic in a loud room (more false onsets from crowd noise)?
- Should onsets be split by band (kick vs hat), so M4 can react differently to each?

## Owner's reasoning (when confirmed)

> (to be written by the M3 owner in their own words)
