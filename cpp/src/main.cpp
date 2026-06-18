#include <iostream>
#include <vector>
#include <string>
#include <chrono>
#include <cctype>
#include <algorithm>
#include <stdexcept>
#include <filesystem>
#include "jobshop/solution.hpp"
#include "jobshop/genetic.hpp"
#include "jobshop/greedy.hpp"
#include "jobshop/exact.hpp"
#include "jobshop/file_io.hpp"

using namespace jobshop;

void print_help(const char* program_name) {
    // Wyodrębnij tylko nazwę pliku z pełnej ścieżki
    std::string program_basename = std::filesystem::path(program_name).filename().string();
    
    std::cout << "\n";
    std::cout << "================================================================================\n";
    std::cout << "  Job Shop Scheduling Optimizer\n";
    std::cout << "================================================================================\n";
    std::cout << "\n";
    
    std::cout << "USAGE:\n";
    std::cout << "  " << program_basename << " <instance_file> [algorithm] [options]\n";
    std::cout << "\n";
    
    std::cout << "ARGUMENTS:\n";
    std::cout << "  <instance_file>    Path to instance file (TXT or CSV format)\n";
    std::cout << "  [algorithm]        Algorithm to use (default: all)\n";
    std::cout << "                       - all       Run all algorithms\n";
    std::cout << "                       - greedy    Greedy heuristic\n";
    std::cout << "                       - exact     Exact solver (A*)\n";
    std::cout << "                       - genetic   Genetic algorithm\n";
    std::cout << "\n";
    
    std::cout << "OPTIONS:\n";
    std::cout << "  -pop N             Population size (default: 50)\n";
    std::cout << "  -gen N             Number of generations (default: 100)\n";
    std::cout << "  -tour N            Tournament size (default: 3)\n";
    std::cout << "  -mut F             Mutation probability 0.0-1.0 (default: 0.2)\n";
    std::cout << "\n";
    std::cout << "  Note: Options only apply to genetic algorithm\n";
    std::cout << "\n";
    
    std::cout << "EXAMPLES:\n";
    std::cout << "  Basic usage:\n";
    std::cout << "    " << program_basename << " data/instances/jsp_06x06.csv\n";
    std::cout << "\n";
    std::cout << "  Run specific algorithm:\n";
    std::cout << "    " << program_basename << " data/instances/jsp_06x06.csv greedy\n";
    std::cout << "    " << program_basename << " data/instances/jsp_06x06.csv genetic\n";
    std::cout << "\n";
    std::cout << "  Genetic with custom parameters:\n";
    std::cout << "    " << program_basename << " data/instances/jsp_06x06.csv genetic -pop 100\n";
    std::cout << "    " << program_basename << " data/instances/jsp_06x06.csv genetic -pop 200 -gen 300\n";
    std::cout << "    " << program_basename << " data/instances/jsp_06x06.csv genetic -pop 50 -gen 100 -tour 5 -mut 0.1\n";
    std::cout << "\n";
    
    std::cout << "HELP:\n";
    std::cout << "  -h, --help, help   Show this help message\n";
    std::cout << "\n";
    
    std::cout << "================================================================================\n";
    std::cout << "\n";
}

void print_schedule(const JobShopInstance& instance, const Solution& solution, 
                    const std::string& algorithm_name) {
    std::cout << "\n=== Schedule for " << algorithm_name << " ===" << std::endl;
    
    // Create a 2D array to track job operations
    std::vector<std::vector<int>> schedule(instance.num_machines);
    
    // Build schedule from solution
    for (size_t op = 0; op < solution.operation_sequence.size(); ++op) {
        auto [job_id, operation_idx] = solution.operation_sequence[op];
        
        if (job_id >= instance.jobs.size() || 
            operation_idx >= instance.jobs[job_id].operations.size()) {
            continue;
        }
        
        const auto& operation = instance.jobs[job_id].operations[operation_idx];
        schedule[operation.machine_id].push_back(static_cast<int>(job_id));
    }
    
    // Print schedule
    for (size_t m = 0; m < instance.num_machines; ++m) {
        std::cout << "Machine " << m << ": ";
        for (int job : schedule[m]) {
            std::cout << "J" << job << " ";
        }
        std::cout << std::endl;
    }
    
    std::cout << "Makespan: " << solution.makespan << std::endl;
    std::cout << std::endl;
}


