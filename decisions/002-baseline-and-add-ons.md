# 002 — Baseline is a mic-only beat show inside a layered platform, plus one MIDI layer; everything else is an add-on

- **Status:** accepted (September 2026, carried over from our earlier decision record)
- **Module:** whole team
- **Decided by:** the team, Sep 26 2026, before the proposal · **Date:** 2026-09-26

## Context

The idea is wide: live audio, DJ data, machine-learning mood, planned looks for known songs,
output to any rig, AI drafts that a person edits. We had to decide what **must** work by April,
and what is optional. The answer shapes every module's Dec 10 target.

## Options (the questions we worked through)

1. **What is the baseline?** (A) a platform that takes plug-in layers, with mic → show as the
   first one; or (B) only mic → beat-synced show, with modularity later. → **A.**
2. **Which layer do we promise on top of the mic?** (A) DJ controls over MIDI; or (B) room energy
   from a camera and AI crowd tracking. → **A in the baseline, B as the first add-on layer.**
3. **What do we show at the expo?** (A) a small live rig visitors can play with, plus a video of
   the full system at Resonnce; or (B) the video plus an on-screen simulator. → **A.**
4. **What is "one third done" by Dec 10?** (A) one thin path end to end on real lights; or (B) the
   show builder and plug-in system first, with real lights in January. → **A, plus a first try at
   one layer.**
5. **Is mood baseline or a layer?** → **Decide by testing.**
6. **Is the list of extras a ranked ladder?** → **No. It is a set, sorted by kind.**

## Decision

**Baseline (must work by April):**
- A platform that takes layers, built on **superposition**: the mic → light stream is the base
  layer; every other input is a layer on top that changes it. If a layer's gear is missing that
  night, the show still runs.
- The base layer: a mic-only, beat-synced show, well developed. Uses beat, tempo and frequency
  bands.
- One promised layer on top: **DJ controls over MIDI** (mixer effects, CDJ loops).
- A simple interface: you build "shows" from modules and tune each one.

**Dec 10:** a very simple interface · the laptop driving the DMX lights at Resonnce · the
baseline prototype · a first test of mixer or DJ input layered on top.

**Expo:** a small live rig visitors can play with, plus a video of the full system at Resonnce.

**Add-ons** (we say "add-on", never "stretch"), sorted by kind:
- *Better inputs* (make everything else work better): clean line-in from the mixer (the easiest),
  DJ player network data (Pro DJ Link).
- *Layers* (change the show): room energy from a camera (the first add-on layer), mood from ML.
- *Built-in options* (part of the system, used or not): planned looks and highlight moments for
  chosen tracks, an AI draft that a person edits, output that rescales to any rig.

**Mood** stays out of the mic-only baseline unless testing shows it works live from a mic. It can
run three ways: live from the mic, live from a clean line, or ahead of time (when a DJ loads a
track, or for tracks known before a show).

## Why

Summarised from the September discussion:
- The point of the project is a system that adjusts to whatever input is there that night, so a
  venue can try ideas and keep what works. That makes the platform the baseline, not a later
  extra.
- Superposition needs proof: at least one layer visibly changing a running show. MIDI is cheap,
  reliable and easy to demo (turn the reverb knob, the lights change). A camera is a very
  different input; good as the next layer, risky as a promise.
- Layers will not add up neatly. Too much data must not wreck the output. That is the core
  technical problem, so it belongs in the baseline, not after it.
- Mood may only work well on clean audio, or ahead of time. Promising it on a noisy mic before
  testing would be a guess.
- An ordered ladder hides how features depend on each other. Line-in, for example, may make every
  other feature better, so it is not "step 2" of anything.
- We do not "pre-make" whole shows. You can give the system planned looks for some tracks, to
  create highlight moments inside a live show.

## How we'd know we were wrong

- By Dec 10 the mic-only show is not good enough to watch on its own → the base layer needs more
  of our time before any layer.
- The MIDI layer cannot change the show without breaking the beat sync or the safety cap → the
  blending design (module 4) needs rethinking before adding more layers.
- Mood tested live on the mic is as good as on line-in → promote mood into the baseline.

**Still open from this discussion:** build order of the add-ons; how layers blend without
wrecking the output; whether line-in is baseline; the mood test; a set-long energy ramp (maybe not
needed: if the DJ builds energy, the lights follow).
