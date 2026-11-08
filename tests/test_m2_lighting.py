"""M2 alone: fake LightIntents in, exact DMX bytes checked."""
import pytest

from lumasync import fakes
from lumasync.contract import FixtureIntent, LightIntent
from lumasync.m2_lighting import DmxOutput, LightingController, SacnOutput
from lumasync.m2_lighting.controller import DEFAULT_PROFILES
import json

PROFILES = json.load(open(DEFAULT_PROFILES))


def ctl(fixtures):
    return LightingController({"fixtures": fixtures}, PROFILES)


def one(rgb, dimmer, strobe=0.0):
    return LightIntent(t=0, fixtures=[FixtureIntent(rgb=rgb, dimmer=dimmer, strobe=strobe)])


def test_generic_rgb_full_red():
    u = ctl([{"name": "A", "profile": "generic_rgb_3ch", "address": 1}]).process(one((1, 0, 0), 1.0))
    assert len(u) == 513 and u[0] == 0
    assert list(u[1:4]) == [255, 0, 0]


def test_generic_rgb_dimmer_goes_into_colour_with_gamma():
    u = ctl([{"name": "A", "profile": "generic_rgb_3ch", "address": 10}]).process(one((1, 1, 1), 0.5))
    assert list(u[10:13]) == [55, 55, 55]          # 0.5 ** 2.2 * 255 = 55.5


def test_srgb_colour_is_linearised():
    u = ctl([{"name": "A", "profile": "generic_drgb_4ch", "address": 1}]).process(one((1, 0.5, 0), 1.0))
    assert list(u[1:5]) == [255, 255, 55, 0]       # sRGB 0.5 -> linear 0.214 -> 55


def test_betopper_guess_layout_and_safety_channels():
    c = ctl([{"name": "P", "profile": "betopper_lpc1818_7ch_guess", "address": 1}])
    u = c.process(one((0, 0, 1), 1.0, strobe=1.0))   # strobe requested: must be ignored
    assert list(u[1:8]) == [255, 0, 0, 255, 0, 0, 0]  # dimmer, R, G, B, W, strobe=0, program=0


def test_lpc1818_11ch_holds_program_channel_at_zero():
    u = ctl([{"name": "P", "profile": "betopper_lpc1818_11ch_manual", "address": 1}]).process(one((1, 1, 1), 1.0, 1.0))
    assert u[9] == 0 and u[8] == 0                   # program (ch 9) and strobe (ch 8)


def test_default_patch_maps_eight_fixtures():
    c = LightingController.from_files()
    assert c.n_fixtures == 8
    u = c.process(fakes.fake_light_intent(8))
    for addr in (1, 11, 21, 31, 41, 51, 61, 71):
        assert u[addr] == 255                         # dimmer channel of each par
    assert any("UNVERIFIED" in w for w in c.warnings)


def test_overlap_is_reported():
    c = ctl([{"name": "A", "profile": "generic_rgb_3ch", "address": 1},
             {"name": "B", "profile": "generic_rgb_3ch", "address": 3}])
    assert any("channel 3" in w for w in c.warnings)


def test_out_of_range_address_rejected():
    with pytest.raises(ValueError):
        ctl([{"name": "A", "profile": "generic_rgb_3ch", "address": 511}])


def test_preview_colour():
    p = ctl([{"name": "A", "profile": "generic_rgb_3ch", "address": None}]).preview(one((1, 0, 0), 0.5))
    assert p[0]["hex"] == "#800000" and p[0]["address"] is None


def test_dmx_output_without_cable_is_graceful():
    d = DmxOutput(enabled=True, port="/dev/cu.usbserial-DOES-NOT-EXIST", rescan_s=0.05)
    d.start()
    d.set_frame(bytearray(513))
    import time
    time.sleep(0.2)
    d.stop()
    assert d.status()["state"] == "searching" and d.frames_sent == 0


def test_sacn_is_a_stub():
    with pytest.raises(NotImplementedError):
        SacnOutput().start()
