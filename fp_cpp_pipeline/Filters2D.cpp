#include "Filters2D.hpp"
#include <cmath>
#include <algorithm>
#include <queue>
#include <iostream>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace std;

// 1. Separable Gaussian
vector<float> Filters2D::gaussian_blur(const vector<float>& img, uint32_t w, uint32_t h, float sigma) {
    if (sigma <= 0) return img;
    int r = (int)ceil(3.0 * sigma);
    vector<float> kernel(2 * r + 1);
    float sum = 0;
    for (int i = -r; i <= r; i++) {
        kernel[i + r] = exp(-(i * i) / (2 * sigma * sigma));
        sum += kernel[i + r];
    }
    for (float& k : kernel) k /= sum;

    vector<float> temp(w * h, 0.0f);
    // Horizontal pass
    for (uint32_t y = 0; y < h; y++) {
        for (uint32_t x = 0; x < w; x++) {
            float val = 0;
            for (int i = -r; i <= r; i++) {
                int cx = std::max(0, std::min((int)w - 1, (int)x + i));
                val += img[y * w + cx] * kernel[i + r];
            }
            temp[y * w + x] = val;
        }
    }
    vector<float> out(w * h, 0.0f);
    // Vertical pass
    for (uint32_t y = 0; y < h; y++) {
        for (uint32_t x = 0; x < w; x++) {
            float val = 0;
            for (int i = -r; i <= r; i++) {
                int cy = std::max(0, std::min((int)h - 1, (int)y + i));
                val += temp[cy * w + x] * kernel[i + r];
            }
            out[y * w + x] = val;
        }
    }
    return out;
}

// 2. Frangi Vesselness
vector<float> Filters2D::frangi_filter(const vector<float>& img, uint32_t w, uint32_t h, float sigma) {
    auto smoothed = gaussian_blur(img, w, h, sigma);
    vector<float> vesselness(w * h, 0.0f);
    
    // Frangi parameters
    float beta = 0.5f;   // structure sensitivity
    float c = 0.01f;     // contrast (scale dependent, typically half of max Hessian norm)
    // we'll compute max norm to scale c
    float max_S = 0;

    vector<float> Lxx(w * h), Lyy(w * h), Lxy(w * h);

    for (int y = 1; y < h - 1; y++) {
        for (int x = 1; x < w - 1; x++) {
            int idx = y * w + x;
            float L = smoothed[idx];
            // Central differences
            Lxx[idx] = smoothed[idx - 1] - 2 * L + smoothed[idx + 1];
            Lyy[idx] = smoothed[idx - w] - 2 * L + smoothed[idx + w];
            Lxy[idx] = (smoothed[idx - w - 1] + smoothed[idx + w + 1] - 
                        smoothed[idx - w + 1] - smoothed[idx + w - 1]) / 4.0f;
            
            // Eigenvalues of [[Lxx, Lxy], [Lxy, Lyy]]
            float tmp1 = (Lxx[idx] + Lyy[idx]) / 2.0f;
            float tmp2 = sqrt(pow((Lxx[idx] - Lyy[idx]) / 2.0f, 2) + Lxy[idx] * Lxy[idx]);
            float lambda1 = tmp1 + tmp2;
            float lambda2 = tmp1 - tmp2;
            
            // Order by magnitude |lambda1| < |lambda2|
            if (abs(lambda1) > abs(lambda2)) swap(lambda1, lambda2);

            if (lambda2 > 0) { // We want bright vessels on dark bg (lambda2 < 0). 
                vesselness[idx] = 0;
            } else {
                float Rb = lambda1 / lambda2;
                float S = sqrt(lambda1 * lambda1 + lambda2 * lambda2);
                if (S > max_S) max_S = S;
                // Just store structural components temporarily
                vesselness[idx] = S > 1e-5f ? exp(-(Rb * Rb) / (2 * beta * beta)) : 0.0f;
                Lxx[idx] = S; // reuse Lxx to store S
            }
        }
    }
    
    c = c > 0 ? (max_S * 0.1f) : 1e-5f; // scale C based on image Hessian magnitude
    if (c < 1e-5f) c = 1e-5f;

    float max_v = 0;
    for (int i = 0; i < w * h; i++) {
        if (vesselness[i] > 0) {
            float S = Lxx[i];
            float v = vesselness[i] * (1.0f - exp(-(S * S) / (2 * c * c)));
            vesselness[i] = v;
            if (v > max_v) max_v = v;
        }
    }
    
    // Normalize to 0..1
    if (max_v > 0) {
        for (float& v : vesselness) v /= max_v;
    }
    return vesselness;
}

// 3. Adaptive Binarize
vector<uint8_t> Filters2D::adaptive_binarize(const vector<float>& img, uint32_t w, uint32_t h, uint32_t win_size, float sensitivity) {
    vector<float> integral(w * h, 0);
    // Build integral image
    for (uint32_t y = 0; y < h; y++) {
        float row_sum = 0;
        for (uint32_t x = 0; x < w; x++) {
            row_sum += img[y * w + x];
            integral[y * w + x] = row_sum + (y > 0 ? integral[(y - 1) * w + x] : 0);
        }
    }

    vector<uint8_t> bin(w * h, 0);
    int r = win_size / 2;
    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            int y1 = max(0, y - r), y2 = min((int)h - 1, y + r);
            int x1 = max(0, x - r), x2 = min((int)w - 1, x + r);
            
            float sum = integral[y2 * w + x2];
            if (x1 > 0) sum -= integral[y2 * w + (x1 - 1)];
            if (y1 > 0) sum -= integral[(y1 - 1) * w + x2];
            if (x1 > 0 && y1 > 0) sum += integral[(y1 - 1) * w + (x1 - 1)];
            
            int count = (y2 - y1 + 1) * (x2 - x1 + 1);
            float local_mean = sum / count;
            
            // Bright foreground: pixel must be greater than local_mean minus an offset
            // MATLAB sensitivity: T = mean(local) * (1 - sensitivity). We tweak to match standard scale.
            float threshold = local_mean * (1.0f - sensitivity);
            if (img[y * w + x] > threshold) {
                bin[y * w + x] = 255;
            }
        }
    }
    return bin;
}

