import argparse
from typing import List
from SMT.models.smt_decision_sb import decision_sb
from SMT.models.smt_optimization_sb import optimization_sb
from SMT.models.smt_decision_no_sb import  test_without_symmetry
from utils import utils

# TODO add missing model
model_functions = {
   "smt_decision_sb": decision_sb,
   "smt_optimization_sb": optimization_sb,
   "smt_decision_!sb":  test_without_symmetry,
    }

def main(teams: List[int], obj_flags: List[str]=["decision", "optimization"], sb_flags: List[str]= ["sb", "!sb"]):
    print("\n=== SMT ===")

    for obj in obj_flags:
        for sb in sb_flags:
            for t in teams:
                model_name = f"smt_{obj}_{sb}"
                print(f"Solver z3 for obj={obj}, sb={sb}")
                model_functions[model_name](t)  

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="CP CLI")
    parser.add_argument("--range", type=int, nargs=2, required=True, metavar=("LOWER", "UPPER"))
    parser.add_argument("--obj", type=str, default="BOTH",
                        help="true | false | both |")
    parser.add_argument("--sb", type=str, default="BOTH",
                        help="true | false | both")

    args = parser.parse_args()
    main(utils.convert_to_range(args.range),utils.extract_obj_flags(args.obj), utils.extract_sb_flags(args.sb))
