# Hardware: DMX from first principles

Everything you need to plug a laptop into real lights, and why each step matters. The full
research with every source is in [research/dmx-path.md](research/dmx-path.md).

## 1. What DMX is

**DMX** (DMX512-A, standard ANSI E1.11-2024) is the cable signal that lighting desks send to
stage lights.

- It is a **one-way broadcast**. The controller talks; the lights only listen. Nothing comes back.
- One cable carries **512 channels**, called one **universe**. Each channel is a number from
  0 to 255.
- The controller sends **all 512 values, again and again**, about 30–44 times per second. One full
  update is a **frame**.
- **Every light hears every value.** Each light just picks out its own few channels and ignores
  the rest.

What one frame looks like on the wire: a **break** (line held low for at least 88 µs: "new frame
starts"), a short **mark after break**, a start byte (0), then up to 512 channel bytes, at
250,000 bits per second. A full frame takes about 23 ms.

The wire is **RS-485**: each bit is sent as the difference between two wires, so noise that hits
both cancels out. Most cheap gear uses 3-pin XLR plugs. Use real DMX cable (120 Ω), not
microphone cable: it looks the same but has the wrong electrical properties.

## 2. Wiring: the daisy chain

Lights are chained one after another. Each light has a DMX **IN** and a DMX **OUT**.

```
laptop ─USB─ [USB-DMX cable] ─▶ light 1 IN   light 1 OUT ─▶ light 2 IN   light 2 OUT ─▶ … ─▶ last light OUT ─▶ [120 Ω terminator]
```

**The terminator** is a small plug with a 120 Ω resistor. It goes in the **last** light's OUT,
and nowhere else. Without it, the signal bounces back off the open end and garbles the data. The
symptom is flicker or random values, usually at the far end of the chain.

## 3. Address and mode: how a light knows its channels

Each light has a small menu with two settings that matter:

- **Mode:** how many channels the light uses and what each one means. For example, a 7-channel
  mode might be: red, green, blue, lime, amber, UV, colour temperature.
- **Start address:** the first channel it listens to. A light in a 10-channel mode at address 11
  uses channels 11–20.

Two lights with the same mode and address do exactly the same thing. That is handy for groups.
Two lights whose channel ranges **overlap** fight each other. That is a bug.

The light must also be in **DMX mode**, not its own auto or sound-active mode.

## 4. Learning a light's channel map

Every model puts different functions on different channels. Before writing a patch file, find out
what each channel does.

```bash
.venv/bin/python tools/dmx_test.py ports                       # find the cable's port
.venv/bin/python tools/dmx_test.py blink                       # all channels full / off, 1 s each
.venv/bin/python tools/dmx_test.py walk --start 1 --count 12   # one channel at a time, 1.5 s each
.venv/bin/python tools/dmx_test.py walk --hold 1=255           # same, with channel 1 (master dimmer) kept up
.venv/bin/python tools/dmx_test.py set 1=255 2=255             # hold chosen values (Ctrl+C to stop)
```

During `walk`, write down what the light does for each channel. Ctrl+C always ends in blackout.

**If nothing moves:**
1. Check the light's menu: DMX mode on, and note its address (for example `A001` or `d001`).
2. Try `--break-mode baud` (a second way to make the break signal).
3. Unplug and replug the cable. Run `ports` again.
4. Some lights need a master dimmer channel up first: add `--hold 1=255`.

The result goes into a **fixture profile** and the rig's **patch file** (Module 2). The format
we plan to follow is Open Fixture Library's JSON. The LPC1818 is not in that library, so we write
its profile ourselves.

## 5. The cable we have, and why it is "dumb"

The **DSD TECH SH-RS09B** is an FTDI USB-to-DMX cable with a 3-pin XLR end (about CAD 22). It has
no processor inside. The **laptop makes the DMX timing** itself, over USB, while also running
everything else. If the laptop is busy, the gaps between frames get uneven, and lights can
flicker. `tools/dmx_test.py` sends 30 frames per second to stay safe. It is not isolated either
(see Safety).

That is fine for tests and for learning the rig. It is not what we build the show on. It has not
been tested on a light yet.

## 6. The later path: ESP32 node + sACN

- An **ESP32** (a microcontroller board, about USD 7.50 for an M5Stack AtomS3 Lite) plus an
  **M5Stack Unit DMX** (USD 6.95, an *isolated* DMX adapter with a built-in terminator switch),
  running the free `esp_dmx` library. The ESP32 makes the timing in hardware, like a USD 110–230
  "pro" interface does.
- The laptop sends **sACN** (ANSI E1.31: DMX inside network packets). The ESP32 turns it into
  real DMX.
- A second ESP32 running **WLED** (free firmware) turns the same packets into WS2812B LED strip
  light: 3 channels per LED, 170 LEDs per universe. An LED strip is then "just another fixture".
- Test sACN **wired first**. Wi-Fi at a venue is untested.
- Known-good fallback if the DIY node stalls: DMXking ultraDMX MAX, USD 110.

## 7. The Resonnce rig

| Lights | Count | Start addresses | Notes |
|---|---|---|---|
| LPC1818 LED PAR (almost certainly Betopper, 18 × 18 W) | 8 | 1, 11, 21 … 71 | 10 apart |
| 200 W blinder (bright white crowd light), model unknown | 4 | 81, 89, 97, 105 | 8 apart, fits an 8-channel mode |

The rig ends at channel 112, well inside one universe. 12 lights is under DMX's limit of 32 per
chain. Rated power is about 2.4 kW: that is the venue's circuits, but worth knowing before an
all-white blinder hit.

**The LPC1818 risk.** There are two versions. The older one has 6/10-channel modes, which fits
the 10-apart addresses. The newer one has **7/11-channel** modes. In 11-channel mode, each light's
channel 11 would land on the next light's channel 1 (master dimmer): the lights would overlap.
On the newer version, the display shows `A001` for 11-channel mode and `d001` for 7-channel.
**We need a photo of one light's display** before writing the profile.

On the newer version, **channel 9 must stay at 0–50**, or the light runs its own built-in
programs and ignores our colours.

**Still to confirm with the venue:** LPC1818 version and mode, the blinder's make and model, 3-pin
or 5-pin DMX, and what drives the chain today.

## 8. Safety

- **Flash rate.** No more than **3 flashes per second** on the final output (WCAG 2.2, the Epilepsy
  Foundation consensus, ITU-R BT.1702-3). Saturated red flashes carry extra risk. The software
  enforces this; nobody turns it off for a demo.
- **Isolation.** Without it, the laptop's USB ground is wired through the cable shield to
  mains-powered lights. A fault can kill a USB port. Use the isolated Unit DMX for anything
  beyond bench tests.
- **LED strips.** A 5 m strip can draw about 11 A at full white. Use a 5 V 10 A supply, cap
  brightness in software, and put a 1000 µF capacitor across the power input. The ESP32 outputs
  3.3 V data but the strip wants at least 3.5 V, so use a 74AHCT125 level shifter.
- **DJ gear at a live gig.** Only listen to its data. Never send commands to someone else's
  players.

## 9. Parts list (from the research, prices seen 2026-09-24)

| Part | Price | Status |
|---|---|---|
| FTDI USB→DMX cable, 3-pin | CAD 22.29 | Bought; not yet tested on a light |
| 3-pin 120 Ω DMX terminator, 2-pack | CAD 8.46 | |
| DMX cable, 25 ft (skip if the venue lends) | CAD 24.00 | |
| M5Stack AtomS3 Lite (ESP32-S3) | USD 7.50 | |
| M5Stack Unit DMX (isolated) | USD 6.95 | |
| ESP32 dev boards, 3-pack (WLED + spares) | CAD 24.00 | |
| WS2812B strip, 5 m, 60 LED/m | CAD 19.76 | |
| 5 V 10 A power supply | CAD 31.06 | |
| 74AHCT125 level shifter | USD 1.50 | |
| 1000 µF capacitor | a few dollars | |
| USB audio interface with line-in (e.g. Behringer UCA202) | about US$16 | |
| QLC+, Python `sacn`, `esp_dmx`, WLED | free | |

About CAD 130 + USD 16 + shipping for the DMX and LED parts. The DMX-only part is about
CAD 31 + USD 14.45. Prices move; treat them as "about". Who buys what is still open.
