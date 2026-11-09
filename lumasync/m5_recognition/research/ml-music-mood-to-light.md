# ML Module Research: Music Mood to Light

**Author:** Rohan Chandan · **Module:** M5 Machine Learning · dated Nov 9, 2026
**Source:** Google Drive › Deliverables › "ML Module Research Music Mood to Light" (pulled into the repo 2026-11-09; the Drive doc may have moved on since. A quadrant colour figure in the original is not reproduced here).
Content is the author's own; only formatting was changed for markdown. See [MODULE.md](../MODULE.md#research-vs-the-prototype) for how it lines up with the prototype.

---

## Summary for the meeting

**Recommendation:** predict two continuous numbers, arousal and valence, about twice a second with a regression model running on the laptop, train it on the DEAM dataset, and map the two numbers to colour using Palmer et al. (2013).

1. **Regression, not genre classification.** Our own cited paper (Yang et al. 2008) uses support vector regression (SVR) to predict arousal and valence, not an SVM that sorts genres.
2. **Arousal will work, valence will be weak.** Yang et al. reached R² of 0.58 for arousal but only 0.28 for valence. So arousal should drive most of the lighting and valence a gentler hue shift.
3. **Training data exists.** DEAM has 1,802 Creative Commons songs with arousal and valence labelled every 0.5 s.
4. **Two build paths.** (A) Our own features plus SVR in scikit-learn. (B) Essentia's free pretrained arousal-valence models as a baseline to beat.
5. **Runs on the laptop as a slow layer.** Updates at 1 to 2 Hz on a low-priority thread and sends a confidence value c to the superposition engine.
6. **Colour mapping is backed by research.** Fast, major-key music pairs with lighter, more saturated, yellower colours. Slow, minor music pairs with darker, greyer, bluer ones.

## Where the proposal's ML section stands

The core idea is sound (timbral features, arousal-valence, SVM family), but six things in the current write-up conflict with each other or with the cited papers. Worth fixing before the next report.

| # | What the proposal says | Issue | Suggested fix |
|---|---|---|---|
| 1 | Colour is assigned "based on the energy of the genre" (EDM red, jazz blue) | Genre is a weak proxy. One track has calm intros, builds and drops, and a slow song can be intense. | Predict arousal and valence directly, frame by frame. Genre is not an output. |
| 2 | An SVM draws a hyperplane between high and low arousal, and the model also outputs a smooth 0.0 to 1.0 score | Classification (SVM) and continuous output (regression) are two different things. Yang et al. [30] actually use support vector regression (SVR). | Use SVR (or another regressor) with two continuous outputs. |
| 3 | One intensity score from 0.0 to 1.0 drives the colour | One number cannot hold both arousal and valence, so the 2D emotion model collapses to 1D. | Output two values, arousal and valence, and map both to light. |
| 4 | Buffering ~40 windows of 20 ms gives a rolling average "without introducing lag" | A 0.8 s window lags by design. That is fine for mood, which the superposition engine smooths over ~2 s anyway. | Reword: mood is a slow layer, so ~1 s of lag is acceptable. |
| 5 | The model sends its output to the embedded microcontroller | The superposition section says mood runs on a low-priority thread on the laptop. | Run the model on the laptop. The MCU only receives final lighting values. |
| 6 | Features are centroid, rolloff, flux and ZCR | These track brightness and noisiness, which helps arousal. They say little about valence (happy vs sad). | Add loudness (RMS), tempo from the rhythm module, MFCCs, and chroma or key/mode features. |

Also missing: which dataset trains the model, and how we measure if it works. Both are covered below.

## Emotion model

Use the dimensional model: every moment of music is a point with two coordinates, arousal (calm to energetic) and valence (negative to positive). This is the model Yang et al. (2008) and the DEAM dataset both use.

**Why dimensional instead of categories.** Labels like "happy" or "sad" break at the borders, where a song is half one and half the other. Yang et al. moved to regression on arousal and valence specifically to avoid that ambiguity. Continuous outputs also give the smooth colour fades the proposal wants, for free.

**Why not genre.** One club track can go from a quiet breakdown to a heavy drop in 16 bars. A genre label gives one colour for the whole track. Arousal and valence, predicted every half second, follow those changes.

**Naming.** The proposal calls it "Thayer's arousal-valence model". Yang et al. do frame it as Thayer's plane, but Thayer's original theory uses energy and tension axes. The usual citation for a valence-arousal circle is Russell (1980). Citing both is safest.

## Audio features

