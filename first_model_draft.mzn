include "alldifferent.mzn";

int: n;
int: weeks = n - 1;
int: periods = n div 2;
int: slots = 2;

array[1..weeks, 1..periods, 1..slots] of var 1..n: game;

% 1
constraint
  forall(i, j in 1..n where i < j) (
    sum(w in 1..weeks, p in 1..periods) (
      bool2int( (game[w,p,1] == i /\ game[w,p,2] == j) \/
                (game[w,p,1] == j /\ game[w,p,2] == i) )
    ) == 1
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
        [i | i in 0..n-1],
        [0 | i in 0..n-1],  % lower bound: 0 appearances
        [2 | i in 0..n-1]   % upper bound: 2 appearances
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
