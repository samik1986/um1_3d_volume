cmake_minimum_required(VERSION 3.14)
project(FP_Volume_Pipeline CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find OpenMP to vastly accelerate the 3D volume mapping
find_package(OpenMP REQUIRED)

# Use FetchContent to automatically download and build standard ZLIB and TIFF
# so the user doesn't have to manually install them on Windows!
include(FetchContent)

# 1. ZLIB (required by TIFF)
FetchContent_Declare(
    ZLIB
    GIT_REPOSITORY https://github.com/madler/zlib.git
    GIT_TAG        v1.2.13
)
FetchContent_MakeAvailable(ZLIB)

# 2. LibTIFF
FetchContent_Declare(
    TIFF
    GIT_REPOSITORY https://gitlab.com/libtiff/libtiff.git
    GIT_TAG        v4.5.1
)
# Disable unwanted TIFF utilities/docs during build
set(tiff-tools OFF CACHE BOOL "" FORCE)
set(tiff-tests OFF CACHE BOOL "" FORCE)
set(tiff-contrib OFF CACHE BOOL "" FORCE)
set(tiff-docs OFF CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(TIFF)

# Main Executable
add_executable(fp_pipeline_v2 main.cpp TiffIO.cpp Filters2D.cpp Geometry3D.cpp)

# Link Libraries
target_link_libraries(fp_pipeline_v2 PRIVATE OpenMP::OpenMP_CXX tiff)
target_include_directories(fp_pipeline_v2 PRIVATE ${TIFF_SOURCE_DIR}/libtiff)

# Enable aggressive optimisations
if(MSVC)
    target_compile_options(fp_pipeline_v2 PRIVATE /O2 /fp:fast /arch:AVX2 /wd4244 /wd4267)
else()
    target_compile_options(fp_pipeline_v2 PRIVATE -O3 -ffast-math -mavx2)
endif()
