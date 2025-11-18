# CDMO_Project/source/SMT/smt_optimized.py
from z3 import *
import json
import os
import time

def create_optimized_smt_solver(n):
    """
    Optimized SMT solver with better strategies
    """
    print(f"Creating OPTIMIZED SMT solver for n={n} teams...")
    
    # Create solver with better tactics
    s = Solver()
    
    # Use different solving strategy
    s.set("timeout", 300 * 1000)
    s.set("auto_config", False)
    s.set("smt.phase_selection", 5)  # Random phase selection
    
    weeks = n - 1
    periods = n // 2
    
    # Create variables (same structure)
    T = []
    for p in range(periods):
        period_games = []
        for w in range(weeks):
            home_var = Int(f'T_{p}_{w}_home')
            away_var = Int(f'T_{p}_{w}_away')
            period_games.append([home_var, away_var])
        T.append(period_games)
    
    # Domain constraints
    for p in range(periods):
        for w in range(weeks):
            home, away = T[p][w]
            s.add(home >= 1, home <= n)
            s.add(away >= 1, away <= n)
            s.add(home != away)
            s.add(home < away)  # Symmetry breaking
    
    # Fix first game
    if periods > 0 and weeks > 0:
        s.add(T[0][0][0] == 1)
        s.add(T[0][0][1] == 2)
    
    # OPTIMIZATION 1: More efficient weekly constraints
    for w in range(weeks):
        week_teams = []
        for p in range(periods):
            week_teams.append(T[p][w][0])
            week_teams.append(T[p][w][1])
        s.add(Distinct(week_teams))
    
    # OPTIMIZATION 2: Alternative unique games encoding
    all_games = []
    for p in range(periods):
        for w in range(weeks):
            home, away = T[p][w]
            # Use simpler encoding
            all_games.append(home * 100 + away)  # Assuming n < 100
    
    s.add(Distinct(all_games))
    
    # OPTIMIZATION 3: More efficient period constraints
    for team in range(1, n+1):
        for p in range(periods):
            period_appearances = []
            for w in range(weeks):
                home, away = T[p][w]
                period_appearances.append(If(Or(home == team, away == team), 1, 0))
            s.add(sum(period_appearances) <= 2)
    
    return s, T, weeks, periods

def run_optimized_experiments():
    """Run experiments with optimized model"""
    
    test_sizes = [6, 8, 10, 12]
    
    print("=== OPTIMIZED SMT EXPERIMENTS ===")
    print(f"{'n':>3} | {'Time (s)':>8} | {'Status':>10}")
    print("-" * 30)
    
    for n in test_sizes:
        solver, T, weeks, periods = create_optimized_smt_solver(n)
        
        start_time = time.time()
        result = solver.check()
        end_time = time.time()
        solve_time = end_time - start_time
        
        if result == sat:
            print(f"{n:3} | {solve_time:8.3f} | {'✅ SAT':>10}")
            save_optimized_solution(n, solver.model(), T, weeks, periods, solve_time)
        elif result == unsat:
            print(f"{n:3} | {solve_time:8.3f} | {'❌ UNSAT':>10}")
        else:
            print(f"{n:3} | {solve_time:8.3f} | {'⏰ TIMEOUT':>10}")

def save_optimized_solution(n, model, T, weeks, periods, solve_time):
    """Save optimized solution"""
    solution = []
    for w in range(weeks):
        week_games = []
        for p in range(periods):
            home_val = model[T[p][w][0]].as_long()
            away_val = model[T[p][w][1]].as_long()
            week_games.append([home_val, away_val])
        solution.append(week_games)
    
    result = {
        "z3_smt_optimized": {
            "time": int(solve_time),
            "optimal": True,
            "obj": None,
            "sol": solution
        }
    }
    
    os.makedirs("../../res/SMT", exist_ok=True)
    filename = f"../../res/SMT/{n}_optimized.json"
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    run_optimized_experiments()