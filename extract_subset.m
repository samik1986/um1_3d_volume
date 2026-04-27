function extract_subset()
    % EXTRACT_SUBSET Extracts a central 512x512 subset from FP.tif for testing.
    input_file = 'FP.tif';
    output_file = 'FP_subset_512.tif';
    
    info = imfinfo(input_file);
    num_slices = numel(info);
    height = info(1).Height;
    width = info(1).Width;
    
    % Define central region
    sub_size = 512;
    r1 = floor(height/2) - floor(sub_size/2);
    r2 = r1 + sub_size - 1;
    c1 = floor(width/2) - floor(sub_size/2);
    c2 = c1 + sub_size - 1;
    
    fprintf('Extracting subset: rows %d:%d, cols %d:%d from %d slices...\n', r1, r2, c1, c2, num_slices);
    
    % Read and save slice by slice to avoid RAM issues
    for z = 1:num_slices
        if mod(z, 50) == 0, fprintf('Processing slice %d/%d...\n', z, num_slices); end
        
        % Read pixel region
        slice_sub = imread(input_file, z, 'Info', info, 'PixelRegion', {[r1, r2], [c1, c2]});
        
        % Write to new TIFF
        if z == 1
            imwrite(slice_sub, output_file, 'WriteMode', 'overwrite', 'Compression', 'none');
        else
            imwrite(slice_sub, output_file, 'WriteMode', 'append', 'Compression', 'none');
        end
    end
    
    fprintf('Subset saved to %s\n', output_file);
end
