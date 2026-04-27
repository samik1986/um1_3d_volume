#pragma once
#include <vector>
#include <cstdint>
#include <cmath>

struct Coords2D {
    uint32_t r, c;
};

class Filters2D {
public:
    // 1. Separable Gaussian blur
    static std::vector<float> gaussian_blur(
        const std::vector<float>& img, uint32_t w, uint32_t h, float sigma);

    // 2. Frangi vesselness filter (computes Hessian -> eigenvalues -> vesselness)
    // Structure sensitivity is equivalent to the beta parameter (here fixed ~0.1 - 0.5)
    static std::vector<float> frangi_filter(
        const std::vector<float>& img, uint32_t w, uint32_t h, float sigma);

    // 3. Adaptive binarization (mean of local neighborhood)
    static std::vector<uint8_t> adaptive_binarize(
        const std::vector<float>& img, uint32_t w, uint32_t h, uint32_t win_size, float sensitivity);

    // 4. Zhang-Suen morphological thinning to extract the skeleton
    // Takes binary image (255 fore, 0 back). Modifies in-place.
    static void zhang_suen_thinning(std::vector<uint8_t>& img, uint32_t w, uint32_t h);

    // 5. Remove small noise components (equivalent to bwareaopen)
    static void area_open(std::vector<uint8_t>& img, uint32_t w, uint32_t h, uint32_t min_area);

    // Helper: Convert dense logical skeleton to coordinate list
    static std::vector<Coords2D> extract_coordinates(const std::vector<uint8_t>& img, uint32_t w, uint32_t h);
};
