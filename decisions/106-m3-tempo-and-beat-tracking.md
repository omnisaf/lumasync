# 106 — Tempo by autocorrelation with a 120 BPM prior; beats from a comb-filter phase estimate and a PLL

- **Status:** proposed — prototype default, team to confirm
- **Module:** M3 Rhythm, Tempo and Transient Detection
- **Decided by:** first prototype build · **Date:** 2026-11-08

## Context

M4 needs `bpm`, a `beat` flag on the tick each beat lands, and `beat_phase` (0–1 between beats) so
it can fire pulses slightly early and hide output delay (115). It must lock within a few seconds and
hold through short quiet gaps.

## Options considered

1. **Autocorrelation of the onset function** (compare the ODF with a delayed copy; the delay where they
   line up best is the beat period). Standard (Ellis 2007, "Beat tracking by dynamic programming",
   uses it for the tempo step). Simple, cheap, explainable.
2. **Comb-filter bank** (Scheirer 1998): a bank of resonators at many tempi. Similar results, more code.
3. **Dynamic programming beat tracker** (Ellis 2007) or a neural tracker (madmom). Better on hard
   music; DP needs look-ahead or a full song; neural needs a model and dependencies.

## What the prototype does and why

Option 1 for tempo, a comb filter for phase, and a **phase-locked loop** (PLL: a clock that keeps
ticking at the tempo and is nudged toward each new phase measurement) to emit beats.

- Every 0.5 s, autocorrelate the last 8 s of ODF (smoothed with a 5-frame Hann window so a period that
  falls between whole frames is not missed). Range 70–180 BPM.
- Score = ac(L) + 0.5·ac(2L), times a **log-Gaussian prior** centred on 120 BPM, 0.7 octaves wide.
  A prior is a gentle preference used when two tempi look equally good; it is how "128 or 64?" is
  usually resolved. With a 1.0-octave width, a breakbeat whose pattern repeats every 2 beats locked at
  70 instead of 140; 0.7 fixed that without breaking 90 BPM tracks.
- Precision: refine the peak at 4×, 3× or 2× the period (error divides by k) with parabolic
  interpolation.
- Lock after two estimates agree within 3 %. While locked: small changes are smoothed; a different
  tempo must repeat 3 times to take over; **an estimate at exactly 2× or ½× is ignored** (octave guard,
  so hi-hat eighths do not double the tempo).
- Phase: slide a pulse train at the period over the ODF; the best offset gives the last beat time; the
  PLL moves the predicted next beat halfway toward it each update.

Measured (synthetic tests, `tests/test_m3_rhythm.py` and offline runs):
click tracks 90 / 128 / 140 BPM → 89.98 / 127.96 / 139.95; lock after 4.6 s; beat times within
6 ms on average (13 ms worst) of the clicks after 10 s; the three demo songs 127.9 / 92.0 / 139.9;
10 random synthetic tracks (95–135 BPM) all within 0.1 BPM. About 0.15 ms per block.

## What would change our mind / how to test it

- Evaluate on real, beat-annotated music (e.g. GTZAN beat annotations, Ballroom dataset, or tapped
  venue recordings) with the standard F-measure (±70 ms). If it is below ~0.8 on dance music, try the
  DP tracker or a band-limited (kick) ODF.
- Synthetic music is easy: real tracks with swing, live drums or tempo drift will be worse. That is
  the main known weakness.

## Open questions for the module owner

- Octave errors on half-time / double-time genres (trap, drum & bass): should the operator be able to
  tap or halve/double the tempo from the UI?
- Should M3 also output bar position (downbeat), so M4 can change colours on bar 1?
- Ableton Link / Pro DJ Link would give exact tempo from DJ gear: an add-on input that could replace
  this estimate when present.

## Owner's reasoning (when confirmed)

> (to be written by the M3 owner in their own words)
