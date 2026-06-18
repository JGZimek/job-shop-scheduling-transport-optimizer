cmake_minimum_required(VERSION 3.16)
project(JobShopSchedulingTransportOptimizer 
    VERSION 1.0.0 
    DESCRIPTION "Job Shop Scheduling with Transport Times Optimizer"
    LANGUAGES CXX
)

# ===== CMAKE SETTINGS =====
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ===== COMPILER FLAGS =====
if(MSVC)
    add_compile_options(/W4 /WX /permissive-)
    set(CMAKE_CXX_FLAGS_RELEASE "/O2 /DNDEBUG")
    set(CMAKE_CXX_FLAGS_DEBUG "/Zi /Od /RTC1")
elseif(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic -Wconversion)
    if(MINGW)
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -static-libgcc -static-libstdc++")
    endif()
    set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")
    set(CMAKE_CXX_FLAGS_DEBUG "-g -O0")
endif()

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "Compiler: ${CMAKE_CXX_COMPILER_ID}")

# ===== INCLUDE DIRECTORIES =====
include_directories(cpp/include)

# ===== SOURCE FILES =====
file(GLOB_RECURSE CORE_SOURCES
    cpp/src/core/*.cpp
    cpp/src/genetic/*.cpp
    cpp/src/greedy/*.cpp
    cpp/src/exact/*.cpp
    cpp/src/io/*.cpp
)

message(STATUS "Found core sources: ${CORE_SOURCES}")

# ===== PYBIND11 DISCOVERY =====
message(STATUS "Searching for pybind11...")

set(PYBIND11_FINDPYTHON ON)

# Try system-wide first
find_package(pybind11 CONFIG QUIET)

# If not found, try venv paths
if(NOT pybind11_FOUND)
    # Get Python executable and extract path
    execute_process(
        COMMAND python -c "import pybind11; print(pybind11.get_cmake_dir())"
        OUTPUT_VARIABLE PYBIND11_CMAKE_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
        RESULT_VARIABLE PYBIND11_EXEC_RESULT
    )
    
    if(PYBIND11_EXEC_RESULT EQUAL 0 AND PYBIND11_CMAKE_DIR)
        message(STATUS "Found pybind11 CMake dir: ${PYBIND11_CMAKE_DIR}")
        find_package(pybind11 CONFIG PATHS "${PYBIND11_CMAKE_DIR}" QUIET)
    endif()
endif()

# Fallback to common venv paths
if(NOT pybind11_FOUND)
    if(WIN32)
        find_package(pybind11 CONFIG PATHS
            "${CMAKE_CURRENT_SOURCE_DIR}/.venv/Lib/site-packages/pybind11/share/cmake"
            "C:/Users/*/AppData/Local/*/Python*/site-packages/pybind11/share/cmake"
            QUIET
        )
    else()
        # Linux/macOS/WSL
        find_package(pybind11 CONFIG PATHS
            "${CMAKE_CURRENT_SOURCE_DIR}/.venv/lib/python*/site-packages/pybind11/share/cmake"
            "/home/*/.*/.venv/lib/python*/site-packages/pybind11/share/cmake"
            "/usr/local/lib/python*/dist-packages/pybind11/share/cmake"
            QUIET
        )
    endif()
endif()

if(NOT pybind11_FOUND)
    message(FATAL_ERROR "pybind11 not found!\n"
        "Install via: pip install pybind11\n"
        "Then run: python -c \"import pybind11; print(pybind11.get_cmake_dir())\""
    )
endif()

message(STATUS "[OK] pybind11 found at: ${pybind11_DIR}")

# ===== PYTHON BINDINGS MODULE =====
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/cpp/bindings/bindings.cpp")
    set(BINDING_FILE "cpp/bindings/bindings.cpp")
elseif(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/cpp/bindings/jobshop_bindings.cpp")
    set(BINDING_FILE "cpp/bindings/jobshop_bindings.cpp")
else()
    message(FATAL_ERROR "Cannot find bindings file in bindings/ directory!")
endif()

message(STATUS "Using binding file: ${BINDING_FILE}")

pybind11_add_module(bindings 
    ${BINDING_FILE}
    ${CORE_SOURCES}
)

target_include_directories(bindings PRIVATE cpp/include)

set_target_properties(bindings PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/python_module"
)

if(MINGW)
    set_target_properties(bindings PROPERTIES
        INTERPROCEDURAL_OPTIMIZATION OFF
    )
endif()

message(STATUS "[OK] Python module: ${CMAKE_BINARY_DIR}/python_module")

# ===== CLI EXECUTABLE =====
add_executable(jobshop_optimizer
    cpp/src/main.cpp
    ${CORE_SOURCES}
)

target_include_directories(jobshop_optimizer PRIVATE cpp/include)

set_target_properties(jobshop_optimizer PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

message(STATUS "[OK] CLI executable: ${CMAKE_BINARY_DIR}/bin")

# ===== SUMMARY =====
message(STATUS "")
message(STATUS "=== Build Configuration ===")
message(STATUS "Project: ${PROJECT_NAME} v${PROJECT_VERSION}")
message(STATUS "C++ Standard: C++${CMAKE_CXX_STANDARD}")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "Compiler: ${CMAKE_CXX_COMPILER_ID}")
message(STATUS "pybind11: ${pybind11_VERSION}")
message(STATUS "")
message(STATUS "Targets to build:")
message(STATUS "  - Python Module: jobshop_bindings")
message(STATUS "  - CLI Executable: jobshop_optimizer")
message(STATUS "")
