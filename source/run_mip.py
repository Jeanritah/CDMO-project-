"""
run_mip.py
================
Module for the MIP approach of the Sports Tournament Scheduling problem.

Two entry points:
-----------------
1. CLI:
       python run_mip.py --range 6 10 --solver gurobi --obj both --algo all

2. Programmatic interface (used by main.py):
       from run_mip import main
       result = main([6,7,8])
"""

import os
import sys
import time
import json
import argparse
from amplpy import ampl_notebook  # type: ignore
from utils import utils

# ------------------------------------------------------------
# CONSTANTS
# ------------------------------------------------------------
SOLVERS = ["gurobi", "cplex"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))        # source/
CONTAINER_DIR = os.path.join(BASE_DIR, "..")                 # root
MODEL_DIR = os.path.join(BASE_DIR, "MIP")                   # source/MIP/
RESULTS_DIR = os.path.join(CONTAINER_DIR, "res/MIP")        # directory to store JSONs

MODELS = [
    "mip_!sb_!lex.mod",
    "mip_sb_!lex.mod",
    "mip_sb_lex.mod",
    "mip_!sb_lex.mod"
]

# Map algorithm names to solver-specific options
ALGO_MAP = {
    "default": "",
    "psmplx": {"gurobi": "Method=0", "cplex": "lpmethod=0"},
    "dsmplx": {"gurobi": "Method=1", "cplex": "lpmethod=2"},
    "barr": {"gurobi": "Method=2", "cplex": "lpmethod=4"},
}

# ------------------------------------------------------------
# INTERNAL FUNCTIONS
# ------------------------------------------------------------
def setup_ampl_solver(solver: str, use_obj: bool, algo: str = "default"):
    """Create and return an AMPL instance with the requested solver algorithm."""
    license_uuid = os.environ.get("AMPL_LICENSE_UUID")
    if not license_uuid:
        raise RuntimeError("Please set AMPL_LICENSE_UUID environment variable")

    ampl = ampl_notebook(modules=[solver], license_uuid=license_uuid)

    # Base solver options
    if solver.lower() == "gurobi":
        solver_opts = "TimeLimit=300 MIPFocus=0 MIPGap=0 Threads=1" if use_obj else "TimeLimit=300 MIPFocus=1 Threads=1"
    elif solver.lower() == "cplex":
        solver_opts = "timelimit=300 mipgap=0 MIPEmphasis=0 threads=1" if use_obj else "timelimit=300 MIPEmphasis=1 threads=1"
    else:
        raise ValueError(f"Unsupported solver: {solver}")

    # Append algorithm-specific option
    if algo != "default":
        solver_opts += " " + ALGO_MAP[algo][solver]

    ampl.setOption("solver", solver)
    ampl.setOption("quiet", True)
    ampl.setOption(f"{solver}_options", solver_opts)

    return ampl


