from harmony import align_modules
from stabiliser import enforce_zero_data, harmonise_state, verify_sentinel


def autonomous_cycle(supervisor):
    results = []
    for name in supervisor.steps:
        result = supervisor.run(name, "y")
        results.append(result)
        if result.get("status") != "completed":
            raise RuntimeError(f"autonomous supervised step failed: {name}")

    harmonise_state(supervisor.state_log)
    align_modules({name: output for name, output, _ in supervisor.state_log})
    enforce_zero_data()
    residue = supervisor.residue()
    if not verify_sentinel(residue["sentinel"]):
        raise RuntimeError("sentinel did not reproduce")
    return {"results": results, "residue": residue}


def invariant_loop():
    from run_supervised_build import create_supervisor

    return autonomous_cycle(create_supervisor())


def self_verify():
    first = invariant_loop()
    second = invariant_loop()
    enforce_zero_data()
    return (
        first["results"] == second["results"]
        and first["residue"]["sentinel"] == second["residue"]["sentinel"]
        and verify_sentinel(first["residue"]["sentinel"])
    )
