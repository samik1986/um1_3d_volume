function fig = overlay_lines(pt1_orig, pt2_orig, recon_pt1, recon_pt2, volSize)
    % OVERLAY_LINES Securely models final geometric evaluations natively aligning dual architectures.
    
    fig = figure('Name', 'Step 6: Mathematical Overlay Comparison', 'Position', [100, 100, 800, 800]);
    hold on; grid on; box on; view(3);
    axis([0 volSize(1) 0 volSize(2) 0 volSize(3)]);
    xlabel('X (Row)'); ylabel('Y (Col)'); zlabel('Z (Depth)');
    title('Step 6: Final Modular Architecture Overlay (Red = Original, Blue = Reconstructed)');

    % Abstract native baseline bounds natively
    plot3([pt1_orig(1), pt2_orig(1)], [pt1_orig(2), pt2_orig(2)], [pt1_orig(3), pt2_orig(3)], 'r', 'LineWidth', 5);
    
    if ~any(isnan(recon_pt1)) && ~any(isnan(recon_pt2))
        plot3([recon_pt1(1), recon_pt2(1)], [recon_pt1(2), recon_pt2(2)], [recon_pt1(3), recon_pt2(3)], 'b--', 'LineWidth', 2);
        
        h1 = scatter3(NaN, NaN, NaN, 100, 'r', 'filled', 'MarkerFaceAlpha', 0.5);
        h2 = plot3([NaN,NaN], [NaN,NaN], [NaN,NaN], 'b--', 'LineWidth', 2);
        legend([h1, h2], {'Original Ground-Truth Trajectory', 'Bridged Modular Pipeline Result'}, 'Location', 'best');
    end
    hold off;
end
