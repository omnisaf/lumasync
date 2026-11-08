# Research digest

What we found in September 2026, in plain terms. Four questions were researched. Each section
gives the short answer, why it matters to us, and where the full notes are. The full notes in
[`docs/research/`](research/) have every source, price and caveat.

---

## 1. What already exists, and where is the gap?

Full notes: [research/existing-solutions.md](research/existing-solutions.md)

**First principles.** There are two ways to make lights follow music:
- **Know the song in advance.** Software analyses each track ahead of time: where the beats are
  (the **beatgrid**) and where the sections change (intro, build, drop). This is called **phrase
  analysis**. Light changes are planned around it.
- **React live.** Listen to the room and respond to what was just heard.

**What is on the market:**

| Product | Price seen | How it works | Weak spot |
|---|---|---|---|
| SoundSwitch | US$199 lifetime + US$39.99 DMX box | Knows the song, via supported DJ apps | Unanalysed track → generic loops |
| rekordbox Lighting | US$180/yr plan + a DMX box | Knows the song, via phrase analysis | No analysis → "cannot perform lighting in sync" |
| MaestroDMX | US$899 | Reacts to line-in audio | Only reacts; one closed box |
| QLC+ | Free + a DMX box | Frequency bands trigger cues | Every cue built by hand; no BPM detection |
| LedFx / WLED | Free + LED hardware | Reacts to audio | LED strips only; pure reaction |
| ChamSys MagicQ | Free software, US$125 box | Pro console with a beat tracker | A trained operator builds the show |
| Sound-active lights | from US$24 per light | Tiny mic, canned patterns | No idea of tempo or song |

**The gap.** Song-aware tools lock you into specific DJ software. Any-audio tools only react, and
the polished one costs about US$900. **No low-cost system does both**: plan looks for known songs,
lock them to the live tempo from any source, and fall back to live reaction for unknown tracks.
And none gets better when you add inputs, which is what superposition is for.

Note: in September 2026, rekordbox and Pioneer's PRO DJ LINK Bridge added SoundSwitch lighting
support. That is a commercial product close to ours; name it in the existing-solutions section.

---

## 2. What is the cheapest way to drive DMX?

Full notes: [research/dmx-path.md](research/dmx-path.md) · plain guide: [HARDWARE.md](HARDWARE.md)

**First principles.** DMX is a one-way broadcast of 512 channel values, sent again and again,
about 30–44 times a second. The hard part is **timing**: each frame starts with a break of exact
length, and the gaps between frames should be steady. Whoever makes that timing decides how
reliable the output is.

| Option | Price | Who makes the timing | Verdict |
|---|---|---|---|
| FTDI USB-DMX cable (what we have) | about CAD 22 | the laptop | Learn the rig; may flicker |
| ESP32 + isolated M5Stack Unit DMX | about USD 15 | the ESP32 | **Build this** |
| DMXking ultraDMX MAX | USD 110 | its own chip | Known-good fallback |
| Enttec DMX USB Pro | about CAD 229 | its own chip | Good, about 15× the DIY cost |

**The plan:** the cable first, to learn each light's mode, address and channel map. Then the
ESP32 node fed by **sACN** (DMX over a network), with a second ESP32 running WLED for LED strips.
Fixture layouts come from **Open Fixture Library** files, so a new rig is a new patch file.

**Venue finding:** the "LPC1818" lights are almost certainly Betopper 18 × 18 W PARs. One version's
11-channel mode would make the 10-apart addresses overlap. We need a photo of the display.

---

## 3. What live data can we read from DJ gear?

Full notes: [research/dj-gear-data.md](research/dj-gear-data.md)

**First principles.** A mic hears the music plus the crowd and the room's echo. Better inputs
either give us **cleaner audio**, or give us **facts** we would otherwise have to guess (the exact
tempo, which track is loaded, what the DJ just touched).

Difficulty is our own judgement: 1 = an afternoon with gear we have, 5 = gear or permission we
cannot get.

