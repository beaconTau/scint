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

    code.interact(
        "="*20+"\n"
        "Interactive Scintillator Control\n\n"+
        f"Created Scintillators instance 'scint' with {range_value} channels.\n\n"+
        "To view current status use 'scint.printStatus()'.\n"+
        "To run command for all scints, use 'scint.runMethod(method, *args, **kwargs)'\n"+
        "To run a command for a single scintillator channel, use 'scint.scints[channel_number]' to access Scintillator methods and atrributes\n\n"+
        "To view all available commands, use 'scint.help()'\n"+
        "="*20+"\n",
        local=scintillators)  # Use the dictionary as the local namespace
