# CDMO_Project/source/SMT/smt_aligned.py
from z3 import *
import argparse
import time
import json
import os


def create_smt_solver(n):
    """
    Create an SMT solver for n teams.
    This follows closely the CP model for fair comparison.
    """
    print(f"Creating SMT solver for n={n} teams...")

    # Create a solver object
    s = Solver()

    # For n teams: n-1 weeks (round-robin), n/2 periods per week
    weeks = n - 1
    periods = n // 2

    print(f" - Weeks: {weeks}, Periods: {periods}")

    # STEP 1: Create variables
    # T[period][week] = [home_team, away_team]
    T = []
    for p in range(periods):
        period_games = []
        for w in range(weeks):
            home_var = Int(f"T_{p}_{w}_home")
            away_var = Int(f"T_{p}_{w}_away")
            period_games.append([home_var, away_var])
        T.append(period_games)

    # STEP 2: Domain constraints
    print(" - Adding domain constraints...")
    for p in range(periods):
        for w in range(weeks):
            home, away = T[p][w]
            s.add(home >= 1, home <= n)
            s.add(away >= 1, away <= n)
            s.add(home != away)  # no team vs itself

    # STEP 3: Symmetry breaking: home < away
    print(" - Adding symmetry breaking (home < away)...")
    for p in range(periods):
        for w in range(weeks):
            home, away = T[p][w]
            s.add(home < away)

    # STEP 4: Fix first game (extra symmetry breaking)
    print(" - Fixing first game (team 1 vs team 2)...")
    if periods > 0 and weeks > 0:
        s.add(T[0][0][0] == 1)
        s.add(T[0][0][1] == 2)

    # STEP 5: Each team plays exactly once per week
    print(" - Adding weekly constraints (each team once per week)...")
    for w in range(weeks):
        week_teams = []
        for p in range(periods):
            week_teams.append(T[p][w][0])  # home
            week_teams.append(T[p][w][1])  # away
        # there are n = 2 * periods teams per week
        s.add(Distinct(week_teams))

    # STEP 6: All games (pairs) are unique
    print(" - Adding unique games constraint...")
    all_games = []
    for p in range(periods):
        for w in range(weeks):
            home, away = T[p][w]
            # encode unordered pair using home < away
            game_code = home * n + away
            all_games.append(game_code)
    s.add(Distinct(all_games))

    # STEP 7: At most 2 appearances per period for each team
    print(" - Adding period constraints (max 2 appearances per team/period)...")
    for team in range(1, n + 1):
        for p in range(periods):
            appearances = 0
            for w in range(weeks):
                home, away = T[p][w]
                appearances = appearances + If(Or(home == team, away == team), 1, 0)
            s.add(appearances <= 2)

    print(f"✅ Created solver with {len(s.assertions())} constraints")
    return s, T, weeks, periods


def print_solution(n, model, T, weeks, periods):
    """Print the solution in a human-readable format (grouped by weeks)."""
    print(f"\n🏆 SOLUTION FOUND for n={n}")
    print("=" * 50)

    for w in range(weeks):
        print(f"Week {w + 1}: ", end="")
        for p in range(periods):
            home_val = model[T[p][w][0]].as_long()
            away_val = model[T[p][w][1]].as_long()
            print(f"{home_val}vs{away_val} ", end="")
        print()

    # Simple uniqueness check
    print("\n🔍 Verifying solution...")
    all_pairs = set()
    for p in range(periods):
        for w in range(weeks):
            home_val = model[T[p][w][0]].as_long()
            away_val = model[T[p][w][1]].as_long()
            all_pairs.add((home_val, away_val))

    expected_games = n * (n - 1) // 2
    print(f"Unique games: {len(all_pairs)} (should be {expected_games})")
    if len(all_pairs) == expected_games:
        print("✅ All games are unique!")
    else:
        print("❌ Problem: Duplicate games found!")


def save_to_json(n, model, T, weeks, periods, runtime, optimal_flag):
    """
    Save solution in the required JSON format for the project.

    sol must be an (n/2) x (n-1) matrix:
    sol[period][week] = [home, away]
    """
    # Build solution as periods x weeks
    solution = []
    for p in range(periods):
        period_games = []
        for w in range(weeks):
            home_val = model[T[p][w][0]].as_long()
            away_val = model[T[p][w][1]].as_long()
            period_games.append([home_val, away_val])
        solution.append(period_games)

    result = {
        "z3_smt": {
            "time": int(runtime),      # floor of runtime in seconds
            "optimal": optimal_flag,   # True if solved within time limit
            "obj": None,               # decision problem -> no objective
            "sol": solution
        }
    }

    # Ensure the res/SMT folder exists (relative to this file)
    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "res", "SMT")
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, f"{n}.json")
    with open(filename, "w") as f:
        json.dump(result, f, indent=2)

    print(f"💾 Solution saved to: {filename}")


def save_no_model_json(n, runtime, optimal_flag):
    """
    Save a JSON file even if no model is available (e.g., timeout/UNKNOWN).
    sol is stored as an empty list; format is still respected.
    """
    result = {
        "z3_smt": {
            "time": int(runtime),
            "optimal": optimal_flag,
            "obj": None,
            "sol": []  # no solution found / not computed
        }
    }

    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "res", "SMT")
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, f"{n}.json")
    with open(filename, "w") as f:
        json.dump(result, f, indent=2)

    print(f"💾 (No model) Result saved to: {filename}")


def test_with_all_constraints(n):
    """Main entry: build solver, solve, print and save JSON."""
    print("\n=== TESTING WITH ALL CONSTRAINTS ===")

    solver, T, weeks, periods = create_smt_solver(n)

    # Set Z3 timeout to 300 seconds (300,000 ms)
    solver.set(timeout=300000)

    print("\n🔍 Solving...")
    start = time.perf_counter()
    result = solver.check()
    end = time.perf_counter()

    runtime = end - start
    print(f"⏱ Runtime: {runtime:.3f} seconds")

    model = None
    optimal_flag = False

    if result == sat:
        print("✅ SAT - Valid solution found!")
        model = solver.model()
        optimal_flag = True  # for decision problem, SAT is "solved"
    elif result == unsat:
        print("❌ UNSAT - No solution exists with current constraints")
        # Decision problem solved (proved unsat)
        model = None
        optimal_flag = True
    else:  # unknown (likely timeout)
        print("⏰ UNKNOWN - Could not determine within the limit")
        # As per project description: if not solved within 300 seconds,
        # set time = 300 and optimal = false
        runtime = 300.0
        optimal_flag = False

    if model is not None:
        print_solution(n, model, T, weeks, periods)
        save_to_json(n, model, T, weeks, periods, runtime, optimal_flag)
    else:
        # No model (unsat or unknown) -> still produce JSON
        save_no_model_json(n, runtime, optimal_flag)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SMT Aligned Model for Sports Tournament Scheduling"
    )
    parser.add_argument("--teams", type=int, default=6, help="Number of teams (n, even)")
    args = parser.parse_args()
    n = args.teams
    print(f"Requested teams: n = {n}")

    # The problem is defined for even n >= 2
    if n < 2 or n % 2 != 0:
        raise ValueError("Number of teams n must be an even integer >= 2")

    test_with_all_constraints(n)
