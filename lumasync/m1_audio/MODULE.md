# Module 1 — Signal Processing of Audio

**Owner:** Youtso · **Folder:** `lumasync/m1_audio/` · **Decision records:** 200–299

## The question this module answers

**What is in the sound right now?** Turn raw audio from a mic or a line input into clean,
comparable numbers that every other module can trust.

## Inputs and outputs (contract terms)

- **In:** audio from the laptop mic, or a clean line from the DJ mixer through a USB audio
  interface. Mono, 44.1 kHz, in blocks of 1024 samples (about 23 ms each), from `contract.py`.
- **Out:** one `AudioFrame` per block:
  - `samples` (float32, −1…1), `t` (seconds since start), `sample_rate`;
  - `rms`: loudness, 0–1;
  - `bands`: energy per band, each normalised 0–1. Keys: `sub`, `bass`, `low_mid`, `mid`,
    `high_mid`, `high`;
  - `spectrum`: the magnitude spectrum from the **FFT** (Fast Fourier Transform: splits a block of
    sound into how much energy sits at each frequency);
  - `centroid_hz`: **spectral centroid**, the "centre of mass" of the spectrum. High = bright,
    hissy; low = dark, bassy;
  - `flux`: **spectral flux**, how much the spectrum changed since the last block. Spikes on drum
    hits. Module 3 lives on this.

Read by: module 3 (rhythm) and module 5 (recognition and mood).

## What the prototype does now

A first-draft front end: reads blocks from the default input, computes loudness, the six bands,
centroid and flux. It is a starting point, not a design. See the code for details.

## The core engineering challenge (report-worthy)

**Make the features mean the same thing in a quiet room and a loud club, from a mic or a line.**

- **Mic vs line-in.** The mic hears the crowd and the room's echo; the line hears only the mix.
  How much does that change each feature? This is measurable, and it feeds module 5's mood test.
- **Normalisation.** `bands` must be 0–1. Against what? A fixed maximum clips in a loud room. A
  running maximum (**automatic gain**) adapts, but how fast? Too fast and every quiet break looks
  like a drop. Too slow and the show lags the room.
- **Window size vs delay.** An FFT of N samples at rate fs spans N/fs seconds. 1024 samples is
  23 ms; 2048 gives finer bass detail but 46 ms, which already blows the 45 ms latency budget.
  Overlapping blocks (a smaller **hop**) is one way out, and would be a contract change.
- **Band edges.** Kick and bass sit around 60–250 Hz; snares and hats around 2–4 kHz. Where
  exactly should the six bands split for lighting?
- **Signal chain.** Nyquist (sample at more than twice the highest frequency), the laptop's ADC
  (analog-to-digital converter) vs a USB interface, levels and clipping.

## How to test it alone

- Feed recorded WAV files in place of the live input. Record the **same track** through the mic
  and through line-in, and compare the `AudioFrame` streams side by side.
- Use synthetic signals with known answers: a pure tone (centroid should equal its frequency),
  white noise, a click track (flux should spike on each click).
- Time your processing per block. It must be far under 23 ms.

## Suggested Dec 10 target

`AudioFrame` streams from both mic and line-in, with a short comparison: noise floor, band
stability on a steady passage, flux peaks on drum hits, and processing time per block.

## Research vs the prototype

Research: [research/signal-processing-research.md](research/signal-processing-research.md) (Youtso, Nov 2026).

**Already agrees:**
- 44.1 kHz, Python on the laptop, `.wav` files first then live input: the prototype does the same (`--source file`, then `--source mic`).
- FFT of 2048 samples with a Hann window: the prototype uses a 2048-sample Hann window, sliding 1024 samples per tick (50 % overlap). See [decision 104](../../decisions/104-m1-features-and-agc.md).
- RMS, spectral centroid, spectral flux and band energies are all in `AudioFrame` today.
- Line-in as primary, mic as backup: matches the baseline's input order.

**Open, for the owner to decide (each is a good decision record):**
- **Buffering.** The research recommends a ring buffer over double buffering. The prototype hands blocks through a queue between threads ([decision 101](../../decisions/101-app-threading-model.md)). Is that good enough, or should capture write into a ring buffer? Measure the backlog under load to decide.
- **Window and hop.** 2048 / 1024 gives ~21.5 Hz bins and ~23 ms per tick. Is that the right time-frequency trade-off for beats *and* bass? Test 1024 and 4096 against the same tracks.
- **Roll-off and zero-crossing rate.** Marked optional in the research. M5 (Rohan's research) wants them for mood. Adding them is an optional contract field: a small change, but it goes through the contract process.
- **Sample-rate hand-off to M5.** M5's research asks whether M1 should give it a 22.05 kHz mono stream or let M5 resample. Agree this with Rohan.

## Open decisions for the owner

1. Band edges for the six bands.
2. Normalisation method and its time constant (fixed, running max, percentile).
3. Block size and hop: keep 1024, or propose overlapping blocks (contract change).
4. Window function for the FFT (Hann, Hamming, …) and why.
5. Mic gain handling: in software, or rely on the interface?

## Starting references

- Tzanetakis & Cook, "Musical genre classification of audio signals," *IEEE TSAP*, 2002
  (centroid, rolloff, flux, zero-crossing rate).
- Bello et al., "A tutorial on onset detection in music signals," *IEEE TSAP*, 2005 (spectral flux).
- McFee et al., "librosa," *SciPy*, 2015 (reference implementations to compare against).
- Müller, *Fundamentals of Music Processing*, Springer, 2015 (STFT, windows).
- Audient, "Frequency ranges explained," 2022, and Yamaha, "Microphone basics," 2017 (both in our
  proposal).

Full list: [docs/research/citation-bank.md](../../docs/research/citation-bank.md).
