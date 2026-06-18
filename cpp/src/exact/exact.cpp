#include "jobshop/exact.hpp"
#include "jobshop/solution.hpp"

#include <queue>
#include <unordered_map>
#include <string>
#include <vector>
#include <limits>
#include <algorithm>
#include <cmath>

namespace jobshop {

namespace {

using size_t = std::size_t;

// ===== STATE SERIALIZATION =====

/**
 * Tworzy unikalny klucz stanu.
 * Optymalizacja: Rezerwacja pamięci dla stringa, aby uniknąć częstych alokacji.
 */
static std::string make_state_key(const std::vector<size_t>& job_next,
                                  const std::vector<int>& machine_avail,
                                  const std::vector<int>& job_last_finish) {
    // Szacujemy rozmiar: liczba elementów * średnio 3 znaki na liczbę + separatory
    size_t reserve_size = (job_next.size() + machine_avail.size() + job_last_finish.size()) * 4 + 10;
    std::string s;
    s.reserve(reserve_size);
    
    for (size_t i = 0; i < job_next.size(); ++i) {
        if (i) s.push_back(',');
        s += std::to_string(job_next[i]);
    }
    s.push_back('|');
    
    for (size_t i = 0; i < machine_avail.size(); ++i) {
        if (i) s.push_back(',');
        s += std::to_string(machine_avail[i]);
    }
    s.push_back('|');
    
    for (size_t i = 0; i < job_last_finish.size(); ++i) {
        if (i) s.push_back(',');
        s += std::to_string(job_last_finish[i]);
    }
    
    return s;
}

// ===== HEURISTIC FUNCTION =====

/**
 * Oblicza heurystykę h(n).
 * Zwraca szacowany CAŁKOWITY makespan (Lower Bound).
 * h = max(kiedy zwolnią się maszyny, kiedy skończą się zadania + ich reszta pracy)
 */
static int heuristic_lb(const JobShopInstance& /* instance */,
                        const std::vector<int>& machine_avail,
                        const std::vector<int>& job_last_finish,
                        const std::vector<size_t>& /* job_next_op */,
                        const std::vector<int>& remaining_proc) {
    int max_machine = 0;
    for (int t : machine_avail) {
        if (t > max_machine) max_machine = t;
    }

    int max_job = 0;
    for (size_t j = 0; j < remaining_proc.size(); ++j) {
        // job_last_finish to moment, kiedy zadanie zeszło z poprzedniej maszyny.
        // remaining_proc to suma "surowych" czasów przetwarzania.
        // To jest poprawne dolne oszacowanie (nie uwzględnia kolejek ani transportu).
        int cand = job_last_finish[j] + remaining_proc[j];
        if (cand > max_job) max_job = cand;
    }
    
    return std::max(max_machine, max_job);
}

// ===== NODE INFO STRUCTURE =====

struct NodeInfo {
    int g;                                      // koszt dotarcia (aktualny makespan)
    std::string parent_key;                     // klucz rodzica
    std::pair<size_t, size_t> scheduled_op;     // (job_id, operation_id) wykonana akcja
    int start_time;                             // kiedy ta operacja się zaczęła
};

// ===== PRIORITY QUEUE ITEM =====

struct PQItem {
    int f;              // f = max(g, h) - szacowany całkowity koszt
    int g;              // koszt dotychczasowy
    std::string key;    // stan

