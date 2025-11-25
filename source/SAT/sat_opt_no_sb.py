# Imports
import os
os.makedirs("res/SAT", exist_ok=True)

import json
import time
from z3 import *

def exactly_one(vs):
    return And(AtLeast(*vs, 1), AtMost(*vs, 1))

def exactly_k(vs, k):
    return And(AtLeast(*vs, k), AtMost(*vs, k))

def at_most_k(vs, k):
    return AtMost(*vs, k)


def solve_opt_no_sb(n):

    assert n % 2 == 0
    W = n - 1
    P = n // 2

    # Variables
    home = [[[Bool(f"home_{i}_{j}_{w}") for w in range(W)]
             for j in range(n)] for i in range(n)]
    per = [[[Bool(f"per_{i}_{w}_{p}") for p in range(P)]
            for w in range(W)] for i in range(n)]

    # Objective expression
    home_count = [
        Sum([If(home[i][j][w], 1, 0)
             for j in range(n) for w in range(W) if j != i])
        for i in range(n)
    ]
    total_games = n - 1
    diff = [home_count[i] - (total_games - home_count[i]) for i in range(n)]

    # Solver
    s = Solver()
    s.set("timeout", 300000)  

    # Base constraints
    for i in range(n):
        for w in range(W):
            s.add(Not(home[i][i][w]))

    for i in range(n):
        for j in range(i+1, n):
            s.add(exactly_one([Or(home[i][j][w], home[j][i][w])
                               for w in range(W)]))

    for i in range(n):
        for j in range(n):
            if i != j:
                for w in range(W):
                    s.add(Implies(home[i][j][w], Not(home[j][i][w])))

    for i in range(n):
        for j in range(n):
            if i != j:
                for w in range(W):
                    for p in range(P):
                        s.add(Implies(home[i][j][w],
                                      per[i][w][p] == per[j][w][p]))

    for i in range(n):
        for w in range(W):
            s.add(exactly_one([
                Or(home[i][j][w], home[j][i][w])
                for j in range(n) if j != i
            ]))

    for i in range(n):
        for w in range(W):
            s.add(exactly_one([per[i][w][p] for p in range(P)]))

    for w in range(W):
        for p in range(P):
            s.add(exactly_k([per[i][w][p] for i in range(n)], 2))

    for i in range(n):
        for p in range(P):
            s.add(at_most_k([per[i][w][p] for w in range(W)], 2))

    # Early feasibility
    t0 = time.time()

    if s.check() == sat:
        m0 = s.model()
        imbalance = []
        for i in range(n):
            hc = sum(1 for j in range(n) for w in range(W)
                     if j != i and m0.evaluate(home[i][j][w]))
            ac = (n - 1) - hc
            imbalance.append(abs(hc - ac))

        best_possible = max(imbalance)
        if best_possible <= 1:
            dt = int(time.time() - t0)
            return ({
                "time": dt,
                "optimal": True,
                "obj": best_possible,
                "sol": extract_solution(n, W, P, m0, per, home)
            })

    # Binary search
    low, high = 0, 2
    best_M = None
    best_model = None

    while low <= high:

        if time.time() - t0 > 300:
            return {"time": 300, "optimal": False, "obj": None, "sol": []}

        mid = (low + high) // 2

        s.push()
        s.set("timeout", 300000)

        for i in range(n):
            s.add(diff[i] <= mid, -diff[i] <= mid)

        res = s.check()

        if res == sat:
            best_M = mid
            best_model = s.model()
            s.pop()
            high = mid - 1
        else:
            s.pop()
            low = mid + 1

    if best_model is None:
        return {"time": int(time.time() - t0),
                "optimal": False, "obj": None, "sol": []}

    dt = int(time.time() - t0)
    sol = extract_solution(n, W, P, best_model, per, home)

    return {"time": dt, "optimal": True, "obj": best_M, "sol": sol}


def extract_solution(n, W, P, m, per, home):
    sol = [[None for _ in range(W)] for _ in range(P)]
    for w in range(W):
        period_map = {p: [] for p in range(P)}
        for i in range(n):
            for p in range(P):
                if m.evaluate(per[i][w][p]):
                    period_map[p].append(i + 1)
        for p in range(P):
            t1, t2 = period_map[p]
            if m.evaluate(home[t1-1][t2-1][w]):
                sol[p][w] = [t1, t2]
            else:
                sol[p][w] = [t2, t1]
    return sol
