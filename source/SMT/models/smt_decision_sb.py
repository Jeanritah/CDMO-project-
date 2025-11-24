# smt_aligned.py
# Decision SMT model for the Sports Tournament Scheduling (STS) problem.
# Round-robin with constraints C1–C4, no optimization.

from z3 import Solver, Int, Distinct, If, Or, Sum, sat, unsat
import argparse
import json
import os
import time
from pathlib import Path


def create_smt_solver(n):
    """
    Create an SMT solver for n teams (decision version).
    Implements:
      - round robin structure
      - each team plays once per week
      - each pair meets exactly once
      - each team plays at most twice in the same period
    """
    # print(f"Creating SMT solver for n={n} teams...")

    # Z3 solver (plain Solver, no optimization)
    s = Solver()

    # Round robin structure
    weeks = n - 1          # number of weeks
    periods = n // 2       # matches per week

    # print(f" - Weeks: {weeks}, Periods: {periods}")

    # T[p][w] = [home_team, away_team]
    T = []
    for p in range(periods):
        period_games = []
        for w in range(weeks):
            home_var = Int(f"T_{p}_{w}_home")
            away_var = Int(f"T_{p}_{w}_away")
            period_games.append([home_var, away_var])
        T.append(period_games)

    # Domain + no team plays itself
    # print(" - Adding domain constraints...")
    for p in range(periods):
        for w in range(weeks):
            home, away = T[p][w]
            s.add(home >= 1, home <= n)
            s.add(away >= 1, away <= n)
            s.add(home != away)

    # Symmetry breaking: order inside a game & fix first game
    # print(" - Adding symmetry breaking (home < away)...")
    for p in range(periods):
        for w in range(weeks):
            home, away = T[p][w]
            s.add(home < away)

    # print(" - Fixing first game (team 1 vs team 2)...")
    if periods > 0 and weeks > 0:
        s.add(T[0][0][0] == 1)
        s.add(T[0][0][1] == 2)

    # C3: each team plays once per week
    # print(" - Adding weekly constraints (each team once per week)...")
    for w in range(weeks):
        week_teams = []
        for p in range(periods):
            week_teams.append(T[p][w][0])
            week_teams.append(T[p][w][1])
        s.add(Distinct(week_teams))

    # C2: each pair of teams plays exactly once (round robin)
    # print(" - Adding unique games constraint...")
    all_games = []
    for p in range(periods):
        for w in range(weeks):
            home, away = T[p][w]
            # encode pair as unique integer (home < away enforced)
            game_code = home * n + away
            all_games.append(game_code)
    s.add(Distinct(all_games))

    # C4: each team appears at most twice in the same period
    # print(" - Adding period constraints (max 2 appearances per team/period)...")
    for team in range(1, n + 1):
        for p in range(periods):
            appearances = []
            for w in range(weeks):
                home, away = T[p][w]
                appearances.append(If(Or(home == team, away == team), 1, 0))
            s.add(Sum(appearances) <= 2)

    # print(f"✅ Created solver with {len(s.assertions())} constraints")
    return s, T, weeks, periods


def extract_solution(n, model, T, weeks, periods):
    """
    Convert model to a (periods x weeks) list: sol[p][w] = [home, away]
    as required by the project JSON format.
    """
    solution = []
    for p in range(periods):
        period_games = []
        for w in range(weeks):
            home_val = model[T[p][w][0]].as_long()
            away_val = model[T[p][w][1]].as_long()
            period_games.append([home_val, away_val])
        solution.append(period_games)
    return solution


def save_to_json(n, result_key, time_sec, optimal, obj_value, solution):
    """
    Save (or update) JSON file for instance n under res/SMT/n.json.
    result_key: name of this configuration, e.g. "z3_smt_decision".
    """
    # base_dir = os.path.dirname(__file__)
    # print(base_dir)
    # res_dir = os.path.join(base_dir, "res", "SMT")
    res_dir = Path('res/SMT')
    # print(res_dir)
    os.makedirs(res_dir, exist_ok=True)

    filename = os.path.join(res_dir, f"{n}.json")

    # If file exists, load and update; else start fresh
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
    else:
        data = {}

    data[result_key] = {
        "time": int(time_sec),
        "optimal": optimal,
        "obj": obj_value,
        "sol": solution
    }

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Result saved to {filename}")
    # print(f"Result saved under key '{result_key}' in: {filename}")


def decision_sb(n):
    """
    Build solver, solve, print solution (if any),
    and save JSON under res/SMT/n.json using key 'z3_smt_decision'.
    """
    # print(f"\n=== TESTING SMT DECISION MODEL for n={n} ===")

    if n % 2 != 0:
        raise ValueError("Number of teams n must be even (C1).")

    s, T, weeks, periods = create_smt_solver(n)

    # Timeout: 300 seconds (300000 ms)
    s.set(timeout=300000)

    # # print("\n🔍 Solving...")
    start = time.time()
    result = s.check()
    end = time.time()
    runtime = end - start

    # # print(f"⏱ Runtime: {runtime:.3f} seconds")

    result_key = "z3_!obj_smt"

    if result == sat:
        # print("✅ SAT - Valid solution found!")
        model = s.model()

        # Pretty-print by weeks
        # print("\n🏆 SOLUTION (grouped by weeks)")
        # print("=" * 50)
        for w in range(weeks):
            # print(f"Week {w+1}: ", end="")
            for p in range(periods):
                home_val = model[T[p][w][0]].as_long()
                away_val = model[T[p][w][1]].as_long()
                # print(f"{home_val}vs{away_val} ", end="")
            # print()

        # Check unique games
        pairs = set()
        for p in range(periods):
            for w in range(weeks):
                h = model[T[p][w][0]].as_long()
                a = model[T[p][w][1]].as_long()
                pairs.add((h, a))
        expected = n * (n - 1) // 2
        # print(f"\n🔍 Unique games: {len(pairs)} (should be {expected})")

        sol = extract_solution(n, model, T, weeks, periods)
        save_to_json(n, result_key, runtime, True, None, sol)

    elif result == unsat:
        # print("❌ UNSAT - No solution exists with these constraints.")
        save_to_json(n, result_key, runtime, True, None, [])

    else:
        # print("⏰ UNKNOWN - Timeout or indeterminate.")
        save_to_json(n, result_key, 300, False, None, [])


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(
#         description="SMT Decision Model for Round-Robin Scheduling"
#     )
#     parser.add_argument("--teams", type=int, required=True,
#                         help="Number of teams (even n)")
#     args = parser.parse_args()

#     decision_sb(args.teams)