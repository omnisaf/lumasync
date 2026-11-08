# 108 — Song recognition by landmark fingerprinting (Shazam-style), numpy only, with stated parameters

- **Status:** proposed — prototype default, team to confirm
- **Module:** M5 Machine Learning: Mood (+ music recognition)
- **Decided by:** first prototype build · **Date:** 2026-11-08

## Context

When a song from the library plays, M4 should switch to that song's planned look. That needs
recognising a known recording from ~5–10 s of live audio, possibly through speakers and a mic.

## Options considered

1. **Landmark fingerprinting** (Wang 2003, "An industrial-strength audio search algorithm"; the
   open-source Dejavu): spectrogram peaks paired into hashes, matched by time-offset voting. Robust to
   noise and EQ, exact-recording only, no training.
2. **Chromaprint / AcoustID** (chroma-based fingerprints). Mature, but designed for whole-file lookup
   and needs a compiled library.
3. **Learned audio embeddings** (e.g. a pretrained audio network + nearest neighbour). Can match
   remixes/covers; heavy dependencies and harder to explain.

## What the prototype does and why

Option 1, in about 200 lines of numpy/scipy (`lumasync/m5_recognition/fingerprint.py`):

| Parameter | Value | Why |
|---|---|---|
| Sample rate | 11 025 Hz | Peaks above 5.5 kHz add little and are lost first through speakers/mic |
| FFT / hop | 1024 (93 ms) / 256 (23 ms) | Good frequency detail; fine time steps |
| Peak = local max over | ±8 frames × ±15 bins | Keeps the strongest point in each ~0.4 s × 320 Hz patch |
| Peak floor | median + 10 dB, and max − 70 dB | Ignores the noise floor |
| Lowest bin | ~150 Hz | Kick drums are near-identical across tracks; they caused false matches |
| Density | ≤ 30 peaks / s | Bounds index size and match time |
| Fan-out | 10 next peaks, 1–63 frames later | Standard; hash = 9 + 9 + 6 = 24 bits |
| Votes | one per (song, offset, **clip moment**) | One chord's many harmonics vote once, not dozens of times |
| Stop hashes | ignore hashes seen > 200 times in the index | They carry no information |

The index is three sorted numpy arrays saved as `library/index/fingerprints.npz` plus a JSON with
song ids and file size/mtime (so stale entries are detected). Lookup uses `searchsorted`.

Measured: indexing three 40–45 s songs takes 0.1–0.5 s; matching an 8 s clip takes about 7–18 ms.

## What would change our mind / how to test it

- The real test is **speakers → room → mic** at the venue: play 20 library songs at show volume, record
  10 s clips at several spots, and measure recognition rate and time-to-recognise. Synthetic tests with
  added noise (5 dB SNR) and reverb pass, but a real room was not tested.
- If DJ pitch/tempo changes (playing a track at +4 %) break matching, landmark hashes will fail: that
  needs tempo-invariant hashes or option 3.

## Open questions for the module owner

- Must recognition survive DJ tempo changes? If yes, this method needs rework.
- How large will the library be? At ~50 k hashes per 4-minute song, 500 songs is fine in memory.

## Owner's reasoning (when confirmed)

> (to be written by the M5 owner in their own words)
