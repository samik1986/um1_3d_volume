function save_nrrd_volume(vol, filename)
% Save uint16 3D volume as an NRRD file.
fid = fopen(filename, 'w', 'l');  % explicitly little-endian
if fid < 0
    warning('Could not open %s for writing.', filename);
    return;
end

% Permute from MATLAB native (Y, X, Z) to standard medical (X, Y, Z) geometry
vol_p = permute(vol, [2, 1, 3]);

fprintf(fid, 'NRRD0004\n');
fprintf(fid, 'type: uint16\n');
fprintf(fid, 'dimension: 3\n');
fprintf(fid, 'space: left-posterior-superior\n');
fprintf(fid, 'sizes: %d %d %d\n', size(vol_p, 1), size(vol_p, 2), size(vol_p, 3));
fprintf(fid, 'space directions: (1,0,0) (0,1,0) (0,0,1)\n');
fprintf(fid, 'kinds: domain domain domain\n');
fprintf(fid, 'endian: little\n');
fprintf(fid, 'encoding: raw\n');
fprintf(fid, 'space origin: (0,0,0)\n');
fprintf(fid, '\n');

fwrite(fid, vol_p, 'uint16');
fclose(fid);
fprintf('   Saved: %s\n', filename);
end
