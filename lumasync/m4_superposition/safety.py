"""Flash-rate safety cap: no more than 3 flashes in any 1-second window. Nothing bypasses it.

Why: flashing light at about 3-60 flashes per second can trigger seizures in people with
photosensitive epilepsy. WCAG 2.2 SC 2.3.1, ITU-R BT.1702 and the Epilepsy Foundation expert
consensus (Harding et al., 2005) all use "no more than 3 flashes in any 1 second".
-> decisions/006-flash-rate-cap.md (team rule) and decisions/114-superposition-flash-safety-cap.md

Definitions used here (conservative versions of the WCAG ones):
  brightness  y = dimmer * brightest colour channel (0..1). Using the brightest channel instead of
              luminance means a saturated red or blue flash counts fully. Saturated red carries
              extra risk, and luminance would under-count it.
  flash       a rise of at least DELTA (10 % of full) from the last dark point ("trough"),
              while that trough is below 0.8. WCAG counts a flash as a pair of opposite changes;
              counting every rise is stricter, because each flash must start with one.
  cap         a 4th rise inside any 1-second window is refused: the light is held just under
              trough + DELTA until the oldest rise leaves the window. Falling (getting darker) is
              always allowed, so blackout is never delayed.

How "nothing can bypass it" is enforced: SuperpositionEngine.process() applies this as its
LAST step, after every layer and every live control (including blackout and strobe). M2 holds
the fixtures' own hardware strobe and auto-program channels at their "off" values, so no light
can flash on its own either (decisions/117-lighting-patch-and-profiles.md).
"""
from __future__ import annotations

from collections import deque

import numpy as np

MAX_FLASHES_PER_S = 3
WINDOW_S = 1.0
DELTA = 0.10
DARK_LIMIT = 0.80


class FlashLimiter:
    """One brightness signal (one fixture, or the whole rig's average).

    Two steps per tick, so the state always follows what was REALLY shown:
      ceiling(t)   -> the brightest value allowed right now
      commit(t, y) -> record the value that was actually output (after every other clamp)
    """

    def __init__(self, max_flashes: int = MAX_FLASHES_PER_S, window_s: float = WINDOW_S,
                 delta: float = DELTA, dark_limit: float = DARK_LIMIT):
        self.max = max_flashes
        self.window = window_s
        self.delta = delta
        self.dark_limit = dark_limit
        self.rises: deque = deque()
        self.rising = False      # True after a counted rise, until a fall of >= delta
        self.trough = 0.0
        self.peak = 0.0

    def ceiling(self, t: float) -> float:
        while self.rises and t - self.rises[0] >= self.window:
            self.rises.popleft()
        if self.rising or self.trough >= self.dark_limit or len(self.rises) < self.max:
            return float("inf")
        return self.trough + self.delta * 0.95   # a 4th flash would start here: hold below it

    def commit(self, t: float, y: float) -> None:
        if self.rising:
            if y > self.peak:
                self.peak = y
            if y <= self.peak - self.delta:
                self.rising = False
                self.trough = y
            return
        if y < self.trough:
            self.trough = y
        if y >= self.trough + self.delta and self.trough < self.dark_limit:
            self.rises.append(t)     # ceiling() guarantees this is at most the 3rd in the window
            self.rising = True
            self.peak = y

    def step(self, t: float, y: float) -> float:
        out = min(y, self.ceiling(t))
        self.commit(t, out)
        return out


class RigFlashLimiter:
    """Applies the cap to every fixture AND to the rig average.

    Per fixture: each light is a large, bright source on its own.
    Rig average: many lights flashing in turn could still read as one flashing room.
    """

    def __init__(self, n: int, **kw):
        self.fixtures = [FlashLimiter(**kw) for _ in range(n)]
        self.rig = FlashLimiter(**kw)
        self._engaged_recent: deque = deque()

    def step(self, t: float, y: np.ndarray) -> np.ndarray:
        y = np.asarray(y, dtype=float)
        out = np.minimum(y, [lim.ceiling(t) for lim in self.fixtures])
        mean_req = float(out.mean()) if len(out) else 0.0
        cap = self.rig.ceiling(t)
        if mean_req > cap:
            out = out * (cap / mean_req)
        for lim, v in zip(self.fixtures, out):
            lim.commit(t, float(v))
        self.rig.commit(t, float(out.mean()) if len(out) else 0.0)
        if (out < y - 1e-9).any():
            self._engaged_recent.append(t)
        while self._engaged_recent and t - self._engaged_recent[0] > 1.0:
            self._engaged_recent.popleft()
        return out

    @property
    def engaged_last_s(self) -> int:
        """Ticks in the last second where the cap changed the output (shown in the UI)."""
        return len(self._engaged_recent)


def count_flashes(t: np.ndarray, y: np.ndarray, delta: float = DELTA, dark_limit: float = DARK_LIMIT) -> np.ndarray:
    """Independent checker for tests: times of every counted flash (rise) in a brightness trace."""
    rises = []
    rising, trough, peak = False, float("inf"), 0.0
    trough = y[0] if len(y) else 0.0
    for ti, yi in zip(t, y):
        if rising:
            peak = max(peak, yi)
            if yi <= peak - delta:
                rising, trough = False, yi
        else:
            trough = min(trough, yi)
            if yi >= trough + delta and trough < dark_limit:
                rises.append(ti)
                rising, peak = True, yi
    return np.array(rises)


def max_flashes_in_window(rise_times: np.ndarray, window: float = WINDOW_S) -> int:
    best = 0
    for i, t0 in enumerate(rise_times):
        best = max(best, int(np.sum((rise_times >= t0) & (rise_times < t0 + window))))
    return best
