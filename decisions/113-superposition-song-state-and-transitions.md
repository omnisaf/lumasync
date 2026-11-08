# 113 — Song presets lock with hysteresis, change on the beat, crossfade (snap on a drop), and hold through short dropouts

- **Status:** proposed — prototype default, team to confirm
- **Module:** M4 Superposition of Inputs and Latency Optimization
- **Decided by:** first prototype build · **Date:** 2026-11-08
- **Code:** `lumasync/m4_superposition/layers.py` (`SongSelector`, `PresetLayer`)

## Context

M5 reports a fresh match about once a second, and its confidence wobbles: crowd noise, a quiet
breakdown, or a DJ blending two tracks. If M4 followed every report, the palette would flicker between
songs. If it waited too long, the planned look would arrive late. A false match (wrong song) puts the
wrong colours on the room.

**Hysteresis** means using a higher bar to switch something on than to keep it on, so a signal
hovering near one threshold does not make the state flicker.

## Options considered

For deciding the active song:
1. **Follow M5 directly** (use `song_id` whenever confidence > x). Fast; flickers; one false match is
   instantly visible.
2. **Hysteresis + time hold (chosen):** separate thresholds for lock-on and keep, plus minimum times.
3. **Majority vote over the last N matches.** Robust, but slow to react to a real song change and needs
   N tuned to the match rate.

For changing the look when the song changes:
1. **Snap** (cut instantly). Clean on a drop; jarring mid-phrase.
2. **Crossfade over a fixed time.** Smooth; may start at a musically random moment.
3. **Crossfade that starts on the next beat, snap on a drop (chosen).**

## What the prototype does and why

`SongSelector` (all times tunable in the constructor):

| Event | Rule |
|---|---|
| Lock on | same song at confidence ≥ 0.5, continuously for 1.5 s |
| Keep | confidence ≥ 0.25 for the locked song counts as "still there" |
| Holding | evidence gone: keep the preset for up to 5 s (state "holding", shown in the UI) |
| Lose | 5 s without evidence: unlock, fade the preset out |
| Switch | a different song at ≥ 0.5 for 2.5 s (longer than lock-on: in a DJ blend both songs are present) |
| Manual | `manual_song_id` wins immediately; recognition keeps running underneath |

`PresetLayer` (what the change looks like):

| Change | How |
|---|---|
| none → A | palette set to A while the preset is invisible, then fade in over 1.5 s |
| A → none | fade out over 2.5 s (slower: losing a song is less certain than finding it) |
| A → B | palette and energy crossfade A → B over 2 s in OKLab; weight stays up (no detour through the house palette) |
| timing | waits for the next beat (at most 1 s; no wait if there is no tempo) |
| on a drop | snap (0 s): a drop is a natural hard cut |
| manual pick | starts at once, 0.6 s fade |

**False match:** a wrong song must hold ≥ 0.5 for 1.5 s to show at all (tested:
`test_brief_false_match_does_not_lock`). If it does lock, the operator overrides with the manual
picker or turns `preset_blend` down. **Lost confidence:** short dropouts hold (tested: still locked
3 s after evidence stops; released after 5 s). **Song change:** tested to crossfade without the weight
dropping below 0.5.

Measured in the app: Neon Drive recognised at 3.4 s, preset locked about 1.5 s later, fully faded in
about 1.5 s after that.

## What would change our mind / how to test it

- Record a real DJ set (with transitions) through the mic and replay it. Count palette changes per
  minute versus real song changes; count wrong-song seconds. If the palette changes more than once per
  real transition, raise the switch hold; if the right preset arrives more than ~8 s into a song,
  lower the lock hold.

## Open questions for the module owner

- In a long DJ blend, should the palette follow the incoming track's confidence continuously (a
  "proportional" blend of A and B) instead of switching at one moment?
- Should "holding" fade the preset weight down gradually instead of keeping it full for 5 s?
- Should transitions wait for the next **bar** (needs downbeat from M3) rather than the next beat?

## Owner's reasoning (when confirmed)

> (to be written by the M4 owner in their own words)
