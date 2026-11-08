"""Colour maths for M4. Palettes are blended in OKLab.

OKLab (B. Ottosson, 2020) is a "perceptual" colour space: equal steps in it look like equal
steps to a person. L = lightness, a = green..red, b = blue..yellow.

Why not blend in RGB? Halfway between red (1,0,0) and green (0,1,0) in RGB is (0.5,0.5,0), a
muddy dark olive: the blend dips in brightness. In OKLab the halfway point keeps its lightness.
Why not HSV? Hue is an angle, so blending must pick a direction round the wheel, and HSV
lightness is not perceptual (yellow and blue at the same "V" look very different).
-> decisions/112-superposition-colour-space.md
"""
from __future__ import annotations

import numpy as np

_M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005]])
_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                [1.9779984951, -2.4285922050, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.8086757660]])
_M2i = np.array([[1.0, 0.3963377774, 0.2158037573],
                 [1.0, -0.1055613458, -0.0638541728],
                 [1.0, -0.0894841775, -1.2914855480]])
_M1i = np.array([[4.0767416621, -3.3077115913, 0.2309699292],
                 [-1.2684380046, 2.6097574011, -0.3413193965],
                 [-0.0041960863, -0.7034186147, 1.7076147010]])


def hex_to_srgb(h: str) -> np.ndarray:
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def srgb_to_hex(rgb) -> str:
    r, g, b = (int(round(float(np.clip(c, 0, 1)) * 255)) for c in rgb)
    return f"#{r:02x}{g:02x}{b:02x}"


def srgb_to_linear(c: np.ndarray) -> np.ndarray:
    c = np.asarray(c, dtype=float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c: np.ndarray) -> np.ndarray:
    c = np.clip(np.asarray(c, dtype=float), 0, None)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def srgb_to_oklab(rgb: np.ndarray) -> np.ndarray:
    lin = srgb_to_linear(rgb)
    lms = np.cbrt(lin @ _M1.T)
    return lms @ _M2.T


def oklab_to_srgb(lab: np.ndarray) -> np.ndarray:
    lms = (np.asarray(lab, dtype=float) @ _M2i.T) ** 3
    lin = lms @ _M1i.T
    return np.clip(linear_to_srgb(np.clip(lin, 0, 1)), 0, 1)


def oklch_to_oklab(L: float, C: float, h_deg: float) -> np.ndarray:
    h = np.radians(h_deg)
    return np.array([L, C * np.cos(h), C * np.sin(h)])


def lerp(a, b, w):
    return a + (b - a) * w


def palette_from_hex(colours: list[str], n: int = 3) -> np.ndarray:
    """2-3 hex colours -> (n, 3) OKLab. A 2-colour palette gets its OKLab midpoint as 3rd colour."""
    labs = [srgb_to_oklab(hex_to_srgb(c)) for c in colours[:n]] or [srgb_to_oklab(np.ones(3))]
    while len(labs) < n:
        labs.append(lerp(labs[0], labs[-1], 0.5) if len(labs) >= 2 else labs[0])
    return np.array(labs[:n])


def palette_at(palette: np.ndarray, x: float) -> np.ndarray:
    """Smooth gradient through the palette colours, x in 0..1."""
    k = len(palette) - 1
    if k <= 0:
        return palette[0]
    x = float(np.clip(x, 0, 1)) * k
    i = min(int(x), k - 1)
    return lerp(palette[i], palette[i + 1], x - i)


def fixture_colour(lab: np.ndarray) -> np.ndarray:
    """OKLab -> sRGB with the brightest channel scaled to 1.

    A light's colour (hue + saturation) and its brightness (dimmer) are separate controls, so the
    colour is normalised and brightness is carried by the dimmer.
    """
    rgb = oklab_to_srgb(lab)
    m = rgb.max()
    return rgb / m if m > 1e-6 else np.ones(3)
