# The cheapest way to drive DMX

What is the cheapest reliable way to send DMX from a laptop or microcontroller to real fixtures and to cheap LED strips, with one code path? Researched 2026-09-24.

**How this was checked (2026-09-24).** Every claim below cites a source we opened on this date: standards write-ups, manufacturer pages and manuals, library READMEs and shop listings. Amazon prices were read from amazon.com with a Canadian delivery address, so they show in **CAD**. US shops show **USD**. Prices move; treat them as "about". Anything we could not open ourselves is marked **(unverified)**. Anything that is our own reasoning or arithmetic is marked **(our judgement)** or **(our arithmetic)**.

---

## Short answer

**Recommendation.**

1. **Day 1 (about CAD 30):** a CAD ~21 FTDI "USB to DMX" cable, a 120 Ω terminator and free QLC+ software. Use it only to *learn the venue rig*: confirm each fixture's mode, address and channel map. No code needed. It may flicker. That is fine for a diagnostic [8], [9], [14].
2. **The real build (about USD 15 of parts):** an ESP32 board plus an **isolated** RS-485 DMX transceiver (M5Stack AtomS3 Lite USD 7.50 + M5Stack Unit DMX USD 6.95), running the open-source `esp_dmx` library [15]–[19]. The ESP32 makes the DMX timing itself, so the laptop's timing no longer matters. Isolation protects the laptop and board from the fixtures' mains-powered electronics [6], [15].
3. **One code path:** the laptop always outputs **sACN** (DMX sent over a network). The ESP32 turns sACN into real DMX for the fixtures. A second ESP32 running WLED turns the same sACN into WS2812B LED strip light [27], [31]. Fixture channel layouts come from **Open Fixture Library** profiles, so a new rig means a new patch file, not new code [39], [40].

**Optional reference box:** a DMXking ultraDMX MAX (USD 110) is a known-good USB interface with its own timing chip. Buy it only if the DIY node stalls [11].

| Option | Price | Timing made by | Isolated? | Verdict |
|---|---|---|---|---|
| FTDI "USB-DMX" cable (Open DMX clone) | CAD ~21–32 [13], [14] | The laptop | No [10] | Day-1 diagnostic only |
| Enttec Open DMX USB | USD 70 [5] (CAD ~95 on Amazon [13]) | The laptop [6] | No [6] | Same design as the clones, higher price. Skip. |
| **ESP32 + M5Stack Unit DMX (DIY)** | **USD ~14.45** [16], [19] | The ESP32 | **Yes, 5 kVrms** [16] | **Build this** |
| ESP32 + bare MAX485 module (DIY) | CAD ~24 for 3 ESP32s [25] + CAD ~11 for 5 modules [22] | The ESP32 | No | Bench only |
| DMXking ultraDMX MAX | USD 110 [11] (CAD ~178 [13]) | Its own chip [11] | Not stated on the page we opened | Known-good fallback |
| Enttec DMX USB Pro | CAD ~229 on Amazon [13] | Its own chip [7] | Yes, 1500 V [6], [7] | Good, but ~15× the DIY cost |
| Art-Net/sACN node (DMXking eDMX1 MAX) | USD 240 [29] | Its own chip | Not stated | For bigger rigs later |

---

## 1. What we found out about the venue rig

### The "LPC1818" is almost certainly a Betopper LPC1818

It is a Betopper **18 × 18 W LED PAR** (a PAR is a simple round wash light). The venue team should still confirm this from the label [48].

There are **two versions**, and they differ in exactly the way that matters to us:

| Version | LEDs | DMX modes | Source |
|---|---|---|---|
| Older | RGBWA+UV (red, green, blue, white, amber, UV) | 6-ch / 10-ch | Betopper blog [50] |
| "Upgraded" (manual v6.0) | RGB + Lime + Amber + UV | 7-ch / 11-ch | Manual [49], product page [48] |

**The venue's addresses (1, 11, 21 … 71) are 10 apart.** That fits the older version in 10-channel mode.

**Warning.** If they are the *upgraded* version set to **11-channel** mode, the addresses overlap by one. Fixture 1's channel 11 (colour temperature) would be the same DMX slot as fixture 2's channel 1 (master dimmer). Changing one would change the other. *(our arithmetic from [49])*

