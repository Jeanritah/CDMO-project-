# CDMO_Project/source/SMT/validate_solutions.py
import json
import os
import subprocess

def validate_with_checker():
    """Validate all SMT solutions with the official checker"""
    
    print("=== VALIDATING SMT SOLUTIONS ===")
    
    for n in [6, 8, 10, 12, 14]:
        json_file = f"../../res/SMT/{n}.json"
        
        if os.path.exists(json_file):
            print(f"\nChecking n={n}...")
            
            # Running  the solution checker (assuming it's in the project root)
            checker_path = "../../solution_checker.py"  
            if os.path.exists(checker_path):
                result = subprocess.run(
                    ["python", checker_path, "../../res/SMT/"], 
                    capture_output=True, 
                    text=True
                )
                # Filter output for this specific n
                for line in result.stdout.split('\n'):
                    if f"{n}.json" in line or "VALID" in line or "INVALID" in line:
                        print(f"  {line}")
            else:
                print(f"  Checker not found at {checker_path}")
        else:
            print(f"  No solution file for n={n}")

if __name__ == "__main__":
    validate_with_checker()