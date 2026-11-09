# Rhythm, Tempo and Transient Detection — research

**Author:** Remsha Akbar Hussain · **Module:** M3 Rhythm, Tempo and Transient Detection
**Source:** Google Drive › Deliverables › "Rhythm, Tempo, and Transient Detection" (pulled into the repo 2026-11-09; the Drive doc may have moved on since — the "Peak picking and thresholding" and "Band split" sections at the end were still empty headings).
Content is the author's own; only formatting was changed for markdown. See [MODULE.md](../MODULE.md#research-vs-the-prototype) for how it lines up with the prototype.

---

**Purpose:** the module turns a stream of spectral frames into timing information: when hits occur, how fast the song is, and when the next beat will land.

**Inputs:** audio frames from the signal processing module.

**Outputs:**
- Onset events
- Tempo
- Predicted beat times
- Potentially: a confidence indicator for songs whose transients are harder to detect

## Software libraries

- **NumPy / SciPy** — Python's core library for working with arrays of numbers fast. Can be used for cutting audio into frames, running the FFT, computing spectral flux, the median threshold, and autocorrelation. SciPy adds signal-processing tools on top, like filters and windowing functions.
- **librosa** — Python library for analysing music. Onset detection, tempo estimation and beat tracking built in, plus plotting. Helps with prototyping: see what the signals look like, generate "click tracks" to hear where it thinks the beats are, and act as a baseline to compare our own version against. Works on whole files, so it isn't built for live use.
- **aubio** — audio analysis library written in C (fast), with a Python interface. Designed for real time: processes audio in small chunks as it arrives. Use it to check that our streaming version behaves sensibly, and as a backup if our own Python code is too slow.
- **madmom** — accuracy benchmark. Pretrained neural network models for onset and beat detection. Among the most accurate tools available, but too heavy for a live system. Use offline to show how close our implementation is.
- **BTrack** — reference open-source real-time beat tracker. Implements the "cumulative score" beat prediction method.
- **mir_eval** — measures accuracy with the standard music-research metrics. Give it detected onsets/beats and the human-labelled correct ones; it returns scores like the F-measure (how many beats were within 70 ms of the right time).
- **sounddevice and soundfile** — audio in and out. soundfile reads/writes WAV etc. (load test songs, save click tracks). sounddevice captures live audio from a mic or line-in for real-time testing.

| Job | Tool |
|---|---|
| Load songs, save tracks | soundfile |
| Explore and get baseline results | librosa |
| Build the module | NumPy, SciPy |
| Score accuracy | mir_eval |
| Compare against accurate results | madmom (offline), BTrack |
| Check real-time behaviour, fallback | aubio |
| Live audio input | sounddevice |

## Process / components

1. **Processing** — gets the raw audio ready to analyse. The audio is cut into short slices, each slice is smoothed at its edges, and an FFT splits it into its frequencies. Taking the log then makes quiet sounds easier to see next to loud ones. The output is a picture of which frequencies are present in each slice.
2. **Onset detection function** — turns each slice into a single number that says "how much did the sound just change?" Using spectral flux, it adds up how much each frequency got louder since the previous slice. The result is a line over time that stays low during steady sound and spikes whenever a new hit or note starts.
3. **Peak picking and thresholding** — decides which spikes are real hits. A spike only counts if it rises well above what's normal right now (the moving median), is the highest point nearby, and isn't too close to the previous hit. The threshold adjusts as the song gets louder or quieter, so hits are caught in both soft and loud sections.
4. **Band split for drum types** — works out which drum was hit by running detection separately on different frequency ranges. A spike in the low range (60–250 Hz) is probably a kick; a spike in the high range (2 kHz and up) is probably a snare crack or hi-hat. That way the lights can react differently to each drum.
5. **Tempo estimation** — finds how fast the song is. Using autocorrelation, it looks at the last several seconds of hits, finds the time gap at which the pattern repeats best, and converts that gap to BPM (e.g. 0.5 s gap = 120 BPM). Also reports a confidence value: high when the beat is clear, low when it isn't.
6. **Beat tracking and prediction** — works out where beats fall and predicts the next one. Next beat = last beat + beat period, nudged slightly whenever a real hit lands close to where a beat was expected. Because the prediction comes before the beat, the lighting command can be sent early so the lights change exactly on the beat instead of slightly after.
7. **Slow songs and ballads** — handles music where the earlier steps struggle. Ballads have soft, gradual notes and few clear hits, so tempo estimates become unreliable. When confidence is low, the module tells the lighting system to stop following beats and use slow, mood-driven transitions instead. Optional extras like chord-change detection could add colour shifts on chord changes.

## Onset detection function — design options

| Design option | How it works | Best for | Cons |
|---|---|---|---|
| Energy / amplitude | Rise in overall loudness | Isolated drums | Misses hits under loud instruments |
| High Frequency Content (HFC) | Energy weighted toward high frequencies | Sharp percussive hits | Weak on bass drums and soft notes |
| Spectral flux | How quickly the power spectrum changes over time: compare one short-term frame's spectrum against the previous frame's | Most popular music | Soft, slow onsets |
| SuperFlux | Spectral flux with a max filter that ignores vibrato | Vocals, strings | One more parameter to tune |
| Phase deviation | Unpredictable phase change at note starts | Soft pitched onsets | Noisy on percussion |

## Peak picking and thresholding

*(empty in the source doc)*

## Band split for drum types

*(empty in the source doc)*
