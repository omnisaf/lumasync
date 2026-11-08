"""End to end without audio devices, threads or a browser: the real Engine fed a demo track."""
import os

import numpy as np
import pytest

from lumasync import fakes
from lumasync import library as lib
from lumasync.app import Engine, parse_args


@pytest.fixture(scope="module")
def engine():
    e = Engine(parse_args(["--no-dmx", "--source", "silence"]))
    # wait for any start-up fingerprinting, then match synchronously for a deterministic test
    import time
    for _ in range(100):
        if not e.index_job["running"]:
            break
        time.sleep(0.1)
    e.m5.async_match = False
    return e


def test_pipeline_end_to_end(engine):
    from lumasync.audiofile import load_audio

    x = load_audio(os.path.join(lib.AUDIO_DIR, "demo_neon_drive.wav"), mono=True)[: 14 * 44100]
    states = []
    for _, block in fakes.blocks(x):
        engine.tick(block)
    s = engine.state()
    assert abs(s["rhythm"]["bpm"] - 128) < 2
    assert s["music"]["song_id"] == "demo_neon_drive" and s["music"]["confidence"] > 0.8
    assert s["m4"]["preset_song"] == "demo_neon_drive"
    assert len(s["fixtures"]) == engine.m2.n_fixtures
    assert len(s["universe"]) == 72
    assert s["latency"]["processing_ms"] < 20


def test_controls_are_validated(engine):
    engine.update_controls({"master": 5, "look": "nonsense", "blackout": 1, "not_a_field": 3})
    c = engine.controls
    assert c.master == 1.0 and c.look == "auto" and c.blackout is True
    engine.update_controls({"blackout": False})


def test_hello_lists_library_and_patch(engine):
    h = engine.hello()
    assert {s["song_id"] for s in h["library"]} >= {"demo_neon_drive", "demo_slow_bloom", "demo_breakbeat_140"}
    assert len(h["patch"]) == 8 and "auto" in h["looks"]
