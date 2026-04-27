% fp_pipeline_smoketest.m
% Runs ALL local helper functions from fp_volume_pipeline
% with a tiny synthetic volume (100x80x20) to catch runtime errors fast.
% Uses addpath to access reconstruct_endpoints_stereo etc.

addpath('C:\Users\banerjee\Desktop\um1_3d_volume');
close all; clc;

%% -- Synthetic mini-volume ------------------------------------------------
rng(42);  % reproducible
H = 100; W = 80; D = 20;
angles       = [0, 15, 30, 45];
clip_val     = 500;
frangi_sigma = [2 4 6];
min_branch   = 5;
min_area     = 10;
output_dir   = 'C:\Users\banerjee\Desktop\um1_3d_volume';

% Create a volume with a bright diagonal line structure as vessel proxy
V = zeros(H, W, D, 'single');
for k = 1:D
    x = round(10 + k*2.5);  y = round(10 + k*2);
    if x<=H && y<=W
        V(max(1,x-3):min(H,x+3), max(1,y-3):min(W,y+3), k) = 400;
    end
end
V = V + 20*single(rand(H,W,D));  % add noise

fprintf('=== Smoke Test: Synthetic volume %dx%dx%d ===\n', H, W, D);

%% --- Test compute_mip_pictures -------------------------------------------
fprintf('[1] compute_mip_pictures...\n');
[pictures, W_pad] = compute_mip_pictures(V, angles, clip_val);
assert(numel(pictures) == numel(angles), 'pictures count mismatch');
assert(size(pictures{1},1) == H, 'MIP height mismatch');
assert(size(pictures{1},2) == W_pad, 'MIP width_pad mismatch');
fprintf('    OK: %d pictures, size %dx%d\n', numel(pictures), size(pictures{1},1), size(pictures{1},2));

%% --- Test compute_skeleton -----------------------------------------------
fprintf('[2] compute_skeleton...\n');
skeletons = cell(1, numel(angles));
MIPs_norm = cell(1, numel(angles));
for ai = 1:numel(angles)
    [skel, mip_n] = compute_skeleton(pictures{ai}, frangi_sigma, min_area, min_branch);
    skeletons{ai} = skel;
    MIPs_norm{ai} = mip_n;
    assert(isequal(size(skel), size(pictures{ai})), 'skeleton size mismatch');
    assert(islogical(skel), 'skeleton not logical');
end
fprintf('    OK: skeletons computed for %d angles\n', numel(angles));

%% --- Test save_overlay ---------------------------------------------------
fprintf('[3] save_overlay...\n');
for ai = 1:numel(angles)
    save_overlay(MIPs_norm{ai}, skeletons{ai}, 99, angles(ai), output_dir);
end
% Check at least one file was created
f = dir(fullfile(output_dir, 'SubVol99_*.jpg'));
assert(~isempty(f), 'No overlay files saved');
fprintf('    OK: %d overlay files written\n', numel(f));

%% --- Test extract_endpoints_silent ---------------------------------------
fprintf('[4] extract_endpoints_silent...\n');
[pts_start, pts_end] = extract_endpoints_silent(skeletons);
assert(size(pts_start,1) == numel(angles), 'pts_start row count wrong');
assert(size(pts_end,2)   == 2,             'pts_end should be Nx2');
fprintf('    OK: start pts = %s\n', mat2str(pts_start));

