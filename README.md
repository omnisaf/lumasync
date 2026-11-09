# LumaSync

**An intelligent and modular music-reactive lighting system.**
A laptop listens to the music and runs real stage lights by itself, so a small venue gets a good light show without paying a lighting operator.
McMaster ELECENG 4OI6 capstone · Group 2 · supervised by Dr. Chen · Fall 2026 to April 2027.

> **New here? Start at [docs/ONBOARDING.md](docs/ONBOARDING.md).**

## The big idea

Small venues, student events and DIY parties usually run their lights on a fixed loop, or on a
"sound-active" mode that just pulses with the volume. Lighting that truly follows the music needs
expensive software and a skilled person at a lighting desk. We want a cheap system that does a
good job on its own.

The first step is plain: connect a laptop to real **DMX** lights (DMX is the standard cable signal
that tells stage lights what to do) and make them react to the music.

**Why build it this way?** Software is changing. Writing code is no longer the slow, expensive
part of making software. That means it is now easy to build a solution that fits one venue, one
DJ or one night, instead of one product for everyone. LumaSync is our take on that: modularity,
unleashed for engineers. Jobs that used to be big, like adding a new input, a new kind of light, or
a custom look for one song, become small changes.

The part we care most about is how the system is built. It is **modular on both ends**:

- **Any input can be layered on top.** A laptop mic, a clean line from the DJ mixer, DJ controls
  over **MIDI** (the messages DJ gear sends when a knob moves), data from the DJ's players, a
  library of songs we planned looks for, a machine-learning mood estimate, later a camera. We call
  this **superposition**: each extra input is a layer that changes the show. If a layer's gear is
  missing that night, the show still runs, from the mic alone.
- **Any output can be swapped.** The USB-to-DMX cable today; later a small **ESP32** board (a
  cheap microcontroller with Wi-Fi), **sACN** (DMX sent over a network), LED strips. A new rig
  means a new patch file, not new code.

Further out: read live data from **CDJs** (the club-standard DJ players) or DJ software, so the
system knows the next song before it plays and prepares its look in advance.

The full picture is in [docs/VISION.md](docs/VISION.md).

## Quick start

```bash
./run.sh
```

This starts the prototype and opens **http://localhost:8765** (a page on your own laptop) with
a live preview of the lights. See [docs/SETUP.md](docs/SETUP.md) if anything fails.

**DMX cable test** (no audio, no app; only "can the laptop make a light move?"):

```bash
.venv/bin/python tools/dmx_test.py ports    # find the cable
.venv/bin/python tools/dmx_test.py blink    # every channel full, then off, 1 s each
.venv/bin/python tools/dmx_test.py walk     # one channel at a time, to learn what each does
```

How to wire the lights first: [docs/HARDWARE.md](docs/HARDWARE.md).

## The five modules

The course rule: each person owns one technical module. Modules talk to each other **only**
through the data contract in [`lumasync/contract.py`](lumasync/contract.py), so everyone can build
and test in parallel.

| # | Module | Owner | Folder | Gives out |
|---|---|---|---|---|
| 1 | Signal Processing of Audio | Youtso | [`lumasync/m1_audio`](lumasync/m1_audio/MODULE.md) | `AudioFrame` |
| 2 | Real-Time Adaptive Lighting Control and LED Interface | Mo | [`lumasync/m2_lighting`](lumasync/m2_lighting/MODULE.md) | DMX / light output |
| 3 | Rhythm, Tempo and Transient Detection | Remsha | [`lumasync/m3_rhythm`](lumasync/m3_rhythm/MODULE.md) | `RhythmState` |
| 4 | Superposition of Inputs and Latency Optimization | Sathvik | [`lumasync/m4_superposition`](lumasync/m4_superposition/MODULE.md) | `LightIntent` |
| 5 | Machine Learning: Mood and Crowd-Energy Estimation (name under review) | Rohan | [`lumasync/m5_recognition`](lumasync/m5_recognition/MODULE.md) | `MusicContext` |

Owners are confirmed in [team/ROSTER.md](team/ROSTER.md). How the pieces connect:
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Where things live

| Path | What it is |
|---|---|
| `lumasync/contract.py` | The data contract. The only thing modules share. Changes need every owner's approval. |
| `lumasync/m1_audio/` … `m5_recognition/` | One folder per module. Each has a `MODULE.md` brief. |
| `lumasync/fakes.py` | Fake data for every contract type, so you can test your module alone. |
| `tests/` | Automated tests. |
| `library/` | The song library (planned looks for known songs). Audio files stay local, not in git. |
| `tools/` | Small standalone tools, such as the DMX cable test. |
| `docs/` | Vision, architecture, hardware, research, setup, onboarding. |
| `docs/research/` | The full research notes with every source. |
| `decisions/` | Decision records: what we chose, the options, and why. |
| `team/STATUS.md` | The shared status board. What each person is doing, next, and blocked on. |
| `team/ROSTER.md` | Who owns which module. |
| `AGENTS.md` | Instructions for the AI assistant (Codex reads it; Claude Code reads it through `CLAUDE.md`). |

## How we work

1. Work on a branch named `<name>/<topic>`, for example `mo/patch-file`.
2. Stay inside your own module folder. Test against fakes.
3. Real design choices get a decision record in `decisions/`, with your reasoning.
4. Update your section of `team/STATUS.md`, then open a pull request.

An AI assistant (Claude Code or Codex) can do all of this with you. It reads `AGENTS.md`, asks who
you are, and catches you up. See [docs/SETUP.md](docs/SETUP.md).

## Key dates

| What | When | Notes |
|---|---|---|
| Instructor meetings with Dr. Chen | about every 2 weeks | **−3% for each missed meeting** |
| Team meeting | weekly, Wednesdays | from our proposal |
| **Progress report** | **Thu Dec 10** | 20% of the mark. At least one third of deliverables must be ready. |
| Final report | Tue Apr 7 | |
| Expo | April | Live demo, 4–6 min video, poster |

Marks are individual. Each person's module is what they are marked on.

## Partner venue

Resonnce, a music venue on Hess St in Hamilton, hosts our live tests and lends its rig:
8 LED PAR lights and 4 blinders on one DMX chain. Details in [docs/HARDWARE.md](docs/HARDWARE.md).
