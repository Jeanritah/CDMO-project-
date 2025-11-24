!pip install z3-solver
import os
os.makedirs("res/SAT", exist_ok=True)

#Imports
import json
import time
from z3 import *

#Cardinality helpers
def exactly_one(vs):
    return And(AtLeast(*vs, 1), AtMost(*vs, 1))

def exactly_k(vs, k):
    return And(AtLeast(*vs, k), AtMost(*vs, k))

def at_most_k(vs, k):
    return AtMost(*vs, k)

#SAT decision model
def solve_tournament_sat(n):
    assert n % 2 == 0
    W = n - 1
    P = n // 2

    # Decision variables
    # home[i][j][w] = i plays j at HOME in week w
    home = [[[Bool(f"home_{i}_{j}_{w}") for w in range(W)]
             for j in range(n)] for i in range(n)]
    # per[i][w][p] = i plays in period p in week w
    per = [[[Bool(f"per_{i}_{w}_{p}") for p in range(P)]
            for w in range(W)] for i in range(n)]

    s = Solver()
    s.set("timeout", 300000)

    #Base constraints
    # (1) No self games
    for i in range(n):
        for w in range(W):
            s.add(Not(home[i][i][w]))

    # (2) Each unordered pair {i,j} plays exactly once over all weeks
    for i in range(n):
        for j in range(i+1, n):
            plays = [Or(home[i][j][w], home[j][i][w]) for w in range(W)]
            s.add(exactly_one(plays))

    # (3) Mutual exclusion: if i plays j at home, j cannot play i at home
    for i in range(n):
        for j in range(n):
            if i != j:
                for w in range(W):
                    s.add(Implies(home[i][j][w], Not(home[j][i][w])))

    # (4) Restored: If i plays j in week w then they must share the same period
    for i in range(n):
        for j in range(n):
            if i != j:
                for w in range(W):
                    for p in range(P):
                        s.add(Implies(home[i][j][w], per[i][w][p] == per[j][w][p]))

    # (5) Each team plays exactly once per week
    for i in range(n):
        for w in range(W):
            games = [Or(home[i][j][w], home[j][i][w]) for j in range(n) if j != i]
            s.add(exactly_one(games))

    # (6) Each team is assigned to exactly one period per week
    for i in range(n):
        for w in range(W):
            s.add(exactly_one([per[i][w][p] for p in range(P)]))

    # (7) Each period has exactly 2 teams every week
    for w in range(W):
        for p in range(P):
            s.add(exactly_k([per[i][w][p] for i in range(n)], 2))

    # (8) Each team plays at most twice in the same period over whole tournament
    for i in range(n):
        for p in range(P):
            s.add(at_most_k([per[i][w][p] for w in range(W)], 2))

    #Solving
    t0 = time.time()
    res = s.check()
    dt = time.time() - t0
    t_int = int(dt // 1)

    if res == unknown:
        return {
            "time": 300,
            "optimal": False,
            "obj": None,
            "sol": None
        }

    # UNSAT proven
    if res == unsat:
        return {
            "time": t_int,
            "optimal": True,
            "obj": None,
            "sol": None
        }

    # SAT case
    m = s.model()

    # sol[p][w] = [home, away]
    sol = [[None for _ in range(W)] for _ in range(P)]

    for w in range(W):
        period_map = {p: [] for p in range(P)}
        for i in range(n):
            for p in range(P):
                if m.evaluate(per[i][w][p]):
                    period_map[p].append(i+1)

        for p in range(P):
            t1, t2 = period_map[p]
            if m.evaluate(home[t1-1][t2-1][w]):
                sol[p][w] = [t1, t2]
            else:
                sol[p][w] = [t2, t1]

    return {
        "time": t_int,
        "optimal": True,
        "obj": None,
        "sol": sol
    }

#Instances
instances = [6, 8, 10, 12, 14, 16, 18]

for n in instances:
    print(f"Solving SAT decision model for n = {n}")
    result = solve_tournament_sat(n)

    out_path = f"res/SAT/{n}.json"
    with open(out_path, "w") as f:
        json.dump({"z3_!obj_!sb": result}, f, indent=2)

    print(f"Saved.")
