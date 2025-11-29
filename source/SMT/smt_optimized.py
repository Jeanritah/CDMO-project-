# smt_optimized.py
# SMT optimization model for the STS problem
# Objective: minimize the maximum home/away imbalance over all teams.

from z3 import *
import argparse
import time

# Reusing model-building + JSON utilities from the decision file
from smt_aligned import create_smt_solver, extract_solution, save_to_json


def create_optimized_model(n):
    """
    Build an Optimize() model starting from the decision constraints
    in create_smt_solver(n), and then add the home/away balance
    objective: minimize max_i |2*h_i - (n-1)|.

    Returns:
        opt      : Optimize object
        T        : 3D array of game variables (same as in smt_aligned)
        weeks    : number of weeks
        periods  : number of periods
        D        : Z3 Int, the max imbalance variable
    """
    print(f"Creating OPTIMIZED SMT model for n={n} teams...")

    # building  the plain decision model (constraints only)
    base_solver, T, weeks, periods = create_smt_solver(n)

    # Creating  an Optimize instance and copy all decision constraints
    opt = Optimize()
    for c in base_solver.assertions():
        opt.add(c)

    # --- Objective modelling ---

    # h_i = number of home matches for team i
    home_vars = []
    for team in range(1, n + 1):
        h = Int(f"h_{team}")
        home_count_terms = []

        for p in range(periods):
            for w in range(weeks):
                home, away = T[p][w]
                home_count_terms.append(If(home == team, 1, 0))

        opt.add(h == Sum(home_count_terms))
        home_vars.append(h)

    # For each team, diff_i >= |2*h_i - (n-1)|
    # and D >= diff_i, and minimize D.
    D = Int("D")
    opt.add(D >= 0)

    for team in range(1, n + 1):
        h = home_vars[team - 1]
        expr = 2 * h - (n - 1)       # 2*h_i - (n-1)
        diff = Int(f"diff_{team}")
        opt.add(diff >= expr)
        opt.add(diff >= -expr)
        opt.add(diff >= 0)
        opt.add(D >= diff)

    # Objective: minimize the maximum imbalance D
    opt.minimize(D)

    print("✅ Optimization model created (same constraints as decision + objective)")
    return opt, T, weeks, periods, D


def run_optimized(n):
    """
    Run the optimization model for n teams and save results to JSON
    under key 'z3_smt_opt'.
    """
    print(f"\n=== SMT OPTIMIZATION MODEL for n={n} ===")

    if n % 2 != 0 or n < 2:
        raise ValueError("Number of teams n must be an even integer >= 2")

    opt, T, weeks, periods, D = create_optimized_model(n)

    # Timeout: 300 seconds
    opt.set(timeout=300000)

    print("\n🔍 Solving (with objective)...")
    start = time.time()
    result = opt.check()
    end = time.time()
    runtime = end - start

    print(f"⏱ Runtime: {runtime:.3f} seconds")

    result_key = "z3_smt_opt"

    if result == sat:
        print("✅ SAT - Feasible solution found (objective minimized).")
        model = opt.model()

        # Objective value (more robust)
        try:
            D_val = model[D].as_long()
        except Exception:
            D_val = None
        print(f"🎯 Max home/away imbalance D* = {D_val}")

        # print schedule by weeks
        print("\n🏆 OPTIMAL SCHEDULE (grouped by weeks)")
        print("=" * 50)
        for w in range(weeks):
            print(f"Week {w+1}: ", end="")
            for p in range(periods):
                home_val = model[T[p][w][0]].as_long()
                away_val = model[T[p][w][1]].as_long()
                print(f"{home_val}vs{away_val} ", end="")
            print()

        sol = extract_solution(n, model, T, weeks, periods)
        # optimal=True because Optimize found a model for the formulated objective
        save_to_json(n, result_key, runtime, True, D_val, sol)

    elif result == unsat:
        print("❌ UNSAT - No solution exists (this should not happen for valid instances).")
        save_to_json(n, result_key, runtime, True, None, [])

    else:
        print("⏰ UNKNOWN - Timeout or indeterminate (no proven optimum).")
        # We treat this as non-optimal; no schedule stored
        save_to_json(n, result_key, 300, False, None, [])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SMT Optimization Model for Round-Robin Scheduling"
    )
    parser.add_argument("--teams", type=int, required=True,
                        help="Number of teams (even n)")
    args = parser.parse_args()

    run_optimized(args.teams)
