import sys

sys.dont_write_bytecode = True

if __package__:
    from .autonomy import autonomous_cycle
    from .pipeline import create_supervisor
else:
    from autonomy import autonomous_cycle
    from pipeline import create_supervisor


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
