#TODO# function to transform time from milliseconds to seconds
	
# By the definition of the floor function, the correct way to approach this problem is:
# divide the time in milliseconds by 1000 (if your solver returns time in milliseconds)
# apply the function floor to it

"""
run_<method>.py
================
Solver module for the <METHOD> approach.

This file defines a `main()` function that is compatible with source/main.py.

Expected Function Signature:
----------------------------
def main(input_path: str) -> dict:
    Reads the input file, runs the solver, and returns a dictionary with the results.

Returned Dictionary Format:
---------------------------
{
    "status": str,         # e.g. "OPTIMAL", "INFEASIBLE", "TIMEOUT"
    "objective": float,    # Best objective value found (if applicable)
    "solution": dict,      # Variable assignments or model output
    "runtime": float,      # Execution time in seconds
    "method": str          # Name of the method, e.g. "CP"
}
"""
#from utils.utils import save_result  # Optional helper if you have one

def main(range: tuple[float, float]):
    """
    Run the <METHOD> solver on the given input.

    Args:
        input_path (str): Path to the input file.

    Returns:
        dict: A dictionary containing solver results.
    """

    # 1️⃣ Parse the arguments/input data

    # 2️⃣ Build the model (this depends on your solver)

    # 3️⃣ Solve the problem
    # call save_result() to save the output to json files following project 
    # requirements

    # 4️⃣ Construct the output 

    result = "This is the SMT runner!"

    lower, upper = range
    print(f"Running SMT solver on range {lower}-{upper}")
    # ... solver code ...
    return result

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SMT solver CLI")
    parser.add_argument("--range", type=float, nargs=2, required=True, metavar=("LOWER", "UPPER"))
    args = parser.parse_args()

    main(args.range)
