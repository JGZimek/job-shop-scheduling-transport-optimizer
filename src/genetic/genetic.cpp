#include "jobshop/genetic.hpp"
#include <vector>
#include <algorithm>
#include <random>
#include <unordered_map>
#include <unordered_set>

namespace jobshop {

namespace {

/**
 * Helper: Converts a Solution (list of pairs) into a Genome (list of Job IDs).
 * This strips the Operation ID, keeping only the sequence of Job IDs.
 */
std::vector<size_t> solution_to_genes(const Solution& sol) {
    std::vector<size_t> genes;
    genes.reserve(sol.operation_sequence.size());
    for (const auto& p : sol.operation_sequence) {
        genes.push_back(p.first); // Keep only Job ID
    }
    return genes;
}

/**
 * Helper: Converts a Genome (list of Job IDs) back into a valid Solution.
 * This guarantees PRECEDENCE CONSTRAINTS are met.
 * The 1st appearance of Job 0 becomes (0, 0).
 * The 2nd appearance of Job 0 becomes (0, 1), etc.
 */
Solution genes_to_solution(const std::vector<size_t>& genes) {
    Solution sol;
    sol.operation_sequence.reserve(genes.size());
    
    // Track next operation index for each job
    std::unordered_map<size_t, size_t> next_op_idx;
    
    for (size_t job_id : genes) {
        size_t op_id = next_op_idx[job_id]++;
        sol.operation_sequence.emplace_back(job_id, op_id);
    }
    
    return sol;
}

/**
 * Helper: safely convert time_t to unsigned int
 */
static unsigned int get_seed(unsigned int seed) {
    if (seed > 0) {
        return seed;
    }
    return static_cast<unsigned int>(std::time(nullptr) & 0xFFFFFFFF);
}

} // namespace

// ===== RANDOM SOLUTION GENERATION =====

Solution generate_random_solution(const JobShopInstance& instance, unsigned int seed) {
    std::mt19937 rng(get_seed(seed));
    
    // Create a genome consisting of Job IDs repeated N times (where N is num operations)
    std::vector<size_t> genes;
    for (const auto& job : instance.jobs) {
        for (size_t i = 0; i < job.operations.size(); ++i) {
            genes.push_back(job.job_id);
        }
    }
    
    // Shuffle the Job IDs
    std::shuffle(genes.begin(), genes.end(), rng);
    
    // Decode into a valid solution (assigns Op IDs in correct order 0, 1, 2...)
    return genes_to_solution(genes);
}

// ===== POPULATION GENERATION =====

std::vector<Solution> generate_population(
    const JobShopInstance& instance,
    size_t population_size,
    unsigned int seed) {
    
    std::mt19937 rng(get_seed(seed));
    std::vector<Solution> population;
    population.reserve(population_size);
    
    for (size_t i = 0; i < population_size; ++i) {
        population.push_back(generate_random_solution(instance, rng()));
    }
    
    return population;
}

// ===== SELECTION =====

Solution tournament_selection(
    const std::vector<Solution>& population,
    const JobShopInstance& instance,
    size_t tournament_size,
    unsigned int seed) {
    
    std::mt19937 rng(get_seed(seed));
    std::uniform_int_distribution<size_t> dist(0, population.size() - 1);
    
    // Select first random individual
    Solution best = population[dist(rng)];
    int best_makespan = calculate_makespan(instance, best);
    
    for (size_t i = 1; i < tournament_size; ++i) {
        // FIX: Create a COPY of the contender.
        // calculate_makespan takes Solution& (non-const) because it fills start_times.
        // We cannot pass a const reference from the population vector directly.
        Solution contender = population[dist(rng)];
        int contender_makespan = calculate_makespan(instance, contender);
        
        if (contender_makespan < best_makespan) {
            // Move assignment is efficient here
            best = std::move(contender);
            best_makespan = contender_makespan;
        }
    }
    
    return best;
}

// ===== CROSSOVER =====

Solution order_crossover(
    const Solution& parent1,
    const Solution& parent2,
    unsigned int seed) {
    
    std::mt19937 rng(get_seed(seed));
    
    // 1. Extract Genomes (Job IDs only)
    std::vector<size_t> p1_genes = solution_to_genes(parent1);
    std::vector<size_t> p2_genes = solution_to_genes(parent2);
    size_t n = p1_genes.size();
    
    if (n == 0) return Solution();
    
    std::vector<size_t> child_genes(n);
    
    // 2. Perform Order Crossover (OX) on Job IDs
    std::uniform_int_distribution<size_t> dist(0, n - 1);
    size_t start = dist(rng);
    size_t end = dist(rng);
    
    if (start > end) std::swap(start, end);
    
    // Count job occurrences in the selected sub-segment of Parent 1
    std::unordered_map<size_t, int> jobs_needed;
    
    // Initialize with total counts from parent 1 (to know how many of each job we need total)
    for (size_t job : p1_genes) jobs_needed[job]++;
    
    // Copy segment from Parent 1 to Child
    for (size_t i = start; i <= end; ++i) {
        child_genes[i] = p1_genes[i];
        jobs_needed[p1_genes[i]]--; // Decrement needed count
    }
    
    // Fill remaining positions from Parent 2
    size_t current_p2_idx = (end + 1) % n;
    size_t current_child_idx = (end + 1) % n;
    
    while (current_child_idx != start) {
        size_t job_candidate = p2_genes[current_p2_idx];
        
        // If we still need this job (based on counts), take it
        if (jobs_needed[job_candidate] > 0) {
            child_genes[current_child_idx] = job_candidate;
            jobs_needed[job_candidate]--;
            current_child_idx = (current_child_idx + 1) % n;
        }
        
        current_p2_idx = (current_p2_idx + 1) % n;
    }
    
    // 3. Decode back to valid Solution (Pairs)
    return genes_to_solution(child_genes);
}

// ===== MUTATION =====

void mutate_swap(Solution& solution, unsigned int seed) {
    std::mt19937 rng(get_seed(seed));
    
    // 1. Convert to genes
    std::vector<size_t> genes = solution_to_genes(solution);
    size_t n = genes.size();
    
    if (n < 2) return;
    
    // 2. Perform Swap
    std::uniform_int_distribution<size_t> dist(0, n - 1);
    size_t i = dist(rng);
    size_t j = dist(rng);
    while (i == j) j = dist(rng);
    
    std::swap(genes[i], genes[j]);
    
    // 3. Reconstruct solution to fix Operation IDs
    solution = genes_to_solution(genes);
}

// ===== MAIN GENETIC ALGORITHM =====

Solution run_genetic(
    const JobShopInstance& instance,
    size_t population_size,
    size_t generations,
    size_t tournament_size,
    double mutation_prob,
    unsigned int seed) {
    
    std::mt19937 rng(get_seed(seed));
    
    auto population = generate_population(instance, population_size, rng());
    
    Solution best_overall = population[0];
    int best_makespan = calculate_makespan(instance, best_overall);
    
    for (size_t gen = 0; gen < generations; ++gen) {
        std::vector<Solution> new_population;
        new_population.reserve(population_size);
        
        // Elitism: keep the best found so far? (Optional, usually good practice)
        // new_population.push_back(best_overall); 
        
        while (new_population.size() < population_size) {
            Solution parent1 = tournament_selection(population, instance, tournament_size, rng());
            Solution parent2 = tournament_selection(population, instance, tournament_size, rng());
            
            Solution child = order_crossover(parent1, parent2, rng());
            
            std::uniform_real_distribution<double> prob_dist(0.0, 1.0);
            if (prob_dist(rng) < mutation_prob) {
                mutate_swap(child, rng());
            }
            
            int child_makespan = calculate_makespan(instance, child);
            if (child_makespan < best_makespan) {
                best_makespan = child_makespan;
                best_overall = child;
            }
            
            new_population.push_back(std::move(child));
        }
        
        population = std::move(new_population);
    }

    return best_overall;
}

// ===== GENETIC ALGORITHM WITH CONVERGENCE LOGGING =====

GeneticResult run_genetic_logged(
    const JobShopInstance& instance,
    size_t population_size,
    size_t generations,
    size_t tournament_size,
    double mutation_prob,
    unsigned int seed) {

    std::mt19937 rng(get_seed(seed));

    auto population = generate_population(instance, population_size, rng());

    Solution best_overall = population[0];
    int best_makespan = calculate_makespan(instance, best_overall);

    GeneticResult result;
    result.history.reserve(generations + 1);
    result.history.push_back(best_makespan); // best of the initial population

    for (size_t gen = 0; gen < generations; ++gen) {
        std::vector<Solution> new_population;
        new_population.reserve(population_size);

        while (new_population.size() < population_size) {
            Solution parent1 = tournament_selection(population, instance, tournament_size, rng());
            Solution parent2 = tournament_selection(population, instance, tournament_size, rng());

            Solution child = order_crossover(parent1, parent2, rng());

            std::uniform_real_distribution<double> prob_dist(0.0, 1.0);
            if (prob_dist(rng) < mutation_prob) {
                mutate_swap(child, rng());
            }

            int child_makespan = calculate_makespan(instance, child);
            if (child_makespan < best_makespan) {
                best_makespan = child_makespan;
                best_overall = child;
            }

            new_population.push_back(std::move(child));
        }

        population = std::move(new_population);
        result.history.push_back(best_makespan);
    }

    result.solution = best_overall;
    return result;
}

} // namespace jobshop