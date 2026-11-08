"""M4 alone: fake RhythmState / MusicContext / LiveControls in, LightIntent checked.
The safety-cap tests try hard to break the cap; none may succeed."""
import dataclasses

import numpy as np
import pytest

from lumasync import fakes
from lumasync.contract import AudioFrame, LiveControls, MusicContext, RhythmState, SongPreset
from lumasync.m4_superposition import SuperpositionEngine, count_flashes, max_flashes_in_window
from lumasync.m4_superposition.colour import hex_to_srgb, lerp, oklab_to_srgb, srgb_to_oklab

PRESETS = {
    "a": SongPreset("a", "Song A", palette=["#ff0040", "#4000ff"], energy=0.9, strobe=True),
    "b": SongPreset("b", "Song B", palette=["#00ff80", "#ffaa00", "#0080ff"], energy=0.3, blend=1.0),
}
TICK = 1024 / 44100


def brightness(intent):
    return np.array([f.dimmer * max(f.rgb) for f in intent.fixtures])


def zigzag_rises(t, y, delta=0.1, dark=0.8):
    """Independent flash counter: turning points of a zig-zag filter, rises from a dark trough."""
    rises, lo, hi, direction = [], y[0], y[0], 0
    for ti, yi in zip(t, y):
        if direction >= 0:
            if yi > hi:
                hi = yi
            if yi <= hi - delta:
                direction, lo = -1, yi
        if direction <= 0:
            if yi < lo:
                lo = yi
            if yi >= lo + delta:
                if lo < dark:
                    rises.append(ti)
                direction, hi = 1, yi
    return np.array(rises)


def check_cap(ts, ys):
    # the rig is dark before the show starts: prepend one dark sample
    ts = np.concatenate([[ts[0] - TICK], ts])
    ys = np.vstack([np.zeros((1, len(ys[0]))), np.array(ys)])
    for i in range(ys.shape[1]):
        assert max_flashes_in_window(count_flashes(ts, ys[:, i])) <= 3
        assert max_flashes_in_window(zigzag_rises(ts, ys[:, i])) <= 3
    assert max_flashes_in_window(count_flashes(ts, ys.mean(axis=1))) <= 3
    assert max_flashes_in_window(zigzag_rises(ts, ys.mean(axis=1))) <= 3


@pytest.mark.parametrize("seed", range(4))
def test_flash_cap_survives_hostile_random_input(seed):
    rng = np.random.default_rng(seed)
    eng = SuperpositionEngine(8, PRESETS)
    ts, ys = [], []
    controls = LiveControls(strobe_enabled=True)
    for i in range(int(40 / TICK)):
        t = i * TICK
        bands = {k: float(rng.random()) for k in ["sub", "bass", "low_mid", "mid", "high_mid", "high"]}
        audio = AudioFrame(t=t, samples=np.zeros(1024, np.float32), rms=float(rng.random()), bands=bands)
        rhythm = RhythmState(t=t, bpm=float(rng.choice([0, 90, 128, 200, 300])), beat=bool(rng.random() < 0.5),
                             beat_phase=float(rng.random()), onset=float(rng.random()), drop=bool(rng.random() < 0.1),
                             energy_trend=float(rng.uniform(-1, 1)))
        music = MusicContext(t=t, song_id=str(rng.choice(["a", "b", "x"])), song_confidence=float(rng.random()))
        if rng.random() < 0.15:  # an operator mashing every control
            controls = dataclasses.replace(
                controls, master=float(rng.random()), reactivity=float(rng.random()),
                preset_blend=float(rng.random()), blackout=bool(rng.random() < 0.5),
                strobe_enabled=bool(rng.random() < 0.8), look=str(rng.choice(["auto", "pulse", "bands", "chase"])),
                manual_song_id=rng.choice([None, "a", "b"]))
        intent = eng.process(audio, rhythm, music, controls)
        ts.append(t)
        ys.append(brightness(intent))
    check_cap(ts, ys)


def test_flash_cap_with_fast_beats_and_strobe():
    eng = SuperpositionEngine(4, PRESETS)
    c = LiveControls(strobe_enabled=True, reactivity=1.0, manual_song_id="a", look="pulse")
    ts, ys = [], []
    for a, r in zip(fakes.fake_audio_frames(200, 20), fakes.fake_rhythm_states(200, 20)):
        r.onset, r.drop = 1.0, True
        ts.append(a.t)
        ys.append(brightness(eng.process(a, r, MusicContext(t=a.t), c)))
    check_cap(ts, ys)


