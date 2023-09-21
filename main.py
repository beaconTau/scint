import sys
from utils.scintillator import Scintillator
    
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

    scintillators = {}  # Use a dictionary to store instances
    for i in range(range_value):
        instance_name = f"scint_{i+1}"
        instance = Scintillator(scint_number = i+1)
        scintillators[instance_name] = instance  # Store instance in the dictionary
        print(f"Created instance: {instance_name}")

    import code
    code.interact(
        "Interactive Scintillator Control\nUse 'scint_[scint number]' objects for access, scint_[i].help() shows functions",
        local=scintillators)  # Use the dictionary as the local namespace
