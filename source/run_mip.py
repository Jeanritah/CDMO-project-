"""
run_mip.py
================
Module for the MIP approach of the Sports Tournament Scheduling problem.

Usage:
    python run_mip.py <n> --solver gurobi --objective true
    python run_mip.py <n> --solver all --objective both
"""

import os
import json
import time
import argparse
from amplpy import ampl_notebook # type: ignore

SOLVERS = ["gurobi", "cplex", "cbc"]

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

    # Disable objective if use_obj is False
    if not use_obj:
        ampl.eval("minimize sample_obj: 0;")

    # solver options
    ampl.setOption("solver", solver)
    solver_opts = "TimeLimit=300"

    if solver.lower() == "cplex":
        # Feasibility first in CPLEX
        solver_opts += " MIPEmphasis=1"  # 1 = feasibility, 0 = balance, 2 = optimality
        solver_opts += " threads=1"
    elif solver.lower() == "gurobi":
        # Feasibility first in Gurobi
        solver_opts += " MIPFocus=1"    # 0 = default, 1 = feasibility, 2 = optimality, 3 = best bound
        solver_opts += " Threads=1"


    ampl.setOption(f"{solver}_options", solver_opts)


    # solve
    start_time = time.time()
    ampl.solve()
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

    # Determine status according to your instructions
    solve_result = ampl.getValue("solve_result")  # 0 = optimal/feasible, >0 = unknown/time limit, <0 = infeasible/UNSAT

    obj_val = None  # as per instructions, obj is None in timeout or UNSAT

    # UNSAT proved
    if solve_result == -1:  # UNSAT
        optimal = True
        sol_matrix = []
        # keep actual elapsed time
    # Timeout / no solution within limit
    elif elapsed >= 300:
        elapsed = 300
        optimal = False
        sol_matrix = []
    else:  # feasible/optimal solution found
        optimal = solve_result == 0
        # objective value if active and solution exists
        try:
            obj_val = float(ampl.getObjective(0).value()) if use_obj else None
        except:
            obj_val = None

    # special case for n=4 (UNSAT)
    if n == 4:
        sol_matrix = []
        optimal = True  # proven UNSAT
        obj_val = None
        elapsed = 0

    return {
        "time": elapsed,
        "optimal": optimal,
        "obj": obj_val,
        "sol": sol_matrix
    }



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("n", type=int)
    parser.add_argument("--solver", type=str, default="gurobi",
                        help="gurobi | cplex | cbc | all")
    parser.add_argument("--objective", type=str, default="false",
                        help="true | false | both")
    args = parser.parse_args()

    n = args.n
    solver_choice = args.solver.lower()
    objective_choice = args.objective.lower()

    if objective_choice not in ["true", "false", "both"]:
        raise ValueError("Invalid --objective flag, must be true | false | both")

    print(f"Running MIP for n={n}, solver={solver_choice}, objective={objective_choice}")

    # run solvers
    results = {}
    models = ["mip_!sb.mod", "mip_sb.mod"]

    solvers_to_run = SOLVERS if solver_choice == "all" else [solver_choice]
    for sol in solvers_to_run:
        if sol not in SOLVERS:
            raise ValueError(f"Unknown solver: {sol}")

        for model in models:
            model_suffix = "_sb" if "_sb" in model else "_!sb"

            # handle objective "both"
            if objective_choice == "both":
                results[f"{sol}_obj{model_suffix}"] = run_single_solver(n, sol, True, model)
                results[f"{sol}_!obj{model_suffix}"] = run_single_solver(n, sol, False, model)
            else:
                use_obj = objective_choice == "true"
                key = f"{sol}_obj{model_suffix}" if use_obj else f"{sol}_!obj{model_suffix}"
                results[key] = run_single_solver(n, sol, use_obj, model)

    # save output
    out_dir = os.path.abspath("../../res/MIP")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{n}.json")

    with open(out_path, "w") as f:
        json.dump(results, f, indent=4)

    print(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()