"""Versioned synthetic inputs and executable experiment contracts."""

FIXTURE_VERSION = "scandoc-fixtures/1"
POLICY_VERSION = "scandoc-policy/1"

SEMANTIC = {
    "shared-core": [["core", "cause:a"], ["core", "effect:b"]],
    "persistent-disagreement": [["core", "claim:p"], ["core", "claim:not-p"]],
    "forced-generic-compression": [["cause:a"], ["effect:b"]],
}

CONTRACT = {
    "semantic": {
        "representations": ["identity", "coarse", "distinction-preserving"],
        "coarse_rule": "replace every symbol with generic",
        "distinction_rule": "bijective prefix encoding",
        "overlap": "mean pairwise Jaccard of symbol sets",
        "retention": "fraction of original unique symbols individually decodable",
        "discarded": "original symbols not individually decodable",
        "size": "symbol counts only; not validated semantic MDL",
        "contradiction": ["claim:p", "claim:not-p"],
        "updates": "none; static representation controls, not attraction",
    },
    "geometry": {
        "generator": "src.tentacled_sphere.TentacledSphere",
        "seed": 1.0,
        "delta": 0.1137,
        "ticks": 4,
        "time_step": 0.1,
        "frame": {"origin": [0, 0, 0], "axes": "right-handed Cartesian"},
        "units": "synthetic dimensionless coordinates",
        "rotation": "(x,y,z) -> (-y,x,z)",
        "frame_change": "rotation then translation by (2,-3,1)",
        "deformation": "add 0.25 to x of TAP_CONVEX at every tick",
        "shuffle_order": [2, 0, 3, 1],
        "distance_invariant": "all labeled within-tick Euclidean pair distances",
        "temporal_metric": "sum of adjacent-tick Euclidean displacements",
        "residue": "displacement projected along/perpendicular to original radial unit vector",
        "residue_scope": "coordinate-dependent decomposition, not physical flux or manifold residue",
        "reference": "raw coordinates, not renderer or fitted sphere",
        "boundary": "no boundary manifold supplied; removal/replacement unsupported",
        "tolerance": 1e-10,
    },
    "recovery": {
        "training": [[0.0, 0.0, 0.0], [0.02, 0.0, 0.0], [-0.02, 0.0, 0.0]],
        "held_out": [[0.01, 0.01, 0.0], [-0.01, 0.0, 0.01]],
        "fit": "coordinate mean of training only",
        "calibration": "maximum training distance to fitted target only",
        "operator": "parabolic_step_down(state,target,control_offset=0.7,t=0.25)",
        "contraction_factor": 0.675,
        "perturbation": [0.1, 0.0, 0.0],
        "max_perturbation": 0.25,
        "steps": 12,
        "scope": "synthetic executable contraction; not Tap dynamics",
    },
    "bounds": {
        "max_responses": 32,
        "max_symbols_per_response": 128,
        "max_symbol_length": 80,
        "max_coordinate": 1e6,
        "max_points": 32,
        "max_ticks": 32,
    },
}
