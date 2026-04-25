"""
clock_engine.py
Aggregates the three clock hands and produces per-tick angle snapshots.
"""

from __future__ import annotations

import datetime
from clock_hand import ClockHand
from hour_hand import HourHand
from minute_hand import MinuteHand
from second_hand import SecondHand


class ClockEngine:
    """
    Owns the three clock hands and exposes a single :meth:`snapshot` method
    that returns ``{hand_name: angle_in_radians}`` for any given moment.

    Usage::

        engine = ClockEngine()
        angles = engine.snapshot()               # uses datetime.now()
        angles = engine.snapshot(some_datetime)  # for a specific moment
    """

    def __init__(self) -> None:
        self.hour_hand: HourHand = HourHand()
        self.minute_hand: MinuteHand = MinuteHand()
        self.second_hand: SecondHand = SecondHand()

    @property
    def hands(self) -> list[ClockHand]:
        """All three hands in drawing order: hour → minute → second."""
        return [self.hour_hand, self.minute_hand, self.second_hand]

    def snapshot(self, now: datetime.datetime | None = None) -> dict[str, float]:
        """
        Return ``{hand_name: angle_in_radians}`` for the given moment.
        Defaults to ``datetime.datetime.now()`` when *now* is ``None``.
        """
        now = now or datetime.datetime.now()
        return {hand.name: hand.angle_rad(now) for hand in self.hands}

    def __repr__(self) -> str:
        lines = [f"  {h.name}: {len(h.positions)} nodes" for h in self.hands]
        return "ClockEngine(\n" + "\n".join(lines) + "\n)"
