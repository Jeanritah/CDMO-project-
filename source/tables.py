import os
import json
import argparse
from typing import Tuple, Sequence, Optional, Dict, List
from utils.utils import convert_to_range

"""
Table generator with adjusted key naming:
Entry keys inside each JSON file follow the pattern:
{s_name}_{obj_flag}_{sb_flag}_{strategy}
where:
  obj_flag: 'obj'  (objective enabled / optimization) OR '!obj' (no objective / decision)
  sb_flag : 'SB'   (symmetry-breaking enabled) OR '!SB' (disabled)
  strategy: one of the predefined strategies for the solver.

This script now:
- Lets the user choose the models and the team size range from the CLI.
- Uses predefined solvers and search strategies per model (user cannot override them).
- Adds the objective flag into the lookup key.
- Creates the output directory if not existing (relative to project root).
- Reads result JSONs from ./res/<MODEL>/<team_size>.json
- Handles UNSAT vs UNKNOWN (timeout/no solution) cases:
    UNSAT  -> 'UNSAT'
    UNKNOWN -> 'N/A'
"""

# --------------------- Data Loading --------------------- #

def load_instance_data(mode: str, team_size: int, base_dir: str = "res") -> Optional[dict]:
    """
    Load JSON data for a given mode (model) and team size.
    Expects: {base_dir}/{mode}/{team_size}.json
    """
    path = os.path.join(base_dir, mode, f"{team_size}.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


# --------------------- Classification --------------------- #

def classify_status(entry: Optional[dict]) -> Optional[str]:
    """
    Classify a solver entry into:
      'UNSAT'  : Proven unsatisfiable
      'UNKNOWN': Timeout / no solution (not optimal, no obj, empty solution list)
      None     : Normal result
    Conditions for UNSAT:
      - entry.get('unsat') is True
      - entry.get('status') == 'UNSAT'
      - (optimal == True AND obj is None AND solution list empty)
    Conditions for UNKNOWN:
      - (optimal == False AND obj is None AND solution list empty)
    """
    if entry is None:
        return None

    if entry.get("unsat") is True or entry.get("status") == "UNSAT":
        return "UNSAT"

    optimal = entry.get("optimal", False)
    obj = entry.get("obj", None)
    sol = entry.get("sol", None)
    sol_empty = isinstance(sol, list) and len(sol) == 0

    if optimal and obj is None and sol_empty:
        return "UNSAT"

    if (not optimal) and obj is None and sol_empty:
        return "UNKNOWN"

    return None


# --------------------- Cell Extraction --------------------- #

def extract_cell_value(entry: Optional[dict],
                       metric: str,
                       bold_if_optimal: bool = True) -> str:
    """
    Produce LaTeX cell content.
    Special cases:
      entry None          -> 'N/A'
      UNSAT               -> 'UNSAT'
      UNKNOWN / timeout   -> 'N/A'
    metric == 'time' -> formatted time or '-'
    metric == 'obj'  -> objective (bold if optimal) or '-'
    """
    if entry is None:
        return "N/A"

    status = classify_status(entry)
    if status == "UNSAT":
        return "UNSAT"
    if status == "UNKNOWN":
        return "N/A"

    optimal = entry.get("optimal", False)

    if metric == "time":
        t = entry.get("time", None)
        if t is None:
            return "-"
        return f"{t}"
    elif metric == "obj":
        obj = entry.get("obj", None)
        if obj is None:
            return "-"
        if optimal and bold_if_optimal:
            return f"\\textbf{{{obj}}}"
        return f"{obj}"
    return "-"


def determine_metric(has_objective: bool) -> str:
    """
    If an objective is active we show objective values (obj).
    If not (decision problem) we focus on time.
    """
    return "obj" if has_objective else "time"


# --------------------- Table Construction --------------------- #

def build_table_for_solver_mode(
    solver: str,
    mode: str,
    obj_flag: str,
    sb_flags: Sequence[str],
    search_strategies: Sequence[str],
    teams_range: Tuple[int, int],
    has_objective: bool,
    output_dir: str = "output",
    base_res_dir: str = "res",
    caption: Optional[str] = None,
    label: Optional[str] = None,
    float_env: bool = True
):
    """
    Build and write a LaTeX table for a single (solver, mode, objective state) combination.

    Columns are grouped by SB flags; each group has one column per search strategy.
    Keys looked up in JSON: {solver}_{obj_flag}_{sb_flag}_{strategy}
    """
    os.makedirs(output_dir, exist_ok=True)

    metric = determine_metric(has_objective)
    teams = convert_to_range(teams_range)

    num_strategy = len(search_strategies)
    num_groups = len(sb_flags)
    total_columns = 1 + num_groups * num_strategy  # first column for team size

    alignment = "l|" + "c" * (total_columns - 1)

    header_lines: List[str] = []
    # Top header row
    top_header_cells = ["Teams"]
    for flag in sb_flags:
        group_title = f"{solver}+{flag}"
        top_header_cells.append(f"\\multicolumn{{{num_strategy}}}{{c}}{{{group_title}}}")
    header_lines.append(" & ".join(top_header_cells) + r" \\")
    # Second header row: strategy names
    second_row_cells = [" "]
    for _flag in sb_flags:
        second_row_cells.extend(search_strategies)
    header_lines.append(" & ".join(second_row_cells) + r" \\")
    header_lines.append(r"\hline")

    body_lines: List[str] = []
    for team_size in teams:
        row_cells = [str(team_size)]
        data = load_instance_data(mode, team_size, base_dir=base_res_dir)
        for sb_flag in sb_flags:
            for strategy in search_strategies:
                key = f"{solver}_{obj_flag}_{sb_flag}_{strategy}"
                print("key:", key)
                entry = data.get(key) if data else None
                cell = extract_cell_value(entry, metric)
                print("cell:", type(cell))
                row_cells.append(cell)
        body_lines.append(" & ".join(row_cells) + r" \\")

    lines: List[str] = []
    if float_env:
        lines.append(r"\begin{table}[ht]")
        lines.append(r"\centering")
    lines.append(r"\begin{tabular}{" + alignment + "}")
    lines.extend(header_lines)
    lines.extend(body_lines)
    lines.append(r"\end{tabular}")
    if caption:
        lines.append(f"\\caption{{{caption}}}")
    if label:
        lines.append(f"\\label{{{label}}}")
    if float_env:
        lines.append(r"\end{table}")

    table_tex = "\n".join(lines) + "\n"

    safe_solver = solver.replace(" ", "_")
    filename = f"{safe_solver}_{mode}_{obj_flag}.tex"
    out_path = os.path.join(output_dir, filename)
    with open(out_path, "w") as f:
        f.write(table_tex)
    print(f"Wrote {out_path}")


def generate_tables_for_models(
    models: Sequence[str],
    teams_range: Tuple[int, int],
    obj_flag: str,
    has_objective: bool,
    output_dir: str,
    base_res_dir: str,
    model_definitions: Dict[str, dict]
):
    """
    For each selected model, generate tables per solver using predefined strategies.
    Includes objective flag in lookup keys.
    """
    for model in models:
        model_cfg = model_definitions.get(model)
        if model_cfg is None:
            print(f"Skipping unknown model '{model}'")
            continue
        sb_flags = model_cfg.get("sb_flags", ["sb", "!sb"])
        solvers_cfg: Dict[str, Sequence[str]] = model_cfg.get("solvers", {})

        for solver, strategies in solvers_cfg.items():
            caption = f"Results for {solver} on model {model} ({'optimization' if has_objective else 'decision'})"
            label = f"tab:{solver}_{model}_{obj_flag}"
            build_table_for_solver_mode(
                solver=solver,
                mode=model,
                obj_flag=obj_flag,
                sb_flags=sb_flags,
                search_strategies=strategies,
                teams_range=teams_range,
                has_objective=has_objective,
                output_dir=output_dir,
                base_res_dir=base_res_dir,
                caption=caption,
                label=label
            )


# --------------------- Helpers --------------------- #

def parse_range(range_vals: Sequence[int]) -> Tuple[int, int]:
    if len(range_vals) != 2:
        raise ValueError("Range must have exactly two integers: LOWER UPPER")
    lower, upper = range_vals
    if lower > upper:
        raise ValueError("LOWER must be <= UPPER")
    return lower, upper


# --------------------- Main --------------------- #

def main():
    parser = argparse.ArgumentParser(description="Generate LaTeX tables for solver/model results.")
    parser.add_argument("--range", type=int, nargs=2, required=True, metavar=("LOWER", "UPPER"),
                        help="Inclusive team size range (LOWER UPPER).")
    parser.add_argument("--models", type=str, nargs="+", default=["CP", "SAT", "MIP", "SMT"],
                        choices=["CP", "SAT", "MIP", "SMT"],
                        help="Models to generate tables for.")
    parser.add_argument("--obj", action="store_true", help="optimization enabled")
    parser.add_argument("--res-dir", type=str, default="res",
                        help="Base directory containing result JSON files (default ./res).")
    parser.add_argument("--out-dir", type=str, default="output",
                        help="Directory to write LaTeX tables (will be created if missing).")

    args = parser.parse_args()

    teams_range = parse_range(args.range)
    obj_flag = "obj" if args.obj else "!obj"
    print("obj_flag:", obj_flag)

    # Predefined mapping of models to solvers and their strategies
    model_definitions = {
        "CP": {
            "solvers": {
                "gecode": ["base", "ff", "DWD+min", "DWD+rand"],
                "chuffed": ["base", "ff", "DWD+min"]
            },
            "sb_flags": ["sb", "!sb"]
        },
        "SAT": {
            "solvers": {
                "kissat": ["base", "phase-saving"],
                "cadical": ["base"]
            },
            "sb_flags": ["SB", "!SB"]
        },
        "MIP": {
            "solvers": {
                "gurobi": ["default"],
                "cplex": ["default"]
            },
            "sb_flags": ["SB", "!SB"]
        },
        "SMT": {
            "solvers": {
                "z3": ["default", "ff"],
                "cvc5": ["default"]
            },
            "sb_flags": ["SB", "!SB"]
        }
    }

    generate_tables_for_models(
        models=args.models,
        teams_range=teams_range,
        obj_flag=obj_flag,
        has_objective=args.obj,
        output_dir=args.out_dir,
        base_res_dir=args.res_dir,
        model_definitions=model_definitions
    )


if __name__ == "__main__":
    main()

