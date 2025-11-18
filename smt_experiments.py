# CDMO_Project/source/SMT/smt_experiments.py
from z3 import *
import json
import os
import time
from smt_aligned import create_smt_solver

def run_smt_experiments():
    """Run SMT experiments on multiple instance sizes"""
    
    # Test the same sizes as your friend's CP model
    test_sizes = [6, 8, 10, 12, 14]
    
    print("=== SMT EXPERIMENTS ===")
    print("Comparing with CP results...")
    print(f"{'n':>3} | {'Time (s)':>8} | {'Status':>10} | {'Unique Games':>12}")
    print("-" * 50)
    
    for n in test_sizes:
        # Set a timeout of 5 minutes (300 seconds) like the project requires
        solver, T, weeks, periods = create_smt_solver(n)
        solver.set("timeout", 300 * 1000)  # 300 seconds in milliseconds
        
        start_time = time.time()
        result = solver.check()
        end_time = time.time()
        solve_time = end_time - start_time
        
        if result == sat:
            model = solver.model()
            # Count unique games to verify
            all_pairs = set()
            for p in range(periods):
                for w in range(weeks):
                    home_val = model[T[p][w][0]].as_long()
                    away_val = model[T[p][w][1]].as_long()
                    all_pairs.add((home_val, away_val))
            
            unique_games = len(all_pairs)
            expected_games = n * (n - 1) // 2
            
            status = "✅ SAT" if unique_games == expected_games else "❌ INVALID"
            print(f"{n:3} | {solve_time:8.3f} | {status:>10} | {unique_games:4}/{expected_games:4}")
            
            # Save solution
            save_solution(n, model, T, weeks, periods, solve_time)
            
        elif result == unsat:
            print(f"{n:3} | {solve_time:8.3f} | {'❌ UNSAT':>10} | {'N/A':>12}")
        else:
            print(f"{n:3} | {solve_time:8.3f} | {'⏰ TIMEOUT':>10} | {'N/A':>12}")
            # Save timeout result
            save_timeout(n, solve_time)

def save_solution(n, model, T, weeks, periods, solve_time):
    """Save a valid solution to JSON"""
    solution = []
    for w in range(weeks):
        week_games = []
        for p in range(periods):
            home_val = model[T[p][w][0]].as_long()
            away_val = model[T[p][w][1]].as_long()
            week_games.append([home_val, away_val])
        solution.append(week_games)
    
    result = {
        "z3_smt": {
            "time": int(solve_time),  # Floor as required
            "optimal": True,
            "obj": None,
            "sol": solution
        }
    }
    
    os.makedirs("../../res/SMT", exist_ok=True)
    filename = f"../../res/SMT/{n}.json"
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)

def save_timeout(n, solve_time):
    """Save timeout result"""
    result = {
        "z3_smt": {
            "time": 300,  # As required: time=300 means timeout
            "optimal": False,
            "obj": None,
            "sol": []
        }
    }
    
    os.makedirs("../../res/SMT", exist_ok=True)
    filename = f"../../res/SMT/{n}.json"
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)

def compare_with_cp():
    """Compare SMT results with your friend's CP results"""
    print("\n" + "="*60)
    print("COMPARISON: SMT vs CP")
    print("="*60)
    print(f"{'n':>3} | {'SMT Time':>8} | {'CP Time':>8} | {'Ratio':>6}")
    print("-" * 40)
    
    # Your friend's CP results from the PDF
    cp_times = {
        6: 0.003,
        8: 0.004, 
        10: 0.541,
        12: 9.546,
        14: 241.026
    }
    
    for n in [6, 8, 10, 12, 14]:
        smt_file = f"../../res/SMT/{n}.json"
        if os.path.exists(smt_file):
            with open(smt_file, 'r') as f:
                data = json.load(f)
                smt_time = data["z3_smt"]["time"]
                cp_time = cp_times.get(n, "N/A")
                
                if smt_time != 300 and cp_time != "N/A":  # Not timeout
                    ratio = smt_time / cp_time
                    print(f"{n:3} | {smt_time:8.3f} | {cp_time:8.3f} | {ratio:6.1f}x")
                else:
                    status = "TIMEOUT" if smt_time == 300 else "N/A"
                    print(f"{n:3} | {smt_time:8} | {cp_time:8} | {status:>6}")

if __name__ == "__main__":
    run_smt_experiments()
    compare_with_cp()