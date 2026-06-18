# Job Shop Scheduling — Transport Optimizer

Job Shop Scheduling Problem solver with transport times. A **C++ core**
(genetic / greedy / exact solvers) exposed to a **Python GUI** via pybind11.

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

## Instances

Sample instances live in `data/instances/`. The file format (jobs, machines,
operation sequences, processing and transport times) is documented in
[`data/instances/DATA_FORMAT.md`](data/instances/DATA_FORMAT.md).
