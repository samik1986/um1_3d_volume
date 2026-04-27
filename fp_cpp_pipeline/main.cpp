#include <iostream>
#include <vector>
#include <string>
#include <cmath>
#include <cstdio>
#include <omp.h>
#include "TiffIO.hpp"
#include "Filters2D.hpp"
#include "Geometry3D.hpp"

using namespace std;

// Main orchestration Pipeline
int main(int argc, char** argv) {
    // Disable stdout buffering for real-time logs in PowerShell pipes
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    string input_tiff = "FP.tif";
    string output_tiff = "fp_pipeline_output/FP_reconstructed_cpp.tif";

    if (argc > 1) input_tiff = argv[1];
    if (argc > 2) output_tiff = argv[2];

    cout << "== Step 1: Reading TIFF header ==\n";
    fflush(stdout);
    TiffInfo info;
    try {
        info = TiffIO::read_header(input_tiff);
    } catch(const exception& e) {
        cerr << "Error: " << e.what() << "\n";
        return 1;
    }
    cout << "   Volume: " << info.height << " rows x " << info.width 
         << " cols x " << info.num_slices << " slices\n";

    uint32_t H = info.height, W = info.width, D = info.num_slices;
    
    // The final stitched output volume
    vector<float> ReconFull(H * W * D, 0.0f);

    // 4 quadrants strategy
    uint32_t q_rows[4][2] = {
        {0, H/2}, {0, H/2}, {H/2, H}, {H/2, H}
    };
    uint32_t q_cols[4][2] = {
        {0, W/2}, {W/2, W}, {0, W/2}, {W/2, W}
    };

    vector<float> angles = {0.0f, 15.0f, 30.0f, 45.0f};

    cout << "== Step 2: Processing 4 Quadrants concurrently via OpenMP ==\n";

    // OpenMP Parallel region! Each quadrant processed on a separate thread.
    #pragma omp parallel for schedule(dynamic, 1)
    for (int q = 0; q < 4; q++) {
        uint32_t y1 = q_rows[q][0], y2 = q_rows[q][1];
        uint32_t x1 = q_cols[q][0], x2 = q_cols[q][1];
        uint32_t sub_H = y2 - y1;
        uint32_t sub_W = x2 - x1;

        int tid = omp_get_thread_num();
        #pragma omp critical
        cout << "[Thread " << tid << "] Starting Q" << q+1 << " (" << sub_H << "x" << sub_W << ")\n";

        // 1. Array containing the quadrant TIFF volume block
        vector<float> V_sub(sub_H * sub_W * D, 0.0f);
        for (uint32_t z = 0; z < D; z++) {
            auto slice = TiffIO::read_slice_crop(input_tiff, z+1, y1, y2, x1, x2);
            for(uint32_t i = 0; i < slice.size(); i++) V_sub[z * (sub_H * sub_W) + i] = slice[i];
        }

        // Local reconstruction volume for this quadrant
        vector<uint8_t> V_recon_sub(sub_H * sub_W * D, 0);

        vector<pair<Coords2D, Coords2D>> endpoints_all;
        vector<vector<Coords2D>> skeletons_all;

        for (float theta : angles) {
            // A. Compute MIP analytically
            auto mip = Geometry3D::compute_mip(V_sub, sub_H, sub_W, D, theta, 1.0f);

            // B. Extract vesselness (Frangi)
            auto vesselness = Filters2D::frangi_filter(mip, sub_W, sub_H, 2.5f);

            // C. Binarise and Morphological filtering
            auto bw = Filters2D::adaptive_binarize(vesselness, sub_W, sub_H, 50, 0.8f);
            Filters2D::area_open(bw, sub_W, sub_H, 350);
            Filters2D::zhang_suen_thinning(bw, sub_W, sub_H);
            
            // Extract sparse coordinates
            auto coords = Filters2D::extract_coordinates(bw, sub_W, sub_H);
            skeletons_all.push_back(coords);

            // D. Farthest pair endpoints
            auto eps = Geometry3D::extract_endpoints(coords);
            endpoints_all.push_back(eps);
        }

        // F. Triangulate central lines stereoscopically
        Geometry3D::triangulate_and_draw_lines(V_recon_sub, sub_H, sub_W, D,
                                               endpoints_all[0], angles[0], 
                                               endpoints_all[3], angles[3]);

        // G. Backproject Skeletons into local quadrant
        for (size_t ai = 0; ai < angles.size(); ai++) {
            Geometry3D::backproject_skeletons(V_recon_sub, V_sub, sub_H, sub_W, D, 
                                              skeletons_all[ai], angles[ai]);
        }

        // H. Stitch back to Main volume (Thread Safe, separate spatial arrays)
        for (uint32_t z = 0; z < D; z++) {
            for (uint32_t y = 0; y < sub_H; y++) {
                for (uint32_t x = 0; x < sub_W; x++) {
                    if (V_recon_sub[z*(sub_H*sub_W) + y*sub_W + x] > 0) {
                        uint32_t global_y = y1 + y;
                        uint32_t global_x = x1 + x;
                        ReconFull[z*(H*W) + global_y*W + global_x] = 1.0f;
                    }
                }
            }
        }
        
        #pragma omp critical
        cout << "[Thread " << tid << "] Finished Q" << q+1 << "\n";
    }

    cout << "== Step 3: Saving multipage output to " << output_tiff << " ==\n";
    // Usually need system call `mkdir fp_pipeline_output` externally, assume it exists or write to dot
    // but just in case, save local to build dir.
    output_tiff = "FP_reconstructed_cpp.tif";

    bool success = TiffIO::write_volume_uint16(output_tiff, ReconFull, W, H, D);
    if(success) cout << "SUCCESS. Saved to " << output_tiff << "\n";
    else cout << "FAILED to write output file.\n";

    return 0;
}
