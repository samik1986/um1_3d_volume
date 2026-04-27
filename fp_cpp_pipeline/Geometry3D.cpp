#include "Geometry3D.hpp"
#include <cmath>
#include <algorithm>
#include <iostream>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace std;

// 1. Analytical MIP
vector<float> Geometry3D::compute_mip(
    const vector<float>& V_sub, 
    uint32_t H, uint32_t W, uint32_t D, float theta_deg, float clip_val) 
{
    vector<float> mip(H * W, 0.0f);
    float cx = (W + 1.0f) / 2.0f;
    float cz = (D + 1.0f) / 2.0f;
    float cos_t = cos(theta_deg * M_PI / 180.0f);
    float sin_t = sin(theta_deg * M_PI / 180.0f);

    vector<int> col_map(D * W);
    for (int z = 0; z < D; z++) {
        float Z_rel = (z + 1.0f) - cz;
        for (int x = 0; x < W; x++) {
            float X_orig = (x + 1.0f) - cx;
            float proj = (X_orig * cos_t) - (Z_rel * sin_t) + cx;
            col_map[z * W + x] = (int)round(proj) - 1; // 0-indexed
        }
    }

    // Accumulate MIP
    for (int z = 0; z < D; z++) {
        const float* slice_data = &V_sub[z * (H * W)];
        for (int x = 0; x < W; x++) {
            int px_col = col_map[z * W + x];
            if (px_col >= 0 && px_col < (int)W) {
                for (int y = 0; y < H; y++) {
                    float val = slice_data[y * W + x];
                    int mip_idx = y * W + px_col;
                    if (val > mip[mip_idx]) mip[mip_idx] = val;
                }
            }
        }
    }

    // Clip and normalize
    float max_v = 0;
    for (int i = 0; i < H * W; i++) {
        if (mip[i] > clip_val) mip[i] = clip_val;
        if (mip[i] > max_v) max_v = mip[i];
    }
    if (max_v > 0) {
        for (int i = 0; i < H * W; i++) mip[i] /= max_v;
    }

    return mip;
}

// 2. Extract Endpoints (Farthest Pair)
pair<Coords2D, Coords2D> Geometry3D::extract_endpoints(const vector<Coords2D>& coords) {
    if (coords.empty()) return {{0,0},{0,0}};
    if (coords.size() == 1) return {coords[0], coords[0]};

    // Find geometrical center
    double mean_r = 0, mean_c = 0;
    for (const auto& pt : coords) {
        mean_r += pt.r; mean_c += pt.c;
    }
    mean_r /= coords.size();
    mean_c /= coords.size();

    // Find point farthest from center
    double max_dist1 = -1;
    Coords2D p1 = coords[0];
    for (const auto& pt : coords) {
        double d = (pt.r - mean_r)*(pt.r - mean_r) + (pt.c - mean_c)*(pt.c - mean_c);
        if (d > max_dist1) { max_dist1 = d; p1 = pt; }
    }

    // Find point farthest from p1
    double max_dist2 = -1;
    Coords2D p2 = coords[0];
    for (const auto& pt : coords) {
        double d = (pt.r - p1.r)*(pt.r - p1.r) + (pt.c - p1.c)*(pt.c - p1.c);
        if (d > max_dist2) { max_dist2 = d; p2 = pt; }
    }

    return {p1, p2};
}

// 3. Draw 3D Line
void Geometry3D::draw_3d_line(
    vector<uint8_t>& V_recon, uint32_t H, uint32_t W, uint32_t D,
    float r1, float c1, float z1, float r2, float c2, float z2) 
{
    float dr = r2 - r1, dc = c2 - c1, dz = z2 - z1;
    float dist = sqrt(dr*dr + dc*dc + dz*dz);
    int num_pts = (int)ceil(dist) * 2 + 1;

    for (int i = 0; i <= num_pts; i++) {
        float f = (float)i / num_pts;
        int r = (int)round(r1 + f * dr);
        int c = (int)round(c1 + f * dc);
        int z = (int)round(z1 + f * dz);

        if (r >= 1 && r <= H && c >= 1 && c <= W && z >= 1 && z <= D) {
            V_recon[(z - 1)*(H*W) + (r - 1)*W + (c - 1)] = 1;
        }
    }
}

