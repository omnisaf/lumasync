"""The song library: library/songs.json (presets) + library/audio/ (audio, not in git) +
library/index/ (fingerprint index, generated). App plumbing, not a module.

M4 gets the presets (SongPreset). M5 gets (song_id, audio path) pairs to fingerprint.
Neither module reads this file directly, so the library format can change without touching them.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import threading
from dataclasses import asdict, fields
from typing import Optional

from lumasync.contract import SongPreset

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_DIR = os.path.join(REPO, "library")
SONGS_JSON = os.path.join(LIB_DIR, "songs.json")
AUDIO_DIR = os.path.join(LIB_DIR, "audio")
INDEX_DIR = os.path.join(LIB_DIR, "index")
AUDIO_EXT = (".wav", ".mp3", ".flac", ".ogg", ".aif", ".aiff", ".m4a", ".aac")

# The synthetic demo tracks: regenerated from these settings if missing (audio is gitignored).
DEMO_AUDIO = {
    "demo_neon_drive.wav": dict(style="neon_drive", seconds=45.0, seed=1),
    "demo_slow_bloom.wav": dict(style="slow_bloom", seconds=40.0, seed=2),
    "demo_breakbeat_140.wav": dict(style="breakbeat_140", seconds=40.0, seed=3),
}

_PRESET_FIELDS = {f.name for f in fields(SongPreset)}


def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return s or "song"


def resolve(path: Optional[str]) -> Optional[str]:
    """Library paths are stored relative to the repo root so the repo can move."""
    if not path:
        return None
    p = os.path.expanduser(path)
    return p if os.path.isabs(p) else os.path.join(REPO, p)


def relative(path: str) -> str:
    ap = os.path.abspath(os.path.expanduser(path))
    return os.path.relpath(ap, REPO) if ap.startswith(REPO + os.sep) else ap


def ensure_demo_audio(log=print) -> list[str]:
    """Generate any missing demo .wav files. Deterministic, ~1 s each."""
    made = []
    for name, cfg in DEMO_AUDIO.items():
        path = os.path.join(AUDIO_DIR, name)
        if os.path.exists(path):
            continue
        from lumasync.audiofile import save_wav
        from lumasync.fakes import synth_song

        log(f"[library] generating demo track {name} ...")
        save_wav(path, synth_song(cfg["style"], cfg["seconds"], seed=cfg["seed"]))
        made.append(path)
    return made


class SongLibrary:
    def __init__(self, path: str = SONGS_JSON):
        self.path = path
        self._lock = threading.Lock()
        self.songs: list[dict] = []
        self.load()

    def load(self) -> None:
        with self._lock:
            if os.path.exists(self.path):
                with open(self.path) as fh:
                    data = json.load(fh)
                self.songs = data.get("songs", data if isinstance(data, list) else [])
            else:
                self.songs = []

    def save(self) -> None:
        with self._lock:
            tmp = self.path + ".tmp"
            with open(tmp, "w") as fh:
                json.dump({"songs": self.songs}, fh, indent=2)
            os.replace(tmp, self.path)

    def presets(self) -> dict[str, SongPreset]:
        out = {}
        for s in self.songs:
            kw = {k: v for k, v in s.items() if k in _PRESET_FIELDS}
            out[s["song_id"]] = SongPreset(**kw)
        return out

    def fingerprint_list(self) -> list[tuple[str, str]]:
        out = []
        for s in self.songs:
            p = resolve(s.get("audio_file"))
            if p and os.path.exists(p):
                out.append((s["song_id"], p))
        return out

    def get(self, song_id: str) -> Optional[dict]:
        return next((s for s in self.songs if s["song_id"] == song_id), None)

    def upsert(self, song: dict, copy_audio: bool = True) -> str:
        """Add or update a song. Audio outside library/audio is copied in (keeps the library
        self-contained). Returns the song_id."""
        title = (song.get("title") or "").strip() or "Untitled"
        sid = song.get("song_id") or slugify(title)
        existing = self.get(sid)
        if existing is None and song.get("song_id") is None:
            base, k = sid, 2
            while self.get(sid):
                sid, k = f"{base}_{k}", k + 1
        audio = song.get("audio_file")
        if audio:
            ap = resolve(audio)
            if not os.path.exists(ap):
                raise FileNotFoundError(f"audio file not found: {audio}")
            if not ap.lower().endswith(AUDIO_EXT):
                raise ValueError(f"not an audio file: {audio}")
            if copy_audio and not os.path.abspath(ap).startswith(AUDIO_DIR + os.sep):
                os.makedirs(AUDIO_DIR, exist_ok=True)
                dest = os.path.join(AUDIO_DIR, os.path.basename(ap))
                if not os.path.exists(dest):
                    shutil.copy2(ap, dest)
                ap = dest
            audio = relative(ap)
        palette = [c for c in (song.get("palette") or []) if isinstance(c, str) and re.fullmatch(r"#?[0-9a-fA-F]{6}", c)]
        palette = [c if c.startswith("#") else "#" + c for c in palette][:3] or ["#ff0040", "#4000ff"]
        blend = song.get("blend")
        rec = {
            "song_id": sid,
            "title": title,
            "artist": (song.get("artist") or "").strip(),
            "palette": palette,
            "energy": float(min(max(float(song.get("energy", 0.7)), 0.0), 1.0)),
            "strobe": bool(song.get("strobe", False)),
            "blend": None if blend in (None, "", "live") else float(min(max(float(blend), 0.0), 1.0)),
            "audio_file": audio,
        }
        with self._lock:
            for i, s in enumerate(self.songs):
                if s["song_id"] == sid:
                    self.songs[i] = rec
                    break
            else:
                self.songs.append(rec)
        self.save()
        return sid

    def delete(self, song_id: str) -> None:
        with self._lock:
            self.songs = [s for s in self.songs if s["song_id"] != song_id]
        self.save()

    def audio_files(self) -> list[str]:
        if not os.path.isdir(AUDIO_DIR):
            return []
        return sorted(relative(os.path.join(AUDIO_DIR, f)) for f in os.listdir(AUDIO_DIR)
                      if f.lower().endswith(AUDIO_EXT))

    def as_json(self) -> list[dict]:
        return [dict(s) for s in self.songs]


def preset_dict(p: SongPreset) -> dict:
    return asdict(p)
