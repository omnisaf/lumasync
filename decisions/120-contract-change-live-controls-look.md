# 120 — Contract change proposal: add optional `LiveControls.look` (default "auto")

- **Status:** proposed — prototype default; needs the contract-change process (every module owner approves)
- **Module:** whole team (contract); used by M4 and the UI
- **Decided by:** first prototype build · **Date:** 2026-11-08

## Context

The prototype has several reactive looks (116). The operator needs to choose one live. Live choices
reach M4 only through `LiveControls`; the contract had no field for it.

## Options considered

1. **A side channel** (the app calls a method on M4 directly). Works, but breaks the rule that the
   contract is the only coupling, and MIDI could not set it the same way.
2. **Add an optional field with a default (chosen).** The cheap kind of contract change
   (AGENTS.md §5): nothing that ignores it breaks.

## What the prototype does and why

Added to `lumasync/contract.py`:

    look: str = "auto"           # base-layer look: "auto", "pulse", "bands", "chase"

Nothing was renamed or removed. Also changed: the module docstring became a raw string (`r"""`) so
Python 3.14 stops warning about the `\_` in the ASCII diagram; no behaviour change.

`CONTRACT_VERSION` was **not** bumped, so the team can bump it (0.1.0 → 0.2.0, middle number for a
field change) when the change is approved through a pull request.

## What would change our mind / how to test it

- If the team prefers looks to be named per song too, add `SongPreset.look: Optional[str] = None` in
  the same pull request.

## Open questions for the team

- Approve and bump to 0.2.0?
- Possible further optional fields raised by the prototype, not added: `MusicContext.song_position_s`
  (timed cues, 109), `RhythmState.downbeat` (bar-aligned changes, 106/113).

## Owner's reasoning (when confirmed)

> (to be written by the team when the contract pull request is approved)
