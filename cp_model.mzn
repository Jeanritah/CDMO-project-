%%writefile "cp_model.mzn"
include "alldifferent.mzn";

%% INSTANCE VARIABLES

int: n;
int: weeks = n - 1;
int: periods = n div 2;
int: slots = 2;

set of int: Weeks =  1..weeks;
set of int: Periods = 1..periods;

%% DECISION VARIABLES

array[Periods, Weeks, 1..slots] of var 1..n: game;

% [0] n is even
constraint n mod 2 = 0;

% [1] Every team plays with every other team only once
constraint alldifferent([game[p,w,1]*n + game[p,w,2] | p in Periods, w in Weeks]);
%faster till n<14, why? other alternatives?
% constraint
%     global_cardinality_low_up(
%         [game[p,w,1]*n + game[p,w,2] | p in Periods, w in Weeks],
%         [i | i in 1..n*n], % these are the n teams otherwise some teams play more than once
%         [0 | i in 1..n*n],
%         [1 | i in 1..n*n]   % 1 appearance x week
% );

% [2] Every team plays once a week
% constraint 
%   forall(w in Weeks)(
%     alldifferent([game[p,w,s] | p in 1..periods, s in 1..slots])
% );
constraint forall(w in Weeks) (
    global_cardinality(
        [game[p,w,s] | p in Periods, s in 1..slots],
        [i | i in 1..n], % these are the n teams otherwise some teams play more than once
        [1 | i in 1..n]   % 1 appearance x week
    )
);

% [3] Every team plays at most twice in the same period over the tournament 
constraint forall(p in Periods) (
    global_cardinality_low_up(
        [game[p,w,s] | w in Weeks, s in 1..slots],
        [i | i in 1..n], % these are the n teams otherwise some teams play more than once
        [1 | i in 1..n],  % lower bound: 0 appearances
        [2 | i in 1..n]   % upper bound: 2 appearances
    )
);

% [4] implied every game must be between different teams + symmetry breaking ordering of teams in a game
constraint forall(w in Weeks, p in Periods) (  game[p,w,1] < game[p,w,2]);

%% SYMMETRY BREAKING CONSTRAINTS

% [5]
constraint game[1, 1, 1] = 1;

% [6]
constraint forall(w in 2..weeks-1) (  game[1,w, 1] < game[1,w+1, 1]);

% SEARCHING STRATEGY 
% restart + randomization to optimiza search

% restart sequence type = luby
% base for geometric restart sequence 1.5
solve :: seq_search([
    int_search(
        [game[p,w,s] | w in Weeks, p in Periods, s in 1..slots],
         most_constrained,   % variable with smallest domain and most constraint impact
         indomain_random,    % value selection: random
         complete
    )
]) satisfy;

% OUTPUT FORMATTING

output ["["++
  join(",",[ 
    "[" ++ join(",", [ show([game[i,j,k] | k in 1..2]) | j in 1..weeks ]) ++ "]"
    | i in 1..periods
  ]) ++ "]"
];