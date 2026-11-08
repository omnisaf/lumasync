"""M1 alone: synthetic signals in, AudioFrame fields checked."""
import numpy as np

from lumasync import fakes
from lumasync.contract import BLOCK_SIZE, SAMPLE_RATE
from lumasync.m1_audio import BAND_NAMES, AudioAnalyzer


def sine(freq, seconds=1.0, amp=0.5):
    t = np.arange(int(seconds * SAMPLE_RATE)) / SAMPLE_RATE
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def run(x):
    an = AudioAnalyzer()
    return [an.process(b, t) for t, b in fakes.blocks(x)]


def test_frame_fields_and_ranges():
    f = run(sine(440))[-1]
    assert len(f.samples) == BLOCK_SIZE
    assert set(f.bands) == set(BAND_NAMES)
    assert all(0.0 <= v <= 1.0 for v in f.bands.values())
    assert 0.3 < f.rms < 0.4                      # 0.5 amplitude sine -> RMS 0.354
    assert f.spectrum is not None and len(f.spectrum) == 1025


def test_bass_sine_lights_the_bass_band():
    f = run(sine(100, 2.0))[-1]
    assert f.bands["bass"] > 0.8
    assert f.bands["bass"] > f.bands["high"] + 0.5


def test_centroid_tracks_frequency():
    assert abs(run(sine(1000))[-1].centroid_hz - 1000) < 60
    assert abs(run(sine(3000))[-1].centroid_hz - 3000) < 150


def test_silence_is_zero_bands():
    f = run(np.zeros(SAMPLE_RATE, np.float32))[-1]
    assert f.rms == 0.0 and all(v == 0.0 for v in f.bands.values())


def test_flux_spikes_on_clicks():
    frames = run(fakes.click_track(120, 4.0))
    flux = np.array([f.flux for f in frames])
    clicks = (np.arange(0, 4.0, 0.5) * SAMPLE_RATE / BLOCK_SIZE).astype(int)
    on = flux[clicks[1:]]
    off = np.delete(flux, np.concatenate([clicks, clicks + 1, clicks - 1]))
    assert on.min() > 5 * np.median(off)
