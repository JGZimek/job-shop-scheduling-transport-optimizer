"""Współdzielone konfiguracje GUI.

Paleta i typografia odwzorowują projekt `JobShop Optimizer.dc.html`
(ciemny granat, IBM Plex Sans/Mono, akcenty zieleń/błękit/bursztyn).
"""

# ===== DESIGN PALETTE (z projektu .dc.html) =====
APP_BG       = "#0a0e14"   # główne tło aplikacji
TOPBAR_BG    = "#0c1119"   # pasek górny
PANEL_BG     = "#0b1019"   # lewy panel konfiguracji
CARD_BG      = "#0e1420"   # karty (metryki, segmenty)
CARD_BG_ALT  = "#0c111a"   # karty wykresów / logu
CHIP_BG      = "#0e1622"   # chip instancji
INPUT_BG     = "#0a0f17"   # pola tekstowe

BORDER       = "#1b2230"   # główne obramowanie
BORDER_SOFT  = "#161d29"   # delikatne linie
BORDER_MED   = "#222b39"   # przyciski drugorzędne
BORDER_BLUE  = "#233247"   # chip / aktywne
BORDER_ACTIVE= "#2a4a6e"   # aktywna karta instancji

TXT          = "#e6edf3"   # tekst główny
TXT_2        = "#c2cad6"
TXT_3        = "#9aa4b2"
TXT_MUTED    = "#7d8799"
TXT_DIM      = "#566072"
TXT_FAINT    = "#3a4452"

GREEN        = "#3fb950"   # sukces / akcja
BLUE         = "#58a6ff"   # info / ready
AMBER        = "#d29922"   # ostrzeżenie / running
RED          = "#f85149"   # błąd
RUN_GREEN    = "#238636"   # przycisk Run
RUN_GREEN_HV = "#2ea043"

# Paleta zadań (job colors) — identyczna jak w projekcie
PAL = ['#6ea8fe', '#5ec8c8', '#7ee0a0', '#c3d96b', '#f0c850', '#f0a868',
       '#f0808a', '#e88fc0', '#b88cf0', '#8c9cf0', '#5fb0d0', '#9ad07a']

# ===== LEGACY (zachowane dla zgodności) =====
DARK_BG = APP_BG
CARD_BG_LEGACY = "#161b22"
LIGHT_BG = "#2b2b2b"
ACCENT_COLOR = BLUE
TEXT_COLOR = TXT
TEXT_SECONDARY = TXT_MUTED
BORDER_COLOR = BORDER_MED

# ===== ROZMIARY =====
WINDOW_WIDTH = 1440
WINDOW_HEIGHT = 880
SIDEBAR_WIDTH = 300

# ===== PRESETY INSTANCJI =====
# Mapowanie kart presetów na pliki w data/instances.
INSTANCE_PRESETS = [
    {"key": "test",   "file": "data/instances/test.txt",   "name": "Test",
     "dim": "4 × 3",   "ops": 12,  "glyph": "4·3",   "color": "#5ec8c8"},
    {"key": "medium", "file": "data/instances/medium.txt", "name": "Medium",
     "dim": "10 × 5",  "ops": 50,  "glyph": "10·5",  "color": "#6ea8fe"},
    {"key": "large",  "file": "data/instances/large.txt",  "name": "Large",
     "dim": "20 × 10", "ops": 200, "glyph": "20·10", "color": "#b88cf0"},
]

# ===== PARAMETRY GA =====
DEFAULT_PARAMS = {
    "population_size": 30,
    "generations": 100,
    "tournament_size": 3,
    "mutation_prob": 0.2,
    "seed": 0,
}

# Zakresy suwaków (min, max, krok)
PARAM_RANGES = {
    "population_size": (10, 500, 1),
    "generations":     (10, 1000, 10),
    "tournament_size": (1, 20, 1),
    "mutation_prob":   (0.0, 1.0, 0.01),
}

# ===== ŚCIEŻKI =====
DATA_DIR = "data/instances"

# ===== KARTY =====
CARD_PADX = 15
CARD_PADY = 15
CORNER_RADIUS = 11
BORDER_WIDTH = 1

# ===== TYPOGRAFIA =====
# Preferowane rodziny z projektu, z bezpiecznymi fallbackami na Windows.
_SANS_PREF = ["IBM Plex Sans", "Segoe UI", "Arial"]
_MONO_PREF = ["IBM Plex Mono", "Cascadia Mono", "Consolas", "Courier New"]

_SANS_FAMILY = None
_MONO_FAMILY = None


def resolve_fonts():
    """Wybiera dostępne rodziny czcionek. Wymaga istniejącego roota Tk."""
    global _SANS_FAMILY, _MONO_FAMILY
    try:
        import tkinter.font as tkfont
        available = set(tkfont.families())
    except Exception:
        available = set()

    def pick(prefs, default):
        for fam in prefs:
            if fam in available:
                return fam
        return default

    _SANS_FAMILY = pick(_SANS_PREF, "Segoe UI")
    _MONO_FAMILY = pick(_MONO_PREF, "Consolas")


def sans(size, weight="normal"):
    return (_SANS_FAMILY or "Segoe UI", size, weight)


def mono(size, weight="normal"):
    return (_MONO_FAMILY or "Consolas", size, weight)


# Predefiniowane (rozwiązywane po resolve_fonts; tuple budowane leniwie w widgetach)
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_SUBTITLE = ("Segoe UI", 14, "bold")
FONT_NORMAL = ("Segoe UI", 11)
FONT_SMALL = ("Segoe UI", 9)