| Source | What it gives | Needs | Difficulty |
|---|---|---|---|
| Mixer line-out → USB audio interface | Clean audio of the mix | Any mixer + about US$16 interface | 1 |
| **Ableton Link** (an open tempo-sharing protocol) | Exact tempo, beat position, start/stop | DJ software that supports Link, same network. Free. | 2 |
| Controller MIDI (e.g. DDJ-FLX4) | Every fader, EQ, filter, FX button | The controller; easiest on a Mac | 2 |
| Club mixer MIDI (e.g. DJM-900NXS2) | Control moves + tempo clock | The mixer + USB | 2 |
| DJ library files (rekordbox, Serato, Engine) | Offline beatgrid, BPM, key, cues; rekordbox also has **phrases** | The DJ's USB stick or library | 2–3 |
| **Pioneer Pro DJ Link** | Every beat, BPM, pitch, which deck is on air, **which track is loaded**, its grid and phrases | Real CDJs with a LINK port, a DJM mixer, a wired switch | 4 |
| Denon StageLinQ | Similar, for Denon gear | Denon Prime / SC6000 gear | 4 |

**Order we chose:** line-in first (cheapest, works with any setup). Then Ableton Link and
controller MIDI. MIDI is the layer promised in the baseline.

**The "prepare the next song" add-on.** Pioneer **CDJs** (club DJ players) broadcast what they are
doing over a network cable, called **Pro DJ Link**. When a DJ loads the next track, the players
announce it, with its beatgrid and phrase analysis, **before it is played**. If we listen, the
system can prepare that song's look in advance: find its planned preset, run the mood model on
it, and line up highlight moments with its phrases (chorus = big look, breakdown = calm look).
The live tempo from Pro DJ Link or Ableton Link then stretches the plan to the speed actually
played (a show planned at 124 BPM can follow the DJ at 135 BPM).

Caveats: the libraries that read Pro DJ Link are reverse-engineered and unofficial. Listening to
broadcast packets on our own network is passive. Canadian copyright law has an interoperability
exception (s. 41.12); this is our reading, not legal advice. At a live gig, **listen only**: one
library warns it can freeze players. It needs wired networking, not Wi-Fi.

---

## 4. Which papers and standards should we cite?

Full notes: [research/citation-bank.md](research/citation-bank.md). 36 sources, each checked
(DOIs against Crossref, standards on the publishers' sites).

| Area | Start with | Module |
|---|---|---|
| Onset, beat, tempo | Bello et al. 2005 (onset tutorial) · Ellis 2007 (beat tracking) · Böck et al. 2016 (beat + downbeat) | M3 |
| Audio libraries | librosa (McFee et al. 2015) · madmom (Böck et al. 2016) | M1, M3, M5 |
| Song structure | Foote 2000 · Nieto et al. 2020 review | M3, M4 |
| Mood | Russell 1980 (valence–arousal) · DEAM dataset (Aljanaki et al. 2017) · PMEmo (Zhang et al. 2018) | M5 |
| Fingerprinting | Wang 2003 (Shazam) · Haitsma & Kalker 2002 · Chromaprint | M5 |
| Tempo-invariant alignment | Sakoe & Chiba 1978 (DTW) · Dixon 2005 (on-line time warping) · Müller 2015 textbook | M4, M5 |
| Automatic light shows | Hsiao et al. 2017 · Zhao et al. 2026 (Skip-BART) · Kohl et al. 2025 (music–light metrics) | all |
| Human–AI co-creation | Horvitz 1999 · Amershi et al. 2019 · Louie et al. 2020 | M4 |
| DMX and protocols | ANSI E1.11-2024 (DMX512-A) · ANSI E1.31-2025 (sACN) · Art-Net 4 | M2 |
| Flash safety | WCAG 2.2 SC 2.3.1 · ITU-R BT.1702-3 · Harding et al. 2005 | M4, M2 |

**Use the current editions:** E1.11-**2024**, E1.31-**2025**, BT.1702-**3**. Two preprints are
flagged in the notes as not yet peer reviewed.

Also used in our proposal and worth reusing: Stark et al. 2009 (real-time beat-synchronous
analysis), McPherson et al. 2016 (action-sound latency), ITU-R BT.1359-1 (sound–vision timing),
ETC Hog 4 manual on HTP/LTP merging, Tzanetakis & Cook 2002 (timbral features), Yang et al. 2008
(regression for music emotion).

**Not covered yet:** crowd-motion estimation from a camera (needed if the camera add-on goes
ahead), and a beat-annotated dataset for Module 3.