**Ask the venue:** a photo of one fixture's display. On the upgraded version the display shows `A001` for 11-channel mode and `d001` for 7-channel mode [49].

**Channel map, upgraded version, 11-ch mode** [49]:

| Ch | Function |
|---|---|
| 1 | Master dimmer |
| 2–7 | Red, Green, Blue, Lime, Amber, Purple (UV) dimmers |
| 8 | Strobe, slow → fast |
| 9 | Function select. **0–50 = direct control by ch 1–7.** 51–100 colour presets, 101–150 jump, 151–200 fade, 201–250 pulse, 251–255 sound-active |
| 10 | Function speed |
| 11 | CTO colour temperature (0–15 off, 16–255 nine presets) |

The 7-ch mode is just ch 2–7 plus CTO [49]. **Practical note:** our software must hold channel 9 at 0–50, or the fixture runs its own built-in programs and ignores our colours [49].

We could not find the **older 10-ch channel map** (unverified). Other facts from the manual: 200 W rated, AC 90–240 V, Auto/Sound/DMX/master-slave modes [49]. One forum user asked a lighting-software vendor for an 11-ch profile, which suggests the upgraded version is in circulation [51]. The fixture is **not** in Open Fixture Library (searched "betopper", no match) [41]. We will have to write its profile ourselves, and could contribute it back.

### The "200W Blinder" — model unknown

A blinder is a very bright white light aimed at the crowd. "200W blinder" is a generic product name. Many brands sell one. For example, the SHEHDS 2-eye 200 W COB blinder has **4-ch and 8-ch** modes, warm + cool white, 3-pin XLR DMX [52]. The venue's addresses (81, 89, 97, 105) are 8 apart, which fits an 8-ch mode. **The exact model and channel map are unverified.** Still to confirm with the venue.

### What the rig needs from us

- **Channels used:** the last blinder starts at 105 and uses 8 channels, so the rig ends at channel **112**. That is well under one universe (a *universe* = one DMX line of 512 channels). *(our arithmetic)*
- **Devices on the line:** 12 fixtures. The DMX limit is 32 "unit loads" per line without a splitter [1]. *(our arithmetic)*
- **Power:** 8 × 200 W + 4 × 200 W = **2.4 kW rated** [49], [52]. That is the venue's circuits, not our electronics, but worth knowing before an all-white blinder hit. *(our arithmetic)*

---

## 2. DMX512-A in one page

**What it is.** DMX512 is the cable signal that lighting desks send to lights. DMX512-A is the current version, standardised as ANSI E1.11 [1].

**The wire.** DMX runs on **RS-485**. RS-485 sends each bit as the *difference* between two wires (Data+ and Data−), so noise that hits both wires cancels out [1]. The standard says 5-pin XLR connectors. In practice most cheap gear uses 3-pin XLR, which the standard technically prohibits [1]. Use real 120 Ω DMX cable: microphone cable has the wrong electrical properties [1].

**Daisy chain and termination.** Fixtures are chained: controller → fixture 1 → fixture 2 → … The **last** fixture needs a **120 Ω terminator** across Data+ and Data−. Without it, the signal bounces back off the open end and garbles the data. The symptom is flicker or random values, usually at the far end of the line [3], [4]. Only terminate the physical end, never in the middle [4].

**Speed and framing.** 250 000 bits per second. Each channel value is one byte sent as 11 bits (1 start bit, 8 data bits, 2 stop bits), so each channel takes 44 µs [2]. One DMX **packet** (one full update of every light) looks like this [1]:

1. **Break**: hold the line low for at least 92 µs (receivers accept 88 µs). This says "a new packet is starting".
2. **Mark After Break (MAB)**: line high for at least 12 µs (receivers accept 8 µs).
3. **Start code**: one byte, 0 for normal dimmer data.
4. **Up to 512 channel bytes**, each 0–255.

**Refresh rate.** A full 512-channel packet takes about 23 ms, so about **44 updates per second** at most [1]. Fewer channels means faster updates [2]. Our 112-channel rig could in theory refresh near 197 times per second (92 + 12 + 113 × 44 µs ≈ 5.1 ms) *(our arithmetic)*. We do not need that. A beat at 128 BPM comes about twice a second, so 30–44 Hz is plenty *(our judgement)*. **Steady timing matters more than speed.** Jitter (uneven gaps between packets) shows up as shimmering fades [2].

