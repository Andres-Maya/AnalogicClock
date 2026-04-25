"""
clock_hand_node.py
Node for the doubly circular linked list that backs each clock hand.
"""

from __future__ import annotations


class ClockHandNode:
    """
    Represents a single tick/position in a clock hand's circular list.

    Attributes:
        degree: Angular position in degrees (0–359.x).
        label:  Optional human-readable label (e.g. "12", "3").
        next:   Forward pointer (circular).
        prev:   Backward pointer (circular).
    """

    def __init__(self, degree: float, label: str = "") -> None:
        self.degree: float = degree
        self.label: str = label
        self.next: ClockHandNode | None = None
        self.prev: ClockHandNode | None = None

    def __repr__(self) -> str:
        return f"ClockHandNode(degree={self.degree:.2f}, label={self.label!r})"
