%MY MODEL
include "alldifferent.mzn";

int: n;
int: weeks = n - 1;
int: periods = n div 2;
int: slots = 2;

set of int: Weeks =  1..weeks;
set of int: Periods = 1..periods;

array[Periods, Weeks, 1..slots] of var 1..n: game;

% [1]
constraint alldifferent([game[p,w,1]*n + game[p,w,2] | p in Periods, w in Weeks]);


% [2]
constraint 
  forall(w in Weeks)(
    alldifferent([game[p,w,s] | p in 1..periods, s in 1..slots])
);

% [3]
constraint forall(p in Periods) (
    global_cardinality_low_up(
        [game[p,w,s] | w in Weeks, s in 1..slots],
        [i | i in 1..n], % these are the n teams otherwise some teams play more than once
        [1 | i in 1..n],  % lower bound: 0 appearances
        [2 | i in 1..n]   % upper bound: 2 appearances
    )
);

% constraint
%   forall(w in Weeks, p in Periods) (
%     game[p,w,1] != game[p,w,2]
%   );

% Symmetry Breaking 1
constraint game[1, 1, 1] = 1;

% Symmetry Breaking 2
constraint forall(w in 2..weeks-1) (  game[1,w, 1] < game[1,w+1, 1]);

% Symmetry Breaking 3
constraint forall(w in Weeks, p in Periods) (  game[p,w,1] < game[p,w,2]);

solve :: seq_search([
    int_search(
        [game[p,w,s] | w in Weeks, p in Periods, s in 1..slots],
        most_constrained,   % variable with smallest domain and most constraint impact
        indomain_split,     % splits domain to branch earlier
        complete
    )
]) satisfy;

output [
  join(",\n ",[ 
    "[" ++ join(",", [ show([game[i,j,k] | k in 1..2]) | j in 1..weeks ]) ++ "]"
    | i in 1..periods
  ])
];