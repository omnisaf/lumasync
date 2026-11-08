# Live data from DJ gear

What live data can we read from DJ equipment, and how hard is each source to get? Researched 2026-09-24.

**How this was checked (2026-09-24).** Every claim below links to a source that was opened on this date: project READMEs, protocol write-ups, manufacturer manuals and support pages. Repo activity (last push, licence) was read from the GitHub API on the same day. Anything we could not open ourselves is marked **(unverified)**. Difficulty scores are **our judgement**, not a source's.

**Difficulty scale.** 1 = an afternoon, works with gear we already have. 3 = a week or two, needs borrowed gear or careful protocol work. 5 = needs gear or permission we realistically cannot get.

---

## Short answer

| Source | Data it gives | Hardware needed | Diff. | Sources |
|---|---|---|---|---|
| **Mixer line-out → USB audio interface** | Clean stereo audio of the mix (no crowd noise, no room echo). No "meaning" (no BPM, no deck info) — we still analyse it ourselves. | Any mixer or controller with a spare output (booth / rec / master). A cheap line-in interface, e.g. Behringer UCA202, about US$16. | **1** | [15], [28] |
| **Ableton Link** | Shared tempo (BPM), beat position and phase (where we are inside the bar), start/stop. Nothing about decks, tracks or effects. | Just a laptop on the same network as DJ software that supports Link (rekordbox, Serato DJ Pro, VirtualDJ, djay, Denon Prime units). Free. | **2** | [24], [25], [26], [27] |
| **MIDI out from a DJ controller** (e.g. DDJ-FLX4) | Every knob, fader and button the DJ touches: channel faders, crossfader, EQ, filter/Color FX knob, FX on/off, tempo slider, play. Positions only — not the software's effect *result*. | The controller + laptop. Reading it alongside the DJ software is easy on a Mac, awkward on older Windows. | **2** | [16], [17], [18], [19], [20] |
| **MIDI out from a club mixer** (e.g. DJM-900NXS2) | Positions of the mixer's faders and controls when moved, plus MIDI clock (BPM) sent all the time. | The mixer, USB cable to our laptop, press the mixer's MIDI ON/OFF button. | **2** | [15] |
| **DJ library files (pre-analysis)** | Offline, per track: beat grid, BPM, key, cue points, waveforms. rekordbox also has **phrase analysis** (intro / verse / chorus / outro, with a mood). Serato and Engine have grids, cues, BPM. | None live. We read the DJ's USB stick or library on a laptop. | **2–3** | [6], [10], [11], [12], [13], [14] |
| **Pioneer Pro DJ Link** (beat-link, prolink-connect, python-prodj-link) | The richest live feed: every beat, BPM, pitch %, beat-in-bar, which player is tempo master, which channel is **on air**, track title/artist/key/artwork, beat grid, waveforms, phrase data. CDJ-3000 adds playhead position every 30 ms. | Real Pioneer gear with an Ethernet "LINK" port (CDJ-2000NXS2, CDJ-3000, XDJ-1000, XDJ-XZ…), ideally a DJM mixer, a wired network switch, laptop on Ethernet. **Not** DJ controllers without a LINK jack. | **4** (software 3, gear 5 for us) | [1]–[5], [7]–[9] |
| **Denon StageLinQ** | Per deck: BPM, play state, track position, track info; mixer fader positions; a beat stream. | Denon/Engine DJ hardware (Prime 4, Prime 2, Prime Go, SC6000, X1850…). Same wired network. | **4** | [21], [22], [23] |
| **Official PRO DJ LINK Bridge** | Track and playback data from CDJs/DJMs to lighting and video software. | Pioneer gear + being a certified licensed partner (unverified). | **5** | [31], [32] |

