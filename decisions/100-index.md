# 100 — Index of prototype decisions (100–199)

Decisions made while building the first end-to-end prototype (Nov 2026). Every one is
**proposed — prototype default, team to confirm**: each module owner reads theirs, then keeps,
changes or replaces it (with a new record in their own range: 200s M1, 300s M2, 400s M3, 500s M4,
600s M5). Team-wide decisions are 000–099.

| # | Decision | Module |
|---|---|---|
| [101](101-app-threading-model.md) | One engine thread runs the modules; audio, DMX, matching, web each get a thread | app |
| [102](102-app-ui-transport.md) | Web UI = one static page + one WebSocket on port 8765 | app |
| [103](103-m1-audio-sources.md) | Mic/line-in, file through the speakers, and silence behind one callback | M1 |
| [104](104-m1-features-and-agc.md) | 2048-point FFT, six bands with adaptive gain, log-compressed flux | M1 |
| [105](105-m3-onset-detection.md) | Onsets: flux above moving median + 2.5 × MAD, 100 ms refractory | M3 |
| [106](106-m3-tempo-and-beat-tracking.md) | Tempo by autocorrelation with a 120 BPM prior; beats by comb filter + PLL | M3 |
| [107](107-m3-energy-trend-and-drop.md) | energy_trend from loudness averages; drop = loudness + bass return | M3 |
| [108](108-m5-fingerprint-parameters.md) | Landmark (Shazam-style) fingerprinting, parameters | M5 |
| [109](109-m5-recognition-confidence-and-schedule.md) | Confidence = margin over noise and runner-up; match once a second off the fast path; **module 5 name is an open team question** | M5 |
| [110](110-m5-mood-placeholder.md) | Mood is a labelled placeholder until a DEAM-trained model replaces it | M5 |
| [111](111-superposition-blending-model.md) | Presets steer the reactive show's parameters; they never replace it | M4 |
| [112](112-superposition-colour-space.md) | Blend palettes in OKLab; colour and brightness kept separate | M4 |
| [113](113-superposition-song-state-and-transitions.md) | Hysteresis on recognition; changes on the beat, snap on a drop, hold through dropouts | M4 |
| [114](114-superposition-flash-safety-cap.md) | Flash cap: count brightness rises per fixture and rig; refuse the 4th in any second | M4 |
| [115](115-superposition-latency-budget.md) | Measure every stage; ~1.6 ms processing; fire beat pulses 40 ms early | M4 |
| [116](116-superposition-reactive-looks.md) | Looks: pulse, bands, chase, and auto | M4 |
| [117](117-lighting-patch-and-profiles.md) | JSON patch + profiles; LPC1818 maps unverified | M2 |
| [118](118-lighting-colour-and-dimmer-curves.md) | sRGB → linear colour; dimmer gamma 2.2 | M2 |
| [119](119-lighting-dmx-output-thread.md) | DMX thread at 30 fps, latest frame only, survives a missing cable | M2 |
| [120](120-contract-change-live-controls-look.md) | Contract: add optional `LiveControls.look` (needs team approval) | contract |
| [121](121-testing-with-fakes.md) | Test each module alone against fakes; architecture test | whole team |
