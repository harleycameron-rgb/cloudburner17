import sys

sys.dont_write_bytecode = True

from supervisor import Supervisor
from ignite import ignite
from burn_harness import burn_harness
from residue import Residue
from autonomy import autonomous_cycle


def create_supervisor():
    sup = Supervisor()

    sup.add_step(
        "burn",
        action=lambda: burn_harness([1, 2, 3], [0.5, 0.7], [0, 1, 2]),
        verify=lambda out: "lambda_updated" in out,
    )

    sup.add_step(
        "ignite",
        action=lambda: ignite([1, 2, 3], [0.5, 0.7], [0, 1, 2]),
        verify=lambda out: "InvariantEngine" in out,
    )

    sup.add_step(
        "residue",
        action=lambda: Residue([1.0, 2.0, 3.0], "mapping-definition"),
        verify=lambda out: isinstance(out[0], float),
    )
    return sup


def run_pipeline(sup):
    cycle = autonomous_cycle(sup)
    return cycle["results"], cycle["residue"]


def main():
    results, residue = run_pipeline(create_supervisor())
    for result in results:
        print(result)
    print(residue)


if __name__ == "__main__":
    main()