%% --- Test reconstruct_endpoints_stereo (suppress figures) ---------------
fprintf('[5] reconstruct_endpoints_stereo...\n');
set(0,'DefaultFigureVisible','off');
pic_size_d  = size(skeletons{1}');
volSize_pic = [H, W_pad, D];
[recon_pt1, recon_pt2] = reconstruct_endpoints_stereo(...
    pts_start, pts_end, angles, volSize_pic, pic_size_d);
set(0,'DefaultFigureVisible','on');
fprintf('    OK: recon_pt1=%s  recon_pt2=%s\n', mat2str(recon_pt1), mat2str(recon_pt2));

%% --- Test create_reconstructed_line_volume --------------------------------
fprintf('[6] create_reconstructed_line_volume...\n');
set(0,'DefaultFigureVisible','off');
V_recon = create_reconstructed_line_volume(recon_pt1, recon_pt2, [H, W, D]);
set(0,'DefaultFigureVisible','on');
assert(isequal(size(V_recon), [H, W, D]), 'V_recon size mismatch');
fprintf('    OK: V_recon size %dx%dx%d, nnz=%d\n', H,W,D, nnz(V_recon));

%% --- Test backproject_skeletons ------------------------------------------
fprintf('[7] backproject_skeletons...\n');
V_recon = backproject_skeletons(V_recon, skeletons, V, angles);
assert(isequal(size(V_recon), [H, W, D]), 'V_recon size after backproject mismatch');
fprintf('    OK: nnz after backproject = %d\n', nnz(V_recon));

%% --- Test display_volume_skeleton ----------------------------------------
fprintf('[8] display_volume_skeleton...\n');
ReconFull = single(V_recon);
display_volume_skeleton(ReconFull, D);
fprintf('    OK: display figures created\n');

%% --- Test save_multipage_tiff -------------------------------------------
fprintf('[9] save_multipage_tiff...\n');
out_tiff = fullfile(output_dir, 'smoketest_recon.tif');
save_multipage_tiff(uint16(ReconFull .* 65535), out_tiff);
assert(exist(out_tiff,'file')>0, 'TIFF not saved');
delete(out_tiff);   % clean up test artefact
fprintf('    OK: TIFF written and removed\n');

%% --- Clean up test overlay files -----------------------------------------
delete(fullfile(output_dir, 'SubVol99_*.jpg'));
delete(fullfile(output_dir, 'SubVol99_*.png'));
close all;

fprintf('\n=== ALL SMOKE TESTS PASSED ===\n');


%% ========= Local helpers (must match fp_volume_pipeline.m exactly) =======

function [pictures, W_pad] = compute_mip_pictures(V, angles, clip_val)
[H, W, D] = size(V);
max_dim  = ceil(sqrt(W^2 + D^2));
pad_W    = max_dim - W;
pad_D    = max_dim - D;
pad_pre  = [0, floor(pad_W/2), floor(pad_D/2)];
pad_post = [0, ceil(pad_W/2),  ceil(pad_D/2)];
V_pad    = padarray(V, pad_pre,  0, 'pre');
V_pad    = padarray(V_pad, pad_post, 0, 'post');
W_pad    = size(V_pad, 2);
num_ang  = numel(angles);
pictures = cell(1, num_ang);
for ai = 1:num_ang
    theta      = angles(ai);
    V_perm     = permute(V_pad, [1, 3, 2]);
    V_rot_perm = imrotate(V_perm, theta, 'bilinear', 'crop');
    V_rot      = ipermute(V_rot_perm, [1, 3, 2]);
    mip = max(V_rot, [], 3);
    clear V_rot V_rot_perm V_perm;
    mip(mip > clip_val) = clip_val;
    m = max(mip(:));
    if m > 0, mip = mip ./ m; end
    pictures{ai} = single(mip);
end
clear V_pad;
end

function [skeleton, mip_norm] = compute_skeleton(mip, sigma, min_area, min_branch)
mip = double(mip);
m   = max(mip(:));
if m <= 0
    mip_norm = single(mip); skeleton = false(size(mip)); return;
end
mip_norm = single(mip ./ m);
mip_g    = imgaussfilt(double(mip_norm), 1.5);
try
    vesselness = fibermetric(mip_g, sigma, 'StructureSensitivity', 0.01);
catch ME
    warning('fibermetric failed: %s', ME.message); vesselness = mip_g;
end
vesselness = mat2gray(double(vesselness));
BW = imbinarize(vesselness,'adaptive','ForegroundPolarity','bright','Sensitivity',0.40);
BW = bwareaopen(BW, min_area);
BW = imclose(BW, strel('disk', 2));
skeleton = bwskel(logical(BW), 'MinBranchLength', min_branch);
end

function save_overlay(mip_norm, skeleton, div_idx, angle_val, out_dir)
prefix = sprintf('SubVol%d_Angle%03d', div_idx, round(angle_val));
mip_d  = double(mip_norm);
imwrite(uint8(mip_d.*255), fullfile(out_dir,[prefix '_MIP.jpg']));
imwrite(skeleton,           fullfile(out_dir,[prefix '_Skeleton.png']));
ovr = imoverlay(mip_d, skeleton, [1,0,1]);
imwrite(ovr,               fullfile(out_dir,[prefix '_Overlay.jpg']));
end

function [pts_start, pts_end] = extract_endpoints_silent(pictures)
num_pics  = numel(pictures);
pts_start = zeros(num_pics,2); pts_end = zeros(num_pics,2);
prev_s=[]; prev_e=[];
for i = 1:num_pics
    I=[]; [r,c] = deal([]);
    I = pictures{i}';
    [r,c] = find(I > 0);
    if numel(r) < 2
        pts_start(i,:)=[NaN,NaN]; pts_end(i,:)=[NaN,NaN]; continue;
    end
    if numel(r)>2000
        idx=randperm(numel(r),2000); r=r(idx); c=c(idx);
    end
    pts=double([c,r]);
    D2=(pts(:,1)-pts(:,1)').^2+(pts(:,2)-pts(:,2)').^2;
    [~,lin]=max(D2(:)); [iA,iB]=ind2sub(size(D2),lin);
    ptA=pts(iA,:); ptB=pts(iB,:);
    if isempty(prev_s)
        if ptA(1)>ptB(1)||(ptA(1)==ptB(1)&&ptA(2)>ptB(2)), [ptA,ptB]=deal(ptB,ptA); end
    else
        if norm(ptA-prev_s)+norm(ptB-prev_e)>norm(ptB-prev_s)+norm(ptA-prev_e)
            [ptA,ptB]=deal(ptB,ptA);
        end
    end
    prev_s=ptA; prev_e=ptB;
    pts_start(i,:)=ptA; pts_end(i,:)=ptB;
end
end

function V_recon = backproject_skeletons(V_recon, skeletons, V_sub, angles)
[H,W,D] = size(V_sub);
max_dim  = ceil(sqrt(W^2+D^2));
pad_W    = max_dim-W; pad_D = max_dim-D;
pad_pre  = [0,floor(pad_W/2),floor(pad_D/2)];
pad_post = [0,ceil(pad_W/2), ceil(pad_D/2)];
W_offset = floor(pad_W/2); D_offset = floor(pad_D/2);
for ai=1:numel(angles)
    theta   = angles(ai);
    skel_2d = logical(skeletons{ai});
    V_pad   = padarray(V_sub,pad_pre,0,'pre');
    V_pad   = padarray(V_pad,pad_post,0,'post');
    D_pad=size(V_pad,3); W_pad=size(V_pad,2);
    V_perm     = permute(V_pad,[1,3,2]);
    V_rot_perm = imrotate(V_perm,theta,'nearest','crop');
    V_rot      = ipermute(V_rot_perm,[1,3,2]);
    clear V_pad V_perm V_rot_perm;
    [~,DepthMap]=max(V_rot,[],3); clear V_rot;
    W_pad_c=(W_pad+1)/2; D_pad_c=(D_pad+1)/2;
    cos_t=cos(deg2rad(theta)); sin_t=sin(deg2rad(theta));
    [row_v,col_v]=find(skel_2d);
    if isempty(row_v), clear DepthMap; continue; end
    row_v=double(row_v); col_v=double(col_v);
    ok=(row_v>=1)&(row_v<=H); row_v=row_v(ok); col_v=col_v(ok);
    if isempty(row_v), clear DepthMap; continue; end
    ok=(col_v>=1)&(col_v<=W_pad); row_v=row_v(ok); col_v=col_v(ok);
    if isempty(row_v), clear DepthMap; continue; end
    lin_idx=sub2ind([H,W_pad],row_v,col_v);
    z_pad_v=double(DepthMap(lin_idx)); clear DepthMap;
    z_orig_v=z_pad_v-D_offset;
    ok=(z_orig_v>=1)&(z_orig_v<=D);
    row_v=row_v(ok); col_v=col_v(ok); z_pad_v=z_pad_v(ok); z_orig_v=z_orig_v(ok);
    if isempty(row_v), continue; end
    cx_rel=col_v-W_pad_c; z_rel=z_pad_v-D_pad_c;
    if abs(cos_t)>1e-6
        ox_rel=(cx_rel+z_rel.*sin_t)./cos_t;
    else
        ox_rel=-z_rel./sin_t;
    end
    ox_v=round(ox_rel+W_pad_c-W_offset);
    ok=(ox_v>=1)&(ox_v<=W);
    row_f=round(row_v(ok)); ox_f=round(ox_v(ok)); z_f=round(z_orig_v(ok));
    if isempty(row_f), continue; end
    lin_recon=sub2ind(size(V_recon),row_f,ox_f,z_f);
    V_recon(lin_recon)=1;
end
end

function display_volume_skeleton(ReconFull, num_slices)
z_show=round(linspace(1,num_slices,min(5,num_slices)));
nc=numel(z_show);
figure('Visible','on','Position',[40,60,min(1600,nc*320),340]);
for si=1:nc
    z=z_show(si); sl_n=mat2gray(double(ReconFull(:,:,z)));
    R=sl_n; G=sl_n; B=sl_n; mask=sl_n>0.45;
    R(mask)=1; G(mask)=0; B(mask)=1;
    subplot(1,nc,si); imshow(cat(3,R,G,B)); title(sprintf('Z=%d',z),'FontSize',8);
end
sgtitle('Smoke Test: Skeleton Overlay');
thresh=0.3; [rx,ry,rz]=ind2sub(size(ReconFull),find(ReconFull>thresh));
if numel(rx)>5000
    idx=randperm(numel(rx),5000); rx=rx(idx); ry=ry(idx); rz=rz(idx);
end
figure('Visible','on','Position',[120,120,700,500]);
scatter3(double(ry),double(rx),double(rz),4,double(rz),'filled');
colormap(jet); xlabel('X'); ylabel('Y'); zlabel('Z');
title('3D Scatter - Smoke Test'); axis tight; grid on; view(3);
end

function save_multipage_tiff(vol, filename)
num_slices=size(vol,3);
t=Tiff(filename,'w');
tagstruct.ImageLength=size(vol,1); tagstruct.ImageWidth=size(vol,2);
tagstruct.Photometric=Tiff.Photometric.MinIsBlack;
tagstruct.BitsPerSample=16; tagstruct.SampleFormat=Tiff.SampleFormat.UInt;
tagstruct.SamplesPerPixel=1; tagstruct.RowsPerStrip=32;
tagstruct.PlanarConfiguration=Tiff.PlanarConfiguration.Chunky;
tagstruct.Compression=Tiff.Compression.LZW;
for z=1:num_slices
    if z>1, t.writeDirectory(); end
    t.setTag(tagstruct); t.write(vol(:,:,z));
end
t.close();
end
