from supervisor import Supervisor
from ignite import ignite
from burn_harness import burn_harness
from residue import Residue

sup = Supervisor()

sup.add_step(
    "burn",
    action=lambda: burn_harness([1,2,3],[0.5,0.7],[0,1,2]),
    verify=lambda out: "lambda_updated" in out
)

sup.add_step(
    "ignite",
    action=lambda: ignite([1,2,3],[0.5,0.7],[0,1,2]),
    verify=lambda out: "InvariantEngine" in out
)

sup.add_step(
    "residue",
    action=lambda: Residue([1.0,2.0,3.0],"mapping-definition"),
    verify=lambda out: isinstance(out[0], float)
)

print(sup.run("burn", "y"))
print(sup.run("ignite", "y"))
print(sup.run("residue", "y"))
print(sup.residue())
