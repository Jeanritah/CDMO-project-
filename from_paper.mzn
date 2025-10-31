%FROM PAPER: P. Van Hentenryck, ‘A preview of OPL’, Department of Computing Science and Engineering, UCL, Belgium, 2000.

include "alldifferent.mzn";
include "distribute.mzn";

int: n;
int: nbTeams = n;
set of int: Teams  = 1..nbTeams;
set of int: Weeks  = 1..nbTeams-1;
set of int: EWeeks = 1..nbTeams;
set of int: Periods = 1..nbTeams div 2;
set of int: Games  = 1..nbTeams*nbTeams;

enum Slots = {home, away};

array[Teams] of int: occur = [2 | t in Teams];
array[Teams] of int: values = [t | t in Teams];

array[Periods, EWeeks, Slots] of var Teams: team;
array[Periods, Weeks] of var Games: game;

predicate link(var int: f, var int: s, var int: g) =
    g = (f-1) * nbTeams + s;

constraint
    forall(w in EWeeks) (
        alldifferent([team[p,w,s] | p in Periods, s in Slots])
    );

constraint
    alldifferent([game[p,w] | p in Periods, w in Weeks]);

constraint
    forall(p in Periods) (
        distribute(occur, values, [team[p,w,s] | w in EWeeks, s in Slots])
    );

constraint
    forall(p in Periods, w in Weeks) (
        link(team[p,w,home], team[p,w,away], game[p,w])
    );

solve :: int_search(
    [game[p,w] | p in Periods, w in Weeks],  % the variables to branch on
    first_fail,   % variable selection: pick the one with smallest domain
    indomain_min, % value selection: try smallest value first
    complete      % search strategy: complete backtracking
) satisfy;

output [
  join(",\n ",[ 
    "[" ++ join(",", ["[\(team[p,w,home]),\(team[p,w,away])]" | w in Weeks]) ++ "]"
    | p in Periods
  ])
];

%FROM PAPER: P. Van Hentenryck, ‘A preview of OPL’, Department of Computing Science and Engineering, UCL, Belgium, 2000.
