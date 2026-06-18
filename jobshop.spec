# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build recipe for the Job Shop Transport Optimizer GUI.

Build (from the project root, with the venv active):

    pyinstaller --noconfirm --workpath build/pyinstaller --distpath dist jobshop.spec

Produces a single-file executable at dist/JobShopOptimizer.exe.

Prerequisite: the C++ bindings must already be compiled
(`cmake --preset default && cmake --build build`) so that
build/python_module/bindings.*.pyd exists.
"""
import glob
import os
from PyInstaller.utils.hooks import collect_all

root = SPECPATH

# --- C++ pybind11 module + its MinGW runtime dependency ---
pyd_matches = glob.glob(os.path.join(root, "build", "python_module", "bindings.*.pyd"))
if not pyd_matches:
    raise SystemExit(
        "bindings .pyd not found — build the C++ core first:\n"
        "  cmake --preset default && cmake --build build")
pyd = pyd_matches[0]

binaries = [(pyd, ".")]

# libwinpthread-1.dll is dynamically linked by the .pyd (libgcc/libstdc++ are
# static). Bundle it next to the module if the toolchain is present.
winpthread = r"C:\msys64\ucrt64\bin\libwinpthread-1.dll"
if os.path.exists(winpthread):
    binaries.append((winpthread, "."))

# --- bundled data ---
datas = [(os.path.join(root, "data", "instances"), "data/instances")]

# CustomTkinter ships themes/assets that must travel with the app.
ctk_datas, ctk_bins, ctk_hidden = collect_all("customtkinter")
datas += ctk_datas
binaries += ctk_bins

a = Analysis(
    ["gui/main.py"],
    pathex=[root],
    binaries=binaries,
    datas=datas,
    hiddenimports=["bindings", "matplotlib.backends.backend_tkagg"] + ctk_hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=["PyQt5", "PyQt6", "PySide2", "PySide6"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="JobShopOptimizer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
)
