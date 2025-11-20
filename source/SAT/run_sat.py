import argparse
import sys
import os
from SAT.solver_sat import ensure_folders, solve_all, json_write

def main(range_values: tuple[float, float]):
    lower, upper = range_values
    print(f"Running SAT on range {lower}-{upper}")

    results = {}

    for n in range(6, 18, 2):
        if not (lower <= n <= upper):
            continue

        print(f"Running SAT for n = {n} ...")

        data = solve_all(n)

        json_write(n, data)

        print(f"Saved result for n={n}")   # ← FIXED (replaces print(path))

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
