# 114 — The flash cap: count rises in brightness per fixture and for the whole rig; refuse a 4th inside any second

- **Status:** proposed — prototype default, team to confirm (implements team decision 006)
- **Module:** M4 Superposition of Inputs and Latency Optimization (M2 must not add flashing after it)
- **Decided by:** first prototype build · **Date:** 2026-11-08
- **Code:** `lumasync/m4_superposition/safety.py`; applied as the last step of `SuperpositionEngine.process()`

## Context

Decision 006 commits the team to **no more than 3 flashes in any 1-second period on the final combined
output** (WCAG 2.2 SC 2.3.1; ITU-R BT.1702-3; Harding et al. 2005). Saturated red needs extra care. This
record says exactly how the code measures a flash and enforces the limit.

## Options considered

How to measure brightness:
1. **Relative luminance** (what WCAG uses for screens). Undercounts saturated colours: full blue is only
   7 % luminance, so a blue strobe would barely count, and saturated red is the riskier case.
2. **Brightest colour channel × dimmer (chosen).** Counts a full red or blue flash as fully as white.
   Stricter than the guideline, never looser.

How to enforce:
1. **Rate-limit the beat** (no pulses faster than 3/s). Misses accents, blackout toggling, look changes.
2. **Low-pass filter the output.** Removes all crispness, and still is not a guarantee.
3. **Count flashes on the final output and refuse the 4th (chosen).**

Where:
1. Per layer (rejected by 006: safe layers can add up).
2. **On the final output, per fixture and for the rig average (chosen).** Per fixture because each par is
   a large bright source; rig average because many lights flashing in turn could read as one flashing room.

## What the prototype does and why

- A **flash** starts when brightness rises by ≥ 0.10 (10 % of full) above the last dark point
  ("trough") while that trough is below 0.8 (WCAG's "darker image" condition). WCAG counts a flash as a
  pair of opposite changes; every such pair begins with a rise, so counting rises is at least as strict.
- If 3 rises already happened in the last 1 s, brightness is **held just under trough + 0.10** until the
  oldest rise leaves the window. **Getting darker is always allowed**, so blackout is never delayed.
- Two steps per tick: `ceiling(t)` gives the brightest allowed value; `commit(t, y)` records what was
  actually shown after every clamp (per-fixture and rig limits interact; each limiter must track the real
  output, or it can miss a rise).
- It runs **after** everything: looks, accents, master, blackout. No input or setting reaches the output
  without passing it. It cannot be switched off from the UI.
- **Hardware strobe is never used.** `FixtureIntent.strobe` is always 0, and M2 holds every fixture's
  strobe and auto-program channels at "off". The fixtures' strobe rates per DMX value are unmeasured; a
  hardware strobe would flash inside the light, where this cap cannot see it.
- At very fast tempi (> 165 BPM) the pulse look pulses every other beat, so the cap rarely has to act.
- The UI shows "safety cap: HOLDING" whenever it changed the output in the last second.

Tests (`tests/test_m4_superposition.py`): hostile random input for 40 s × 4 seeds (random beats, drops,
onsets, BPM up to 300, strobe on, blackout and every control mashed), 200 BPM with every tick a drop,
and blackout toggled ~10 times per second. Each is checked by two independent flash counters on every
fixture and the rig average. Maximum seen: 3 in any 1 s window.

## What would change our mind / how to test it

- Film the real fixtures at 120+ fps during the hostile test and count flashes from the video (006 asks
  for this). If the video shows more than the software counts (e.g. LED drivers overshoot), lower the
  threshold or measure luminance with a photodiode.
- If the cap engages often in normal music (UI shows HOLDING), the looks are too flashy: fix the look,
  not the cap.

## Open questions for the module owner

- Should the cap also apply to large slow changes of colour at constant brightness (WCAG's red-flash
  rule is about saturated red transitions, which can happen without a brightness change)?
- Should the 10 % threshold be relative to the fixture's real output (a 200 W par at 10 % is still
  bright)? A photodiode measurement would settle this.

## Owner's reasoning (when confirmed)

> (to be written by the M4 owner in their own words)