int main(int argc, char* argv[]) {
    // Check for help flag FIRST
    if (argc < 2) {
        print_help(argv[0]);
        return 0;
    }
    
    std::string first_arg = argv[1];
    std::transform(first_arg.begin(), first_arg.end(), first_arg.begin(),
                  [](unsigned char c) { return std::tolower(c); });
    
    if (first_arg == "-h" || first_arg == "--help" || first_arg == "help") {
        print_help(argv[0]);
        return 0;
    }
    
    std::cout << "Job Shop Scheduling Optimizer\n" << std::endl;
    
    // Parse arguments
    std::string filename = argv[1];
    std::string algorithm = "all";
    
    // Genetic algorithm parameters
    size_t pop_size = 50;
    size_t generations = 100;
    size_t tournament_size = 3;
    double mutation_prob = 0.2;
    
    if (argc > 2) {
        algorithm = argv[2];
        std::transform(algorithm.begin(), algorithm.end(), algorithm.begin(),
                      [](unsigned char c) { return std::tolower(c); });
    }
    
    // Parse GA parameters
    for (int i = 3; i < argc; ++i) {
        std::string arg = argv[i];
        std::transform(arg.begin(), arg.end(), arg.begin(),
                      [](unsigned char c) { return std::tolower(c); });
        
        try {
            if (arg == "-pop" && i + 1 < argc) {
                pop_size = static_cast<size_t>(std::stoul(argv[++i]));
            } else if (arg == "-gen" && i + 1 < argc) {
                generations = static_cast<size_t>(std::stoul(argv[++i]));
            } else if (arg == "-tour" && i + 1 < argc) {
                tournament_size = static_cast<size_t>(std::stoul(argv[++i]));
            } else if (arg == "-mut" && i + 1 < argc) {
                mutation_prob = std::stod(argv[++i]);
                if (mutation_prob < 0.0 || mutation_prob > 1.0) {
                    throw std::out_of_range("Mutation probability must be between 0.0 and 1.0");
                }
            }
        } catch (const std::exception& e) {
            std::cerr << "Error parsing arguments: " << e.what() << std::endl;
            return 1;
        }
    }
    
    // Validate algorithm
    if (algorithm != "all" && algorithm != "greedy" && algorithm != "exact" && algorithm != "genetic") {
        std::cerr << "Error: Unknown algorithm '" << algorithm << "'" << std::endl;
        std::cerr << "Use -h for help" << std::endl;
        return 1;
    }
    
    // Load instance
    JobShopInstance instance;
    try {
        std::cout << "Loading instance from: " << filename << std::endl;
        instance = load_instance_from_file(filename);
        std::cout << "OK - Loaded " << instance.jobs.size() << " jobs, " 
                  << instance.num_machines << " machines\n" << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    // ===== GREEDY =====
    if (algorithm == "all" || algorithm == "greedy") {
        std::cout << "--- Greedy Algorithm ---" << std::endl;
        auto start = std::chrono::high_resolution_clock::now();
        Solution sol_greedy = greedy_schedule(instance);
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        
        if (sol_greedy.makespan == 0) {
            sol_greedy.makespan = calculate_makespan(instance, sol_greedy);
        }
        
        std::cout << "Makespan: " << sol_greedy.makespan << std::endl;
        std::cout << "Time: " << duration.count() << " ms" << std::endl;
        print_schedule(instance, sol_greedy, "Greedy");
    }

    // ===== EXACT =====
    if (algorithm == "all" || algorithm == "exact") {
        std::cout << "--- Exact Algorithm (A*) ---" << std::endl;
        
        bool run_exact = false;
        
        // Check heuristics for "safe" size (approx 4 jobs, 3 machines is very safe)
        if (instance.jobs.size() <= 4 && instance.num_machines <= 3) {
            run_exact = true;
        } else {
            std::cout << "Warning: Instance size (" << instance.jobs.size() << "x" << instance.num_machines 
                      << ") is large for the exact solver (Exponential Complexity).\n";
            std::cout << "This might take a very long time or consume all memory.\n";
            std::cout << "Do you want to proceed? (y/N): ";
            
            char response;
            std::cin >> response;
            
            if (std::tolower(response) == 'y') {
                run_exact = true;
            } else {
                std::cout << "Skipped Exact Algorithm." << std::endl;
            }
        }

        if (run_exact) {
            std::cout << "Running Exact Solver..." << std::endl;
            auto start = std::chrono::high_resolution_clock::now();
            Solution sol_exact = solve_exact(instance);
            auto end = std::chrono::high_resolution_clock::now();
            auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
            
            if (sol_exact.makespan == 0) {
                sol_exact.makespan = calculate_makespan(instance, sol_exact);
            }
            
            std::cout << "Makespan: " << sol_exact.makespan << std::endl;
            std::cout << "Time: " << duration.count() << " ms" << std::endl;
            print_schedule(instance, sol_exact, "Exact (A*)");
        }
    }

    // ===== GENETIC =====
    if (algorithm == "all" || algorithm == "genetic") {
        std::cout << "--- Genetic Algorithm ---" << std::endl;
        std::cout << "Parameters:" << std::endl;
        std::cout << "  Population:  " << pop_size << std::endl;
        std::cout << "  Generations: " << generations << std::endl;
        std::cout << "  Tournament:  " << tournament_size << std::endl;
        std::cout << "  Mutation:    " << mutation_prob << std::endl;
        
        auto start = std::chrono::high_resolution_clock::now();
        Solution sol_genetic = run_genetic(instance, pop_size, generations, 
                                           tournament_size, mutation_prob, 42);
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        
        if (sol_genetic.makespan == 0) {
            sol_genetic.makespan = calculate_makespan(instance, sol_genetic);
        }
        
        std::cout << "Makespan: " << sol_genetic.makespan << std::endl;
        std::cout << "Time: " << duration.count() << " ms" << std::endl;
        print_schedule(instance, sol_genetic, "Genetic");
    }
    
    return 0;
}