// 4. Zhang-Suen Thinning
void Filters2D::zhang_suen_thinning(vector<uint8_t>& img, uint32_t w, uint32_t h) {
    bool has_changed = true;
    vector<uint8_t> marker(w * h, 0);

    auto get = [&](int x, int y) -> int {
        if (x < 0 || x >= w || y < 0 || y >= h) return 0;
        return img[y * w + x] > 0 ? 1 : 0;
    };

    while (has_changed) {
        has_changed = false;
        // Step 1
        for (int y = 1; y < h - 1; y++) {
            for (int x = 1; x < w - 1; x++) {
                if (!get(x, y)) continue;
                int p2 = get(x, y-1), p3 = get(x+1, y-1), p4 = get(x+1, y);
                int p5 = get(x+1, y+1), p6 = get(x, y+1), p7 = get(x-1, y+1);
                int p8 = get(x-1, y), p9 = get(x-1, y-1);

                int A  = (p2 == 0 && p3 == 1) + (p3 == 0 && p4 == 1) + 
                         (p4 == 0 && p5 == 1) + (p5 == 0 && p6 == 1) + 
                         (p6 == 0 && p7 == 1) + (p7 == 0 && p8 == 1) +
                         (p8 == 0 && p9 == 1) + (p9 == 0 && p2 == 1);
                int B  = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9;
                int m1 = p2 * p4 * p6;
                int m2 = p4 * p6 * p8;

                if (A == 1 && (B >= 2 && B <= 6) && m1 == 0 && m2 == 0) {
                    marker[y * w + x] = 1;
                    has_changed = true;
                }
            }
        }
        for (int i = 0; i < w * h; i++) {
            if (marker[i]) { img[i] = 0; marker[i] = 0; }
        }

        // Step 2
        for (int y = 1; y < h - 1; y++) {
            for (int x = 1; x < w - 1; x++) {
                if (!get(x, y)) continue;
                int p2 = get(x, y-1), p3 = get(x+1, y-1), p4 = get(x+1, y);
                int p5 = get(x+1, y+1), p6 = get(x, y+1), p7 = get(x-1, y+1);
                int p8 = get(x-1, y), p9 = get(x-1, y-1);

                int A  = (p2 == 0 && p3 == 1) + (p3 == 0 && p4 == 1) + 
                         (p4 == 0 && p5 == 1) + (p5 == 0 && p6 == 1) + 
                         (p6 == 0 && p7 == 1) + (p7 == 0 && p8 == 1) +
                         (p8 == 0 && p9 == 1) + (p9 == 0 && p2 == 1);
                int B  = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9;
                int m1 = p2 * p4 * p8;
                int m2 = p2 * p6 * p8;

                if (A == 1 && (B >= 2 && B <= 6) && m1 == 0 && m2 == 0) {
                    marker[y * w + x] = 1;
                    has_changed = true;
                }
            }
        }
        for (int i = 0; i < w * h; i++) {
            if (marker[i]) { img[i] = 0; marker[i] = 0; }
        }
    }
}

// 5. bwareaopen
void Filters2D::area_open(vector<uint8_t>& img, uint32_t w, uint32_t h, uint32_t min_area) {
    vector<bool> visited(w * h, false);
    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            if (img[y * w + x] > 0 && !visited[y * w + x]) {
                // BFS to find all connected pixels
                vector<int> blob;
                queue<int> q;
                q.push(y * w + x);
                visited[y * w + x] = true;

                while (!q.empty()) {
                    int curr = q.front();
                    q.pop();
                    blob.push_back(curr);

                    int cy = curr / w, cx = curr % w;
                    int dirs[8][2] = {{-1,0},{1,0},{0,-1},{0,1},{-1,-1},{-1,1},{1,-1},{1,1}};
                    for (auto& d : dirs) {
                        int ny = cy + d[0], nx = cx + d[1];
                        if (ny >= 0 && ny < h && nx >= 0 && nx < w) {
                            int nidx = ny * w + nx;
                            if (img[nidx] > 0 && !visited[nidx]) {
                                visited[nidx] = true;
                                q.push(nidx);
                            }
                        }
                    }
                }

                // If blob is too small, erase it
                if (blob.size() < min_area) {
                    for (int idx : blob) img[idx] = 0;
                }
            }
        }
    }
}

vector<Coords2D> Filters2D::extract_coordinates(const vector<uint8_t>& img, uint32_t w, uint32_t h) {
    vector<Coords2D> coords;
    for (uint32_t y = 0; y < h; y++) {
        for (uint32_t x = 0; x < w; x++) {
            if (img[y * w + x]) coords.push_back({y + 1, x + 1}); // 1-indexed (MATLAB match)
        }
    }
    return coords;
}
