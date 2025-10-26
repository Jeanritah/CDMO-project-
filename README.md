include "globals.mzn";

int: n;
int: weeks = n - 1;
int: periods = n div 2;
int: slots = 2;

array[1..weeks, 1..periods, 1..slots] of var 1..n: game;

% 1. Weekly constraint
constraint forall(w in 1..weeks) (
    all_different([game[w,p,s] | p in 1..periods, s in 1..slots])
);

% 2. No self-play
constraint forall(w in 1..weeks, p in 1..periods) (
    game[w,p,1] != game[w,p,2]
);

% 3. Simple symmetry breaking
constraint game[1,1,1] = 1;
constraint game[1,1,2] = 2;

% 4. Home team < Away team
constraint forall(w in 1..weeks, p in 1..periods) (
    game[w,p,1] < game[w,p,2]
);

% 5. PERIOD CONSTRAINT (NEW)
constraint forall(i in 1..n, p in 1..periods) (
    sum(w in 1..weeks, s in 1..slots) ( bool2int(game[w,p,s] == i) ) <= 2
);

% Round-robin constraint using match IDs
array[1..weeks, 1..periods] of var 1..(n*(n-1) div 2): match_id;

constraint all_different(match_id);

constraint forall(w in 1..weeks, p in 1..periods) (
    % Convert team pair to unique match ID
    match_id[w,p] = (game[w,p,1]-1) * (2*n - game[w,p,1]) div 2 + 
                    (game[w,p,2] - game[w,p,1])
);

solve satisfy;
