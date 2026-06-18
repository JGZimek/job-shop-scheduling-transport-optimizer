import customtkinter as ctk
from gui import config as C


class MetricsFrame(ctk.CTkFrame):
    """Pasek metryk: Makespan, Improvement, Runtime, Generation, Operations."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        weights = [13, 10, 10, 10, 10]  # Makespan szerszy (1.3fr)
        for i, w in enumerate(weights):
            self.grid_columnconfigure(i, weight=w, uniform="m")
        self.grid_rowconfigure(0, weight=1)

        # Makespan (z paskiem akcentu po lewej)
        self.makespan_card, self.makespan_val, _ = self._card(
            0, "Makespan", big=True, unit="units", accent=True)
        self.improve_card, self.improve_val, self.improve_sub = self._card(
            1, "Improvement", sub="vs baseline")
        self.runtime_card, self.runtime_val, self.runtime_sub = self._card(
            2, "Runtime", sub="")
        self.gen_card, self.gen_val, self.gen_sub = self._card(
            3, "Generation", sub="")
        self.ops_card, self.ops_val, self.ops_sub = self._card(
            4, "Operations", sub="")

        self.reset()

    def _card(self, col, title, big=False, unit=None, sub=None, accent=False):
        card = ctk.CTkFrame(self, fg_color=C.CARD_BG, corner_radius=11,
                            border_width=1, border_color=C.BORDER)
        card.grid(row=0, column=col, sticky="nsew",
                  padx=(0 if col == 0 else 6, 0), pady=0)

        accent_bar = None
        if accent:
            accent_bar = ctk.CTkFrame(card, width=3, fg_color=C.BORDER_MED,
                                      corner_radius=0)
            accent_bar.pack(side="left", fill="y")
            self.makespan_accent = accent_bar

        pad = ctk.CTkFrame(card, fg_color="transparent")
        pad.pack(side="left", fill="both", expand=True, padx=15, pady=12)

        ctk.CTkLabel(pad, text=title.upper(), font=C.sans(10, "bold"),
                     text_color=C.TXT_DIM, anchor="w").pack(anchor="w")

        val_row = ctk.CTkFrame(pad, fg_color="transparent")
        val_row.pack(anchor="w", pady=(6, 0), fill="x")
        val = ctk.CTkLabel(val_row, text="—",
                           font=C.mono(28 if big else 22, "bold"),
                           text_color=C.TXT, anchor="w")
        val.pack(side="left")
        if unit:
            ctk.CTkLabel(val_row, text=" " + unit, font=C.sans(11),
                         text_color=C.TXT_DIM).pack(side="left", pady=(10, 0))

        sub_lbl = None
        if sub is not None:
            sub_lbl = ctk.CTkLabel(pad, text=sub, font=C.sans(10),
                                   text_color=C.TXT_DIM, anchor="w")
            sub_lbl.pack(anchor="w", pady=(5, 0))

        return card, val, sub_lbl

    # ---------- API ----------
    def reset(self):
        self.makespan_val.configure(text="—", text_color=C.TXT)
        self.improve_val.configure(text="—", text_color=C.TXT_DIM)
        self.runtime_val.configure(text="—")
        self.runtime_sub.configure(text="")
        self.gen_val.configure(text="—")
        self.gen_sub.configure(text="—")
        self.set_accent("empty")

    def set_accent(self, phase):
        color = {"done": C.GREEN, "running": C.AMBER}.get(phase, C.BORDER_MED)
        self.makespan_accent.configure(fg_color=color)

    def set_operations(self, value, sub=""):
        self.ops_val.configure(text=str(value))
        self.ops_sub.configure(text=sub)

    def set_makespan(self, value):
        self.makespan_val.configure(text=str(value))

    def set_runtime(self, text, sub=""):
        self.runtime_val.configure(text=text)
        self.runtime_sub.configure(text=sub)

    def set_improvement(self, pct):
        if pct is None:
            self.improve_val.configure(text="—", text_color=C.TXT_DIM)
        else:
            sign = "−" if pct >= 0 else "+"
            color = C.GREEN if pct > 0 else C.TXT_DIM
            self.improve_val.configure(text=f"{sign}{abs(pct)}%", text_color=color)

    def set_generation(self, value, total=None):
        self.gen_val.configure(text=str(value))
        self.gen_sub.configure(text=(f"of {total}" if total is not None else "—"))
