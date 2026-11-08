"""Module 5: Machine Learning: Mood (+ music recognition). AudioFrame in, MusicContext out.

Two parts:
  - song recognition by audio fingerprint (fingerprint.py, recognizer.py)
  - mood estimate, currently a PLACEHOLDER heuristic (mood.py), to be replaced by a trained model
Whether this module is renamed "Machine Learning: Music Recognition and Mood Estimation" is an
open team question: decisions/109-m5-recognition-confidence-and-schedule.md.
"""
from .fingerprint import FingerprintIndex, MatchResult
from .mood import MoodEstimator
from .recognizer import RecognitionModule, build_index

__all__ = ["FingerprintIndex", "MatchResult", "MoodEstimator", "RecognitionModule", "build_index"]
