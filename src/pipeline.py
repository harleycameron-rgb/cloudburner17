if __package__:
    from .supervisor import Supervisor
    from .ignite import ignite
    from .burn_harness import burn_harness
    from .residue import Residue
else:
    from supervisor import Supervisor
    from ignite import ignite
    from burn_harness import burn_harness
    from residue import Residue


def create_supervisor():
    supervisor = Supervisor()
    supervisor.add_step(
        "burn",
        action=lambda: burn_harness([1, 2, 3], [0.5, 0.7], [0, 1, 2]),
        verify=lambda output: "lambda_updated" in output,
    )
    supervisor.add_step(
        "ignite",
        action=lambda: ignite([1, 2, 3], [0.5, 0.7], [0, 1, 2]),
        verify=lambda output: "InvariantEngine" in output,
    )
    supervisor.add_step(
        "residue",
        action=lambda: Residue([1.0, 2.0, 3.0], "mapping-definition"),
        verify=lambda output: isinstance(output[0], float),
    )
    return supervisor
