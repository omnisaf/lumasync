# 121 — Every module is tested alone against fakes; one architecture test enforces "no module imports another"

- **Status:** proposed — prototype default, team to confirm
- **Module:** whole team (`lumasync/fakes.py`, `tests/`)
- **Decided by:** first prototype build · **Date:** 2026-11-08

## Context

Five people build in parallel. Each must be able to test their module without anyone else's code, and
the team needs proof that the rules (contract-only coupling, flash cap) hold.

## Options considered

1. **Test only end to end.** Realistic; a failure does not say which module broke, and nobody can test
   until everything works.
2. **Fakes per contract type + tests per module + a few end-to-end checks (chosen).**

## What the prototype does and why

- `lumasync/fakes.py` imports only the contract: click tracks at known tempi; synthetic songs (the three
  demo tracks, plus random "unknown" songs); a small reference analyser so M3/M5 can be tested without
  M1; fake AudioFrame, RhythmState, MusicContext and LightIntent streams.
- `tests/`: 65 tests, ~6 s. Examples: M3 recovers 90/128/140 BPM clicks within ±2 and puts beats on the
  clicks; M5 recognises 8 s noisy excerpts (≥ 0.8) and rejects unknown tracks (< 0.5); M4 never exceeds
  3 flashes/s under hostile input; M2 maps intents to exact DMX bytes and survives a missing cable; the
  real engine recognises a demo track end to end; an AST scan fails if any module imports another.
- Demo audio is regenerated deterministically from `library.py` settings if missing (audio is not in git).

Run: `.venv/bin/python -m pytest -q`

## What would change our mind / how to test it

- Synthetic audio is easy. When recorded venue audio exists, add it as fixtures (e.g. `recordings/`,
  gitignored, with a small labelled subset in git) and make it the main test data.

## Open questions for the team

- Who records the first labelled venue session (beats, drops, songs), so every module shares it?

## Owner's reasoning (when confirmed)

> (to be written by the team when confirmed)