def prepare_ampl_model(ampl, n: int, model_file: str, use_obj: bool):
    """Load the model, set parameters/sets, and optionally add fairness objective."""
    ampl.read(model_file)
    ampl.getParameter("n").set(n)
    ampl.getParameter("weeks").set(n - 1)
    ampl.getParameter("periods").set(n // 2)
    ampl.getSet("TEAMS").setValues(range(1, n + 1))
    ampl.getSet("WEEKS").setValues(range(1, n))
    ampl.getSet("PERIODS").setValues(range(1, n // 2 + 1))

    if use_obj:
        ampl.eval("""
            var home_games {i in TEAMS} integer >= 0 <= card(TEAMS);
            var away_games {i in TEAMS} integer >= 0 <= card(TEAMS);
            var home_away_diff {i in TEAMS} >= 0;
            var max_deviation >= 0;

            s.t. calc_home {i in TEAMS}:
                home_games[i] = sum {w in WEEKS, p in PERIODS, j in TEAMS: i != j} x[w,p,i,j];

            s.t. calc_away {i in TEAMS}:
                away_games[i] = sum {w in WEEKS, p in PERIODS, j in TEAMS: i != j} x[w,p,j,i];

            s.t. diff1 {i in TEAMS}:
                home_away_diff[i] >= home_games[i] - away_games[i];

            s.t. diff2 {i in TEAMS}:
                home_away_diff[i] >= away_games[i] - home_games[i];

            s.t. max_dev_constraint {i in TEAMS}:
                max_deviation >= home_away_diff[i];

            minimize MaxDeviation: max_deviation;
        """)
    else:
        ampl.eval("minimize dummy_obj: 0;")


def extract_solution(ampl, n: int):
    """Parse AMPL variable 'x' into Python solution matrix."""
    x = ampl.getVariable("x")
    sol_matrix = []
    periods, weeks = n // 2, n - 1

    for p in range(1, periods + 1):
        week_row = []
        for w in range(1, weeks + 1):
            found = False
            for i in range(1, n + 1):
                for j in range(1, n + 1):
                    if x[w, p, i, j].value() > 0.5:
                        week_row.append([i, j])
                        found = True
                        break
                if found:
                    break
        sol_matrix.append(week_row)

    return sol_matrix


def run_single_solver(n: int, solver: str, use_obj: bool, model_file: str, algo: str):
    """Run a solver instance and return a result dictionary."""
    ampl = setup_ampl_solver(solver, use_obj, algo)
    prepare_ampl_model(ampl, n, model_file, use_obj)

    start_time = time.time()
    with open(os.devnull, "w") as fnull:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = fnull, fnull
        try:
            ampl.solve()
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

    elapsed = int(time.time() - start_time)

    if n == 4:
        return {"time": 0, "optimal": True, "obj": None, "sol": []}

    solve_result = ampl.getValue("solve_result")
    optimal = None
    obj_val = None
    sol_matrix = []

    if solve_result == -1:
        optimal = True
        sol_matrix = []
        obj_val = None
    elif elapsed >= 300:
        optimal = False
        elapsed = 300
        sol_matrix = []
        obj_val = None
    else:
        sol_matrix = extract_solution(ampl, n)
        optimal = True
        if use_obj:
            try:
                obj_val = int(round(ampl.getValue("MaxDeviation")))
            except:
                obj_val = None

    return {"time": elapsed, "optimal": optimal, "obj": obj_val, "sol": sol_matrix}


# ------------------------------------------------------------
# SHARED LOGIC
# ------------------------------------------------------------
def run_mip_logic(teams, solver_list, objective_choice, algo_choice="default"):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    results = {}

    # Convert 'all' -> list of all algorithms
    if algo_choice == "all":
        algos = ["default", "psmplx", "dsmplx", "barr"]
    else:
        algos = [algo_choice]

    for n in teams:
        results[n] = {}

        for solver in solver_list:
            for model in MODELS:
                model_suffix = os.path.basename(model).replace(".mod", "").replace("mip", "")

                for algo in algos:
                    key_suffix = f"_{algo}" if algo != "default" else ""
                    if objective_choice == "both":
                        results[n][f"{solver}_obj{model_suffix}{key_suffix}"] = run_single_solver(
                            n, solver, True, os.path.join(MODEL_DIR, model), algo
                        )
                        results[n][f"{solver}_!obj{model_suffix}{key_suffix}"] = run_single_solver(
                            n, solver, False, os.path.join(MODEL_DIR, model), algo
                        )
                    else:
                        use_obj = objective_choice == "true"
                        key = f"{solver}_obj{model_suffix}{key_suffix}" if use_obj else f"{solver}_!obj{model_suffix}{key_suffix}"
                        results[n][key] = run_single_solver(
                            n, solver, use_obj, os.path.join(MODEL_DIR, model), algo
                        )

        out_path = os.path.join(RESULTS_DIR, f"{n}.json")
        with open(out_path, "w") as f:
            json.dump(results[n], f, indent=4)
        print(f"Saved MIP result for n={n} to {out_path}\n")

    return results


# ------------------------------------------------------------
# PROGRAMMATIC ENTRY POINT
# ------------------------------------------------------------
def main(teams, solver_list=SOLVERS, objective_choice="both", algo_choice="all"):
    print(f"\nRunning MIP for teams={teams}, solvers={solver_list}, objective={objective_choice}, algo={algo_choice}\n")
    return run_mip_logic(teams, solver_list, objective_choice, algo_choice)

# ------------------------------------------------------------
# CLI ENTRY POINT
# ------------------------------------------------------------
def main_cli():
    parser = argparse.ArgumentParser(description="MIP CLI")
    parser.add_argument("--range", type=int, nargs=2, required=True, metavar=("LOWER", "UPPER"))
    parser.add_argument("--solver", type=str, nargs="+", default=["gurobi"], choices=SOLVERS + ["all"])
    parser.add_argument("--obj", type=str, default="false", choices=["true", "false", "both"])
    parser.add_argument("--algo", type=str, default="default", choices=["default","psmplx","dsmplx","barr","all"])
    args = parser.parse_args()

    teams = utils.convert_to_range((args.range[0], args.range[1]))
    solver_choice = SOLVERS if "all" in args.solver else args.solver
    objective_choice = args.obj.lower()
    algo_choice = args.algo.lower()

    print(f"\nRunning MIP for teams={teams}, solvers={solver_choice}, objective={objective_choice}, algo={algo_choice}\n")
    run_mip_logic(teams, solver_choice, objective_choice, algo_choice)



if __name__ == "__main__":
    main_cli()
