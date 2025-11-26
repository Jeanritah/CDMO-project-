# smt_optimized_no_symmetry.py
# SMT optimization model for the STS problem WITHOUT symmetry breaking.
#
# This extends the NO-SB decision model from smt_no_symmetry.py by adding
# the same home/away imbalance objective used in smt_optimized.py.
#
# Results are stored in res/SMT/n.json under the key "z3_smt_opt_noSB".

from z3 import *
import argparse
import time

# Reuse:
#  - the NO-SB decision model
#  - the JSON / solution utilities from the aligned (SB) file
from SMT.models.smt_decision_no_sb import create_smt_solver_no_symmetry
from SMT.models.smt_decision_sb import extract_solution, save_to_json


def create_optimized_model_no_symmetry(n):
    """
    Build an Optimize() model starting from the NO-SB decision constraints
    in create_smt_solver_no_symmetry(n), then add the home/away imbalance
    objective as in smt_optimized.py.

    Returns:
        opt      : Optimize model
        T        : game assignment variables
        weeks    : number of weeks
        periods  : number of periods
        D        : imbalance objective variable
    """
    # print(f"Creating OPTIMIZED SMT model WITHOUT symmetry for n={n} teams...")

    # Build base NO-SB SMT model with all constraints
    base_solver, T, weeks, periods = create_smt_solver_no_symmetry(n)

    # Copy constraints into Optimize()
    opt = Optimize()
    for c in base_solver.assertions():
        opt.add(c)

    # h_i = number of home matches per team
    home_vars = []
    for team in range(1, n + 1):
        h = Int(f"h_ns_{team}")
        home_count_terms = []
        for p in range(periods):
            for w in range(weeks):
                home, away = T[p][w]
                home_count_terms.append(If(home == team, 1, 0))
        opt.add(h == Sum(home_count_terms))
        home_vars.append(h)

    # Objective: minimize max_i |2*h_i - (n-1)|
    D = Int("D_ns")
    opt.add(D >= 0)

    for team in range(1, n + 1):
        h = home_vars[team - 1]
        expr = 2 * h - (n - 1)
        diff = Int(f"diff_ns_{team}")
        opt.add(diff >= expr)
        opt.add(diff >= -expr)
        opt.add(diff >= 0)
        opt.add(D >= diff)

    opt.minimize(D)

    # print("✅ Optimization model created (NO-SB constraints + objective)")
    return opt, T, weeks, periods, D


def run_optimized_no_symmetry(n):
    """Run NO-SB optimization and save result in JSON."""
    # print(f"\n=== SMT OPTIMIZATION MODEL WITHOUT SYMMETRY for n={n} ===")

    if n % 2 != 0 or n < 2:
        raise ValueError("Number of teams n must be an even integer >= 2")

    opt, T, weeks, periods, D = create_optimized_model_no_symmetry(n)
    opt.set(timeout=300000)  # 300 seconds

    # print("\n🔍 Solving (with objective, NO symmetry breaking)...")
    start = time.time()
    result = opt.check()
    end = time.time()
    runtime = end - start

    # print(f"⏱ Runtime: {runtime:.3f} seconds")

    result_key = "z3_obj_!sb"

    if result == sat:
        # print("✅ SAT - Feasible solution found (objective minimized, NO-SB).")
        model = opt.model()

        # Read objective safely
        try:
            D_val = model[D].as_long()
        except Exception:
            D_val = None

        # print(f"🎯 Max home/away imbalance D* (NO-SB) = {D_val}")

        # Pretty # print schedule
        # print("\n🏆 OPTIMAL SCHEDULE (grouped by weeks, NO-SB)")
        # print("=" * 50)
        for w in range(weeks):
            # print(f"Week {w+1}: ", end="")
            for p in range(periods):
                home_val = model[T[p][w][0]].as_long()
                away_val = model[T[p][w][1]].as_long()
                # print(f"{home_val}vs{away_val} ", end="")
            # print()

        sol = extract_solution(n, model, T, weeks, periods)
        save_to_json(n, result_key, runtime, True, D_val, sol)

    elif result == unsat:
        # print("❌ UNSAT - No feasible schedule exists (NO-SB).")
        save_to_json(n, result_key, runtime, True, None, [])

    else:
        # print("⏰ UNKNOWN - Timeout or indeterminate (NO-SB).")
        save_to_json(n, result_key, 300, False, None, [])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SMT Optimization Model for STS WITHOUT Symmetry Breaking"
    )
    parser.add_argument("--teams", type=int, required=True,
                        help="Number of teams (even n)")
    args = parser.parse_args()

    run_optimized_no_symmetry(args.teams)