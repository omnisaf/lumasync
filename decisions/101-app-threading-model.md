# 101 — One engine thread runs the modules; audio, DMX, matching and the web page each get their own thread

- **Status:** proposed — prototype default, team to confirm
- **Module:** whole team (app runner, `lumasync/app.py`)
- **Decided by:** first prototype build · **Date:** 2026-11-08

## Context

Five things happen at different speeds: audio arrives every 23 ms, DMX frames go out every 33 ms,
song matching takes 7–20 ms but only needs to happen once a second, the web page updates 30 times a
second, and the operator clicks things at random times. If any slow job sits in the path of a beat,
the light comes late. A **thread** is a separate line of work the computer runs at the same time as
others.

## Options considered

1. **One loop does everything in turn.** Simplest. A slow fingerprint match or a slow browser would
   delay the next beat. Hard to keep DMX timing steady.
2. **One thread per module.** Each module runs on its own and passes data through queues. Very
   parallel, but five queues add five waits, ordering bugs appear, and it is harder to measure one
   tick end to end.
3. **One engine thread for the fast path, separate threads only for jobs with their own clock**
   (audio capture, DMX output, fingerprint matching, web server).

## What the prototype does and why

Option 3.

- **Audio thread** (PortAudio's callback, or a clock for muted files): puts each block in a small
  queue (8 blocks). If the engine falls behind, the **oldest** block is dropped, so delay never builds up.
- **Engine thread:** one tick per block, M1 → M3 → M5 → M4 → M2, in order. Each stage is timed.
  Measured on a MacBook Pro: about **1.5–2.5 ms per tick** in total, worst tick about 3 ms, against a
  23 ms budget.
- **M5 worker:** fingerprint matching runs about once a second in its own thread. The tick only copies
  the block into a buffer (about 0.1 ms), so a slow match can never hold up a flash.
- **DMX thread:** sends the latest universe at a steady 30 frames/s, whatever the engine is doing.
- **Main thread:** the web server (asyncio).
- **Only the engine thread ever touches a module.** UI commands that reset modules (for example, a
  source change) are queued and run by the engine thread before its next tick. An early version reset
  modules from the web thread mid-tick; this is the likely cause of one wrong tempo reading (184
  instead of 92 BPM) seen during testing, so the rule is now enforced.
- **Opening an input never blocks the show.** Opening a mic can hang until macOS's microphone-permission
  dialog is answered. The switch runs in its own thread; the engine ticks on silence meanwhile.

## What would change our mind / how to test it

- If `tick max` in the latency panel goes above ~15 ms, or `dropped_blocks` climbs, the single
  engine thread is too slow; move the heaviest stage out or optimise it.
- Python's GIL (a lock that lets only one Python thread run Python code at a time) could make the DMX
  thread late when the engine is busy. Measure DMX frame spacing with a logic analyser or by
  timestamping sends; if jitter is above ~5 ms, move DMX to a separate process or to the ESP32 node.

## Open questions for the team

- Should MIDI input (the promised DJ-controls layer) get its own thread that writes `LiveControls`,
  the same way the web page does? (The prototype's design expects yes.)

## Owner's reasoning (when confirmed)

> (to be written by whoever confirms or replaces this, in their own words)
