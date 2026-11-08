"""Module 4: Superposition of Inputs and Latency Optimization.
AudioFrame + RhythmState + MusicContext + LiveControls + SongPresets in, LightIntent out."""
from .engine import LOOKS, SuperpositionEngine
from .safety import MAX_FLASHES_PER_S, FlashLimiter, RigFlashLimiter, count_flashes, max_flashes_in_window

__all__ = ["LOOKS", "SuperpositionEngine", "MAX_FLASHES_PER_S", "FlashLimiter", "RigFlashLimiter",
           "count_flashes", "max_flashes_in_window"]
