# Module 4 — Superposition of Inputs and Latency Optimization

**Owner:** Sathvik · **Folder:** `lumasync/m4_superposition/` · **Decision records:** 500–599
(prototype-era choices: `decisions/1xx`)

## The question this module answers

**How do many inputs become one safe show, fast enough to look in time?** This is the mixing desk
for lighting, and the home of the project's main idea.

## Inputs and outputs (contract terms)

- **In:** `RhythmState` (M3), `MusicContext` (M5), `LiveControls` (the web page; MIDI later),
  `SongPreset` from the song library. If the base show uses band energy, also `AudioFrame` (M1);
  the contract header should then say so.
- **Out:** `LightIntent` for module 2: per light, colour, dimmer and strobe, plus `source` (which
  layers produced it).

## What the prototype does now

A first-draft mixing engine: a base show from the rhythm data, song presets blended in when a
song is recognised, live controls on top, and safety limits at the end. See the code and the
`decisions/1xx` records for the choices made while building it.

## The core engineering challenge (report-worthy)

**Superposition** borrows from physics: the response to many inputs is the sum of the responses
to each. As a mixing stage:

```
L(t) = B(t) + Σ_k w_k · A_k(t)        then        L_out(t) = S(L(t))
```

`B` is the base show from audio. `A_k` is what layer k asks for. `w_k` (0–1) is that layer's
weight; a missing layer has weight 0. `S` is the output stage that keeps the result valid and safe.

The nuances, each one a section of the report:

- **Blending is not linear.** Brightness can add. Colour cannot: red + blue is not "more". Use
  per-parameter merge rules from lighting consoles: **HTP** (highest takes precedence, for
  intensity) and **LTP** (latest takes precedence, for colour).
- **Priorities.** Blackout and the manual song override beat everything. Then presets, then the
  base show. Write the order down and test it.
- **Weights follow confidence.** A mood guess from a noisy mic should count less. Stale input
  (no update for a while) fades to zero, so a dropped layer never freezes the show.
- **Hysteresis on song change.** If recognition flickers between two songs, the colours must not.
  Switch only when `song_confidence` stays above a threshold for a while; switch back only below a
  lower one; crossfade, never cut. `preset_blend` and the per-song `blend` set how much a preset
  overrides the live show.
- **Too much data must not make a mess.** Many active layers can turn into visual noise. Some limit
  on "busyness" (changes per second) may be needed.
- **The safety cap.** No more than 3 flashes per second on the final output, whatever the layers
  do ([decisions/006](../../decisions/006-flash-rate-cap.md)). Test it with the worst inputs you
  can invent.
- **The latency budget.** People notice light more than about 45 ms after sound. Fast features
  (beats, flashes) on a short path; slow ones (mood, recognition) separate so they never delay a
  flash; send cues early using M3's predicted beat; measure the real end-to-end delay and
  calibrate. See [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md#the-latency-budget).

## How to test it alone

- Fake `RhythmState`, `MusicContext` and `LiveControls` from `lumasync/fakes.py` → check
  `LightIntent`. Scripted scenarios: song change with flickering confidence, a layer that stops
  updating, every layer at full, blackout mid-strobe.
- A real MIDI controller for the promised layer.
- Measure: mixing time per tick, end-to-end delay (mic and line-in), flashes per second on output.

## Suggested Dec 10 target

The base layer plus one live MIDI layer mixed together; the flash cap proven by test; measured
end-to-end delay for mic and line-in input.

## Open decisions for the owner

1. How MIDI enters: mapped into `LiveControls`, or a new layer type (contract change, with M2).
2. Merge rule per parameter (HTP/LTP/weighted average) and the priority order.
3. Hysteresis thresholds, hold time and crossfade length for song changes.
4. The flash definition the cap counts (on/off, or a luminance change as the guidelines define it).
5. Where the latency is spent, and what to cut first.

## Starting references

- ETC, "HTP and LTP," *Hog 4 Software Manual*, sec. 2.5.
- ITU-R BT.1359-1 (sound–vision timing) · McPherson et al., "Action-sound latency," *NIME*, 2016.
- Stark et al., *DAFx*, 2009 (beat prediction).
- WCAG 2.2 SC 2.3.1 · ITU-R BT.1702-3 · Harding et al., *Epilepsia*, 2005 · Jordan & Vanderheiden, *ACM TACCESS*, 2024.
- Horvitz, *CHI*, 1999 · Amershi et al., *CHI*, 2019 (people keep control over automatic choices).
