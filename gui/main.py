import customtkinter as ctk
import threading
import queue
import sys
import os
from pathlib import Path
import time
from datetime import datetime

# Frozen (PyInstaller) vs. source run: resolve resource root + import paths.
FROZEN = getattr(sys, "frozen", False)
if FROZEN:
    # Bundled resources (data/, bindings.pyd, runtime DLLs) live under _MEIPASS.
    _ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
else:
    _ROOT = Path(__file__).parent.parent
    sys.path.insert(0, str(_ROOT))
    sys.path.insert(0, str(_ROOT / "build" / "python_module"))
    sys.path.insert(0, str(Path(__file__).parent))

# DLL path setup (dev machines with MSYS2 toolchain; harmless if absent / frozen)
if sys.platform == "win32":
    msys_bin = r"C:\msys64\ucrt64\bin"
    if os.path.exists(msys_bin):
        os.add_dll_directory(msys_bin)

from gui import config as C
from gui.widgets import (HeaderFrame, SidebarFrame, ConsoleFrame, GanttFrame,
                         ButtonsFrame, MetricsFrame, ConvergenceFrame)
from gui.dialogs.status_dialog import StatusDialog
from gui.dialogs.export_dialog import ExportDialog
from gui.utils.export import ScheduleExporter

# Try to import bindings
try:
    import bindings as jb
    BINDINGS_AVAILABLE = True
except ImportError as e:
    BINDINGS_AVAILABLE = False
    IMPORT_ERROR = str(e)


class JobShopApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Job Shop Transport Optimizer")
        self.geometry(f"{C.WINDOW_WIDTH}x{C.WINDOW_HEIGHT}")
        self.minsize(1180, 720)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        C.resolve_fonts()

        self.instance = None
        self.instance_label = ""
        self.best_solution = None
        self.baseline = 0
        self.is_running = False
        self._playback_id = 0

        if not BINDINGS_AVAILABLE:
            self.after(200, lambda: StatusDialog(
                self, "Critical Error",
                "Failed to import C++ bindings. The application cannot function correctly.",
                details=f"{IMPORT_ERROR}\n\nMake sure you compiled the project using CMake.",
                type_="error"))

        self.create_widgets()

    # ============================================================
    def create_widgets(self):
        self.configure(fg_color=C.APP_BG)

        # ---- TOPBAR ----
        self.header = HeaderFrame(self, bindings_available=BINDINGS_AVAILABLE)
        self.header.pack(side="top", fill="x")

        # ---- BODY ----
        body = ctk.CTkFrame(self, fg_color=C.APP_BG, corner_radius=0)
        body.pack(side="top", fill="both", expand=True)

        # ---- LEFT PANEL ----
        left = ctk.CTkFrame(body, fg_color=C.PANEL_BG, corner_radius=0,
                            width=C.SIDEBAR_WIDTH, border_width=0)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        # cienka linia oddzielająca
        ctk.CTkFrame(body, width=1, fg_color=C.BORDER, corner_radius=0).pack(
            side="left", fill="y")

        self.buttons = ButtonsFrame(left, on_optimize=self.run_optimization,
                                    on_clear=self.clear_results,
                                    on_export=self.export_schedule)
        self.buttons.pack(side="bottom", fill="x")
        ctk.CTkFrame(left, height=1, fg_color=C.BORDER).pack(
            side="bottom", fill="x")

        self.sidebar = SidebarFrame(left, on_preset_load=self.load_preset,
                                    on_instance_load=self.load_instance,
                                    on_algorithm_change=self.on_algorithm_change)
        self.sidebar.pack(side="top", fill="both", expand=True, padx=16, pady=16)

        # ---- RIGHT MAIN ----
        right = ctk.CTkFrame(body, fg_color=C.APP_BG, corner_radius=0)
        right.pack(side="left", fill="both", expand=True, padx=16, pady=16)

        self.metrics = MetricsFrame(right)
        self.metrics.pack(side="top", fill="x")

        # bottom row (convergence + log)
        bottom = ctk.CTkFrame(right, fg_color="transparent", height=180)
        bottom.pack(side="bottom", fill="x", pady=(14, 0))
        bottom.pack_propagate(False)
        bottom.grid_columnconfigure(0, weight=10, uniform="b")
        bottom.grid_columnconfigure(1, weight=15, uniform="b")
        bottom.grid_rowconfigure(0, weight=1)

        self.convergence = ConvergenceFrame(bottom)
        self.convergence.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        self.console = ConsoleFrame(bottom)
        self.console.grid(row=0, column=1, sticky="nsew", padx=(7, 0))

        # gantt fills remaining space
        self.gantt = GanttFrame(right)
        self.gantt.pack(side="top", fill="both", expand=True, pady=(14, 0))

    # ============================================================
    # INSTANCE LOADING
    # ============================================================
    def load_preset(self, key):
        preset = next((p for p in C.INSTANCE_PRESETS if p["key"] == key), None)
        if not preset:
            return False
        path = _ROOT / preset["file"]
        label = f"{preset['name']} {preset['dim']}"
        return self._load_file(str(path), label)

    def load_instance(self):
        """Browse arbitrary .txt/.csv file (zwraca True/False)."""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            initialdir=str(_ROOT / "data" / "instances"),
            filetypes=[("All Supported", "*.txt *.csv"), ("Text Files", "*.txt"),
                       ("CSV Files", "*.csv"), ("All files", "*.*")])
        if not file_path:
            return False
        return self._load_file(file_path, Path(file_path).name)

    def _load_file(self, file_path, label):
        if self.is_running:
            return False
        try:
            self.header.update_status("Loading…", C.AMBER)
            self.update_idletasks()

            inst = jb.load_instance_from_file(file_path)
            jobs = len(inst.jobs)
            machines = inst.num_machines
            if jobs == 0 or machines == 0:
                raise ValueError("Instance contains 0 jobs or 0 machines.")

            # baseline = naiwny harmonogram sekwencyjny.
            # Uwaga: .operation_sequence zwraca KOPIĘ wektora C++, więc budujemy
            # pełną listę i przypisujemy ją w całości (append na proxy nic nie da).
            seq = jb.Solution()
            seq.operation_sequence = [(j, op) for j in range(jobs)
                                      for op in range(len(inst.jobs[j].operations))]
            self.baseline = jb.calculate_makespan(inst, seq)

            self.instance = inst
            self.instance_label = label
            self.best_solution = None

            total_ops = sum(len(j.operations) for j in inst.jobs)
            self.console.log_loaded(label, jobs, machines, self.baseline)
            self.header.set_instance_info(label, jobs, machines)
            self.header.set_status("loaded")

            self.metrics.reset()
            self.metrics.set_operations(total_ops, f"{jobs}J × {machines}M")
            self.convergence.clear()
            self.gantt.show_ready(label, jobs)
            self.buttons.set_run_state("loaded")
            self.buttons.disable_export()
            return True
        except Exception as e:
            StatusDialog(self, "Load Error", f"Failed to load instance: {label}",
                         details=str(e), type_="error")
            self.console.log_error(str(e))
            self.header.update_status("Error", C.RED)
            self.instance = None
            return False

    def on_algorithm_change(self, algorithm):
        # runtime-sub w metrykach pokazuje wybrany algorytm po uruchomieniu
        pass

    # ============================================================
    # OPTIMIZATION
    # ============================================================
    def run_optimization(self):
        if not self.instance:
            StatusDialog(self, "Action Required", "Please load an instance first.",
                         type_="info")
            return
        if self.is_running:
            return

        params = self.sidebar.get_parameters()
        if params is None:
            return

        algorithm = params.get("algorithm", "genetic")

        if algorithm == "exact":
            total_ops = sum(len(j.operations) for j in self.instance.jobs)
            if total_ops > 12:
                dialog = StatusDialog(
                    self, title="High Complexity Warning",
                    message=f"Exact solver is NOT recommended for this instance "
                            f"({len(self.instance.jobs)}×{self.instance.num_machines}).",
                    details=("Exact algorithms have exponential time complexity.\n\n"
                             f"This instance has {total_ops} operations. Running an "
                             "exact solver will likely FREEZE or CRASH the app.\n\n"
                             "Recommended: use 'Genetic' or 'Greedy' instead."),
                    type_="warning")
                if not dialog.result:
                    return

        # enter running state
        self.is_running = True
        self._playback_id += 1
        self.buttons.set_run_state("running", 0)
        self.buttons.disable_export()
        self.header.set_status("running", 0)
        self.metrics.set_accent("running")
        self.gantt.show_running()

        if algorithm == "genetic":
            self.console.log_ga_params(params)
        self.console.log_running(algorithm.capitalize())

        # Tkinter nie jest thread-safe: wątek tylko liczy i wrzuca wynik do kolejki,
        # a pętla główna odbiera go przez _poll_result (zarejestrowane z main thread).
        self._result_queue = queue.Queue()
        thread = threading.Thread(target=self._worker, args=(params,), daemon=True)
        thread.start()
        self.after(60, self._poll_result)

    def _worker(self, params):
        """Compute in background thread; push result to the queue (no Tk calls)."""
        try:
            algorithm = params.get("algorithm", "genetic")
            t0 = time.time()
            if algorithm == "genetic":
                res = jb.run_genetic_logged(
                    self.instance, params["population_size"], params["generations"],
                    params["tournament_size"], params["mutation_prob"], params["seed"])
                solution = res.solution
                history = list(res.history)
                makespan = jb.calculate_makespan(self.instance, solution)
                self._result_queue.put(
                    ("genetic", solution, history, makespan, time.time() - t0, params))
            else:
                solution = (jb.greedy_schedule(self.instance) if algorithm == "greedy"
                            else jb.solve_exact(self.instance))
                makespan = jb.calculate_makespan(self.instance, solution)
                self._result_queue.put(
                    ("instant", solution, makespan, time.time() - t0, algorithm))
        except Exception as e:
            self._result_queue.put(("error", str(e)))

    def _poll_result(self):
        """Runs on the main thread; dispatches worker results when ready."""
        try:
            item = self._result_queue.get_nowait()
        except queue.Empty:
            self.after(60, self._poll_result)
            return
        kind = item[0]
        if kind == "genetic":
            _, solution, history, makespan, elapsed, params = item
            self._start_playback(solution, history, makespan, elapsed, params)
        elif kind == "instant":
            _, solution, makespan, elapsed, algorithm = item
            self._instant_done(solution, makespan, elapsed, algorithm)
        else:
            self._on_error(item[1])

    def _on_error(self, msg):
        self.is_running = False
        self.console.log_error(msg)
        self.header.update_status("Error", C.RED)
        self.metrics.set_accent("empty")
        self.buttons.set_run_state("loaded")
        self.gantt.show_ready(self.instance_label,
                              len(self.instance.jobs) if self.instance else 0)

    # ---------- genetic playback ----------
    def _start_playback(self, solution, history, makespan, elapsed, params):
        self.best_solution = solution
        token = self._playback_id
        n = len(history)
        total_gens = max(1, n - 1)
        best_gen = history.index(min(history))

        self.convergence.prepare(history)

        frames = min(n, 48)
        duration = 1600  # ms
        interval = max(20, duration // max(1, frames))

        def step(f):
            if token != self._playback_id:
                return  # cancelled (cleared / reloaded)
            idx = round(f / max(1, frames - 1) * (n - 1)) if frames > 1 else n - 1
            progress = round(f / max(1, frames - 1) * 100)
            self.metrics.set_makespan(history[idx])
            self.metrics.set_generation(idx, total_gens)
            self.header.set_status("running", progress)
            self.buttons.set_run_state("running", progress)
            self.convergence.draw_upto(idx + 1)
            if f < frames - 1:
                self.after(interval, lambda: step(f + 1))
            else:
                self._finish_genetic(solution, history, makespan, elapsed,
                                     total_gens, best_gen, token)

        step(0)

    def _finish_genetic(self, solution, history, makespan, elapsed,
                        total_gens, best_gen, token):
        if token != self._playback_id:
            return
        self.is_running = False
        improvement = self._improvement(makespan)

        self.convergence.finalize(history)
        self.gantt.draw_gantt(self.instance, solution)

        self.metrics.set_accent("done")
        self.metrics.set_makespan(makespan)
        self.metrics.set_improvement(improvement)
        self.metrics.set_runtime(f"{elapsed:.2f}s", "genetic")
        self.metrics.set_generation(best_gen, total_gens)

        self.console.log_converged(makespan, best_gen)
        self.console.log_completed(makespan, elapsed)

        self.header.set_status("done")
        self.buttons.set_run_state("done")
        self.buttons.enable_export()

    # ---------- greedy / exact ----------
    def _instant_done(self, solution, makespan, elapsed, algorithm):
        self.is_running = False
        self.best_solution = solution
        improvement = self._improvement(makespan)

        self.convergence.show_placeholder("not available for " + algorithm)
        self.gantt.draw_gantt(self.instance, solution)

        self.metrics.set_accent("done")
        self.metrics.set_makespan(makespan)
        self.metrics.set_improvement(improvement)
        self.metrics.set_runtime(f"{elapsed:.2f}s", algorithm)
        self.metrics.set_generation("—", None)

        self.console.log_completed(makespan, elapsed)
        self.header.set_status("done")
        self.buttons.set_run_state("done")
        self.buttons.enable_export()

    def _improvement(self, makespan):
        if self.baseline > 0:
            return round((self.baseline - makespan) / self.baseline * 100)
        return None

    # ============================================================
    # CLEAR / EXPORT
    # ============================================================
    def clear_results(self):
        self._playback_id += 1  # cancel any playback
        self.is_running = False
        self.best_solution = None
        self.console.clear()
        self.metrics.reset()
        self.convergence.clear()
        self.buttons.disable_export()
        if self.instance:
            total_ops = sum(len(j.operations) for j in self.instance.jobs)
            self.metrics.set_operations(total_ops)
            self.gantt.show_ready(self.instance_label, len(self.instance.jobs))
            self.buttons.set_run_state("loaded")
            self.header.set_status("loaded")
        else:
            self.gantt.show_empty()
            self.buttons.set_run_state("empty")
            self.header.set_status("empty")

    def export_schedule(self):
        if not self.best_solution or not self.instance:
            StatusDialog(self, "No Data", "No solution to export. Run optimization first.",
                         type_="info")
            return
        dialog = ExportDialog(self)
        self.wait_window(dialog)
        if not dialog.result:
            return
        result = dialog.result
        save_path = result["path"]
        try:
            exported = []
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if result["csv"]:
                p = ScheduleExporter.export_to_csv(
                    self.instance, self.best_solution,
                    output_path=save_path / f"schedule_{timestamp}.csv")
                exported.append(Path(p).name)
                self.console.insert_log(f"Exported {Path(p).name}")
            if result["json"]:
                p = ScheduleExporter.export_to_json(
                    self.instance, self.best_solution,
                    output_path=save_path / f"schedule_{timestamp}.json")
                exported.append(Path(p).name)
                self.console.insert_log(f"Exported {Path(p).name}")
            if result["png"] and self.gantt.fig:
                p = ScheduleExporter.export_gantt_image(
                    self.gantt.fig, output_path=save_path / f"gantt_{timestamp}.png")
                exported.append(Path(p).name)
                self.console.insert_log(f"Exported {Path(p).name}")

            files_list = "\n".join([f"• {x}" for x in exported])
            StatusDialog(self, "Export Successful",
                         f"Successfully saved {len(exported)} files to folder:",
                         details=f"{save_path}\n\n{files_list}", type_="success")
        except Exception as e:
            self.console.log_error(f"Export error: {e}")
            StatusDialog(self, "Export Failed", "An error occurred during file export.",
                         details=str(e), type_="error")


def main():
    app = JobShopApp()
    app.mainloop()


if __name__ == "__main__":
    main()
