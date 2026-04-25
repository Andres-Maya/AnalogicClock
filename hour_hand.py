"""
hour_hand.py
Concrete clock hand: completes one revolution every 12 hours.
"""

from __future__ import annotations

import datetime
from clock_hand import ClockHand


class HourHand(ClockHand):
    """
    Hour hand — completes one full revolution every 12 hours (43 200 s).

    Uses 720 ticks (one per 0.5°) for smooth analog motion.
    """

    _TICKS: int = 720

    def __init__(self) -> None:
        super().__init__(
            name="hour",
            tick_count=self._TICKS,
            length=0.50,
            width=7,
            color="#1a1a2e",
        )

    def angle_deg(self, now: datetime.datetime) -> float:
        total_seconds = (now.hour % 12) * 3600 + now.minute * 60 + now.second
        return (total_seconds / 43_200) * 360.0
