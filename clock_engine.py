"""
clock_engine.py
Domain model: builds the three clock hands (hours, minutes, seconds)
each backed by a CircularHandList, and computes their current angles.
"""

import math
import datetime
from circular_hand_list import CircularHandList


class ClockHand:
    """Abstract clock hand backed by a doubly circular linked list."""

    FULL_CIRCLE: float = 360.0
    TOP_OFFSET: float = -90.0          # 0° points right; we want 0° pointing up

    def __init__(self, name: str, tick_count: int, length: float, width: int, color: str):
        self.name: str = name
        self.length: float = length
        self.width: int = width
        self.color: str = color
        self._positions: CircularHandList = CircularHandList()
        self._build_positions(tick_count)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_positions(self, tick_count: int) -> None:
        """Populate the circular list with evenly-spaced degree positions."""
        step = self.FULL_CIRCLE / tick_count
        for i in range(tick_count):
            degree = i * step
            self._positions.append(degree)

    # ------------------------------------------------------------------
    # Angle computation (overridden per hand type)
    # ------------------------------------------------------------------

    def angle_deg(self, now: datetime.datetime) -> float:  # pragma: no cover
        raise NotImplementedError

    def angle_rad(self, now: datetime.datetime) -> float:
        deg = self.angle_deg(now) + self.TOP_OFFSET
        return math.radians(deg)

    # ------------------------------------------------------------------
    # Nearest-node query (uses the circular list)
    # ------------------------------------------------------------------

    def nearest_node(self, now: datetime.datetime) -> object:
        return self._positions.find_nearest(self.angle_deg(now))

    @property
    def positions(self) -> CircularHandList:
        return self._positions


# ------------------------------------------------------------------
# Concrete hands
# ------------------------------------------------------------------

class HourHand(ClockHand):
    """Hour hand: completes one revolution in 12 hours (43 200 s)."""

    TICKS = 720          # 1 tick per 0.5°  →  smooth motion

    def __init__(self):
        super().__init__(
            name="hour",
            tick_count=self.TICKS,
            length=0.50,
            width=7,
            color="#1a1a2e",
        )

    def angle_deg(self, now: datetime.datetime) -> float:
        total_seconds = (now.hour % 12) * 3600 + now.minute * 60 + now.second
        return (total_seconds / 43_200) * 360.0


class MinuteHand(ClockHand):
    """Minute hand: completes one revolution in 60 minutes (3 600 s)."""

    TICKS = 3_600        # 1 tick per 0.1°  →  very smooth motion

    def __init__(self):
        super().__init__(
            name="minute",
            tick_count=self.TICKS,
            length=0.72,
            width=5,
            color="#16213e",
        )

    def angle_deg(self, now: datetime.datetime) -> float:
        total_seconds = now.minute * 60 + now.second
        return (total_seconds / 3_600) * 360.0


class SecondHand(ClockHand):
    """Second hand: completes one revolution in 60 seconds."""

    TICKS = 60           # 1 tick per second (discrete jump)

    def __init__(self):
        super().__init__(
            name="second",
            tick_count=self.TICKS,
            length=0.82,
            width=2,
            color="#e94560",
        )

    def angle_deg(self, now: datetime.datetime) -> float:
        return (now.second / 60.0) * 360.0


# ------------------------------------------------------------------
# Clock engine aggregator
# ------------------------------------------------------------------

class ClockEngine:
    """
    Aggregates the three hands and provides a snapshot of angles
    for any given datetime.
    """

    def __init__(self):
        self.hour_hand: HourHand = HourHand()
        self.minute_hand: MinuteHand = MinuteHand()
        self.second_hand: SecondHand = SecondHand()

    @property
    def hands(self) -> list[ClockHand]:
        return [self.hour_hand, self.minute_hand, self.second_hand]

    def snapshot(self, now: datetime.datetime | None = None) -> dict:
        """Return {hand_name: angle_rad} for the given moment."""
        now = now or datetime.datetime.now()
        return {
            hand.name: hand.angle_rad(now)
            for hand in self.hands
        }

    def __repr__(self) -> str:
        info = [f"  {h.name}: {len(h.positions)} nodes" for h in self.hands]
        return "ClockEngine(\n" + "\n".join(info) + "\n)"
