import customtkinter as ctk
from gui import config as C


class HeaderFrame(ctk.CTkFrame):
    """Górny pasek: logo, tytuł, chip instancji, pigułka statusu, status bindingów."""

    # Mapowanie faz na wygląd pigułki statusu
    _STATUS = {
        "empty":   ("Idle",       C.TXT_MUTED, "#15191f", C.BORDER_MED),
        "loaded":  ("Ready",      C.BLUE,      "#0d1722", "#1d3a5c"),
        "running": ("Optimizing", C.AMBER,     "#1a1710", "#3a2f12"),
        "done":    ("Completed",  C.GREEN,     "#0f1c12", "#1b3a22"),
    }

    def __init__(self, parent, bindings_available=True, **kwargs):
        super().__init__(parent, fg_color=C.TOPBAR_BG, corner_radius=0,
                         height=54, **kwargs)
        self.pack_propagate(False)
        self.bindings_available = bindings_available

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=18, pady=0)

        # ---- LOGO ----
        logo = ctk.CTkFrame(inner, fg_color="#13202e", corner_radius=7,
                            width=30, height=30, border_width=1,
                            border_color="#2a3b52")
        logo.pack(side="left", pady=12)
        logo.pack_propagate(False)
        grid = ctk.CTkFrame(logo, fg_color="transparent")
        grid.place(relx=0.5, rely=0.5, anchor="center")
        for r, c, col in [(0, 0, C.GREEN), (0, 1, C.BLUE),
                          (1, 0, C.AMBER), (1, 1, "#8c9cf0")]:
            cell = ctk.CTkFrame(grid, fg_color=col, corner_radius=1,
                                width=7, height=7)
            cell.grid(row=r, column=c, padx=1, pady=1)

        # ---- TITLE BLOCK ----
        titles = ctk.CTkFrame(inner, fg_color="transparent")
        titles.pack(side="left", padx=(11, 0))
        line = ctk.CTkFrame(titles, fg_color="transparent")
        line.pack(anchor="w")
        ctk.CTkLabel(line, text="Job Shop", font=C.sans(14, "bold"),
                     text_color=C.TXT).pack(side="left")
        ctk.CTkLabel(line, text=" Transport Optimizer", font=C.sans(14),
                     text_color=C.TXT_MUTED).pack(side="left")
        ctk.CTkLabel(titles, text="genetic scheduler · v2.0",
                     font=C.mono(10), text_color=C.TXT_DIM).pack(anchor="w")

        # ---- SEPARATOR ----
        ctk.CTkFrame(inner, width=1, height=22, fg_color=C.BORDER_MED,
                     corner_radius=0).pack(side="left", padx=14, pady=16)

        # ---- INSTANCE CHIP ----
        self.chip = ctk.CTkFrame(inner, fg_color=C.CHIP_BG, corner_radius=8,
                                 border_width=1, border_color=C.BORDER_BLUE)
        self._chip_dot = ctk.CTkFrame(self.chip, width=6, height=6,
                                      corner_radius=3, fg_color=C.BLUE)
        self._chip_dot.pack(side="left", padx=(11, 0), pady=8)
        self._chip_name = ctk.CTkLabel(self.chip, text="", font=C.sans(12),
                                       text_color=C.TXT_2)
        self._chip_name.pack(side="left", padx=(9, 0))
        self._chip_dim = ctk.CTkLabel(self.chip, text="", font=C.mono(10),
                                      text_color=C.TXT_DIM)
        self._chip_dim.pack(side="left", padx=(8, 11))

        self.no_instance = ctk.CTkLabel(inner, text="No instance loaded",
                                        font=C.sans(12, ),
                                        text_color=C.TXT_DIM)
        self.no_instance.pack(side="left")

        # ---- SPACER ----
        ctk.CTkFrame(inner, fg_color="transparent").pack(
            side="left", fill="x", expand=True)

        # ---- C++ BINDINGS PILL (po prawej) ----
        b_color = C.GREEN if bindings_available else C.RED
        b_bg = "#0f1c12" if bindings_available else "#1c1011"
        b_text = "C++ bindings" if bindings_available else "C++ error"
        bpill = ctk.CTkFrame(inner, fg_color=b_bg, corner_radius=20,
                             border_width=1, border_color=b_color)
        bpill.pack(side="right", pady=13)
        ctk.CTkFrame(bpill, width=6, height=6, corner_radius=3,
                     fg_color=b_color).pack(side="left", padx=(11, 0), pady=7)
        ctk.CTkLabel(bpill, text=b_text, font=C.mono(11),
                     text_color=b_color).pack(side="left", padx=(7, 11))

        # ---- STATUS PILL ----
        self.status_pill = ctk.CTkFrame(inner, corner_radius=20,
                                        border_width=1)
        self.status_pill.pack(side="right", padx=(0, 9), pady=13)
        self._status_dot = ctk.CTkFrame(self.status_pill, width=7, height=7,
                                        corner_radius=4)
        self._status_dot.pack(side="left", padx=(12, 0), pady=7)
        self._status_label = ctk.CTkLabel(self.status_pill, text="",
                                          font=C.sans(11, "bold"))
        self._status_label.pack(side="left", padx=(8, 12))

        self.set_status("empty")

    # ---------- API ----------
    def set_status(self, phase, progress=None):
        text, color, bg, border = self._STATUS.get(phase, self._STATUS["empty"])
        if phase == "running" and progress is not None:
            text = f"Optimizing {progress}%"
        self.status_pill.configure(fg_color=bg, border_color=border)
        self._status_dot.configure(fg_color=color)
        self._status_label.configure(text=text, text_color=color)

    def update_status(self, text, color=C.TXT_MUTED):
        """Zgodność wsteczna: ustawia dowolny tekst statusu."""
        self.status_pill.configure(fg_color="#15191f", border_color=C.BORDER_MED)
        self._status_dot.configure(fg_color=color)
        self._status_label.configure(text=text, text_color=color)

    def set_instance_info(self, filename, jobs, machines):
        self.no_instance.pack_forget()
        self._chip_name.configure(text=filename)
        self._chip_dim.configure(text=f"{jobs}J × {machines}M")
        if not self.chip.winfo_ismapped():
            self.chip.pack(side="left")

    def reset_instance_info(self):
        self.chip.pack_forget()
        if not self.no_instance.winfo_ismapped():
            self.no_instance.pack(side="left")
