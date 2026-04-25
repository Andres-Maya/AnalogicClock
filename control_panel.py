"""
control_panel.py
Two-row control panel widget for the Analog Clock application.

Row 1 (always visible) — mode switcher: Clock | Stopwatch | Timer
Row 2 (context-sensitive) — action buttons that appear only for the
                            active mode (Stopwatch or Timer).
"""

from __future__ import annotations

from typing import Callable
import tkinter as tk

# Shared colour tokens
COL_BG: str    = "#0d0d1a"
COL_BTN: str   = "#1a1a3a"
COL_BTN_ON: str = "#2a2a5a"
COL_FG: str    = "#9090d0"
COL_NUM: str   = "#c8c8ff"


class ControlPanel:
    """
    Manages the two-row control area at the bottom of the clock window.

    The panel is packed at the bottom of *parent* using ``pack()``, so
    it never overlaps the canvas above it.
    """

    _MODES: tuple[str, ...] = ("Clock", "Stopwatch", "Timer")
    _BTN_W: int = 10  # uniform button character width

    def __init__(
        self,
        parent: tk.Widget,
        on_mode_change: Callable[[int], None],
        on_start: Callable[[], None],
        on_pause: Callable[[], None],
        on_reset: Callable[[], None],
        on_set_timer: Callable[[str], None],
    ) -> None:
        self._on_mode_change = on_mode_change
        self._on_start = on_start
        self._on_pause = on_pause
        self._on_reset = on_reset
        self._on_set_timer = on_set_timer
        self._current_mode: int = 0

        outer = tk.Frame(parent, bg=COL_BG)
        outer.pack(side=tk.BOTTOM, fill=tk.X, pady=(4, 8))

        self._build_row1(outer)
        self._build_row2(outer)
        self._refresh_row2()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_mode(self, mode_index: int) -> None:
        """Highlight the active mode button and refresh the action row."""
        self._current_mode = mode_index
        for idx, btn in enumerate(self._mode_buttons):
            active = idx == mode_index
            btn.config(
                bg=COL_BTN_ON if active else COL_BTN,
                relief=tk.SUNKEN if active else tk.FLAT,
            )
        self._refresh_row2()

    # ------------------------------------------------------------------
    # Row builders
    # ------------------------------------------------------------------

    def _build_row1(self, parent: tk.Frame) -> None:
        """Create the always-visible mode-switcher row."""
        row = tk.Frame(parent, bg=COL_BG)
        row.pack(pady=(0, 4))

        self._mode_buttons: list[tk.Button] = []
        for idx, label in enumerate(self._MODES):
            btn = tk.Button(
                row,
                text=label,
                width=self._BTN_W,
                command=lambda i=idx: self._on_mode_change(i),
                relief=tk.FLAT,
                bg=COL_BTN,
                fg=COL_FG,
                activebackground=COL_BTN_ON,
                activeforeground="#ffffff",
                cursor="hand2",
            )
            btn.pack(side=tk.LEFT, padx=3)
            self._mode_buttons.append(btn)

    def _build_row2(self, parent: tk.Frame) -> None:
        """Create the context-sensitive action row (initially empty)."""
        self._row2 = tk.Frame(parent, bg=COL_BG)
        self._row2.pack()

        btn_cfg = dict(
            width=self._BTN_W, relief=tk.FLAT,
            bg=COL_BTN, fg=COL_FG,
            activebackground=COL_BTN_ON, activeforeground="#ffffff",
            cursor="hand2",
        )

        self._entry_duration = tk.Entry(
            self._row2, width=8, justify="center",
            bg=COL_BTN, fg=COL_NUM, insertbackground=COL_NUM,
        )
        self._btn_set = tk.Button(
            self._row2, text="Set", width=5,
            command=self._handle_set,
            **{k: v for k, v in btn_cfg.items() if k != "width"},
        )
        self._btn_start = tk.Button(
            self._row2, text="Start",
            command=self._on_start, **btn_cfg,
        )
        self._btn_pause = tk.Button(
            self._row2, text="Pause",
            command=self._on_pause, **btn_cfg,
        )
        self._btn_reset = tk.Button(
            self._row2, text="Reset",
            command=self._on_reset, **btn_cfg,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _refresh_row2(self) -> None:
        """Show only the widgets relevant to the current mode."""
        for widget in self._row2.winfo_children():
            widget.pack_forget()

        if self._current_mode == 1:  # Stopwatch
            self._btn_start.pack(side=tk.LEFT, padx=3)
            self._btn_pause.pack(side=tk.LEFT, padx=3)
            self._btn_reset.pack(side=tk.LEFT, padx=3)

        elif self._current_mode == 2:  # Timer
            self._entry_duration.pack(side=tk.LEFT, padx=(0, 2))
            self._btn_set.pack(side=tk.LEFT, padx=(0, 4))
            self._btn_start.pack(side=tk.LEFT, padx=3)
            self._btn_pause.pack(side=tk.LEFT, padx=3)
            self._btn_reset.pack(side=tk.LEFT, padx=3)
        # Mode 0 (Clock): row 2 is intentionally empty.

    def _handle_set(self) -> None:
        self._on_set_timer(self._entry_duration.get().strip())
