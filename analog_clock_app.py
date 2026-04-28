"""
analog_clock_app.py
Main application class for the Analog Clock.

Wires together the canvas, hand renderers, control panel,
and the 50 ms repaint loop.
"""

from __future__ import annotations

import math
import datetime
import tkinter as tk

from clock_engine import ClockEngine
from stopwatch_engine import StopwatchEngine
from timer_engine import TimerEngine
from hand_renderer import HandRenderer
from control_panel import ControlPanel
from sound_manager import SoundManager

# ── Layout & palette ──────────────────────────────────────────────────────────
WINDOW_W: int      = 520
WINDOW_H: int      = 680
CLOCK_RADIUS: int  = 210
CENTER_X: int      = WINDOW_W // 2
CENTER_Y: int      = WINDOW_H // 2 - 60

COL_BG: str           = "#0d0d1a"
COL_FACE: str         = "#12122a"
COL_FACE_BORDER: str  = "#2a2a5a"
COL_FACE_SHADOW: str  = "#070714"
COL_TICK_HOUR: str    = "#e8e8ff"
COL_TICK_MIN: str     = "#4a4a8a"
COL_NUMBER: str       = "#c8c8ff"
COL_CENTER: str       = "#e94560"
COL_DIGITAL: str      = "#6a6aaa"
COL_TITLE: str        = "#9090d0"
COL_SUBTITLE: str     = "#5a5a9a"

REPAINT_MS: int = 50  # ≈ 20 fps


