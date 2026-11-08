# Vision

One page on why LumaSync exists and what we are building. Read this first.

## The problem

Lighting shapes how people experience live music. In one set of experiments, people judged music
performances more accurately from silent video than from the sound alone [Tsay 2013]. At a club
night or a gig, the lights are the main visual layer.

Lighting that truly follows the music is hard to get. It needs fixtures, control software and,
most of all, a skilled operator who knows both the lights and the music. Big productions pay for
that. Small events cannot. Independent venues run on thin margins: in the UK, 53% of grassroots
music venues made no profit in 2025, with an average margin of 2.5% [Music Venue Trust 2026].

So most small events run their lights on a fixed loop, or on a **sound-active** mode (a tiny mic
inside each light that makes it jump through canned patterns when it hears bass). The lights and
the music run side by side, but they are not connected.

## What exists, and the gap

Existing products fall into two groups ([docs/RESEARCH.md](RESEARCH.md) has the detail):

1. **They know the song, but only inside DJ software.** SoundSwitch and rekordbox Lighting plan
   light changes around each track's sections. A track they have not analysed falls back to
   generic loops. They need specific DJ software or Pioneer gear.
2. **They hear the room, but only react.** MaestroDMX, QLC+, WLED and sound-active fixtures work
   with any audio, but only react to the last beat. The polished one costs about US$900.

Nothing cheap does both. And none of them gets better when you give it more inputs.

## The big idea

**Step one is plain:** connect a laptop to real DMX lights (DMX is the standard cable signal that
tells stage lights what to do) and run a good show from audio alone.

**The real idea is how the system is built: hyper-modularity on the input and the output.**
This is what modern software and systems engineering looks like: small, swappable parts with a
strict contract between them, so the whole thing can be customised for each venue and each night.

- **Inputs layer on top of each other.** We call this **superposition**. The mic gives a base
  show. Each extra input is a layer that changes it:
  - a clean line from the DJ mixer (better audio than a mic in a loud room);
  - DJ controls over **MIDI** (the messages DJ gear sends when a knob or button moves): turn the
    reverb knob before a drop, and the lights respond to that gesture;
  - a **song library**: looks we planned in advance for chosen songs, which switch on when the
    system recognises the song (highlight moments, not a whole pre-built show);
  - a **mood estimate** from machine learning;
  - later, DJ player data and a camera reading crowd energy.

  If a layer's gear is missing that night, it counts for zero. **The show still runs from a mic
  alone.**

- **Outputs are swappable.** The same show can drive DMX fixtures through a USB cable today, and
  later an **ESP32** (a cheap microcontroller board) node fed by **sACN** (DMX over a network), an
  LED strip, or a club rig. A new rig means a new patch file (a list of which light sits on which
  channels), not new code.

- **The hard part is that layers do not add up neatly.** Brightness can add. Colour cannot.
  Too many layers at once look like noise. And the whole chain must stay fast enough to look in
  time with the beat. Solving that is real engineering, and it is spread across all five modules.

**Further out:** read live data from **CDJs** (the club-standard DJ players, which share what is
loaded over a network cable) or from DJ software. Then the system knows the next song before it
plays, and can prepare its look in advance: colours, mood, the planned highlight moments, even
stretched to the tempo the DJ is actually playing.

## Baseline and add-ons

The full reasoning is in [decisions/002-baseline-and-add-ons.md](../decisions/002-baseline-and-add-ons.md).

**Baseline (must work by April):**
- A platform that accepts layers, built on superposition.
- The base layer: a mic-only, beat-synced show that runs well alone, using beat, tempo and
  frequency bands.
- One promised layer on top: **DJ controls over MIDI**.
- A simple interface where you build a "show" from modules and tune each one.

**Add-ons** (not a ranked list; a set we choose from as we learn):
- *Better inputs* that make everything else work better: clean line-in from the mixer (the
  easiest), DJ player data (Pioneer Pro DJ Link, Ableton Link).
- *Layers* that change the show: mood from machine learning, crowd energy from a camera.
- *Built-in options* you can use or not: planned looks for chosen songs, an AI-drafted show that
  a person edits, output that rescales to any rig, a small ESP32 box that runs a saved show
  without the laptop.

Mood joins the baseline **only if testing shows it works live from a mic**.

## Who it helps

- **Small venues, promoters and student events** that cannot pay for an operator or pro software.
- **DJs and musicians**, who keep their freedom to improvise. Nothing has to be pre-recorded or
  timecoded to look good.
- **Audiences**, through lighting that follows the music with care, and through an automatic
  flash-rate limit that protects people with photosensitive epilepsy.
- **Researchers** in music and light (for example, therapy studies), who need a cheap, repeatable,
  logged platform where the music or the lighting can be held fixed.
- **Anyone using AI tools**: the system drafts, a person edits and keeps control. Every automatic
  choice can be seen, changed or switched off.

Which one or two of these the report leads with is still open.

## What success looks like

**By Dec 10 (progress report, at least one third of deliverables ready):**
- A simple interface.
- The laptop driving the real DMX lights at Resonnce, our partner venue.
- The mic-only baseline running as a prototype.
- A first test of a mixer or DJ input layered on top.
- Each module tested alone against the contract, with its first measurements.

**By April (final report Apr 7, then the expo):**
- The baseline plus the MIDI layer, running well and measured (beat accuracy, latency).
- Add-ons chosen by what testing showed was worth it.
- An expo demo: a small live rig visitors can play with (music in, knobs turned, lights react),
  plus a video of the full system on the Resonnce rig.

Sources: Tsay, *PNAS* 110(36), 2013, doi:10.1073/pnas.1221454110 · Music Venue Trust Annual
Report 2025, https://www.musicvenuetrust.com/2026/01/music-venue-trust-annual-report-2025/
