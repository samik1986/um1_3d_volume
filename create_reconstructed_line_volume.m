function V_line_recon = create_reconstructed_line_volume(recon_pt1, recon_pt2, volSize)
    % CREATE_RECONSTRUCTED_LINE_VOLUME Takes spatial vertex matches generating dense line traces.
    
    V_line_recon = zeros(volSize, 'single');
    
    if any(isnan(recon_pt1)) || any(isnan(recon_pt2))
        warning('Cannot formulate reconstruction volume; bounds contain NaN.');
        return;
    end
    
    num_points = max(abs(recon_pt2 - recon_pt1)) * 2;
    if num_points == 0, num_points = 1; end
    
    X_line = round(linspace(recon_pt1(1), recon_pt2(1), num_points));
    Y_line = round(linspace(recon_pt1(2), recon_pt2(2), num_points));
    Z_line = round(linspace(recon_pt1(3), recon_pt2(3), num_points));

    for k = 1:length(X_line)
        if X_line(k)>=1 && X_line(k)<=volSize(1) && ...
           Y_line(k)>=1 && Y_line(k)<=volSize(2) && ...
           Z_line(k)>=1 && Z_line(k)<=volSize(3)
            V_line_recon(X_line(k), Y_line(k), Z_line(k)) = 1;
        end
    end
    
    % Step 5 Figure Artifact Generation
    figure('Name', 'Step 5: Reconstructed Line Volume');
    [x, y, z] = ind2sub(volSize, find(V_line_recon));
    scatter3(x, y, z, 50, 'b', 'filled');
    axis([0 volSize(1) 0 volSize(2) 0 volSize(3)]);
    grid on; box on; view(3); xlabel('X'); ylabel('Y'); zlabel('Z');
    title('Step 5: Reconstructed 3D Line Trace');
end
