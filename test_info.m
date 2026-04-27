info = imfinfo('F0200_multichannel_cmle_ch04.tif');
fprintf('Size: %d x %d x %d\n', info(1).Height, info(1).Width, numel(info));
