# Build and Run Instructions
(How to Run)
This project contains the SMT models for the Sports Tournament Scheduling (STS) problem.
All scripts are written in Python using the **Z3 SMT Solver**.

---

## **1. Requirements**

Before running anything, install:

```bash
pip install z3-solver
```

No other dependencies are required.

---

## **2. File Structure**

```
CDMO-project/
│
├── smt_aligned.py
├── smt_optimized.py
├── smt_experiments_final.py
├── validate_solutions.py
│
└── res/SMT/n.json     (generated results)
```

---

## **3. Running the Decision Model**

This model solves the STS feasibility problem for **n** teams.

```bash
python smt_aligned.py --teams n
```

Example:

```bash
python smt_aligned.py --teams 8
```

This creates:

```
res/SMT/8.json
```

Containing:

* runtime
* status (SAT/UNSAT/TIMEOUT)
* schedule solution (if SAT)

---

## **4. Running the Optimization Model**

This model minimizes the home/away imbalance:

```bash
python smt_optimized.py --teams n
```

Example:

```bash
python smt_optimized.py --teams 6
```

Output is also saved in the JSON file under key `"z3_smt_opt"`.

---

## **5. Running All Experiments at Once**

To produce the results tables for the report:

```bash
python smt_experiments_final.py
```

This prints two tables:

* Decision model results
* Optimization model results

And verifies JSON data automatically.

---

## **6. JSON Output Format**

Each `n.json` file has the structure:

```json
{
  "z3_smt_decision": {
    "time": "...",
    "optimal": true,
    "obj": null,
    "sol": [[...]]
  },

  "z3_smt_opt": {
    "time": "...",
    "optimal": true,
    "obj": 5,
    "sol": [[...]]
  }
}
```

If the solver timed out, `"sol"` will be an empty list.

---

## **7. Validating Solutions**

Optional but included:

```bash
python validate_solutions.py
```

This checks:

* unique games
* weekly constraints
* period constraints
* domain
* symmetry



# Project Overview
SMT Model for Sports Tournament Scheduling

The Sports Tournament Scheduling (STS) problem consists of generating a valid round-robin tournament in which every team plays every other team exactly once, subject to additional fairness and structural constraints.
This problem is combinatorial and grows rapidly in complexity as the number of teams increases, making it a classical benchmark for constraint programming and SMT solving.

In this project, we implement two SMT-based models using the **Z3 solver**:

### **1. Decision Model (Feasibility)**

This model checks whether a schedule exists that satisfies the four official STS constraints:

* **C1 — Number of teams is even**
* **C2 — Each pair of teams plays exactly once** (round-robin)
* **C3 — Each team plays exactly one match per week**
* **C4 — No team appears more than twice in the same period**

The decision model produces a valid schedule whenever one exists.

### **2. Optimization Model**

In addition to the feasibility constraints, this model minimizes the **home/away imbalance** for each team:

[
\min \max_i | 2h_i - (n-1) |
]

where ( h_i ) is the number of home matches of team ( i ).
The imbalance is stored as the objective value ( D^* ).

### **Approach Summary**

* Games are represented by integer variables `T[p][w][home/away]`.
* Structural constraints (round-robin, weekly schedule, symmetry breaking) are encoded using SMT.
* All results are exported automatically as structured JSON files.
* A final experiment script (`smt_experiments_final.py`) runs all instances and prints clean tables for the report.

### **Why SMT?**

SMT is well-suited for STS because:

* Constraints on integers are expressed naturally
* Symmetry-breaking can drastically reduce the search space
* Optimization features of Z3 allow adding fairness measures
* Declarative modelling avoids manually generating round-robin templates

This makes SMT an effective and transparent approach for small- and medium-sized tournament sizes.