def test_blackout_toggling_cannot_make_flashes():
    eng = SuperpositionEngine(4, PRESETS)
    ts, ys = [], []
    for i, (a, r) in enumerate(zip(fakes.fake_audio_frames(128, 10), fakes.fake_rhythm_states(128, 10))):
        c = LiveControls(blackout=(i // 2) % 2 == 0, reactivity=0.0, master=1.0)  # blackout on/off ~10x/s
        ts.append(a.t)
        ys.append(brightness(eng.process(a, r, None, c)))
    check_cap(ts, ys)


def test_blackout_is_immediate_and_total():
    eng = SuperpositionEngine(8, PRESETS)
    a, r = fakes.fake_audio_frames(128, 2), fakes.fake_rhythm_states(128, 2)
    for x, y in zip(a[:40], r[:40]):
        eng.process(x, y, None, LiveControls())
    out = eng.process(a[40], r[40], None, LiveControls(blackout=True))
    assert all(f.dimmer == 0.0 for f in out.fixtures)


def test_master_scales_output():
    def avg(master):
        eng = SuperpositionEngine(8, PRESETS)
        vals = [brightness(eng.process(a, r, None, LiveControls(master=master, reactivity=0.0))).mean()
                for a, r in zip(fakes.fake_audio_frames(128, 3), fakes.fake_rhythm_states(128, 3))]
        return np.mean(vals[-20:])
    assert abs(avg(0.5) / avg(1.0) - 0.5) < 0.02


def test_hardware_strobe_channel_never_used():
    eng = SuperpositionEngine(8, PRESETS)
    c = LiveControls(strobe_enabled=True, manual_song_id="a")
    for a, r in zip(fakes.fake_audio_frames(128, 5), fakes.fake_rhythm_states(128, 5, drop_at=2)):
        assert all(f.strobe == 0.0 for f in eng.process(a, r, None, c).fixtures)


def test_missing_inputs_count_as_zero():
    eng = SuperpositionEngine(6)
    out = eng.process(AudioFrame(t=0, samples=np.zeros(1024, np.float32)), None, None, LiveControls())
    assert len(out.fixtures) == 6 and all(0 <= f.dimmer <= 1 for f in out.fixtures)


def run_script(script, seconds, controls=None):
    eng = SuperpositionEngine(8, PRESETS)
    states = []
    for a, r, m in zip(fakes.fake_audio_frames(128, seconds), fakes.fake_rhythm_states(128, seconds),
                       fakes.fake_music_contexts(script, seconds)):
        eng.process(a, r, m, controls or LiveControls())
        states.append((a.t, dict(eng.status())))
    return states


def at(states, t):
    return next(s for ts, s in states if ts >= t)


def test_brief_false_match_does_not_lock():
    st = run_script([(0, None, 0), (2, "b", 0.9), (2.8, None, 0)], 8)
    assert all(s["preset_song"] is None for _, s in st)


def test_sustained_match_locks_and_fades_in():
    st = run_script([(0, None, 0), (1, "a", 0.9)], 8)
    assert at(st, 2.0)["song_state"] in ("candidate", "none")
    assert at(st, 5.0)["song_state"] == "locked" and at(st, 5.0)["preset_song"] == "a"
    assert at(st, 6.0)["preset_weight"] > 0.7


def test_short_dropout_holds_preset_long_loss_releases():
    st = run_script([(0, "a", 0.9), (6, None, 0)], 16)
    assert at(st, 9.0)["song_state"] == "holding" and at(st, 9.0)["preset_song"] == "a"
    assert at(st, 15.5)["song_state"] == "none" and at(st, 15.5)["preset_weight"] < 0.05


def test_song_change_crossfades_without_passing_through_house():
    st = run_script([(0, "a", 0.9), (8, "b", 0.9)], 18)
    assert at(st, 16)["preset_song"] == "b"
    weights = [s["preset_weight"] for t, s in st if 9 < t < 15]
    assert min(weights) > 0.5     # weight stays up during A -> B: palettes blend directly


def test_manual_override_is_immediate():
    st = run_script([(0, "a", 0.9)], 4, controls=LiveControls(manual_song_id="b"))
    assert at(st, 0.1)["song_state"] == "manual"
    assert at(st, 1.0)["preset_song"] == "b" and at(st, 1.0)["preset_weight"] > 0.9


def test_preset_modulates_rather_than_replaces():
    """With a preset fully applied, the lights still pulse with the beat."""
    eng = SuperpositionEngine(8, PRESETS)
    c = LiveControls(manual_song_id="a", preset_blend=1.0, look="pulse")
    d = [eng.process(a, r, None, c).fixtures[0].dimmer
         for a, r in zip(fakes.fake_audio_frames(128, 6), fakes.fake_rhythm_states(128, 6))]
    assert np.ptp(d[-60:]) > 0.4


def test_oklab_midpoint_does_not_dip_in_lightness():
    red, green = srgb_to_oklab(hex_to_srgb("#ff0000")), srgb_to_oklab(hex_to_srgb("#00ff00"))
    mid = lerp(red, green, 0.5)
    assert mid[0] >= min(red[0], green[0]) - 1e-9
    rgb_mid_lab = srgb_to_oklab(np.array([0.5, 0.5, 0.0]))     # the RGB-space midpoint, for contrast
    assert rgb_mid_lab[0] < mid[0] - 0.1
    assert np.allclose(oklab_to_srgb(srgb_to_oklab(np.array([0.2, 0.4, 0.9]))), [0.2, 0.4, 0.9], atol=1e-6)
