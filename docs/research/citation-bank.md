# Citation bank

Which papers and standards each part of the project should cite. Checked 2026-09-24.

**How this was checked (2026-09-24).** Every entry below was confirmed to exist.
Anything with a DOI was checked against the Crossref registry (title, authors,
venue, year, pages). Conference papers without a DOI were checked on the ISMIR
or DAFx proceedings archive. Standards were checked on the publisher's own site
(ESTA TSP, ITU, W3C). Nothing here is from memory alone. If you add a source,
check it the same way.

**How to use it.** Numbers run [1]–[36] in one list, so you can paste straight
into the report's reference section and renumber in citation order. Each entry
has one line on what it gives us and one line on where it gets cited.

> Standards note: DMX512-A and sACN both had new editions recently.
> Cite **E1.11-2024** and **E1.31-2025**, not the older 2008 / 2018 editions.
> Same for photosensitivity: **ITU-R BT.1702-3 (2023)** is the one in force.

---

## 1. Onset, beat and tempo tracking

The live audio front end: finding note starts (onsets), the beat grid, and BPM.

**[1]** J. P. Bello, L. Daudet, S. Abdallah, C. Duxbury, M. Davies, and M. B. Sandler, "A tutorial on onset detection in music signals," *IEEE Trans. Speech Audio Process.*, vol. 13, no. 5, pp. 1035–1047, Sep. 2005, doi: 10.1109/TSA.2005.851998.
- Gives: the standard survey of onset-detection functions (spectral flux, phase, energy). Justifies whichever onset function we pick.
- Cite in: beat/onset module · background.

**[2]** E. D. Scheirer, "Tempo and beat analysis of acoustic musical signals," *J. Acoust. Soc. Am.*, vol. 103, no. 1, pp. 588–601, Jan. 1998, doi: 10.1121/1.421129.
- Gives: the classic filterbank + resonator approach to real-time tempo. Good "where the field started" reference and a cheap baseline.
- Cite in: beat/onset module · background.

**[3]** D. P. W. Ellis, "Beat tracking by dynamic programming," *J. New Music Res.*, vol. 36, no. 1, pp. 51–60, 2007, doi: 10.1080/09298210701653344.
- Gives: a simple, well-known beat tracker (it is the one inside librosa). Our likely offline baseline.
- Cite in: beat/onset module · song pre-analysis.

**[4]** S. Böck, F. Krebs, and G. Widmer, "Joint beat and downbeat tracking with recurrent neural networks," in *Proc. 17th Int. Soc. Music Inf. Retrieval Conf. (ISMIR)*, New York, NY, USA, 2016, pp. 255–261. [Online]. Available: https://archives.ismir.net/ismir2016/paper/000186.pdf
- Gives: state-of-the-art neural beat **and downbeat** (bar start) tracking. Downbeats matter for lighting because cues usually change on the bar, not the beat.
- Cite in: beat/onset module · ML approach.

## 2. Audio analysis software

The libraries we will build on. Cite them like papers; both projects ask to be cited this way.

**[5]** B. McFee, C. Raffel, D. Liang, D. P. W. Ellis, M. McVicar, E. Battenberg, and O. Nieto, "librosa: Audio and music signal analysis in Python," in *Proc. 14th Python in Science Conf. (SciPy)*, 2015, pp. 18–24, doi: 10.25080/Majora-7b98e3ed-003.
- Gives: feature extraction (spectrograms, chroma, onset strength, beat tracking) in Python.
- Cite in: implementation / tools section.

