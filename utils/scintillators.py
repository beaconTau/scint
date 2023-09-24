"""Class for handling multiple scintillator instances at once"""

from utils.scintillator import Scintillator


class Scintillators():
    """
    Handles scintillator commands simultaneously for all scintillator channels given.
    An individual scintillator channel can also be used via the scints attribute.

    Parameters
    ----------
    number_of_scints : int
        The number of scintillator channels
    serial_ports : list or None
        If given, each element is assigned as the port in Serial for each scint channel
    baud_rate : int
        The baud rate for Serial connection.

    Attributes
    ----------
    count : int
        The total number of scint channels
    ports : list[str]
        A list containing the Serial port paths for each scint channel
    scints : list[Scintillator]
        A list containing the Scintillator instances corresponding to each channel. Can
        be used to access functions for a single scintillator channel.
    status : dict
        A dictionary containing the status of all channels
    
    Methods
    -------
    printStatus()
        Print a table sumarizing the status of the scintillators
    runMethod(method, *args, **kwargs)
        Run a Scintillator method for all scintillators. *args and **kwargs should be for the requested method.
    
    """

    def __init__(self, number_of_scints = 1, serial_ports = None, baud_rate = 9600):

        self.count = number_of_scints

        if serial_ports is None:
            serial_ports = [None]*number_of_scints
        self.ports = serial_ports
        assert len(serial_ports) == number_of_scints, "Mismatching number of given ports to given number of scintillators"

        self.scints = []
        for scint_i in range(number_of_scints):
            self.scints.append(Scintillator(scint_number=scint_i+1, serial_port=self.ports[scint_i], baud_rate=baud_rate))

    
    @property
    def status(self):
        """A dictionary of status parameters"""

        allStatusesDict = {}
        singleScintStatuses = []

        for scint in self.scints:
            singleScintStatuses.append(scint.getStatus())
        
        for key in singleScintStatuses[0]:
            allStatusesDict[key] = [singleScintStatuses[i][key] for i in range(self.count)]
        
        return allStatusesDict
        
    def printStatus(self):
        """Print a message outlining the status of all scints"""
        status_dict = self.status

        # formatting, keep track of longest names in each column
        customTab = " "*4
        tabLen = len(customTab)
        fixedMax = 15    # a fixed absolute max for column entries
        key0 = list(status_dict.keys())[0]
        maxChars = [len(key0)] + list(map(lambda x: len(str(x)), status_dict[key0]))  # for each col, get max length

        # iterate through entire dict
        for key in status_dict:
            maxChars[0] = max(maxChars[0], len(str(key)))
            for ind, element in enumerate(status_dict[key]):
                maxChars[ind+1] = max(maxChars[ind+1], len(str(element)))
        
        # limit max by overflow max
        for i in range(1, len(maxChars)):
            maxChars[i] = min(maxChars[i], fixedMax)

        # prepare status message string
        status_msg = "-+" + "-"*(maxChars[0]+tabLen*2-2) + '+'
        for maxChar in maxChars[1:]:
            status_msg += "-"*(maxChar+tabLen*2) + '+'
        status_msg += "-\n"
        for key in status_dict:
            cols = [key] + list(map(str, status_dict[key])) # full entry strings
            overflowRows = 0  # number of overflow rows
            sep = '|'     # sep between header and values
            entries = []    # character limited entry strings
            for ind, col in enumerate(cols):
                overflowRows = max(overflowRows, len(col) // (fixedMax+1))

                # get entries per column, truncate by max length
                entry = col[:maxChars[ind]]
                entries.append(entry + ' '*(maxChars[ind] - len(entry)))

            for row in range(overflowRows+1):
                status_msg += "{0}{1}{2}{3}{4}{5}\n".format(customTab, entries[0], customTab, sep, customTab, (customTab*2+' ').join(entries[1:]))
                entries[0] = ' '*maxChars[0]
                for i, col in enumerate(cols[1:]):
                    ind = i + 1
                    entry = col[maxChars[ind]*(row+1):maxChars[ind]*(row+2)]
                    entries[ind] = (entry + ' '*(maxChars[ind] - len(entry)))
            
            status_msg += "-+" + "-"*(maxChars[0]+tabLen*2-2) + '+'
            for maxChar in maxChars[1:]:
                status_msg += "-"*(maxChar+tabLen*2) + '+'
            status_msg += "-\n"
                
        print(status_msg)
    
    def runMethod(self, method, *args, **kwargs):
        """Run a Scintillator method for all scintillators"""
        for scint in self.scints:
            try:
                scintMethod = getattr(scint, method)
                scintMethod(*args, **kwargs)
                print(f"Command successfully sent to Scintillator {scint.scint_channel}")
            except AttributeError:
                raise AttributeError(f"Class 'Scintillator' does not have method '{method}'")
            except Exception as e:
                print(f'Scintillator {scint.scint_channel} raised an error: {e}')
                pass

    def help(self):
        """Display help message"""
        print(Scintillators.__doc__)
        print("\nYou can use the following methods from the Scintillator class in runMethod():\n")
        print(Scintillator.__doc__)