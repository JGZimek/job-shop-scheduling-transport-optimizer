#ifndef JOBSHOP_SOLUTION_HPP
#define JOBSHOP_SOLUTION_HPP

#include <vector>
#include <utility>
#include <cstddef>
#include <unordered_map>
#include <algorithm>
#include <stdexcept>

namespace jobshop {

struct Operation {
    std::size_t job_id; // TODO: do usuniecia
    std::size_t operation_id;
    std::size_t machine_id;
    int processing_time;
};

struct Job {
    std::size_t job_id;
    std::vector<Operation> operations;
};

struct JobShopInstance {
    std::vector<Job> jobs;
    std::size_t num_machines;
    std::vector<std::vector<int>> transport_times;
};

struct Solution {
    std::vector<std::pair<size_t, size_t>> operation_sequence; // <job_id, operation_id>
    std::vector<int> start_times; // czasy startu operacji
    int makespan = 0;
};

// Deklaracja funkcji obliczającej makespan
int calculate_makespan(const JobShopInstance& instance, Solution& solution);

} // namespace jobshop

#endif // JOBSHOP_SOLUTION_HPP
