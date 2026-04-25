"""
analog_clock_ui.py
Frontend del reloj analógico — construido 100 % con tkinter (sin HTML/CSS).
Toda la interfaz gráfica y textos están en ESPAÑOL.
"""


import math
import datetime
import tkinter as tk
from tkinter import font as tkfont

from clock_engine import ClockEngine, ClockHand
from timer_engine import StopwatchEngine, TimerEngine


# ──────────────────────────────────────────────────────────────────────────────
# Palette & geometry constants
# ──────────────────────────────────────────────────────────────────────────────

VENTANA_ANCHO: int = 520
VENTANA_ALTO: int  = 620

RADIO_RELOJ: int   = 210          # radius of the clock face
CENTRO_X: int      = VENTANA_ANCHO // 2
CENTRO_Y: int      = VENTANA_ALTO  // 2 - 30

COLOR_FONDO:          str = "#0d0d1a"
COLOR_ESFERA:         str = "#12122a"
COLOR_ESFERA_BORDE:   str = "#2a2a5a"
COLOR_ESFERA_SOMBRA:  str = "#070714"
COLOR_MARCA_HORA:     str = "#e8e8ff"
COLOR_MARCA_MIN:      str = "#4a4a8a"
COLOR_NUMERO:         str = "#c8c8ff"
COLOR_CENTRO:         str = "#e94560"
COLOR_TEXTO_DIGITAL:  str = "#6a6aaa"
COLOR_TITULO:         str = "#9090d0"
COLOR_SUBTITULO:      str = "#5a5a9a"
COLOR_SEGUNDO_GLOW:   str = "#ff6080"

INTERVALO_MS: int = 50            # repaint every 50 ms → 20 fps


# ──────────────────────────────────────────────────────────────────────────────
# Helper: canvas arc segments for "glow" effects
# ──────────────────────────────────────────────────────────────────────────────

def _glow_oval(canvas: tk.Canvas, cx: int, cy: int, radio: int,
               color: str, layers: int = 4, alpha_step: int = 20) -> None:
    """Draw concentric circles to simulate a soft glow (pure tkinter)."""
    for i in range(layers, 0, -1):
        offset = i * 2
        shade = _darken(color, alpha_step * i)
        canvas.create_oval(
            cx - radio - offset, cy - radio - offset,
            cx + radio + offset, cy + radio + offset,
            outline=shade, width=1,
        )


