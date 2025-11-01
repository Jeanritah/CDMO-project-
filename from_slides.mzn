include "alldifferent.mzn";
include "globals.mzn";
include "lex_lesseq.mzn";

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
array[Periods, EWeeks] of var 1..((n-1)*10)+n: game;

constraint n mod 2 = 0; %n is even;

% Constraint Tijh < Tija
constraint
  forall(p in Periods, w in EWeeks) (
    team_home[p,w] < team_away[p,w]
  );

% every two teams play each other exactly once: 
% Alldiff constraints defined on M variables
constraint alldifferent([ game[p,w] | p in Periods, w in Weeks ]);
%this way alldifferent is applied also on the diagonals

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
constraint
  forall(p in Periods, w in EWeeks) (
     game[p,w] = team_home[p,w]*10 + team_away[p,w]
   );

%each team occurs exactly once in the dummy column
constraint
  alldifferent([ team_home[p,n] | p in Periods ] ++ [ team_away[p,n] | p in Periods ]);

%TODO Break more symmetries?

% --- fixed lexicographic symmetry-breaking (all comprehensions have same shape) ---
% Compare the flattened game array with week-order reversed
constraint lex_lesseq(
  [ game[p,w] | p in Periods, w in EWeeks ],
  [ game[p,w] | p in Periods, w in reverse(EWeeks) ]
);

% Compare the flattened game array with period-order reversed
constraint lex_lesseq(
  [ game[p,w] | p in Periods, w in EWeeks ],
  [ game[p,w] | p in reverse(Periods), w in EWeeks ]
);

% Compare the flattened game array with both period and week order reversed
constraint lex_lesseq(
  [ game[p,w] | p in Periods, w in EWeeks ],
  [ game[p,w] | p in reverse(Periods), w in reverse(EWeeks) ]
);


% Break symmetry: 0 vs 1 is the first game of the dummy column
% constraint
%   team_home[1,n] = 1 /\ team_away[1,n] = 2;
% I should break symmetries also on the game table which should be easier

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

%solve satisfy;

output [
  join(",\n", [ 
    "[" ++ join(",", [ "[" ++ show(team_home[p,w]) ++ "," ++ show(team_away[p,w]) ++ "]" | w in Weeks ]) ++ "]"
    | p in Periods
  ])
];