# CDMO_Project/source/SMT/smt_aligned.py
from z3 import *

def create_smt_solver(n):
    """
    Create an SMT solver for n teams
    This follows EXACTLY the same approach as the CP model
    """
    print(f"Creating SMT solver for n={n} teams...")
    
    # Create a solver object
    s = Solver()
    
    # Calculate weeks and periods (same as CP)
    weeks = n - 1
    periods = n // 2
    
    print(f" - Weeks: {weeks}, Periods: {periods}")
    
    # STEP 1: Create variables 
    T = []
    for p in range(periods):
        period_games = []
        for w in range(weeks):
            home_var = Int(f'T_{p}_{w}_home')
            away_var = Int(f'T_{p}_{w}_away')
            period_games.append([home_var, away_var])
        T.append(period_games)
    
    # STEP 2: Add basic domain constraints
    print(" - Adding domain constraints...")
    for p in range(periods):
        for w in range(weeks):
            home, away = T[p][w]
            # Teams are from 1 to n (like the CP model)
            s.add(home >= 1, home <= n)
            s.add(away >= 1, away <= n)
            # A team cannot play against itself
            s.add(home != away)
    
    # STEP 3: Add symmetry breaking (home < away)
    print(" - Adding symmetry breaking...")
    for p in range(periods):
        for w in range(weeks):
            home, away = T[p][w]
            s.add(home < away)  # Home team ID < Away team ID
    
    # STEP 4: Fix first game (like CP model)
    print(" - Fixing first game...")
    if periods > 0 and weeks > 0:
        s.add(T[0][0][0] == 1)  # First game home team = 1
        s.add(T[0][0][1] == 2)  # First game away team = 2
    
    # STEP 5: CONSTRAINT 1 - Each team plays once per week
    print(" - Adding weekly constraints...")
    for w in range(weeks):
        # Collect all teams playing in this week
        week_teams = []
        for p in range(periods):
            week_teams.append(T[p][w][0])  # Home team
            week_teams.append(T[p][w][1])  # Away team
        # All teams in the week must be different
        s.add(Distinct(week_teams))
    
    # STEP 6: CONSTRAINT 2 - All unique games
    print(" - Adding unique games constraint...")
    all_games = []
    for p in range(periods):
        for w in range(weeks):
            home, away = T[p][w]
            # Encode each game as a unique number (like CP model: home*n + away)
            game_code = home * n + away
            all_games.append(game_code)
    # All game codes must be different
    s.add(Distinct(all_games))
    
    # STEP 7: CONSTRAINT 3 - At most 2 appearances per period
    print(" - Adding period constraints...")
    for team in range(1, n+1):  # Teams 1 to n
        for p in range(periods):
            appearances = 0
            for w in range(weeks):
                home, away = T[p][w]
                # Count if this team appears in this period
                appearances = appearances + If(Or(home == team, away == team), 1, 0)
            s.add(appearances <= 2)
    
    print(f"✅ Created solver with {len(s.assertions())} constraints")
    return s, T, weeks, periods

def print_solution(n, model, T, weeks, periods):
    """Print the solution in a nice format"""
    print(f"\n🏆 SOLUTION FOUND for n={n}")
    print("=" * 50)
    
    # Print schedule by weeks (easier to read)
    for w in range(weeks):
        print(f"Week {w+1}: ", end="")
        for p in range(periods):
            home_val = model[T[p][w][0]].as_long()
            away_val = model[T[p][w][1]].as_long()
            print(f"{home_val}vs{away_val} ", end="")
        print()
    
    # Verify the solution
    print(f"\n🔍 Verifying solution...")
    
    # Check all games are unique
    all_pairs = set()
    for p in range(periods):
        for w in range(weeks):
            home_val = model[T[p][w][0]].as_long()
            away_val = model[T[p][w][1]].as_long()
            pair = (home_val, away_val)
            all_pairs.add(pair)
    
    expected_games = n * (n - 1) // 2
    print(f"Unique games: {len(all_pairs)} (should be {expected_games})")
    
    if len(all_pairs) == expected_games:
        print("✅ All games are unique!")
    else:
        print("❌ Problem: Duplicate games found!")

def test_with_all_constraints():
    """Test with ALL constraints"""
    print("\n=== TESTING WITH ALL CONSTRAINTS ===")
    
    n = 6
    solver, T, weeks, periods = create_smt_solver(n)
    
    # Try to solve
    print(f"\n🔍 Solving...")
    result = solver.check()
    
    if result == sat:
        print("✅ SAT - Valid solution found!")
        model = solver.model()
        print_solution(n, model, T, weeks, periods)
        
        # Save to JSON (we'll implement this next)
        save_to_json(n, model, T, weeks, periods)
        
    elif result == unsat:
        print("❌ UNSAT - No solution exists with current constraints")
    else:
        print("⏰ UNKNOWN - Could not determine in time")

def save_to_json(n, model, T, weeks, periods):
    """Save solution in the required JSON format"""
    import json
    import os
    
    # Build the solution in the required format
    solution = []
    for w in range(weeks):
        week_games = []
        for p in range(periods):
            home_val = model[T[p][w][0]].as_long()
            away_val = model[T[p][w][1]].as_long()
            week_games.append([home_val, away_val])
        solution.append(week_games)
    
    # Create the result object
    result = {
        "z3_smt": {
            "time": 0,  # We'll add timing later
            "optimal": True,
            "obj": None,
            "sol": solution
        }
    }
    
    # Ensure the res/SMT folder exists
    os.makedirs("../../res/SMT", exist_ok=True)
    
    # Save to file
    filename = f"../../res/SMT/{n}.json"
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"💾 Solution saved to: {filename}")

# Run the test
if __name__ == "__main__":
    test_with_all_constraints()