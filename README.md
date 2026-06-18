# Job Shop Scheduling — Transport Optimizer

Job Shop Scheduling Problem solver with transport times. A **C++ core**
(genetic / greedy / exact solvers) exposed to a **Python GUI** via pybind11.

## Features

- **Three solvers**: a genetic algorithm (population / generations / tournament /
  mutation, with seedable RNG), a fast greedy active scheduler used as a
  baseline, and an exact branch & bound solver for small instances.
- **Live convergence**: the genetic solver reports its best makespan per
  generation, plotted as a real convergence curve (not a mock-up).
- **Interactive Gantt chart**: machine × time schedule with per-job colors,
  dashed transport connectors between consecutive operations, and hover tooltips.
- **Metrics**: makespan, improvement vs. baseline, runtime, generation, and
  operation count.
- **Export**: schedule to CSV / JSON and the Gantt chart to PNG.

## Repository structure

```
.
├── cpp/                     # C++ core
│   ├── include/jobshop/     #   public headers
│   ├── src/                 #   implementation (core, genetic, greedy, exact, io)
│   │   ├── core/  genetic/  greedy/  exact/  io/
│   │   └── main.cpp         #   standalone CLI entry point
│   └── bindings/            #   pybind11 module (bindings.cpp)
├── gui/                     # Python desktop app (CustomTkinter)
│   ├── main.py              #   application & wiring
│   ├── config.py            #   palette, fonts, presets, GA defaults
│   ├── widgets/             #   topbar, sidebar, metrics, gantt, convergence, log
│   ├── dialogs/             #   status & export dialogs
│   └── utils/               #   schedule export (CSV/JSON/PNG)
├── data/instances/          # sample instances (test, medium, large) + DATA_FORMAT.md
├── CMakeLists.txt           # builds the pybind11 module + CLI executable
├── CMakePresets.json
└── requirements.txt         # Python dependencies
```

The build artifacts land in `build/` (git-ignored): the Python module at
`build/python_module/` and the CLI binary at `build/bin/`.

## Prerequisites

- Python 3.13 (a virtual environment is recommended)
- A C++17 compiler (tested with MinGW-w64 / GCC 14 from MSYS2 `ucrt64`)
- CMake ≥ 3.16 and Ninja

## Build

```bash
# 1. Python dependencies
python -m venv .venv
.venv/Scripts/activate          # Windows; use `source .venv/bin/activate` elsewhere
pip install -r requirements.txt

# 2. Configure & build the C++ core + Python bindings
cmake --preset default
cmake --build build
```

On Windows with MSYS2 the GUI loads the compiler runtime from
`C:\msys64\ucrt64\bin` (added to the DLL search path automatically in
`gui/main.py`).

## Run

```bash
python -m gui                   # launch the desktop app
# or
python -m gui.main
```

The CLI solver is available at `build/bin/jobshop_optimizer`.

## Standalone executable

The GUI can be packaged into a single-file Windows executable with PyInstaller.
The C++ bindings must be built first (see *Build* above), then:

```bash
pip install pyinstaller
pyinstaller --noconfirm --workpath build/pyinstaller --distpath dist jobshop.spec
```

This produces `dist/JobShopOptimizer.exe` (~38 MB). The recipe in
[`jobshop.spec`](jobshop.spec) bundles:

- the compiled `bindings.*.pyd` and its `libwinpthread-1.dll` dependency
  (libgcc / libstdc++ are statically linked),
- the CustomTkinter theme/asset files and matplotlib backends,
- the sample instances under `data/instances/`.

Being a one-file build, the first launch is slightly slower (it self-extracts to
a temp directory). The app resolves bundled resources via `sys._MEIPASS` when
frozen, so it runs without Python or the MSYS2 toolchain installed.

## Architecture

```
GUI (gui/) ──imports──> bindings.pyd ──calls──> C++ core (cpp/)
   CustomTkinter            pybind11           genetic / greedy / exact
```

The GUI runs solvers on a worker thread and marshals results back to the Tk main
loop through a queue (Tkinter is not thread-safe). For the genetic solver it
then "plays back" the real per-generation history into the metrics and
convergence chart.

## Instances

Sample instances live in `data/instances/`. The file format (jobs, machines,
operation sequences, processing and transport times) is documented in
[`data/instances/DATA_FORMAT.md`](data/instances/DATA_FORMAT.md).
