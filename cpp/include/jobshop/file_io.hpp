#ifndef JOBSHOP_FILE_IO_HPP
#define JOBSHOP_FILE_IO_HPP

#include "jobshop/solution.hpp"
#include <string>
#include <fstream>
#include <sstream>
#include <vector>
#include <stdexcept>

namespace jobshop {

/**
 * File format enumeration
 */
enum class FileFormat { TXT, CSV, JSON };

/**
 * Detect file format from filename extension
 */
FileFormat detect_format(const std::string& filename);

/**
 * Load job shop instance from file (supports TXT and CSV)
 * 
 * File format (TXT/CSV):
 * - Line 1: n_jobs n_machines
 * - Lines 2 to n_jobs+1: Machine sequence for each job
 * - Lines n_jobs+2 to 2*n_jobs+1: Processing times for each job
 * - Lines 2*n_jobs+2 to 2*n_jobs+1+n_machines: Transport times matrix
 * 
 * Comments starting with # and empty lines are ignored.
 */
JobShopInstance load_instance_from_file(const std::string& filename);

/**
 * Format-specific parsers (internal use)
 */
JobShopInstance parse_txt_format(std::ifstream& file);
JobShopInstance parse_csv_format(std::ifstream& file);

/**
 * Validate loaded instance
 */
void validate_instance(const JobShopInstance& instance);

} // namespace jobshop

#endif // JOBSHOP_FILE_IO_HPP