---

## 3. USB-to-DMX interfaces

There are two kinds. The difference is **who makes the timing**.

**"Open" style (laptop makes the timing).** An FTDI USB-serial chip and an RS-485 chip. Nothing else. The laptop must produce the break, MAB and bytes on time, over USB, while also running everything else [6]. Enttec's own Open DMX USB (USD 70 [5]) works this way. It has no processor, no frame buffer, no isolation, and no adjustable timing [6]. The CAD ~21 Amazon cables are clones of this design [13], [14].

- QLC+ documents that Open DMX clones "might flicker at 44Hz" on Windows and suggests lowering the rate [8].
- An xLights user saw random flashes and wrong colours with the cheapest FT232R dongles, while the same dongle worked in QLC+ [9].
- A QLC+ forum user found an FTDI RS-485 cable smooth at 30 Hz, but a reply warned about no isolation, timing that depends on CPU load, and counterfeit FTDI chips [10].
- On macOS, QLC+ talks to FTDI devices directly. Do **not** install FTDI's VCP driver; it interferes [8].

**"Pro" style (a chip in the box makes the timing).** The laptop sends whole frames over USB. A microcontroller in the interface outputs them with steady timing. Enttec DMX USB Pro: internal frame buffer, adjustable 1–40 fps, 1500 V isolation, about CAD 229 [7], [13]. DMXking ultraDMX MAX: microprocessor timing, "zero lost frames", adjustable transmit timing for fussy fixtures, USD 110 [11]. It speaks the Enttec Pro protocol, so most software supports it [11]. The older ultraDMX Micro no longer shows on the dealer's USB-DMX page; the MAX is what they sell [12].

**Our takeaway.** The cheap cable is a good way to test the rig on day one. It is not what we build the show on. *(our judgement from [2], [6], [8]–[10])*

---

## 4. DIY: ESP32 + RS-485 transceiver

**The idea.** An ESP32 (a USD 7.50–15 microcontroller board with Wi-Fi [19], [20]) does what the "Pro" boxes do. It receives frames from the laptop and makes the DMX timing in hardware. That gives Pro-style reliability at clone prices *(our judgement)*.

**Software.** The `esp_dmx` library sends and receives DMX512-A and RDM on ESP32. It works in Arduino (core 2.0.3+) and ESP-IDF [15]. Break and MAB lengths are settable; the README example uses a 180 µs break and 20 µs MAB, above the minimums [15]. It needs three pins: TX, RX, and a direction-enable pin [15].

**Transceiver choice.**

| Part | Price | Isolated | Notes |
|---|---|---|---|
| **M5Stack Unit DMX** (CA-IS3092W) | **USD 6.95** [16] | **Yes, 5 kVrms** [16] | XLR-3 female, switchable 120 Ω terminator, 5 V over a 4-pin Grove-style plug [16], [17]. M5Stack's library is built on `esp_dmx` [18]. |
| MAX485 module | USD 1.09 [21]; CAD ~11 for 5 [22] | No | A **5 V** part [21]. Some modules have a 120 Ω resistor soldered on already [21] — remove it unless the module is at the end of the line. |

**Pair the Unit DMX with** an M5Stack AtomS3 Lite (ESP32-S3, USD 7.50, has the matching 4-pin port) [19]. Any ESP32 works; the official ESP32-S3 DevKitC is USD 15 at DigiKey but was out of stock on 2026-09-24 [20].

**Unknown to check on the bench:** M5Stack's docs list only 5 V, GND, RX and TX on the Unit DMX plug — no direction pin [17]. How the board switches between send and receive is **unverified**. For our use (send only) it may not matter.

**Why isolation.** ANSI E1.11 says DMX devices should be electrically isolated from each other [15]. Without isolation, the laptop's USB ground is wired through the DMX cable shield to the chassis of mains-powered fixtures. A fault or ground difference can then damage the transceiver or the laptop port [10]. Enttec charges extra for isolation on its Pro for this reason [6], [7].

---

## 5. Network DMX: Art-Net and sACN

Both put DMX universes inside ordinary network packets (UDP, a "fire and forget" message). A **node** is a box that receives them and outputs real DMX.

