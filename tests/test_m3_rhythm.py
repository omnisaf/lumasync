"""M3 alone: AudioFrames from fakes.py (no M1), tempo / beat / drop checked."""
import numpy as np
import pytest

from lumasync import fakes
from lumasync.m3_rhythm import RhythmTracker


def track(frames):
    tr = RhythmTracker()
    states = [tr.process(f) for f in frames]
    return tr, states


@pytest.mark.parametrize("bpm", [90, 128, 140])
def test_click_track_bpm_within_2(bpm):
    frames = fakes.audio_frames_from_samples(fakes.click_track(bpm, 20.0))
    _, states = track(frames)
    assert abs(states[-1].bpm - bpm) <= 2.0
    assert states[-1].confidence > 0.3


def test_128_locks_within_6_seconds():
    frames = fakes.audio_frames_from_samples(fakes.click_track(128, 12.0))
    _, states = track(frames)
    lock = next(s.t for s in states if s.bpm > 0)
    assert lock < 6.0


def test_beats_land_on_the_clicks():
    bpm = 128
    frames = fakes.audio_frames_from_samples(fakes.click_track(bpm, 20.0))
    _, states = track(frames)
    beats = np.array([s.t for s in states if s.beat and s.t > 10])
    clicks = fakes.click_times(bpm, 20.0)
    err = np.array([np.min(np.abs(clicks - b)) for b in beats])
    assert len(beats) >= 18                       # ~21 beats in 10 s at 128 BPM
    assert np.mean(err) < 0.035                   # within ~1.5 blocks on average


def test_beat_phase_wraps_between_beats():
    frames = fakes.audio_frames_from_samples(fakes.click_track(120, 15.0))
    _, states = track(frames)
    ph = np.array([s.beat_phase for s in states[-80:]])
    assert ph.min() >= 0 and ph.max() < 1 and ph.max() > 0.8


@pytest.mark.parametrize("style,bpm", [("neon_drive", 128), ("slow_bloom", 92), ("breakbeat_140", 140)])
def test_demo_songs_bpm(style, bpm):
    frames = fakes.audio_frames_from_samples(fakes.synth_song(style, 30.0, seed=1))
    _, states = track(frames)
    assert abs(states[-1].bpm - bpm) <= 2.0


def test_fake_feature_stream_also_locks():
    _, states = track(fakes.fake_audio_frames(128, 15.0))
    assert abs(states[-1].bpm - 128) <= 2.0


def test_silence_never_locks_or_beats():
    _, states = track(fakes.audio_frames_from_samples(np.zeros(44100 * 8, np.float32)))
    assert all(s.bpm == 0 and not s.beat and not s.drop for s in states)


def test_drop_after_breakdown():
    # neon_drive: breakdown 22.5-30 s (no kick, no bass), drop at 30 s
    frames = fakes.audio_frames_from_samples(fakes.synth_song("neon_drive", 36.0, seed=1))
    _, states = track(frames)
    drops = [s.t for s in states if s.drop]
    assert any(29.5 <= d <= 31.5 for d in drops)


def test_energy_trend_sign():
    ramp = fakes.synth_song("neon_drive", 20.0, seed=1) * np.linspace(0.05, 1.0, 20 * 44100, dtype=np.float32)
    _, states = track(fakes.audio_frames_from_samples(ramp))
    assert np.mean([s.energy_trend for s in states[-200:]]) > 0.1
