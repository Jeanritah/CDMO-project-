from minizinc import Instance, Model, Solver
import json
import os
from pathlib import Path
import ast

def save_result(end_time, sol, file_path, obj=None, optimal=True, solver_name="gecode"):
    """
    Save the result to a JSON file under a solver key (e.g. 'gecode', 'chuffed').
    If the file exists, update or add the solver result.

    Args:
        solver_name (str): Name of the solver (used as key in the JSON file).
        end_time (float): The time the computation ended.
        sol (any): The solution to be saved.
        file_path (str): Path to the JSON file.
        obj (float, optional): Objective value. Defaults to None.
        optimal (bool, optional): Whether the solution is optimal. Defaults to True.
    """
    new_result = {
        "time": end_time,
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

#TODO TRANSFORM INTO A MAIN FUNCTION

# PARAMETERS
solver = "gecode"
values = [2, 6, 8, 10,12, 14]

for teams in values:
    sts = Model("./cp_model.mzn")
    # Find the MiniZinc solver configuration for Gecode
    solver_name = "gecode"
    gecode = Solver.lookup(solver_name)

    # Create an Instance of the sts model for Gecode
    instance = Instance(gecode, sts)
    instance["n"] = teams

    # Solve configuration:
    params = {
        "restart": "luby",
        "restart-base": 1.5,
        "random-seed": 50,
        "time-limit": 300000
    }

    result = instance.solve(**params)

    # print(result)

    # Save result to JSON
    output_dir = Path('res/CP')
    output_dir.mkdir(parents=True, exist_ok=True)
    json_file_path = output_dir / f"{teams}.json"
    #TRANSFORM STRING INTO ARRAY
    array_res = ast.literal_eval(str(result.solution))
    # print(result.statistics['time'])
    s = str(result.statistics['time'])
    h, m, s = s.split(':')
    seconds = float(h) * 3600 + float(m) * 60 + float(s)
    # print(seconds)

    save_result(seconds, array_res, json_file_path, solver_name)
    print(f"Result for {teams} teams saved to {json_file_path}")
