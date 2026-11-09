# 003 — Five technical modules, one per person, joined only by the feature stream

- **Status:** accepted for modules 1, 2 and 4 (in the proposal). **Open:** owners of 3 and 5,
  and module 5's name and scope.
- **Module:** whole team
- **Decided by:** the team, in the Sep 27 2026 proposal · **Date:** 2026-09-27

## Context

The course requires one technical module per person, balanced, built in parallel. Banned names:
hardware, software, GUI, front-end, back-end, testing, integration. Two modules (audio, lighting)
were already written into the draft report. We needed five that do not overlap and do not wait on
each other.

## Options

1. **A straight chain** (capture → features → beat → ML → lights), each stage waiting for the one
   before. Simple to explain. Works in series, which the course forbids, and the last module
   cannot start until the rest work.
2. **Keep a "Real-Time System Integration and Latency Optimization" module.** Covers the glue.
   "Integration" is a banned name, and an integration module waits on every other module.
3. **Five modules joined by one shared data format** (the feature stream), each tested alone
   against fake or recorded data. The integration work (latency budget, data flow) moves into a
   real technical module: superposition.

## Decision

Option 3.

| # | Module | Question it answers | Owner | Tests alone with |
|---|---|---|---|---|
| 1 | Signal Processing of Audio | *What* is in the sound: capture, conditioning, FFT, frequency bands. Mic vs line-in. | Youtso | Recorded audio files |
| 2 | Real-Time Adaptive Lighting Control and LED Interface | How lighting intent becomes real light: DMX and LED strips. Later: one show on any rig. | Mo | Fake `LightIntent` |
| 3 | Rhythm, Tempo and Transient Detection | *When* things happen: beat, tempo, onsets, drops. M1 is frequency; M3 is time. | Remsha | Beat-annotated audio |
| 4 | Superposition of Inputs and Latency Optimization | How layers combine without wrecking the output, fast enough to look in time. | Sathvik | Fake features + a MIDI controller |
| 5 | Machine Learning: Mood and Crowd-Energy Estimation | What the music feels like (valence, arousal); add-on: crowd energy from a camera. | Rohan | Public labelled mood datasets |

The shared format is `lumasync/contract.py`. See [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).

## Why

- M1 (frequency) and M3 (time) were overlapping in early drafts. Splitting them by "what" vs
  "when" gives each a clear job and its own literature.
- Superposition is the project's unique idea and its hardest problem (non-linear blending,
  priorities, the flash-rate cap, the latency budget). It deserves a module, and it replaces the
  banned "integration" module with real engineering.
- Mood estimation is a real ML problem with public datasets, so module 5 can start without
  anyone else's code.

> (owners of modules 3 and 5 to add their reasoning when they confirm)

## Open: module 5's name and scope

The prototype puts **song recognition** in module 5: matching live audio against our song
library by **audio fingerprint** (a compact signature of a recording, as Shazam does). That is
not in the module's current name. Options for the team:

1. Keep the name. Recognition counts as part of the ML module's work.
2. Rename to **"Machine Learning: Music Recognition and Mood Estimation"**, with crowd energy as an
   add-on.
3. Move recognition elsewhere (for example into module 4's song-preset handling).

Weigh: does the name match the work the owner will be marked on? Is module 5 balanced against
the others (recognition + mood may be more than one module's work; mood alone may be enough)?
Modules change only if necessary. Record the answer as `decisions/007-module-5-scope.md`.

## How we'd know we were wrong

- A module cannot test anything for two weeks without another module's code → the split is not
  really parallel; fix the contract or the fakes.
- One module ends up with far more work than the others by Dec 10 → rebalance as a team.
