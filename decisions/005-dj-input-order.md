# 005 — DJ inputs: line-in first, then Ableton Link and MIDI; Pro DJ Link later

- **Status:** accepted (September 2026, carried over from our earlier decision record)
- **Module:** M1 (line-in), M4 (layers), M3 and M5 (better tempo and song data)
- **Decided by:** the team, from the DJ-gear research · **Date:** 2026-09-24

## Context

Beyond the laptop mic, DJ gear can give us cleaner audio or real data: exact tempo, which track is
loaded, what the DJ touched. Each source costs a different amount of gear and effort. Full
research: [docs/research/dj-gear-data.md](../docs/research/dj-gear-data.md).

## Options

1. **Mixer line-out into a USB audio interface** (about US$16). Clean audio, works with any setup.
   No meaning: we still analyse it ourselves.
2. **Ableton Link** (free, official). Exact tempo and beat phase from Link-enabled DJ software.
   Nothing about decks or effects.
3. **Controller or mixer MIDI.** Every fader, filter and FX button. Positions only, per model.
4. **Pioneer Pro DJ Link.** The richest data, including which track is loaded before it plays.
   Needs CDJs with a LINK port, a DJM mixer and a wired switch; unofficial libraries.

## Decision

Order of work: **line-in first**, then **Ableton Link and controller MIDI** (MIDI is the layer
promised in the baseline, see [002](002-baseline-and-add-ons.md)), then **Pro DJ Link** as an
add-on if we can borrow the gear. At a live gig we only ever listen; we never send commands to
the DJ's players.

## Why

Summarised from the research:
- Line-in fixes the mic's biggest problem (crowd noise and room echo) for about US$16 and has no
  protocol to break.
- Ableton Link gives exactly the signal needed to stretch a planned look to the live tempo, for
  free.
- MIDI is the cheapest way to show superposition: a DJ gesture visibly changing the show.
- Pro DJ Link is the best data by far, and the path to "prepare the next song in advance", but
  the gear is the blocker.

## How we'd know we were wrong

- Beat tracking on line-in is no better than on the mic → line-in is not worth its setup time.
- The venue's DJ setup has no Link-enabled software → skip Link, go to MIDI clock from the mixer.
- We can borrow CDJs and a DJM easily → move Pro DJ Link earlier.
