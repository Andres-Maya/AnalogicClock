"""
circular_hand_list.py
Doubly circular linked list that stores the tick positions of a clock hand.
Each node holds a degree value and an optional label.
"""

from __future__ import annotations
from clock_hand_node import ClockHandNode


class CircularHandList:
    """
    Doubly circular linked list of clock hand degree positions.

    The list is always circular: the tail's ``next`` points back to the
    head and the head's ``prev`` points to the tail.  An internal
    ``_current`` cursor enables forward/backward traversal.
    """

    def __init__(self) -> None:
        self._head: ClockHandNode | None = None
        self._current: ClockHandNode | None = None
        self._size: int = 0

    # ------------------------------------------------------------------
    # Insertion
    # ------------------------------------------------------------------

    def append(self, degree: float, label: str = "") -> None:
        """Append a new node at the tail while keeping the list circular."""
        node = ClockHandNode(degree, label)

        if self._head is None:
            node.next = node
            node.prev = node
            self._head = node
            self._current = node
        else:
            tail = self._head.prev  # type: ignore[assignment]
            tail.next = node
            node.prev = tail
            node.next = self._head
            self._head.prev = node

        self._size += 1

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def find_nearest(self, degree: float) -> ClockHandNode:
        """
        Walk the list and return the node whose degree is closest to
        *degree*.  Updates the internal ``_current`` cursor.

        Raises:
            ValueError: If the list is empty.
        """
        if self._head is None:
            raise ValueError("Cannot search an empty CircularHandList.")

        best: ClockHandNode = self._head
        best_diff: float = abs(best.degree - degree)

        node: ClockHandNode = self._head.next  # type: ignore[assignment]
        while node is not self._head:
            diff = abs(node.degree - degree)
            if diff < best_diff:
                best_diff = diff
                best = node
            node = node.next  # type: ignore[assignment]

        self._current = best
        return best

    def advance(self) -> ClockHandNode | None:
        """Move the cursor one step forward (circular) and return it."""
        if self._current is not None:
            self._current = self._current.next  # type: ignore[assignment]
        return self._current

    def retreat(self) -> ClockHandNode | None:
        """Move the cursor one step backward (circular) and return it."""
        if self._current is not None:
            self._current = self._current.prev  # type: ignore[assignment]
        return self._current

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return self._size

    def __iter__(self):
        """Iterate every node exactly once (head → … → tail)."""
        if self._head is None:
            return
        node: ClockHandNode = self._head
        while True:
            yield node
            node = node.next  # type: ignore[assignment]
            if node is self._head:
                break

    def __repr__(self) -> str:
        nodes = [f"{n.degree:.1f}°" for n in self]
        return f"CircularHandList([{' ↔ '.join(nodes)}] ↺)"
