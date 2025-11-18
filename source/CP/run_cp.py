#TODO# function to transform time from milliseconds to seconds
	
# By the definition of the floor function, the correct way to approach this problem is:
# divide the time in milliseconds by 1000 (if your solver returns time in milliseconds)
# apply the function floor to it

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

from pyexpat import model
from typing import List
from minizinc import Instance, Model, Solver
import json
import os
from pathlib import Path
import ast
from source.utils import utils
import argparse

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
    

def main(teams: List[int], sb: str, search_strategies: List[str] = ["base", "ff", "DWD+min", "DWD+rand"],
         objective: List[str] = False, solver_names:List[str]=["gecode", "chuffed"]) -> None:
    """

    Args:
        teams (List[int]): list of teams to run the model on
        sb (str): whtether to use models with symmetry breaking (TRUE) or not 
                (FALSE) or both (BOTH)
        search_strategy (str): models with specific search strategy to be used: "base", "FF", "BFS", etc.
        solver_names (List[str], optional): Default solvers when running all instances = ["gecode", "chuffed"].
    """

    dir_path = os.path.join(os.path.dirname(os.path.relpath(__file__)), "models")
    # print(model_base_path)

    ## TODO delegate responsibility to the main method so that there are less
    # if else statements in the code of every single model
    # 
    sb_flags = extract_sb_flags(sb)
    obj_flags = extract_obj_flags(objective)

    for s_name in solver_names:
        for obj in obj_flags:
            for sb in sb_flags:
                for strategy in search_strategies:
                    if s_name == "chuffed" and strategy == "DWD+rand":
                        continue

                    model_path = os.path.join(os.path.join(dir_path, f"{obj}"), f"cp_{sb}_{strategy}.mzn")
                    print(f"Running model: {model_path} with solver: {s_name}")
                    for t in teams:
                        #TODO how to load the correct file based on all possible parameters?
                        '''
                        Possible parameters to consider:
                        - solver name: for chuffed certain models cannot be runned (we already know this)
                        - sb = True/False
                        - search strategy: which one? base, ff, DWD+min, DWD+rand
                        REMBER you should be able to run just one model with one search strategy
                        and solver, or all models with all search strategies,
                        think of a modular solution
                        '''
                        print()
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

                        # Save result to JSON---------------------------------------------------
                        
                        #TODO: check if this methods works also for the optimization version of 
                        # the model, otherwise modify it accordingly
                        output_dir = Path('res/CP')
                        output_dir.mkdir(parents=True, exist_ok=True)
                        json_file_path = output_dir / f"{t}.json"

                        # convert team schedule to an array 
                        array_res = ast.literal_eval(str(result.solution))

                        # convert time into seconds
                        s = str(result.statistics['time'])
                        h, m, s = s.split(':')
                        seconds = float(h) * 3600 + float(m) * 60 + float(s)

                        utils.save_result(seconds, array_res, json_file_path, s_name)
                        print(f"Result saved to {json_file_path}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="CP CLI")
    parser.add_argument("--range", type=int, nargs=2, required=True, metavar=("LOWER", "UPPER"))
    args = parser.parse_args()
    teams = utils.convert_to_range((args.range[0], args.range[1]))

    #TODO modify with parameters from command line
    main(teams,objective="FALSE", sb="FALSE", search_strategies=["base"], solver_names=["gecode"])

'''
{
    "gecode": {
        "time": 0.29,
        "optimal": true,
        "obj": "gecode",
        "sol": [
'''