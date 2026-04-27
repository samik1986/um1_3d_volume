function cw_json = load_cw_json(json_path)
    % LOAD_CW_JSON Dynamically parses the target JSON CW object natively extracting strictly formatting bounds over the arrays.
    
    fid = fopen(json_path, 'r');
    if fid < 0
        error('Could not open file natively: %s', json_path);
    end
    raw_text = fscanf(fid, '%c');
    fclose(fid);
    
    cw_json = jsondecode(raw_text);
    fprintf('Loaded JSON network structure bypassing tree parsing completely.\n');
end
