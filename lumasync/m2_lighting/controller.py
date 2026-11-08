"""M2 mapping: LightIntent (what each light should look like) -> one DMX universe (512 bytes).

The patch file says which real light each logical fixture is, and at which DMX address.
The profile says what each of that light's channels does. Nothing else in the system knows
about channels, so a new rig is a new patch file, not new code.
-> decisions/117-lighting-patch-and-profiles.md

Colour and dimmer curves (decisions/118-lighting-colour-and-dimmer-curves.md):
  - FixtureIntent.rgb is a screen colour (sRGB, like a CSS colour). LEDs are linear: twice the
    DMX value gives about twice the light. So colour channels get the sRGB -> linear conversion,
    which keeps the light's colour close to the colour on the screen.
  - FixtureIntent.dimmer is perceptual (0.5 should LOOK half as bright). Eyes are roughly
    logarithmic, so the dimmer is raised to a gamma (2.2) before it becomes a DMX value.
Safety: FixtureIntent.strobe is ignored. Strobe and built-in-program channels are always sent at
the profile's "fixed" value (off), so a light can never flash by itself faster than the safety cap.
"""
from __future__ import annotations

import json
import os
from typing import Optional

import numpy as np

from lumasync.contract import LightIntent

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PATCH = os.path.join(HERE, "patch.json")
DEFAULT_PROFILES = os.path.join(HERE, "profiles.json")

COLOUR = {"red": 0, "green": 1, "blue": 2}
ALWAYS_FIXED = {"strobe", "program", "speed"}   # held at the fixed value even if a profile forgets


def _srgb_to_linear(c: np.ndarray) -> np.ndarray:
    c = np.clip(np.asarray(c, dtype=float), 0, 1)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _to_byte(v: float) -> int:
    return int(round(float(np.clip(v, 0.0, 1.0)) * 255))


class LightingController:
    def __init__(self, patch: dict, profiles: dict):
        self.profiles = {k: v for k, v in profiles.items() if not k.startswith("_")}
        self.fixtures = patch["fixtures"]
        self.warnings: list[str] = []
        self._validate()
        self.last_universe = bytearray(513)

    @classmethod
    def from_files(cls, patch_path: Optional[str] = None, profiles_path: Optional[str] = None) -> "LightingController":
        with open(patch_path or DEFAULT_PATCH) as fh:
            patch = json.load(fh)
        with open(profiles_path or DEFAULT_PROFILES) as fh:
            profiles = json.load(fh)
        return cls(patch, profiles)

    @property
    def n_fixtures(self) -> int:
        return len(self.fixtures)

    def _validate(self) -> None:
        used: dict[int, str] = {}
        for fx in self.fixtures:
            prof = self.profiles.get(fx["profile"])
            if prof is None:
                raise ValueError(f"{fx['name']}: unknown profile {fx['profile']!r}")
            addr = fx.get("address")
            if addr is None:
                continue
            last = addr + len(prof["channels"]) - 1
            if addr < 1 or last > 512:
                raise ValueError(f"{fx['name']}: channels {addr}-{last} outside 1-512")
            for ch in range(addr, last + 1):
                if ch in used:
                    self.warnings.append(f"channel {ch} used by both {used[ch]} and {fx['name']}")
                used[ch] = fx["name"]
            if not prof.get("verified", False):
                self.warnings.append(f"{fx['name']}: profile {fx['profile']} is UNVERIFIED")

    def process(self, intent: LightIntent) -> bytearray:
        """LightIntent -> 513 bytes: [start code 0] + channels 1..512."""
        uni = bytearray(513)
        for i, fx in enumerate(self.fixtures):
            addr = fx.get("address")
            if addr is None or i >= len(intent.fixtures):
                continue
            prof = self.profiles[fx["profile"]]
            fi = intent.fixtures[i]
            lin = _srgb_to_linear(fi.rgb)
            dim = float(np.clip(fi.dimmer, 0, 1)) ** prof.get("dimmer_gamma", 2.2)
            has_dimmer = "dimmer" in prof["channels"]
            colour = lin if has_dimmer else lin * dim
            fixed = prof.get("fixed", {})
            for k, name in enumerate(prof["channels"]):
                ch = addr + k
                if name in fixed:
                    uni[ch] = int(fixed[name])
                elif name in ALWAYS_FIXED:
                    uni[ch] = 0
                elif name == "dimmer":
                    uni[ch] = _to_byte(dim)
                elif name in COLOUR:
                    uni[ch] = _to_byte(colour[COLOUR[name]])
                elif name == "white" and prof.get("white_mode") == "min_rgb":
                    uni[ch] = _to_byte(colour.min())
                else:
                    uni[ch] = 0
        self.last_universe = uni
        return uni

    def preview(self, intent: LightIntent) -> list[dict]:
        """What the virtual fixtures in the UI show: the screen colour x dimmer."""
        out = []
        for i, fx in enumerate(self.fixtures):
            if i >= len(intent.fixtures):
                break
            fi = intent.fixtures[i]
            rgb = np.clip(np.array(fi.rgb) * float(np.clip(fi.dimmer, 0, 1)), 0, 1)
            out.append({
                "name": fx["name"],
                "hex": "#%02x%02x%02x" % tuple(int(round(c * 255)) for c in rgb),
                "colour": "#%02x%02x%02x" % tuple(int(round(c * 255)) for c in np.clip(fi.rgb, 0, 1)),
                "dimmer": round(float(fi.dimmer), 3),
                "address": fx.get("address"),
            })
        return out

    def describe(self) -> list[dict]:
        out = []
        for fx in self.fixtures:
            prof = self.profiles[fx["profile"]]
            out.append({"name": fx["name"], "profile": fx["profile"], "address": fx.get("address"),
                        "channels": prof["channels"], "verified": prof.get("verified", False)})
        return out

    def status(self) -> dict:
        return {"fixtures": len(self.fixtures), "warnings": self.warnings[:6]}
