"""
clock_hand.py
Abstract base class for a clock hand backed by a doubly circular linked list.
"""

from __future__ import annotations

import math
import datetime
from circular_hand_list import CircularHandList


class ClockHand:
    """
    Abstract base class for a clock hand.

    Each hand maintains a CircularHandList of evenly-spaced degree
    positions and exposes angle queries for any given datetime.

    Subclasses must implement :meth:`angle_deg`.
    """

    FULL_CIRCLE: float = 360.0
    TOP_OFFSET: float = -90.0  # Tkinter 0° points right; clock 0° points up.

    def __init__(
        self,
        name: str,
        tick_count: int,
        length: float,
        width: int,
        color: str,
    ) -> None:
        self.name: str = name
        self.length: float = length   # fraction of the clock radius
        self.width: int = width       # line width in pixels
        self.color: str = color
        self._positions: CircularHandList = CircularHandList()
        self._build_positions(tick_count)

    # ------------------------------------------------------------------
    # Internal builders
    # ------------------------------------------------------------------

    def _build_positions(self, tick_count: int) -> None:
        """Populate the circular list with *tick_count* evenly-spaced positions."""
        step = self.FULL_CIRCLE / tick_count
        for i in range(tick_count):
            self._positions.append(i * step)

    # ------------------------------------------------------------------
    # Angle computation (must be implemented by each subclass)
    # ------------------------------------------------------------------

    def angle_deg(self, now: datetime.datetime) -> float:
        """Return this hand's angular position in degrees for *now*."""
        raise NotImplementedError(
            f"{type(self).__name__} must implement angle_deg()."
        )

    def angle_rad(self, now: datetime.datetime) -> float:
        """Return the hand angle in radians, adjusted for canvas origin."""
        return math.radians(self.angle_deg(now) + self.TOP_OFFSET)

    def nearest_node(self, now: datetime.datetime) -> object:
        """Return the circular-list node closest to the current angle."""
        return self._positions.find_nearest(self.angle_deg(now))

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def positions(self) -> CircularHandList:
        """Read-only access to the underlying circular list."""
        return self._positions
