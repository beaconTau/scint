"""
Usage:
python3 run.py <number of scint channels>

Runs interactive code with Scintillators instance.
Uses commands to control all scints simultaneously, or a single scint.
"""

import sys
from utils.scintillators import Scintillators

# for interactive
import code
    
if __name__ == "__main__":
     # Check if an argument is provided
    if len(sys.argv) < 2:
        print("Please provide a range value as a command-line argument.")
        sys.exit(1)
    try:
        range_value = int(sys.argv[1])
    except ValueError:
        print("Invalid range value. Please provide a valid integer.")
        sys.exit(1)

    scintillators = {"scint" : Scintillators(number_of_scints = range_value)}  # Use a dictionary to store instances
    
    print(f"Created instance: scint")

    code.interact(
        "Interactive Scintillator Control\nUse 'scint_[scint number]' objects for access, scint_[i].help() shows functions",
        local=scintillators)  # Use the dictionary as the local namespace
