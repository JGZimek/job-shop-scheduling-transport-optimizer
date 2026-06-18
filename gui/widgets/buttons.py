import customtkinter as ctk
from gui import config as C


class ButtonsFrame(ctk.CTkFrame):
    """Sekcja akcji: Run Optimization + Clear / Export."""

    def __init__(self, parent, on_optimize=None, on_clear=None, on_export=None, **kwargs):
        super().__init__(parent, fg_color=C.PANEL_BG, corner_radius=0, **kwargs)
        self.on_optimize = on_optimize
        self.on_clear = on_clear
        self.on_export = on_export

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        self.optimize_btn = ctk.CTkButton(
            inner, text="Run Optimization", command=self._optimize,
            height=40, corner_radius=9, font=C.sans(13, "bold"),
            fg_color="#161d29", hover_color="#1c2533",
            text_color=C.TXT_DIM, border_width=1, border_color=C.BORDER_MED)
        self.optimize_btn.pack(fill="x", pady=(0, 8))

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x")
        row.grid_columnconfigure((0, 1), weight=1)

        self.clear_btn = ctk.CTkButton(
            row, text="Clear", command=self._clear, height=34, corner_radius=8,
            font=C.sans(12), fg_color="#131a25", hover_color="#1c2533",
            text_color=C.TXT_2, border_width=1, border_color=C.BORDER_MED)
        self.clear_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.export_btn = ctk.CTkButton(
            row, text="Export", command=self._export, height=34, corner_radius=8,
            font=C.sans(12), fg_color="#131a25", hover_color="#1c2533",
            text_color=C.TXT_FAINT, border_width=1, border_color=C.BORDER_MED)
        self.export_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        self.export_btn.configure(state="disabled")

        self.set_run_state("empty")

    # ---------- click handlers ----------
    def _optimize(self):
        if self.on_optimize:
            self.on_optimize()

    def _clear(self):
        if self.on_clear:
            self.on_clear()

    def _export(self):
        if self.on_export:
            self.on_export()

    # ---------- state ----------
    def set_run_state(self, phase, progress=None):
        if phase in ("loaded", "done"):
            label = "Run Again" if phase == "done" else "Run Optimization"
            self.optimize_btn.configure(
                state="normal", text=label, fg_color=C.RUN_GREEN,
                hover_color=C.RUN_GREEN_HV, text_color="#ffffff",
                border_color=C.RUN_GREEN_HV)
        elif phase == "running":
            txt = "Optimizing…" if progress is None else f"Optimizing… {progress}%"
            self.optimize_btn.configure(
                state="disabled", text=txt, fg_color="#1f2a1f",
                text_color=C.GREEN, border_color="#1b3a22")
        else:  # empty
            self.optimize_btn.configure(
                state="disabled", text="Run Optimization", fg_color="#161d29",
                text_color=C.TXT_DIM, border_color=C.BORDER_MED)

    def enable_optimize(self):
        self.set_run_state("loaded")

    def disable_optimize(self):
        self.set_run_state("empty")

    def enable_export(self):
        self.export_btn.configure(state="normal", text_color=C.TXT_2)

    def disable_export(self):
        self.export_btn.configure(state="disabled", text_color=C.TXT_FAINT)
