SMT Model Description - STS Problem
1. Instance Parameters
n: number of teams (even integer)
weeks = n - 1
periods = n // 2
slots = 2 (home/away)
2. Decision Variables
T[period][week][slot] ∈ [1, n]
3D array where T[p][w][0] = home team, T[p][w][1] = away team
3. Constraints
3.1 Domain Constraints
Teams between 1 and n
No self-play: home ≠ away
3.2 Weekly Constraints
All teams distinct per week
3.3 Unique Games
Each team pair plays exactly once
3.4 Period Constraints
Each team plays ≤2 times per period
4. Implementation
Solver: Z3 with Python
Search strategies tested: default, random phase, restarts
