"""
analog_clock_app.py
Main application class for the Analog Clock.

Wires together the canvas, hand renderers, control panel,
and the 50 ms repaint loop.

Now supports three visual styles:
  default    — original dark/navy theme
  minimalist — clean white face, black hands, red second
  python     — grey face, yellow markers, blue hour/minute, yellow second + Python logo
"""

from __future__ import annotations

import math
import datetime
import os
import tkinter as tk
from tkinter import PhotoImage

from clock_engine import ClockEngine
from stopwatch_engine import StopwatchEngine
from timer_engine import TimerEngine
from hand_renderer import HandRenderer
from control_panel import ControlPanel
from sound_manager import SoundManager

# ── Layout ────────────────────────────────────────────────────────────────────
WINDOW_W: int      = 520
WINDOW_H: int      = 640
CLOCK_RADIUS: int  = 210
CENTER_X: int      = WINDOW_W // 2
CENTER_Y: int      = WINDOW_H // 2 - 50

REPAINT_MS: int = 50  # ≈ 20 fps

# ── Style palettes ─────────────────────────────────────────────────────────────
STYLES: dict[str, dict] = {
    "default": {
        "name":         "Default",
        "bg":           "#0d0d1a",
        "face":         "#12122a",
        "face_border":  "#2a2a5a",
        "face_shadow":  "#070714",
        "tick_hour":    "#e8e8ff",
        "tick_min":     "#4a4a8a",
        "number":       "#c8c8ff",
        "center":       "#e94560",
        "digital":      "#6a6aaa",
        "title":        "#9090d0",
        "subtitle":     "#5a5a9a",
        "hour_color":   "#1a1a2e",
        "minute_color": "#16213e",
        "second_color": "#e94560",
        "second_glow":  "#ff6080",
        "hand_shadow":  "#070714",
        "legend_hour":  "#1a1a2e",
        "legend_min":   "#16213e",
        "legend_sec":   "#e94560",
        "deco_ring":    True,
    },
    "minimalist": {
        "name":         "Minimalist",
        "bg":           "#f0f0f0",
        "face":         "#ffffff",
        "face_border":  "#222222",
        "face_shadow":  "#cccccc",
        "tick_hour":    "#111111",
        "tick_min":     "#999999",
        "number":       "#111111",
        "center":       "#cc0000",
        "digital":      "#555555",
        "title":        "#444444",
        "subtitle":     "#888888",
        "hour_color":   "#111111",
        "minute_color": "#111111",
        "second_color": "#cc0000",
        "second_glow":  "#ff4444",
        "hand_shadow":  "#cccccc",
        "legend_hour":  "#111111",
        "legend_min":   "#111111",
        "legend_sec":   "#cc0000",
        "deco_ring":    False,
    },
    "python": {
        "name":         "Python",
        "bg":           "#4a4a4a",
        "face":         "#666666",
        "face_border":  "#888888",
        "face_shadow":  "#333333",
        "tick_hour":    "#FFD43B",
        "tick_min":     "#aaaaaa",
        "number":       "#FFD43B",
        "center":       "#FFD43B",
        "digital":      "#cccccc",
        "title":        "#4B8BBE",
        "subtitle":     "#aaaaaa",
        "hour_color":   "#4B8BBE",
        "minute_color": "#4B8BBE",
        "second_color": "#FFD43B",
        "second_glow":  "#FFE873",
        "hand_shadow":  "#333333",
        "legend_hour":  "#4B8BBE",
        "legend_min":   "#4B8BBE",
        "legend_sec":   "#FFD43B",
        "deco_ring":    True,
    },
}

STYLE_KEYS: list[str] = ["default", "minimalist", "python"]


def _darken(hex_color: str, amount: int) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i: i + 2], 16) for i in (0, 2, 4))
    return f"#{max(0, r - amount):02x}{max(0, g - amount):02x}{max(0, b - amount):02x}"


