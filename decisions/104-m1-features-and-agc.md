# 104 — M1 features: 2048-point Hann FFT, six fixed bands with adaptive gain, log-compressed flux

- **Status:** proposed — prototype default, team to confirm
- **Module:** M1 Signal Processing of Audio
- **Decided by:** first prototype build · **Date:** 2026-11-08

## Context

`AudioFrame` needs `rms`, six bands each 0–1, the spectrum, the centroid and the flux, every 23 ms.
"0–1" is the hard part: the same song is 30 dB quieter from a far mic than from line-in, and a
quiet song should still move the lights.

## Options considered

For the spectrum: (a) FFT of just the 1024-sample block (21.5 Hz bins would be 43 Hz bins; poor bass
resolution); (b) **2048-point FFT over the last two blocks** (50 % overlap: 21.5 Hz bins, still one
result per block, adds no delay because the newest block is always included); (c) a constant-Q /
mel filter bank (better matches hearing, more code).

For 0–1 normalisation:
1. **Fixed dB scale** (e.g. −60..0 dBFS → 0..1). Predictable, but a quiet mic never reaches the top.
2. **Adaptive gain (AGC)** per band: track each band's recent loud level ("peak") and quiet level
   ("floor"), and map between them. Works at any input level; can over-amplify noise if unguarded.
3. **Divide by a running maximum.** Simple; one loud hit squashes everything for a long time.

## What the prototype does and why

- Hann window, 2048-point FFT, magnitude scaled so a full-scale sine reads 1.0.
- Bands: sub 20–60, bass 60–250, low-mid 250–500, mid 500–2000, high-mid 2–4 k, high 4–16 kHz Hz.
- **AGC (option 2) with guards:** the peak jumps up at once and falls 1.5 dB/s; the floor falls
  quickly and rises 0.5 dB/s; the window is never narrower than 24 dB (so steady noise is not
  scaled up to full scale); the peak never falls below −50 dB; blocks below −70 dBFS count as silence
  (all bands 0).
- **Flux:** mean of the positive change in log(1 + 1000·|X|) between blocks. The log stops loud bins
  dominating, so a hi-hat counts as well as a kick.
- `rms` is the raw block RMS (linear, 0–1), not normalised, so M3 can see real loudness changes
  (needed for drops).

Measured: M1 takes about 0.3 ms per block. Tests: a 100 Hz sine lights the bass band (> 0.8); the
centroid of a 1 kHz sine reads within 60 Hz; flux on clicks is more than 5× the median between clicks.

## What would change our mind / how to test it

- If the lights "pump" (get brighter in quiet passages because the AGC turned up), slow the peak
  release or raise the minimum window. Test: play a song with a long breakdown and watch the bands.
- If beat tracking on bass-heavy music misses beats, try a flux restricted to < 250 Hz for M3.

## Open questions for the module owner

- Should the AGC time constants differ per band (bass changes slower than hi-hats)?
- Is a mel / constant-Q band split worth it for the report's literature comparison?

## Owner's reasoning (when confirmed)

> (to be written by the M1 owner in their own words)
