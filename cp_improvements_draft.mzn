% Use this editor as a MiniZinc scratch book

include "alldifferent.mzn";
include "globals.mzn";
include "lex_less.mzn";

int: n;
int: weeks = n - 1;
int: periods = n div 2;
int: slots = 2;

set of int: Weeks =  1..weeks;
set of int: Periods = 1..periods;

array[Periods, Weeks, 1..slots] of var 1..n: game;

% [1]
constraint alldifferent([game[p,w,1]*n + game[p,w,2] | p in Periods, w in Weeks]);
%slow down a bit the following version:
% constraint alldifferent([ min(game[p,w,1], game[p,w,2]) * n + max(game[p,w,1], game[p,w,2]) | p in Periods, w in Weeks ]);

% slows down a bit: sanity: total number of slots in a period = 2*weeks 
% constraint forall(p in Periods) ( sum(i in 1..n)( 0 ) + 0 = 0 
% % (no-op if not needed) 
% );


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

%Per teams total appearances NOT USEFUL
% constraint forall(t in 1..n) ( sum(p in Periods, w in Weeks)( bool2int(game[p,w,1] = t) + bool2int(game[p,w,2] = t) ) = n-1 );

% constraint NOT USEFUL
%   forall(w in Weeks, p in Periods) (
%     game[p,w,1] != game[p,w,2]
%   );

% Symmetry Breaking 1 (no improvement but also no conflict)
constraint game[1, 1, 1] = 1;

% Fix the ordering of team labels for the first week — Berger seed
constraint forall(p in Periods) ( game[p, 1, 1] = p /\ game[p, 1, 2] = n - p + 1 );

%NECESSARY
constraint forall(w in Weeks, p in Periods) ( game[p,w,1] < game[p,w,2]);

% % Symmetry Breaking 2 Fix the schedule of a particular team across weeks (anchor)
constraint forall(w in 2..weeks-1) (  game[1,w, 1] < game[1,w+1, 1]);

% Break symmetry between periods COMPATIBLE NO IMPROVEMENT
constraint forall(p in 1..(periods-1)) ( lex_less( [ game[p,w,1] | w in Weeks ] ++ [ game[p,w,2] | w in Weeks ], [ game[p+1,w,1] | w in Weeks ] ++ [ game[p+1,w,2] | w in Weeks ] ) );

% solve :: seq_search([
%     int_search(
%         [game[p,w,s] | w in Weeks, p in Periods, s in 1..slots],
%         most_constrained,   % variable with smallest domain and most constraint impact
%         indomain_split,     % splits domain to branch earlier
%         complete
%     )
% ]) satisfy;

solve :: seq_search([
    int_search(
        [game[p,w,s] | p in Periods, w in Weeks, s in 1..slots],
        dom_w_deg,          % dynamic weighted degree variable selection
        indomain_random,   % randomized value selection
        complete
    )
]) satisfy;

output [
  join(",\n ",[ 
    "[" ++ join(",", [ show([game[i,j,k] | k in 1..2]) | j in 1..weeks ]) ++ "]"
    | i in 1..periods
  ])
];