**Recommendation.** The cheapest, most reliable level-2 input is **mixer line-out into a ~US$16 USB interface**. It works with any DJ setup, has no protocol to break, and fixes the mic's biggest problem (crowd and room noise). The first step into real DJ *data* is **Ableton Link** (free, official, gives exact BPM + beat phase — exactly what we need to stretch a 124 BPM light show to 135 BPM), paired with **controller MIDI** on a Mac for faders, filter and FX. **Pro DJ Link is a later add-on**: best data by far, but only if we can borrow CDJs and a switch.

---

## 1. Pioneer Pro DJ Link

**What it is.** Pro DJ Link is the network that Pioneer (now AlphaTheta) CDJs and DJM mixers use to talk to each other over Ethernet. The players constantly broadcast small UDP packets (UDP = a "fire and forget" network message) saying what they are doing. Deep Symmetry reverse-engineered these packets by capturing them, and published the results [3].

**What it exposes.**
- **Beat packets**, sent on every beat. They carry the BPM (×100), the pitch adjustment, the beat within the bar (counts 1 → 2 → 3 → 4), and how many milliseconds until the next beat, next bar, and so on [4]. The mixer also sends beat packets as a backup metronome [4].
- **CDJ-3000 absolute position packets**, every 30 ms, giving the playhead position in milliseconds. This stays accurate during scratching, reverse and loops [4].
- **Status**: playing / stopped, sync on/off, **on-air**, and which player is **tempo master** (the deck everyone else syncs to) [1].
- **On-air flags come from the mixer.** A DJM broadcasts one flag per channel saying whether that channel is audible (faders, crossfader, filters and master level all count). It sends only on/off — the write-up documents no actual fader positions [5].
- **Metadata**: title, artist, genre, length, key and artwork [1].
- **Analysis**: beat grids, waveforms and phrase analysis [1]. Beat Link Trigger can fire **phrase triggers** (e.g. "the chorus started") and run pre-built "show files" tied to a track [7].

**Libraries.**

| Library | Language | Licence | Last push (GitHub API) | Notes |
|---|---|---|---|---|
| beat-link [1] | Java | EPL-2.0 | 2026-06-22 | The reference library. |
| Beat Link Trigger [2], [7] | Java app | EPL-2.0 | 2026-08-28 | Ready-made app. Outputs MIDI, OSC, Ableton Link; has examples for QLC+, grandMA2, Pangolin BEYOND. We could use it as a data source with zero code. |
| prolink-connect [8] | TypeScript | MIT | 2026-09-18 | Player status + metadata from USB/SD or rekordbox. |
| python-prodj-link [9] | Python | Apache-2.0 | 2025-05-11 | Self-described "early beta"; warns it "can freeze your players". Tested on CDJ-2000/NXS/NXS2, XDJ-1000, DJM-900 Nexus/NXS2. |

**Hardware.** Works well with Nexus-era gear and newer: CDJ-2000NXS/NXS2, CDJ-3000, XDJ-1000, XDJ-XZ [1], [2]. The XDJ-RX and XDJ-RX2 are **not** supported ("the XDJ-RX does not actually implement the protocol") [1]. Opus Quad is experimental [1]. **Controllers with no LINK (Ethernet) jack cannot work** [1] — so a DDJ controller running rekordbox gives us nothing here.

**Network.** Wired only: "Do not use Wi-Fi" [7]. Best setup is a dedicated gigabit switch with only DJ gear on it, and a second network adapter on our laptop. rekordbox must not run on the same adapter. UDP ports 50000–50002 must not be firewalled [7].

**Virtual CDJ limits.** Our laptop joins the network pretending to be a player (a "virtual CDJ").
- beat-link uses an unused device number 5–15 by default. That is enough to *hear* beats and status [1].
- To pull **metadata** it must take a real player number, so you can have **no more than three real players** [1].
- prolink-connect: using an ID of 1–6 takes a CDJ slot, leaving room for 5 CDJs [8].
- Tracks from **streaming services** lack the analysis files, so many features break. Use local USB tracks analysed in rekordbox [2].

