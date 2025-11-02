include "alldifferent.mzn";
include "globals.mzn";
include "lex_lesseq.mzn";

int: n; % number of teams
set of int: Teams = 1..n;
set of int: Weeks = 1..n-1;
set of int: EWeeks = 1..n; % extended weeks for bye weeks when n is odd/dummy column
set of int: Periods = 1..n div 2;

constraint n mod 2 = 0; % n is even

% helper: rotated position (circle method)
function int: rot(int: w, int: pos) =
  if pos = 1 then 1
  else ((pos-2 + (w-1)) mod (n-1)) + 2
  endif;

% round-robin mapping: for each week w and period p, give the game id = f*n + s with f<s
array[Weeks, Periods] of int: roundGame = array2d(Weeks, Periods,
  [ let { int: a = rot(w,p), int: b = rot(w, n+1-p),
         int: f = if a < b then a else b endif,
         int: s = if a < b then b else a endif }
    in f * n + s
    | w in Weeks, p in Periods
  ]);

% domain of games allowed in each real week
array[Weeks] of set of int: domainW = [ { roundGame[w,p] | p in Periods } | w in Weeks ];

% Decision variables
array[Periods, EWeeks] of var 1..n-1: team_home;
array[Periods, EWeeks] of var 2..n:   team_away;
array[Periods, EWeeks] of var (n+2)..(n*n): game;

% Ensure team_home < team_away
constraint forall(p in Periods, w in EWeeks) ( team_home[p,w] < team_away[p,w] );

% Link game <-> teams
constraint forall(p in Periods, w in EWeeks) (
  team_home[p,w] = game[p,w] div n /\
  team_away[p,w] = game[p,w] - team_home[p,w] * n
);

% Restrict games in real weeks to the round-robin set for that week
constraint forall(p in Periods, w in Weeks) (
  game[p,w] in domainW
);

% every two teams play each other exactly once (only real weeks)
constraint alldifferent([ game[p,w] | p in Periods, w in Weeks ]);

% every team plays one game in each week (including dummy column)
constraint
  forall(w in EWeeks) (
    alldifferent([ team_home[p,w] | p in Periods ] ++ [ team_away[p,w] | p in Periods ])
  );

% each team occurs exactly twice in each period (with dummy column)
constraint forall(period in Periods, team in Teams) (
    count(
        [team_home[period, week] | week in EWeeks] ++ 
        [team_away[period, week] | week in EWeeks],
        team
    ) = 2
);

% each team occurs exactly once in the dummy column
constraint
  alldifferent([ team_home[p,n] | p in Periods ] ++ [ team_away[p,n] | p in Periods ]);

% Break symmetry: fix one match in dummy column
constraint team_home[1,n] = 1 /\ team_away[1,n] = 2;

solve
:: seq_search([
int_search(
[ game[p,w] | w in Weeks, p in Periods ] ++
[ team_home[p,w] | w in Weeks, p in Periods ] ++
[ team_away[p,w] | w in Weeks, p in Periods ],
first_fail,
indomain_min,
complete
),
int_search(
[ team_home[p,n] | p in Periods ] ++ [ team_away[p,n] | p in Periods ],
first_fail,
indomain_min,
complete
)
]) satisfy;

output [
  join(",\n", [ 
    "[" ++ join(",", [ "[" ++ show(team_home[p,w]) ++ "," ++ show(team_away[p,w]) ++ "]" | w in Weeks ]) ++ "]"
    | p in Periods
  ])
];
