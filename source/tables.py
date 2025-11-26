import os
import json
import argparse
from typing import Tuple, Sequence, Optional, Dict, List
from utils.utils import convert_to_range

"""
Table generator with adjusted key naming:

Entry keys follow:
{s_name}_{obj_flag}_{lex_flag?}_{sb_flag}_{strategy}

Where:
  obj_flag:   'obj' or '!obj'
  lex_flag:   'lex' or '!lex' (MIP only; omitted for other models)
  sb_flag:    'sb'  or '!sb'
  strategy:   solver-specific strategy name (or omitted when 'default')

This script:
- Allows choosing model(s) & team size range.
- Uses fixed predefined solvers & strategies.
- Handles objective/decision mode.
- Handles UNSAT vs UNKNOWN.
- Adds lex flag for MIP only, before SB.
"""

# --------------------- Data Loading --------------------- #

def load_instance_data(mode: str, team_size: int, base_dir: str = "res") -> Optional[dict]:
    path = os.path.join(base_dir, mode, f"{team_size}.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


# --------------------- Status Classification --------------------- #

def classify_status(entry: Optional[dict]) -> Optional[str]:
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

def extract_cell_value(entry: Optional[dict], metric: str, bold_if_optimal: bool = True) -> str:
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
        return "-" if t is None else f"{t}"

    elif metric == "obj":
        obj = entry.get("obj", None)
        if obj is None:
            return "-"
        if optimal and bold_if_optimal:
            return f"\\textbf{{{obj}}}"
        return f"{obj}"

    return "-"


def determine_metric(has_objective: bool) -> str:
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
    float_env: bool = True,
    lex_flags: Optional[Sequence[str]] = None    # <-- added
):
    os.makedirs(output_dir, exist_ok=True)

    metric = determine_metric(has_objective)
    teams = convert_to_range(teams_range)

    # If not MIP → ignore lex flag
    if mode != "MIP":
        lex_flags = [""]  # placeholder, no lex
    else:
        lex_flags = lex_flags or ["lex", "!lex"]

    # Column count
    num_strategy = len(search_strategies)
    num_groups = len(lex_flags) * len(sb_flags)
    total_columns = 1 + num_groups * num_strategy

    alignment = "l|" + "c" * ((total_columns - 1)//2) + "|" + "c" * (total_columns - 1 - (total_columns - 1)//2)

    header_lines: List[str] = []

    # ---- Top Header Row ----
    top_header_cells = ["Teams"]
    if mode == "MIP":
        for lex in lex_flags:
            for sb_flag in sb_flags:
                title = f"{solver}+{lex}+{sb_flag}"
                top_header_cells.append(f"\\multicolumn{{{num_strategy}}}{{c}}{{{title}}}")
    else:
        for sb_flag in sb_flags:
            title = f"{solver}+{sb_flag}"
            top_header_cells.append(f"\\multicolumn{{{num_strategy}}}{{c}}{{{title}}}")

    header_lines.append(" & ".join(top_header_cells) + r" \\")

    # ---- Second Header Row: strategy names ----
    second_row_cells = [" "]
    if mode == "MIP":
        for _lex in lex_flags:
            for _sb in sb_flags:
                second_row_cells.extend(search_strategies)
    else:
        for _sb in sb_flags:
            second_row_cells.extend(search_strategies)

    header_lines.append(" & ".join(second_row_cells) + r" \\")
    header_lines.append(r"\hline")

    # ---- Body Rows ----
    body_lines: List[str] = []

    for team_size in teams:
        row_cells = [str(team_size)]
        data = load_instance_data(mode, team_size, base_dir=base_res_dir)

        for lex_flag in lex_flags:
            for sb_flag in sb_flags:
                for strategy in search_strategies:

                    # Build key
                    if strategy == "default":
                        if lex_flag:
                            key = f"{solver}_{obj_flag}_{sb_flag}_{lex_flag}"
                        else:
                            key = f"{solver}_{obj_flag}_{sb_flag}"
                    else:
                        if lex_flag:
                            key = f"{solver}_{obj_flag}_{sb_flag}_{lex_flag}_{strategy}"
                        else:
                            key = f"{solver}_{obj_flag}_{sb_flag}_{strategy}"

                    entry = data.get(key) if data else None
                    cell = extract_cell_value(entry, metric)
                    row_cells.append(cell)

        body_lines.append(" & ".join(row_cells) + r" \\")

    # ---- Build LaTeX ----
    lines: List[str] = []
    if float_env:
        lines.append(r"\begin{table}[h!]")
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


# --------------------- High-level Generator --------------------- #

def generate_tables_for_models(
    models: Sequence[str],
    teams_range: Tuple[int, int],
    obj_flag: str,
    has_objective: bool,
    output_dir: str,
    base_res_dir: str,
    model_definitions: Dict[str, dict]
):
    for model in models:
        model_cfg = model_definitions.get(model)
        if model_cfg is None:
            print(f"Skipping unknown model '{model}'")
            continue

        sb_flags = model_cfg.get("sb_flags", ["sb", "!sb"])
        lex_flags = model_cfg.get("lex_flags")  # Only MIP has this
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
                label=label,
                lex_flags=lex_flags
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
                        help="Inclusive team size range.")
    parser.add_argument("--models", type=str, nargs="+", default=["CP", "SAT", "MIP", "SMT"],
                        choices=["CP", "SAT", "MIP", "SMT"])
    parser.add_argument("--obj", action="store_true", help="Enable optimization mode.")
    parser.add_argument("--res-dir", type=str, default="res")
    parser.add_argument("--out-dir", type=str, default="output")

    args = parser.parse_args()

    teams_range = parse_range(args.range)
    obj_flag = "obj" if args.obj else "!obj"

    print("obj_flag:", obj_flag)

    # Model definitions (now with lex for MIP)
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
                "z3": ["default"]
            },
            "sb_flags": ["sb", "!sb"]
        },
        "MIP": {
            "solvers": {
                "gurobi": ["default", "psmplx", "dsmplx", "barr"],
                "cplex": ["default", "psmplx", "dsmplx", "barr"]
            },
            "sb_flags": ["sb", "!sb"],
            "lex_flags": ["lex", "!lex"]
        },
        "SMT": {
            "solvers": {
                "z3": ["default"],
            },
            "sb_flags": ["sb", "!sb"]
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