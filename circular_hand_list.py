"""
circular_hand_list.py
Doubly Circular Linked List that stores the tick positions of a clock hand.
Each node holds a degree value and an optional label (e.g. "12", "3", "6", "9").
"""

from clock_hand import ClockHandNode


class CircularHandList:
    """Doubly circular linked list of clock hand degree positions."""

    def __init__(self):
        self._head: ClockHandNode | None = None
        self._size: int = 0
        self._current: ClockHandNode | None = None

    # ------------------------------------------------------------------
    # Core insert
    # ------------------------------------------------------------------

    def append(self, degree: float, label: str = "") -> None:
        """Append a new node at the tail, keeping the list circular."""
        node = ClockHandNode(degree, label)

        if self._head is None:
            # Single-node circle
            node.next = node
            node.prev = node
            self._head = node
            self._current = node
        else:
            tail = self._head.prev          # last node
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
        Walk the list and return the node whose degree is closest
        to the requested value.
        """
        if self._head is None:
            raise ValueError("Empty list.")

        best = self._head
        best_diff = abs(best.degree - degree)

        node = self._head.next
        while node is not self._head:
            diff = abs(node.degree - degree)
            if diff < best_diff:
                best_diff = diff
                best = node
            node = node.next

        self._current = best
        return best

    def advance(self) -> ClockHandNode:
        """Move current pointer one step forward (circular)."""
        if self._current is not None:
            self._current = self._current.next
        return self._current

    def retreat(self) -> ClockHandNode:
        """Move current pointer one step backward (circular)."""
        if self._current is not None:
            self._current = self._current.prev
        return self._current

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return self._size

    def __iter__(self):
        if self._head is None:
            return
        node = self._head
        while True:
            yield node
            node = node.next
            if node is self._head:
                break

    def __repr__(self) -> str:
        nodes = [f"{n.degree:.1f}°" for n in self]
        return f"CircularHandList([{' ↔ '.join(nodes)}] ↺)"
