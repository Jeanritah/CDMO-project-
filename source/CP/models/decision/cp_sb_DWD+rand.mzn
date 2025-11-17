% indomain_rand is not supported by chuffed
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
array[Weeks, Periods] of var 1..periods: perm;
array[Periods, Weeks, Slots] of var Teams: team;

% CONSTRAINTS-------------------------------------------------------------------

% C1 n must be even
constraint n mod 2 = 0;

% C2
%TODO or redundant? or just in the basic model?

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

% C5 Fixed round-robin schedule
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

% ------------------------------
% Permutation of period slots each week
% ------------------------------
% C6
constraint
  forall(w in Weeks) (
    alldifferent([perm[w,p] | p in Periods])
  );

% C7
constraint
  forall(p in Periods) ( perm[1,p] = p );

% C8
constraint
  forall(w in Weeks, p in Periods) (
    team[perm[w,p], w, 1] = srr[p,w,1] /\
    team[perm[w,p], w, 2] = srr[p,w,2]
  );


solve :: seq_search(
  [ int_search([perm[w,p] | p in Periods], 
  dom_w_deg, 
  indomain_random,
  complete) 
  | w in Weeks ]
) ::restart_luby(100)
satisfy;

output [
  "[" ++
    join(",\n", [
      "[" ++ join(",", [show([team[i,j,k] | k in Slots]) | j in Weeks]) ++ "]"
      | i in Periods
    ]) ++
  "]"
];