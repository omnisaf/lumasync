# 115 — Latency: measure every stage every tick, keep processing under ~3 ms, and fire beat pulses 40 ms early

- **Status:** proposed — prototype default, team to confirm
- **Module:** M4 Superposition of Inputs and Latency Optimization
- **Decided by:** first prototype build · **Date:** 2026-11-08
- **Code:** `Engine.latency()` in `lumasync/app.py`; `lead_s` in `SuperpositionEngine`

## Context

People notice when the light comes more than about 45 ms after the sound (ITU-R BT.1359;
docs/ARCHITECTURE.md). Total delay = capture + analysis + mixing + output + the fixture itself.

## Options considered

1. **Make every stage faster.** Analysis can be made tiny, but capture (one block) and DMX output
   (frame period + wire time) are fixed costs.
2. **Predict the beat and fire early.** Beats are regular, so a pulse can be sent before the beat by
   the known delay. Works only for the beat-locked part of the show.
3. **Both, plus measure (chosen).**

## What the prototype does and why

**Measured** in the app (MacBook Pro, file source, muted, no cable; averages per tick):

| Stage | Measured / computed |
|---|---|
| Capture: one 1024-sample block | 23.2 ms (mic only; plus the device buffer) |
| Queue wait (block ready → engine starts) | 0.07 ms (worst 0.5) |
| M1 audio | 0.29 ms (worst 0.9) |
| M3 rhythm | 0.15 ms (worst 1.0) |
| M5 per tick (matching runs elsewhere: 7–18 ms, once a second) | 0.13 ms |
| M4 superposition | 0.53 ms (worst 1.0) |
| M2 mapping + preview | 0.51 ms (worst 1.1) |
| DMX: wait for next 30 fps frame (average half a period) | 16.7 ms |
| DMX: wire time, 513 slots × 44 µs + break | 22.7 ms |
| Fixture's own response | unknown — measure |

Processing (M1–M2) totals about **1.6 ms**; worst single tick about 3 ms. The fixed costs dominate.
Estimated sound → light: **mic ≈ 23 + device + 1.6 + 16.7 + 22.7 ≈ 65–75 ms**; **file playback
≈ 41 ms minus the speaker buffer (~41 ms on the MacBook) ≈ 0 ms**, because the pipeline sees each block
as it is handed to the speakers.

**Beat lead:** M4 computes beat pulses from `beat_phase` shifted by `lead_s` = 40 ms (`--lead-ms`), so
the pulse peak leaves about 40 ms before M3's beat time. For steady beats this cancels most of the mic
path's delay. Onset-driven reactions (no tempo lock) cannot be predicted and keep the full delay.

The UI shows every stage live, the total, and the lead, so the team can see the budget at the demo.

## What would change our mind / how to test it

- **Measure the real end-to-end delay:** put a mic and a photodiode (or a phone at 240 fps filming a
  speaker cone and a light) side by side, play clicks, and measure click → light. Set `--lead-ms` from
  that number. If it differs from the estimate by > 10 ms, find the missing stage (likely the fixture).
- Send only the channels in use (112 for the venue rig ≈ 5 ms on the wire instead of 23 ms), or raise
  the DMX rate, if the measured delay is too high. Some fixtures dislike short frames: test first.
- Smaller blocks (512) halve capture delay; check M3 accuracy does not drop.

## Open questions for the module owner

- Should the lead be measured automatically (a calibration mode that flashes and listens)?
- Should the lead differ per fixture type (LED pars vs blinders warming up)?
- Audience distance hides some delay (sound travels ~29 ms over 10 m). Is the target "45 ms at the DJ
  booth" or "at the middle of the room"?

## Owner's reasoning (when confirmed)

> (to be written by the M4 owner in their own words)
