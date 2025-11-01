% The problem
% • n teams and n-1 weeks and n/2 periods
% • every two teams play each other exactly once
% • every team plays one game in each week
% • no team plays more than twice in the same period
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
array[Periods, EWeeks] of var 1..(n*(n-1) div 2): game;

% Constraint Tijh < Tija
constraint
  forall(p in Periods, w in EWeeks) (
    team_home[p,w] < team_away[p,w]
  );

% every two teams play each other exactly once: 
% Alldiff constraints defined on M variables

% constraint forall(w in Weeks) (
%   alldifferent([ game[p,w] | p in Periods ])
% );
% constraint forall(p in Periods) (
%   alldifferent([ game[p,w] | w in Weeks ])
% );

constraint alldifferent([ game[p,w] | p in Periods, w in Weeks ]);

% every team plays one game in each week: 
%For each week w:Alldiff constraint defined on {Tpwh, p=1..4} U {Tpwa, p=1..4}
constraint
  forall(w in EWeeks) (
    alldifferent([ team_home[p,w] | p in Periods ] ++ [ team_away[p,w] | p in Periods ])
  );

% no team plays more than twice in the same period: 
% For each period p: global cardinality constraint defined on{Tpwh, w=1..7} U {Tpwa, w=1..7}every team t is taken at most 2
% With the Introduction of a dummy column to model bye weeks when n is odd each team occurs exactly twice for each period
constraint forall(period in Periods, team in Teams) (
    count(
        [team_home[period, week] | week in EWeeks] ++ 
        [team_away[period, week] | week in EWeeks],
        team
    ) = 2
);

% For each slot the two T variables and the M variable must be linked together; 
%example:M12 = game T12h vs T12a
%For each slot we add Cij a ternary constraint defined on the two Tvariables and the M variable; 
%example:C12 defined on {T12h,T12a,M12}
% Cij are defined by the list of allowed tuples:for n=4: {(0,1,1),(0,2,2),(0,3,3),(1,2,4),(1,3,5),(2,3,6)}(1,2,4) means game 1 vs 2 is the game number 4
% All these constraints have the same list of allowed tuples

% array[1..(n*(n-1) div 2), 1..3] of int: game_table = 
%   array2d(1..(n*(n-1) div 2), 1..3, 
%     [if k == 1 then i 
%      elseif k == 2 then j 
%      else (i-1)*(2*n-i) div 2 + (j-i)
%      endif
%      | g in 1..(n*(n-1) div 2), 
%        i in 1..n-1, j in i+1..n, k in 1..3 
%        where g == (i-1)*(2*n-i) div 2 + (j-i)
%     ]);

% constraint
%   forall(p in Periods, w in EWeeks) (
%     table([team_home[p,w], team_away[p,w], game[p,w]], game_table)
%   );

constraint
  forall(p in Periods, w in Weeks) (  % Changed from EWeeks to Weeks
    game[p,w] = ((team_home[p,w]-1)*(2*n-team_home[p,w])) div 2 + 
                (team_away[p,w] - team_home[p,w])
  );

%each team occurs exactly once in the dummy column
constraint
  alldifferent([ team_home[p,n] | p in Periods ] ++ [ team_away[p,n] | p in Periods ]);

%TODO Break symmetries: 0 vs w appears in week w

% Break symmetry: 0 vs 1 is the first game of the dummy column
constraint
  team_home[1,n] = 1 /\ team_away[1,n] = 2;

% 1. Find a round-robin. 
%Define all the gamesfor each column (except for the dummy)
%- Alldiff constraint on M is satisfied
%- Alldiff constraint for each week is satisfied
% 2. set the games in order to satisfy constraints on periods. 
%If no solution go to 1)

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
])


satisfy;

output [
  join(",\n", [ 
    "[" ++ join(",", [ "[" ++ show(team_home[p,w]) ++ "," ++ show(team_away[p,w]) ++ "]" | w in Weeks ]) ++ "]"
    | p in Periods
  ])
];