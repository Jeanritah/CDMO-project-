# ------------------------------
# Symmetry-Breaking STS Model with Automatic Lex SB
# ------------------------------

# Parameters
param n integer;           # number of teams
param weeks integer;       # number of weeks
param periods integer;     # number of periods

# Sets (populated from Python)
set TEAMS;
set WEEKS;
set PERIODS;

# Binary decision variable: 1 if team i plays at home against team j in period p, week w
var x {WEEKS, PERIODS, TEAMS, TEAMS} binary;


# ------------------------------
# Basic Constraints
# ------------------------------

# [1] No team plays itself
s.t. no_self {w in WEEKS, p in PERIODS, i in TEAMS}:
    x[w,p,i,i] = 0;

# [2] One match per period per week
s.t. one_match_per_period {w in WEEKS, p in PERIODS}:
    sum {i in TEAMS, j in TEAMS} x[w,p,i,j] = 1;

# [3] One match per team per week
s.t. one_match_per_team_week {w in WEEKS, i in TEAMS}:
    sum {p in PERIODS, j in TEAMS} (x[w,p,i,j] + x[w,p,j,i]) = 1;

# [4] Each pair plays once
s.t. one_pair_match {i in TEAMS, j in TEAMS: i < j}:
    sum {w in WEEKS, p in PERIODS} (x[w,p,i,j] + x[w,p,j,i]) = 1;

# [5] Each team plays at most twice per period
s.t. max_two_per_period {i in TEAMS, p in PERIODS}:
    sum {w in WEEKS, j in TEAMS} (x[w,p,i,j] + x[w,p,j,i]) <= 2;

# ------------------------------
# Lexicographical symmetry breaking
# ------------------------------

# Assign a unique number to each match (i,j)
param game_value {i in TEAMS, j in TEAMS: i != j} = (i-1)*card(TEAMS) + j;

# Lexicographical ordering of weeks
subject to LexicographicalWeekOrdering {w in WEEKS: w < card(WEEKS)}:
    sum {p in PERIODS, i in TEAMS, j in TEAMS: i != j} game_value[i,j] * x[w,p,i,j]
    <=
    sum {p in PERIODS, i in TEAMS, j in TEAMS: i != j} game_value[i,j] * x[w+1,p,i,j];
    
# Sample objective : will be replaced by python incase objective is used or else by a dummy objective
maximize sample_obj: 0;