**[6]** S. Böck, F. Korzeniowski, J. Schlüter, F. Krebs, and G. Widmer, "madmom: A new Python audio and music signal processing library," in *Proc. 24th ACM Int. Conf. Multimedia (MM '16)*, Amsterdam, The Netherlands, 2016, pp. 1174–1178, doi: 10.1145/2964284.2973795.
- Gives: ready-made RNN beat, downbeat and tempo models, including online (real-time) processors.
- Cite in: implementation / tools section · beat/onset module.

## 3. Music structure and section boundaries

Finding verse / chorus / drop boundaries, so the show can change "scene" at the right moment.

**[7]** J. Foote, "Automatic audio segmentation using a measure of audio novelty," in *Proc. IEEE Int. Conf. Multimedia Expo (ICME)*, New York, NY, USA, 2000, vol. 1, pp. 452–455, doi: 10.1109/ICME.2000.869637.
- Gives: the self-similarity matrix + novelty curve method. Simple, explainable, and our likely baseline for boundaries.
- Cite in: structure module · background.

**[8]** J. Paulus, M. Müller, and A. Klapuri, "State of the art report: Audio-based music structure analysis," in *Proc. 11th Int. Soc. Music Inf. Retrieval Conf. (ISMIR)*, Utrecht, The Netherlands, 2010, pp. 625–636. [Online]. Available: https://ismir2010.ismir.net/proceedings/ismir2010-107.pdf
- Gives: the three families of methods (repetition, novelty, homogeneity). Useful for framing the design choice.
- Cite in: structure module · literature review.

**[9]** K. Ullrich, J. Schlüter, and T. Grill, "Boundary detection in music structure analysis using convolutional neural networks," in *Proc. 15th Int. Soc. Music Inf. Retrieval Conf. (ISMIR)*, Taipei, Taiwan, 2014, pp. 417–422. [Online]. Available: https://archives.ismir.net/ismir2014/paper/000271.pdf
- Gives: a learned (CNN) boundary detector on mel spectrograms. The ML option to compare against Foote.
- Cite in: structure module · ML approach.

**[10]** O. Nieto, G. J. Mysore, C.-i. Wang, J. B. L. Smith, J. Schlüter, T. Grill, and B. McFee, "Audio-based music structure analysis: Current trends, open challenges, and applications," *Trans. Int. Soc. Music Inf. Retrieval*, vol. 3, no. 1, pp. 246–263, 2020, doi: 10.5334/tismir.54.
- Gives: the up-to-date review, including evaluation metrics (boundary hit rate at ±0.5 s / ±3 s) we can reuse for our own testing.
- Cite in: structure module · evaluation plan.

## 4. Music emotion (mood) recognition

Mapping audio to mood, so colour and intensity follow the feel of the song.

**[11]** J. A. Russell, "A circumplex model of affect," *J. Pers. Soc. Psychol.*, vol. 39, no. 6, pp. 1161–1178, 1980, doi: 10.1037/h0077714.
- Gives: the valence–arousal model. Valence is how positive a song feels; arousal is how energetic. This is the 2-D space our mood output lives in.
- Cite in: mood module · background.

**[12]** Y.-H. Yang and H. H. Chen, "Machine recognition of music emotion: A review," *ACM Trans. Intell. Syst. Technol.*, vol. 3, no. 3, pp. 1–30, May 2012, doi: 10.1145/2168752.2168754.
- Gives: the standard review of music emotion recognition (features, categorical vs. dimensional models, regression).
- Cite in: mood module · literature review.

**[13]** A. Aljanaki, Y.-H. Yang, and M. Soleymani, "Developing a benchmark for emotional analysis of music," *PLOS ONE*, vol. 12, no. 3, Art. no. e0173392, 2017, doi: 10.1371/journal.pone.0173392.
- Gives: the **DEAM** dataset — ~1,800 songs with valence–arousal labels over time (per half-second), which suits a live system.
- Cite in: mood module · training data.

**[14]** K. Zhang, H. Zhang, S. Li, C. Yang, and L. Sun, "The PMEmo dataset for music emotion recognition," in *Proc. ACM Int. Conf. Multimedia Retrieval (ICMR)*, Yokohama, Japan, 2018, pp. 135–142, doi: 10.1145/3206025.3206037.
- Gives: **PMEmo**, a pop/chorus-focused valence–arousal dataset. A second dataset for testing that the model generalises.
- Cite in: mood module · training data / evaluation.

## 5. Audio fingerprinting (recognising a pre-analysed song)

Identifying which song is playing so we can load its pre-planned looks.

**[15]** A. L.-C. Wang, "An industrial-strength audio search algorithm," in *Proc. 4th Int. Conf. Music Inf. Retrieval (ISMIR)*, Baltimore, MD, USA, 2003. [Online]. Available: https://www.ee.columbia.edu/~dpwe/papers/Wang03-shazam.pdf
- Gives: the Shazam method — spectrogram peak "constellations" hashed in pairs. Robust to crowd noise, which a live venue has.
- Cite in: song-recognition module · background.

**[16]** J. Haitsma and T. Kalker, "A highly robust audio fingerprinting system," in *Proc. 3rd Int. Conf. Music Inf. Retrieval (ISMIR)*, Paris, France, 2002, pp. 107–115. [Online]. Available: https://ismir2002.ismir.net/proceedings/02-FP04-2.pdf
- Gives: the Philips method — sign-of-energy-difference bits across bands. The main alternative design to Wang.
- Cite in: song-recognition module · design comparison.

**[17]** P. Cano, E. Batlle, T. Kalker, and J. Haitsma, "A review of audio fingerprinting," *J. VLSI Signal Process. Syst.*, vol. 41, no. 3, pp. 271–284, Nov. 2005, doi: 10.1007/s11265-005-4151-3.
- Gives: the requirements framework (robustness, granularity, speed, database size). Good for writing our own spec.
- Cite in: song-recognition module · requirements.

**[18]** L. Lalinský, *Chromaprint* (audio fingerprinting library for AcoustID). AcoustID OÜ. Accessed: Sep. 24, 2026. [Online]. Available: https://acoustid.org/chromaprint (source: https://github.com/acoustid/chromaprint)
- Gives: an open-source fingerprint library we could use instead of writing one.
- Cite in: song-recognition module · implementation / tools.

## 6. Tempo-invariant alignment (stretching a show to the live tempo)

Warping a pre-planned show onto a live version that is faster, slower, or drifting.

**[19]** H. Sakoe and S. Chiba, "Dynamic programming algorithm optimization for spoken word recognition," *IEEE Trans. Acoust., Speech, Signal Process.*, vol. 26, no. 1, pp. 43–49, Feb. 1978, doi: 10.1109/TASSP.1978.1163055.
- Gives: the original dynamic time warping (DTW) paper. DTW finds the best stretch/squash mapping between two sequences.
- Cite in: show-sync module · background.

**[20]** S. Dixon, "Live tracking of musical performances using on-line time warping," in *Proc. 8th Int. Conf. Digital Audio Effects (DAFx)*, Madrid, Spain, 2005. [Online]. Available: https://www.dafx.de/paper-archive/2005/P_092.pdf
- Gives: **on-line** time warping — aligns as the audio arrives, in linear time. This is the real-time version we need.
- Cite in: show-sync module · core method.

**[21]** M. Müller, *Fundamentals of Music Processing: Audio, Analysis, Algorithms, Applications*. Cham, Switzerland: Springer, 2015, doi: 10.1007/978-3-319-21945-5.
- Gives: textbook treatment of DTW for music (ch. 3), tempo and beat (ch. 6) and structure (ch. 4). One reference that backs several modules.
- Cite in: show-sync, beat and structure modules · background.

## 7. Automatic light-show / stage-lighting generation

The closest prior work to the project itself. Use these to show the gap we fill.

**[22]** S.-W. Hsiao, S.-K. Chen, and C.-H. Lee, "Methodology for stage lighting control based on music emotions," *Inf. Sci.*, vols. 412–413, pp. 14–35, Oct. 2017, doi: 10.1016/j.ins.2017.05.026.
- Gives: the earlier approach — classify song mood (SVM, four quadrants), then pick a preset lighting pattern. Also states the problem: engineers and DJs spend 2–3× longer matching light cues to music.
- Cite in: introduction (problem statement) · literature review.

**[23]** Z. Zhao, D. Jin, Z. Zhou, and X. Zhang, "Automatic stage lighting control: Is it a rule-driven process or generative task?," in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2026. [Online]. Available: https://arxiv.org/abs/2506.01482
- Gives: Skip-BART, a transformer that generates light hue and intensity straight from audio, trained on real lighting engineers. Released a public dataset (RPMC-L2) and code.
- Cite in: literature review · AI show-generation module.

**[24]** Z. Zhao, D. Jin, Z. Zhou, and X. Zhang, "Stage light is sequence²: Multi-light control via imitation learning," arXiv:2605.03660, May 2026. [Online]. Available: https://arxiv.org/abs/2605.03660
- Gives: extends [23] from one light to **many lights**, each with its own colour. Relevant to our "map onto any rig" goal. Preprint — flag as not yet peer reviewed.
- Cite in: literature review · fixture-mapping module.

**[25]** M. Kohl, T. Wursthorn, and C. Weiß, "Cross-modal metrics for capturing correspondences between music audio and stage lighting signals," in *Proc. 33rd ACM Int. Conf. Multimedia (MM '25)*, 2025, pp. 528–534, doi: 10.1145/3746027.3755488.
- Gives: metrics for scoring how well lighting matches music. We can use these to evaluate our own shows instead of inventing a score.
- Cite in: evaluation / testing plan.

## 8. Human–AI co-creation (editing a generated show)

Why the user edits an AI draft rather than accepting it or starting from scratch.

**[26]** E. Horvitz, "Principles of mixed-initiative user interfaces," in *Proc. SIGCHI Conf. Human Factors Comput. Syst. (CHI '99)*, Pittsburgh, PA, USA, 1999, pp. 159–166, doi: 10.1145/302979.303030.
- Gives: the founding principles for systems where human and AI both take initiative, e.g. let the user easily correct or override the AI.
- Cite in: show-editor module · design rationale.

**[27]** S. Amershi *et al.*, "Guidelines for human-AI interaction," in *Proc. CHI Conf. Human Factors Comput. Syst. (CHI '19)*, Glasgow, U.K., 2019, pp. 1–13, doi: 10.1145/3290605.3300233.
- Gives: 18 tested design guidelines (e.g. "support efficient correction"). A checklist for the editor UI.
- Cite in: show-editor module · design rationale / evaluation.

**[28]** R. Louie, A. Coenen, C. Z. Huang, M. Terry, and C. J. Cai, "Novice-AI music co-creation via AI-steering tools for deep generative models," in *Proc. CHI Conf. Human Factors Comput. Syst. (CHI '20)*, Honolulu, HI, USA, 2020, pp. 1–13, doi: 10.1145/3313831.3376739.
- Gives: user-study evidence that giving people "steering" controls over a generative music model increases ownership and trust. Direct analogy to steering a generated light show.
- Cite in: show-editor module · literature review.

**[29]** F. A. Robinson, V. Raj, D. Cooper, F. Du, and D. Gunawan, "Glow with the flow: AI-assisted creation of ambient lightscapes for music videos," arXiv:2602.08838, Feb. 2026 (accepted to IEEE PacificVis 2026). [Online]. Available: https://arxiv.org/abs/2602.08838
- Gives: the nearest match to our editor idea — AI generates a lighting sequence from music, users rate it as a good *starting point* and then refine it.
- Cite in: show-editor module · literature review.

## 9. DMX512-A and lighting-control protocols

The output side. What the fixtures actually speak.

**[30]** *Entertainment Technology — USITT DMX512-A, Asynchronous Serial Digital Data Transmission Standard for Controlling Lighting Equipment and Accessories*, ANSI E1.11-2024, ESTA, approved Apr. 25, 2024. [Online]. Available: https://tsp.esta.org/tsp/documents/published_docs.php
- Gives: the DMX512-A standard itself — packet timing, 512 channels (slots) per universe, the EIA-485 electrical layer. Our output must meet it.
- Cite in: DMX output module · standards section.

**[31]** *Entertainment Technology — Lightweight Streaming Protocol for Transport of DMX512 Using ACN*, ANSI E1.31-2025, ESTA, approved Jan. 5, 2026. [Online]. Available: https://tsp.esta.org/tsp/documents/published_docs.php
- Gives: sACN — DMX sent over Ethernet/Wi-Fi. Lets a laptop drive many universes without a DMX cable per universe.
- Cite in: DMX output module · standards section.

**[32]** Artistic Licence, *Art-Net 4 Specification for the Art-Net 4 Ethernet Communication Protocol*. Accessed: Sep. 24, 2026. [Online]. Available: https://art-net.org.uk/downloads/art-net.pdf
- Gives: the other common DMX-over-IP protocol. Many cheap USB/Ethernet DMX nodes speak Art-Net, so it matters for the "cheap DIY" goal.
- Cite in: DMX output module · design comparison.

## 10. Photosensitive seizure (flash-rate) safety

Why the controller must cap flash rate. This is a safety requirement, not a style choice.

**[33]** W3C, "Success Criterion 2.3.1: Three flashes or below threshold," in *Web Content Accessibility Guidelines (WCAG) 2.2*, W3C Recommendation, 2023. [Online]. Available: https://www.w3.org/TR/WCAG22/#three-flashes-or-below-threshold
- Gives: the plain rule — no more than **3 flashes in any 1-second period**, unless below the general and red flash thresholds. Simplest number to put in our requirements.
- Cite in: safety requirements · flash-limiter.

**[34]** *Guidance for the Reduction of Photosensitive Epileptic Seizures Caused by Television*, ITU-R Recommendation BT.1702-3, International Telecommunication Union, Nov. 2023. [Online]. Available: https://www.itu.int/rec/R-REC-BT.1702/
- Gives: the international broadcast guidance, including how to measure luminance flashes and saturated-red transitions.
- Cite in: safety requirements · flash-limiter test method.

**[35]** G. Harding, A. J. Wilkins, G. Erba, G. L. Barkley, and R. S. Fisher, "Photic- and pattern-induced seizures: Expert consensus of the Epilepsy Foundation of America Working Group," *Epilepsia*, vol. 46, no. 9, pp. 1423–1425, Sep. 2005, doi: 10.1111/j.1528-1167.2005.31305.x.
- Gives: the medical basis — the expert consensus that the flash rules come from, including the higher risk of saturated red.
- Cite in: safety requirements · background.

**[36]** J. B. Jordan and G. C. Vanderheiden, "International guidelines for photosensitive epilepsy: Gap analysis and recommendations," *ACM Trans. Access. Comput.*, vol. 17, no. 3, pp. 1–35, 2024, doi: 10.1145/3694790.
- Gives: compares WCAG, ITU and other guidelines side by side and notes where they disagree. Helps us justify which threshold we choose.
- Cite in: safety requirements · literature review.

---

## Also verified, not used above

Real and checked, kept here in case a section needs one more:

- G. N. Yannakakis, A. Liapis, and C. Alexopoulos, "Mixed-initiative co-creativity," in *Proc. 9th Int. Conf. Foundations Digit. Games (FDG)*, 2014. Available: https://www.um.edu.mt/library/oar/bitstream/123456789/29459/1/Mixed-initiative_co-creativity.pdf
- R. S. Fisher, G. Harding, G. Erba, G. L. Barkley, and A. Wilkins, "Photic- and pattern-induced seizures: A review for the Epilepsy Foundation of America Working Group," *Epilepsia*, vol. 46, no. 9, pp. 1426–1441, 2005, doi: 10.1111/j.1528-1167.2005.31405.x.
- *Entertainment Technology — Remote Device Management over DMX512 Networks*, ANSI E1.20-2025, ESTA, approved Jan. 8, 2025. (RDM: two-way talk with fixtures — could auto-discover a rig.)
- R. Panda, R. Malheiro, and R. P. Paiva, "Novel audio features for music emotion recognition," *IEEE Trans. Affect. Comput.*, vol. 11, no. 4, pp. 614–626, 2020, doi: 10.1109/TAFFC.2018.2820691.
