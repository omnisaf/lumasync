# Existing solutions and the gap

What already turns music into lighting, what it costs, what it needs, and what none of it can do. Researched 2026-09-24; prices move, treat them as "about".


**How this was checked (2026-09-24).** Every price and claim below comes from a page that was opened on that date. Source numbers like [3] point to the list at the bottom. Where a page did not say something, the table says **unverified** rather than guessing. Prices are as shown on the page, with the currency the page used.

---

## Words you need first

- **DMX** (DMX512): the standard cable signal that stage lights listen to. One cable carries 512 channels, called one **universe**. A laptop needs a small USB-to-DMX box to speak it.
- **Art-Net / sACN**: DMX sent over a normal network cable instead of a DMX cable.
- **Beatgrid**: the list of beat positions a DJ app works out for a track, so it knows where every beat and bar falls.
- **Phrase analysis**: software splitting a track into sections (intro, build, drop/chorus, outro) ahead of time.
- **Pre-scripting**: a human sits down and programs a light show for one specific song, like editing a video timeline.
- **Pro DJ Link**: Pioneer's network link between CDJ players. It shares what is playing, the tempo and the beat position.
- **Sound-active mode**: a built-in mode in cheap lights. A tiny microphone hears the bass and the light steps through its own canned patterns.

---

## Comparison table

