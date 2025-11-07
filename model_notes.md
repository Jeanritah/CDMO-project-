## ⚙️ PARAMETERS AND SETUP

Let:

* $n$: number of teams (even, $n \ge 6 $)
* $W = n - 1$: number of weeks
* $P = n / 2$: number of periods per week
  (each period corresponds to one simultaneous game)
* $T = {1, 2, ..., n}$: set of teams
* $G = {1, 2, ..., P}$: set of periods
* $K = {1, 2, ..., W}$: set of weeks

Each **game** is represented by a pair (home, away) between two distinct teams.

We will also use a **dummy column** (week $W + 1$) for modeling generalization to odd $n$ — when $n$ is odd, the dummy team “sits out”.

---

# 🧩 MODEL 1 — Decision Problem

### 🔹 Decision Variables

* $Th[g, k] \in T$: the team playing **home** in period $g$ of week $k$
* $Ta[g, k] \in T$: the team playing **away** in period $g$ of week $k$
* $Game[g, k] = (Th[g, k], Ta[g, k])$: represents the match pairing

---

### 🔹 Constraints

#### 1. Each team plays every other team exactly once

$\forall i,j \in T, i \ne j: \text{match}(i,j) \text{ occurs exactly once over all } (g,k)$
Formally:
$\sum_{g=1}^{P}\sum_{k=1}^{W} [Th[g,k] = i \land Ta[g,k] = j \lor Th[g,k] = j \land Ta[g,k] = i] = 1$

---

#### 2. Each team plays exactly once per week

$\forall i \in T, \forall k \in K:
\sum_{g=1}^{P} ([Th[g,k] = i] + [Ta[g,k] = i]) = 1$

---

#### 3. A team plays at most twice in the same period

$\forall i \in T, \forall g \in G:
\sum_{k=1}^{W} ([Th[g,k] = i] + [Ta[g,k] = i]) \le 2$

---

#### 4. Home and away distinction (no self-matches)

$\forall g,k: Th[g,k] \ne Ta[g,k]$

---

#### 5. All games in a week are distinct

$\forall g_1 \ne g_2, \forall k: {Th[g_1,k], Ta[g_1,k]} \ne {Th[g_2,k], Ta[g_2,k]}$

---

#### 6. Link game and teams variables



### 🔹 Implied Constraints

(These help prune search but do not alter feasibility)

* **Each week has exactly ( n/2 ) games**, i.e. all teams appear once.
* **Each period features distinct teams** within the same week.
* The total number of matches = ( n(n-1)/2 ).

---

### 🔹 Symmetry Breaking Constraints

To reduce equivalent mirrored solutions:

9 **Fix the first week** to a canonical order:
$Th[g,1] = g, \quad Ta[g,1] = n - g + 1, \quad \forall g \in G$
(or use any fixed rotation schedule)

10 **Fix the home/away pattern of one team** (e.g., team 1 always plays home first week).

11 **Order constraint**:
$Th[1,1] < Ta[1,1]$
to eliminate equivalent relabelings.

---

✅ **This model finds a feasible tournament satisfying all conditions**.

---

# 🧭 MODEL 2 — Optimization Version (Fairness / Home-Away Balance)

We extend the previous model by introducing **optimization** for home/away balance.

---

### 🔹 Additional Decision Variables

* $H[i] = \sum_{g,k} [Th[g,k] = i]$: number of **home** games for team ( i )
* $A[i] = \sum_{g,k} [Ta[g,k] = i]$: number of **away** games for team ( i )
* $D[i] = |H[i] - A[i]|$: absolute difference (imbalance)

---

### 🔹 Objective Function

**Minimize imbalance across all teams:**

$\text{Minimize } Z = \sum_{i=1}^{n} D[i]$
or equivalently,
$\text{Minimize } \max_i D[i]$
if you prefer a stricter fairness objective.

---

### 🔹 Additional Constraints

All constraints from **Model 1** still apply, plus:

* Each team plays ( W ) games total:
  $H[i] + A[i] = W, \quad \forall i \in T$

* Define balance variable:
  $D[i] \ge H[i] - A[i], \quad D[i] \ge A[i] - H[i]$

---

### 🔹 Implied Constraints (same as before)

* You can optionally fix one team’s home/away pattern to break home/away symmetry:
  $H[1] = \lceil W/2 \rceil$

---

### 🔹 Symmetry Breaking Constraints (same as before)

1. Fix first week schedule.
2. Fix home team for first match.
3. Possibly fix home/away pattern of team 1.

---

✅ **This second model not only ensures a valid round-robin schedule, but also minimizes home/away imbalance across all teams.**

---

## 💡 OPTIONAL EXTENSIONS

* Add **travel cost** or **venue constraints** if needed.
* For **odd n**, include a dummy team ( n+1 ) that "rests" each week.

---

## 📘 Summary Table

| Component           | Model 1 (Decision)              | Model 2 (Optimization)   |
| ------------------- | ------------------------------- | ------------------------ |
| Decision variables  | (Th[g,k], Ta[g,k])              | + (H[i], A[i], D[i])     |
| Constraints         | Pairwise, weekly, period limits | + Home/Away balance      |
| Objective           | None (feasibility only)         | Minimize ( \sum_i D[i] ) |
| Symmetry breaking   | Fix first week, team 1 home     | Same                     |
| Implied constraints | Distinctness, participation     | Same                     |


