# Signal Processing Research

**Author:** Tenzin Youtso · **Module:** M1 Signal Processing of Audio
**Source:** Google Drive › Deliverables › "Signal Processing Research" (pulled into the repo 2026-11-09; the Drive doc may have moved on since).
Content is the author's own; only formatting was changed for markdown. See [MODULE.md](../MODULE.md#research-vs-the-prototype) for how it lines up with the prototype.

---

## Decision choices

| Decision | Initial choice | Rationale |
|---|---|---|
| Processor | Laptop running Python | Quick development and easy integration |
| Audio source | .wav files first, then live line-input | Easier testing and debugging |
| Sampling frequency | 44.1 kHz | Standard music sampling rate |
| ADC resolution | 16 bits minimum | Standard in industry baseline for reliable spectral extraction + provides a SQNR of ~96 dB |
| FFT size | 2048 samples | Reasonable initial time-frequency trade-off |

## Audio acquisition and sampling

**Question:** What sampling frequency and input method will provide sufficient information for your algorithms without unnecessary computational overhead?

How continuous audio becomes digital signals:
- Prep signal before sampling since an ADC has finite input range.
- Anti-aliasing filter limits unwanted high-frequency content before sampling.
- f_sampling = 44,100 samples/s → f_nyquist = 22,050 Hz.
- **Sampling: discretize time.** Must take a measurement at regularly spaced instants to sample. Sampled sequence x[n] is its value at sample index n. Sampling interval at 44.1 kHz: T = 1/44,100 ≈ 22.7 µs.
- **Quantization: discretize amplitude.** An ADC can't store infinitely precise voltage, so each measurement is assigned to an available amplitude level. For an N-bit ADC there are 2^N levels. Each quantized level is assigned a digital code.
- How this connects with implementation: for a .wav file the ADC already happened, and the software begins with stored digital samples.

### Microphone vs line-level input

| | Microphone | Line level |
|---|---|---|
| Signal source | Sound waves from speakers/instruments | Electrical signals from a mixer/audio device |
| Noise | Background noise, crowd, room reflections | Generally cleaner audio |
| Delay | Includes acoustic propagation delay | Avoids acoustic propagation delay |
| Applies to | Live bands, acoustic instruments | DJ sets, electronic music |

**What voltage levels do microphones and line outputs typically produce?**
- Line level: 0.3–2 V. Consumer line input level: 0.32 V (−7.8 dBu).
- Microphone: 5–50 mV. Weak electrical signal, between −60 dBV and −40 dBV (0.001–0.01 V).

**What microphone type is appropriate for capturing live music?**
- Condenser: wide frequency response, very sensitive; because of that sensitivity it sometimes picks up unwanted signals from other sources.
- Dynamic: used for live performances and recordings because it handles high sound pressure levels without distortion.
- Ribbon: a very thin metal ribbon between two magnets; used for brass, strings and guitar amplifiers for natural sound and warmth.
- Might be best to use line-level input as the primary input and microphone input as a secondary option.

**How many bits do we need for the ADC? How does bit depth affect the signal entering the FFT?**
- Higher resolution gives more amplitude levels, so quieter components are represented with less quantization noise.
- 16-bit is the industry-standard baseline for reliable spectral feature extraction.
- ~96 dB SQNR keeps quantization noise low enough not to mask important spectral components.

**Anti-aliasing filters**
- A USB audio interface will most likely include anti-aliasing.
- A custom ADC circuit would need an analog input filter designed for it.

## Audio buffering (capturing and processing music continuously)

Buffering = temporarily storing a small amount of audio in memory before it is played, processed or transmitted. A safety reserve that keeps sound smooth and prevents dropouts.

Buffering strategies:
- **Block-based buffering:** collect a block of samples and process them together, instead of one sample at a time.
- **Double buffering:** two storage areas; one fills while the other is processed. Leaves little flexibility if analysis occasionally runs long, and capture must never overwrite data still being analysed. *Not recommended.*
- **Ring / circular buffer:** a fixed-size array treated as circular; the write position wraps to the start. Read and write positions track which data is available.
  - Buffer capacity: how much audio storage is available.
  - Buffer backlog: how much captured audio is waiting to be processed.

## Libraries and APIs

- **python-sounddevice + PortAudio:** capture live audio from microphones, line-in instruments or system audio.
- **librosa:** audio and music signal processing. Reads audio files, spectral analysis (incl. STFT), tempo (BPM) estimation and beat tracking (`librosa.beat`), pitch shifting, time stretching, harmonic-percussive source separation (HPSS).
- **SciPy:** DSP: FIR and IIR filter design, FFT, convolution.

## FFT and short-time Fourier transform (STFT) — parameters to research

- **Window length:** how much audio is analysed per FFT.
- **Hop length:** how far the analysis advances between windows.
- **Window function:** Hann, Hamming, etc., used to reduce spectral leakage.
- **Frequency resolution:** how precisely individual frequency components can be separated.
- **Time resolution:** how quickly changes in the music can be detected.

## Audio feature extraction — to calculate

- RMS energy from time-domain samples.
- Spectral centroid from FFT magnitudes.
- Spectral flux for detecting changes in frequency content.
- Low-, mid- and high-frequency band energy.
- Spectral roll-off and zero-crossing rate (optional).
