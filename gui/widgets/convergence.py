import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from gui import config as C


class ConvergenceFrame(ctk.CTkFrame):
    """Wykres zbieżności GA (najlepszy makespan / generacja) — realne dane."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=C.CARD_BG_ALT, corner_radius=13,
                         border_width=1, border_color=C.BORDER, **kwargs)

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=15, pady=(13, 6))
        ctk.CTkLabel(head, text="Convergence", font=C.sans(12, "bold"),
                     text_color=C.TXT).pack(side="left")
        ctk.CTkLabel(head, text="best makespan / gen", font=C.mono(10),
                     text_color=C.TXT_DIM).pack(side="right")

        self.canvas_frame = ctk.CTkFrame(self, fg_color=C.CARD_BG_ALT)
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.canvas = None
        self.fig = None
        self.ax = None
        self.line = None
        self._x = []
        self._history = []

        self.show_placeholder()

    # ---------- internal ----------
    def _clear_canvas(self):
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
        self.ax = self.line = None

    def _embed(self):
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _new_fig(self):
        self._clear_canvas()
        self.fig = Figure(figsize=(4, 2), dpi=100, facecolor=C.CARD_BG_ALT)
        self.fig.subplots_adjust(left=0.02, right=0.99, top=0.96, bottom=0.04)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(C.CARD_BG_ALT)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        for spine in self.ax.spines.values():
            spine.set_visible(False)

    # ---------- API ----------
    def show_placeholder(self, text="awaiting optimization run"):
        self._new_fig()
        self.ax.axis("off")
        self.ax.text(0.5, 0.5, text, ha="center", va="center",
                     fontsize=10, color=C.TXT_FAINT,
                     transform=self.ax.transAxes)
        self._embed()

    def prepare(self, history):
        """Inicjalizuje osie pod pełen zakres danych; rysuje pusty wykres."""
        self._history = list(history)
        self._x = list(range(len(self._history)))
        self._new_fig()
        n = max(1, len(self._history) - 1)
        self.ax.set_xlim(0, n)
        vhi, vlo = max(self._history), min(self._history)
        span = max(1, vhi - vlo)
        self.ax.set_ylim(vlo - span * 0.08, vhi + span * 0.08)
        (self.line,) = self.ax.plot([], [], color=C.GREEN, linewidth=1.6,
                                    solid_joinstyle="round")
        self._embed()

    def draw_upto(self, k):
        """Aktualizuje krzywą do k punktów (playback)."""
        if self.line is None or k < 1:
            return
        self.line.set_data(self._x[:k], self._history[:k])
        self.canvas.draw_idle()

    def finalize(self, history=None):
        """Rysuje pełną krzywą z wypełnieniem gradientowym."""
        if history is not None:
            self._history = list(history)
            self._x = list(range(len(self._history)))
        if not self._history:
            return self.show_placeholder()
        self._new_fig()
        n = max(1, len(self._history) - 1)
        self.ax.set_xlim(0, n)
        vhi, vlo = max(self._history), min(self._history)
        span = max(1, vhi - vlo)
        ylo, yhi = vlo - span * 0.08, vhi + span * 0.08
        self.ax.set_ylim(ylo, yhi)
        self.ax.fill_between(self._x, self._history, ylo, color=C.GREEN,
                             alpha=0.16, linewidth=0)
        self.ax.plot(self._x, self._history, color=C.GREEN, linewidth=1.6,
                     solid_joinstyle="round")
        self._embed()

    def clear(self):
        self._history = []
        self._x = []
        self.show_placeholder()
