import ast
import json
import os


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