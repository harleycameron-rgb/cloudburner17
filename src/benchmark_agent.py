import numpy as np
import pandas as pd

# -----------------------------
#  PRE-REGISTERED ENCODINGS
# -----------------------------

def phi(x):
    """Map structural input x to s0 on S^2."""
    v = np.array(x, dtype=float)
    return v / np.linalg.norm(v)

def A(p):
    """Contextual pressure encoding."""
    return np.eye(3) * np.array(p, dtype=float)

def G(s):
    """Gate mapping surface state to core."""
    return np.array([s[0], s[1]])

def F(z, u):
    """Arterial flow field evaluated at u inside B^3."""
    return np.array([z[0] * u[0], z[1] * u[1], 0.0])

# -----------------------------
#  SEPARATE PARABOLIC STEP-DOWN
# -----------------------------

def parabolic_step_down(s, u, control_offset=0.7, t=1.0):
    """
    Quadratic Bézier parabola.
    This is *not* the sandbox parabola.
    """
    c = s + control_offset * (u - s)
    return (1 - t)**2 * s + 2*t*(1 - t) * c + t**2 * u

# -----------------------------
#  BENCHMARK COMPUTATION
# -----------------------------

def compute_benchmark_row(row):
    x = row['x_params']
    p = row['p_params']

    # Sphere model
    s0 = phi(x)

    # Tangential displacement
    vp = (np.eye(3) - np.outer(s0, s0)) @ A(p)
    sp = (s0 + vp) / np.linalg.norm(s0 + vp)

    # Surface drift
    D_surface = np.arccos(np.clip(s0 @ sp, -1, 1))

    # Optional: step-down parabola (separate from sandbox)
    u0 = s0[:2]
    up = sp[:2]
    s0_surf = parabolic_step_down(s0, u0)
    sp_surf = parabolic_step_down(sp, up)

    # Core drift
    z0 = G(s0)
    zp = G(sp)
    D_core = np.linalg.norm(zp - z0)

    # Flow drift
    N = 100
    us = np.random.randn(N, 3)
    us = us / np.linalg.norm(us, axis=1, keepdims=True) * np.random.rand(N, 1)

    flow_diffs = []
    for u in us:
        f0 = F(z0, u)
        fp = F(zp, u)
        flow_diffs.append(np.linalg.norm(fp - f0)**2)

    D_flow = np.sqrt(np.mean(flow_diffs))

    return pd.Series({
        'D_surface': D_surface,
        'D_core': D_core,
        'D_flow': D_flow,
        's0': s0.tolist(),
        'sp': sp.tolist(),
        'z0': z0.tolist(),
        'zp': zp.tolist(),
        's0_surf': s0_surf.tolist(),
        'sp_surf': sp_surf.tolist()
    })

# -----------------------------
#  BENCHMARK AGENT
# -----------------------------

class BenchmarkAgent:
    def __init__(self, df):
        self.df = df
        self.results = None

    def run(self):
        self.results = self.df.apply(compute_benchmark_row, axis=1)
        return self.results

    def worst_case_leakage(self):
        return self.results['D_core'].max()

    def structural_control(self, x, x_prime):
        """Ensure structural difference is non-vacuous."""
        return np.linalg.norm(G(phi(x_prime)) - G(phi(x)))
