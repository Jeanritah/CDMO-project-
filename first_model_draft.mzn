% FROM SLIDES
include "alldifferent.mzn";
include "globals.mzn";

int: n; % number of teams

set of int: Teams = 1..n;
set of int: Weeks = 1..n-1;
set of int: EWeeks = 1..n; % extended weeks for bye weeks when n is odd/dummy column
set of int: Periods = 1..n div 2;

% Decision variables
% For each slot: 2 variables represent the teamsand 1 variable represents the match are defined
% Domains: D(Tija)=[1,n-1] D(Tijh)=[0,n-2] D(Mij)=[1,n(n-1)/2]
array[Periods, EWeeks] of var 1..n-1: team_home;
array[Periods, EWeeks] of var 2..n: team_away;
array[Periods, EWeeks] of var (n+2)..(n*n): game;

% [0] n is even
% constraint n mod 2 = 0;

% [1] Each team plays every other team exactly once: 
% Alldiff constraints defined on game variables only for real weeks
constraint alldifferent([ game[p,w] | p in Periods, w in Weeks ]);

% [2] Each team plays exactly once (one game) per week:
% For each week w: Alldiff constraint defined on {Th_pw, p=1..Periods} U {Ta_pw, p=1..Periods}
constraint
  forall(w in EWeeks) (
    alldifferent([ team_home[p,w] | p in Periods ] ++ [ team_away[p,w] | p in Periods ])
  );

% [3] A team plays at most twice in the same period:
% With the Introduction of a dummy column to model also an odd number of weeks each team occurs exactly twice for each period
% TODO For each period p: global cardinality constraint defined on{Tpwh, w=1..7} U {Tpwa, w=1..7}every team t is taken 2 times
constraint forall(period in Periods, team in Teams) (
    count(
        [team_home[period, week] | week in EWeeks] ++ 
        [team_away[period, week] | week in EWeeks],
        team
    ) = 2
);
% constraint forall(period in Periods) (
%   global_cardinality(
%     [team_home[period, week] | week in EWeeks] ++
%     [team_away[period, week] | week in EWeeks],
%     [team | team in Teams],
%     [2 | team in Teams]
%   )
% );

% [4] No self matches:
% !!REDUNDANT!!
% constraint
%   forall(p in Periods, w in EWeeks) (
%     team_home[p,w] != team_away[p,w]
%   );

% [5] All games in a week must be different:
% !!REDUNDANT!!
% constraint
%   forall(w in Weeks) (
%     alldifferent([ game[p,w] | p in Periods ])
%   );

% [6] Link game <-> teams
% For each slot the two T variables and the M variable must be linked together; 
% We add a ternary constraint defined on the two Tvariables and the M variable; 
constraint
  forall(p in Periods, w in EWeeks) (
     game[p,w] = team_home[p,w]*n + team_away[p,w]
   );

%%% OTHER CONSTRAINTS

% [7] Each week has exactly n/2 games:
% TODO IMPLEMENT if not redundant

% [8] Each period features distinct teams within the same week
% TODO IMPLEMENT if not redundant

%%% SYMMETRY BREAKING CONSTRAINTS

% [9] Fix the first week to a canonical order:
% !!NOT HELPFUL!!
% Th[g,1] = g, \quad Ta[g,1] = n - g + 1, \quad \forall g \in G
% constraint forall(p in Periods)(
%   team_home[p, 1] == p /\ team_away[p, 1] == n-p+1
% );

% [10] Fix the home/away pattern of one team
% Break symmetry: 0 vs 1 is the first game of the dummy column
% constraint
%   team_home[1,n] = 1; 
% %   /\ team_away[1,n] = 2;
  
% % Symmetry Breaking 2
constraint forall(w in Weeks) (game[1,w] < game[1,w+1]);

% [11] Order constraint Tijh < Tija
constraint
  forall(p in Periods, w in EWeeks) (
    team_home[p,w] < team_away[p,w]
  );

% This is not a symmetry breaking constraint
% [12] Each team occurs exactly once in the dummy column
constraint
  alldifferent([ team_home[p,n] | p in Periods ] ++ [ team_away[p,n] | p in Periods ]);

solve
:: seq_search([
% Phase 1: search the real-week variables first (games and team slots in weeks 1..n-1)
int_search(
[ game[p,w] | w in Weeks, p in Periods ] ++
[ team_home[p,w] | w in Weeks, p in Periods ] ++
[ team_away[p,w] | w in Weeks, p in Periods ],
first_fail, % choose most constrained slot
indomain_min, % try smallest team numbers first
complete
),


% Phase 2: search the dummy-week variables (week n) to satisfy period constraints
int_search(
[ team_home[p,n] | p in Periods ] ++ [ team_away[p,n] | p in Periods ],
first_fail,
indomain_min,
complete
)
]) satisfy;

% solve satisfy;

output [
  join(",\n", [ 
    "[" ++ join(",", [ "[" ++ show(team_home[p,w]) ++ "," ++ show(team_away[p,w]) ++ "]" | w in Weeks ]) ++ "]"
    | p in Periods
  ])
];