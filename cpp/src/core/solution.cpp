#include "jobshop/solution.hpp"

namespace jobshop {

// Funkcja pomocnicza do obliczenia makespanu
int calculate_makespan(const JobShopInstance& instance, Solution& solution) {
    size_t n_ops = solution.operation_sequence.size();
    solution.start_times.assign(n_ops, 0);

    // TODO: do usuniecia
    // Mapowanie operacji na indeks w solution.operation_sequence
    std::unordered_map<size_t, std::unordered_map<size_t, size_t>> op_index_map;
    for (size_t i = 0; i < n_ops; ++i) {
        size_t job_id = solution.operation_sequence[i].first;
        size_t op_id = solution.operation_sequence[i].second;
        op_index_map[job_id][op_id] = i;
    }

    // Śledzenie czasu zakończenia na maszynach
    std::vector<int> machine_available(instance.num_machines, 0);
    // Śledzenie czasu zakończenia ostatniej operacji w zadaniu
    std::vector<int> job_last_finish(instance.jobs.size(), 0);
    // TODO: do usuniecia
    // Śledzenie maszyny poprzedniej operacji w zadaniu
    std::vector<size_t> job_last_machine(instance.jobs.size(), 0);

    for (size_t i = 0; i < n_ops; ++i) {
        size_t job_id = solution.operation_sequence[i].first;
        size_t op_id = solution.operation_sequence[i].second;
        const Operation& op = instance.jobs[job_id].operations[op_id];

        // Czas transportu z poprzedniej maszyny w zadaniu
        int transport_time = 0;
        if (op_id > 0) {
            size_t prev_machine = instance.jobs[job_id].operations[op_id - 1].machine_id;
            size_t curr_machine = op.machine_id;
            transport_time = instance.transport_times[prev_machine][curr_machine];
        }

        // Najwcześniejszy start operacji
        int earliest_start = std::max(machine_available[op.machine_id], job_last_finish[job_id] + transport_time);

        solution.start_times[i] = earliest_start;
        int finish_time = earliest_start + op.processing_time;

        // Aktualizuj dostępność maszyny i ostatni czas zakończenia zadania
        machine_available[op.machine_id] = finish_time;
        job_last_finish[job_id] = finish_time;
        job_last_machine[job_id] = op.machine_id;
    }

    // Makespan to maksymalny czas zakończenia
    int max_finish = 0;
    for (size_t i = 0; i < n_ops; ++i) {
        size_t job_id = solution.operation_sequence[i].first;
        size_t op_id = solution.operation_sequence[i].second;
        const Operation& op = instance.jobs[job_id].operations[op_id];
        int finish_time = solution.start_times[i] + op.processing_time;
        if (finish_time > max_finish) {
            max_finish = finish_time;
        }
    }

    solution.makespan = max_finish;
    return max_finish;
}

} // namespace jobshop
