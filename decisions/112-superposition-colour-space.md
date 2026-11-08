# 112 — Palettes are blended in OKLab; fixtures get colour (max channel = 1) and brightness separately

- **Status:** proposed — prototype default, team to confirm
- **Module:** M4 Superposition of Inputs and Latency Optimization
- **Decided by:** first prototype build · **Date:** 2026-11-08
- **Code:** `lumasync/m4_superposition/colour.py`

## Context

Blending happens all the time: house palette ↔ song palette, song A ↔ song B, look ↔ look,
colour ↔ white for accents. The blend must not dip in brightness or pass through ugly colours halfway.

## Options considered

1. **RGB (straight mix of red, green, blue values).** Simplest. Halfway between red and green is dark
   olive: a visible brightness dip and a muddy colour mid-fade.
2. **HSV / HSL (hue angle, saturation, value).** Keeps saturation, but the hue must go one way round the
   colour wheel (which way?), and "value" is not perceived brightness: yellow and blue at the same value
   look very different.
3. **OKLab** (Ottosson 2020): a perceptual space where straight lines look like even changes. Lightness
   stays steady through a blend. Cost: two small matrix multiplies and a cube root.
4. **OKLCh** (OKLab in polar form): keeps chroma (colourfulness) through a blend, like HSV, but has the
   same "which way round" hue problem.

## What the prototype does and why

Option 3. Palettes are converted from hex to OKLab once; every blend is a straight line in OKLab; the
result goes back to sRGB. The house palette is defined in OKLCh (fixed lightness and chroma, drifting
hue) and converted to OKLab. Test: the OKLab midpoint of red and green is not darker than the darker
end, while the RGB midpoint is more than 0.1 darker (`test_oklab_midpoint_does_not_dip_in_lightness`).

**Colour and brightness are separate.** `FixtureIntent.rgb` is the colour with its brightest channel
scaled to 1; `dimmer` carries brightness. Lights have both controls, and the safety cap (114) then works
on one number (dimmer × max channel).

Known trade-off: OKLab blends between complementary colours (e.g. red ↔ cyan) pass near white/grey in
the middle. OKLCh would keep them colourful but would swing through other hues.

## What would change our mind / how to test it

- Film a 2-second palette fade on real fixtures in RGB and OKLab. LEDs are not screens; if the
  difference is invisible on the pars, RGB is simpler.
- If complementary-colour fades look washed out on stage, use OKLCh for those (shortest hue path).

## Open questions for the module owner

- The fixtures have amber, lime and UV LEDs too (see HARDWARE.md). Should M4 stay in RGB and let M2 mix
  the extra LEDs, or should intent carry a colour temperature?

## Owner's reasoning (when confirmed)

> (to be written by the M4 owner in their own words)
