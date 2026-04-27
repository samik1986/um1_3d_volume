function save_cw_json(cw_json, out_path)
    % SAVE_CW_JSON Translates purely the parsed or edited mathematical JSON bounds straight down to text representations flawlessly.
    
    try
        json_str = jsonencode(cw_json, 'PrettyPrint', true);
    catch
        json_str = jsonencode(cw_json);
    end
    
    fid = fopen(out_path, 'w');
    if fid > 0
        fwrite(fid, json_str, 'char');
        fclose(fid);
        fprintf('Saved edited native network structurally out strictly to bounds: %s\n', out_path);
    else
        error('Could not save raw arrays natively over bounds.');
    end
end
