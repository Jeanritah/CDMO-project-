% Fixed transition-rule implementation (use 'elseif', not 'else if')

include "globals.mzn";

int: n;
constraint n mod 2 = 0;

int: weeks = n - 1;
int: periods = n div 2;

set of int: Weeks = 1..weeks;
set of int: Periods = 1..periods;

array[Periods, Weeks, 1..2] of var 1..n: pairings;

% week 1 seed (example, keep your seed or adapt)
constraint
  forall(p in Periods) (
    if p = 1 then
      pairings[p,1,1] = 1 /\
      pairings[p,1,2] = 2
    else
      pairings[p,1,1] = p + 1 /\
      pairings[p,1,2] = n - p + 2
    endif
  );

% ------------------------------
% Transition rule to compute subsequent weeks:
% f' = 1 if f=1; 2 if f=n; else f+1.
% s' = 2 if s=n; else s+1.
% ------------------------------
constraint
  forall(w in 2..weeks, p in Periods) (
    pairings[p,w,1] =
      ( if pairings[p,w-1,1] = 1 then 1
        elseif pairings[p,w-1,1] = n then 2
        else pairings[p,w-1,1] + 1 endif ) /\
    pairings[p,w,2] =
      ( if pairings[p,w-1,2] = n then 2
        else pairings[p,w-1,2] + 1 endif )
  );

% ------------------------------
% Permutation of period slots each week
% ------------------------------
array[Weeks, Periods] of var 1..periods: perm;

constraint
  forall(w in Weeks) (
    alldifferent([perm[w,p] | p in Periods])
  );

% Anchor week 1 permutation to identity
constraint
  forall(p in Periods) ( perm[1,p] = p );

% game[period,week,1..2] is the actual schedule after placing pairs into permuted slots
array[Periods, Weeks, 1..2] of var 1..n: game;

constraint
  forall(w in Weeks, p in Periods) (
    game[perm[w,p], w, 1] = pairings[p,w,1] /\
    game[perm[w,p], w, 2] = pairings[p,w,2]
  );

% ------------------------------
% Required constraints:
% 1) Each team plays exactly once per week.
% 2) Each team plays at most twice per period across all weeks.
% ------------------------------
constraint
  forall(w in Weeks) (
    alldifferent([ game[p,w,s] | p in Periods, s in 1..2 ])
  );

constraint forall(p in Periods) (
    global_cardinality_low_up(
        [game[p,w,s] | w in Weeks, s in 1..2],
        [i | i in 1..n],
        [0 | i in 1..n],
        [2 | i in 1..n]
    )
);


% ------------------------------
% Search: search only the perm variables, week-by-week
% ------------------------------
solve :: seq_search(
  [ int_search([perm[w,p] | p in Periods], first_fail, indomain_min) | w in Weeks ]
) satisfy;

output [
  "[" ++
    join(",\n", [
      "[" ++ join(",", [show([game[i,j,k] | k in 1..2]) | j in Weeks]) ++ "]"
      | i in Periods
    ]) ++
  "]"
];

%best model, works with chuffed until n <=16
% config random seed =42, restart type luby