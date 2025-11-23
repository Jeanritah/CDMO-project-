#TODO call from here the different files jean created for SMT
#TODO print(f"Running model with solver: {s_name} for obj: {obj}, sb: {sb}, strategy: {strategy}")
#TODO after dinner
"""
run_<model>.py
================
Module for the <MODEL> approach.

This file defines a `main()` function that is compatible with source/main.py.

Expected Function Signature:
----------------------------
def main(input_path: str) -> dict:
    Reads the input file, runs the solver, and returns a dictionary with the results.

output: "Result saved to {output_path}"
"""
import argparse
from typing import List
from SMT.smt_decision_sb import decision_sb
#TODO import missing models without dying
# from SMT.smt_optimization_sb import optimization_sb
from utils import utils
#from utils.utils import save_result  # ptional helper if you have one

# TODO add missing models
model_functions = {
    "smt_decision_sb": decision_sb,
   # "smt_optimization_sb": optimization_sb,
    }

def main(teams: List[int], obj_flags: List[str]=["decision", "optimization"], sb_flags: List[str]= ["sb", "!sb"]):
    for obj in obj_flags:
        for sb in sb_flags:
            for t in teams:
                model_name = f"smt_{obj}_{sb}"
                print(f"Running model with solver: z3 for obj: {obj}, sb: {sb}")
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
