import math
from typing import List
from minizinc import Instance, Model, Solver
import os
from pathlib import Path
import ast
from utils import utils
import argparse

def main(teams: List[int], sb_flags: List[str]=["sb", "!sb"], obj_flags: List[str]=["decision", "optimization"], 
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

    print("\n=== CP ===")

    for s_name in solver_names:
        for obj in obj_flags:
            for sb in sb_flags:
                for strategy in search_strategies:
                    if s_name == "chuffed" and strategy == "DWD+rand":
                        continue

                    model_path = os.path.join(os.path.join(dir_path, f"{obj}"), f"cp_{sb}_{strategy}.mzn")
                    
                    print(f"Solver {s_name} for obj={obj}, sb={sb}, strategy={strategy}")

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
                        # print(model_path)
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

                        # print(result.status)
                        # SATISFIED
                        # UNSATISFIABLE
                        # UNKNOWN


                        # print(result.statistics)

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
                                #print(type(tokens[1:]))
                                array_res = '\n'.join(tokens[1:]).strip() 
                                array_res = ast.literal_eval(array_res)
                            else:
                            # convert team schedule to an array 
                                obj_value = None
                                array_res = ast.literal_eval(str(result.solution))
                            
                        json_key = f"{s_name}_{utils.convert_obj_to_flag(obj)}_{sb}_{strategy}"
                        # object field need to be modified after each execution
                        utils.save_result(seconds, array_res, json_file_path, obj=obj_value, solver_name=json_key)
                        print(f"Result saved under '{json_key}' to {json_file_path}")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="CP CLI")
    parser.add_argument("--range", type=int, nargs=2, required=True, metavar=("LOWER", "UPPER"))
    parser.add_argument("--solver", type=str, nargs="+", default=["gecode", "chuffed"],
                        choices=["gecode", "chuffed"], help="gecode | chuffed")
    parser.add_argument("--obj", type=str, default="BOTH",
                        help="true | false | both |")
    parser.add_argument("--sb", type=str, default="BOTH",
                        help="true | false | both")
    parser.add_argument("--search", nargs="+", type=str, default=["base", "ff", "DWD+min", "DWD+rand"],
                        choices=["base", "ff", "DWD+min", "DWD+rand"],
                        help="base | ff | DWD+min | DWD+rand")

    args = parser.parse_args()

    teams = utils.convert_to_range((args.range[0], args.range[1]))

    sb_flags = utils.extract_sb_flags(args.sb)
    obj_flags = utils.extract_obj_flags(args.obj)

    main(teams, obj_flags=obj_flags, sb_flags=sb_flags, search_strategies=args.search, solver_names=args.solver)