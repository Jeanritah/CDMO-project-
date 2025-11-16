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

    result = "This is the MIP runner!"

    lower, upper = range
    print(f"Running MIP on range {lower}-{upper}")
    # ... solver code ...
    return result

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MIP CLI")
    parser.add_argument("--range", type=float, nargs=2, required=True, metavar=("LOWER", "UPPER"))
    args = parser.parse_args()

    main(args.range)