    // Kolejka priorytetowa w C++ to Max-Heap (największy element na górze).
    // Chcemy najmniejsze f, więc odwracamy logikę operatora <.
    bool operator<(const PQItem& other) const {
        if (f != other.f) return f > other.f; // Wyższe f ma niższy priorytet
        // Tie-breaker: Jeśli f jest równe, preferujemy WIĘKSZE g.
        // Dlaczego? Większe g oznacza, że jesteśmy głębiej w drzewie (bliżej rozwiązania).
        // To zmienia zachowanie na DFS przy równych kosztach (szybsze znalezienie pierwszego wyniku).
        return g < other.g; 
    }
};

// ===== AUXILIARY STATE DATA =====

struct Aux {
    std::vector<size_t> job_next;
    std::vector<int> machine_avail;
    std::vector<int> job_last_finish;
    std::vector<int> remain_proc;
};

} // namespace

// ===== MAIN A* SOLVER =====

Solution solve_exact(const JobShopInstance& instance) {
    Solution empty;
    const size_t num_jobs = instance.jobs.size();
    const size_t num_machines = instance.num_machines;

    // Szybkie sprawdzenie poprawności instancji
    size_t total_ops = 0;
    for (const auto& job : instance.jobs) {
        total_ops += job.operations.size();
    }
    if (total_ops == 0) return empty;

    // Precompute total processing time per job
    std::vector<int> job_total_proc(num_jobs, 0);
    for (size_t j = 0; j < num_jobs; ++j) {
        int sum = 0;
        for (const auto& op : instance.jobs[j].operations) {
            sum += op.processing_time;
        }
        job_total_proc[j] = sum;
    }

    // ===== INITIALIZE SEARCH =====

    std::vector<size_t> init_job_next(num_jobs, 0);
    std::vector<int> init_machine_avail(num_machines, 0);
    std::vector<int> init_job_last_finish(num_jobs, 0);
    std::vector<int> init_remain_proc(num_jobs, 0);
    
    for (size_t j = 0; j < num_jobs; ++j) {
        init_remain_proc[j] = job_total_proc[j];
    }

    std::string init_key = make_state_key(init_job_next, init_machine_avail, init_job_last_finish);

    // Mapy odwiedzonych stanów
    std::unordered_map<std::string, NodeInfo> visited;
    std::unordered_map<std::string, Aux> aux_map;
    
    // Rezerwacja pamięci
    visited.reserve(100000);
    aux_map.reserve(100000);

    std::priority_queue<PQItem> pq;

    // Stan początkowy
    int init_g = 0;
    int init_h = heuristic_lb(instance, init_machine_avail, init_job_last_finish,
                              init_job_next, init_remain_proc);
    
    // NAPRAWA #1: f to szacowany całkowity czas, a nie suma.
    // Ponieważ h szacuje "całkowity czas zakończenia", f = max(g, h).
    int init_f = std::max(init_g, init_h);

    pq.push(PQItem{init_f, init_g, init_key});
    visited[init_key] = NodeInfo{init_g, std::string(), 
                                 std::pair<size_t, size_t>{size_t(-1), size_t(-1)}, 0};
    aux_map[init_key] = Aux{init_job_next, init_machine_avail, init_job_last_finish, init_remain_proc};

    // ===== A* MAIN LOOP =====

    while (!pq.empty()) {
        PQItem current = pq.top();
        pq.pop();

        // Lazy deletion / Pruning
        auto vit = visited.find(current.key);
        // Jeśli znaleźliśmy wcześniej lepszą ścieżkę do tego samego stanu, pomijamy obecną
        if (vit != visited.end() && vit->second.g < current.g) {
            continue;
        }

        const Aux& curr_aux = aux_map.at(current.key);
        const auto& job_next = curr_aux.job_next;
        const auto& machine_avail = curr_aux.machine_avail;
        const auto& job_last_finish = curr_aux.job_last_finish;
        const auto& remain_proc = curr_aux.remain_proc;

        // Sprawdzenie warunku końca (wszystkie operacje wykonane)
        bool is_goal = true;
        for (size_t j = 0; j < num_jobs; ++j) {
            if (job_next[j] < instance.jobs[j].operations.size()) {
                is_goal = false;
                break;
            }
        }

        if (is_goal) {
            // Rekonstrukcja rozwiązania
            std::vector<std::pair<size_t, size_t>> seq_rev;
            std::vector<int> starts_rev;
            
            std::string cur_key = current.key;
            while (true) {
                auto it = visited.find(cur_key);
                if (it == visited.end()) break;
                
                const NodeInfo& info = it->second;
                if (info.parent_key.empty()) break; // Root
                
                seq_rev.push_back(info.scheduled_op);
                starts_rev.push_back(info.start_time);
                cur_key = info.parent_key;
            }

            std::reverse(seq_rev.begin(), seq_rev.end());
            std::reverse(starts_rev.begin(), starts_rev.end());

            Solution solution;
            solution.operation_sequence = std::move(seq_rev);
            solution.start_times = std::move(starts_rev);
            solution.makespan = current.g;
            return solution;
        }

        // Generowanie następników
        for (size_t j = 0; j < num_jobs; ++j) {
            size_t op_idx = job_next[j];
            
            // Jeśli zadanie zakończone, pomiń
            if (op_idx >= instance.jobs[j].operations.size()) continue;

            const Operation& op = instance.jobs[j].operations[op_idx];
            size_t machine_id = op.machine_id;
            int proc_time = op.processing_time;

            // Czas transportu
            int transport_time = 0;
            if (op_idx > 0) {
                size_t prev_machine = instance.jobs[j].operations[op_idx - 1].machine_id;
                transport_time = instance.transport_times[prev_machine][machine_id];
            }

            // Najwcześniejszy możliwy start
            int earliest_start = std::max(machine_avail[machine_id],
                                          job_last_finish[j] + transport_time);
            int finish_time = earliest_start + proc_time;
            
            // Nowy koszt g (makespan)
            int new_g = std::max(current.g, finish_time);

            // Tworzenie stanu następnika
            std::vector<size_t> next_job_next = job_next;
            next_job_next[j]++;
            
            std::vector<int> next_machine_avail = machine_avail;
            next_machine_avail[machine_id] = finish_time;
            
            std::vector<int> next_job_last_finish = job_last_finish;
            next_job_last_finish[j] = finish_time;
            
            std::vector<int> next_remain_proc = remain_proc;
            next_remain_proc[j] -= proc_time;

            std::string next_key = make_state_key(next_job_next, next_machine_avail, next_job_last_finish);

            // Pruning: Jeśli odwiedziliśmy ten stan z lepszym lub równym g, nie dodajemy
            auto known_it = visited.find(next_key);
            if (known_it != visited.end() && known_it->second.g <= new_g) {
                continue;
            }

            // Heurystyka i f
            int h = heuristic_lb(instance, next_machine_avail, next_job_last_finish,
                                 next_job_next, next_remain_proc);
            
            // NAPRAWA #2: Poprawne obliczenie f.
            // f = max(g, h), ponieważ h jest dolnym oszacowaniem CAŁOŚCI.
            int f = std::max(new_g, h);

            // Zapisz i dodaj do kolejki
            visited[next_key] = NodeInfo{new_g, current.key,
                                         std::pair<size_t, size_t>{j, op_idx},
                                         earliest_start};
                                         
            aux_map[next_key] = Aux{std::move(next_job_next),
                                    std::move(next_machine_avail),
                                    std::move(next_job_last_finish),
                                    std::move(next_remain_proc)};

            pq.push(PQItem{f, new_g, next_key});
        }
    }

    return empty;
}

} // namespace jobshop