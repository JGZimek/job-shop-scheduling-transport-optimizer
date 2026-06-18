import customtkinter as ctk
from gui import config as C
from gui.dialogs.status_dialog import StatusDialog


class SidebarFrame(ctk.CTkFrame):
    """Lewy panel konfiguracji: instancje (presety + browse), algorytm, parametry GA."""

    def __init__(self, parent, on_preset_load=None, on_instance_load=None,
                 on_algorithm_change=None, **kwargs):
        super().__init__(parent, fg_color=C.PANEL_BG, corner_radius=0, **kwargs)

        self.on_preset_load = on_preset_load
        self.on_instance_load = on_instance_load
        self.on_algorithm_change_callback = on_algorithm_change

        self.selected_algorithm = "genetic"
        self.selected_preset = None
        self._preset_cards = {}
        self.params_widgets = {}
        self._value_labels = {}
        self._param_values = dict(C.DEFAULT_PARAMS)

        body = ctk.CTkScrollableFrame(
            self, fg_color=C.PANEL_BG,
            scrollbar_button_color=C.BORDER_MED,
            scrollbar_button_hover_color="#313c4d")
        body.pack(fill="both", expand=True, side="top")
        self.body = body

        self._build_instance_section(body)
        self._sep(body)
        self._build_algo_section(body)
        self._build_param_section(body)
        self._update_param_visibility()

    # ---------- helpers ----------
    def _section_label(self, parent, text):
        ctk.CTkLabel(parent, text=text.upper(), font=C.sans(10, "bold"),
                     text_color=C.TXT_DIM).pack(anchor="w", padx=2, pady=(2, 8))

    def _sep(self, parent):
        ctk.CTkFrame(parent, height=1, fg_color=C.BORDER).pack(
            fill="x", padx=2, pady=14)

    def _bind_recursive(self, widget, handler):
        widget.bind("<Button-1>", handler)
        for child in widget.winfo_children():
            self._bind_recursive(child, handler)

    # ---------- INSTANCE ----------
    def _build_instance_section(self, parent):
        self._section_label(parent, "Instance")
        for preset in C.INSTANCE_PRESETS:
            self._make_preset_card(parent, preset)

        browse = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=8,
                              border_width=1, border_color="#2a3445", height=34)
        browse.pack(fill="x", pady=(4, 0))
        browse.pack_propagate(False)
        lbl = ctk.CTkLabel(browse, text="+  Browse .txt / .csv",
                           font=C.sans(11), text_color=C.TXT_MUTED)
        lbl.place(relx=0.5, rely=0.5, anchor="center")
        self._bind_recursive(browse, lambda e: self._on_browse())

    def _make_preset_card(self, parent, preset):
        card = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=9,
                            border_width=1, border_color=C.BORDER_SOFT)
        card.pack(fill="x", pady=3)

        icon = ctk.CTkFrame(card, width=26, height=26, corner_radius=6,
                            fg_color="#141b27")
        icon.pack(side="left", padx=(10, 0), pady=9)
        icon.pack_propagate(False)
        ctk.CTkLabel(icon, text=preset["glyph"], font=C.mono(10, "bold"),
                     text_color=preset["color"]).place(relx=0.5, rely=0.5,
                                                        anchor="center")

        mid = ctk.CTkFrame(card, fg_color="transparent")
        mid.pack(side="left", padx=11, fill="x", expand=True)
        name = ctk.CTkLabel(mid, text=preset["name"], font=C.sans(12, "bold"),
                            text_color=C.TXT_2, anchor="w")
        name.pack(anchor="w")
        ctk.CTkLabel(mid, text=f"{preset['dim']} · {preset['ops']} ops",
                     font=C.mono(10), text_color=C.TXT_DIM,
                     anchor="w").pack(anchor="w")

        dot = ctk.CTkFrame(card, width=6, height=6, corner_radius=3,
                           fg_color=C.BLUE)
        # widoczność kropki sterowana przez _refresh_preset_styles

        self._preset_cards[preset["key"]] = {"card": card, "name": name, "dot": dot}
        self._bind_recursive(card, lambda e, k=preset["key"]: self._on_preset(k))

    def _on_preset(self, key):
        if self.on_preset_load:
            ok = self.on_preset_load(key)
            if ok:
                self.set_active_preset(key)

    def set_active_preset(self, key):
        self.selected_preset = key
        self._refresh_preset_styles()

    def _refresh_preset_styles(self):
        for k, refs in self._preset_cards.items():
            active = (k == self.selected_preset)
            refs["card"].configure(
                fg_color="#0f1a28" if active else "transparent",
                border_color=C.BORDER_ACTIVE if active else C.BORDER_SOFT)
            refs["name"].configure(text_color=C.TXT if active else C.TXT_2)
            if active:
                refs["dot"].pack(side="right", padx=(0, 11))
            else:
                refs["dot"].pack_forget()

    def _on_browse(self):
        if self.on_instance_load:
            res = self.on_instance_load()
            if res:
                # browse czyści zaznaczenie presetu
                self.selected_preset = None
                self._refresh_preset_styles()

    # ---------- ALGORITHM ----------
    def _build_algo_section(self, parent):
        self._section_label(parent, "Algorithm")
        self.algo_seg = ctk.CTkSegmentedButton(
            parent, values=["Genetic", "Greedy", "Exact"],
            command=self._on_algorithm_change,
            fg_color=C.CARD_BG, selected_color="#1c2533",
            selected_hover_color="#243044", unselected_color=C.CARD_BG,
            unselected_hover_color="#141b27", text_color=C.TXT_MUTED,
            font=C.sans(12, "bold"), corner_radius=7, border_width=2)
        self.algo_seg.set("Genetic")
        self.algo_seg.pack(fill="x", pady=(0, 12))

    def _on_algorithm_change(self, choice):
        self.selected_algorithm = {"Genetic": "genetic", "Greedy": "greedy",
                                   "Exact": "exact"}.get(choice, "genetic")
        self._update_param_visibility()
        if self.on_algorithm_change_callback:
            self.on_algorithm_change_callback(self.selected_algorithm)

    # ---------- PARAMS ----------
    def _build_param_section(self, parent):
        # GA container
        self.ga_container = ctk.CTkFrame(parent, fg_color="transparent")

        head = ctk.CTkFrame(self.ga_container, fg_color="transparent")
        head.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(head, text="GA Parameters", font=C.sans(11),
                     text_color=C.TXT_MUTED).pack(side="left")
        ctk.CTkLabel(head, text="genetic", font=C.mono(9),
                     text_color=C.TXT_DIM).pack(side="right")

        labels = {
            "population_size": "Population size",
            "generations": "Generations",
            "tournament_size": "Tournament size",
            "mutation_prob": "Mutation prob.",
        }
        for key in ["population_size", "generations", "tournament_size", "mutation_prob"]:
            self._make_slider(self.ga_container, key, labels[key])

        # seed
        seed_box = ctk.CTkFrame(self.ga_container, fg_color="transparent")
        seed_box.pack(fill="x", pady=(3, 0))
        sl = ctk.CTkFrame(seed_box, fg_color="transparent")
        sl.pack(fill="x")
        ctk.CTkLabel(sl, text="Random Seed ", font=C.sans(11),
                     text_color=C.TXT_3).pack(side="left")
        ctk.CTkLabel(sl, text="(0 = random)", font=C.sans(11),
                     text_color=C.TXT_DIM).pack(side="left")
        self.seed_entry = ctk.CTkEntry(seed_box, fg_color=C.INPUT_BG,
                                       border_color=C.BORDER_MED, height=34,
                                       text_color=C.TXT, font=C.mono(12),
                                       corner_radius=7)
        self.seed_entry.insert(0, "0")
        self.seed_entry.pack(fill="x", pady=(7, 0))

        # Greedy note
        self.greedy_note = ctk.CTkLabel(
            parent, text="Greedy list scheduler — deterministic active schedule, "
                         "no parameters. Fast baseline.",
            font=C.sans(11), text_color=C.TXT_MUTED, justify="left",
            wraplength=255, anchor="w", fg_color=C.CARD_BG, corner_radius=9,
            padx=12, pady=11)

        # Exact note
        self.exact_note = ctk.CTkLabel(
            parent, text="Exact solver (Branch & Bound). Exponential complexity — "
                         "only safe for instances ≤ 12 operations.",
            font=C.sans(11), text_color=C.AMBER, justify="left",
            wraplength=255, anchor="w", fg_color="#191510", corner_radius=9,
            padx=12, pady=11)

    def _make_slider(self, parent, key, label):
        lo, hi, step = C.PARAM_RANGES[key]
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 15))

        top = ctk.CTkFrame(row, fg_color="transparent")
        top.pack(fill="x", pady=(0, 7))
        ctk.CTkLabel(top, text=label, font=C.sans(11), text_color=C.TXT_3).pack(side="left")
        val_lbl = ctk.CTkLabel(top, text=self._fmt(key, self._param_values[key]),
                               font=C.mono(12, "bold"), text_color=C.TXT)
        val_lbl.pack(side="right")
        self._value_labels[key] = val_lbl

        n_steps = int(round((hi - lo) / step))
        slider = ctk.CTkSlider(
            row, from_=lo, to=hi, number_of_steps=n_steps, height=16,
            command=lambda v, k=key: self._on_slider(k, v),
            progress_color=C.GREEN, button_color=C.TXT,
            button_hover_color=C.GREEN, fg_color=C.BORDER_MED)
        slider.set(self._param_values[key])
        slider.pack(fill="x")
        self.params_widgets[key] = slider

    def _fmt(self, key, value):
        if key == "mutation_prob":
            return f"{float(value):.2f}"
        return str(int(round(value)))

    def _on_slider(self, key, value):
        if key == "mutation_prob":
            self._param_values[key] = round(float(value), 2)
        else:
            self._param_values[key] = int(round(value))
        self._value_labels[key].configure(text=self._fmt(key, self._param_values[key]))

    def _update_param_visibility(self):
        self.ga_container.pack_forget()
        self.greedy_note.pack_forget()
        self.exact_note.pack_forget()
        if self.selected_algorithm == "genetic":
            self.ga_container.pack(fill="x", pady=0)
        elif self.selected_algorithm == "greedy":
            self.greedy_note.pack(fill="x", pady=0)
        elif self.selected_algorithm == "exact":
            self.exact_note.pack(fill="x", pady=0)

    # ---------- API ----------
    def get_algorithm(self):
        return self.selected_algorithm

    def get_parameters(self):
        if self.selected_algorithm != "genetic":
            return {"algorithm": self.selected_algorithm}

        params = {"algorithm": "genetic"}
        for key in ["population_size", "generations", "tournament_size"]:
            params[key] = int(self._param_values[key])
        params["mutation_prob"] = float(self._param_values["mutation_prob"])

        # seed
        raw = self.seed_entry.get().strip()
        try:
            seed = int(raw) if raw else 0
            if seed < 0:
                seed = 0
        except ValueError:
            StatusDialog(self.winfo_toplevel(), "Configuration Error",
                         "Random seed must be a non-negative integer.",
                         type_="error")
            return None
        params["seed"] = seed

        # tournament nie może przekraczać populacji
        if params["tournament_size"] > params["population_size"]:
            params["tournament_size"] = params["population_size"]
            self.params_widgets["tournament_size"].set(params["tournament_size"])
            self._on_slider("tournament_size", params["tournament_size"])

        return params
