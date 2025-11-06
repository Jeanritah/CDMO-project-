# CDMO_Project/source/SMT/smt_aligned.py
from z3 import *
# library parsing arguments from command line
import argparse

def create_smt_solver(n):
    """
    Create an SMT solver for n teams
    This follows EXACTLY the same approach as the CP model for fair comparison
    """
    print(f"Creating SMT solver for n={n} teams...")
    
    # Create a solver object - this is the Z3 "engine" that will solve our constraints
    s = Solver()
    
    # Calculate weeks and periods (same as CP)
    # For n teams: n-1 weeks needed for round-robin, n/2 periods per week
    weeks = n - 1
    periods = n // 2
    
    print(f" - Weeks: {weeks}, Periods: {periods}")
    
    # STEP 1: Create variables - 3D array structure matching CP model
    # T[period][week] = [home_team, away_team]
    # This mirrors the CP model's game[p,w,1] and game[p,w,2] structure
    T = []
    for p in range(periods):
        period_games = []
        for w in range(weeks):
            # Create Z3 integer variables for home and away teams
            home_var = Int(f'T_{p}_{w}_home')  # Home team in period p, week w
            away_var = Int(f'T_{p}_{w}_away')  # Away team in period p, week w
            period_games.append([home_var, away_var])
        T.append(period_games)
    
    # STEP 2: Add basic domain constraints
    # Ensure all team assignments are valid numbers
    print(" - Adding domain constraints...")
    for p in range(periods):
        for w in range(weeks):
            home, away = T[p][w]
            # Teams are from 1 to n (like the CP model)
            s.add(home >= 1, home <= n)  # Home team must be valid team number
            s.add(away >= 1, away <= n)  # Away team must be valid team number
            # A team cannot play against itself
            s.add(home != away)  # Prevent meaningless "Team 1 vs Team 1" games
    
    # STEP 3: Add symmetry breaking (home < away)
    # This eliminates duplicate solutions where [1,2] and [2,1] represent the same game
    # Reduces search space by forcing consistent team ordering within games
    print(" - Adding symmetry breaking...")
    for p in range(periods):
        for w in range(weeks):
            home, away = T[p][w]
            s.add(home < away)  # Home team ID < Away team ID for consistent ordering
    
    # STEP 4: Fix first game (like CP model)
    # Break symmetry by fixing the very first game to specific teams
    # This prevents counting permutations of team labels as different solutions
    print(" - Fixing first game...")
    if periods > 0 and weeks > 0:
        s.add(T[0][0][0] == 1)  # First game home team = Team 1
        s.add(T[0][0][1] == 2)  # First game away team = Team 2
    
    # STEP 5: CONSTRAINT 1 - Each team plays once per week
    # In each week, all n teams must appear exactly once across all periods
    # This implements "every team plays once a week" requirement
    print(" - Adding weekly constraints...")
    for w in range(weeks):
        # Collect all teams playing in this week (both home and away)
        week_teams = []
        for p in range(periods):
            week_teams.append(T[p][w][0])  # Home team in this period
            week_teams.append(T[p][w][1])  # Away team in this period
        # All teams in the week must be different - no team plays twice in same week
        s.add(Distinct(week_teams))  # Z3's built-in "all different" constraint
    
    # STEP 6: CONSTRAINT 2 - All unique games
    # Every pair of teams must play exactly once in the tournament
    # We use a mathematical trick: encode each game as a unique number
    print(" - Adding unique games constraint...")
    all_games = []
    for p in range(periods):
        for w in range(weeks):
            home, away = T[p][w]
            # Encode each game as a unique number using: home * n + away
            # Example: Game "Team 2 vs Team 5" becomes 2*6 + 5 = 17 (for n=6)
            # This creates a unique identifier for each possible game pair
            game_code = home * n + away
            all_games.append(game_code)
    # All game codes must be different - ensures each game appears exactly once
    s.add(Distinct(all_games))  # No duplicate games in the tournament
    
    # STEP 7: CONSTRAINT 3 - At most 2 appearances per period
    # Each team can play at most twice in the same period across all weeks
    # This implements the "no team plays more than twice in same period" requirement
    print(" - Adding period constraints...")
    for team in range(1, n+1):  # Check constraints for each team (Team 1 to Team n)
        for p in range(periods):  # For each period slot
            appearances = 0
            for w in range(weeks):  # Count appearances across all weeks
                home, away = T[p][w]
                # Count if this team appears in this period (either as home or away)
                # If-then-else: 1 if team appears, 0 otherwise
                appearances = appearances + If(Or(home == team, away == team), 1, 0)
            # Team cannot appear more than twice in this period
            s.add(appearances <= 2)
    
    print(f"✅ Created solver with {len(s.assertions())} constraints")
    return s, T, weeks, periods