// 4. Triangulate and Draw Lines
void Geometry3D::triangulate_and_draw_lines(
    vector<uint8_t>& V_recon, uint32_t H, uint32_t W, uint32_t D,
    const pair<Coords2D, Coords2D>& ep1, float theta1,
    const pair<Coords2D, Coords2D>& ep2, float theta2)
{
    if(ep1.first.r == 0 || ep2.first.r == 0) return;
    
    float t1 = theta1 * M_PI / 180.0f;
    float t2 = theta2 * M_PI / 180.0f;
    float tan1 = tan(t1), tan2 = tan(t2);

    float cx = (W + 1.0f) / 2.0f;
    float cz = (D + 1.0f) / 2.0f;

    auto triangulate = [&](float u1, float u2) -> pair<float, float> {
        float x_rel1 = u1 - cx, x_rel2 = u2 - cx;
        float z_rel = 0, x_orig = 0;
        
        if (abs(cos(t1)) < 1e-6) {
            z_rel = -x_rel1 / sin(t1);
            x_orig = (x_rel2 + z_rel * sin(t2)) / cos(t2);
        } else if (abs(cos(t2)) < 1e-6) {
            z_rel = -x_rel2 / sin(t2);
            x_orig = (x_rel1 + z_rel * sin(t1)) / cos(t1);
        } else {
            z_rel = (x_rel2 / cos(t2) - x_rel1 / cos(t1)) / (tan(t1) - tan(t2));
            x_orig = (x_rel1 + z_rel * sin(t1)) / cos(t1);
        }
        return {x_orig + cx, z_rel + cz};
    };

    // Mean row is used as Y coordinate
    float mean_r_A = (ep1.first.r + ep2.first.r) / 2.0f;
    float mean_r_B = (ep1.second.r + ep2.second.r) / 2.0f;

    auto [x_A, z_A] = triangulate(ep1.first.c, ep2.first.c);
    auto [x_B, z_B] = triangulate(ep1.second.c, ep2.second.c);

    draw_3d_line(V_recon, H, W, D, mean_r_A, x_A, z_A, mean_r_B, x_B, z_B);

    // Also draw alternate matching just in case ends flipped
    auto [x_A_alt, z_A_alt] = triangulate(ep1.first.c, ep2.second.c);
    auto [x_B_alt, z_B_alt] = triangulate(ep1.second.c, ep2.first.c);
    
    // Choose the matching that produces smaller depth variance (simplistic stereoscopic heuristic)
    float diff1 = abs(z_A - z_B);
    float diff2 = abs(z_A_alt - z_B_alt);
    if (diff2 < diff1) {
        V_recon.assign(H * W * D, 0); // clear
        draw_3d_line(V_recon, H, W, D, mean_r_A, x_A_alt, z_A_alt, mean_r_B, x_B_alt, z_B_alt);
    }
}

// 5. Backproject Skeletons
void Geometry3D::backproject_skeletons(
    vector<uint8_t>& V_recon,
    const vector<float>& V_sub, uint32_t H, uint32_t W, uint32_t D,
    const vector<Coords2D>& coords, float theta_deg)
{
    if (coords.empty()) return;

    float cx = (W + 1.0f) / 2.0f;
    float cz = (D + 1.0f) / 2.0f;
    float cos_t = cos(theta_deg * M_PI / 180.0f);
    float sin_t = sin(theta_deg * M_PI / 180.0f);

    vector<float> MIP_max(H * W, -1.0f);
    vector<uint16_t> DepthMap(H * W, 0);

    // Build local depth map for this specific quadrant volume
    for (int z = 0; z < D; z++) {
        float Z_rel = (z + 1.0f) - cz;
        for (int x = 0; x < W; x++) {
            float X_orig = (x + 1.0f) - cx;
            float proj = (X_orig * cos_t) - (Z_rel * sin_t) + cx;
            int px_col = (int)round(proj) - 1;

            if (px_col >= 0 && px_col < W) {
                for (int y = 0; y < H; y++) {
                    float val = V_sub[z * (H * W) + y * W + x];
                    int midx = y * W + px_col;
                    if (val > MIP_max[midx]) {
                        MIP_max[midx] = val;
                        DepthMap[midx] = z + 1; // 1-indexed initially
                    }
                }
            }
        }
    }

    // For every coordinated skeleton pixel, look up its depth
    for (const auto& pt : coords) {
        int r = pt.r - 1, c = pt.c - 1; // to 0-index
        if (r < 0 || r >= H || c < 0 || c >= W) continue;

        int z_mip = DepthMap[r * W + c];
        if (z_mip < 1 || z_mip > D) continue;

        float X_proj_rel = (c + 1.0f) - cx;
        float Z_rel_v = z_mip - cz;
        float X_orig_v;
        if (abs(cos_t) > 1e-6) {
            X_orig_v = (X_proj_rel + Z_rel_v * sin_t) / cos_t + cx;
        } else {
            X_orig_v = -Z_rel_v / sin_t + cx;
        }

        int ox = (int)round(X_orig_v) - 1; // to 0-index
        int z_f = z_mip - 1;
        if (ox >= 0 && ox < W && z_f >= 0 && z_f < D) {
            V_recon[z_f * (H * W) + r * W + ox] = 1;
        }
    }
}
