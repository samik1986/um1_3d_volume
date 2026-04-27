#include "TiffIO.hpp"
#include <tiffio.h>
#include <iostream>
#include <stdexcept>

TiffInfo TiffIO::read_header(const std::string& filename) {
    TIFF* tif = TIFFOpen(filename.c_str(), "r");
    if (!tif) throw std::runtime_error("Cannot open TIFF: " + filename);

    TiffInfo info;
    TIFFGetField(tif, TIFFTAG_IMAGEWIDTH, &info.width);
    TIFFGetField(tif, TIFFTAG_IMAGELENGTH, &info.height);
    
    info.num_slices = 0;
    do { info.num_slices++; } while (TIFFReadDirectory(tif));
    
    TIFFClose(tif);
    return info;
}

std::vector<float> TiffIO::read_slice_crop(
    const std::string& filename, uint32_t slice_idx, 
    uint32_t y1, uint32_t y2, uint32_t x1, uint32_t x2) 
{
    TIFF* tif = TIFFOpen(filename.c_str(), "r");
    if (!tif) throw std::runtime_error("Cannot open TIFF");

    TIFFSetDirectory(tif, slice_idx - 1); // 0-indexed in libtiff
    
    uint32_t w, h;
    uint16_t bps, spp;
    TIFFGetField(tif, TIFFTAG_IMAGEWIDTH, &w);
    TIFFGetField(tif, TIFFTAG_IMAGELENGTH, &h);
    TIFFGetField(tif, TIFFTAG_BITSPERSAMPLE, &bps);
    TIFFGetField(tif, TIFFTAG_SAMPLESPERPIXEL, &spp);

    if(y2 > h) y2 = h;
    if(x2 > w) x2 = w;
    uint32_t crop_h = y2 - y1;
    uint32_t crop_w = x2 - x1;

    std::vector<float> result(crop_h * crop_w, 0.0f);
    
    // We use TIFFReadRGBAImageOriented which safely handles all formats (8-bit, 16-bit, RGB, Grayscale, etc)
    // and converts them to an 8-bit RGBA stream in memory. (Warning: 16-bit dynamic range is compressed to 8-bit, 
    // but the MATLAB pipeline also often read RGB as 8-bit). 
    // To preserve full 16-bit, we do manual scanline reads if it's Grayscale.
    
    if (spp == 1 && (bps == 8 || bps == 16)) {
        tdata_t buf = _TIFFmalloc(TIFFScanlineSize(tif));
        for (uint32_t y = 0; y < h; y++) {
            TIFFReadScanline(tif, buf, y);
            if (y >= y1 && y < y2) {
                uint32_t out_y = y - y1;
                if (bps == 8) {
                    uint8_t* ptr = (uint8_t*)buf;
                    for (uint32_t x = x1; x < x2; x++) result[out_y * crop_w + (x - x1)] = ptr[x];
                } else if (bps == 16) {
                    uint16_t* ptr = (uint16_t*)buf;
                    for (uint32_t x = x1; x < x2; x++) result[out_y * crop_w + (x - x1)] = ptr[x];
                }
            }
        }
        _TIFFfree(buf);
    } else {
        // Fallback to RGBA converter for RGB/Palette images
        std::vector<uint32_t> raster(w * h);
        TIFFReadRGBAImageOriented(tif, w, h, raster.data(), ORIENTATION_TOPLEFT, 0);
        for (uint32_t y = y1; y < y2; y++) {
            uint32_t out_y = y - y1;
            for (uint32_t x = x1; x < x2; x++) {
                uint32_t pixel = raster[y * w + x];
                uint8_t r = TIFFGetR(pixel);
                uint8_t g = TIFFGetG(pixel);
                uint8_t b = TIFFGetB(pixel);
                result[out_y * crop_w + (x - x1)] = 0.299f * r + 0.587f * g + 0.114f * b;
            }
        }
    }
    
    TIFFClose(tif);
    return result;
}

bool TiffIO::write_volume_uint16(
    const std::string& filename, 
    const std::vector<float>& volume, 
    uint32_t width, uint32_t height, uint32_t depth) 
{
    TIFF* tif = TIFFOpen(filename.c_str(), "w8");
    if (!tif) return false;

    for (uint32_t z = 0; z < depth; z++) {
        TIFFSetField(tif, TIFFTAG_IMAGEWIDTH, width);
        TIFFSetField(tif, TIFFTAG_IMAGELENGTH, height);
        TIFFSetField(tif, TIFFTAG_SAMPLESPERPIXEL, 1);
        TIFFSetField(tif, TIFFTAG_BITSPERSAMPLE, 16);
        TIFFSetField(tif, TIFFTAG_ORIENTATION, ORIENTATION_TOPLEFT);
        TIFFSetField(tif, TIFFTAG_PLANARCONFIG, PLANARCONFIG_CONTIG);
        TIFFSetField(tif, TIFFTAG_PHOTOMETRIC, PHOTOMETRIC_MINISBLACK);
        TIFFSetField(tif, TIFFTAG_COMPRESSION, COMPRESSION_LZW);
        TIFFSetField(tif, TIFFTAG_ROWSPERSTRIP, 32);

        std::vector<uint16_t> strip_buf(width);
        for (uint32_t y = 0; y < height; y++) {
            for (uint32_t x = 0; x < width; x++) {
                float v = volume[z * (width * height) + y * width + x];
                strip_buf[x] = static_cast<uint16_t>(v * 65535.0f);
            }
            TIFFWriteScanline(tif, strip_buf.data(), y, 0);
        }
        TIFFWriteDirectory(tif);
    }

    TIFFClose(tif);
    return true;
}
