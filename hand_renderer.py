"""
hand_renderer.py
Renders a single clock hand on a Tkinter canvas.
Supports multiple visual styles via the style parameter.
"""

from __future__ import annotations

import math
import tkinter as tk
from clock_hand import ClockHand

# Fallback colour constants (used when no style palette overrides them)
COL_FACE_SHADOW: str  = "#070714"
COL_SECOND_GLOW: str  = "#ff6080"

# Style-specific glow colours for the second hand
_SECOND_GLOW: dict[str, str] = {
    "default":    "#ff6080",
    "minimalist": "#ff4444",
    "python":     "#FFE873",
}

# Style-specific shadow colours
_HAND_SHADOW: dict[str, str] = {
    "default":    "#070714",
    "minimalist": "#cccccc",
    "python":     "#333333",
}


class HandRenderer:
    """
    Draws and redraws a single clock hand on a Tkinter canvas.

    Each renderer owns a unique canvas tag so it can erase only its
    own items before redrawing, leaving everything else untouched.
    """

    def __init__(
        self,
        canvas: tk.Canvas,
        hand: ClockHand,
        cx: int,
        cy: int,
        radius: int,
        style: str = "default",
    ) -> None:
        self._canvas = canvas
        self._hand = hand
        self._cx = cx
        self._cy = cy
        self._radius = radius
        self._style = style
        self._tag = f"hand_{hand.name}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def hand(self) -> ClockHand:
        return self._hand

    def set_style(self, style: str) -> None:
        """Switch the active visual style (takes effect on next draw)."""
        self._style = style

    def draw(self, angle_rad: float) -> None:
        """Erase the previous frame and redraw the hand at *angle_rad*."""
        self._canvas.delete(self._tag)

        length_px = int(self._radius * self._hand.length)
        end_x = self._cx + length_px * math.cos(angle_rad)
        end_y = self._cy + length_px * math.sin(angle_rad)

        self._draw_shadow(end_x, end_y)
        self._draw_body(end_x, end_y)

        if self._hand.name == "second":
            self._draw_second_accents(angle_rad, end_x, end_y)

    # ------------------------------------------------------------------
    # Private drawing helpers
    # ------------------------------------------------------------------

    def _draw_shadow(self, end_x: float, end_y: float) -> None:
        """Draw a subtle depth shadow (skipped for the thin second hand)."""
        if self._hand.name == "second":
            return
        shadow_color = _HAND_SHADOW.get(self._style, COL_FACE_SHADOW)
        self._canvas.create_line(
            self._cx + 2, self._cy + 2,
            end_x + 2, end_y + 2,
            fill=shadow_color,
            width=self._hand.width + 2,
            capstyle=tk.ROUND,
            tags=self._tag,
        )

    def _draw_body(self, end_x: float, end_y: float) -> None:
        """Draw the main hand line."""
        self._canvas.create_line(
            self._cx, self._cy, end_x, end_y,
            fill=self._hand.color,
            width=self._hand.width,
            capstyle=tk.ROUND,
            tags=self._tag,
        )

    def _draw_second_accents(
        self, angle_rad: float, end_x: float, end_y: float
    ) -> None:
        """Draw the glow overlay and counter-weight tail for the second hand."""
        glow_color = _SECOND_GLOW.get(self._style, COL_SECOND_GLOW)

        # Glow overlay
        self._canvas.create_line(
            self._cx, self._cy, end_x, end_y,
            fill=glow_color,
            width=1,
            capstyle=tk.ROUND,
            tags=self._tag,
        )
        # Counter-weight tail (opposite direction)
        tail_len = int(self._radius * 0.18)
        opp = angle_rad + math.pi
        self._canvas.create_line(
            self._cx, self._cy,
            self._cx + tail_len * math.cos(opp),
            self._cy + tail_len * math.sin(opp),
            fill=glow_color,
            width=2,
            capstyle=tk.ROUND,
            tags=self._tag,
        )
