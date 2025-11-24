"""
run_mip.py
================
Module for the MIP approach of the Sports Tournament Scheduling problem.

Two entry points:
-----------------
1. CLI:
       python run_mip.py --range 6 10 --solver gurobi --objective both

2. Programmatic interface (used by main.py):
       from run_mip import main
       result = main([6,7,8])
"""

import os
import json
import time
import argparse
import sys
from amplpy import ampl_notebook  # type: ignore
from utils import utils

SOLVERS = ["gurobi", "cplex", "cbc"]

# ------------------------------------------------------------
# FIX: Absolute model directory for Docker & local consistency
# ------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))    # source/
CONTAINER_DIR = os.path.join(BASE_DIR,"..")                 #root
MODEL_DIR = os.path.join(BASE_DIR, "MIP")                # source/MIP/
RESULTS_DIR = os.path.join(CONTAINER_DIR,"res/MIP")   #directory to store jsons

# ------------------------------------------------------------
# INTERNAL FUNCTION: solve for one solver/model/obj setting
# ------------------------------------------------------------
def run_single_solver(n: int, solver: str, use_obj: bool, model_file: str):
    """Runs the model for a single solver and returns a result dict."""

    license_uuid = os.environ.get("AMPL_LICENSE_UUID")
    if not license_uuid:
        raise RuntimeError("Please set AMPL_LICENSE_UUID environment variable")

    ampl = ampl_notebook(
        modules=[solver],
        license_uuid=license_uuid
    )

    ampl.read(model_file)

    # parameters
    ampl.getParameter("n").set(n)
    ampl.getParameter("weeks").set(n - 1)
    ampl.getParameter("periods").set(n // 2)

    ampl.getSet("TEAMS").setValues(range(1, n + 1))
    ampl.getSet("WEEKS").setValues(range(1, n))
    ampl.getSet("PERIODS").setValues(range(1, n // 2 + 1))

    if not use_obj:
        ampl.eval("minimize sample_obj: 0;")

    ampl.setOption("solver", solver)
    ampl.setOption("quiet", True)

    solver_opts = "TimeLimit=300"
    if solver.lower() == "cplex":
        solver_opts += " MIPEmphasis=1 threads=1"
    elif solver.lower() == "gurobi":
        solver_opts += " MIPFocus=1 Threads=1"
    ampl.setOption(f"{solver}_options", solver_opts)

    # solve with stdout/stderr suppressed
    start_time = time.time()
    with open(os.devnull, "w") as fnull:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = fnull, fnull
        try:
            ampl.solve()
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
    end_time = time.time()

    x = ampl.getVariable("x")
    sol_matrix = []
    periods = n // 2
    weeks = n - 1

    for p in range(1, periods + 1):
        week_row = []
        for w in range(1, weeks + 1):
            match_found = False
            for i in range(1, n + 1):
                for j in range(1, n + 1):
                    if x[w, p, i, j].value() > 0.5:
                        week_row.append([i, j])
                        match_found = True
                        break
                if match_found:
                    break
        sol_matrix.append(week_row)

    elapsed = int(end_time - start_time)
    solve_result = ampl.getValue("solve_result")
    obj_val = None

    if solve_result == -1:  # UNSAT
        optimal = True
        sol_matrix = []
    elif elapsed >= 300:
        elapsed = 300
        optimal = False
        sol_matrix = []
    else:
        optimal = solve_result == 0
        try:
            obj_val = float(ampl.getObjective(0).value()) if use_obj else None
        except:
            obj_val = None

    if n == 4:  # special UNSAT case
        sol_matrix = []
        optimal = True
        obj_val = None
        elapsed = 0

    return {
        "time": elapsed,
        "optimal": optimal,
        "obj": obj_val,
        "sol": sol_matrix
    }


# ------------------------------------------------------------
# SHARED LOGIC used by CLI *and* main.py
# ------------------------------------------------------------
def run_mip_logic(teams, solver_list, objective_choice):
    """
    Runs the MIP solver for all n in 'teams'.
    solver_list: list of solver names
    objective_choice: "true", "false", or "both"
    """
    results = {}

    models = [
        os.path.join(MODEL_DIR, "mip_!sb.mod"),
        os.path.join(MODEL_DIR, "mip_sb.mod"),
    ]

    for n in teams:
        results[n] = {}

        for sol in solver_list:
            for model in models:
                model_suffix = "_sb" if model.endswith("_sb.mod") else "_!sb"

                if objective_choice == "both":

                    results[n][f"{sol}_obj{model_suffix}"] = run_single_solver(n, sol, True, model)
                    results[n][f"{sol}_!obj{model_suffix}"] = run_single_solver(n, sol, False, model)
                else:

                    use_obj = (objective_choice == "true")
                    key = f"{sol}_obj{model_suffix}" if use_obj else f"{sol}_!obj{model_suffix}"
                    results[n][key] = run_single_solver(n, sol, use_obj, model)

    return results

def save_results(results):

    out_dir = RESULTS_DIR
    os.makedirs(out_dir, exist_ok=True)
    for n, data in results.items():
        out_path = os.path.join(out_dir, f"{n}.json")
        with open(out_path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Saved MIP result to {out_path}")


# ------------------------------------------------------------
# PROGRAMMATIC ENTRY POINT (used by main.py)
# ------------------------------------------------------------
def main(teams):
    """
    main.py will import THIS function.
    teams: list of ints (team sizes)
    Returns results for all n in a dict.
    """
    solver_list = SOLVERS     # runs all
    objective_choice = "both"    # runs both with and without optimization
    print(f"\nRunning MIP for teams={teams}, solvers={solver_list}, objective={objective_choice}\n")

    results = run_mip_logic(teams, solver_list, objective_choice)
    save_results(results)
    
    


# ------------------------------------------------------------
# CLI ENTRY POINT
# ------------------------------------------------------------
def main_cli():
    parser = argparse.ArgumentParser(description="MIP CLI")
    parser.add_argument("--range", type=int, nargs=2, required=True, metavar=("LOWER", "UPPER"))
    parser.add_argument("--solver", type=str, nargs="+", default=["gurobi"], choices=SOLVERS + ["all"])
    parser.add_argument("--objective", type=str, default="false",
                        choices=["true", "false", "both"])
    args = parser.parse_args()

    teams = utils.convert_to_range((args.range[0], args.range[1]))
    solver_choice = SOLVERS if "all" in args.solver else args.solver
    objective_choice = args.objective.lower()

    print(f"\nRunning MIP for teams={teams}, solvers={solver_choice}, objective={objective_choice}\n")

    results = run_mip_logic(teams, solver_choice, objective_choice)

    save_results(results)


if __name__ == "__main__":
    main_cli()