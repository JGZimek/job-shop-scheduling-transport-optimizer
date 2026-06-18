#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "jobshop/genetic.hpp"
#include "jobshop/greedy.hpp"
#include "jobshop/exact.hpp"
#include "jobshop/file_io.hpp"
#include "jobshop/solution.hpp"

namespace py = pybind11;
using namespace jobshop;

PYBIND11_MODULE(bindings, m) {
    m.doc() = "Job Shop Scheduling with Transport Times Optimizer";

    // ========== STRUKTURY ==========
    
    // Operation
    py::class_<Operation>(m, "Operation")
        .def(py::init<>())
        .def_readwrite("job_id", &Operation::job_id)
        .def_readwrite("operation_id", &Operation::operation_id)
        .def_readwrite("machine_id", &Operation::machine_id)
        .def_readwrite("processing_time", &Operation::processing_time);

    // Job
    py::class_<Job>(m, "Job")
        .def(py::init<>())
        .def_readwrite("job_id", &Job::job_id)
        .def_readwrite("operations", &Job::operations);

    // JobShopInstance
    py::class_<JobShopInstance>(m, "JobShopInstance")
        .def(py::init<>())
        .def_readwrite("jobs", &JobShopInstance::jobs)
        .def_readwrite("num_machines", &JobShopInstance::num_machines)
        .def_readwrite("transport_times", &JobShopInstance::transport_times);

    // Solution
    py::class_<Solution>(m, "Solution")
        .def(py::init<>())
        .def_readwrite("operation_sequence", &Solution::operation_sequence)
        .def_readwrite("start_times", &Solution::start_times)
        .def_readwrite("makespan", &Solution::makespan);

    // ========== FILE I/O ==========
    
    m.def("load_instance_from_file", &load_instance_from_file, 
          py::arg("filename"),
          "Load instance from file (TXT/CSV format)");
    
    // ========== SOLUTION CALCULATION ==========
    
    m.def("calculate_makespan", &calculate_makespan, 
          py::arg("instance"),
          py::arg("solution"),
          "Calculate makespan for a solution");

    // ========== GENETIC ALGORITHM ==========
    
    m.def("generate_random_solution", &generate_random_solution,
          py::arg("instance"),
          py::arg("seed") = 0,
          "Generate a random solution");
    
    m.def("generate_population", &generate_population,
          py::arg("instance"),
          py::arg("population_size"),
          py::arg("seed") = 0,
          "Generate initial population");
    
    m.def("tournament_selection", &tournament_selection,
          py::arg("population"),
          py::arg("instance"),
          py::arg("tournament_size"),
          py::arg("seed") = 0,
          "Tournament selection");
    
    m.def("order_crossover", &order_crossover,
          py::arg("parent1"),
          py::arg("parent2"),
          py::arg("seed") = 0,
          "Order Crossover (OX)");
    
    m.def("mutate_swap", &mutate_swap,
          py::arg("solution"),
          py::arg("seed") = 0,
          "Swap mutation");
    
    m.def("run_genetic", &run_genetic,
          py::arg("instance"),
          py::arg("population_size"),
          py::arg("generations"),
          py::arg("tournament_size"),
          py::arg("mutation_prob"),
          py::arg("seed") = 0,
          "Run genetic algorithm");

    // GeneticResult: solution + per-generation convergence history
    py::class_<GeneticResult>(m, "GeneticResult")
        .def(py::init<>())
        .def_readwrite("solution", &GeneticResult::solution)
        .def_readwrite("history", &GeneticResult::history);

    m.def("run_genetic_logged", &run_genetic_logged,
          py::arg("instance"),
          py::arg("population_size"),
          py::arg("generations"),
          py::arg("tournament_size"),
          py::arg("mutation_prob"),
          py::arg("seed") = 0,
          "Run genetic algorithm and return the best solution together with its "
          "best-so-far makespan after every generation (history).");

    // ========== GREEDY ALGORITHM ==========
    
    m.def("greedy_schedule", &greedy_schedule,
          py::arg("instance"),
          "Run greedy scheduling algorithm");

    // ========== EXACT ALGORITHM ==========
    
    m.def("solve_exact", &solve_exact,
          py::arg("instance"),
          "Run exact algorithm (A* search)");
}
