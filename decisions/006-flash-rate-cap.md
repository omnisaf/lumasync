# 006 — No more than 3 flashes per second, enforced on the final combined output

- **Status:** accepted (committed in the Sep 27 2026 proposal)
- **Module:** M4 (output stage), M2 (must not add flashing after it)
- **Decided by:** the team · **Date:** 2026-09-27

## Context

The system flashes lights automatically, from many inputs at once. Some people have
**photosensitive epilepsy**: flashing light can trigger seizures. A live audience includes people
we cannot warn individually.

## Options

1. **Limit each input separately.** Simple per layer. Two layers that are each "safe" can still
   add up to an unsafe flash rate.
2. **Limit the final combined output.** One check, after every layer is mixed. No combination of
   inputs or settings can get past it.
3. **Leave it to the operator.** Not acceptable: the point is that there may be no operator.

## Decision

Option 2. The output stage enforces **no more than three flashes in any one-second period** on
the final combined output, following WCAG 2.2 SC 2.3.1, the Epilepsy Foundation expert consensus
(Harding et al. 2005) and ITU-R BT.1702-3. Saturated red flashes get extra care. The cap cannot
be switched off from the interface or by any input. Exactly where it sits in code: see the code
and `decisions/1xx`.

## Why

- It is a safety requirement, not a style choice, and it is a promise in our proposal.
- Superposition means we cannot predict every mix of layers. Only a check on the final output
  covers all of them.

## How we'd know we were wrong

- A test with fake inputs (for example, strobe on + every beat flagged + a fast MIDI pulse) shows
  more than 3 flashes in a one-second window on the output → the cap has a hole; fix before any
  live show.
- A measured flash (on a light, with a camera) differs from what the software counted → the
  definition of "a flash" needs to match the guideline's luminance rule, not just on/off.
