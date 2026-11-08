# 111 — Superposition: a song preset steers the reactive show's parameters; it never replaces the show

- **Status:** proposed — prototype default, team to confirm
- **Module:** M4 Superposition of Inputs and Latency Optimization
- **Decided by:** first prototype build · **Date:** 2026-11-08
- **Code:** `lumasync/m4_superposition/engine.py`, `layers.py`

## Context

Three layers can be active at once:

1. **Base reactive layer** from audio (M1) and rhythm (M3). Always on. A mic alone must give a full show.
2. **Song-preset layer** when a library song is recognised (M5) or picked by hand: 2–3 colours,
   energy, strobe permission, blend.
3. **Live controls layer** from the UI (later MIDI): master, reactivity, preset blend, strobe enable,
   blackout, look, manual song.

"Superposition" is how these combine into one `LightIntent`. The rules must be predictable for an
operator, never break when a layer is missing, and never get around the safety cap (006, 114).

## Options considered

1. **Output-space crossfade.** Each layer renders its own complete light show; mix the two shows'
   colours and brightness by a weight `w` (like a DJ crossfader between two videos).
   - + Each layer is independent and easy to write.
   - − Two beat-synced shows mixed together give half-bright double pulses and muddy colours. At
     `w = 0.5` neither show is visible; the room looks broken.
   - − A preset needs to know how to "react", duplicating the base layer.
2. **Hard override with priority.** Highest-priority active layer wins outright (manual > recognised >
   reactive).
   - + Simple and predictable.
   - − Recognition errors cause visible jumps; there is no "a bit of the planned look".
   - − The preset look is static unless it duplicates the reactive logic.
3. **Parameter-space modulation (chosen).** There is only ever **one** show, the reactive one. A preset
   changes its **parameters**: which colours it uses, how hard it reacts, whether strobe accents are
   allowed. The preset weight `w` blends those parameters, not finished outputs.
   - + The beat pulse is always crisp, at any `w`. Missing layers simply leave parameters at defaults.
   - + Song changes become parameter fades (palette A → B), which look intentional.
   - − A preset cannot draw a completely custom look (e.g. a hand-made chase only for one song).
     That needs a "look" field in the preset (open question below).

## What the prototype does and why

Option 3. Per tick, in this fixed order (each step only uses earlier results):

1. **Song layer** decides the active preset with hysteresis (113) and gives a fade envelope `env`
   (0 = no preset, 1 = fully in).
2. **Preset weight** `w = env × blend`, where `blend` is the song's own `blend` if set, otherwise the
   live `preset_blend` slider (as the contract defines). The slider acts instantly; fades only shape `env`.
3. **Palette** = OKLab blend of the house palette and the preset palette by `w` (112).
4. **Energy** = `lerp(0.5, preset.energy, w)` (0.5 = neutral when no song).
   **Depth** (how far brightness swings with the music) = `reactivity × (0.4 + 1.2 × energy)`,
   clipped to 0–1. So energy 0.5 leaves reactivity unchanged, 1.0 makes it 1.6× stronger, 0 makes it
   0.4×. The preset **modulates** the operator's reactivity; it never overrides it, and reactivity 0
   always means a calm static wash.
5. **Look** renders per-fixture colour and "drive" 0–1 from the palette, beat phase, bands and onsets
   (116). Brightness = `lerp(idle 0.55, floor 0.06 + 0.94 × drive, depth)`.
6. **Strobe accents** (white hits on drops and big onsets) only if the live strobe toggle is on
   **and** (no song is active, or the active song allows strobe). Live toggle = permission;
   song = request.
7. **Live controls:** master multiplies brightness; blackout snaps to 0 at once and fades back over 0.5 s
   when released (a sudden full-on after blackout would itself be a flash).
8. **Safety cap** (114): last, on the final brightness of every fixture and of the rig average.

**Priority / override order, highest first:** safety cap > blackout > master > manual song pick >
recognised song (with hysteresis) > house palette. The safety cap is not a layer; it is a limit on the
result, and no setting can turn it off.

**Missing inputs count as zero:** `process()` accepts `None` for rhythm or music. No tempo → pulses
follow onsets instead of the beat clock. No recognition → house palette. No audio → idle glow.

## What would change our mind / how to test it

- Show both behaviours to 5–10 people on the same recording: option 3 versus an output-space crossfade
  at `w = 0.5`. If people do not prefer option 3, revisit.
- If song owners keep asking for "this exact look in this song", add a per-song look (below) before
  considering a second rendered layer.
- `tests/test_m4_superposition.py::test_preset_modulates_rather_than_replaces` checks that a fully
  applied preset still pulses with the beat (brightness range > 0.4).

## Open questions for the module owner

- Should the live `preset_blend` slider **scale** a song's own blend (song 0.9 × slider 0.5 = 0.45)
  instead of being ignored when the song sets one? Scaling keeps the operator in charge; the contract
  currently says the song's value replaces the slider.
- Should a preset be able to pick a look (`SongPreset.look`)? Cheap to add as an optional field.
- MIDI controls (the promised layer): which controls map to parameters (palette shift, energy) and
  which to overrides (blackout, flash-on-press under the cap)?
- Where should "crowd energy" (camera add-on) enter: as a modulation of depth, like song energy?

## Owner's reasoning (when confirmed)

> (to be written by the M4 owner in their own words)
