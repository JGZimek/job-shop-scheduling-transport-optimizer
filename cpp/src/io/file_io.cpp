#include "jobshop/file_io.hpp"
#include <algorithm>
#include <cctype>
#include <iostream>

namespace jobshop {

// ===== HELPER FUNCTIONS =====

/**
 * Trim whitespace and quotes from string
 */
static std::string trim(const std::string& str) {
    size_t first = str.find_first_not_of(" \t\r\n\"");
    if (first == std::string::npos) return "";
    
    size_t last = str.find_last_not_of(" \t\r\n\"");
    return str.substr(first, last - first + 1);
}

/**
 * Split string by delimiter
 */
static std::vector<std::string> split_by_delimiter(const std::string& line, char delim) {
    std::vector<std::string> result;
    std::stringstream ss(line);
    std::string item;

    while (std::getline(ss, item, delim)) {
        std::string trimmed = trim(item);
        if (!trimmed.empty()) {
            result.push_back(trimmed);
        }
    }

    return result;
}

/**
 * Check if line is comment or empty
 */
static bool is_comment_line(const std::string& line) {
    std::string trimmed = trim(line);
    return trimmed.empty() || trimmed[0] == '#';
}

// ===== FORMAT DETECTION =====

FileFormat detect_format(const std::string& filename) {
    if (filename.size() > 5 && filename.substr(filename.size() - 5) == ".json") {
        return FileFormat::JSON;
    } else if (filename.size() > 4 && filename.substr(filename.size() - 4) == ".csv") {
        return FileFormat::CSV;
    } else {
        return FileFormat::TXT;
    }
}

// ===== TXT FORMAT PARSER =====

JobShopInstance parse_txt_format(std::ifstream& file) {
    std::string line;
    size_t n_jobs = 0;
    size_t n_machines = 0;
    int line_num = 0;

    // Read header: n_jobs n_machines
    while (std::getline(file, line)) {
        line_num++;
        if (!is_comment_line(line)) {
            auto parts = split_by_delimiter(line, ' ');
            if (parts.size() < 2) {
                throw std::runtime_error("Line " + std::to_string(line_num) +
                    ": Expected 'n_jobs n_machines'");
            }
            try {
                n_jobs = std::stoul(parts[0]);
                n_machines = std::stoul(parts[1]);
            } catch (const std::exception&) {
                throw std::runtime_error("Line " + std::to_string(line_num) +
                    ": Invalid n_jobs or n_machines");
            }
            break;
        }
    }

    if (n_jobs == 0 || n_machines == 0) {
        throw std::runtime_error("Error: n_jobs and n_machines must be positive");
    }

    JobShopInstance instance;
    instance.num_machines = n_machines;
    instance.jobs.resize(n_jobs);

    // ===== MACHINE SEQUENCES =====
    for (size_t j = 0; j < n_jobs; ++j) {
        instance.jobs[j].job_id = j;
        instance.jobs[j].operations.resize(n_machines);

        // Skip comments and empty lines
        while (std::getline(file, line)) {
            line_num++;
            if (!is_comment_line(line)) break;
        }

        auto machines = split_by_delimiter(line, ' ');
        if (machines.size() < n_machines) {
            throw std::runtime_error("Line " + std::to_string(line_num) +
                ": Job " + std::to_string(j) + " - not enough machine IDs");
        }

        for (size_t op = 0; op < n_machines; ++op) {
            try {
                size_t machine_id = std::stoul(machines[op]);
                if (machine_id >= n_machines) {
                    throw std::runtime_error("Invalid machine ID");
                }
                instance.jobs[j].operations[op].machine_id = machine_id;
                instance.jobs[j].operations[op].job_id = j; // TODO: do usuniecia
                instance.jobs[j].operations[op].operation_id = op;
            } catch (const std::exception&) {
                throw std::runtime_error("Line " + std::to_string(line_num) +
                    ": Job " + std::to_string(j) + " Op " + std::to_string(op) +
                    " - invalid machine ID");
            }
        }
    }

    // ===== PROCESSING TIMES =====
    for (size_t j = 0; j < n_jobs; ++j) {
        while (std::getline(file, line)) {
            line_num++;
            if (!is_comment_line(line)) break;
        }

        auto times = split_by_delimiter(line, ' ');
        if (times.size() < n_machines) {
            throw std::runtime_error("Line " + std::to_string(line_num) +
                ": Job " + std::to_string(j) + " - not enough processing times");
        }

        for (size_t op = 0; op < n_machines; ++op) {
            try {
                int proc_time = std::stoi(times[op]);
                if (proc_time <= 0) {
                    throw std::runtime_error("Processing time must be positive");
                }
                instance.jobs[j].operations[op].processing_time = proc_time;
            } catch (const std::exception&) {
                throw std::runtime_error("Line " + std::to_string(line_num) +
                    ": Job " + std::to_string(j) + " Op " + std::to_string(op) +
                    " - invalid processing time");
            }
        }
    }

    // ===== TRANSPORT TIMES MATRIX =====
    instance.transport_times.resize(n_machines, std::vector<int>(n_machines, 0));
    for (size_t i = 0; i < n_machines; ++i) {
        while (std::getline(file, line)) {
            line_num++;
            if (!is_comment_line(line)) break;
        }

        auto transports = split_by_delimiter(line, ' ');
        if (transports.size() < n_machines) {
            throw std::runtime_error("Line " + std::to_string(line_num) +
                ": Machine " + std::to_string(i) + " - not enough transport times");
        }

        for (size_t k = 0; k < n_machines; ++k) {
            try {
                int transport_time = std::stoi(transports[k]);
                if (transport_time < 0) {
                    throw std::runtime_error("Transport time cannot be negative");
                }
                instance.transport_times[i][k] = transport_time;
            } catch (const std::exception&) {
                throw std::runtime_error("Line " + std::to_string(line_num) +
                    ": Transport time from M" + std::to_string(i) + " to M" +
                    std::to_string(k) + " - invalid value");
            }
        }
    }

    return instance;
}

// ===== CSV FORMAT PARSER =====

JobShopInstance parse_csv_format(std::ifstream& file) {
    std::string line;
    size_t line_num = 0;
    size_t n_jobs = 0;
    size_t n_machines = 0;

    // Read header
    while (std::getline(file, line)) {
        line_num++;
        if (!is_comment_line(line)) {
            auto header = split_by_delimiter(line, ',');
            if (header.size() < 2) {
                throw std::runtime_error("CSV Line " + std::to_string(line_num) +
                    ": Expected 'n_jobs,n_machines'");
            }
            try {
                n_jobs = std::stoul(header[0]);
                n_machines = std::stoul(header[1]);
            } catch (const std::exception&) {
                throw std::runtime_error("CSV Line " + std::to_string(line_num) +
                    ": Invalid values");
            }
            break;
        }
    }

    if (n_jobs == 0 || n_machines == 0) {
        throw std::runtime_error("Error: n_jobs and n_machines must be positive");
    }

    JobShopInstance instance;
    instance.num_machines = n_machines;
    instance.jobs.resize(n_jobs);

    // ===== MACHINE SEQUENCES =====
    for (size_t j = 0; j < n_jobs; ++j) {
        instance.jobs[j].job_id = j;
        instance.jobs[j].operations.resize(n_machines);

        while (std::getline(file, line)) {
            line_num++;
            if (!is_comment_line(line)) break;
        }

        auto machines = split_by_delimiter(line, ',');
        if (machines.size() < n_machines) {
            throw std::runtime_error("CSV Line " + std::to_string(line_num) +
                ": Not enough machine IDs for job " + std::to_string(j));
        }

        for (size_t op = 0; op < n_machines; ++op) {
            try {
                size_t machine_id = std::stoul(machines[op]);
                if (machine_id >= n_machines) {
                    throw std::runtime_error("Invalid machine ID");
                }
                instance.jobs[j].operations[op].machine_id = machine_id;
                instance.jobs[j].operations[op].job_id = j;
                instance.jobs[j].operations[op].operation_id = op;
            } catch (const std::exception&) {
                throw std::runtime_error("CSV Line " + std::to_string(line_num) +
                    ": Invalid machine ID for job " + std::to_string(j));
            }
        }
    }

    // ===== PROCESSING TIMES =====
    for (size_t j = 0; j < n_jobs; ++j) {
        while (std::getline(file, line)) {
            line_num++;
            if (!is_comment_line(line)) break;
        }

        auto times = split_by_delimiter(line, ',');
        if (times.size() < n_machines) {
            throw std::runtime_error("CSV Line " + std::to_string(line_num) +
                ": Not enough processing times for job " + std::to_string(j));
        }

        for (size_t op = 0; op < n_machines; ++op) {
            try {
                int proc_time = std::stoi(times[op]);
                if (proc_time <= 0) {
                    throw std::runtime_error("Processing time must be positive");
                }
                instance.jobs[j].operations[op].processing_time = proc_time;
            } catch (const std::exception&) {
                throw std::runtime_error("CSV Line " + std::to_string(line_num) +
                    ": Invalid processing time for job " + std::to_string(j));
            }
        }
    }

    // ===== TRANSPORT TIMES MATRIX =====
    instance.transport_times.resize(n_machines, std::vector<int>(n_machines, 0));
    for (size_t i = 0; i < n_machines; ++i) {
        while (std::getline(file, line)) {
            line_num++;
            if (!is_comment_line(line)) break;
        }

        auto transports = split_by_delimiter(line, ',');
        if (transports.size() < n_machines) {
            throw std::runtime_error("CSV Line " + std::to_string(line_num) +
                ": Not enough transport times for machine " + std::to_string(i));
        }

        for (size_t k = 0; k < n_machines; ++k) {
            try {
                int transport_time = std::stoi(transports[k]);
                if (transport_time < 0) {
                    throw std::runtime_error("Transport time cannot be negative");
                }
                instance.transport_times[i][k] = transport_time;
            } catch (const std::exception&) {
                throw std::runtime_error("CSV Line " + std::to_string(line_num) +
                    ": Invalid transport time");
            }
        }
    }

    return instance;
}

// ===== VALIDATION =====

void validate_instance(const JobShopInstance& instance) {
    if (instance.jobs.empty()) {
        throw std::runtime_error("Instance has no jobs");
    }
    if (instance.num_machines == 0) {
        throw std::runtime_error("Instance has no machines");
    }
    if (instance.transport_times.size() != instance.num_machines) {
        throw std::runtime_error("Transport matrix size mismatch");
    }
    for (size_t i = 0; i < instance.transport_times.size(); ++i) {
        if (instance.transport_times[i].size() != instance.num_machines) {
            throw std::runtime_error("Transport matrix row " + std::to_string(i) + 
                " has incorrect size");
        }
    }
}

// ===== MAIN LOADER =====

JobShopInstance load_instance_from_file(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        throw std::runtime_error("Cannot open file: " + filename);
    }

    FileFormat format = detect_format(filename);
    JobShopInstance instance;

    try {
        switch (format) {
            case FileFormat::TXT:
                instance = parse_txt_format(file);
                break;

            case FileFormat::CSV:
                instance = parse_csv_format(file);
                break;

            case FileFormat::JSON:
                throw std::runtime_error("JSON format not yet implemented");

            default:
                throw std::runtime_error("Unknown file format");
        }

        validate_instance(instance);
        return instance;

    } catch (const std::exception& e) {
        throw std::runtime_error("Error loading '" + filename + "': " + 
                                std::string(e.what()));
    }
}

} // namespace jobshop
