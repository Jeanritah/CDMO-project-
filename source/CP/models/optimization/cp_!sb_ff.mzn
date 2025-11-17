include "globals.mzn";

% INSTANCE VARIABLES------------------------------------------------------------
int: n;

int: weeks = n - 1;
int: periods = n div 2;
int: slots = 2;

set of int: Teams = 1..n;
set of int: Weeks = 1..weeks;
set of int: Periods = 1..periods;
set of int: Slots = 1..slots;

% DECISION VARIABLES------------------------------------------------------------
array[Periods, Weeks, Slots] of var Teams: team;
array[Teams] of var 0..weeks: home_count;
var 0..weeks: max_deviation;

% CONSTRAINTS-------------------------------------------------------------------

% C1 n must be even
constraint n mod 2 = 0;

% C2 
constraint alldifferent([team[p,w,1]*n + team[p,w,2] | p in Periods, w in Weeks]);
constraint forall(p in Periods, w in Weeks) (team[p,w,1] < team[p,w,2]);

% C3 every team plays once a week 
constraint
  forall(w in Weeks) (
    alldifferent([ team[p,w,s] | p in Periods, s in Slots ])
  );

% C4 every team plays at most twice in the same period over the tournament
constraint forall(p in Periods) (
    global_cardinality_low_up(
        [team[p,w,s] | w in Weeks, s in Slots],
        [i | i in Teams],
        [0 | i in Teams],
        [2 | i in Teams]
    )
);

% C10 Max_deviation
constraint max_deviation = max(i in Teams)(
  abs(2*home_count[i] - (n-1))
 );

solve :: int_search(
  [ team[p,w,s] | p in Periods, w in Weeks, s in Slots ],
  first_fail, indomain_min, complete)
minimize max_deviation;

output [
  "max_deviation=" ++ show(max_deviation) ++ "\n" ++
  "[" ++
    join(",\n", [
      "[" ++ join(",", [show([team[i,j,k] | k in Slots]) | j in Weeks]) ++ "]"
      | i in Periods
    ]) ++
  "]"
];