Keep the four timbral features from the proposal and add six more, so the model has something to work with for valence, not just arousal.

| Feature | What it captures | Mostly helps | Status |
|---|---|---|---|
| Spectral centroid | Brightness (bassy vs sharp) | Arousal | In proposal |
| Spectral rolloff | Where 85% of the energy sits; noisy highs like cymbals | Arousal | In proposal |
| Spectral flux | How fast the spectrum changes frame to frame | Arousal | In proposal (also used by rhythm module) |
| Zero-crossing rate | Noisiness (snare, distorted guitar) | Arousal | In proposal |
| RMS energy / loudness | How loud the music is | Arousal | Add |
| Low-energy ratio | Share of quiet frames in the window (sparse vs dense) | Arousal | Add (part of Tzanetakis's set) |
| MFCCs (first 5 to 13) | Overall timbre and instrumentation | Both | Add (part of Tzanetakis's set) |
| Tempo and beat strength | Speed and how strong the pulse is | Arousal | Reuse from rhythm module |
| Chroma and key/mode | Which notes are playing; major vs minor | Valence | Add |
| Spectral contrast | Peaks vs valleys in each band (clear vs muddy) | Both | Add |

**Windows.** The proposal's numbers (40 windows of 20 ms = 1 s) come from the 2001 conference version of Tzanetakis and Cook. The 2002 journal version [29] uses 23 ms windows and 43 of them, so both round to about 1 s. Each feature is summarised as its mean and standard deviation over that window.

**Tools.** librosa has every feature above and is easiest for training offline. For live use, compute the same features with the same code, or with Essentia, which supports streaming. DEAM also ships with 260 precomputed openSMILE features at 500 ms windows. These are a fast way to train a first model, but then the live system must compute openSMILE features too.

## Model options

Start with SVR on our own features (it matches our cited paper), and compare it against a linear baseline and Essentia's pretrained model. Pick whichever scores best on held-out songs without hurting the beat path's CPU budget.

| Option | How it works | Pros | Cons | Verdict |
|---|---|---|---|---|
| Ridge (linear) regression | Weighted sum of features, one model each for arousal and valence | Tiny, fast, easy to explain, could even run on an MCU | Misses non-linear patterns | Baseline |
| SVR, RBF kernel | Yang et al.'s method; two regressors in scikit-learn | Proven on small datasets, smooth continuous output | Needs feature scaling and tuning; stores support vectors, so not MCU friendly | Main model |
| SVM classifier (current proposal) | Splits the plane into high/low classes | Simple | Outputs classes, so colours jump at the borders | Drop as main model |
| Gradient boosting (XGBoost / LightGBM) | Many small decision trees | Often strongest on tabular features | More hyperparameters | Optional comparison |
| Small MLP or LSTM on feature sequences | Neural net that sees the last few seconds | DEAM's benchmark found recurrent nets with large feature sets did best for time-varying emotion | Needs more data and tuning time | Stretch goal |
| Essentia pretrained models | MusiCNN or VGGish audio embeddings plus a one-hidden-layer MLP, trained on DEAM, EmoMusic or MuSe | No training needed; ready in a day | Heavier compute; 16 kHz input; CC BY-NC-SA licence (fine for a capstone) | Baseline to beat, fallback |

Whatever we pick, train two separate regressors (arousal, valence) or one model with two outputs, and scale both outputs to 0 to 1 for the lighting module.

## Training data

Train on DEAM and test on PMEmo. DEAM is the largest public dataset with labels that change over time, which is exactly what a live light show needs.

| Dataset | Size | Labels | Notes |
|---|---|---|---|
| DEAM (2017) | 1,802 tracks: 1,744 excerpts of 45 s plus 58 full songs | Arousal and valence every 0.5 s, plus one rating per song; crowdsourced | Free CC-licensed audio (1.3 GB), openSMILE features included. Rock, pop, electronic, country, jazz. The dataset manual says arousal labels are more reliable than valence. |
| PMEmo (2019) | 794 pop chorus clips | Arousal and valence every 0.5 s | High-quality pop; a good second test set closer to club music. |
| EmoMusic | 744 clips of 45 s | Continuous arousal and valence | From the 2013 MediaEval task, which DEAM later combined. Check for overlap before mixing. |
| MuSe | 41,021 tracks | One arousal/valence value per track, derived from Last.fm tags | Huge but noisy and not time-varying. Skip for now. |

**Warning on generalisation.** Scores on one dataset do not carry over. One 2025 study found a model trained on EmoMusic scored R² 0.67 on EmoMusic, 0.44 on DEAM, and below zero on PMEmo. Testing on a second dataset (and on our own playlist) is the honest check.

**Studio vs live audio.** All of these are clean recordings. Our microphone input will have room noise and echo. Plan to add noise and reverb to training audio, and to compare predictions on line input vs mic for the same tracks.

## Mapping mood to colour

Let valence choose the hue (cool to warm) and arousal choose brightness and saturation. That matches the strongest study we cite: in Palmer et al. (2013), faster major-key music drew lighter, more saturated, yellower colour picks, and slower minor-key music drew darker, greyer, bluer ones, in both the US and Mexico.

*(Original figure: arousal-valence plane, 4 quadrants and their light colours.)*

**How this differs from the proposal:** "high energy = red/orange" is half right. Happy high energy (an uplifting drop) points to yellow-orange; red fits tense or aggressive music, since Palmer's team found angry faces paired with dark red.

**Implementation idea.** Pick one colour per quadrant corner and blend between them by (arousal, valence), in a perceptual colour space such as OKLab so blends do not go muddy. Then scale brightness and saturation by arousal.

**Caveat.** Palmer et al. used 18 classical pieces by Bach, Mozart and Brahms. The pattern was very strong (correlations of 0.89 to 0.99 between the music's emotion and the colours' emotion), but nobody has tested it on club music. Our listening test should check it.

## Real-time integration

The mood model is a slow layer: it updates every 0.5 s, lags about 1 s, and that is fine because the superposition engine already smooths mood over about 2 s.

1. Take the shared audio stream from the signal processing module and downsample to 22.05 kHz mono (16 kHz if we use Essentia's models).
2. Every 20 to 23 ms frame, compute the features in the table above.
3. Every 0.5 s, summarise the last 1 to 3 s of frames as mean and standard deviation. A 0.5 s step matches DEAM's 2 Hz labels.
4. Predict arousal and valence, each scaled to 0 to 1.
5. Compute a confidence c from 0 to 1: low when the input is near silence or very noisy, or when consecutive predictions jump around.
6. Push (arousal, valence, c, timestamp) to the superposition engine through the lock-free queue. Its one-pole filter does the smoothing.

**Where it runs.** On the laptop, in its own low-priority thread or process, so it never delays the beat path. The microcontroller only receives final LED or DMX values. If we ever need the model on the MCU, a linear model or small MLP through TensorFlow Lite Micro [31] fits; an RBF SVR does not, because it must store its support vectors.

**Precompute when possible.** If the DJ's players report the loaded track, run the model over the whole file before it plays and replay the curve in sync. That removes mood from the live path entirely, as the superposition section already suggests.

**Lag budget.** Expected delay is roughly half the summary window plus one 0.5 s step plus compute time. We should measure the real number on the demo laptop rather than estimate it.

## Evaluation plan

**Proposed target:** R² of at least 0.5 for arousal and 0.2 for valence on held-out DEAM songs, which is in line with published results for this kind of model.

| Reference result | Arousal R² | Valence R² |
|---|---|---|
| Yang et al. 2008, SVR, 195 clips | 0.58 | 0.28 |
| Yang et al. 2008, test-retest agreement between people (rough ceiling) | 0.81 | 0.59 |
| Kang and Herremans 2025, deep model on DEAM (state of the art) | 0.60 | 0.51 |

**Metrics.** R² and RMSE for each dimension, as used in the MediaEval benchmark. Also plot predicted vs true curves for a few songs, since that is what the light show will look like.

**Split by song, never by frame.** Frames from the same song look almost identical. If some land in training and some in testing, the score is inflated. Use grouped k-fold cross-validation with the song ID as the group.

**System tests.**
- Same tracks through line input and microphone; compare the two prediction curves.
- CPU load and beat-path timing with the mood model on vs off.
- A quick listening check: 5 to 10 people rate whether the colours fit the music, compared with a random colour mapping.

## Risks

The biggest risk is weak valence making the hue wander; the fix is to lean on arousal and smooth valence hard.

| Risk | Why it happens | Mitigation |
|---|---|---|
| Valence predictions are noisy | Even people disagree on valence; published R² is low | Give valence a lower weight and a longer smoothing time than arousal |
| Mic input fools the model | Trained on clean studio audio; live rooms add noise and echo | Augment training audio; prefer line input; let c drop the layer's weight |
| Music style mismatch | DEAM is mostly Western pop, rock, electronic and jazz excerpts, not DJ sets | Test on PMEmo and our own club playlist; fine-tune if needed |
| CPU contention with the beat path | Feature extraction and inference share the processor | Separate low-priority thread or process; 1 to 2 Hz updates; measure |
| Overreaching on deep models | LSTMs and transformers take weeks to tune | Ship the SVR baseline first; deep models only if time allows |
| Licence limits | Essentia models are CC BY-NC-SA | Fine for the capstone; note it if anyone wants to commercialise |

## Next steps

A working arousal-valence stream by the end of November leaves December for integration with the superposition engine. Dates are proposals to agree on.

- **Week of Nov 9:** download DEAM and PMEmo, set up an ml/ folder in the repo, extract features with librosa.
- **Week of Nov 16:** train Ridge and SVR baselines with grouped k-fold; report R² for both dimensions.
- **Week of Nov 23:** run Essentia's pretrained model on the same test songs; pick the main model.
- **Week of Nov 30:** live wrapper that reads mic or line input and outputs (arousal, valence, c) at 2 Hz; measure CPU and lag.
- **Early December:** plug into the superposition engine as a slow layer; run the line vs mic test.
- **Next report:** rewrite the ML section with the fixes from the gaps table.

## Questions for the group

The interface between ML and lighting is the main thing to agree on.

1. **Who owns the colour mapping?** Proposal: ML outputs only (arousal, valence, c, timestamp); the lighting module turns that into colour.
2. **Message format and rate.** Two floats from 0 to 1, a confidence, and a timestamp, sent at 2 Hz. Does that work for the superposition engine?
3. **Audio hand-off.** Will signal processing give ML a mono stream at 22.05 kHz, or should ML resample the raw 48 kHz input itself?
4. Confirm the model runs on the laptop, and the microcontroller only drives LEDs.
5. **Drop genre from the abstract?** It currently says colours come from genre energy, which no longer matches the design.
6. **Line input for the demo?** A clean feed from the mixer would make mood far more reliable than the room mic.
7. **Report housekeeping.** In the proposal's reference list, in-text [5] is the CAD $50 DMX interface but list item [5] is the silent disco paper, so in-text [5] to [16] each point one item too far. List items [16] and [19] are the same paper (which is why numbering lines up again from [17]), and [38] duplicates [23].

## References

Numbers in square brackets, like [29], refer to the proposal's own reference list. New sources:

1. Y.-H. Yang, Y.-C. Lin, Y.-F. Su and H. H. Chen, "A Regression Approach to Music Emotion Recognition," IEEE TASLP, vol. 16, no. 2, pp. 448–457, 2008. (Proposal [30].)
2. A. Aljanaki, Y.-H. Yang and M. Soleymani, "Developing a benchmark for emotional analysis of music," PLoS ONE, vol. 12, no. 3, e0173392, 2017. (DEAM paper.)
3. DEAM dataset download page and manual, University of Geneva.
4. S. E. Palmer, K. B. Schloss, Z. Xu and L. R. Prado-León, "Music–color associations are mediated by emotion," PNAS, vol. 110, no. 22, pp. 8836–8841, 2013. (Proposal [7].)
5. G. Tzanetakis, G. Essl and P. Cook, "Automatic Musical Genre Classification of Audio Signals," Proc. ISMIR, 2001. (Source of the 40 × 20 ms window.)
6. G. Tzanetakis and P. Cook, "Musical genre classification of audio signals," IEEE TSAP, vol. 10, no. 5, 2002. (Proposal [29].)
7. D. Bogdanov, X. Lizarraga-Seijas, P. Alonso-Jiménez and X. Serra, "MusAV: A dataset of relative arousal-valence annotations for validation of audio models," Proc. ISMIR, 2022. (Describes Essentia's arousal-valence models.)
8. MTG-UPF, "music-arousal-valence" demo and model card (Essentia models, CC BY-NC-SA).
9. J. Kang and D. Herremans, "Towards Unified Music Emotion Recognition across Dimensional and Categorical Models," arXiv, 2025.
10. "Embedding-based Music Emotion Recognition Using Composite Loss," arXiv, 2021. (DEAM and PMEmo details.)
11. EmoMusic overview and cross-dataset results, Emergent Mind (secondary summary; check the original before citing in the report).
12. J. A. Russell, "A circumplex model of affect," J. Personality and Social Psychology, vol. 39, no. 6, 1980. (Background, not looked up.)
13. R. E. Thayer, The Biopsychology of Mood and Arousal, Oxford University Press, 1989. (Background, not looked up.)
