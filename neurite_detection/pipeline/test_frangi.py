import cupy as cp
import cupyx.scipy.ndimage as cp_ndi

def eigh_3x3_analytical(dxx, dyy, dzz, dxy, dxz, dyz):
    p1 = dxx + dyy + dzz
    p2 = dxx*dyy + dxx*dzz + dyy*dzz - dxy**2 - dxz**2 - dyz**2
    p3 = dxx*dyy*dzz + 2*dxy*dxz*dyz - dxx*dyz**2 - dyy*dxz**2 - dzz*dxy**2
    
    a = p1 / 3.0
    p = p2 - p1 * a
    q = p1 * p2 / 3.0 - p3 - 2.0 * (a**3)
    
    p_div_3 = p / 3.0
    rho = cp.sqrt(cp.maximum(-p_div_3**3, 0))
    
    theta = cp.arccos(cp.clip(-q / (2.0 * rho + 1e-15), -1.0, 1.0))
    
    sqrt_p = cp.sqrt(cp.maximum(-p_div_3, 0))
    r1 = 2.0 * sqrt_p * cp.cos(theta / 3.0)
    r2 = 2.0 * sqrt_p * cp.cos((theta + 2.0 * cp.pi) / 3.0)
    r3 = 2.0 * sqrt_p * cp.cos((theta + 4.0 * cp.pi) / 3.0)
    
    L1_raw = r1 + a
    L2_raw = r2 + a
    L3_raw = r3 + a
    
    L_stack = cp.stack([L1_raw, L2_raw, L3_raw], axis=-1)
    abs_eig = cp.abs(L_stack)
    sort_indices = cp.argsort(abs_eig, axis=-1)
    L_sorted = cp.take_along_axis(L_stack, sort_indices, axis=-1)
    
    return L_sorted[..., 0], L_sorted[..., 1], L_sorted[..., 2]

def frangi_3d(img, sigma=1.0, alpha=0.5, beta=0.5, c=None):
    img_smooth = cp_ndi.gaussian_filter(img, sigma)
    
    grad_z = cp.gradient(img_smooth, axis=0)
    grad_y = cp.gradient(img_smooth, axis=1)
    grad_x = cp.gradient(img_smooth, axis=2)
    
    dzz = cp.gradient(grad_z, axis=0) * (sigma ** 2)
    dyy = cp.gradient(grad_y, axis=1) * (sigma ** 2)
    dxx = cp.gradient(grad_x, axis=2) * (sigma ** 2)
    
    dyz = cp.gradient(grad_y, axis=0) * (sigma ** 2)
    dxz = cp.gradient(grad_x, axis=0) * (sigma ** 2)
    dxy = cp.gradient(grad_x, axis=1) * (sigma ** 2)
    
    L1, L2, L3 = eigh_3x3_analytical(dxx, dyy, dzz, dxy, dxz, dyz)
    
    L2_sq = L2 ** 2
    L3_sq = L3 ** 2
    
    Ra = cp.abs(L2) / (cp.abs(L3) + 1e-10)
    Rb = cp.abs(L1) / cp.sqrt(cp.abs(L2 * L3) + 1e-10)
    S_sq = L1**2 + L2_sq + L3_sq
    
    if c is None:
        c = cp.max(S_sq) ** 0.5 * 0.5
        if c == 0:
            c = 1.0
            
    term1 = 1 - cp.exp(-(Ra**2) / (2 * alpha**2))
    term2 = cp.exp(-(Rb**2) / (2 * beta**2))
    term3 = 1 - cp.exp(-S_sq / (2 * c**2))
    
    vesselness = term1 * term2 * term3
    
    vesselness[L2 > 0] = 0
    vesselness[L3 > 0] = 0
    vesselness[cp.isnan(vesselness)] = 0
    
    return vesselness

if __name__ == "__main__":
    a = cp.random.rand(32, 64, 64).astype(cp.float32)
    v = frangi_3d(a)
    print("Analytical Frangi test complete. Max:", v.max())
