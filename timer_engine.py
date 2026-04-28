"""
timer_engine.py
Countdown timer engine: counts down from a configurable duration to zero.
"""

from __future__ import annotations

import time

from sound_manager import SoundManager


class TimerEngine:
    """
    Counts down from a configurable duration to zero.

    The alarm sound is delegated to a :class:`~sound_manager.SoundManager`
    instance, which is injected at construction time.  This keeps the
    timer logic free of any audio concerns (Dependency-Inversion Principle).

    Usage::

        sm = SoundManager()
        timer = TimerEngine(duration_sec=90, sound_manager=sm)
        timer.start()
        remaining = timer.get_remaining()
        if timer.is_finished():
            ...
        timer.pause()
        timer.reset()
        timer.set(120)   # change the duration
    """

    def __init__(
        self,
        duration_sec: float = 60.0,
        sound_manager: SoundManager | None = None,
    ) -> None:
        self._duration: float = duration_sec
        self._remaining: float = duration_sec
        self._end_time: float | None = None
        self._running: bool = False
        self._alarm_played: bool = False
        # Accept an externally-created SoundManager or create a default one
        self._sound_manager: SoundManager = sound_manager or SoundManager()

    # ------------------------------------------------------------------
    # Sound configuration
    # ------------------------------------------------------------------

    @property
    def sound_manager(self) -> SoundManager:
        """The :class:`~sound_manager.SoundManager` used for the alarm."""
        return self._sound_manager

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def set(self, duration_sec: float) -> None:
        """Set a new duration and stop/reset any active countdown."""
        self._duration = duration_sec
        self._remaining = duration_sec
        self._end_time = None
        self._running = False
        self._alarm_played = False

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start or resume the countdown (no-op if already finished)."""
        if not self._running and self._remaining > 0:
            self._end_time = time.time() + self._remaining
            self._running = True

    def pause(self) -> None:
        """Pause the countdown, preserving remaining time."""
        if self._running:
            self._remaining = max(0.0, self._end_time - time.time())  # type: ignore[operator]
            self._running = False

    def reset(self) -> None:
        """Stop and restore the countdown to its configured duration."""
        self._remaining = self._duration
        self._end_time = None
        self._running = False
        self._alarm_played = False

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_remaining(self) -> float:
        """Return the number of seconds remaining (never negative)."""
        if self._running:
            return max(0.0, self._end_time - time.time())  # type: ignore[operator]
        return self._remaining

    def is_running(self) -> bool:
        """Return ``True`` if the countdown is active."""
        return self._running

    def is_finished(self) -> bool:
        """Return ``True`` if the countdown has reached zero."""
        return self.get_remaining() <= 0

    def __repr__(self) -> str:
        state = "running" if self._running else "paused"
        return f"TimerEngine({state}, remaining={self.get_remaining():.2f}s)"
    
    def check_and_play_alarm(self) -> None:
        """
        Play the alarm once when the countdown first reaches zero.

        Subsequent calls while :attr:`is_finished` are no-ops until
        :meth:`reset` or :meth:`set` is called.
        """
        if self.is_finished() and not self._alarm_played:
            self._sound_manager.play()
            self._alarm_played = True

    def __repr__(self) -> str:
        state = "running" if self._running else "paused"
        return (
            f"TimerEngine({state}, remaining={self.get_remaining():.2f}s, "
            f"sound={self._sound_manager.selected_sound!r})"
        )
