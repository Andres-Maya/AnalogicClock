"""
clock_hand.py
Doubly Circular Linked List node representing a clock hand tick.
"""


class ClockHandNode:
    """Represents a single tick/position node in a clock hand's circular list."""

    def __init__(self, degree: float, label: str = ""):
        self.degree: float = degree
        self.label: str = label
        self.next: "ClockHandNode | None" = None
        self.prev: "ClockHandNode | None" = None

    def __repr__(self) -> str:
        return f"ClockHandNode(degree={self.degree:.2f}, label='{self.label}')"