def _darken(hex_color: str, amount: int) -> str:
    """Return a darker hex colour by subtracting *amount* from each RGB channel."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i: i + 2], 16) for i in (0, 2, 4))
    return f"#{max(0, r - amount):02x}{max(0, g - amount):02x}{max(0, b - amount):02x}"


class AnalogClockApp:
    """
    Main application window for the Analog Clock.

    Modes
    -----
    0 — Clock      : displays the current system time.
    1 — Stopwatch  : counts elapsed time upward.
    2 — Timer      : counts down from a user-defined duration.
    """

    _MONTHS: list[str] = [
        "", "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    _WEEKDAYS: list[str] = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday",
    ]

    def __init__(self) -> None:
        self._engine = ClockEngine()
        self._stopwatch = StopwatchEngine()
        self._sound_manager = SoundManager()
        self._timer = TimerEngine(duration_sec=60, sound_manager=self._sound_manager)
        self._mode: int = 0

        self._root = tk.Tk()
        self._canvas: tk.Canvas
        self._hand_renderers: list[HandRenderer] = []
        self._digital_text_id: int = -1
        self._date_text_id: int = -1

        self._build_window()
        self._build_static_face()
        self._build_hand_renderers()
        self._build_control_panel()

        self._root.bind("1", lambda _: self._change_mode(0))
        self._root.bind("2", lambda _: self._change_mode(1))
        self._root.bind("3", lambda _: self._change_mode(2))

    # ------------------------------------------------------------------
    # Window & canvas
    # ------------------------------------------------------------------

    def _build_window(self) -> None:
        self._root.title("Analog Clock — Doubly Circular Linked List")
        self._root.resizable(False, False)
        self._root.configure(bg=COL_BG)

        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        self._root.geometry(
            f"{WINDOW_W}x{WINDOW_H}"
            f"+{(sw - WINDOW_W) // 2}+{(sh - WINDOW_H) // 2}"
        )

        self._canvas = tk.Canvas(
            self._root,
            width=WINDOW_W,
            height=WINDOW_H - 90,
            bg=COL_BG,
            highlightthickness=0,
        )
        self._canvas.pack(side=tk.TOP)

    # ------------------------------------------------------------------
    # Static face
    # ------------------------------------------------------------------

    def _build_static_face(self) -> None:
        c = self._canvas

        c.create_text(CENTER_X, 28, text="⟳  ANALOG CLOCK",
                      fill=COL_TITLE, font=("Courier", 15, "bold"))
        c.create_text(CENTER_X, 50,
                      text="Doubly Circular Linked List  •  Python",
                      fill=COL_SUBTITLE, font=("Courier", 9))

        for i in range(5, 0, -1):
            c.create_oval(
                CENTER_X - CLOCK_RADIUS - i * 3,
                CENTER_Y - CLOCK_RADIUS - i * 3,
                CENTER_X + CLOCK_RADIUS + i * 3,
                CENTER_Y + CLOCK_RADIUS + i * 3,
                outline=_darken(COL_FACE_BORDER, i * 18), width=1,
            )

        c.create_oval(
            CENTER_X - CLOCK_RADIUS, CENTER_Y - CLOCK_RADIUS,
            CENTER_X + CLOCK_RADIUS, CENTER_Y + CLOCK_RADIUS,
            fill=COL_FACE, outline=COL_FACE_BORDER, width=3,
        )

        for tick in range(60):
            angle = math.radians(tick * 6 - 90)
            is_hour = tick % 5 == 0
            outer_r = CLOCK_RADIUS - 4
            inner_r = CLOCK_RADIUS - (18 if is_hour else 8)
            c.create_line(
                CENTER_X + outer_r * math.cos(angle),
                CENTER_Y + outer_r * math.sin(angle),
                CENTER_X + inner_r * math.cos(angle),
                CENTER_Y + inner_r * math.sin(angle),
                fill=COL_TICK_HOUR if is_hour else COL_TICK_MIN,
                width=3 if is_hour else 1,
            )

        num_r = CLOCK_RADIUS - 40
        for hour in range(1, 13):
            a = math.radians(hour * 30 - 90)
            c.create_text(
                CENTER_X + num_r * math.cos(a),
                CENTER_Y + num_r * math.sin(a),
                text=str(hour), fill=COL_NUMBER,
                font=("Courier", 12, "bold"),
            )

        deco_r = CLOCK_RADIUS - 55
        c.create_oval(
            CENTER_X - deco_r, CENTER_Y - deco_r,
            CENTER_X + deco_r, CENTER_Y + deco_r,
            outline=COL_FACE_BORDER, width=1, dash=(3, 8),
        )

        c.create_text(CENTER_X, CENTER_Y - CLOCK_RADIUS // 2 + 10,
                      text="CLOCK", fill=COL_SUBTITLE,
                      font=("Courier", 8, "bold"))

        self._digital_text_id = c.create_text(
            CENTER_X, CENTER_Y + CLOCK_RADIUS // 2 - 18,
            text="--:--:--", fill=COL_DIGITAL,
            font=("Courier", 16, "bold"),
        )
        self._date_text_id = c.create_text(
            CENTER_X, CENTER_Y + CLOCK_RADIUS // 2 + 8,
            text="", fill=COL_SUBTITLE, font=("Courier", 9),
        )

        # Hand legend
        bottom_y = WINDOW_H - 90
        for lx, lcolor, ltext in [
            (130, "#1a1a2e", "Hour"),
            (230, "#16213e", "Minute"),
            (330, "#e94560", "Second"),
        ]:
            by = bottom_y - 12
            c.create_oval(lx - 5, by - 5, lx + 5, by + 5,
                          fill=lcolor, outline=COL_FACE_BORDER)
            c.create_text(lx + 22, by, text=ltext,
                          fill=COL_SUBTITLE, font=("Courier", 8))

    # ------------------------------------------------------------------
    # Hand renderers
    # ------------------------------------------------------------------

    def _build_hand_renderers(self) -> None:
        for hand in self._engine.hands:
            self._hand_renderers.append(
                HandRenderer(
                    canvas=self._canvas,
                    hand=hand,
                    cx=CENTER_X,
                    cy=CENTER_Y,
                    radius=CLOCK_RADIUS,
                )
            )

    # ------------------------------------------------------------------
    # Control panel
    # ------------------------------------------------------------------

    def _build_control_panel(self) -> None:
        self._controls = ControlPanel(
            parent=self._root,
            on_mode_change=self._change_mode,
            on_start=self._action_start,
            on_pause=self._action_pause,
            on_reset=self._action_reset,
            on_set_timer=self._action_set_timer,
            sound_manager=self._sound_manager,
        )

    # ------------------------------------------------------------------
    # Mode & action handlers
    # ------------------------------------------------------------------

    def _change_mode(self, mode_index: int) -> None:
        self._mode = mode_index
        self._controls.set_mode(mode_index)
        if mode_index == 1:
            self._stopwatch.reset()
        elif mode_index == 2:
            self._timer.reset()

    def _action_start(self) -> None:
        if self._mode == 1:
            self._stopwatch.start()
        elif self._mode == 2:
            self._timer.start()

    def _action_pause(self) -> None:
        if self._mode == 1:
            self._stopwatch.pause()
        elif self._mode == 2:
            self._timer.pause()

    def _action_reset(self) -> None:
        if self._mode == 1:
            self._stopwatch.reset()
        elif self._mode == 2:
            self._timer.reset()

    def _action_set_timer(self, raw_text: str) -> None:
        """Parse HH:MM:SS / MM:SS / SS and configure the timer engine."""
        try:
            parts = [int(x) for x in raw_text.split(":")]
            if len(parts) == 3:
                total = parts[0] * 3600 + parts[1] * 60 + parts[2]
            elif len(parts) == 2:
                total = parts[0] * 60 + parts[1]
            elif len(parts) == 1:
                total = parts[0]
            else:
                return
            if total > 0:
                self._timer.set(total)
        except ValueError:
            pass

    # ------------------------------------------------------------------
    # Repaint loop
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        """Recompute angles, redraw hands, and update all dynamic text."""
        if self._mode == 0:
            now = datetime.datetime.now()
            angles = self._engine.snapshot(now)
            digital_text = now.strftime("%H:%M:%S")
            sub_text = (
                f"{self._WEEKDAYS[now.weekday()]}, "
                f"{self._MONTHS[now.month]} {now.day}, {now.year}"
            )

        elif self._mode == 1:
            elapsed = int(self._stopwatch.get_elapsed())
            h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
            digital_text = f"{h:02}:{m:02}:{s:02}"
            angles = self._engine.snapshot(datetime.datetime(2000, 1, 1, h, m, s))
            sub_text = "Stopwatch"

        else:
            remaining = int(self._timer.get_remaining())
            h, m, s = remaining // 3600, (remaining % 3600) // 60, remaining % 60
            digital_text = f"{h:02}:{m:02}:{s:02}"
            angles = self._engine.snapshot(datetime.datetime(2000, 1, 1, h, m, s))
            sub_text = "Timer"
            if self._timer.is_finished():
                self._timer.check_and_play_alarm()

        for renderer in self._hand_renderers:
            renderer.draw(angles[renderer.hand.name])

        self._canvas.delete("center_jewel")
        jr = 7
        self._canvas.create_oval(
            CENTER_X - jr, CENTER_Y - jr,
            CENTER_X + jr, CENTER_Y + jr,
            fill=COL_CENTER, outline=COL_FACE_BORDER, width=1,
            tags="center_jewel",
        )
        self._canvas.create_oval(
            CENTER_X - 2, CENTER_Y - 2,
            CENTER_X + 2, CENTER_Y + 2,
            fill="#ffffff", outline="", tags="center_jewel",
        )

        self._canvas.itemconfig(self._digital_text_id, text=digital_text)
        self._canvas.itemconfig(self._date_text_id, text=sub_text)

        self._root.after(REPAINT_MS, self._tick)

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the animation loop and enter the Tkinter main loop."""
        self._tick()
        self._root.mainloop()
