#include "jobshop/greedy.hpp"
#include <limits>
#include <vector>
#include <tuple>

namespace jobshop {

Solution greedy_schedule(const JobShopInstance& instance) {
    Solution solution;
    size_t num_jobs = instance.jobs.size();
    size_t num_machines = instance.num_machines;

    // Liczba wszystkich operacji
    size_t total_ops = 0;
    for (const auto& job : instance.jobs) total_ops += job.operations.size();

    // Indeksy następnej operacji dla każdego zadania
    std::vector<size_t> next_op(num_jobs, 0);

    // Czas, kiedy maszyna będzie wolna
    std::vector<int> machine_available(num_machines, 0);
    // Czas zakończenia ostatniej operacji w zadaniu
    std::vector<int> job_finish_time(num_jobs, 0);

    while (solution.operation_sequence.size() < total_ops) {
        int best_start_time = std::numeric_limits<int>::max();
        size_t best_job = -1;
        size_t best_machine = -1;
        int best_proc_time = std::numeric_limits<int>::max();

        // Szukamy operacji, która może wystartować najwcześniej
        for (size_t j = 0; j < num_jobs; ++j) {
            size_t op_idx = next_op[j];
            if (op_idx >= instance.jobs[j].operations.size()) continue;

            const Operation& op = instance.jobs[j].operations[op_idx];

            // Transport z poprzedniej maszyny (jeśli nie pierwsza operacja)
            int transport_time = 0;
            if (op_idx > 0) {
                size_t prev_mach = instance.jobs[j].operations[op_idx - 1].machine_id;
                size_t curr_mach = op.machine_id;
                transport_time = instance.transport_times[prev_mach][curr_mach];
            }

            // Najwcześniejszy możliwy start
            int start_time = std::max(machine_available[op.machine_id],
                                      job_finish_time[j] + transport_time);

            // Wybór zachłanny: najwcześniejszy start, a przy remisie – najkrótszy czas
            if (start_time < best_start_time ||
                (start_time == best_start_time && op.processing_time < best_proc_time)) {
                best_start_time = start_time;
                best_job = j;
                best_machine = op.machine_id;
                best_proc_time = op.processing_time;
            }
        }

        // Dodajemy wybraną operację do sekwencji
        size_t op_id = next_op[best_job];
        const Operation& op = instance.jobs[best_job].operations[op_id];
        solution.operation_sequence.emplace_back(best_job, op_id);
        solution.start_times.push_back(best_start_time);

        int finish_time = best_start_time + op.processing_time;
        machine_available[best_machine] = finish_time;
        job_finish_time[best_job] = finish_time;

        next_op[best_job]++; // Przechodzimy do kolejnej operacji w zadaniu
    }

    // Oblicz końcowy makespan
    calculate_makespan(instance, solution);
    return solution;
}

} // namespace jobshop