- **Art-Net**: by Artistic Licence, royalty-free, UDP port 6454, up to 32 768 universes in Art-Net 3/4 [26].
- **sACN** (ANSI E1.31, "streaming ACN"): carries DMX512 data over IP [28]. It uses multicast addresses `239.255.0.<universe>` on port 5568, and has a **priority** field from 0 to 200 so two sources can share a universe without fighting [27].

**Cheap nodes.** Commercial single-universe nodes start around USD 240 (DMXking eDMX1 MAX) [29]. DMXking's nodes speak sACN, Art-Net 4, RDM and USB DMX [30]. The DIY ESP32 node in §4 *is* a node once its firmware listens for sACN, at about USD 15. For LED strips, WLED already is a free sACN/Art-Net node (§6).

**Why go network at all.** It is the scaling path. One laptop can drive many universes, many nodes, and LED strips all with the same packets. The QLC+ forum user in [10] made the same point about growing past USB. **Caveat:** we have not measured sACN over Wi-Fi at a venue. Test it wired (Ethernet or USB) if Wi-Fi drops frames *(our judgement)*.

---

## 6. Addressable LED strips (WS2812B)

**What they are.** Each LED has its own tiny chip. You send colour data down one wire; each LED keeps the first 24 bits (8 per colour) and passes the rest on [32].

**Timing.** 800 kbit/s; each bit is 1.25 µs; a gap of 50 µs or more means "show it" [32]. So each LED takes 30 µs to update. 300 LEDs take about 9 ms, which allows roughly 100+ updates a second *(our arithmetic from [32])*. The LEDs' own PWM is only about 400 Hz, which can flicker on camera [33].

**Power.** Up to 60 mA per LED at full white; budget 20 mA per LED for typical use [34]. BTF-Lighting rates its 60 LED/m strip at 11 W per metre, so a 5 m strip is about 55 W, or 11 A at 5 V [36]. A 5 V 10 A supply is about CAD 31 [38]: cap brightness in software so it is not overloaded *(our judgement)*. Put a 500–1000 µF capacitor across the strip's power input [34].

**Logic level.** The strip needs a data signal of at least 70% of its supply, i.e. 3.5 V on 5 V [32], [34]. The ESP32 outputs 3.3 V. Use a 74AHCT125 level shifter (USD 1.50) [35].

**Prices.** BTF-Lighting WS2812B, 1 m / 60 LEDs: USD 7.99 [36]. 5 m / 300 LEDs: about CAD 20 on Amazon [37].

### One abstraction for both

The trick: **treat an LED strip as just another fixture.** WLED (free ESP32 firmware) receives sACN or Art-Net and maps 3 channels per LED, up to 170 LEDs per universe [31]. So a 60-LED strip is "a fixture with 180 channels".

