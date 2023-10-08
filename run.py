"""
Usage:
python3 run.py [scint_number] [command] [command_args]

For all scints, scint_number = 'all', otherwise 1-4

Runs scintillator code.
Uses a command to control all scints simultaneously, or a single scint.
"""

import sys
from utils.scintillators import Scintillators
from utils.scintillator import Scintillator

# for interactive
import code
    
if __name__ == "__main__":
    # Check if an argument is provided
    if len(sys.argv) < 3:
        help_msg = "Run a command for all scints or a single scint.\n\nUsage:\npython3 run.py [scint_number] [command] [command args]\n\nFor all scints, scint_number = 'all', otherwise 1-4\n\nList of commands:\n-----------------\nIf all scints:\n    printStatus()\n\tPrint a table sumarizing the status of all scintillators\n\nAll or Single scint:"+Scintillator.__doc__.split('-------')[-1]
        print(help_msg)
        sys.exit(1)

    scint_num = sys.argv[1]
    cmd = sys.argv[2]
    cmd_args = sys.argv[3:]

    if scint_num == 'all':
        # do cmd with all scints
        scint = Scintillators(number_of_scints=4)
        scint.runMethod(cmd, *cmd_args)
    elif int(scint_num) in [1,2,3,4]:
        # do cmd with scint int(scint_num)
        scint = Scintillator(scint_number=int(scint_num))
        try:
            scintMethod = getattr(scint, cmd)
            scintMethod(*cmd_args)
            print(f"Command successfully sent to Scintillator {scint.scint_channel}")
            sys.exit(1)
        except AttributeError:
            raise AttributeError(f"Class 'Scintillator' does not have command '{cmd}'")
        except Exception as e:
            print(f'Scintillator {scint.scint_channel} raised an error: {e}')
            sys.exit(1)
    else:
        raise ValueError('scint_number invalid')
