"""
second_hand.py
Concrete clock hand: completes one revolution every 60 seconds.
"""

from __future__ import annotations

import datetime
from clock_hand import ClockHand


class SecondHand(ClockHand):
    """
    Second hand — completes one full revolution every 60 seconds.

    Uses 60 ticks (one per second) for a classic discrete sweep.
    """

    _TICKS: int = 60

    def __init__(self) -> None:
        super().__init__(
            name="second",
            tick_count=self._TICKS,
            length=0.82,
            width=2,
            color="#e94560",
        )

    def angle_deg(self, now: datetime.datetime) -> float:
        return (now.second / 60.0) * 360.0
