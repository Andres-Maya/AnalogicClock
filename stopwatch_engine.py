"""
stopwatch_engine.py
Stopwatch engine: counts elapsed time upward from zero.
"""

from __future__ import annotations

import time


class StopwatchEngine:
    """
    Counts elapsed time upward from zero.

    Usage::

        sw = StopwatchEngine()
        sw.start()
        elapsed = sw.get_elapsed()
        sw.pause()
        sw.reset()
    """

    def __init__(self) -> None:
        self._start_time: float = 0.0
        self._elapsed: float = 0.0
        self._running: bool = False

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start or resume the stopwatch."""
        if not self._running:
            self._start_time = time.time() - self._elapsed
            self._running = True

    def pause(self) -> None:
        """Pause the stopwatch, preserving the elapsed time."""
        if self._running:
            self._elapsed = time.time() - self._start_time
            self._running = False

    def reset(self) -> None:
        """Stop and reset the stopwatch to zero."""
        self._start_time = 0.0
        self._elapsed = 0.0
        self._running = False

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_elapsed(self) -> float:
        """Return total elapsed seconds (including any paused periods)."""
        if self._running:
            return time.time() - self._start_time
        return self._elapsed

    def is_running(self) -> bool:
        """Return ``True`` if the stopwatch is currently counting."""
        return self._running

    def __repr__(self) -> str:
        state = "running" if self._running else "paused"
        return f"StopwatchEngine({state}, elapsed={self.get_elapsed():.2f}s)"