class AnalogClockApp:
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
        self._style_key: str = "default"

        self._root = tk.Tk()
        self._canvas: tk.Canvas
        self._hand_renderers: list[HandRenderer] = []
        self._digital_text_id: int = -1
        self._date_text_id: int = -1

        self._python_logo: PhotoImage | None = None
        self._load_python_logo()

        self._build_window()
        self._build_static_face()
        self._build_hand_renderers()
        self._build_style_bar()
        self._build_control_panel()

        self._root.bind("1", lambda _: self._change_mode(0))
        self._root.bind("2", lambda _: self._change_mode(1))
        self._root.bind("3", lambda _: self._change_mode(2))

    # ------------------------------------------------------------------
    # Python logo
    # ------------------------------------------------------------------

    def _load_python_logo(self) -> None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(script_dir, "pythonlogo.png")
        if os.path.isfile(logo_path):
            try:
                raw = PhotoImage(file=logo_path)
                w, h = raw.width(), raw.height()
                scale = max(1, max(w, h) // 52)
                self._python_logo = raw.subsample(scale, scale)
            except Exception:
                self._python_logo = None

    # ------------------------------------------------------------------
    # Window & canvas
    # ------------------------------------------------------------------

    def _build_window(self) -> None:
        self._root.title("Analog Clock — Doubly Circular Linked List")
        self._root.resizable(False, False)
        pal = STYLES[self._style_key]
        self._root.configure(bg=pal["bg"])

        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        self._root.geometry(
            f"{WINDOW_W}x{WINDOW_H}"
            f"+{(sw - WINDOW_W) // 2}+{(sh - WINDOW_H) // 2}"
        )

        self._canvas = tk.Canvas(
            self._root,
            width=WINDOW_W,
            height=WINDOW_H - 100,
            bg=pal["bg"],
            highlightthickness=0,
        )
        self._canvas.pack(side=tk.TOP)

    # ------------------------------------------------------------------
    # Static face
    # ------------------------------------------------------------------

    def _build_static_face(self) -> None:
        c = self._canvas
        pal = STYLES[self._style_key]

        c.delete("static")

        c.create_text(CENTER_X, 28, text="⟳  ANALOG CLOCK",
                      fill=pal["title"], font=("Courier", 15, "bold"),
                      tags="static")
        c.create_text(CENTER_X, 50,
                      text="Doubly Circular Linked List  •  Python",
                      fill=pal["subtitle"], font=("Courier", 9),
                      tags="static")

        for i in range(5, 0, -1):
            c.create_oval(
                CENTER_X - CLOCK_RADIUS - i * 3,
                CENTER_Y - CLOCK_RADIUS - i * 3,
                CENTER_X + CLOCK_RADIUS + i * 3,
                CENTER_Y + CLOCK_RADIUS + i * 3,
                outline=_darken(pal["face_border"], i * 18), width=1,
                tags="static",
            )

        c.create_oval(
            CENTER_X - CLOCK_RADIUS, CENTER_Y - CLOCK_RADIUS,
            CENTER_X + CLOCK_RADIUS, CENTER_Y + CLOCK_RADIUS,
            fill=pal["face"], outline=pal["face_border"], width=3,
            tags="static",
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
                fill=pal["tick_hour"] if is_hour else pal["tick_min"],
                width=3 if is_hour else 1,
                tags="static",
            )

        num_r = CLOCK_RADIUS - 40
        for hour in range(1, 13):
            a = math.radians(hour * 30 - 90)
            c.create_text(
                CENTER_X + num_r * math.cos(a),
                CENTER_Y + num_r * math.sin(a),
                text=str(hour), fill=pal["number"],
                font=("Courier", 12, "bold"),
                tags="static",
            )

        if pal.get("deco_ring", False):
            deco_r = CLOCK_RADIUS - 55
            c.create_oval(
                CENTER_X - deco_r, CENTER_Y - deco_r,
                CENTER_X + deco_r, CENTER_Y + deco_r,
                outline=pal["face_border"], width=1, dash=(3, 8),
                tags="static",
            )

        c.create_text(CENTER_X, CENTER_Y - CLOCK_RADIUS // 2 + 10,
                      text="CLOCK", fill=pal["subtitle"],
                      font=("Courier", 8, "bold"),
                      tags="static")

        self._digital_text_id = c.create_text(
            CENTER_X, CENTER_Y + CLOCK_RADIUS // 2 - 18,
            text="--:--:--", fill=pal["digital"],
            font=("Courier", 16, "bold"),
            tags="static",
        )
        self._date_text_id = c.create_text(
            CENTER_X, CENTER_Y + CLOCK_RADIUS // 2 + 8,
            text="", fill=pal["subtitle"], font=("Courier", 9),
            tags="static",
        )

        bottom_y = WINDOW_H - 100
        for lx, lcolor, ltext in [
            (130, pal["legend_hour"],  "Hour"),
            (230, pal["legend_min"],   "Minute"),
            (330, pal["legend_sec"],   "Second"),
        ]:
            by = bottom_y - 12
            c.create_oval(lx - 5, by - 5, lx + 5, by + 5,
                          fill=lcolor, outline=pal["face_border"],
                          tags="static")
            c.create_text(lx + 22, by, text=ltext,
                          fill=pal["subtitle"], font=("Courier", 8),
                          tags="static")

    # ------------------------------------------------------------------
    # Hand renderers
    # ------------------------------------------------------------------

    def _build_hand_renderers(self) -> None:
        self._hand_renderers.clear()
        pal = STYLES[self._style_key]
        for hand in self._engine.hands:
            if hand.name == "hour":
                hand.color = pal["hour_color"]
            elif hand.name == "minute":
                hand.color = pal["minute_color"]
            elif hand.name == "second":
                hand.color = pal["second_color"]
            self._hand_renderers.append(
                HandRenderer(
                    canvas=self._canvas,
                    hand=hand,
                    cx=CENTER_X,
                    cy=CENTER_Y,
                    radius=CLOCK_RADIUS,
                    style=self._style_key,
                )
            )

    def _update_hand_renderers(self) -> None:
        pal = STYLES[self._style_key]
        for renderer in self._hand_renderers:
            hand = renderer.hand
            if hand.name == "hour":
                hand.color = pal["hour_color"]
            elif hand.name == "minute":
                hand.color = pal["minute_color"]
            elif hand.name == "second":
                hand.color = pal["second_color"]
            renderer.set_style(self._style_key)

    # ------------------------------------------------------------------
    # Style bar
    # ------------------------------------------------------------------

    def _build_style_bar(self) -> None:
        pal = STYLES[self._style_key]
        self._style_frame = tk.Frame(self._root, bg=pal["bg"])
        self._style_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 2))

        tk.Label(
            self._style_frame, text="Style:",
            bg=pal["bg"], fg=pal["subtitle"],
            font=("Courier", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(10, 4))

        self._style_buttons: dict[str, tk.Button] = {}
        for key in STYLE_KEYS:
            s = STYLES[key]
            is_active = key == self._style_key
            btn = tk.Button(
                self._style_frame,
                text=s["name"],
                width=10,
                relief=tk.SUNKEN if is_active else tk.FLAT,
                bg="#2a2a5a" if is_active else "#1a1a3a",
                fg="#ffffff" if is_active else "#9090d0",
                activebackground="#3a3a7a",
                activeforeground="#ffffff",
                cursor="hand2",
                font=("Courier", 9),
                command=lambda k=key: self._change_style(k),
            )
            btn.pack(side=tk.LEFT, padx=3)
            self._style_buttons[key] = btn

    def _change_style(self, key: str) -> None:
        if key == self._style_key:
            return
        self._style_key = key
        pal = STYLES[key]

        self._root.configure(bg=pal["bg"])
        self._canvas.configure(bg=pal["bg"])
        self._style_frame.configure(bg=pal["bg"])

        for child in self._style_frame.winfo_children():
            if isinstance(child, tk.Label):
                child.configure(bg=pal["bg"], fg=pal["subtitle"])

        for k, btn in self._style_buttons.items():
            active = k == key
            btn.configure(
                relief=tk.SUNKEN if active else tk.FLAT,
                bg="#2a2a5a" if active else "#1a1a3a",
                fg="#ffffff" if active else "#9090d0",
            )

        self._build_static_face()
        self._update_hand_renderers()

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
        pal = STYLES[self._style_key]

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

        # Centre jewel / Python logo
        self._canvas.delete("center_jewel")

        if self._style_key == "python" and self._python_logo is not None:
            self._canvas.create_image(
                CENTER_X, CENTER_Y,
                image=self._python_logo,
                tags="center_jewel",
            )
        else:
            jr = 7
            self._canvas.create_oval(
                CENTER_X - jr, CENTER_Y - jr,
                CENTER_X + jr, CENTER_Y + jr,
                fill=pal["center"], outline=pal["face_border"], width=1,
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
        self._tick()
        self._root.mainloop()