| Product | Price seen (2026-09-24) | Inputs it uses | Human setup | New/unanalysed track, or tempo change |
|---|---|---|---|---|
| **SoundSwitch** (software) | Software $7.99/mo, $79.99/yr or $199 lifetime; Micro DMX box $39.99; Control One $299.99 [1]. Micro DMX box is CAD $49 at a Canadian shop [7]. SoundSwitch's own site shows "$" with no currency code, likely USD. | Deck data from supported DJ apps: Engine DJ, rekordbox, Serato, Virtual DJ, plus Ableton Link and MIDI clock [2], [3]. Since v2.9, also a mic or any audio input, but only for tempo [5]. | Low to high. AutoScripting and phrase detection build a show per track automatically. Hand-made shows are built cue by cue in its editor [3]. Needs supported DJ software for full use [6]. | Tracks with no script fall back to **Autoloops**: generic 8–128-bar loops locked to the DJ app's beatgrid [4]. Because it follows the beatgrid, it follows tempo changes made in the DJ app. From plain audio it only gets BPM and runs Autoloops, with no song sections [5]. |
| **rekordbox Lighting mode** | Plans: Core $120/yr, Creative $180/yr, Professional $360/yr, Free $0 (USD) [8]. The plan page lists DMX lighting on all plans [8], but the lighting FAQ says ENTTEC boxes need Creative or Professional [9]. The two official pages disagree. | Tracks in rekordbox with phrase analysis done [9], [10]. Also Pioneer players over Pro DJ Link ("PRO DJ LINK Lighting") [10]. Needs a supported DMX box: RB-DMX1, DDJ-FLX10, or ENTTEC Open DMX / DMX USB Pro / Pro Mk2 [9]. | Low. Scenes are picked automatically from phrase and "mood" (HIGH/MID/LOW, from tempo, rhythm, kick drum and density) [10]. Can be hand-edited in a macro editor [10]. | "If tracks are not phrase-analyzed, you cannot perform lighting in sync with the tracks" [9]. With Pro DJ Link, a "default scene" plays when no phrase info arrives [10]. Following live tempo changes is not stated in the guide: **unverified**. Only fixed fixture types work (par, bar, moving head, strobe, spot) [9]. |
| **Pioneer RB-DMX1** (the DMX box for rekordbox) | Launched at $349 USD with a rekordbox dj licence (2018) [12]. Now listed as discontinued [13]. Cheapest supported replacement: ENTTEC Open DMX at $70 on ENTTEC's site (currency not shown) [14]; ENTTEC DMX USB Pro at $162 [16]. | USB from the laptop; one DMX universe [11]. | Plug in; setup is all in rekordbox [11]. | Same as rekordbox above. It is only an output box. |
| **MaestroDMX** (Limbic Media) | $899.00 USD on the maker's site [18]; $959 USD at Thomann [19]. One-off hardware, no subscription [21]. | Live audio only: RCA line-in, or a USB audio interface for XLR [17]. One DMX universe (512 channels) [19]. No Pro DJ Link; tempo comes from the kick drum in the audio [20]. | Low. Browser setup "in minutes" [18]. A reviewer on the maker's page says it is not quite set-and-forget: you still choose a lighting style [18]. | Works with any song because nothing is pre-analysed [17], [21]. But it only knows what it has already heard. It cannot see a drop coming (our reading of how it works, not a vendor claim). BPM tracking relies on a clear kick drum [20]. |
| **Lightkey** (Mac app) | 1-year licences (USD): $79 (256 ch), $119 (512 ch), $199 (1024 ch), $379 (8192 ch). Free edition limited to 24 DMX channels [23]. | Tempo from tapping, MIDI clock or Ableton Link. Cues can be placed on an Ableton Live timeline [22]. No built-in audio analysis found on its official pages [22]. | High. A human builds every cue and look [22]. | Nothing is analysed, so no track is "new" to it. It follows whatever tempo the tap or clock gives it. It knows nothing about song sections. |
| **QLC+** (open source) | Free, Windows/macOS/Linux [24]. Needs a USB-DMX box (e.g. $70 ENTTEC Open DMX [14]). | Audio input (mic or line) split into 5–32 frequency bars. Each bar can trigger a light, a function or a cue list when it crosses a threshold [25]. Art-Net, sACN, OSC, MIDI [24]. | High. You build the scenes, then wire each frequency band to them [25]. | Reacts to any audio in real time. Its own site says "BPM detection coming soon", so today it has no tempo tracking [24]. No song-structure awareness [25]. |
| **LedFx** (open source) | Free, GPL-3.0 [26]. Needs a PC plus LED strip controllers such as WLED boards (not priced here). | The PC's own audio output, or a mic [26]. Sends to WLED and E1.31 (sACN) devices [26]. | Low to medium. Pick effects in a web page [26]. | Pure live reaction to the sound. Tempo tracking or song structure is not described in its docs [26]. LED strips only, not stage lights. |
| **WLED sound-reactive** (open source) | Free firmware. Needs an ESP32 board and a mic (not priced here) [27]. | I2S digital mic (e.g. INMP441), or line-in through a small audio chip. One board can share its audio with others over Wi-Fi (UDP) [27], [28]. | Medium. Wiring, then tuning Squelch, Gain and auto-gain [27]. | Pure live reaction. The docs mention no tempo tracking or song structure [27]. LED strips only. |
| **ChamSys MagicQ** (pro console software) | Software free [29]. Demo mode already outputs 64 universes over Art-Net/sACN [29]. MagicDMX Full USB box $125 USD [30]. Some features need paid ChamSys hardware (price not listed) [29]. | Audio input can drive a fader level, fire GO, set BPM, or step cues on the beat [31]. DJ links listed: VirtualDJ (OS2L), Engine DJ (StagelinQ), TCNet, plus a beat-tracking section [32]. | High. A trained operator programs cue stacks. It is a full professional console, not an auto-show tool. | Audio beat tracking sets the tempo live [31], so tempo changes are followed. It does not write a show for a new song; a human must have built one. |
| **Built-in "sound active" mode** on cheap fixtures | Betopper pars from $24.19 USD each; 8-packs from $299 USD [35]. Brand-name example: Chauvet DJ SlimPAR H6 ILS, $371.99 CAD [36]. | Tiny mic inside the light. Chauvet: it will "trigger the built-in program to the beat of the music" [33]. | None. Flip a switch; set a sensitivity knob [33], [37]. Several lights can copy one "master" light [33]. | Works with any song. It just chases through canned colour patterns when it hears sound [34]. No idea of tempo, sections, or the rest of the rig. |

**Also found:** ENTTEC ships a 3-month licence for its own sound-to-light app, EMU, with the DMX USB Pro [15]. A Chauvet controller manual (DM-X6) shows the same sound-active idea built into a cheap desk: colour jumps to the beat its internal mic hears [37].

---

## What the table shows

Every product falls into one of two groups.

**1. They know the song, but only inside DJ software.** SoundSwitch and rekordbox Lighting do the clever part: they cut each track into sections ahead of time and plan light changes around them. The catch is that they only work when the music plays through their supported DJ apps or Pioneer gear. An unanalysed track drops to generic loops [4] or a default scene [9], [10]. A live band, a phone on Spotify, or vinyl only gets SoundSwitch's BPM-only mode [5]. rekordbox has nothing for them.

