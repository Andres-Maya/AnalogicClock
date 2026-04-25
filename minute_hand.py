"""
minute_hand.py
Concrete clock hand: completes one revolution every 60 minutes.
"""

from __future__ import annotations

import datetime
from clock_hand import ClockHand


class MinuteHand(ClockHand):
    """
    Minute hand — completes one full revolution every 60 minutes (3 600 s).

    Uses 3 600 ticks (one per 0.1°) for very smooth analog motion.
    """

    _TICKS: int = 3_600

    def __init__(self) -> None:
        super().__init__(
            name="minute",
            tick_count=self._TICKS,
            length=0.72,
            width=5,
            color="#16213e",
        )

    def angle_deg(self, now: datetime.datetime) -> float:
        total_seconds = now.minute * 60 + now.second
        return (total_seconds / 3_600) * 360.0
