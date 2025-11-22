"""
main.py
========
This is the main entry point for the project.

Purpose:
--------
- To provide a unified command-line interface (CLI) for running different 
    solving methods: CP, MIP, SAT, and SMT.
- To ensure all models follow a consistent interface so they can be called 
    interchangeably.
- Optionally check solutions after solving, using `solution_checker.py`.

Expected Structure:
-------------------
Each model (e.g. CP, MIP, SAT, SMT) must have a file named `run_<method>.py`
inside its corresponding folder under `source/`.

Example:
    source/
        CP/run_cp.py
        MIP/run_mip.py
        SAT/run_sat.py
        SMT/run_smt.py

Each of these files must expose a top-level function:

    def main(input_path: str) -> dict:
        ...

which:
- takes as arguments:
    - n a range of instances to be solved,
    - solver's name,
    - (eventually other solver-specific parameters),
- returns for each instance:
output: "Result saved to {output_path}"
"""

import argparse
import subprocess
import sys
from run_cp import main as run_cp_main
from run_mip import main as run_mip_main
from run_sat import main as run_sat_main
from run_smt import main as run_smt_main
from utils import utils

#TODO add a method that transforms single instances results into a table if the
# number of models is > 1. The table should have the following format:
# instance num | model_solver_name1 | model_solver_name2 |....| For each 
# instance under the model_solver_nameN column the value will be: - in seconds 
# if the time is <300 s - UNSAT if the model is UNSATISFIABLE for that specific 
# instance - N/A if time >= 300s
# make this output friendly for copying it into latex lately

def main():
    parser = argparse.ArgumentParser(description="Main entry point for the project.")

    parser.add_argument(
        "--mode",
        choices=["CP", "MIP", "SAT", "SMT"],
        nargs="+",
        default=["CP", "MIP", "SAT", "SMT"],
        help="Choose one or more solving methods to run (e.g. --mode CP SMT)."
    )

    parser.add_argument(
        "--range",
        type=int,
        nargs=2,
        metavar=('LOWER', 'UPPER'),
        required=True,
        help="Specify the instance range as two numbers, e.g. --range 0.1 0.9"
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check the solution after solving."
    )

    args = parser.parse_args()

    model_functions = {
        "CP": run_cp_main,
        "MIP": run_mip_main,
        "SAT": run_sat_main,
        "SMT": run_smt_main,
    }

    results = {}

    for mode in args.mode:
        teams = utils.convert_to_range(args.range)
        # this function should call also other parameters, but parameters change depending on the model...
        # how to solve this? 
        # If no additional parameter is added the model is run on all possible configurations for that model
        
        result = model_functions[mode](teams)
        results[mode] = result
        print(f"{mode} result:", result)

        if args.check:
            print(f"\n=== Checking {mode} solution ===")
            subprocess.run(
                [sys.executable, "source/solution_checker.py", f"./res/{mode}"],
                check=True
            )


if __name__ == "__main__":
    main()