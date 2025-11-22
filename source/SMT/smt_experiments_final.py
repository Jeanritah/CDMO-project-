# smt_experiments_final.py
# Summarise SMT results (decision + optimization) from res/SMT/*.json

import json
import os
from math import comb


BASE_DIR = os.path.dirname(__file__)
RES_DIR = os.path.join(BASE_DIR, "res", "SMT")


def load_result(n, key):
    """Load a given solver result (key) for instance n from res/SMT/n.json."""
    filename = os.path.join(RES_DIR, f"{n}.json")
    if not os.path.exists(filename):
        print(f"[WARN] Missing file for n={n}: {filename}")
        return None

    with open(filename, "r") as f:
        data = json.load(f)

    if key not in data:
        print(f"[WARN] Key '{key}' not found in {filename}")
        return None

    return data[key]


def analyze_solution(n, sol):
    """Return (uniq_games, expected_games) from a solution array."""
    if not sol:
        return 0, comb(n, 2)

    games = []
    for period in sol:
        for g in period:
            if isinstance(g, list) and len(g) == 2:
                games.append(tuple(g))

    uniq = len(set(games))
    expected = comb(n, 2)
    return uniq, expected


def classify_decision_status(entry):
    """Classify status for the decision model."""
    if entry is None:
        return "MISSING"

    time_val = entry.get("time")
    optimal = entry.get("optimal")
    sol = entry.get("sol") or []

    if optimal and sol:
        return "SAT"
    if optimal and not sol:
        return "UNSAT"
    if not optimal and time_val == 300:
        return "TIMEOUT"
    return "UNKNOWN"


def classify_opt_status(entry):
    """Classify status for the optimization model."""
    if entry is None:
        return "MISSING"

    time_val = entry.get("time")
    optimal = entry.get("optimal")
    sol = entry.get("sol") or []

    if optimal and sol:
        return "OPT"  # found feasible schedule + minimized objective
    if optimal and not sol:
        return "UNSAT"
    if not optimal and time_val == 300:
        return "TIMEOUT"
    return "UNKNOWN"


def print_decision_table(test_sizes):
    print("=== SMT DECISION MODEL (z3_smt_decision) ===")
    print(f"{'n':>3} | {'time(s)':>8} | {'status':>8} | {'uniq':>6} | {'expected':>8}")
    print("-" * 50)

    for n in test_sizes:
        entry = load_result(n, "z3_smt_decision")
        if entry is None:
            print(f"{n:3} | {'-':>8} | {'MISSING':>8} | {'-':>6} | {'-':>8}")
            continue

        time_val = entry.get("time")
        sol = entry.get("sol") or []
        status = classify_decision_status(entry)
        uniq, expected = analyze_solution(n, sol)
        t_str = f"{time_val:.0f}" if isinstance(time_val, (int, float)) else str(time_val)

        print(f"{n:3} | {t_str:>8} | {status:>8} | {uniq:6} | {expected:8}")
    print()


def print_opt_table(test_sizes):
    print("=== SMT OPTIMIZATION MODEL (z3_smt_opt) ===")
    print(f"{'n':>3} | {'time(s)':>8} | {'status':>8} | {'D*':>6} | {'uniq':>6} | {'exp':>6}")
    print("-" * 60)

    for n in test_sizes:
        entry = load_result(n, "z3_smt_opt")
        if entry is None:
            print(f"{n:3} | {'-':>8} | {'MISSING':>8} | {'-':>6} | {'-':>6} | {'-':>6}")
            continue

        time_val = entry.get("time")
        sol = entry.get("sol") or []
        obj = entry.get("obj")
        status = classify_opt_status(entry)
        uniq, expected = analyze_solution(n, sol)
        t_str = f"{time_val:.0f}" if isinstance(time_val, (int, float)) else str(time_val)
        d_str = "-" if obj is None else str(obj)

        print(f"{n:3} | {t_str:>8} | {status:>8} | {d_str:>6} | {uniq:>6} | {expected:>6}")
    print()


def main():
    test_sizes = [4, 6, 8, 10, 12]
    print_decision_table(test_sizes)
    print_opt_table(test_sizes)


if __name__ == "__main__":
    main()
