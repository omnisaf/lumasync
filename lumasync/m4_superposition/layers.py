"""M4 song layer: decides WHICH song preset is active, and fades between presets.

Two parts, kept separate so each can be tested and tuned alone:

SongSelector (hysteresis = different thresholds for switching on and off, so a signal that
hovers near one threshold does not flicker the state):
    lock on   : the same song at confidence >= 0.5, held for 1.5 s
    keep      : confidence >= 0.25 for the locked song counts as "still there"
    lose      : no good evidence for 5 s -> unlock (fade the preset out)
    switch    : a different song at >= 0.5, held for 2.5 s -> switch songs (longer than lock on,
                because a DJ blend has both songs playing for a while)
    manual    : the operator's manual_song_id always wins, at once
    -> decisions/113-superposition-song-state-and-transitions.md

PresetLayer (what changes, and how fast):
    The preset is NOT a second light show mixed on top. It is a set of PARAMETERS
    (palette, energy, strobe permission, blend) that steer the one reactive show.
    none -> A : palette set to A while invisible, then its weight fades in over 1.5 s
    A -> none : weight fades out over 2.5 s (slower: losing a song is less certain than finding it)
    A -> B    : palette and energy crossfade A -> B over 2 s in OKLab; weight stays up
    timing    : a change waits for the next beat (max 1 s) so it lands in time with the music;
                a detected drop makes it snap instantly (a drop is a natural hard cut);
                a manual pick starts at once with a short 0.6 s fade.
    -> decisions/111-superposition-blending-model.md
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from lumasync.contract import MusicContext, SongPreset

from .colour import lerp, palette_from_hex


def smoothstep(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


class SongSelector:
    def __init__(self, lock_conf: float = 0.5, keep_conf: float = 0.25, lock_hold_s: float = 1.5,
                 lose_hold_s: float = 5.0, switch_hold_s: float = 2.5):
        self.lock_conf, self.keep_conf = lock_conf, keep_conf
        self.lock_hold, self.lose_hold, self.switch_hold = lock_hold_s, lose_hold_s, switch_hold_s
        self.reset()

    def reset(self) -> None:
        self.active: Optional[str] = None
        self.candidate: Optional[str] = None
        self.candidate_since = 0.0
        self.last_good = 0.0
        self.state = "none"

    def update(self, t: float, music: MusicContext, manual_id: Optional[str], known: set) -> tuple[Optional[str], str]:
        sid = music.song_id if music.song_id in known else None
        conf = music.song_confidence if sid else 0.0

        # candidate tracking (a song other than the active one, seen strongly)
        if sid and sid != self.active and conf >= self.lock_conf:
            if self.candidate != sid:
                self.candidate, self.candidate_since = sid, t
        elif sid != self.candidate:
            self.candidate = None

        if self.active is None:
            if self.candidate and t - self.candidate_since >= self.lock_hold:
                self.active, self.last_good, self.candidate = self.candidate, t, None
                self.state = "locked"
            else:
                self.state = "candidate" if self.candidate else "none"
        else:
            if sid == self.active and conf >= self.keep_conf:
                self.last_good = t
                self.state = "locked"
            elif self.candidate and t - self.candidate_since >= self.switch_hold:
                self.active, self.last_good, self.candidate = self.candidate, t, None
                self.state = "locked"
            elif t - self.last_good >= self.lose_hold:
                self.active = None
                self.state = "none"
            else:
                self.state = "holding"   # evidence dropped; keep the preset for now

        if manual_id and manual_id in known:
            return manual_id, "manual"
        return self.active, self.state


class PresetLayer:
    def __init__(self, fade_in_s: float = 1.5, fade_out_s: float = 2.5, switch_s: float = 2.0,
                 manual_s: float = 0.6, max_wait_s: float = 1.0):
        self.fade_in, self.fade_out, self.switch, self.manual = fade_in_s, fade_out_s, switch_s, manual_s
        self.max_wait = max_wait_s
        self.reset()

    def reset(self) -> None:
        self.song_id: Optional[str] = None       # the preset currently shown (or fading out)
        self.goal_id: Optional[str] = None       # what the selector wants
        self.palette = palette_from_hex(["#ffffff"])
        self.energy = 0.5
        self.strobe = False
        self.blend: Optional[float] = None
        self.env = 0.0                            # 0..1 how present the preset is
        self._from = None
        self._to = None
        self._t0 = 0.0
        self._dur = 0.0
        self.pending_since: Optional[float] = None
        self.pending_reason = ""
        self.last_transition = ""

    def update(self, t: float, goal_id: Optional[str], preset: Optional[SongPreset], reason: str,
               beat: bool, drop: bool, tempo_locked: bool) -> None:
        if goal_id != self.goal_id:
            self.goal_id = goal_id
            self.pending_since = t
            self.pending_reason = reason
        if self.pending_since is not None:
            waited = t - self.pending_since
            snap = drop
            go = snap or beat or reason == "manual" or not tempo_locked or waited >= self.max_wait
            if go:
                self._start(t, preset, reason, snap)
                self.pending_since = None
        self._advance(t)

    def _snapshot(self):
        return dict(palette=self.palette.copy(), energy=self.energy, env=self.env,
                    blend=self.blend if self.blend is not None else -1.0)

    def _start(self, t: float, preset: Optional[SongPreset], reason: str, snap: bool) -> None:
        start = self._snapshot()
        if preset is None:               # A -> none
            target = dict(start, env=0.0)
            dur = self.fade_out
            kind = "fade out"
        else:
            pal = palette_from_hex(preset.palette)
            target = dict(palette=pal, energy=float(preset.energy), env=1.0,
                          blend=preset.blend if preset.blend is not None else -1.0)
            if self.env < 0.02:          # none -> A: change palette while invisible
                start = dict(start, palette=pal, energy=float(preset.energy), blend=target["blend"])
                self.palette, self.energy = pal.copy(), float(preset.energy)
                dur, kind = self.fade_in, "fade in"
            else:                        # A -> B
                dur, kind = self.switch, "crossfade"
            self.strobe = bool(preset.strobe)
            self.song_id = preset.song_id
        if reason == "manual":
            dur, kind = self.manual, kind + " (manual)"
        if snap:
            dur, kind = 0.0, kind + " (snap on drop)"
        self._from, self._to, self._t0, self._dur = start, target, t, dur
        self.last_transition = kind

    def _advance(self, t: float) -> None:
        if self._to is None:
            return
        p = 1.0 if self._dur <= 0 else smoothstep((t - self._t0) / self._dur)
        f, g = self._from, self._to
        self.palette = lerp(f["palette"], g["palette"], p)   # OKLab: straight-line blend
        self.energy = lerp(f["energy"], g["energy"], p)
        self.env = lerp(f["env"], g["env"], p)
        fb, gb = f["blend"], g["blend"]
        if fb < 0 and gb < 0:
            self.blend = None
        else:
            self.blend = gb if gb >= 0 else None
        if p >= 1.0:
            self._to = None
            if self.env <= 1e-3:
                self.env, self.song_id, self.strobe = 0.0, None, False

    def weight(self, live_blend: float) -> float:
        """How much the preset steers the show right now, 0..1."""
        b = self.blend if self.blend is not None else live_blend
        return float(np.clip(self.env * b, 0.0, 1.0))
