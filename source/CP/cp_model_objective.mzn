% Fixed transition-rule implementation (use 'elseif', not 'else if')
%TODO: adjust code, and check n limit or best search
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

% ------------------------------
% Orientation (home/away flip) per match
% swap[p,w] = true means flip the order of the two teams for that match
% ------------------------------
array[Periods, Weeks] of var bool: swap;

% game[period,week,1..2] is the actual schedule after placing (and optionally flipping) pairs
array[Periods, Weeks, 1..2] of var 1..n: game;

constraint
  forall(w in Weeks, p in Periods) (
    game[perm[w,p], w, 1] = (if swap[p,w] then pairings[p,w,2] else pairings[p,w,1] endif) /\
    game[perm[w,p], w, 2] = (if swap[p,w] then pairings[p,w,1] else pairings[p,w,2] endif)
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
% Optional optimization: balance home vs away per team
% home = times team appears in position 1 across all weeks/periods
% away = weeks - home (since each team plays exactly once per week)
% deviation[i] = |home[i] - away[i]| = |2*home[i] - weeks|
% Objective: minimize total imbalance = sum_i deviation[i]
% ------------------------------
array[1..n] of var 0..weeks: home_count;
array[1..n] of var 0..weeks: deviation;

constraint
  forall(i in 1..n) (
    home_count[i] = sum(w in Weeks, p in Periods)( bool2int(game[p,w,1] = i) )
  );

constraint
  forall(i in 1..n) (
    deviation[i] = abs(2 * home_count[i] - weeks)
  );

var 0..n*weeks: total_imbalance = sum(i in 1..n)(deviation[i]);

% ------------------------------
% Search: include swap vars so the objective can improve early
% You can also remove this 'solve :: seq_search(...)' and let Chuffed free-search.
% ------------------------------
% solve :: seq_search(
%   [
%     int_search([ bool2int(swap[p,w]) | p in Periods ], first_fail, indomain_min),
%     int_search([ perm[w,p] | p in Periods ], first_fail, indomain_min)
%   | w in Weeks ]
% ) minimize total_imbalance;
solve minimize total_imbalance;

output [
  "total_imbalance=" ++ show(total_imbalance) ++ "\n" ++
  "[" ++
    join(",\n", [
      "[" ++ join(",", [show([game[i,j,k] | k in 1..2]) | j in Weeks]) ++ "]"
      | i in Periods
    ]) ++
  "]"
];

% best model, works with chuffed until n <= 16
% config random seed = 42, restart type luby

% Notes:
% - To use as a decision problem (no optimization), change the 'solve ... minimize total_imbalance;'
%   line to 'solve :: seq_search(...) satisfy;'
% - Alternatively, to minimize the worst (max) imbalance, you can replace the objective with:
%     var 0..weeks: max_deviation = max(i in 1..n)(deviation[i]);
%     solve :: seq_search(...) minimize max_deviation;