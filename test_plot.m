addpath('cw_graph_tools');
cw_json = load_cw_json('fp_pipeline_output/SubVol1_Angle000_cw_complex.json');
plot_cw_complex(cw_json);
disp('Execution passed purely array constraints fully natively without throwing errors.');
