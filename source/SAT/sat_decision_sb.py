# Imports
!pip install z3-solver
import os
os.makedirs("res/SAT", exist_ok=True)

import json
import time
from z3 import *

# Cardinality helpers
def exactly_one(vs):
    return And(AtLeast(*vs, 1), AtMost(*vs, 1))

def exactly_k(vs, k):
    return And(AtLeast(*vs, k), AtMost(*vs, k))

def at_most_k(vs, k):
    return AtMost(*vs, k)


# Solver
def solve_tournament_sat_safe_sb(n):
    assert n % 2 == 0
    W = n - 1
    P = n // 2

    # Decision variables
    home = [[[Bool(f"home_{i}_{j}_{w}") for w in range(W)]
             for j in range(n)]
             for i in range(n)]

    per = [[[Bool(f"per_{i}_{w}_{p}") for p in range(P)]
            for w in range(W)]
            for i in range(n)]

    s = Solver()
    s.set("timeout", 300000)

    # BASE CONSTRAINTS

    # (1) No self games
    for i in range(n):
        for w in range(W):
            s.add(Not(home[i][i][w]))

    # (2) Exactly once per unordered pair
    for i in range(n):
        for j in range(i+1, n):
            s.add(exactly_one([Or(home[i][j][w], home[j][i][w])
                               for w in range(W)]))

    # (3) Mutual exclusion
    for i in range(n):
        for j in range(n):
            if i != j:
                for w in range(W):
                    s.add(Implies(home[i][j][w], Not(home[j][i][w])))

    # (4) Same period if they play
    for i in range(n):
        for j in range(n):
            if i != j:
                for w in range(W):
                    for p in range(P):
                        s.add(Implies(home[i][j][w],
                                      per[i][w][p] == per[j][w][p]))

    # (5) One match per team per week
    for i in range(n):
        for w in range(W):
            s.add(exactly_one(
                [Or(home[i][j][w], home[j][i][w])
                 for j in range(n) if j != i]
            ))

    # (6) Exactly 1 period per team per week
    for i in range(n):
        for w in range(W):
            s.add(exactly_one([per[i][w][p] for p in range(P)]))

    # (7) Exactly 2 teams per period
    for w in range(W):
        for p in range(P):
            s.add(exactly_k([per[i][w][p] for i in range(n)], 2))

    # (8) At most twice in same period
    for i in range(n):
        for p in range(P):
            s.add(at_most_k([per[i][w][p] for w in range(W)], 2))


    # Symmetry Breaking

    # SB1 — fix Team 1 vs Team n in Week 0, Team 1 is home
    s.add(home[0][n-1][0] == True)
    s.add(home[n-1][0][0] == False)

    # SB2 — put this match in Period 0
    s.add(per[0][0][0] == True)
    s.add(per[n-1][0][0] == True)


    # Solve
    t0 = time.time()
    res = s.check()
    runtime = int(time.time() - t0)

    if res == unknown:
        return {"time": 300, "optimal": False, "obj": None, "sol": None}

    if res == unsat:
        return {"time": runtime, "optimal": True, "obj": None, "sol": None}

    # SAT — extract result
    m = s.model()
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

    return {"time": runtime, "optimal": True, "obj": None, "sol": sol}

# Instances
instances = [6, 8, 10, 12, 14, 16, 18]

for n in instances:
    print(f"Solving SB SAT model for n = {n}")
    result = solve_tournament_sat_safe_sb(n)

    with open(f"res/SAT/{n}.json","w") as f:
        json.dump({"z3_!obj_sb": result}, f, indent=2)

    print("Saved.")
