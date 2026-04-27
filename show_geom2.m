addpath('cw_graph_tools');
cw_json = load_cw_json('fp_pipeline_output/SubVol1_Angle000_cw_complex.json');
for i = 1:length(cw_json.cells_1_linestrings)
  geom = cw_json.cells_1_linestrings(i).geometry;
  if size(geom, 2) ~= 2
    fprintf('Line %d width is not 2. Size = [%d, %d]\n', i, size(geom,1), size(geom,2));
    if iscell(geom)
      fprintf('It is a cell array.\n');
    elseif size(geom, 1) == 2 && size(geom, 2) == 1
      fprintf('It is a 2x1 array? Values: [%f, %f]\n', geom(1), geom(2));
    end
  end
end
