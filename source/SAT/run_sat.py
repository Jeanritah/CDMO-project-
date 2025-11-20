import argparse
import sys
import os
from SAT.solver_sat import ensure_folders, solve_all, json_write

def main(range_vals: tuple[float, float]):

    ensure_folders()

    n_values = [8, 10, 12, 14, 16]

    results = {}

    for n in n_values:
        print(f"Running SAT for n = {n} ...")

        data = solve_all(n)

        # Save JSON
        path = f"res/SAT/{n}.json"
        json_write(path, data)

        print(f"saved: {path}")

        results[n] = data

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SAT CLI")
    parser.add_argument(
        "--range",
        type=float,
        nargs=2,
        required=False,
        metavar=("LOWER", "UPPER"),
        help="(ignored) Range required by main.py"
    )
    args = parser.parse_args()
    if args.range is None:
        main((0.0, 1.0))
    else:
        main(tuple(args.range))
