# How to check your output

First save the output of your code in the folder `res/SMT` strictly following the `.json` format given by professor (you can also check mine)
Then run in the cmd the following command:

```bash
solution_checker.py res/SMT/
```

Install Z3
Option A: Using pip (Recommended for beginners)
bash
pip install z3-solver

from z3 import \*

def generate_sts_model_improved(n):
"""Improved SMT model for n teams"""

    s = Solver()
    weeks = n - 1
    periods = n // 2

    print(f"n={n}, weeks={weeks}, periods={periods}, total_games_needed={n*(n-1)//2}")

    # Create variables
    T_h = [[Int(f'T_h_{w}_{p}') for p in range(periods)] for w in range(weeks)]
    T_a = [[Int(f'T_a_{w}_{p}') for p in range(periods)] for w in range(weeks)]

    # Domain constraints
    for w in range(weeks):
        for p in range(periods):
            s.add(T_h[w][p] >= 0, T_h[w][p] < n)
            s.add(T_a[w][p] >= 0, T_a[w][p] < n)
            s.add(T_h[w][p] != T_a[w][p])

    # Constraint 1: Each team plays once per week
    for w in range(weeks):
        week_teams = []
        for p in range(periods):
            week_teams.append(T_h[w][p])
            week_teams.append(T_a[w][p])
        s.add(Distinct(week_teams))

    # Constraint 2: All pairs meet exactly once (more efficient)
    all_games = []
    for w in range(weeks):
        for p in range(periods):
            all_games.append((T_h[w][p], T_a[w][p]))

    # For n=4, we know all 6 games must appear exactly once
    if n == 4:
        required_games = [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3)]
        for game in required_games:
            game_appears = False
            for (h, a) in all_games:
                game_appears = Or(game_appears,
                                Or(And(h == game[0], a == game[1]),
                                   And(h == game[1], a == game[0])))
            s.add(game_appears)
    else:
        # For larger n, use the pairwise approach but optimized
        for i in range(len(all_games)):
            for j in range(i + 1, len(all_games)):
                h1, a1 = all_games[i]
                h2, a2 = all_games[j]
                # Two games cannot have the same pair of teams
                same_teams = And(Or(h1 == h2, h1 == a2), Or(a1 == h2, a1 == a2))
                s.add(Not(same_teams))

    # Constraint 3: Each team plays at most twice in each period
    for team in range(n):
        for p in range(periods):
            appearances = 0
            for w in range(weeks):
                appearances = appearances + If(Or(T_h[w][p] == team, T_a[w][p] == team), 1, 0)
            s.add(appearances <= 2)

    # Strong symmetry breaking
    if weeks > 0:
        # Fix first week completely
        first_week_teams = list(range(n))
        for p in range(periods):
            s.add(T_h[0][p] == first_week_teams[2*p])
            s.add(T_a[0][p] == first_week_teams[2*p + 1])

        # For first period, fix order to break more symmetry
        if periods > 0:
            s.add(T_h[0][0] < T_a[0][0])

    return s, T_h, T_a

def save_solution_to_json(n, model, T_h, T_a, approach_name="z3_basic"):
"""Save solution in the required JSON format"""
weeks = n - 1
periods = n // 2

    # Build the solution matrix
    solution = []
    for w in range(weeks):
        week_games = []
        for p in range(periods):
            home = model[T_h[w][p]].as_long()
            away = model[T_a[w][p]].as_long()
            week_games.append([home, away])
        solution.append(week_games)

    # Create JSON data
    import json
    import os

    result = {
        approach_name: {
            "time": 0,  # We'll add timing later
            "optimal": True,
            "obj": None,  # No optimization yet
            "sol": solution
        }
    }

    # Ensure res/SAT folder exists
    os.makedirs("../res/SAT", exist_ok=True)

    # Save to file
    filename = f"../res/SAT/{n}.json"
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"Solution saved to {filename}")
    return result

if **name** == "**main**":
print("=== Improved STS Solver ===")

    # Test specific instances
    test_cases = [4, 6]  # Start with these

    for n in test_cases:
        print(f"\n--- Solving n={n} ---")
        solver, T_h, T_a = generate_sts_model_improved(n)

        solver.set("timeout", 60000)  # 60 seconds

        import time
        start_time = time.time()
        result = solver.check()
        end_time = time.time()

        if result == sat:
            model = solver.model()
            print(f"✓ SOLUTION FOUND for n={n} in {end_time - start_time:.2f}s")

            # Print schedule
            weeks = n - 1
            periods = n // 2
            for w in range(weeks):
                print(f"Week {w+1}: ", end="")
                for p in range(periods):
                    home = model[T_h[w][p]].as_long()
                    away = model[T_a[w][p]].as_long()
                    print(f"{home}vs{away} ", end="")
                print()

            # Save to JSON
            save_solution_to_json(n, model, T_h, T_a)

        elif result == unknown:
            print(f"? TIMEOUT for n={n}")
        else:
            print(f"✗ NO SOLUTION for n={n}")

            # For n=4, let's check if it's actually impossible
            if n == 4:
                print("Checking if n=4 is fundamentally impossible...")
                # Relax the period constraint
                s_relaxed = Solver()
                weeks = 3
                periods = 2

                T_h_r = [[Int(f'T_h_r_{w}_{p}') for p in range(periods)] for w in range(weeks)]
                T_a_r = [[Int(f'T_a_r_{w}_{p}') for p in range(periods)] for w in range(weeks)]

                # Only basic constraints
                for w in range(weeks):
                    for p in range(periods):
                        s_relaxed.add(T_h_r[w][p] >= 0, T_h_r[w][p] < 4)
                        s_relaxed.add(T_a_r[w][p] >= 0, T_a_r[w][p] < 4)
                        s_relaxed.add(T_h_r[w][p] != T_a_r[w][p])

                for w in range(weeks):
                    week_teams = []
                    for p in range(periods):
                        week_teams.append(T_h_r[w][p])
                        week_teams.append(T_a_r[w][p])
                    s_relaxed.add(Distinct(week_teams))

                # All 6 games must appear
                all_games_r = []
                for w in range(weeks):
                    for p in range(periods):
                        all_games_r.append((T_h_r[w][p], T_a_r[w][p]))

                required_games = [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3)]
                for game in required_games:
                    game_appears = False
                    for (h, a) in all_games_r:
                        game_appears = Or(game_appears,
                                        Or(And(h == game[0], a == game[1]),
                                           And(h == game[1], a == game[0])))
                    s_relaxed.add(game_appears)

                if s_relaxed.check() == sat:
                    print("  ✓ n=4 is possible without period constraints")
                else:
                    print("  ✗ n=4 is impossible even without period constraints!")

this gives

n=4: Weekly constraints are satisfiable but full problem isn't - there might be a fundamental issue with n=4..........(idk why )

n=6: WORKS! We found a solution

n=8: Times out - this is expected as the problem gets harder

The n=4 Issue
For n=4 teams, we have:

3 weeks × 2 periods = 6 games

But we need exactly 6 unique games (4×3/2 = 6)

This means every possible game must be scheduled
