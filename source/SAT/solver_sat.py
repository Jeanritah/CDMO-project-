import os, json, time
from z3 import *

def ensure_folders():
    if not os.path.exists("res"):
        os.makedirs("res")
    if not os.path.exists("res/SAT"):
        os.makedirs("res/SAT")

def json_write(n, data):
    ensure_folders()
    with open(f"res/SAT/{n}.json", "w") as f:
        json.dump(data, f, indent=4)
        
def create_vars(n):
    W = n - 1
    P = n // 2

    home = {}  
    per = {}    
    for i in range(1, n):
        for j in range(i+1, n+1):
            for w in range(1, W+1):
                home[(i, j, w)] = Bool(f"h_{i}_{j}_{w}")

    # per[t,w,p]
    for t in range(1, n+1):
        for w in range(1, W+1):
            for p in range(1, P+1):
                per[(t, w, p)] = Bool(f"per_{t}_{w}_{p}")

    return home, per
def extract_schedule(model, n, home, per):
    W = n - 1
    P = n // 2
    schedule = [[None for _ in range(W)] for _ in range(P)]

    for w in range(1, W+1):
        for p in range(1, P+1):

            teams = [t for t in range(1, n+1)
                     if model.evaluate(per[(t, w, p)], model_completion=True)]

            if len(teams) != 2:
                schedule[p-1][w-1] = [None, None]
                continue

            i, j = teams
            a, b = min(i,j), max(i,j)

            if model.evaluate(home[(a,b,w)], model_completion=True):
                schedule[p-1][w-1] = [a,b]
            else:
                schedule[p-1][w-1] = [b,a]

    return schedule
def add_base_constraints(s, n, home, per):
    W = n - 1
    P = n // 2

    # 1) Each pair plays exactly once
    for i in range(1, n):
        for j in range(i+1, n+1):
            matches = []
            for w in range(1, W+1):
                matches.append(home[(i,j,w)])   # i home vs j
                # j home vs i is: home[i,j,w] == False but occurs
            s.add(PbEq([(m,1) for m in matches], 1))

    # 2) Each team plays exactly once per week
    for t in range(1, n+1):
        for w in range(1, W+1):
            vars_week = []
            for opp in range(1, n+1):
                if opp == t: continue
                i, j = min(t, opp), max(t, opp)
                vars_week.append(home[(i,j,w)])
            s.add(PbEq([(v,1) for v in vars_week], 1))

    # 3) Period limit = 2
    for t in range(1, n+1):
        for p in range(1, P+1):
            appear = []
            for w in range(1, W+1):
                for opp in range(1, n+1):
                    if opp == t: continue
                    i, j = min(t, opp), max(t, opp)
                    appear.append(per[(t,w,p)])
            s.add(PbLe([(a,1) for a in appear], 2))

def add_channeling_and_implied(s, n, home, per):
    W = n - 1
    P = n // 2

    # 1) Exactly two teams per period each week
    for w in range(1, W+1):
        for p in range(1, P+1):
            teams = [per[(t,w,p)] for t in range(1,n+1)]
            s.add(PbEq([(t,1) for t in teams], 2))

    # 2) Each team exactly one period per week
    for t in range(1,n+1):
        for w in range(1, W+1):
            s.add(PbEq([(per[(t,w,p)],1) for p in range(1,P+1)], 1))

    # 3) Home ↔ period consistency
    for i in range(1,n):
        for j in range(i+1,n+1):
            for w in range(1, W+1):
                s.add(Implies(
                    home[(i,j,w)],
                    Or([And(per[(i,w,p)], per[(j,w,p)]) for p in range(1,P+1)])
                ))
                s.add(Implies(
                    Or([And(per[(i,w,p)], per[(j,w,p)]) for p in range(1,P+1)]),
                    home[(i,j,w)]
                ))
                
def add_symmetry_breaking(s, n, home, per, for_opt):
    """Correct SB: does NOT break satisfiability."""
    W = n - 1

    # SB1: Fix first match (1,2) in week 1, period 1
    s.add(home[(1,2,1)] == True)
    s.add(per[(1,1,1)] == True)
    s.add(per[(2,1,1)] == True)

    # SB2: Team 1 meets team (w+1) in week w
    for w in range(1, W+1):
        opp = w+1
        if opp <= n:
            i, j = 1, opp
            s.add(home[(1,opp,w)] == True)

    # SB3: Lower index home (ONLY for no-opt)
    if not for_opt:
        for i in range(1,n):
            for j in range(i+1,n+1):
                for w in range(1,W+1):
                    s.add(home[(i,j,w)] == True)
                    
def solve_decision(n, use_sb):
    home, per = create_vars(n)
    s = Solver()
    s.set("timeout", 300000)
    s.set("threads", 1)

    add_base_constraints(s, n, home, per)
    add_channeling_and_implied(s, n, home, per)

    if use_sb:
        add_symmetry_breaking(s, n, home, per, for_opt=False)

    t0 = time.time()
    res = s.check()
    elapsed = time.time() - t0

    if res == unsat:
        return {"time": int(elapsed), "optimal": True, "obj": None, "sol": None}

    if res != sat:
        return {"time": 300, "optimal": False, "obj": None, "sol": None}

    model = s.model()
    sol = extract_schedule(model, n, home, per)
    return {"time": int(min(300,elapsed)), "optimal": True, "obj": None, "sol": sol}
    
def max_imbalance_constraint(s, n, home, M):
    W = n - 1
    for t in range(1, n+1):
        H = []
        A = []
        for opp in range(1, n+1):
            if opp == t: continue
            i, j = min(t,opp), max(t,opp)
            for w in range(1, W+1):
                if i == t:
                    H.append(home[(i,j,w)])
                else:
                    A.append(home[(i,j,w)])
        s.add(PbLe([(h,1) for h in H] + [(a,-1) for a in A], M))
        s.add(PbLe([(a,1) for a in A] + [(h,-1) for h in H], M))

def solve_opt(n, use_sb):
    best_model = None
    best_val = None

    low, high = 0, n-1
    start = time.time()

    while low <= high:
        mid = (low + high)//2

        home, per = create_vars(n)
        s = Solver()
        remaining = max(0, 300 - (time.time() - start))
        s.set("timeout", int(remaining*1000))
        s.set("threads", 1)

        add_base_constraints(s, n, home, per)
        add_channeling_and_implied(s, n, home, per)
        max_imbalance_constraint(s, n, home, mid)

        if use_sb:
            add_symmetry_breaking(s, n, home, per, for_opt=True)

        res = s.check()
        if res == sat:
            model = s.model()
            best_model = model
            best_val = mid
            high = mid - 1
        elif res == unsat:
            low = mid + 1
        else:
            return {"time": 300, "optimal": False, "obj": None, "sol": None}

        if time.time() - start >= 300:
            return {"time": 300, "optimal": False, "obj": None, "sol": None}

    if best_model is None:
        return {"time": 300, "optimal": False, "obj": None, "sol": None}

    sol = extract_schedule(best_model, n, home, per)
    return {
        "time": int(min(300, time.time() - start)),
        "optimal": True,
        "obj": best_val,
        "sol": sol
    }
def solve_all(n):
    return {
        "z3_nosb_noopt": solve_decision(n, use_sb=False),
        "z3_sb_noopt":   solve_decision(n, use_sb=True),
        "z3_nosb_opt":   solve_opt(n, use_sb=False),
        "z3_sb_opt":     solve_opt(n, use_sb=True)
    }
