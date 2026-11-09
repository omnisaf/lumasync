# Module 5 — Machine Learning: Mood and Crowd-Energy Estimation

**Owner:** Rohan · **Folder:** `lumasync/m5_recognition/` · **Decision records:** 600–699

**Name under review.** Song recognition lives here in the prototype. The team may rename this
module "Machine Learning: Music Recognition and Mood Estimation". See
[decisions/003](../../decisions/003-five-modules.md).

## The question this module answers

**What kind of music is this?** Which song from our library is playing (if any), and how does it
feel? It is one of the layers on top of the base show. If it says nothing, the show still runs.

## Inputs and outputs (contract terms)

- **In:** `AudioFrame` from module 1 (samples, spectrum, features). Can also compute its own
  features from the samples. The song library (`SongPreset.audio_file`) for fingerprints.
- **Out:** `MusicContext`, a few times per second:
  - `song_id`, `song_confidence` (0–1): which library song, or `None` if unknown;
  - `valence` (−1…1, sad ↔ happy) and `arousal` (−1…1, calm ↔ intense), or `None` when there is
    no estimate. This is the **valence–arousal** model of emotion (Russell 1980).

Module 4 decides what the lights do with it (for example, colour).

## What the prototype does now

Song recognition by **audio fingerprinting**: each library song gets a compact "signature" built
from peaks in its spectrogram, and live audio is matched against it (the idea behind Shazam).
Mood is at most a placeholder so far; the real model is this module's work. See the code for details.

## The core engineering challenge (report-worthy)

**Datasets are clean studio audio. We hear a noisy mic in a loud room.**

- **Mood.** Estimate valence and arousal in real time from degraded audio, and measure how much
  accuracy drops from clean → line-in → mic. Mood changes slowly, so an update every 0.5–1 s is
  fine; it runs on the slow path and never delays a flash.
- **Mood is not promised in the baseline.** The job is to build it and **test whether it earns a
  place**, three ways: live from the mic, live from a clean line, and ahead of time on a full
  track (for example when a DJ loads it). If it works live on the mic, it joins the baseline.
  If not, it stays a layer for better inputs. Either result is a valid finding.
- **Recognition.** How many seconds until a song is identified? How often is it wrong? A wrong
  song is worse than none (wrong colours), so confidence must be honest. DJs also play tracks
  faster or slower than the original; test whether fingerprints survive a tempo or pitch change.
- **Add-on:** crowd energy from a camera (how much the room is moving). Same layer idea, very
  different input. No sources in our citation bank yet.

## How to test it alone

- Mood: train on public labelled datasets. **DEAM** (~1,800 songs, valence–arousal every half
  second) and **PMEmo** (pop, a second test set). Features with librosa; no need to wait for M1.
- Make "mic" audio yourself: play dataset songs through a speaker and record with a laptop, or add
  noise and reverb in code.
- Recognition: build a small library, play its songs through a speaker in a noisy room, at the
  original tempo and at ±5–8%.
- Measure: RMSE and R² on a held-out DEAM split; the same model on PMEmo; the accuracy drop clean →
  line → mic; recognition accuracy and time-to-identify; time per update on a laptop.

## Suggested path for mood

1. Audio features (spectral, rhythm, loudness) → a small regression model. Hsiao et al. did mood →
   lighting with an SVM on four mood quadrants; match or beat that with continuous values.
2. Check which features matter (Panda et al. propose features built for mood).
3. Only then try a small neural network, if the simple model is not enough.

## Suggested Dec 10 target

A mood model trained on DEAM, with a results table for clean audio vs recorded mic audio. A
recognition test on a small library: accuracy and time-to-identify, mic vs line-in.

## Open decisions for the owner

1. Module name and scope (team decision, `decisions/007`).
2. Mood model: regression on features, SVM on quadrants, or a small network.
3. Fingerprinting: our own (Wang-style peaks) vs Chromaprint; how to handle tempo changes.
4. Confidence thresholds: when to report a song, and when to say `None`.
5. Whether the camera add-on is in scope this year.

## Starting references

- Russell, "A circumplex model of affect," *J. Pers. Soc. Psychol.*, 1980.
- Aljanaki, Yang & Soleymani, DEAM, *PLOS ONE*, 2017 · Zhang et al., PMEmo, *ICMR*, 2018.
- Yang & Chen, "Machine recognition of music emotion: A review," *ACM TIST*, 2012.
- Hsiao, Chen & Lee, "Stage lighting control based on music emotions," *Inf. Sci.*, 2017.
- Panda, Malheiro & Paiva, "Novel audio features for music emotion recognition," *IEEE TAFFC*, 2020.
- Wang, "An industrial-strength audio search algorithm," *ISMIR*, 2003 · Haitsma & Kalker, *ISMIR*, 2002 · Chromaprint.
- McFee et al., librosa, *SciPy*, 2015.

Full list: [docs/research/citation-bank.md](../../docs/research/citation-bank.md).
