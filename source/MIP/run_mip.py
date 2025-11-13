"""
run_mip.py
================
Module for the MIP approach of the Sports Tournament Scheduling problem.

Usage:
    python run_mip.py <n>

This will generate a solution for n teams and save it to ../../res/MIP/<n>.json.
"""
import os
import json
import time
from amplpy import ampl_notebook

def main(n: int):
    print(f"Running MIP for n = {n}")

    # ✅ Activate AMPL Community Edition license locally
    license_uuid = os.environ.get("AMPL_LICENSE_UUID")
    if not license_uuid:
        raise RuntimeError("Please set AMPL_LICENSE_UUID environment variable")

    ampl = ampl_notebook(
        modules=["gurobi"],  # choose solvers you want
        license_uuid=license_uuid
    )

    # ✅ Load MIP model
    ampl.read("mip.mod")

    # ✅ Set parameters
    ampl.getParameter("n").set(n)
    ampl.getParameter("weeks").set(n - 1)
    ampl.getParameter("periods").set(n // 2)

    # ✅ Populate sets without redeclaring them
    ampl.getSet("TEAMS").setValues(range(1, n + 1))
    ampl.getSet("WEEKS").setValues(range(1, n))
    ampl.getSet("PERIODS").setValues(range(1, n // 2 + 1))

    # ✅ Set solver to Gurobi with 300-second time limit
    ampl.setOption("solver", "gurobi")
    ampl.setOption("gurobi_options", "TimeLimit=300")  # 300 seconds max

    # ✅ Solve
    start_time = time.time()
    ampl.solve()
    end_time = time.time()

    # ✅ Extract solution matrix
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

    # ✅ Compute runtime and handle timeout
    elapsed = int(end_time - start_time)
    if elapsed >= 300:  # reached time limit
        elapsed = 300
        optimal = False
    else:
        optimal = ampl.getValue("solve_result") == 0

    # ✅ Construct JSON result
    result = {
        "gurobi": {
            "time": elapsed,
            "optimal": optimal,
            "obj": 0,  # dummy objective
            "sol": sol_matrix
        }
    }

    # ✅ Save results
    out_dir = os.path.abspath("../../res/MIP")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{n}.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=4)

    print(f"Results saved to {out_path}")
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python run_mip.py <n>")
        sys.exit(1)

    n = int(sys.argv[1])
    
    """  #RUNS FOR ALL NUMBERS FROM 6 TO N
    # Run main only for even numbers starting from 6 up to n
    for i in range(6, n + 1, 2):
        main(i)
    """
    main(n)
