# 103 — Three audio sources (mic/line-in, file through the speakers, silence) behind one callback

- **Status:** proposed — prototype default, team to confirm
- **Module:** M1 Signal Processing of Audio
- **Decided by:** first prototype build · **Date:** 2026-11-08

## Context

The demo must work with no live audio, and the real system must work from a room mic or a mixer
line-in. Every other module should not care where the sound came from.

## Options considered

1. **Mic only.** Matches the baseline. A demo then depends on room noise and speaker placement.
2. **Mic plus a file that is analysed but not played.** Repeatable, but the audience hears nothing,
   and the lights cannot be judged against the sound.
3. **Mic plus a file that is played through the speakers, with the pipeline fed the exact blocks
   handed to the speakers.** Repeatable, audible, and the lights follow what is heard.

## What the prototype does and why

Option 3, plus a silence source. All three call `on_block(samples, capture_time)` once per 1024-sample
block (23.2 ms at 44.1 kHz), mono float32. Stereo inputs are averaged to mono.

- **MicSource:** `sounddevice` (PortAudio) input stream, device picked in the UI or with `--device N`
  (`--list-devices` lists them). Asks for "low" latency.
- **FileSource:** reads wav/flac/mp3 (libsndfile), other formats via `afconvert`/`ffmpeg`; resamples to
  44.1 kHz; loops. Playback runs in the speaker's own callback, so the speaker's clock paces the
  pipeline. Measured device buffer on the MacBook speakers: about 41 ms. Because the pipeline sees each
  block ~41 ms *before* it is heard, file playback hides most output delay (see 115). `--mute` paces
  with a clock instead.
- **SilenceSource:** keeps the show ticking (idle glow) when there is no input.

## What would change our mind / how to test it

- Mic vs line-in is the real M1 question: record the same set both ways and compare onset and beat
  accuracy (M3) and recognition rate (M5). If line-in is far better, the baseline should recommend it.
- If the mic picks up the lights' own fan noise or the crowd too strongly, add a high-pass filter or
  a noise gate per source.

## Open questions for the module owner

- Is 1024 samples the right block? 512 halves capture delay (11.6 ms) but doubles the tick rate and
  halves frequency resolution per block.
- Should M1 own a "which input is better right now" check (level, clipping) for the operator?

## Owner's reasoning (when confirmed)

> (to be written by the M1 owner in their own words)
