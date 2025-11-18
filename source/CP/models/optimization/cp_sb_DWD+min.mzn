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
array[Periods, Weeks, Slots] of var Teams: srr;
array[Weeks, Periods] of var Periods: perm;
array[Periods, Weeks, Slots] of var Teams: team;
array[Periods, Weeks] of var bool: swap;
array[Teams] of var 0..weeks: home_count;
var 0..weeks: max_deviation;

% CONSTRAINTS-------------------------------------------------------------------

% C1 n must be even
constraint n mod 2 = 0;

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

% C5
% C5.1 Fixing the set of teams in the first week
constraint
  forall(p in Periods) (
    if p = 1 then
      srr[p,1,1] = 1 /\
      srr[p,1,2] = 2
    else
      srr[p,1,1] = p + 1 /\
      srr[p,1,2] = n - p + 2
    endif
  );

% C5.2 Generating the subsequent weeks from the previous weeks 
constraint
  forall(w in 2..weeks, p in Periods) (
    srr[p,w,1] =
      ( if srr[p,w-1,1] = 1 then 1
        elseif srr[p,w-1,1] = n then 2
        else srr[p,w-1,1] + 1 endif ) /\
    srr[p,w,2] =
      ( if srr[p,w-1,2] = n then 2
        else srr[p,w-1,2] + 1 endif )
  );

% C6 Each period from srr[p,w,s] is mapped to a single period in team[p,w,s]
constraint
  forall(w in Weeks) (
    alldifferent([perm[w,p] | p in Periods])
  );

% C7 Break period symmetries
constraint
  forall(p in Periods) ( perm[1,p] = p );

% C8 Channelling constraints 
constraint
  forall(w in Weeks, p in Periods) (
    team[perm[w,p], w, 1] = (if swap[p,w] then srr[p,w,2] else srr[p,w,1] endif) /\
    team[perm[w,p], w, 2] = (if swap[p,w] then srr[p,w,1] else srr[p,w,2] endif)
  );

% C9 Home count for each team
constraint
  forall(i in Teams) (
    home_count[i] = sum(w in Weeks, p in Periods)( bool2int(team[p,w,1] = i) )
  );

% C10 Max_deviation
constraint max_deviation = max(i in Teams)(
  abs(2*home_count[i] - (n-1))
 );

solve :: int_search(
  [ team[p,w,s] | p in Periods, w in Weeks, s in Slots ] ++
  [ perm[w,p]     | w in Weeks, p in Periods ] ++
  [ srr[p,w,s]    | p in Periods, w in Weeks, s in Slots ], 
  dom_w_deg, indomain_min, complete)
minimize max_deviation;

output [
  "max_deviation=" ++ show(max_deviation) ++ "\n" ++
  "[" ++
    join(",", [
      "[" ++ join(",", [show([team[i,j,k] | k in Slots]) | j in Weeks]) ++ "]"
      | i in Periods
    ]) ++
  "]"
];