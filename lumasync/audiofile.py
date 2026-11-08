"""Load an audio file into a numpy array. Shared plumbing, not a module.

M1 (file source) and M5 (fingerprinting) both need to read audio files. This helper holds no
state and knows nothing about either module, so sharing it does not couple them.

Formats: anything libsndfile reads (wav, flac, ogg, mp3). For other formats (m4a/aac from
Apple Music, for example) it converts through macOS `afconvert` or `ffmpeg` if present.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from math import gcd

import numpy as np


def _read_soundfile(path: str):
    import soundfile as sf

    data, sr = sf.read(path, dtype="float32", always_2d=True)
    return data, sr


def _convert_to_wav(path: str) -> str:
    """Convert an unsupported format to a temporary 16-bit wav. Returns the temp path."""
    fd, out = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    if shutil.which("afconvert"):
        cmd = ["afconvert", "-f", "WAVE", "-d", "LEI16", path, out]
    elif shutil.which("ffmpeg"):
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", path, out]
    else:
        raise RuntimeError(f"cannot read {path}: install ffmpeg or convert it to .wav")
    subprocess.run(cmd, check=True, capture_output=True)
    return out


def resample(x: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    """Polyphase resampling (scipy): filters out aliasing, exact for integer ratios."""
    if sr_in == sr_out:
        return x
    from scipy.signal import resample_poly

    g = gcd(int(sr_in), int(sr_out))
    return resample_poly(x, sr_out // g, sr_in // g, axis=0).astype(np.float32)


def load_audio(path: str, sr: int = 44100, mono: bool = False) -> np.ndarray:
    """Return float32 audio at `sr`. Shape (n,) if mono else (n, channels)."""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    try:
        data, file_sr = _read_soundfile(path)
    except Exception:
        tmp = _convert_to_wav(path)
        try:
            data, file_sr = _read_soundfile(tmp)
        finally:
            os.unlink(tmp)
    data = resample(data, file_sr, sr)
    if mono:
        return data.mean(axis=1).astype(np.float32)
    return data.astype(np.float32)


def save_wav(path: str, x: np.ndarray, sr: int = 44100) -> None:
    import soundfile as sf

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    sf.write(path, np.clip(x, -1, 1), sr, subtype="PCM_16")
