# smt_no_symmetry.py
# SMT decision model for the STS problem WITHOUT symmetry breaking.
#
# Differences from smt_aligned.py:
#   - NO constraint home < away
#   - NO fixed first game (1 vs 2)
#
# We still enforce:
#   - C1: domain & no self-play
#   - C2: each unordered pair of teams plays exactly once
#   - C3: each team plays exactly once per week
#   - C4: each team appears at most twice in the same period
#
# Results are stored in res/SMT/n.json under the key "z3_smt_decision_noSB".

from z3 import *
import argparse
import time

# Reuse helpers from the aligned (with symmetry) model
from smt_aligned import extract_solution, save_to_json


def create_smt_solver_no_symmetry(n):
    """
    Create an SMT solver for n teams (decision version) WITHOUT
    the artificial symmetry-breaking:
      - NO home < away
      - NO fixed first match (1 vs 2).

    Still enforces:
      - domain & no self-play (C1)
      - weekly constraint (C3)
      - unique games (C2) as unordered pairs
      - period constraint (C4)
    """
    print(f"Creating SMT solver WITHOUT symmetry breaking for n={n} teams...")

    s = Solver()

    # Round-robin structure
    weeks = n - 1          # number of weeks
    periods = n // 2       # matches per week

    print(f" - Weeks: {weeks}, Periods: {periods}")

    # T[p][w] = [home_team, away_team]
    T = []
    for p in range(periods):
        period_games = []
        for w in range(weeks):
            # Use different variable prefix to distinguish from smt_aligned
            home_var = Int(f"Tns_{p}_{w}_home")
            away_var = Int(f"Tns_{p}_{w}_away")
            period_games.append([home_var, away_var])
        T.append(period_games)

    # C1: Domain + no team plays itself
    print(" - Adding domain constraints (no self-play)...")
    for p in range(periods):
        for w in range(weeks):
            home, away = T[p][w]
            s.add(home >= 1, home <= n)
            s.add(away >= 1, away <= n)
            s.add(home != away)

    # *** NO symmetry-breaking here ***
    # (no home < away, no fixed first game)

    # C3: each team plays once per week
    print(" - Adding weekly constraints (each team once per week)...")
    for w in range(weeks):
        week_teams = []
        for p in range(periods):
            week_teams.append(T[p][w][0])  # home
            week_teams.append(T[p][w][1])  # away
        s.add(Distinct(week_teams))

    # C2: each unordered pair of teams plays exactly once (round robin)
    print(" - Adding unique games constraint (unordered pairs)...")
    all_games = []
    for p in range(periods):
        for w in range(weeks):
            home, away = T[p][w]
            # Encode unordered pair {home, away} by always taking (min, max)
            min_team = If(home < away, home, away)
            max_team = If(home < away, away, home)
            game_code = min_team * n + max_team
            all_games.append(game_code)
    s.add(Distinct(all_games))

    # C4: each team appears at most twice in the same period
    print(" - Adding period constraints (max 2 appearances per team/period)...")
    for team in range(1, n + 1):
        for p in range(periods):
            appearances = []
            for w in range(weeks):
                home, away = T[p][w]
                appearances.append(If(Or(home == team, away == team), 1, 0))
            s.add(Sum(appearances) <= 2)

    print(f"✅ Created NO-SB solver with {len(s.assertions())} constraints")
    return s, T, weeks, periods


def test_without_symmetry(n):
    """
    Build NO-SB solver, solve, print solution (if any),
    and save JSON under res/SMT/n.json using key 'z3_smt_decision_noSB'.
    """
    print(f"\n=== TESTING SMT DECISION MODEL WITHOUT SYMMETRY for n={n} ===")

    if n % 2 != 0:
        raise ValueError("Number of teams n must be even (C1).")

    s, T, weeks, periods = create_smt_solver_no_symmetry(n)

    # Timeout: 300 seconds (300000 ms)
    s.set(timeout=300000)

    print("\n🔍 Solving (NO symmetry breaking)...")
    start = time.time()
    result = s.check()
    end = time.time()
    runtime = end - start

    print(f"⏱ Runtime: {runtime:.3f} seconds")

    result_key = "z3_smt_decision_noSB"

    if result == sat:
        print("✅ SAT - Valid solution found (NO symmetry breaking).")
        model = s.model()

        # Pretty-print by weeks
        print("\n🏆 SOLUTION (grouped by weeks, NO-SB)")
        print("=" * 50)
        for w in range(weeks):
            print(f"Week {w+1}: ", end="")
            for p in range(periods):
                home_val = model[T[p][w][0]].as_long()
                away_val = model[T[p][w][1]].as_long()
                print(f"{home_val}vs{away_val} ", end="")
            print()

        # Check unordered unique games
        pairs = set()
        for p in range(periods):
            for w in range(weeks):
                h = model[T[p][w][0]].as_long()
                a = model[T[p][w][1]].as_long()
                pair = tuple(sorted((h, a)))
                pairs.add(pair)
        expected = n * (n - 1) // 2
        print(f"\n🔍 Unique unordered games: {len(pairs)} (should be {expected})")

        sol = extract_solution(n, model, T, weeks, periods)
        save_to_json(n, result_key, runtime, True, None, sol)

    elif result == unsat:
        print("❌ UNSAT - No solution exists with these constraints (NO-SB).")
        save_to_json(n, result_key, runtime, True, None, [])

    else:
        print("⏰ UNKNOWN - Timeout or indeterminate (NO-SB).")
        save_to_json(n, result_key, 300, False, None, [])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SMT Decision Model WITHOUT Symmetry Breaking"
    )
    parser.add_argument("--teams", type=int, required=True,
                        help="Number of teams (even n)")
    args = parser.parse_args()

    test_without_symmetry(args.teams)
