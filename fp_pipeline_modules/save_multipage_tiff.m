function save_multipage_tiff(vol, filename)
% Save uint16 3D volume as an LZW-compressed multipage TIFF.
num_slices = size(vol, 3);
t = Tiff(filename, 'w');
tagstruct.ImageLength        = size(vol, 1);
tagstruct.ImageWidth         = size(vol, 2);
tagstruct.Photometric        = Tiff.Photometric.MinIsBlack;
tagstruct.BitsPerSample      = 16;
tagstruct.SampleFormat       = Tiff.SampleFormat.UInt;
tagstruct.SamplesPerPixel    = 1;
tagstruct.RowsPerStrip       = 32;
tagstruct.PlanarConfiguration = Tiff.PlanarConfiguration.Chunky;
tagstruct.Compression        = Tiff.Compression.LZW;
for z = 1:num_slices
    if z > 1, t.writeDirectory(); end
    t.setTag(tagstruct);
    t.write(vol(:,:,z));
    if mod(z, 50) == 0
        fprintf('   Saved slice %d / %d\n', z, num_slices);
    end
end
t.close();
fprintf('   Saved: %s\n', filename);
end

% -------------------------------------------------------------------------
