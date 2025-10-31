% Improve translation from paper P. Van Hentenryck, L. Michel, L. Perron, and J.-C. Régin, ‘Constraint Programming in OPL’, in Principles and Practice of Declarative Programming, G. Nadathur, Ed., Berlin, Heidelberg: Springer, 1999, pp. 98–116. doi: 10.1007/10704567_6.

include "alldifferent.mzn";
int: nbTeams;

set of int: Teams   = 1..nbTeams;
set of int: Weeks   = 1..nbTeams - 1;
set of int: EWeeks  = 1..nbTeams;
set of int: Periods = 1..nbTeams div 2;
set of int: Games   = 1..(nbTeams * nbTeams);

enum Slots = { home, away };

% Constants for distribute/global_cardinality
array[Teams] of int: occur  = [2 | t in Teams];
array[Teams] of int: values = [t | t in Teams];

% Decision variables
array[Periods, EWeeks, Slots] of var Teams: team;
array[Periods, Weeks] of var Games: game;

% Constraints
constraint
  forall(w in EWeeks) (
    alldifferent([ team[p,w,s] | p in Periods, s in Slots ])
  );

constraint
  alldifferent([ game[p,w] | p in Periods, w in Weeks ]);

constraint
  forall(p in Periods) (
    global_cardinality(
      [ team[p,w,s] | w in EWeeks, s in Slots ],
      values,
      occur
    )
  );

constraint
  forall(p in Periods, w in Weeks) (
    team[p,w,home] < team[p,w,away] /\
    game[p,w] = (team[p,w,home] - 1) * nbTeams + team[p,w,away]
  );

solve satisfy;

output [
  join(",\n ",[ 
    "[" ++ join(",", ["[\(team[p,w,home]),\(team[p,w,away])]" | w in Weeks]) ++ "]"
    | p in Periods
  ])
];