# Module 3 — Rhythm, Tempo and Transient Detection

**Owner:** Remsha · **Folder:** `lumasync/m3_rhythm/` · **Decision records:** 400–499

## The question this module answers

**When do things happen in the music?** The beat, the tempo, the drum hits, the build-ups and the
drops. Module 1 is about frequency (what); this module is about time (when).

## Inputs and outputs (contract terms)

- **In:** `AudioFrame` from module 1, every ~23 ms. Mostly `flux` (spectral flux), `bands`, `rms`
  and `t`.
- **Out:** `RhythmState`, every tick:
  - `bpm` (beats per minute; 0 = not locked yet) and `confidence` (0–1);
  - `beat`: true on the tick a beat lands; `beat_phase`: 0–1 position between beats;
  - `onset`: **transient** strength this tick (a transient, or onset, is the sharp start of a
    sound, like a drum hit);
  - `energy_trend`: −1…1, falling or rising energy (build-ups);
  - `drop`: true on the tick a drop is detected.

Read by: module 4, which turns beats into flashes and changes.

## What the prototype does now

A simple live beat and tempo tracker built on spectral flux. It is a starting point, not a design.
See the code for details.

## The core engineering challenge (report-worthy)

**Track the beat live, using only the past, and say when the next beat will land.**

- **Causal vs offline.** Offline beat trackers (like the one in librosa) see the whole song. A live
  system only has what it has heard. That is harder, and it is the real problem.
- **Prediction hides delay.** By the time a beat is detected, it is already late. Predicting the
  next beat from the tempo and phase lets module 4 send the light cue early (Stark et al. 2009).
- **Picking real onsets.** Flux spikes on many things. A fixed threshold fails in quiet passages.
  An **adaptive threshold** (relative to the median of the last few seconds) is the standard fix.
  Run it per band: kick in the bass, snares and hats in the upper mids.
- **Tempo errors.** Trackers often lock to half or double the tempo (64 vs 128 BPM). DJ mixes add
  another twist: during a transition, two tracks play at once, sometimes at slightly different
  tempos.
- **What is a "drop"?** There is no single definition. Pick one you can measure (for example, a
  sharp rise in bass energy after a build), and justify it.

## How to test it alone

- Feed recorded audio, or fake `AudioFrame`s, in. No other module needed.
- Ground truth: a public beat-annotated dataset (choose one and cite it), plus your own
  recordings with beats tapped in by hand.
- Compare against offline references (librosa, madmom) on the same tracks.
- Measure: beat timing error, how long until the tempo locks, tempo accuracy, and behaviour on
  mic vs line-in recordings.

## Suggested Dec 10 target

A live tracker running on recorded tracks, with a results table against ground truth: beat
error, lock time, tempo accuracy, and the delay between the real beat and `beat = True`.

## Research vs the prototype

Research: [research/rhythm-tempo-transient-research.md](research/rhythm-tempo-transient-research.md) (Remsha, Nov 2026).

**Already agrees:**
- Spectral flux as the onset detection function, with an adaptive threshold built on the moving median and a minimum gap between hits. The prototype uses median + k × mean absolute deviation over the last 0.5 s and a 100 ms gap ([decision 105](../../decisions/105-m3-onset-detection.md)).
- Tempo by autocorrelation of the onset curve, with a confidence value ([decision 106](../../decisions/106-m3-tempo-and-beat-tracking.md)).
- Beat prediction so lights fire early, on the beat. The prototype fires beat pulses ~40 ms early to hide output latency.

**Open, for the owner to decide:**
- **Band split for drum types (kick 60–250 Hz vs snare/hats 2 kHz+).** Not in the prototype. It needs new optional fields in `RhythmState` (for example `kick` and `snare` onset strengths), so it goes through the contract process. A strong report item.
- **Low-confidence fallback for ballads.** The research says: when confidence is low, stop following beats and use slow transitions. `RhythmState.confidence` already exists. Agree with Sathvik (M4) who acts on it: M3 reports, M4 decides.
- **Which onset function.** The research's comparison table (energy, HFC, flux, SuperFlux, phase deviation) is the decision record waiting to be written. Measure on beat-annotated tracks with `mir_eval`.
- **Benchmarks.** madmom (offline) and BTrack as references, aubio as a real-time check: pick the comparison set for the report.

## Open decisions for the owner

1. Method: flux + autocorrelation, dynamic programming (Ellis 2007), or an online neural tracker
   (madmom). Accuracy vs CPU vs delay.
2. Adaptive threshold design and window length.
3. How to handle half/double tempo and DJ transitions.
4. A measurable definition of `drop`.
5. Whether external tempo (Ableton Link, Pro DJ Link) should override the estimate when present.
   That would touch the contract and module 4.

## Starting references

- Bello et al., "A tutorial on onset detection in music signals," *IEEE TSAP*, 2005.
- Scheirer, "Tempo and beat analysis of acoustic musical signals," *JASA*, 1998.
- Ellis, "Beat tracking by dynamic programming," *JNMR*, 2007.
- Böck, Krebs & Widmer, "Joint beat and downbeat tracking with RNNs," *ISMIR*, 2016 · madmom (2016).
- Stark, Davies & Plumbley, "Real-time beat-synchronous analysis of musical audio," *DAFx*, 2009.
- Müller, *Fundamentals of Music Processing*, ch. 6, 2015.

Full list: [docs/research/citation-bank.md](../../docs/research/citation-bank.md).
