@echo off
echo Running pipeline for F0046...
python run_pipeline.py --input ..\data_046\F0046_multichannel_cmle_ch03.tif --outdir ..\NEWFP_output --no-vis
echo Done!
pause
