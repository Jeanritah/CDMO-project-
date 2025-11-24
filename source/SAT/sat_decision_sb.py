# Imports
!pip install z3-solver
import os
os.makedirs("res/SAT", exist_ok=True)

import json
import time
from z3 import *

def exactly_one(vs):
    return And(AtLeast(*vs,1), AtMost(*vs,1))

def exactly_k(vs,k):
    return And(AtLeast(*vs,k), AtMost(*vs,k))

def at_most_k(vs,k):
    return AtMost(*vs,k)


# Solver
def solve_tournament_sat_noopt(n):
    assert n % 2 == 0
    W = n - 1         # weeks
    P = n // 2        # periods

    # Variables
    home = [[[Bool(f"home_{i}_{j}_{w}") for w in range(W)]
              for j in range(n)] for i in range(n)]

    per  = [[[Bool(f"per_{i}_{w}_{p}") for p in range(P)]
              for w in range(W)] for i in range(n)]

    # Solver
    s = Solver()
    s.set("timeout", 300000)    # 5 min wall timeout

    # Base constraints

    # No self games
    for i in range(n):
        for w in range(W):
            s.add(Not(home[i][i][w]))

    # Each pair plays exactly once
    for i in range(n):
        for j in range(i+1, n):
            s.add(exactly_one([Or(home[i][j][w], home[j][i][w])
                               for w in range(W)]))

    # Match, same period
    for i in range(n):
        for j in range(n):
            if i != j:
                for w in range(W):
                    for p in range(P):
                        s.add(Implies(home[i][j][w],
                                      per[i][w][p] == per[j][w][p]))

    # One match per week
    for i in range(n):
        for w in range(W):
            s.add(exactly_one([
                Or(home[i][j][w], home[j][i][w])
                for j in range(n) if j != i
            ]))

    # One period per week
    for i in range(n):
        for w in range(W):
            s.add(exactly_one([per[i][w][p] for p in range(P)]))

    # Exactly 2 teams per period
    for w in range(W):
        for p in range(P):
            s.add(exactly_k([per[i][w][p] for i in range(n)], 2))

    # At most 2 uses of same period per team
    for i in range(n):
        for p in range(P):
            s.add(at_most_k([per[i][w][p] for w in range(W)], 2))


    # Symmetry breaking

    # SB1: Fix match (1,n) in week 0, team 1 home
    s.add(home[0][n-1][0] == True)
    s.add(home[n-1][0][0] == False)

    # SB2: Fix all week 0 pairings (1,n), (2,n-1),...
    for i in range(1, n//2):
        j = n - 1 - i

        # Fix the ORIENTATION to avoid branching
        s.add(home[i][j][0] == True)
        s.add(home[j][i][0] == False)

        # Forbid these pairs from occurring in other weeks
        for w in range(1, W):
            s.add(home[i][j][w] == False)
            s.add(home[j][i][w] == False)

    # Solve
    t0 = time.time()
    result = s.check()

    if result != sat:
        return {"time": int(time.time()-t0), "optimal": True,
                "obj": None, "sol": None}

    m = s.model()
    sol = extract_solution(n, W, P, m, per, home)

    return {
        "time": int(time.time()-t0),
        "optimal": True,
        "obj": None,
        "sol": sol
    }


# Solution
def extract_solution(n,W,P,m,per,home):
    sol = [[None for _ in range(W)] for _ in range(P)]

    for w in range(W):
        period_map = {p: [] for p in range(P)}

        for i in range(n):
            for p in range(P):
                if is_true(m.evaluate(per[i][w][p])):
                    period_map[p].append(i+1)

        for p in range(P):
            t1, t2 = period_map[p]
            if is_true(m.evaluate(home[t1-1][t2-1][w])):
                sol[p][w] = [t1, t2]
            else:
                sol[p][w] = [t2, t1]

    return sol


# Instances
instances=[6,8,10,12,14,16,18]

for n in instances:
    print(f"\nSolving SB model for n = {n}")
    result = solve_tournament_sat_noopt(n)
    with open(f"res/SAT/{n}.json","w") as f:
        json.dump({"z3_!obj_sb":result}, f, indent=2)
    print("Saved.")
