#pragma once

#include <string>
#include <vector>
#include <cstdint>

struct TiffInfo {
    uint32_t width = 0;
    uint32_t height = 0;
    uint32_t num_slices = 0;
};

class TiffIO {
public:
    // Read the dimensions and count the number of slices in a multipage TIFF
    static TiffInfo read_header(const std::string& filename);

    // Read a specific slice, crop to [x1, x2) and [y1, y2). 
    // Converts RGB to grayscale if needed, outputs standard Float32 image.
    static std::vector<float> read_slice_crop(
        const std::string& filename, uint32_t slice_idx, 
        uint32_t y1, uint32_t y2, uint32_t x1, uint32_t x2);

    // Write a dense 3D volume of floats (normalised to uint16) as an LZW-compressed TIFF
    static bool write_volume_uint16(
        const std::string& filename, 
        const std::vector<float>& volume, 
        uint32_t width, uint32_t height, uint32_t depth);
};
