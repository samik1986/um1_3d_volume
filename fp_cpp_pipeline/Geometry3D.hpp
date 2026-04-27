#pragma once
#include "Filters2D.hpp"
#include <vector>

class Geometry3D {
public:
    // Computes analytical MIP for a given angle slice-by-slice mapping
    static std::vector<float> compute_mip(
        const std::vector<float>& V_sub, 
        uint32_t H, uint32_t W, uint32_t D, float theta_deg, float clip_val);

    // Endpoint Extraction (farthest pair of lit pixels)
    static std::pair<Coords2D, Coords2D> extract_endpoints(
        const std::vector<Coords2D>& coords);

    // Draw 3D Line between two 3D spatial points
    static void draw_3d_line(
        std::vector<uint8_t>& V_recon, uint32_t H, uint32_t W, uint32_t D,
        float r1, float c1, float z1, float r2, float c2, float z2);

    // EndToEnd lightweight stereo triangulation and line building
    static void triangulate_and_draw_lines(
        std::vector<uint8_t>& V_recon, uint32_t H, uint32_t W, uint32_t D,
        const std::pair<Coords2D, Coords2D>& ep1, float theta1,
        const std::pair<Coords2D, Coords2D>& ep2, float theta2);

    // Dense vectorised slice-by-slice back-projection
    static void backproject_skeletons(
        std::vector<uint8_t>& V_recon,
        const std::vector<float>& V_sub, uint32_t H, uint32_t W, uint32_t D,
        const std::vector<Coords2D>& coords, float theta_deg);
};
