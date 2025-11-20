import array
import math
from pyexpat import model
from typing import List
from minizinc import Instance, Model, Solver
import json
import os
from pathlib import Path
import ast
from utils import utils
import argparse

"""
run_<model>.py
================
Module for the <MODEL> approach.

This file defines a `main()` function that is compatible with source/main.py.

Expected Function Signature:
----------------------------
def main(input_path: str) -> dict:
    Reads the input file, runs the solver, and returns a dictionary with the results.

output: None
"""

# import in main before calling main method ------------------------------------
def extract_sb_flags(sb: str) -> str:
    sb = sb.upper()
    if sb == "TRUE":
        flags = ["sb"]
    elif sb == "BOTH":
        flags = ["sb", "!sb"]
    else:  # sb == "FALSE"
        flags = ["!sb"]
    return flags

def extract_obj_flags(objective: str) -> str:
    objective = objective.upper()
    if objective == "TRUE":
        flags = ["optimization"]
    elif objective == "BOTH":
        flags = ["decision", "optimization"]
    else:  # objective == "FALSE"
        flags = ["decision"]
    return flags
#-------------------------------------------------------------------------------   

def main(teams: List[int], sb_flags: List[str], obj_flags: List[str], 
        search_strategies: List[str] = ["base", "ff", "DWD+min", "DWD+rand"],
        solver_names:List[str]=["gecode", "chuffed"]) -> None:
    """
    Args:
        teams (List[int]): list of teams to run the model on
        sb (str): whtether to use models with symmetry breaking (TRUE) or not 
                (FALSE) or both (BOTH)
        search_strategy (str): models with specific search strategy to be used: "base", "FF", "BFS", etc.
        solver_names (List[str], optional): Default solvers when running all instances = ["gecode", "chuffed"].
    """

    dir_path = os.path.join(os.path.dirname(os.path.relpath(__file__)), "CP/models")
    # print(f"Model path: {dir_path}")

    ## TODO delegate responsibility to the main method so that there are less
    # if else statements in the code of every single model
    
    # --------------------------------------------------------------------------

    for s_name in solver_names:
        for obj in obj_flags:
            for sb in sb_flags:
                for strategy in search_strategies:
                    if s_name == "chuffed" and strategy == "DWD+rand":
                        continue

                    model_path = os.path.join(os.path.join(dir_path, f"{obj}"), f"cp_{sb}_{strategy}.mzn")
                    for t in teams:
                        '''
                        Possible parameters to consider:
                        - solver name: for chuffed certain models cannot be runned (we already know this)
                        - sb = True/False
                        - search strategy: which one? base, ff, DWD+min, DWD+rand
                        REMBER you should be able to run just one model with one search strategy
                        and solver, or all models with all search strategies,
                        think of a modular solution
                        '''
                        #print()
                        sts = Model(model_path)
                        # Find the MiniZinc solver configuration for Gecode
                        solver = Solver.lookup(s_name)

                        # Create an Instance of the sts model for Gecode
                        instance = Instance(solver, sts)
                        instance["n"] = t

                        # Solve configuration:
                        params = {
                            "time-limit": 300000
                        }

                        result = instance.solve(**params)

                        output_dir = Path('res/CP')
                        output_dir.mkdir(parents=True, exist_ok=True)
                        json_file_path = output_dir / f"{t}.json"

                        print(result.status)
                        # SATISFIED
                        # UNSATISFIABLE


                        # print(result.statistics)
                        #TODO guarda come catturare UNSAT e UNKNOWN per settare variabile 
                        # con il valore giusto

                        # Save result to JSON---------------------------------------------------
                        if f"{result.status}" == "UNSATISFIABLE":
                            seconds = 0
                            array_res = [] 
                            obj_value = None

                        elif f"{result.status}" == "UNKNOWN":
                            seconds = 300
                            array_res = [] 
                            obj_value = None

                        else: # SATISFIED
                            # convert time into seconds
                            s = str(result.statistics['time'])
                            h, m, s = s.split(':')
                            seconds = float(h) * 3600 + float(m) * 60 + float(s)
                            seconds = math.floor(seconds)

                            if obj == "optimization":
                                tokens = f'{result.solution}'.split('\n')
                                obj_value = tokens[0].split('=')[1].strip()
                                print(type(tokens[1:]))
                                array_res = '\n'.join(tokens[1:]).strip() 
                                array_res = ast.literal_eval(array_res)
                            else:
                            # convert team schedule to an array 
                                obj_value = None
                                array_res = ast.literal_eval(str(result.solution))
                            
                        # object field need to be modified after each execution
                        utils.save_result(seconds, array_res, json_file_path, obj=obj_value, solver_name=f"{s_name}_{obj}_{sb}_{strategy}")
                        print(f"Result saved to {json_file_path}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="CP CLI")
    parser.add_argument("--range", type=int, nargs=2, required=True, metavar=("LOWER", "UPPER"))
    parser.add_argument("--solver", type=List[str], default=["gecode", "chuffed"],
                        help="gecode | chuffed")
    parser.add_argument("--obj", type=str, default="BOTH",
                        help="true | false | both |")
    parser.add_argument("--sb", type=str, default="BOTH",
                        help="true | false | both")
    parser.add_argument("--search", type=str, default=["base", "ff", "DWD+min", "DWD+rand"],
                        help="base | ff | DWD+min | DWD+rand")

    args = parser.parse_args()

    teams = utils.convert_to_range((args.range[0], args.range[1]))

    sb_flags = extract_sb_flags(args.sb)
    obj_flags = extract_obj_flags(args.obj)

    main(teams, obj_flags=obj_flags, sb_flags=sb_flags, search_strategies=args.search, solver_names=args.solver)