**2. They hear the room, but only react.** MaestroDMX, QLC+, LedFx, WLED, MagicQ's audio input and sound-active fixtures all work with any sound source. But they react to what just happened. None of them knows a drop is 8 bars away, or that the chorus is coming back. The only one that looks polished, MaestroDMX, costs about $900 USD for one universe [18], [19].

**Nobody offers editable, AI-drafted shows.** SoundSwitch's AutoScripting comes closest: it drafts a show that you can then edit [3]. But it runs inside one vendor's software, on tracks in that vendor's library.

---

## The gap (for the report introduction)

1. Tools that *know the song* (SoundSwitch, rekordbox Lighting) only work inside specific DJ software, and fall back to generic loops or a default scene the moment a track has not been pre-analysed.
2. Tools that *work with any audio* (MaestroDMX, QLC+, WLED/LedFx, sound-active fixtures) only react to the last beat they heard, and the one polished option costs about US $900.
3. No low-cost system does both: a per-song show planned in advance (or drafted by AI and edited by a human), locked to the live tempo from any source, that falls back to live-audio mode for unknown tracks.

**One-line gist:** Song-aware tools lock you into DJ software; any-audio tools only react. Nothing cheap does both.

---

## Loose ends

- **rekordbox plan conflict.** The plans page [8] and the lighting FAQ [9] disagree on which plan you need to drive an ENTTEC box. If this matters for the report, cite the stricter one (Creative, $180 USD/yr).
- **Cheap-fixture prices** change often. The Betopper figure is a lower bound from the maker's own store.
- **SoundSwitch currency.** The official shop shows "$" only. Use the Canadian price [7] if the report needs CAD.

---

## Sources (IEEE style, all accessed Sep. 24, 2026)

[1] SoundSwitch, "Shop." [Online]. Available: https://www.soundswitch.com/shop

[2] SoundSwitch, "SoundSwitch – DMX lighting control for DJs." [Online]. Available: https://www.soundswitch.com/

[3] SoundSwitch, "Software." [Online]. Available: https://www.soundswitch.com/software

[4] SoundSwitch Support, "SoundSwitch | Autoloops explained." [Online]. Available: https://support.soundswitch.com/en/support/solutions/articles/69000847100-soundswitch-autoloops-explained

[5] SoundSwitch Support, "SoundSwitch | BPM Detection overview." [Online]. Available: https://support.soundswitch.com/en/support/solutions/articles/69000858486-soundswitch-bpm-detection-overview

[6] SoundSwitch Support, "Can I use SoundSwitch without a DJ controller?" [Online]. Available: https://support.soundswitch.com/en/support/solutions/articles/69000848636-can-i-use-soundswitch-without-a-dj-controller-

[7] Acclaim Sound and Lighting, "SoundSwitch DMX Micro Interface USB to DMX XLR connector and software." [Online]. Available: https://www.acclaim-music.com/soundswitch-dmx-micro-interface-usb-to-dmx-xlr-connector-and-software.html

[8] AlphaTheta, "Plans & pricing | rekordbox." [Online]. Available: https://rekordbox.com/en/plan/

[9] AlphaTheta, "FAQ: Lighting function | rekordbox." [Online]. Available: https://rekordbox.com/en/support/faq/lighting-7/

[10] AlphaTheta, *rekordbox LIGHTING mode Operation Guide* (rekordbox 7.0.7). [Online]. Available: https://cdn.rekordbox.com/files/20241216130922/rekordbox7.0.7_lighting_operation_guide_EN.pdf

[11] Pioneer DJ, "RB-DMX1 – DMX interface for rekordbox dj lighting mode." [Online]. Available: https://www.pioneerdj.com/en/product/software-interfaces/rb-dmx1/

[12] DJ TechTools, "Rekordbox 5.1 Lyric, Rekordbox 5.2 Lighting, and RB-DMX1," Jan. 18, 2018. [Online]. Available: https://djtechtools.com/2018/01/18/rekordbox-5-1-lyric-rekordbox-5-2-lighting-rb-dmx1/

