from z3 import *
import os
import time
import sys
import json

def ensure_folders():
    if not os.path.exists("res"):
        os.makedirs("res")
    if not os.path.exists("res/SAT"):
        os.makedirs("res/SAT")

def exactly1(vs):
    return PbEq([(v,1) for v in vs], 1)

def at_most(k, vs):
    return PbLe([(v,1) for v in vs], k)


def json_write(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def create_vars(n):
    W = n - 1
    P = n // 2

    home = {}
    per = {}

    for i in range(1, n):
        for j in range(i+1, n+1):
            for w in range(1, W+1):
                home[(i,j,w)] = Bool(f"h_{i}_{j}_{w}")

    for i in range(1, n+1):
        for w in range(1, W+1):
            for p in range(1, P+1):
                per[(i,w,p)] = Bool(f"per_{i}_{w}_{p}")

    return home, per

def extract_schedule(model, n, home, per):
    W = n - 1
    P = n // 2
    sched = [[None for _ in range(W)] for _ in range(P)]

    for w in range(1, W+1):
        for p in range(1, P+1):

            teams = [i for i in range(1, n+1)
                     if is_true(model.evaluate(per[(i,w,p)], model_completion=True))]

            if len(teams) != 2:
                sched[p-1][w-1] = [None, None]
                continue

            a,b = sorted(teams)

            if is_true(model.evaluate(home[(a,b,w)], model_completion=True)):
                sched[p-1][w-1] = [a, b]
            else:
                sched[p-1][w-1] = [b, a]

    return sched


def add_base_constraints(s, n, home, per):
    W = n - 1
    P = n // 2

    # Pair plays exactly once
    for i in range(1, n):
        for j in range(i+1, n+1):
            occ = []
            for w in range(1, W+1):
                for p in range(1, P+1):
                    occ.append(And(per[(i,w,p)], per[(j,w,p)]))
            s.add(exactly1(occ))

    # Team plays exactly once per week
    for i in range(1, n+1):
        for w in range(1, W+1):
            plays = []
            for p in range(1, P+1):
                for opp in range(1, n+1):
                    if opp == i: continue
                    a,b = min(i,opp), max(i,opp)
                    cond = And(per[(i,w,p)], per[(opp,w,p)])
                    plays.append(cond)
            s.add(exactly1(plays))

    # Each team exactly one period per week
    for i in range(1, n+1):
        for w in range(1, W+1):
            s.add(exactly1([per[(i,w,p)] for p in range(1, P+1)]))

    # Each period houses exactly 2 teams
    for w in range(1, W+1):
        for p in range(1, P+1):
            slots = [(per[(i, w, p)], 1) for i in range(1, n+1)]
            s.add(PbEq(slots,2))

    # Period limit ≤ 2
    for i in range(1, n+1):
        for p in range(1, P+1):
            appear = []
            for w in range(1, W+1):
                appear.append(per[(i,w,p)])
            s.add(at_most(2, appear))

def add_channeling_implied(s, n, home, per, use_sb, sb_home_lower_index):
    W = n - 1
    P = n // 2

    for i in range(1, n):
        for j in range(i+1, n+1):
            for w in range(1, W+1):

                # link home variable to per:
                # If this match occurs in week w, they must share a period
                for p in range(1, P+1):
                    s.add(Implies(home[(i,j,w)], And(per[(i,w,p)], per[(j,w,p)])))

                #if they meet in period p, refine home/away:
                for p in range(1, P+1):
                    s.add(Implies(And(per[(i,w,p)], per[(j,w,p)]),
                                  Or(home[(i,j,w)],  # (i,j)
                                     Not(home[(i,j,w)])))) # Z3 formality

    # SB rule: home team lower index (only when SB active AND no optimization)
    if sb_home_lower_index:
        for i in range(1, n):
            for j in range(i+1, n+1):
                for w in range(1, W+1):
                    # force lower index as home: home[i,j,w] = True
                    s.add(home[(i,j,w)])

def apply_symmetry_breaking(s, n, home, per, use_sb, sb_home_lower_index):
    if not use_sb:
        return

    W = n - 1
    P = n // 2

    # SB1: fix first match in week 1
    s.add(home[(1,2,1)])

    # SB2: order team 1's opponents
    # team 1 meets 2 in w=1, 3 in w=2, ..., n in w=n-1
    for opp in range(2, n+1):
        w = opp - 1
        if 1 < opp:
            for p in range(1, P+1):
                # team 1 & opp must be in same period in week w
                s.add(And(per[(1,w,p)], per[(opp,w,p)]))

    # SB3 is handled inside channeling: home[i,j,w]=True when no optimization

def add_imbalance_constraints(s, n, home, max_val):
    W = n - 1

    for i in range(1, n+1):

        home_ct = []
        away_ct = []

        for j in range(1, n+1):
            if j == i: continue
            a,b = min(i,j), max(i,j)
            for w in range(1, W+1):
                hv = home[(a,b,w)]
                if i == a:
                    home_ct.append(hv)
                else:
                    away_ct.append(hv)
        s.add(PbLe([(v,1) for v in home_ct] + [(v,-1) for v in away_ct], max_val))
        s.add(PbLe([(v,1) for v in away_ct] + [(v,-1) for v in home_ct], max_val))

def solve_decision(n, use_sb, sb_home_lower_index=False):
    home, per = create_vars(n)
    s = Solver()
    s.set("timeout", 300000)
    s.set("threads", 1)

    add_base_constraints(s, n, home, per)
    apply_symmetry_breaking(s, n, home, per, use_sb, sb_home_lower_index)
    add_channeling_implied(s, n, home, per, use_sb, sb_home_lower_index)

    start = time.time()
    res = s.check()
    elapsed = time.time() - start

    if res == sat:
        model = s.model()
        sol = extract_schedule(model, n, home, per)
        return {"time": int(min(300,elapsed)), "optimal": True, "obj": None, "sol": sol}

    if res == unsat:
        return {"time": int(elapsed), "optimal": True, "obj": None, "sol": None}

    return {"time": 300, "optimal": False, "obj": None, "sol": None}


def solve_opt(n, use_sb):
    home, per = create_vars(n)
    start = time.time()
    low, high = 0, n-1
    best_model = None
    best_obj = None

    while low <= high:
        mid = (low + high)//2

        s = Solver()
        s.set("timeout", max(1, 300000 - int((time.time()-start)*1000)))
        s.set("threads", 1)

        add_base_constraints(s, n, home, per)
        apply_symmetry_breaking(s, n, home, per, use_sb, sb_home_lower_index=False)
        add_channeling_implied(s, n, home, per, use_sb, sb_home_lower_index=False)
        add_imbalance_constraints(s, n, home, mid)

        res = s.check()

        if (time.time() - start) >= 300:
            break

        if res == sat:
            best_model = s.model()
            best_obj = mid
            high = mid - 1
        elif res == unsat:
            low = mid + 1
        else:
            break

    if best_model is None:
        elapsed = time.time()-start
        return {"time": 300, "optimal": False, "obj": None, "sol": None}

    sol = extract_schedule(best_model, n, home, per)
    elapsed = time.time() - start
    optimal = (low > high and elapsed < 300)

    return {"time": int(min(300,elapsed)), "optimal": optimal, "obj": best_obj, "sol": sol}

def solve_all(n):
    return {
        "z3_nosb_noopt": solve_decision(n, use_sb=False),
        "z3_nosb_opt":   solve_opt(n, use_sb=False),
        "z3_sb_noopt":   solve_decision(n, use_sb=True, sb_home_lower_index=True),
        "z3_sb_opt":     solve_opt(n, use_sb=True)
    }
