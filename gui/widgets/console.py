import customtkinter as ctk
from datetime import datetime
from gui import config as C

COLOR_TIMESTAMP = C.TXT_FAINT
COLOR_TEXT = C.TXT_3
COLOR_SUCCESS = C.GREEN
COLOR_WARNING = C.AMBER
COLOR_ERROR = C.RED
COLOR_ACCENT = C.BLUE
COLOR_VALUE = "#a5d6ff"


class ConsoleFrame(ctk.CTkFrame):
    """Panel Activity Log — monospaced, kolorowane wpisy ze znacznikiem czasu."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=C.CARD_BG_ALT, corner_radius=13,
                         border_width=1, border_color=C.BORDER, **kwargs)

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=15, pady=(13, 6))
        ctk.CTkLabel(head, text="Activity Log", font=C.sans(12, "bold"),
                     text_color=C.TXT).pack(side="left")
        live = ctk.CTkFrame(head, fg_color="transparent")
        live.pack(side="right")
        ctk.CTkFrame(live, width=6, height=6, corner_radius=3,
                     fg_color=C.GREEN).pack(side="left", pady=4)
        ctk.CTkLabel(live, text="live", font=C.mono(10),
                     text_color=C.TXT_DIM).pack(side="left", padx=(6, 0))

        self.textbox = ctk.CTkTextbox(
            self, font=C.mono(11), fg_color=C.CARD_BG_ALT,
            text_color=COLOR_TEXT, activate_scrollbars=True, wrap="word",
            scrollbar_button_color=C.BORDER_MED)
        self.textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.textbox.tag_config("timestamp", foreground=COLOR_TIMESTAMP)
        self.textbox.tag_config("normal", foreground=COLOR_TEXT)
        self.textbox.tag_config("success", foreground=COLOR_SUCCESS)
        self.textbox.tag_config("warning", foreground=COLOR_WARNING)
        self.textbox.tag_config("error", foreground=COLOR_ERROR)
        self.textbox.tag_config("header", foreground=COLOR_ACCENT)
        self.textbox.tag_config("accent", foreground=COLOR_ACCENT)
        self.textbox.tag_config("value", foreground=COLOR_VALUE)
        self.textbox.tag_config("placeholder", foreground=C.TXT_FAINT)

        self._empty = False
        self._show_placeholder()

    # ---------- internal ----------
    def _show_placeholder(self):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", "— no activity —", "placeholder")
        self.textbox.configure(state="disabled")
        self._empty = True

    def _ensure_clean(self):
        if self._empty:
            self.textbox.configure(state="normal")
            self.textbox.delete("1.0", "end")
            self.textbox.configure(state="disabled")
            self._empty = False

    def _write(self, text, tag="normal"):
        self._ensure_clean()
        self.textbox.configure(state="normal")
        self.textbox.insert("end", text, tag)
        self.textbox.configure(state="disabled")
        self.textbox.see("end")

    def _write_ts(self):
        self._write(datetime.now().strftime("%H:%M:%S") + "  ", "timestamp")

    # ---------- public API ----------
    def log_loaded(self, filename, jobs, machines, baseline=None):
        self._write_ts()
        self._write(f"Loaded {filename} ", "success")
        self._write(f"({jobs}J × {machines}M)\n", "value")

    def log_algorithm_selected(self, algorithm):
        pass

    def log_ga_params(self, p):
        self._write_ts()
        self._write(
            f"GA · pop={p['population_size']} gen={p['generations']} "
            f"tour={p['tournament_size']} mut={p['mutation_prob']:.2f}\n",
            "accent")

    def log_running(self, algorithm):
        self._write_ts()
        self._write(f"Running {algorithm} solver…\n", "warning")

    def log_completed(self, makespan, elapsed_time):
        self._write_ts()
        self._write(f"Done · makespan={makespan} ", "success")
        self._write(f"({elapsed_time:.2f}s)\n", "normal")

    def log_converged(self, makespan, best_gen):
        self._write_ts()
        self._write(f"Converged · makespan={makespan} ", "success")
        self._write(f"(best @ gen {best_gen})\n", "normal")

    def log_error(self, error_msg):
        self._write_ts()
        self._write(f"ERROR: {error_msg}\n", "error")

    def log(self, text, kind="normal"):
        self._write_ts()
        self._write(text.rstrip("\n") + "\n", kind)

    def insert_log(self, text, tag="normal"):
        if text.strip() == "":
            return
        self._write_ts()
        if "Exported" in text:
            self._write(text.strip() + "\n", "success")
        elif "error" in text.lower():
            self._write(text.strip() + "\n", "error")
        else:
            self._write(text.strip() + "\n", tag)

    def clear(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
        self._show_placeholder()
