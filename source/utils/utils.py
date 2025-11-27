import ast
import json
import os
from typing import List, Tuple

#trying to do a pull request for demo purposes

def save_result(tot_time:int, sol:str, file_path:str, obj=None, solver_name="gecode"):
    """
    Save the result to a JSON file under a solver key (e.g. 'gecode', 'chuffed').
    If the file exists, update or add the solver result.

    Args:
        solver_name (str): Name of the solver (used as key in the JSON file).
        tot_time (int): The time the computation took in seconds.
        sol (any): The solution to be saved.
        file_path (str): Path to the JSON file.
        obj (float, optional): Objective function value. Defaults to None without an objective function,
    """

    sol = ast.literal_eval(str(sol))

    if tot_time < 300:
        optimal = True
    else:
        optimal = False

    new_result = {
        "time": tot_time,
        "optimal": optimal,
        "obj": obj,
        "sol": sol
    }

    # Load existing file if available
    if os.path.exists(file_path):
        with open(file_path, "r") as infile:
            try:
                data = json.load(infile)
                if not isinstance(data, dict):
                    data = {}
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}

    # Update or add new solver result
    data[solver_name] = new_result

    # Write back to file
    with open(file_path, "w") as outfile:
        json.dump(data, outfile, indent=4)

def convert_to_range(value_range: Tuple[int, int]) -> List[int]:
    """
    Convert (lower, upper) bounds to an inclusive list of even integers.
    Ensures both bounds are even, then steps by 2.
    """
    lower, upper = value_range
    lower = lower + (lower % 2)     # ensure even
    upper = upper - (upper % 2)     # ensure even
    return list(range(lower, upper + 1, 2))

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

def convert_obj_to_flag(obj: str) -> str:
    obj = obj.upper()
    if obj == "OPTIMIZATION":
        flag = "obj"
    else:  # obj == "BOTH"
        flag = "!obj"
    return flag