**Verdict.** Best data by a mile, and the software side is mature. The problem is gear: we would need to borrow at least two NXS2/3000 players, a DJM mixer and a switch.

---

## 2. Library metadata and pre-analysis files

This is the source for the **pre-planned light show** feature: we read the DJ's analysis ahead of time, then use a live BPM (Link, DJ Link or our own beat tracker) to stretch the show to the live tempo.

- **rekordbox XML (official).** rekordbox can export and import an XML library, and publishes the format [11], [12]. Each track has `AverageBpm` and `Tonality` (key). A `TEMPO` element gives the beat grid: `Inizio` (start time), `Bpm`, `Metro` (time signature) and `Battito` (beat number in the bar). `POSITION_MARK` gives cue points [12]. **Easiest and fully documented.** No phrase data in this format (as far as the spec we read shows).
- **rekordbox ANLZ files (reverse-engineered).** These sit on the exported USB stick. `.DAT` = standard analysis, `.EXT` = extended (colour waveforms), `.2EX` = CDJ-3000 three-band waveforms [6]. Tags include `PQTZ` (beat grid), `PCOB`/`PCO2` (cues), waveforms, and `PSSI` (**song structure / phrases**) [6]. Phrases come in three moods (high / mid / low) with kinds like Intro, Verse 1–6, Chorus, Bridge, Up, Down, Outro, each with the beat it starts on [6]. PSSI is XOR-masked (lightly scrambled with a known pattern), which the documentation explains how to undo [6].
- **pyrekordbox** (Python, MIT) reads the rekordbox `master.db` database (encrypted SQLite, needs SQLCipher and a key present on the rekordbox machine), XML, ANLZ files and settings files. Tested on rekordbox 5.8.6, 6.7.7, 7.0.9 [10]. It warns: back up your collection first [10].
- **Serato** stores its analysis *inside the audio file*, in ID3 GEOB tags (MP3) or MP4 atoms: `BeatGrid`, `Markers2` (hot cues, loops, colours), `Autotags` (BPM, gain), `Overview` (waveform) [13]. Documented by reverse engineering; scripts MIT [13].
- **Engine DJ (Denon)** uses a database library. libdjinterop (C++, LGPL-3.0) reads tracks, beat grids, hot cues, loops and waveforms; supports Engine DJ OS 1.0.3–4.3.3 and desktop 1.0.1–4.3.0; "not all features are implemented yet" [14].

**Verdict.** rekordbox XML is difficulty 2 and enough for beat grids. ANLZ via pyrekordbox is difficulty 3 but is the only source with **phrase analysis** — very useful for lighting (chorus = big look, breakdown = calm look).

---

## 3. MIDI out from controllers and mixers

**What it is.** MIDI is a simple standard where each control sends a small message such as "control 19 moved to value 87". Most DJ controllers are just MIDI devices; the DJ software turns those messages into actions.