def print_solution(n, model, T, weeks, periods):
    """Print the solution in a nice format that's easy to read"""
    print(f"\n🏆 SOLUTION FOUND for n={n}")
    print("=" * 50)
    
    # Print schedule by weeks (easier to read than by periods)
    for w in range(weeks):
        print(f"Week {w+1}: ", end="")
        for p in range(periods):
            # Get the actual team numbers from Z3's solution
            home_val = model[T[p][w][0]].as_long()  # Convert Z3 value to Python integer
            away_val = model[T[p][w][1]].as_long()  # Convert Z3 value to Python integer
            print(f"{home_val}vs{away_val} ", end="")  # Print "Home vs Away" format
        print()  # New line after each week
    
    # Verify the solution meets all requirements
    print(f"\n🔍 Verifying solution...")
    
    # Check all games are unique (Constraint 2)
    all_pairs = set()
    for p in range(periods):
        for w in range(weeks):
            home_val = model[T[p][w][0]].as_long()
            away_val = model[T[p][w][1]].as_long()
            pair = (home_val, away_val)  # Store as tuple
            all_pairs.add(pair)
    
    expected_games = n * (n - 1) // 2  # Formula for number of games in round-robin
    print(f"Unique games: {len(all_pairs)} (should be {expected_games})")
    
    if len(all_pairs) == expected_games:
        print("✅ All games are unique!")
    else:
        print("❌ Problem: Duplicate games found!")

def test_with_all_constraints(n):
    """Test with ALL constraints - main demonstration function"""
    print("\n=== TESTING WITH ALL CONSTRAINTS ===")
    
    #n = 6  # Test with 6 teams (manageable size for demonstration)
    solver, T, weeks, periods = create_smt_solver(n)
    
    # Try to solve - this is where Z3 does the hard work!
    print(f"\n🔍 Solving...")
    result = solver.check()  # Z3 attempts to find a solution
    
    if result == sat:  # sat = satisfiable (solution exists)
        print("✅ SAT - Valid solution found!")
        model = solver.model()  # Extract the solution from Z3
        print_solution(n, model, T, weeks, periods)
        
        # Save to JSON format required by project
        save_to_json(n, model, T, weeks, periods)
        
    elif result == unsat:  # unsat = unsatisfiable (no solution exists)
        print("❌ UNSAT - No solution exists with current constraints")
    else:  # unknown = couldn't determine (timeout or other issue)
        print("⏰ UNKNOWN - Could not determine in time")

def save_to_json(n, model, T, weeks, periods):
    """Save solution in the required JSON format for project submission"""
    import json
    import os
    
    # Build the solution in the required format: list of weeks, each containing list of games
    solution = []
    for w in range(weeks):
        week_games = []
        for p in range(periods):
            home_val = model[T[p][w][0]].as_long()
            away_val = model[T[p][w][1]].as_long()
            week_games.append([home_val, away_val])  # Each game as [home, away]
        solution.append(week_games)  # Add week to schedule
    
    # Create the result object following project specifications
    result = {
        "z3_smt": {
            "time": 0,  # We'll add proper timing in experiments
            "optimal": True,  # For decision problem, any solution is "optimal"
            "obj": None,  # No objective function (this is satisfaction, not optimization)
            "sol": solution  # The actual schedule
        }
    }
    
    # Ensure the res/SMT folder exists
    os.makedirs("../../res/SMT", exist_ok=True)
    
    # Save to file - this creates the JSON file that the project checker will validate
    filename = f"../../res/SMT/{n}.json"
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)  # Pretty-print JSON for readability
    
    print(f"💾 Solution saved to: {filename}")
    
# Run the test when this file is executed directly
if __name__ == "__main__":
    # argument parsing from command line
    parser = argparse.ArgumentParser(description="SMT Aligned Model for Round-Robin Tournament Scheduling")
    parser.add_argument("--teams", type=int, default=6, help="Number of teams (n)")
    args = parser.parse_args()
    n = args.teams
    print(n)
    test_with_all_constraints(n)

#TODO output for each instance needs to be saved in res/SMT as n.json (check structure of json in project requirements)
#TODO add timing information
#TODO the output of the SMT solver needs to be formatted in the following way:
# [[[1, 2],[2, 4],[3, 5],[4, 6],[5, 7],[6, 9],[7, 8],[8, 12],[9, 10],[10, 11],[11, 14],[12, 13],[13, 14]],
#  [[6, 7],[9, 12],[10, 14],[9, 11],[3, 12],[2, 10],[6, 13],[4, 5],[1, 3],[1, 8],[2, 13],[7, 14],[8, 11]],
#  [[10, 12],[5, 11],[8, 13],[1, 13],[1, 10],[11, 12],[4, 9],[2, 14],[6, 14],[5, 9],[4, 8],[2, 3],[3, 7]],
#  [[3, 4],[1, 14],[4, 11],[5, 14],[6, 8],[3, 13],[2, 5],[10, 13],[7, 11],[6, 12],[1, 7],[8, 9],[2, 9]],
#  [[11, 13],[8, 10],[7, 12],[2, 12],[4, 14],[4, 7],[1, 11],[1, 6],[2, 8],[3, 14],[3, 9],[5, 10],[5, 6]],
#  [[9, 14],[3, 6],[2, 6],[7, 10],[2, 11],[8, 14],[3, 10],[7, 9],[5, 13],[4, 13],[5, 12],[1, 4],[1, 12]],
#  [[5, 8],[7, 13],[1, 9],[3, 8],[9, 13],[1, 5],[12, 14],[3, 11],[4, 12],[2, 7],[6, 10],[6, 11],[4, 10]]]
