import ast
import json
import os

#trying to do a pull request for demo purposes

def save_result(end_time:float, sol:str, file_path, obj=None, optimal=True, solver_name="gecode"):
    """
    Save the result to a JSON file under a solver key (e.g. 'gecode', 'chuffed').
    If the file exists, update or add the solver result.

    Args:
        solver_name (str): Name of the solver (used as key in the JSON file).
        end_time (float): The time the computation ended.
        sol (any): The solution to be saved.
        file_path (str): Path to the JSON file.
        obj (float, optional): Objective function value. Defaults to None without an objective function,
        optimal (bool, optional): Whether the solution is optimal. Defaults to True.
    """
    #TODO check whether time is optimal or not and eventually override default value
    #TODO By the definition of the floor function, the correct way to approach this problem is:
    # divide the time in milliseconds by 1000 (if your solver returns time in milliseconds)
    # apply the function floor to it

    sol = ast.literal_eval(str(sol))

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

    #TODO check how the overwriting works (in case of multiple solvers)
    # Write back to file
    with open(file_path, "w") as outfile:
        json.dump(data, outfile, indent=4)