include "alldifferent.mzn";

int: n;
int: weeks = n - 1;
int: periods = n div 2;
int: slots = 2;

array[1..weeks, 1..periods, 1..slots] of var 1..n: game;

% [1]
constraint forall(i in 1..n) (
    global_cardinality_closed(
        [game[w,p,s] | w in 1..weeks, p in 1..periods, s in 1..slots],
        1..n,
        [weeks | _ in 1..n]  % Each team plays exactly 'weeks' times
    )
);

% [2]
constraint 
  forall(w in 1..weeks)(
    alldifferent([game[w,p,s] | p in 1..periods, s in 1..slots])
);

% [3]
constraint forall(p in 1..periods) (
    global_cardinality_low_up(
        [game[w,p,s] | w in 1..weeks, s in 1..2],
        [i | i in 1..n], % these are the n teams otherwise some teams play more than once
        [1 | i in 1..n],  % lower bound: 0 appearances
        [2 | i in 1..n]   % upper bound: 2 appearances
    )
);

constraint
  forall(w in 1..weeks, p in 1..periods) (
    game[w,p,1] != game[w,p,2]
  );

% Symmetry Breaking 1
constraint game[1, 1, 1] == 1;

% Symmetry Breaking 2
constraint forall(w in 1..weeks-1) (  game[w, 1, 1] < game[w+1, 1, 1]);

% Symmetry Breaking 3
constraint forall(w in 1..weeks, p in 1..periods) (  game[w,p,1] < game[w,p,2]);

solve satisfy;

output [
  join(",\n ",[ 
    "[" ++ join(",", [ show([game[i,j,k] | k in 1..2]) | i in 1..weeks ]) ++ "]"
    | j in 1..periods
  ])
];
