import argparse
from pathlib import Path
from typing import List
from utils import utils

from decision_no_sb import solve_decision_no_sb
from decision_sb import solve_decision_sb
from opt_no_sb import solve_opt_no_sb
from opt_sb import solve_opt_sb


def normalize_obj_flags(obj: str) -> List[str]:
    o = obj.strip().lower()
    if o in ("optimization", "opt", "obj", "true"):
        return ["optimization"]
    if o in ("decision", "dec", "false", "!obj"):
        return ["decision"]
    return ["decision", "optimization"]


def normalize_sb_flags(sb: str) -> List[str]:
    s = sb.strip().lower()
    if s in ("true", "sb"):
        return ["sb"]
    if s in ("false", "!sb", "nosb"):
        return ["!sb"]
    return ["sb", "!sb"]


SOLVER_MAP = {
    ("decision", "!sb"): solve_decision_no_sb,
    ("decision", "sb"):  solve_decision_sb,
    ("optimization", "!sb"): solve_opt_no_sb,
    ("optimization", "sb"):  solve_opt_sb,
}


def main(teams: List[int], sb_flags: List[str], obj_flags: List[str]) -> None:

    out_dir = Path("res/SAT")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n=== SAT Runner ===")
    print("Teams:", teams)
    print("Objectives:", obj_flags)
    print("Symmetry-breaking:", sb_flags)

    for obj in obj_flags:
        for sb in sb_flags:

            solver_fun = SOLVER_MAP[(obj, sb)]
            print(f"\Running obj={obj}, sb={sb}")

            for n in teams:
                print(f"Solving n={n}")

                result = solver_fun(n)

                time_val = result.get("time", 300)
                sol_raw = result.get("sol", [])
                obj_value = result.get("obj", None)

                sol = str(sol_raw)

                solver_key = f"z3_{utils.convert_obj_to_flag(obj)}_{sb}"

                json_path = out_dir / f"{n}.json"

                utils.save_result(
                    tot_time=time_val,
                    sol=sol,             
                    file_path=str(json_path),
                    obj=obj_value,
                    solver_name=solver_key,
                )

                print(f"Saved under '{solver_key}' to {json_path}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="SAT Runner")

    parser.add_argument("--range", type=int, nargs=2, required=True,
        metavar=("LOWER", "UPPER"), help="Inclusive integer range")

    parser.add_argument("--obj", type=str, default="BOTH",
        help="decision | optimization | both")

    parser.add_argument("--sb", type=str, default="BOTH",
        help="sb | !sb | both")

    parser.add_argument("--search", nargs="+", type=str, default=["base"])
    parser.add_argument("--solver", nargs="+", type=str, default=["z3"])

    args = parser.parse_args()

    teams = utils.convert_to_range((args.range[0], args.range[1]))
    sb_flags = normalize_sb_flags(args.sb)
    obj_flags = normalize_obj_flags(args.obj)

    main(teams, sb_flags, obj_flags)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SAT CLI")
    parser.add_argument(
        "--range",
        type=float,
        nargs=2,
        required=False,
        metavar=("LOWER", "UPPER"),
        help="(ignored) Range required by main.py"
    )
    args = parser.parse_args()
    if args.range is None:
        main((0.0, 1.0))
    else:
        main(tuple(args.range))
