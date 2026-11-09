# Status board

The team's main centre. Read the top section before every meeting.

**Rules.** Each person (or their AI) edits **only their own section**. The AI also keeps "Current
focus & conflicts" up to date: short lines, newest first, delete them when resolved. If git shows
a merge conflict in this file, keep both sides.

---

## Current focus & conflicts

- **2026-11-08** · Repo set up; first shown to the team on Nov 9. The prototype runs end to end as a first draft built
  for the team. Each module's real work starts now.
- **Open:** owners for modules 3 and 5, and module 5's name. Settle at the first team session.
- **Open:** the DMX cable has not been tested on a light yet. A Resonnce test date is needed.
- **Watch:** the promised MIDI layer will need a contract change (`LiveControls` says "MIDI later").
  Affects modules 4 and 2.

---

## Youtso · Module 1 · Signal Processing of Audio

- **My one-liner:** takes in … , gives out `AudioFrame`, my first test is …
- **Working on:** onboarding. The prototype has a first-draft audio front end (see code).
- **Next:** read `lumasync/m1_audio/MODULE.md`; record a few test clips from mic and line-in.
- **Blockers:** none yet.
- **Decisions this week:** none.
- **Last updated:** 2026-11-08

---

## Mo · Module 2 · Real-Time Adaptive Lighting Control and LED Interface

- **My one-liner:** takes in `LightIntent`, gives out … , my first test is …
- **Working on:** onboarding. The prototype has a first-draft patch and DMX output (see code).
- **Next:** read `lumasync/m2_lighting/MODULE.md`; plan the first rig test with `tools/dmx_test.py`.
- **Blockers:** cable untested on a light; LPC1818 mode and blinder model unconfirmed.
- **Decisions this week:** none.
- **Last updated:** 2026-11-08

---

## Rohan · Module 5

- **My one-liner:** takes in … , gives out … , my first test is …
- **Working on:** onboarding.
- **Next:** confirm module at the first team session; read that module's `MODULE.md`.
- **Blockers:** module not confirmed yet.
- **Decisions this week:** none.
- **Last updated:** 2026-11-08

---

## Remsha · Module 3

- **My one-liner:** takes in … , gives out … , my first test is …
- **Working on:** onboarding.
- **Next:** confirm module at the first team session; read that module's `MODULE.md`.
- **Blockers:** module not confirmed yet.
- **Decisions this week:** none.
- **Last updated:** 2026-11-08

---

## Sathvik · Module 4 · Superposition of Inputs and Latency Optimization

- **My one-liner:** takes in `RhythmState`, `MusicContext`, `LiveControls`, `SongPreset`, gives out
  `LightIntent`, my first test is …
- **Working on:** onboarding. The prototype has a first-draft mixing engine (see code and
  `decisions/1xx`).
- **Next:** read `lumasync/m4_superposition/MODULE.md`; plan the MIDI layer with module 2.
- **Blockers:** none yet.
- **Decisions this week:** none.
- **Last updated:** 2026-11-08
