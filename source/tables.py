import os
import json
from typing import Tuple, Sequence, Optional
from utils.utils import convert_to_range


def load_instance_data(mode: str, team_size: int, base_dir: str = "res") -> Optional[dict]:
    """
    Load JSON data for a given mode and team size.
    Returns None if file not found or invalid.
    """
    path = os.path.join(base_dir, mode, f"{team_size}.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def extract_cell_value(entry: dict,
                       metric: str,
                       bold_if_optimal: bool = True) -> str:
    """
    Extract a string to print in the LaTeX cell, based on metric:
    - metric == 'time': use entry['time']
    - metric == 'obj': use entry['obj']
    Special cases:
    - UNSAT if entry indicates unsatisfiable (entry.get('unsat') == True or status == 'UNSAT')
    - Bold objective if optimal and metric == 'obj'
    - '-' if missing metric or no data
    """
    if entry is None:
        return "N/A"

    # Detect unsatisfiable
    if entry.get("unsat") is True or entry.get("status") == "UNSAT":
        return "UNSAT"

    optimal = entry.get("optimal", False)

    if metric == "time":
        t = entry.get("time", None)
        if t is None:
            return "-"
        # Format time; adjust decimals as needed
        return f"{t:.3f}"
    elif metric == "obj":
        obj = entry.get("obj", None)
        if obj is None:
            return "-"
        if optimal and bold_if_optimal:
            return f"\\textbf{{{obj}}}"
        return f"{obj}"
    else:
        return "-"


def determine_metric(decision_vs_optimization: str) -> str:
    """
    Map problem type to metric field.
    decision -> 'time'
    optimization -> 'obj'
    """
    decision_vs_optimization = decision_vs_optimization.lower()
    if decision_vs_optimization.startswith("dec"):
        return "time"
    return "obj"


def build_table_for_solver_mode(
    solver: str,
    mode: str,
    sb_flags: Sequence[str],
    search_strategies: Sequence[str],
    teams_range: Tuple[int, int],
    decision_vs_optimization: str,
    output_dir: str = "output",
    base_res_dir: str = "res",
    caption: Optional[str] = None,
    label: Optional[str] = None,
    float_env: bool = True
):
    """
    Build and write a LaTeX table for a single (solver, mode) pair.

    Columns are grouped by SB flags; each group has one column per search strategy.
    """
    os.makedirs(output_dir, exist_ok=True)

    metric = determine_metric(decision_vs_optimization)
    teams = convert_to_range(teams_range)

    # Number of columns: row label + groups
    num_strategy = len(search_strategies)
    num_groups = len(sb_flags)
    total_columns = 1 + num_groups * num_strategy  # first column for team size

    # Start LaTeX table
    alignment = "l|" + "c" * (total_columns - 1)  # first column left, rest center
    header_lines = []

    # First header row: solver+SBFlag groups using multicolumn
    top_header_cells = [" "]
    for flag in sb_flags:
        group_title = f"{solver}+{flag}"
        top_header_cells.append(f"\\multicolumn{{{num_strategy}}}{{c}}{{{group_title}}}")
    header_lines.append(" & ".join(top_header_cells) + r" \\")
    header_lines.append("Teams ")  # optional: a rule under all groups

    # Second header row: search strategies repeated per group
    second_row_cells = [" "]
    for _flag in sb_flags:
        second_row_cells.extend(search_strategies)
    header_lines.append(" & ".join(second_row_cells) + r" \\")

    # Body rows
    body_lines = []
    for team_size in teams:
        row_cells = [str(team_size)]
        data = load_instance_data(mode, team_size, base_dir=base_res_dir)
        for flag in sb_flags:
            for strategy in search_strategies:
                key = f"{solver}_{flag}_{strategy}"
                entry = data.get(key) if data else None
                cell = extract_cell_value(entry, metric)
                row_cells.append(cell)
        body_lines.append(" & ".join(row_cells) + r" \\")

    # Assemble LaTeX code
    lines = []
    if float_env:
        lines.append(r"\begin{table}[ht]")
        lines.append(r"\centering")
    lines.append(r"\begin{tabular}{" + alignment + "}")
    lines.extend(header_lines)
    lines.append(r"\hline")
    lines.extend(body_lines)
    lines.append(r"\end{tabular}")
    if caption:
        lines.append(f"\\caption{{{caption}}}")
    if label:
        lines.append(f"\\label{{{label}}}")
    if float_env:
        lines.append(r"\end{table}")

    table_tex = "\n".join(lines) + "\n"

    # Output filename
    safe_solver = solver.replace(" ", "_")
    filename = f"{safe_solver}_{mode}.tex"
    out_path = os.path.join(output_dir, filename)
    with open(out_path, "w") as f:
        f.write(table_tex)
    print(f"Wrote {out_path}")


def generate_all_tables(
    solver: str,
    modes: Sequence[str],
    sb_flags: Sequence[str],
    search_strategies: Sequence[str],
    teams_range: Tuple[int, int],
    decision_vs_optimization: str,
    output_dir: str = "output",
    base_res_dir: str = "res"
):
    """
    Generate tables for every (solver, mode) pair.
    """
    for mode in modes:
        caption = f"Results for {solver} on mode {mode} ({decision_vs_optimization})"
        label = f"tab:{solver}_{mode}"
        build_table_for_solver_mode(
            solver=solver,
            mode=mode,
            sb_flags=sb_flags,
            search_strategies=search_strategies,
            teams_range=teams_range,
            decision_vs_optimization=decision_vs_optimization,
            output_dir=output_dir,
            base_res_dir=base_res_dir,
            caption=caption,
            label=label
        )


if __name__ == "__main__":
    # Example usage; replace with your actual lists.
    solvers = ["gecode", "chuffed"]
    modes = ["CP", "SAT"]
    sb_flags = ["SB", "!SB"]
    search_strategies = ["FF", "BFS"]
    teams_range = (2, 16)  # inclusive, even range
    decision_vs_optimization = "optimization"  # or "decision"

    for solver in solvers:
        generate_all_tables(
            solver=solver,
            modes=modes,
            sb_flags=sb_flags,
            search_strategies=search_strategies,
            teams_range=teams_range,
            decision_vs_optimization=decision_vs_optimization
        )