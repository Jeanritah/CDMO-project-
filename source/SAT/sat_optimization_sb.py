# Imports
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
def solve_opt_sb(n):
    assert n % 2 == 0
    W = n - 1
    P = n // 2

    home = [[[Bool(f"home_{i}_{j}_{w}") for w in range(W)]
             for j in range(n)] for i in range(n)]

    per  = [[[Bool(f"per_{i}_{w}_{p}") for p in range(P)]
             for w in range(W)] for i in range(n)]

    # Imbalance
    home_count = [
        Sum([If(home[i][j][w],1,0)
             for j in range(n) for w in range(W) if j!=i])
        for i in range(n)
    ]
    total_games = n - 1
    diff = [home_count[i] - (total_games - home_count[i]) for i in range(n)]

    # Solver
    s = Solver()
    s.set("timeout", 300000)

    # BASE CONSTRAINTS
    # no self games
    for i in range(n):
        for w in range(W):
            s.add(Not(home[i][i][w]))

    # each pair plays exactly once
    for i in range(n):
        for j in range(i+1,n):
            s.add(exactly_one([Or(home[i][j][w], home[j][i][w])
                               for w in range(W)]))

    # match implies same period
    for i in range(n):
        for j in range(n):
            if i!=j:
                for w in range(W):
                    for p in range(P):
                        s.add(Implies(home[i][j][w],
                                      per[i][w][p] == per[j][w][p]))

    # one match per week
    for i in range(n):
        for w in range(W):
            s.add(exactly_one([
                Or(home[i][j][w], home[j][i][w])
                for j in range(n) if j != i
            ]))

    # one period per week
    for i in range(n):
        for w in range(W):
            s.add(exactly_one([per[i][w][p] for p in range(P)]))

    # exactly two teams per period per week
    for w in range(W):
        for p in range(P):
            s.add(exactly_k([per[i][w][p] for i in range(n)], 2))

    # each team uses each period at most twice
    for i in range(n):
        for p in range(P):
            s.add(at_most_k([per[i][w][p] for w in range(W)], 2))


    # Symmetry breaking

    # SB1: Fix (1,n) in week 0, 1 home
    s.add(home[0][n-1][0] == True)
    s.add(home[n-1][0][0] == False)

    # SB2: Fix all week-0 pairings
    for i in range(1, n//2):
        j = n-1-i
        s.add(home[i][j][0] == True)
        s.add(home[j][i][0] == False)

        # forbid them anywhere else
        for w in range(1, W):
            s.add(home[i][j][w] == False)
            s.add(home[j][i][w] == False)

    # Early feasibility
    t0 = time.time()
    r = s.check()

    if r != sat:
        return {"time":300, "optimal":False, "sol":[]}

    m0 = s.model()

    imbalance = []
    for i in range(n):
        hc = sum(1 for j in range(n) for w in range(W)
                 if j!=i and is_true(m0.evaluate(home[i][j][w])))
        ac = (n-1) - hc
        imbalance.append(abs(hc-ac))

    best_possible = max(imbalance)

    if best_possible <= 1:
        return {
            "time": int(time.time()-t0),
            "optimal": True,
            "obj": best_possible,
            "sol": extract_solution(n,W,P,m0,per,home)
        }

    # Binary search
    low, high = 0, 2
    best_M = None
    best_model = None

    while low <= high:

        if time.time() - t0 > 300:
            return {"time":300, "optimal":False}

        mid = (low+high)//2

        s.push()
        for i in range(n):
            s.add(diff[i] <= mid)
            s.add(-diff[i] <= mid)

        r = s.check()

        if r == sat:
            best_M = mid
            best_model = s.model()
            s.pop()
            high = mid - 1
        else:
            s.pop()
            low = mid + 1

    if best_model is None:
        return {"time":int(time.time()-t0), "optimal":False}

    return {
        "time": int(time.time()-t0),
        "optimal": True,
        "obj": best_M,
        "sol": extract_solution(n,W,P,best_model,per,home)
    }


# Extract solution
def extract_solution(n,W,P,m,per,home):
    sol = [[None for _ in range(W)] for _ in range(P)]
    for w in range(W):
        period_map = {p:[] for p in range(P)}
        for i in range(n):
            for p in range(P):
                if is_true(m.evaluate(per[i][w][p])):
                    period_map[p].append(i+1)
        for p in range(P):
            t1,t2 = period_map[p]
            if is_true(m.evaluate(home[t1-1][t2-1][w])):
                sol[p][w] = [t1,t2]
            else:
                sol[p][w] = [t2,t1]
    return sol
