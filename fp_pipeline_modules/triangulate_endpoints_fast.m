function [pt1, pt2] = triangulate_endpoints_fast( ...
        pts_start, pts_end, angles, H, W, D, cx_img, cy_img, cz_img)
% Memory-safe stereo triangulation.  No large 3D array allocated.
% Uses Y-axis disparity between consecutive angle pairs to solve for depth.
%
%   Forward projection (Y-rotation):
%     col_proj = (ox - cx)*cos(t) - (oz - cz)*sin(t) + cx
%   => oz = ((ox-cx)*cos(t) - (col_proj-cx)) / sin(t) + cz
%
% Accumulate (ox, oy, oz) votes via a running mean, clamp to [1..W/H/D].

n = size(pts_start, 1);

xs_acc = 0; ys_acc = 0; zs_acc = 0; ns = 0;
xe_acc = 0; ye_acc = 0; ze_acc = 0; ne = 0;

for i = 1:n-1
    t1 = deg2rad(angles(i));
    t2 = deg2rad(angles(i+1));
    dt = t2 - t1;
    if abs(sin(dt)) < 1e-4, continue; end

    % --- start-point triangulation ---
    c1s = pts_start(i,   1);  r1s = pts_start(i,   2);
    c2s = pts_start(i+1, 1);
    if isnan(c1s) || isnan(c2s), continue; end
    % disparity gives depth at angle t1
    xl_s  = c1s - cx_img;   xr_s = c2s - cx_img;
    oz_s  = (xl_s*cos(dt) - xr_s) / sin(dt) + cz_img;
    ox_s  = c1s;             oy_s = r1s;
    % inverse-rotate ox from padded-image col to volume W space
    cos1  = cos(t1);  sin1 = sin(t1);
    if abs(cos1) > 1e-6
        ox_orig_s = round((xl_s + (oz_s - cz_img)*sin1) / cos1 + cx_img);
    else
        ox_orig_s = cx_img;
    end
    ox_orig_s = max(1, min(W, round(ox_orig_s)));
    oy_s      = max(1, min(H, round(oy_s)));
    oz_s_int  = max(1, min(D, round(oz_s)));
    xs_acc = xs_acc + oy_s;   % row -> Y in volume
    ys_acc = ys_acc + ox_orig_s; % col -> X in volume
    zs_acc = zs_acc + oz_s_int;
    ns = ns + 1;

    % --- end-point triangulation ---
    c1e = pts_end(i,   1);  r1e = pts_end(i,   2);
    c2e = pts_end(i+1, 1);
    if isnan(c1e) || isnan(c2e), continue; end
    xl_e  = c1e - cx_img;  xr_e = c2e - cx_img;
    oz_e  = (xl_e*cos(dt) - xr_e) / sin(dt) + cz_img;
    ox_e  = c1e;
    if abs(cos1) > 1e-6
        ox_orig_e = round((xl_e + (oz_e - cz_img)*sin1) / cos1 + cx_img);
    else
        ox_orig_e = cx_img;
    end
    ox_orig_e = max(1, min(W, round(ox_orig_e)));
    oy_e      = max(1, min(H, round(r1e)));
    oz_e_int  = max(1, min(D, round(oz_e)));
    xe_acc = xe_acc + oy_e;
    ye_acc = ye_acc + ox_orig_e;
    ze_acc = ze_acc + oz_e_int;
    ne = ne + 1;
end

if ns > 0
    pt1 = [round(xs_acc/ns), round(ys_acc/ns), round(zs_acc/ns)];
else
    pt1 = [NaN, NaN, NaN];
end
if ne > 0
    pt2 = [round(xe_acc/ne), round(ye_acc/ne), round(ze_acc/ne)];
else
    pt2 = [NaN, NaN, NaN];
end
end


% -------------------------------------------------------------------------
