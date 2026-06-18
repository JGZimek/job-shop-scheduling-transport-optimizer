#ifndef JOBSHOP_GENETIC_HPP
#define JOBSHOP_GENETIC_HPP

#include "jobshop/solution.hpp"
#include <vector>
#include <random>
#include <unordered_set>
#include <algorithm>
#include <utility>
#include <cstddef>
#include <ctime>

namespace jobshop {

/**
 * Generate random solution (random permutation of operations)
 * 
 * @param instance Job shop instance
 * @param seed Random seed (0 = use time-based seed)
 * @return Randomly shuffled operation sequence
 */
Solution generate_random_solution(const JobShopInstance& instance, unsigned int seed = 0);

/**
 * Generate initial population of random solutions
 */
std::vector<Solution> generate_population(
    const JobShopInstance& instance,
    size_t population_size,
    unsigned int seed = 0);

/**
 * Tournament selection - select best individual from random subset
 */
Solution tournament_selection(
    const std::vector<Solution>& population,
    const JobShopInstance& instance,
    size_t tournament_size,
    unsigned int seed = 0);

/**
 * Order Crossover (OX) - preserves relative order of operations
 */
Solution order_crossover(
    const Solution& parent1,
    const Solution& parent2,
    unsigned int seed = 0);

/**
 * Swap mutation - exchange two random operations
 */
void mutate_swap(Solution& solution, unsigned int seed = 0);

/**
 * Main genetic algorithm
 * 
 * @param instance Job shop instance
 * @param population_size Population size per generation
 * @param generations Number of generations
 * @param tournament_size Tournament selection size
 * @param mutation_prob Mutation probability (0.0-1.0)
 * @param seed Random seed
 * @return Best solution found
 */
Solution run_genetic(
    const JobShopInstance& instance,
    size_t population_size,
    size_t generations,
    size_t tournament_size,
    double mutation_prob,
    unsigned int seed = 0);

/**
 * Result of a genetic run that also reports its convergence history.
 *
 * `history[g]` holds the best makespan found up to and including generation `g`.
 * `history[0]` is the best of the initial population, so the vector has
 * `generations + 1` entries.
 */
struct GeneticResult {
    Solution solution;
    std::vector<int> history;
};

/**
 * Same as run_genetic but additionally records the best-so-far makespan after
 * every generation, enabling a real convergence curve in the GUI.
 */
GeneticResult run_genetic_logged(
    const JobShopInstance& instance,
    size_t population_size,
    size_t generations,
    size_t tournament_size,
    double mutation_prob,
    unsigned int seed = 0);

} // namespace jobshop

#endif // JOBSHOP_GENETIC_HPP
