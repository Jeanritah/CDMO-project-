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

---






# Project Overview