[13] SE Concept, "Pioneer DJ RB-DMX1 (Discontinued)." [Online]. Available: https://seconcept.com/products/rb-dmx1

[14] ENTTEC, "Open DMX USB." [Online]. Available: https://www.enttec.com/product/dmx-usb-interfaces/open-dmx-usb/

[15] ENTTEC, "DMX USB PRO." [Online]. Available: https://www.enttec.com/product/dmx-usb-interfaces/dmx-usb-pro-professional-1u-usb-to-dmx512-converter/

[16] Techni-Lux, "ENTTEC 70304 DMX USB PRO." [Online]. Available: https://www.techni-lux.com/Products/Usb/Enttec/70304/CT-EN70304

[17] MaestroDMX, "MaestroDMX – intelligent lighting control." [Online]. Available: https://maestrodmx.com/

[18] MaestroDMX, "MaestroDMX" (product page). [Online]. Available: https://maestrodmx.com/products/maestrodmx

[19] Thomann, "LimbicMedia MaestroDMX." [Online]. Available: https://www.thomannmusic.com/limbicmedia_maestrodmx.htm

[20] MaestroDMX Support Forum, "Pro DJ Link integration for enhanced synchronization in MaestroDMX." [Online]. Available: https://maestrodmx.freshdesk.com/support/discussions/topics/153001057597

[21] National Association of Disc Jockeys (UK), "DMX lighting software for DJs: The complete guide." [Online]. Available: https://www.nadj.org.uk/news/dmx-lighting-software-for-djs-the-complete-guide/

[22] Lightkey, "Lightkey – Professional DMX lighting control." [Online]. Available: https://lightkeyapp.com/en/

[23] Lightkey (FastSpring store), "Lightkey – all products." [Online]. Available: https://sites.fastspring.com/lightkey/product/all

[24] QLC+ project, "Q Light Controller+." [Online]. Available: https://www.qlcplus.org/

[25] QLC+ project, "Audio triggers – basics," *QLC+ Documentation*. [Online]. Available: https://docs.qlcplus.org/v4/virtual-console/audio-triggers

[26] LedFx contributors, "LedFx," GitHub repository. [Online]. Available: https://github.com/ledfx/ledfx

[27] WLED project, "Audio reactive WLED," *WLED Knowledge Base*. [Online]. Available: https://kno.wled.ge/advanced/audio-reactive/

[28] WLED contributors, "usermods/audioreactive/readme.md," GitHub repository. [Online]. Available: https://github.com/wled/WLED/blob/main/usermods/audioreactive/readme.md

[29] ChamSys, "MagicQ software licensing." [Online]. Available: https://chamsyslighting.com/software/magicq-software-licensing/

[30] ChamSys, "MagicDMX Full." [Online]. Available: https://chamsyslighting.com/product/magicdmx-full/

[31] ChamSys, "Audio," *MagicQ User Manual* (v1.9.9.x). [Online]. Available: https://docs.chamsys.co.uk/magicq/1.9.9.x/manual/audio.html

[32] ChamSys, "DJ," *MagicQ User Manual* (v1.9.9.x). [Online]. Available: https://docs.chamsys.co.uk/magicq/1.9.9.x/manual/dj.html

[33] Chauvet DJ, *6SPOT User Manual*, Rev. 4. [Online]. Available: https://www.chauvetdj.com/wp-content/uploads/2015/12/6Spot_UM_Rev4.pdf

[34] Venue Lighting Effects, *LED PAR64 User Manual*. [Online]. Available: https://venuelightingeffects.com/wp-content/uploads/2024/06/Venue_PAR64_LED.pdf

[35] Betopper, "DJ par lights – DMX controlled, sound activated." [Online]. Available: https://betopperdj.com/products/betopper-leds-upgrade-stage-lights-dmx-controlled-dj-par-lights-for-party-wash-lighting

[36] Long & McQuade, "Chauvet DJ SlimPAR H6 ILS." [Online]. Available: https://www.long-mcquade.com/290716/Pro-Audio-Recording/Lighting-Fog-Machines/Chauvet-DJ/SlimPAR-H6-ILS.htm

[37] AVSL, *DM-X6 Mini DMX PAR Controller User Manual* (item 154.097UK). [Online]. Available: https://www.avsl.com/assets/manuals/1/5/154097UK.pdf
