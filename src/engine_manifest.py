ENGINE_MANIFEST = {
    "name": "CLOUDBURNER17",
    "mode": "zero-data",
    "modules": [
        "agent_core",
        "benchmark_agent",
        "stabiliser",
        "harmony",
        "autonomy",
        "orchestrator",
        "agent_interface",
        "agent_memory",
        "agent_validator",
        "waxtablet_adapter",
        "runtime_ignition",
    ],
    "invariants": {
        "zero_data": True,
        "deterministic_execution": True,
        "sentinel_reproducibility": True,
        "no_persistence": True,
    },
    "cycles": {
        "harmonic": {
            "steps": ["burn", "ignite", "residue"],
            "autonomy": True,
            "stabiliser": True,
        }
    },
}
