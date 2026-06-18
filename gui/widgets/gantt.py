import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from gui import config as C

PLOT_BG = C.CARD_BG_ALT
ZEBRA = "#0e131c"
GRID = C.BORDER_SOFT


class GanttFrame(ctk.CTkFrame):
    """Panel harmonogramu: nagłówek + legenda + wykres Gantta z trasami transportu."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=C.CARD_BG_ALT, corner_radius=13,
                         border_width=1, border_color=C.BORDER, **kwargs)

        # ---- HEADER ----
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=17, pady=(13, 0))
        ctk.CTkLabel(head, text="Schedule", font=C.sans(13, "bold"),
                     text_color=C.TXT).pack(side="left")
        ctk.CTkLabel(head, text="Gantt · machine × time", font=C.mono(11),
                     text_color=C.TXT_DIM).pack(side="left", padx=(12, 0))

        self.legend = ctk.CTkFrame(head, fg_color="transparent")
        self.legend.pack(side="right")
        self.hover_label = ctk.CTkLabel(head, text="", font=C.sans(11),
                                        text_color=C.TXT_MUTED)
        self.hover_label.pack(side="right", padx=(0, 14))

        ctk.CTkFrame(self, height=1, fg_color=C.BORDER_SOFT).pack(
            fill="x", padx=0, pady=(13, 0))

        # ---- PLOT ----
        self.canvas_frame = ctk.CTkFrame(self, fg_color=C.CARD_BG_ALT)
        self.canvas_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.canvas = None
        self.fig = None
        self.ax = None
        self._bars = []  # (patch, info-text)

        self.show_empty()

    # ---------- canvas helpers ----------
    def _clear_canvas(self):
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
        self.ax = None
        self._bars = []

    def _embed(self):
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _new_fig(self):
        self._clear_canvas()
        self.fig = Figure(figsize=(8, 5), dpi=100, facecolor=C.CARD_BG_ALT)
        self.ax = self.fig.add_subplot(111)

    def _clear_legend(self):
        for w in self.legend.winfo_children():
            w.destroy()

    def set_legend(self, n_jobs):
        self._clear_legend()
        cap = 12  # ogranicz liczbę chipów, by nagłówek się nie przepełnił
        shown = min(n_jobs, cap)
        for j in range(shown):
            chip = ctk.CTkFrame(self.legend, fg_color="transparent")
            chip.pack(side="left", padx=(0, 9))
            ctk.CTkFrame(chip, width=9, height=9, corner_radius=2,
                         fg_color=C.PAL[j % len(C.PAL)]).pack(side="left")
            ctk.CTkLabel(chip, text=f"J{j}", font=C.mono(10),
                         text_color=C.TXT_3).pack(side="left", padx=(5, 0))
        if n_jobs > cap:
            ctk.CTkLabel(self.legend, text=f"+{n_jobs - cap}", font=C.mono(10),
                         text_color=C.TXT_DIM).pack(side="left")

    # ---------- placeholders ----------
    def _placeholder(self, title, subtitle, t_color=C.TXT_2):
        self._new_fig()
        self.ax.set_facecolor(C.CARD_BG_ALT)
        self.ax.axis("off")
        self.ax.text(0.5, 0.56, title, ha="center", va="center", fontsize=15,
                     color=t_color, fontweight="bold", transform=self.ax.transAxes)
        self.ax.text(0.5, 0.44, subtitle, ha="center", va="center", fontsize=11,
                     color=C.TXT_DIM, transform=self.ax.transAxes)
        self._embed()

    def show_empty(self):
        self._clear_legend()
        self.hover_label.configure(text="")
        self._placeholder("No schedule yet",
                          "Select an instance from the left panel to begin")

    def show_ready(self, instance_name, n_jobs):
        self.set_legend(n_jobs)
        self.hover_label.configure(text="")
        self._placeholder(f"{instance_name} loaded",
                          "Press  Run Optimization  to schedule", t_color=C.TXT_2)

    def show_running(self):
        self.hover_label.configure(text="optimizing…")
        self._placeholder("Optimizing…", "running genetic search", t_color=C.AMBER)

    # ---------- main chart ----------
    def draw_gantt(self, instance, solution):
        self._new_fig()
        self.fig.subplots_adjust(left=0.07, right=0.985, top=0.97, bottom=0.1)
        self.ax.set_facecolor(PLOT_BG)
        self.set_legend(len(instance.jobs))
        self.hover_label.configure(text="")

        # zbuduj dane operacji
        ops = []
        op_lookup = {}
        for i, (job_id, op_id) in enumerate(solution.operation_sequence):
            op = instance.jobs[job_id].operations[op_id]
            rec = {"job": job_id, "op": op_id, "machine": op.machine_id,
                   "start": solution.start_times[i],
                   "proc": op.processing_time}
            ops.append(rec)
            op_lookup[(job_id, op_id)] = rec

        makespan = max((r["start"] + r["proc"] for r in ops), default=0)
        M = instance.num_machines

        # 1. zebra
        for m in range(M):
            if m % 2 == 0:
                self.ax.axhspan(m - 0.5, m + 0.5, facecolor=ZEBRA, zorder=0)
        # 2. siatka pionowa
        self.ax.grid(True, axis="x", color=GRID, linewidth=0.8, zorder=1)
        self.ax.set_axisbelow(True)

        # 3. trasy transportu (łączniki między kolejnymi operacjami zadania)
        for job_id in range(len(instance.jobs)):
            n_ops = len(instance.jobs[job_id].operations)
            color = C.PAL[job_id % len(C.PAL)]
            for k in range(n_ops - 1):
                a = op_lookup.get((job_id, k))
                b = op_lookup.get((job_id, k + 1))
                if a is None or b is None:
                    continue
                self.ax.plot([a["start"] + a["proc"], b["start"]],
                             [a["machine"], b["machine"]],
                             linestyle=(0, (3, 3)), color=color, linewidth=1.2,
                             alpha=0.55, zorder=2)

        # 4. słupki
        for r in ops:
            color = C.PAL[r["job"] % len(C.PAL)]
            bar = self.ax.barh(r["machine"], r["proc"], left=r["start"],
                               height=0.56, color=color, zorder=3,
                               edgecolor="#ffffff", linewidth=0.6, alpha=0.95)
            patch = bar[0]
            self._bars.append((patch,
                               f"J{r['job']} · M{r['machine']} · "
                               f"start {r['start']} · dur {r['proc']}"))
            if r["proc"] / max(makespan, 1) > 0.04:
                self.ax.text(r["start"] + r["proc"] / 2, r["machine"],
                             f"J{r['job']}", ha="center", va="center",
                             fontsize=8.5, fontweight="bold", zorder=4,
                             color=self._text_color(color))

        # osie
        self.ax.set_xlim(0, max(makespan * 1.02, 1))
        self.ax.set_ylim(M - 0.4, -0.6)  # M0 na górze
        self.ax.set_yticks(range(M))
        self.ax.set_yticklabels([f"M{i}" for i in range(M)],
                                color=C.TXT_MUTED, fontsize=10,
                                fontfamily="monospace", fontweight="bold")
        self.ax.tick_params(axis="y", length=0)
        self.ax.tick_params(axis="x", colors=C.TXT_DIM, labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_visible(False)

        self._embed()
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)

    def _text_color(self, bg):
        r, g, b, _ = mcolors.to_rgba(bg)
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        return "#0a0e14" if lum > 0.5 else "white"

    def _on_hover(self, event):
        if event.inaxes != self.ax:
            return
        try:
            for patch, info in self._bars:
                contains, _ = patch.contains(event)
                if contains:
                    self.hover_label.configure(text=info)
                    return
            self.hover_label.configure(text="")
        except Exception:
            pass

    def clear(self):
        self.show_empty()
