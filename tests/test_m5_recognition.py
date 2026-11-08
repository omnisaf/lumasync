"""M5 alone: fingerprint index built from synthetic songs, matched against noisy excerpts."""
import numpy as np
import pytest

from lumasync import fakes
from lumasync.contract import AudioFrame
from lumasync.m5_recognition import FingerprintIndex, MoodEstimator, RecognitionModule

SR = 44100
LIB = {"neon_drive": 1, "slow_bloom": 2, "breakbeat_140": 3}


@pytest.fixture(scope="module")
def songs():
    return {s: fakes.synth_song(s, 40.0, seed=seed) for s, seed in LIB.items()}


@pytest.fixture(scope="module")
def index(songs):
    return FingerprintIndex.build([(s, s) for s in songs], loader=lambda p: (songs[p], SR))


def noisy(x, snr_db, seed=0):
    rng = np.random.default_rng(seed)
    p = np.mean(x ** 2)
    return (0.6 * (x + rng.standard_normal(len(x)) * np.sqrt(p / 10 ** (snr_db / 10)))).astype(np.float32)


@pytest.mark.parametrize("song", list(LIB))
def test_recognises_8s_excerpt_with_noise(index, songs, song):
    clip = noisy(songs[song][12 * SR:20 * SR], snr_db=10)
    r = index.match(clip, SR)
    assert r.song_id == song
    assert r.confidence >= 0.8
    assert abs(r.offset_s - 12.0) < 0.1          # it also knows WHERE in the song the clip is


def test_rejects_unknown_tracks(index):
    for seed in range(200, 210):
        r = index.match(noisy(fakes.synth_song("random", 10.0, seed=seed)[:8 * SR], 20), SR)
        assert r.confidence < 0.5, (seed, r)


def test_rejects_silence_and_noise(index):
    assert index.match(np.zeros(8 * SR, np.float32), SR).song_id is None
    rng = np.random.default_rng(1)
    assert index.match((rng.standard_normal(8 * SR) * 0.1).astype(np.float32), SR).song_id is None


def test_index_round_trip(tmp_path, index, songs):
    index.save(str(tmp_path))
    loaded = FingerprintIndex.load(str(tmp_path))
    assert loaded.song_ids == index.song_ids
    assert loaded.match(songs["slow_bloom"][5 * SR:13 * SR], SR).song_id == "slow_bloom"


def test_live_module_recognises_from_frames(index, songs):
    m5 = RecognitionModule(index, async_match=False)
    x = songs["breakbeat_140"]
    ctx = None
    for i in range(0, 6 * SR, 1024):
        ctx = m5.process(AudioFrame(t=i / SR, samples=x[i:i + 1024], rms=0.2))
    assert ctx.song_id == "breakbeat_140" and ctx.song_confidence > 0.8


def test_mood_placeholder_ranges():
    mood = MoodEstimator()
    v = a = None
    for f in fakes.audio_frames_from_samples(fakes.synth_song("neon_drive", 6.0, seed=1)):
        v, a = mood.process(f)
    assert v is not None and -1 <= v <= 1 and -1 <= a <= 1
    silent = MoodEstimator()
    for f in fakes.audio_frames_from_samples(np.zeros(3 * SR, np.float32)):
        out = silent.process(f)
    assert out == (None, None)
