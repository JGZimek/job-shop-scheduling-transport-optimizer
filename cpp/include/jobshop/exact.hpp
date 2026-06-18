#ifndef JOBSHOP_EXACT_HPP
#define JOBSHOP_EXACT_HPP

#include "jobshop/solution.hpp"

namespace jobshop {

/**
 * Exact A* solver for Job Shop Scheduling with transport times.
 *
 * Uses A* algorithm with admissible heuristic to find optimal solution.
 * WARNING: This is exponential in complexity. Use only for small instances
 * (typically up to 10x10 or smaller depending on structure).
 *
 * @param instance Job shop instance with jobs, machines, and transport times
 * @return Optimal Solution (operation sequence with start times and makespan)
 */
Solution solve_exact(const JobShopInstance& instance);

} // namespace jobshop

#endif // JOBSHOP_EXACT_HPP