The software then has four layers *(our judgement — this is the design, not a source's)*:

1. **Show engine.** Audio features → looks, in abstract words: "group A intensity 80%, colour warm red, strobe on the beat".
2. **Patch.** A list of fixture instances: *profile + mode + universe + start address*. Profiles come from Open Fixture Library JSON (§7). The patch converts abstract words into channel numbers. An LPC1818 gets RGB on ch 2–4 and ch 9 held at 0; a strip pixel gets RGB on its 3 channels.
3. **Universe buffers.** Arrays of 512 bytes, one per universe.
4. **Output drivers.** Each buffer goes out one way: sACN to the ESP32 DMX node, sACN to WLED, sACN to a commercial node, or USB serial to an Enttec-Pro-compatible box.

**Rescaling to a new rig** = a new patch file. The engine and drivers do not change.

---

## 7. Fixture description formats

**Why they matter.** Every fixture model puts different functions on different channels (compare the LPC1818's 7- and 11-ch maps above [49]). To "rescale to any rig", the software must read those layouts from files, not hard-code them.

- **Open Fixture Library (OFL).** A free, MIT-licensed library of fixture definitions in JSON [39]. Each file lists `availableChannels`, `modes` (which channels, in what order) and `capabilities` (what each value range does) [40]. It exports to other formats including QLC+, DMXControl, GDTF and grandMA2 [40]. It was started because fixture files for one program could not be reused in another [39]. **Use this as our internal format.**
- **GDTF** (General Device Type Format, DIN SPEC 15800:2021). A zip holding an XML description plus 3D models. It covers DMX modes, geometry and physical properties. Backed by Vectorworks, MA Lighting and Robe; now run by the VPLT association; a public "GDTF Share" database exists [42]. It is richer than we need; OFL can export to it [40].

---

## 8. Open-source software

| Tool | What it is | Use for us | Source |
|---|---|---|---|
| **QLC+** | Free lighting desk for Windows, macOS, Linux. Outputs DMX USB, Art-Net, sACN, OSC, MIDI. Has audio triggers. | Day-1 rig test; a reference to compare our output against. | [44], [8], [27] |
| **OLA** (Open Lighting Architecture) | Lighting framework for Linux/macOS (Windows mostly unsupported). Art-Net, sACN, Enttec Pro, DMXking, pixel strips. C++ and Python APIs. | Possible back-end for our output drivers on Linux/macOS. | [43] |
| **`sacn`** (Python) | Send/receive sACN. MIT. `pip install sacn`. Default 30 fps. Marked "inactive" but stable. | Our first sACN output driver: about five lines of code. | [45] |
| **`stupidArtnet`** (Python) | Minimal Art-Net send/receive. MIT. Threaded sending at 30 Hz. | Art-Net output driver if a node needs it. | [47] |
| **`DMXEnttecPro`** (Python) | Talks the Enttec Pro protocol over serial. GPL-3.0. Only needs `pyserial`. Rates 1–40 Hz. | Driver for an ultraDMX MAX or Enttec Pro. | [46] |
| **`esp_dmx`** (C/C++) | ESP32 DMX/RDM driver. | Firmware for the DIY node. | [15] |
| **WLED** | ESP32 LED firmware that accepts sACN, Art-Net and DDP. | LED-strip output, no firmware of our own. | [31] |

---

## 9. Recommended first test setup

**Session 1 — learn the rig (no code).**

Laptop → FTDI USB-DMX cable → fixture 1 → … → last blinder → 120 Ω terminator.

1. Open QLC+. Patch 8 LPC1818s at 1, 11, … 71 and 4 blinders at 81, 89, 97, 105.
2. Move one channel at a time. Write down what each channel does on each fixture.
3. Confirm the LPC1818 version and mode (see §1).
4. If the cable flickers, lower QLC+'s output rate [8]. The goal today is the channel map, not a clean show.

**Session 2 — the real path.**

Laptop (Python, `sacn`) → Wi-Fi or Ethernet → **ESP32 + Unit DMX** (`esp_dmx`, listening for sACN) → fixtures → terminator.
Same laptop → sACN → **ESP32 + WLED** → WS2812B strip.

Pass test: the fixtures and the strip follow the same beat with no visible flicker, at a steady 30–44 Hz. *(our judgement)*

### Parts list

| # | Part | Price | Source |
|---|---|---|---|
| 1 | FTDI USB → DMX cable (3-pin XLR) | CAD 22.29 | [14] |
| 2 | 3-pin DMX 120 Ω terminator, 2-pack | CAD 8.46 | [23] |
| 3 | 3-pin DMX cable, 25 ft (skip if the venue lends one) | CAD 24.00 | [24] |
| 4 | M5Stack AtomS3 Lite (ESP32-S3) | USD 7.50 | [19] |
| 5 | M5Stack Unit DMX (isolated, XLR-3) | USD 6.95 | [16] |
| 6 | ESP32 dev boards, 3-pack (for WLED + spares) | CAD 24.00 | [25] |
| 7 | WS2812B strip, 5 m, 60 LED/m | CAD 19.76 | [37] |
| 8 | 5 V 10 A power supply | CAD 31.06 | [38] |
| 9 | 74AHCT125 level shifter | USD 1.50 | [35] |
| 10 | 1000 µF 6.3 V+ capacitor | a few dollars (unverified) | value from [34] |
| — | QLC+, `sacn`, `esp_dmx`, WLED | free | [44], [45], [15], [31] |
| opt. | DMXking ultraDMX MAX (known-good fallback) | USD 110 | [11] |

**Total without the optional box: about CAD 130 + USD 16 plus shipping.** The DMX-only part (items 1, 2, 4, 5) is about CAD 31 + USD 14.45. *(our arithmetic)*

---

## 10. Risks

| # | Risk | What to do | Source |
|---|---|---|---|
| 1 | **LPC1818 address overlap.** Upgraded version in 11-ch mode at 10-channel spacing: each fixture's ch 11 collides with the next one's master dimmer. | Confirm version and mode (display `A001` / `d001`) before writing any profile. Readdress if needed. | [49] |
| 2 | **LPC1818 ignores us.** Ch 9 outside 0–50 runs built-in programs. | Pin ch 9 to 0 in the profile. | [49] |
| 3 | **Blinder model unknown.** Channel map unverified. | Venue photo of the label; map it by hand in Session 1. | [52] |
| 4 | **Cheap FTDI cable flicker.** The laptop makes the timing. | Diagnostic only; lower the rate; move to the ESP32 node. | [6], [8], [9], [10] |
| 5 | **No isolation.** Ground faults via the cable shield can kill a USB port or transceiver. | Use the isolated Unit DMX (5 kVrms). Keep bare MAX485s on the bench. | [6], [15], [16] |
| 6 | **Missing or doubled termination.** Flicker at the end of the line. | One terminator, at the last fixture only. Check MAX485 modules for an on-board 120 Ω. | [3], [4], [21] |
| 7 | **Voltage mismatch.** 3.3 V ESP32 vs 5 V LED data and 5 V MAX485 modules. | 74AHCT125 for the strip; the Unit DMX for DMX. | [21], [32], [34], [35] |
| 8 | **LED power.** A 5 m strip can draw ~11 A at full white. | 10 A supply, brightness cap, capacitor, feed power at both ends for long runs. | [34], [36] |
| 9 | **Fussy fixtures.** Some cheap fixtures dislike fast or short packets. | Stay at 30–44 Hz and full-length frames; the ultraDMX MAX has timing adjustment if needed. | [2], [11] |
| 10 | **Wi-Fi jitter for sACN** (untested). | Test wired first at the venue. | (our judgement) |
| 11 | **Wrong cable.** Mic cable is not DMX cable. | Use 120 Ω DMX cable. | [1] |
| 12 | **Unit DMX direction pin** not documented. | Bench test before the venue. | [17] |

---

## References

[1] Wikipedia, "DMX512." [Online]. Available: https://en.wikipedia.org/wiki/DMX512 (accessed Sep. 24, 2026).

[2] Y-Link, "DMX refresh rate explained (DMX512 timing and FPS)." [Online]. Available: https://www.y-link.no/en/guides/dmx-timing-refresh-rate (accessed Sep. 24, 2026).

[3] American Society of Theatre Consultants, "Why terminate DMX cables?" [Online]. Available: https://theatreconsultants.org/why-terminate-dmx-cables/ (accessed Sep. 24, 2026).

[4] Y-Link, "DMX termination: do you need a terminator?" [Online]. Available: https://www.y-link.no/en/blog/dmx-termination (accessed Sep. 24, 2026).

[5] ENTTEC, "Open DMX USB." [Online]. Available: https://www.enttec.com/product/dmx-usb-interfaces/open-dmx-usb/ (accessed Sep. 24, 2026).

[6] ENTTEC Support, "USB>DMX: compare ENTTEC's DMX USB devices." [Online]. Available: https://support.enttec.com/support/solutions/articles/101000396080-usb-dmx-compare-enttec-s-dmx-usb-devices (accessed Sep. 24, 2026).

[7] ENTTEC, "DMX USB PRO." [Online]. Available: https://www.enttec.com/product/dmx-usb-interfaces/dmx-usb-pro-professional-1u-usb-to-dmx512-converter/ (accessed Sep. 24, 2026).

[8] QLC+ Documentation, "DMX USB — basics." [Online]. Available: https://docs.qlcplus.org/v4/plugins/dmx-usb (accessed Sep. 24, 2026).

[9] xLights, "FTDI USB DMX adapter: flickering lights," GitHub issue #3484. [Online]. Available: https://github.com/xLightsSequencer/xLights/issues/3484 (accessed Sep. 24, 2026).

[10] Q Light Controller+ forum, "Cheap USB interface: uDMX vs. FTDI RS485 cable." [Online]. Available: http://www.qlcplus.org/forum/viewtopic.php?t=13379 (accessed Sep. 24, 2026).

[11] DMX Pro Sales, "DMXking UltraDMX MAX — USB-DMX adapter." [Online]. Available: https://dmxprosales.com/products/dmxking-ultradmx-max (accessed Sep. 24, 2026).

[12] DMX Pro Sales, "USB DMX" collection. [Online]. Available: https://dmxprosales.com/collections/usb-dmx (accessed Sep. 24, 2026).

[13] Amazon.com, search results for "enttec dmx usb pro" (prices shown in CAD for a Canadian address). [Online]. Available: https://www.amazon.com/enttec-dmx-usb-pro/s?k=enttec+dmx+usb+pro (accessed Sep. 24, 2026).

[14] Amazon.com, "USB to DMX512 interface cable FT232RNL DMX controller adapter 3 pin XLR." [Online]. Available: https://www.amazon.com/dp/B07D6LCF35 (accessed Sep. 24, 2026; CAD 22.29).

[15] someweisguy, "esp_dmx," GitHub repository. [Online]. Available: https://github.com/someweisguy/esp_dmx (accessed Sep. 24, 2026).

[16] M5Stack, "DMX Unit with isolated RS-485 transceiver (CA-IS3092W)." [Online]. Available: https://shop.m5stack.com/products/dmx-unit-with-isolated-rs485-transceiver (accessed Sep. 24, 2026).

[17] M5Stack Docs, "Unit DMX." [Online]. Available: https://docs.m5stack.com/en/unit/Unit-DMX (accessed Sep. 24, 2026).

[18] M5Stack, "M5Unit-DMX512," GitHub repository. [Online]. Available: https://github.com/m5stack/M5Unit-DMX512 (accessed Sep. 24, 2026).

[19] M5Stack, "AtomS3 Lite ESP32S3 dev kit." [Online]. Available: https://shop.m5stack.com/products/atoms3-lite-esp32s3-dev-kit (accessed Sep. 24, 2026).

[20] DigiKey, "ESP32-S3-DEVKITC-1-N8R8." [Online]. Available: https://www.digikey.com/en/products/detail/espressif-systems/ESP32-S3-DEVKITC-1-N8R8/15295894 (accessed Sep. 24, 2026).

[21] ProtoSupplies, "MAX485 TTL to RS-485 interface module." [Online]. Available: https://protosupplies.com/product/max485-ttl-to-rs-485-interface-module/ (accessed Sep. 24, 2026).

[22] Amazon.com, search results for "max485 module" (CAD). [Online]. Available: https://www.amazon.com/s?k=max485+module (accessed Sep. 24, 2026).

[23] Amazon.com, search results for "dmx terminator 3 pin" (CAD). [Online]. Available: https://www.amazon.com/s?k=dmx+terminator+3+pin (accessed Sep. 24, 2026).

[24] Amazon.com, search results for "dmx cable 3 pin 25ft" (CAD). [Online]. Available: https://www.amazon.com/s?k=dmx+cable+3+pin+25ft (accessed Sep. 24, 2026).

[25] Amazon.com, search results for "esp32 devkit" (CAD). [Online]. Available: https://www.amazon.com/s?k=esp32+devkit (accessed Sep. 24, 2026).

[26] Wikipedia, "Art-Net." [Online]. Available: https://en.wikipedia.org/wiki/Art-Net (accessed Sep. 24, 2026).

[27] QLC+ Documentation, "E1.31 (sACN) — basics." [Online]. Available: https://docs.qlcplus.org/v4/plugins/e1-31-sacn (accessed Sep. 24, 2026).

[28] Wikipedia, "Architecture for Control Networks." [Online]. Available: https://en.wikipedia.org/wiki/Architecture_for_Control_Networks (accessed Sep. 24, 2026).

[29] DMX Pro Sales, "DMXking eDMX1 MAX — ArtNet/sACN to DMX controller." [Online]. Available: https://dmxprosales.com/products/dmxking-edmx1-max (accessed Sep. 24, 2026).

[30] DMXking, "eDMX1 PRO" / ArtNet-sACN nodes. [Online]. Available: https://dmxking.com/artnetsacn/edmx1-pro (accessed Sep. 24, 2026).

[31] WLED Knowledge Base, "E1.31 (DMX) / Art-Net." [Online]. Available: https://kno.wled.ge/interfaces/e1.31-dmx/ (accessed Sep. 24, 2026).

[32] Worldsemi, "WS2812B intelligent control LED integrated light source," datasheet (Adafruit mirror). [Online]. Available: https://cdn-shop.adafruit.com/datasheets/WS2812B.pdf (accessed Sep. 24, 2026).

[33] Advatek Lighting, "WS2812B — pixel protocol." [Online]. Available: https://www.advateklighting.com/pixel-protocols/ws2812b (accessed Sep. 24, 2026).

[34] Adafruit, "Adafruit NeoPixel Überguide — powering NeoPixels." [Online]. Available: https://learn.adafruit.com/adafruit-neopixel-uberguide/powering-neopixels (accessed Sep. 24, 2026).

[35] Adafruit, "74AHCT125 — quad level-shifter (3V to 5V)," product 1787. [Online]. Available: https://www.adafruit.com/product/1787 (accessed Sep. 24, 2026).

[36] BTF-Lighting, "WS2812B RGB LED strip DC5V." [Online]. Available: https://www.btf-lighting.com/products/ws2812b-led-pixel-strip-30-60-74-96-100-144-pixels-leds-m (accessed Sep. 24, 2026).

[37] Amazon.com, search results for "ws2812b 5m 60" (CAD). [Online]. Available: https://www.amazon.com/s?k=ws2812b+5m+60 (accessed Sep. 24, 2026).

[38] Amazon.com, search results for "5v 10a power supply" (CAD). [Online]. Available: https://www.amazon.com/s?k=5v+10a+power+supply (accessed Sep. 24, 2026).

[39] Open Fixture Library, "About." [Online]. Available: https://open-fixture-library.org/about (accessed Sep. 24, 2026).

[40] Open Lighting Project, "open-fixture-library," GitHub repository. [Online]. Available: https://github.com/OpenLightingProject/open-fixture-library (accessed Sep. 24, 2026).

[41] Open Fixture Library, search for "betopper." [Online]. Available: https://open-fixture-library.org/search?q=betopper (accessed Sep. 24, 2026; no results).

[42] GDTF, "General Device Type Format." [Online]. Available: https://gdtf.eu/ (accessed Sep. 24, 2026).

[43] Open Lighting Project, "Open Lighting Architecture (OLA)." [Online]. Available: https://www.openlighting.org/ola/ (accessed Sep. 24, 2026).

[44] QLC+, "Q Light Controller+." [Online]. Available: https://www.qlcplus.org/ (accessed Sep. 24, 2026).

[45] Hundemeier, "sacn," GitHub repository. [Online]. Available: https://github.com/Hundemeier/sacn (accessed Sep. 24, 2026).

[46] SavinaRoja, "DMXEnttecPro," GitHub repository. [Online]. Available: https://github.com/SavinaRoja/DMXEnttecPro (accessed Sep. 24, 2026).

[47] cpvalente, "stupidArtnet," GitHub repository. [Online]. Available: https://github.com/cpvalente/stupidArtnet (accessed Sep. 24, 2026).

[48] Betopper, "Betopper LPC1818 upgraded 18×18W Lime Amber UV + RGB LED PAR light." [Online]. Available: https://betopperdj.com/products/betopper-18x18w-rgbw-amber-uv-6-in-1-led-par-light (accessed Sep. 24, 2026).

[49] Betopper, "User manual 18x18W RGB+Lime+Amber+UV 6-in-1, model LPC1818," rev. 1.00 (file 406-18110-003, v6.0). [Online]. Available: https://cdn.shopify.com/s/files/1/0084/5230/9047/files/406-18110-003_LPC1818_BETOPPER_6_0.pdf?v=1752802327 (accessed Sep. 24, 2026).

[50] Betopper, "Real feedback from users of the LPC1818 RGBWA+UV 6-in-1 PAR light." [Online]. Available: https://betopperdj.com/blogs/news/real-feedback-from-users-of-the-lpc1818-rgbwa-uv-6-in-1-par-light (accessed Sep. 24, 2026).

[51] The Lighting Controller forum, "Betopper — LPC1818 (11ch)." [Online]. Available: https://forum.thelightingcontroller.com/viewtopic.php?t=8586 (accessed Sep. 24, 2026).

[52] SHEHDS, "SHEHDS Blinder 2 Eyes 200W LED COB cool & warm white light." [Online]. Available: https://shehds.com/products/shehds-2eyes-200w-led-cob-blinder-cool-white-warm-white-lighting-p0217 (accessed Sep. 24, 2026).
