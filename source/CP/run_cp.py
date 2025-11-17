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
from typing import List
from utils.utils import save_result
from minizinc import Instance, Model, Solver
import json
import os
from pathlib import Path
import ast

def main(teams: List[int], solver_name="gecode",) -> None:
    """
    Run the <MODEL> with a specific solver on the given input.

    Args:
        input_path (str): Path to the input file.

    Returns:
        dict: A dictionary containing solver results.
    """

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
        file_name = "./cp_model.mzn"
        sts = Model(file_name)
        # Find the MiniZinc solver configuration for Gecode
        solver = Solver.lookup(solver_name)

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

        save_result(seconds, array_res, json_file_path, solver_name)
        print(f"Result saved to {json_file_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CP CLI")
    parser.add_argument("--range", type=float, nargs=2, required=True, metavar=("LOWER", "UPPER"))
    args = parser.parse_args()

    main(args.range)
