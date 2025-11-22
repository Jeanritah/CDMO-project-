# smt_experiments.py
# Read SMT JSON results from res/SMT and print a summary table.

import json
import os
from math import comb


def load_smt_result(n, key="z3_smt_decision"):
    base_dir = os.path.dirname(__file__)
    res_dir = os.path.join(base_dir, "res", "SMT")
    filename = os.path.join(res_dir, f"{n}.json")

    if not os.path.exists(filename):
        print(f"[WARN] Missing file for n={n}: {filename}")
        return None, None, None

    with open(filename, "r") as f:
        data = json.load(f)

    entry = data.get(key)
    if entry is None:
        print(f"[WARN] Key '{key}' not found in {filename}")
        return None, None, None

    return entry.get("time"), entry.get("optimal"), entry.get("sol")


def analyze_solution(n, sol):
    if not sol:
        return 0, comb(n, 2)

    games = []
    for period in sol:
        for game in period:
            if isinstance(game, list) and len(game) == 2:
                games.append(tuple(game))

    uniq = len(set(games))
    expected = comb(n, 2)
    return uniq, expected


def classify_status(time_val, optimal, sol):
    if time_val is None or optimal is None:
        return "MISSING"

    if not optimal and time_val == 300:
        return "TIMEOUT"
    if optimal and (not sol or sol == []):
        return "UNSAT"
    if optimal and sol:
        return "SAT"
    return "UNKNOWN"


def run_smt_experiments():
    test_sizes = [4, 6, 8, 10, 12]

    print("=== SMT EXPERIMENTS (decision model) ===")
    print(f"{'n':>3} | {'time(s)':>8} | {'status':>8} | {'uniq':>6} | {'expected':>8}")
    print("-" * 45)

    for n in test_sizes:
        time_val, optimal, sol = load_smt_result(n)

        if time_val is None:
            print(f"{n:3} | {'-':>8} | {'MISSING':>8} | {'-':>6} | {'-':>8}")
            continue

        status = classify_status(time_val, optimal, sol)
        uniq, expected = analyze_solution(n, sol)
        t_str = f"{time_val:.0f}" if isinstance(time_val, (int, float)) else str(time_val)

        print(f"{n:3} | {t_str:>8} | {status:>8} | {uniq:6} | {expected:8}")


if __name__ == "__main__":
    run_smt_experiments()