**DJ controllers.** The DDJ-FLX4 is "USB audio and MIDI class compliant" (needs no driver) [16]. Its effects run **in the software**; the controller only sends positions [16]. A community-written message list (not checked against Pioneer's official list, which we could not open) shows 14-bit messages (extra-fine, two messages per move) for channel faders, crossfader, EQ high/mid/low, the Color FX/filter knob and the tempo slider, and notes for FX on/off and play [17].

So we **can** see: fader moves, EQ, filter sweeps, FX button presses. We **cannot** see: which effect is selected in the software, or what it sounds like — only the knob.

**Club mixers.** The DJM-900NXS2 "outputs the operation information of buttons and controls in universal MIDI format" over USB. After pressing MIDI ON/OFF, "When a fader or control is moved, a message corresponding to the position is sent." MIDI timing clock (BPM) is sent regardless of the button [15, p. 14]. The full message list is on Pioneer's support site (unverified — we did not open it).

**Sharing the MIDI port with the DJ software.**
- **macOS:** fine. Core MIDI runs one MIDIServer that "allows multiple clients to be connected simultaneously" [18].
- **Windows:** the classic MIDI API is exclusive — one app per device [19]. The new Windows MIDI Services stack is multi-client and began rolling out in Feb 2026 on Windows 11 24H2/25H2/26H1, with bugs still being fixed [20]. Workaround on older systems: a virtual loopback port (e.g. loopMIDI) [19].

**Verdict.** Difficulty 2. Cheap and reliable if we own a controller and demo on a Mac. Mapping is per model, so pick one controller and stick with it.

---

## 4. Denon StageLinQ

StageLinQ is Denon's network protocol for sharing live deck and mixer state, used by lighting desks and stream overlays [21]. Devices use link-local addresses (169.254.x.x) and announce themselves by UDP broadcast on port 51337 [21]. Data comes from a "StateMap" service: play state, BPM, position, fader positions, track info, beat info [21], [22].

- go-stagelinq (Go, MIT): current beat, total beats, BPM, timeline position; "only has been practically tested with the Denon Prime 4"; calls itself "an experimental reverse-engineering effort" [22].
- StageLinq (Node.js, GPL-3.0): tested with SC6000, X1850, Prime 4, Prime 2, Prime Go [23]. Last push Feb 2023 (GitHub API).
- PyStageLinQ (Python, MIT) exists; its protocol notes admit the full list of paths is not documented [21].

**Verdict.** Difficulty 4: needs Denon gear, and the libraries are thinner than Pioneer's.

---

## 5. Ableton Link

Link is Ableton's open protocol that keeps tempo, beat and phase in sync between apps on a local network, including start/stop [24]. It is **official and documented**, not reverse-engineered. Licence: GPLv2+, or a paid proprietary licence from Ableton [24].

- DJ software on Ableton's Link product list includes **rekordbox**, **VirtualDJ**, **djay**, and Denon Prime / SC5000 / SC6000 hardware [25]. Serato DJ Pro supports Link according to Serato's support pages (unverified — the page blocked our fetch; seen only in search results) [27].
- Python: **aalink** (GPL-3.0) gives tempo, beat and phase and can `await link.sync(1)` to wake on every beat [26].
- **Limit:** Link shares one session tempo and phase. It does not say which deck is live, which track is playing, or anything about effects [24].

**Verdict.** Difficulty 2 and free. Best "real DJ data" per dollar. It is exactly the signal needed to time-stretch a pre-planned light show.

---

## 6. Plain mixer line-out

Every mixer has spare outputs. The DJM-900NXS2 has BOOTH and REC OUT terminals besides MASTER1/2 [15, p. 6]. A USB interface with RCA line inputs, like the Behringer UCA202 (2× RCA in, USB-powered, 16-bit / 48 kHz, US$16.40 at Thomann), brings that into the laptop [28].

This is still just audio, so our own beat tracking and ML do all the work. But it is clean audio: no crowd, no room reflections, known level.

**Verdict.** Difficulty 1. Works with every DJ setup on earth.

---

## 7. Legal and licensing notes

This is not legal advice — it is what the sources say.

- **Not sanctioned.** beat-link says it is "in no way a sanctioned implementation of the protocols" — use at your own risk [1]. Firmware updates can break it [2]. go-stagelinq and pyrekordbox carry similar "independent / experimental" warnings [10], [22].
- **Interoperability is a recognised exception.** Canada's Copyright Act s. 41.12 lets a person get around a technical protection measure on a lawfully obtained program "for the purpose of obtaining information that would allow the person to make the program … interoperable" with other programs or devices [30]. The US has a similar rule in 17 U.S.C. §1201(f) [29]. Also, most of what we would do is **passive listening** to broadcast packets on our own network, which involves no circumvention at all. (Our reading; unverified by a lawyer.)
- **Software licences matter if we ship code.** MIT and Apache-2.0 are permissive. EPL-2.0 (beat-link) is weak copyleft. GPL (Ableton Link, aalink, StageLinq-Node) means any program we *distribute* that includes it must also be released under the GPL [24], [26]. For a capstone that is published openly, that is fine.
- **Safety at a live gig.** Only *listen*. Do not use the libraries' remote-control features (loading tracks, taking a player number) on someone else's gig — python-prodj-link warns it can freeze players [9].
- **The official route exists but is closed to us.** AlphaTheta's PRO DJ LINK Bridge passes real-time track and playback data from CDJs and DJMs to lighting software [32]. AlphaTheta runs a certification program for third-party PRO DJ LINK products [31], and its help pages describe Bridge as working with **certified products from licensed companies** (unverified — the help page blocked our fetch; seen in search results only). The certification page does not say how an independent developer could join [31]. Relevant news from today: rekordbox and PRO DJ LINK Bridge now support SoundSwitch lighting [32] — a commercial product close to ours, worth naming in the proposal's "existing solutions" section.

---

## Sources

[1] Deep Symmetry, "beat-link," GitHub repository. [Online]. Available: https://github.com/Deep-Symmetry/beat-link (accessed Sep. 24, 2026).

[2] Deep Symmetry, "beat-link-trigger," GitHub repository. [Online]. Available: https://github.com/Deep-Symmetry/beat-link-trigger (accessed Sep. 24, 2026).

[3] Deep Symmetry, "DJ Link Ecosystem Analysis: Packet Analysis." [Online]. Available: https://djl-analysis.deepsymmetry.org/djl-analysis/ (accessed Sep. 24, 2026).

[4] Deep Symmetry, "DJ Link Ecosystem Analysis: Beats." [Online]. Available: https://djl-analysis.deepsymmetry.org/djl-analysis/beats.html (accessed Sep. 24, 2026).

[5] Deep Symmetry, "DJ Link Ecosystem Analysis: Mixer Integration." [Online]. Available: https://djl-analysis.deepsymmetry.org/djl-analysis/mixer_integration.html (accessed Sep. 24, 2026).

[6] Deep Symmetry, "rekordbox Export Structure Analysis: Analysis Files." [Online]. Available: https://djl-analysis.deepsymmetry.org/rekordbox-export-analysis/anlz.html (accessed Sep. 24, 2026).

[7] Deep Symmetry, "Beat Link Trigger User Guide." [Online]. Available: https://blt-guide.deepsymmetry.org/beat-link-trigger/README.html (accessed Sep. 24, 2026).

[8] E. Purkhiser, "prolink-connect," GitHub repository. [Online]. Available: https://github.com/EvanPurkhiser/prolink-connect (accessed Sep. 24, 2026).

[9] flesniak, "python-prodj-link," GitHub repository. [Online]. Available: https://github.com/flesniak/python-prodj-link (accessed Sep. 24, 2026).

[10] dylanljones, "pyrekordbox," GitHub repository. [Online]. Available: https://github.com/dylanljones/pyrekordbox (accessed Sep. 24, 2026).

[11] AlphaTheta, "rekordbox — For developers." [Online]. Available: https://rekordbox.com/en/support/developer/ (accessed Sep. 24, 2026).

[12] AlphaTheta, "rekordbox XML format list," PDF. [Online]. Available: https://cdn.rekordbox.com/files/20200410160904/xml_format_list.pdf (accessed Sep. 24, 2026).

[13] Holzhaus, "serato-tags," GitHub repository. [Online]. Available: https://github.com/Holzhaus/serato-tags (accessed Sep. 24, 2026).

[14] xsco, "libdjinterop," GitHub repository. [Online]. Available: https://github.com/xsco/libdjinterop (accessed Sep. 24, 2026).

[15] Pioneer DJ, *DJ Mixer DJM-900NXS2 Operating Instructions*, pp. 6, 14. [Online]. Available (third-party mirror): https://www.novelty.fr/wp-content/uploads/downloaded/downloads/materiel_manuels/pioneer_djm-900nxs2_manual_EN.pdf (accessed Sep. 24, 2026).

[16] Mixxx, "Pioneer DDJ-FLX4," *Mixxx User Manual 2.4*. [Online]. Available: https://manual.mixxx.org/2.4/en/hardware/controllers/pioneer_ddj_flx4 (accessed Sep. 24, 2026).

[17] brxs, "midi-ddj-flx4.md," GitHub repository *lsdjai* (community document). [Online]. Available: https://github.com/brxs/lsdjai/blob/main/docs/midi-ddj-flx4.md (accessed Sep. 24, 2026).

[18] Sound On Sound, "Audio MIDI Setup." [Online]. Available: https://www.soundonsound.com/techniques/audio-midi-setup (accessed Sep. 24, 2026).

[19] Microsoft Q&A, "Windows 11 25H2 multiclient MIDI." [Online]. Available: https://learn.microsoft.com/en-us/answers/questions/4371458/windows-11-25h2-multiclient-midi (accessed Sep. 24, 2026).

[20] Microsoft, "Windows MIDI Services 2026 release — known issues and workarounds," *Windows MIDI and Music dev blog*. [Online]. Available: https://devblogs.microsoft.com/windows-music-dev/windows-midi-services-rollout-known-issues-and-workarounds/ (accessed Sep. 24, 2026).

[21] Jaxc, "StageLinQ_protocol.md," GitHub repository *PyStageLinQ*. [Online]. Available: https://github.com/Jaxc/PyStageLinQ/blob/main/StageLinQ_protocol.md (accessed Sep. 24, 2026).

[22] icedream, "go-stagelinq," GitHub repository. [Online]. Available: https://github.com/icedream/go-stagelinq (accessed Sep. 24, 2026).

[23] MarByteBeep, "StageLinq," GitHub repository. [Online]. Available: https://github.com/MarByteBeep/StageLinq (accessed Sep. 24, 2026).

[24] Ableton, "Link," GitHub repository. [Online]. Available: https://github.com/Ableton/link (accessed Sep. 24, 2026).

[25] Ableton, "Link-enabled products." [Online]. Available: https://www.ableton.com/en/link/products/ (accessed Sep. 24, 2026).

[26] artfwo, "aalink," GitHub repository. [Online]. Available: https://github.com/artfwo/aalink (accessed Sep. 24, 2026).

[27] Serato, "Using Link," *Serato Support*. [Online]. Available: https://support.serato.com/hc/en-us/articles/228009728-Using-Link (unverified — page returned HTTP 403 to our fetcher; content seen in search results only, Sep. 24, 2026).

[28] Thomann, "Behringer U-Control UCA202." [Online]. Available: https://www.thomannmusic.com/behringer_ucontrol_uca_202.htm (accessed Sep. 24, 2026).

[29] *Circumvention of copyright protection systems*, 17 U.S.C. § 1201(f). [Online]. Available: https://www.law.cornell.edu/uscode/text/17/1201 (accessed Sep. 24, 2026).

[30] *Copyright Act*, R.S.C. 1985, c. C-42, s. 41.12. [Online]. Available: https://laws-lois.justice.gc.ca/eng/acts/C-42/section-41.12.html (accessed Sep. 24, 2026).

[31] AlphaTheta, "AlphaTheta Certification Program." [Online]. Available: https://www.pioneerdj.com/en/landing/alphatheta-certified/ (accessed Sep. 24, 2026).

[32] The FADER, "rekordbox and PRO DJ LINK Bridge now support SoundSwitch lighting software," Sep. 24, 2026. [Online]. Available: https://www.thefader.com/2026/09/24/rekordbox-pro-dj-link-bridge-lighting-software (accessed Sep. 24, 2026).