def _darken(hex_color: str, amount: int) -> str:
    """Return a darker version of a hex color by subtracting `amount` from each channel."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r = max(0, r - amount)
    g = max(0, g - amount)
    b = max(0, b - amount)
    return f"#{r:02x}{g:02x}{b:02x}"


# ──────────────────────────────────────────────────────────────────────────────
# Hand renderer
# ──────────────────────────────────────────────────────────────────────────────

class HandRenderer:
    """Draws a single clock hand on the canvas."""

    def __init__(self, canvas: tk.Canvas, hand: ClockHand, cx: int, cy: int, radius: int):
        self._canvas: tk.Canvas = canvas
        self._hand: ClockHand = hand
        self._cx: int = cx
        self._cy: int = cy
        self._radius: int = radius
        self._tag: str = f"hand_{hand.name}"

    def draw(self, angle_rad: float) -> None:
        """Erase the previous frame and redraw the hand at the new angle."""
        self._canvas.delete(self._tag)
        length_px = int(self._radius * self._hand.length)
        end_x = self._cx + length_px * math.cos(angle_rad)
        end_y = self._cy + length_px * math.sin(angle_rad)

        # Shadow / depth line
        if self._hand.name != "second":
            self._canvas.create_line(
                self._cx + 2, self._cy + 2,
                end_x + 2, end_y + 2,
                fill=COLOR_ESFERA_SOMBRA,
                width=self._hand.width + 2,
                capstyle=tk.ROUND,
                tags=self._tag,
            )

        # Main hand line
        self._canvas.create_line(
            self._cx, self._cy,
            end_x, end_y,
            fill=self._hand.color,
            width=self._hand.width,
            capstyle=tk.ROUND,
            tags=self._tag,
        )

        # Second-hand glow accent
        if self._hand.name == "second":
            self._canvas.create_line(
                self._cx, self._cy,
                end_x, end_y,
                fill=COLOR_SEGUNDO_GLOW,
                width=1,
                capstyle=tk.ROUND,
                tags=self._tag,
            )

            # Counter-weight (tail)
            tail_len = int(self._radius * 0.18)
            opp_rad = angle_rad + math.pi
            tail_x = self._cx + tail_len * math.cos(opp_rad)
            tail_y = self._cy + tail_len * math.sin(opp_rad)
            self._canvas.create_line(
                self._cx, self._cy,
                tail_x, tail_y,
                fill=COLOR_SEGUNDO_GLOW,
                width=2,
                capstyle=tk.ROUND,
                tags=self._tag,
            )


# ──────────────────────────────────────────────────────────────────────────────
# Main UI class
# ──────────────────────────────────────────────────────────────────────────────

class RelojAnalogico:
    """
    Ventana principal del Reloj Analógico.
    Gestiona el lienzo, los renderizadores de manecillas y el loop de refresco.
    """

    # Spanish month/day names for the date display
    _MESES: list[str] = [
        "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]
    _DIAS: list[str] = [
        "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"
    ]

    MODOS = ["Reloj", "Cronómetro", "Temporizador"]

    def __init__(self):
        self._engine: ClockEngine = ClockEngine()
        self._stopwatch = StopwatchEngine()
        self._timer = TimerEngine(60)
        self._modo = 0  # 0=reloj, 1=cronómetro, 2=temporizador
        self._root: tk.Tk = tk.Tk()
        self._canvas: tk.Canvas | None = None
        self._hand_renderers: list[HandRenderer] = []
        self._setup_ventana()
        self._draw_esfera_estatica()
        self._setup_manecillas()
        self._setup_controles()
        self._root.bind("1", lambda e: self._cambiar_modo(0))
        self._root.bind("2", lambda e: self._cambiar_modo(1))
        self._root.bind("3", lambda e: self._cambiar_modo(2))

    def _setup_controles(self):
        # Botones para cambiar de modo
        frame = tk.Frame(self._root, bg=COLOR_FONDO)
        frame.place(x=20, y=VENTANA_ALTO-48)
        for i, nombre in enumerate(self.MODOS):
            b = tk.Button(frame, text=nombre, width=11, command=lambda idx=i: self._cambiar_modo(idx))
            b.grid(row=0, column=i, padx=2)

        # Etiqueta de modo activo
        self._modo_label = tk.Label(self._root, text="Modo: Reloj", fg=COLOR_TITULO, bg=COLOR_FONDO, font=("Courier", 10, "bold"))
        self._modo_label.place(x=VENTANA_ANCHO-170, y=VENTANA_ALTO-48)

        # Controles de cronómetro y temporizador
        self._controles_frame = tk.Frame(self._root, bg=COLOR_FONDO)
        self._controles_frame.place(x=VENTANA_ANCHO//2 - 120, y=VENTANA_ALTO-48)
        self._boton_start = tk.Button(self._controles_frame, text="Iniciar", width=8, command=self._accion_start)
        self._boton_pause = tk.Button(self._controles_frame, text="Pausar", width=8, command=self._accion_pause)
        self._boton_reset = tk.Button(self._controles_frame, text="Reset", width=8, command=self._accion_reset)
        self._entrada_tiempo = tk.Entry(self._controles_frame, width=8, justify="center")
        self._boton_set = tk.Button(self._controles_frame, text="Set", width=5, command=self._accion_set_tiempo)
        self._actualizar_controles()

    def _actualizar_controles(self):
        # Oculta todos los controles
        for widget in self._controles_frame.winfo_children():
            widget.grid_forget()
        if self._modo == 1:  # Cronómetro
            self._boton_start.grid(row=0, column=0, padx=2)
            self._boton_pause.grid(row=0, column=1, padx=2)
            self._boton_reset.grid(row=0, column=2, padx=2)
        elif self._modo == 2:  # Temporizador
            self._entrada_tiempo.grid(row=0, column=0, padx=2)
            self._boton_set.grid(row=0, column=1, padx=2)
            self._boton_start.grid(row=0, column=2, padx=2)
            self._boton_pause.grid(row=0, column=3, padx=2)
            self._boton_reset.grid(row=0, column=4, padx=2)

    def _accion_start(self):
        if self._modo == 1:
            self._stopwatch.start()
        elif self._modo == 2:
            self._timer.start()

    def _accion_pause(self):
        if self._modo == 1:
            self._stopwatch.pause()
        elif self._modo == 2:
            self._timer.pause()

    def _accion_reset(self):
        if self._modo == 1:
            self._stopwatch.reset()
        elif self._modo == 2:
            self._timer.reset()

    def _accion_set_tiempo(self):
        # Espera formato HH:MM:SS o MM:SS o SS
        valor = self._entrada_tiempo.get().strip()
        try:
            partes = [int(x) for x in valor.split(":")]
            if len(partes) == 3:
                total = partes[0]*3600 + partes[1]*60 + partes[2]
            elif len(partes) == 2:
                total = partes[0]*60 + partes[1]
            elif len(partes) == 1:
                total = partes[0]
            else:
                total = 60
            if total > 0:
                self._timer.set(total)
                self._timer.reset()
        except Exception:
            pass

    def _cambiar_modo(self, idx):
        self._modo = idx
        self._modo_label.config(text=f"Modo: {self.MODOS[idx]}")
        self._actualizar_controles()
        if idx == 1:
            self._stopwatch.reset()
        elif idx == 2:
            self._timer.reset()

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------

    def _setup_ventana(self) -> None:
        self._root.title("Reloj Analógico — Lista Circular Doble")
        self._root.resizable(False, False)
        self._root.configure(bg=COLOR_FONDO)

        # Center window on screen
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        pos_x = (screen_w - VENTANA_ANCHO) // 2
        pos_y = (screen_h - VENTANA_ALTO)  // 2
        self._root.geometry(f"{VENTANA_ANCHO}x{VENTANA_ALTO}+{pos_x}+{pos_y}")

        self._canvas = tk.Canvas(
            self._root,
            width=VENTANA_ANCHO,
            height=VENTANA_ALTO,
            bg=COLOR_FONDO,
            highlightthickness=0,
        )
        self._canvas.pack()

    # ------------------------------------------------------------------
    # Static face drawing
    # ------------------------------------------------------------------

    def _draw_esfera_estatica(self) -> None:
        c = self._canvas

        # ── Title ────────────────────────────────────────────────────
        c.create_text(
            CENTRO_X, 28,
            text="⟳  RELOJ ANALÓGICO",
            fill=COLOR_TITULO,
            font=("Courier", 15, "bold"),
        )
        c.create_text(
            CENTRO_X, 50,
            text="Lista Circular Doble  •  Python",
            fill=COLOR_SUBTITULO,
            font=("Courier", 9),
        )

        # ── Outer glow rings ─────────────────────────────────────────
        for i in range(5, 0, -1):
            shade = _darken(COLOR_ESFERA_BORDE, i * 18)
            c.create_oval(
                CENTRO_X - RADIO_RELOJ - i * 3,
                CENTRO_Y - RADIO_RELOJ - i * 3,
                CENTRO_X + RADIO_RELOJ + i * 3,
                CENTRO_Y + RADIO_RELOJ + i * 3,
                outline=shade, width=1,
            )

        # ── Clock face ───────────────────────────────────────────────
        c.create_oval(
            CENTRO_X - RADIO_RELOJ, CENTRO_Y - RADIO_RELOJ,
            CENTRO_X + RADIO_RELOJ, CENTRO_Y + RADIO_RELOJ,
            fill=COLOR_ESFERA, outline=COLOR_ESFERA_BORDE, width=3,
        )

        # ── Tick marks (60 minutes, 12 hours) ────────────────────────
        for tick in range(60):
            angle_rad = math.radians(tick * 6 - 90)
            is_hour_mark = (tick % 5 == 0)

            outer_r = RADIO_RELOJ - 4
            inner_r = RADIO_RELOJ - (18 if is_hour_mark else 8)
            width   = 3 if is_hour_mark else 1
            color   = COLOR_MARCA_HORA if is_hour_mark else COLOR_MARCA_MIN

            x1 = CENTRO_X + outer_r * math.cos(angle_rad)
            y1 = CENTRO_Y + outer_r * math.sin(angle_rad)
            x2 = CENTRO_X + inner_r * math.cos(angle_rad)
            y2 = CENTRO_Y + inner_r * math.sin(angle_rad)
            c.create_line(x1, y1, x2, y2, fill=color, width=width)

        # ── Hour numbers ─────────────────────────────────────────────
        number_r = RADIO_RELOJ - 40
        for hour in range(1, 13):
            angle_rad = math.radians(hour * 30 - 90)
            nx = CENTRO_X + number_r * math.cos(angle_rad)
            ny = CENTRO_Y + number_r * math.sin(angle_rad)
            c.create_text(
                nx, ny,
                text=str(hour),
                fill=COLOR_NUMERO,
                font=("Courier", 12, "bold"),
            )

        # ── Inner decorative ring ─────────────────────────────────────
        inner_deco = RADIO_RELOJ - 55
        c.create_oval(
            CENTRO_X - inner_deco, CENTRO_Y - inner_deco,
            CENTRO_X + inner_deco, CENTRO_Y + inner_deco,
            outline=COLOR_ESFERA_BORDE, width=1, dash=(3, 8),
        )

        # ── Static text labels ────────────────────────────────────────
        c.create_text(
            CENTRO_X, CENTRO_Y - RADIO_RELOJ // 2 + 10,
            text="RELOJ",
            fill=COLOR_SUBTITULO,
            font=("Courier", 8, "bold"),
        )

        # ── Digital display placeholder (updated each tick) ───────────
        self._digital_id = c.create_text(
            CENTRO_X, CENTRO_Y + RADIO_RELOJ // 2 - 18,
            text="--:--:--",
            fill=COLOR_TEXTO_DIGITAL,
            font=("Courier", 16, "bold"),
        )
        self._fecha_id = c.create_text(
            CENTRO_X, CENTRO_Y + RADIO_RELOJ // 2 + 8,
            text="",
            fill=COLOR_SUBTITULO,
            font=("Courier", 9),
        )

        # ── Bottom info bar ───────────────────────────────────────────
        c.create_rectangle(
            0, VENTANA_ALTO - 50, VENTANA_ANCHO, VENTANA_ALTO,
            fill="#09090f", outline="",
        )
        c.create_text(
            CENTRO_X, VENTANA_ALTO - 30,
            text="Hora  ●  Minuto  ●  Segundo",
            fill=COLOR_SUBTITULO,
            font=("Courier", 8),
        )
        # Hand legend dots
        legend_items = [
            (130, "#1a1a2e", "Hora"),
            (230, "#16213e", "Minuto"),
            (330, "#e94560", "Segundo"),
        ]
        for lx, lcolor, ltext in legend_items:
            c.create_oval(lx - 5, VENTANA_ALTO - 18, lx + 5, VENTANA_ALTO - 8,
                          fill=lcolor, outline=COLOR_ESFERA_BORDE)
            c.create_text(lx + 18, VENTANA_ALTO - 13,
                          text=ltext, fill=COLOR_SUBTITULO,
                          font=("Courier", 8))

    # ------------------------------------------------------------------
    # Hand setup
    # ------------------------------------------------------------------

    def _setup_manecillas(self) -> None:
        # Order matters: draw hour first, then minute, then second (on top)
        for hand in self._engine.hands:
            renderer = HandRenderer(
                canvas=self._canvas,
                hand=hand,
                cx=CENTRO_X,
                cy=CENTRO_Y,
                radius=RADIO_RELOJ,
            )
            self._hand_renderers.append(renderer)

    # ------------------------------------------------------------------
    # Tick loop
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        if self._modo == 0:  # Reloj
            now = datetime.datetime.now()
            angles = self._engine.snapshot(now)
            hora_digital = now.strftime("%H:%M:%S")
            nombre_dia = self._DIAS[now.weekday()]
            nombre_mes = self._MESES[now.month]
            fecha_str  = f"{nombre_dia}, {now.day} de {nombre_mes} de {now.year}"
        elif self._modo == 1:  # Cronómetro
            elapsed = int(self._stopwatch.get_elapsed())
            h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
            hora_digital = f"{h:02}:{m:02}:{s:02}"
            angles = self._engine.snapshot(datetime.datetime(2000,1,1,h,m,s))
            fecha_str = "Cronómetro"
        else:  # Temporizador
            remaining = int(self._timer.get_remaining())
            h, m, s = remaining // 3600, (remaining % 3600) // 60, remaining % 60
            hora_digital = f"{h:02}:{m:02}:{s:02}"
            angles = self._engine.snapshot(datetime.datetime(2000,1,1,h,m,s))
            fecha_str = "Temporizador"
            if self._timer.is_finished() and self._timer.is_running():
                self._timer.pause()
                self._root.bell()

        # Dibujar manecillas
        for renderer in self._hand_renderers:
            renderer.draw(angles[renderer._hand.name])

        # Centro
        jewel_r = 7
        self._canvas.delete("centro")
        self._canvas.create_oval(
            CENTRO_X - jewel_r, CENTRO_Y - jewel_r,
            CENTRO_X + jewel_r, CENTRO_Y + jewel_r,
            fill=COLOR_CENTRO, outline=COLOR_ESFERA_BORDE, width=1,
            tags="centro",
        )
        self._canvas.create_oval(
            CENTRO_X - 2, CENTRO_Y - 2,
            CENTRO_X + 2, CENTRO_Y + 2,
            fill="#ffffff", outline="",
            tags="centro",
        )

        # Digital
        self._canvas.itemconfig(self._digital_id, text=hora_digital)
        self._canvas.itemconfig(self._fecha_id, text=fecha_str)

        self._root.after(INTERVALO_MS, self._tick)

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def iniciar(self) -> None:
        """Start the clock loop and enter the Tk main loop."""
        self._tick()
        self._root.mainloop()


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    reloj = RelojAnalogico()
    reloj.iniciar()
