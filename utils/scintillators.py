"""Class for handling multiple scintillator instances at once"""

from utils.scintillator import Scintillator


def Scintillators():
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
    
    """

    def __init__(self, number_of_scints = 1, serial_ports = None, baud_rate = 9600):

        self.count = number_of_scints

        if serial_ports is None:
            serial_ports = [None]*number_of_scints
        self.ports = serial_ports
        assert len(serial_ports) == number_of_scints, "Mismatching number of given ports to given number of scintillators"

        self.scints = []
        for scint_i in range(number_of_scints):
            self.scints.append(Scintillator(scint_number=scint_i, serial_port=self.ports[scint_i], baud_rate=baud_rate))

    
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
        maxChars = []

        # initialize
        key0 = list(status_dict.keys())[0]
        maxChars.append(len(key0))
        for element in status_dict[key0]:
            maxChars.append(len(str(element)))

        # iterate through entire dict
        for key in status_dict:
            maxChars[0] = max(maxChars[0], len(key))
            for ind, element in enumerate(status_dict[key]):
                maxChars[ind+1] = max(maxChars[ind+1], len(str(element)))

        # prepare status message string
        status_msg = "-"*(sum(maxChars) + 8*(len(maxChars)-1)) + '\n'
        for key in status_dict:
            header = key + ' '*(maxChars[0] - len(key))
            cols = [str(element) + ' '*(maxChars[ind+1] - len(str(element))) for ind, element in enumerate(status_dict[key])]
            status_msg += "{0}\t-+-\t{1}\n".format(header, '\t'.join(cols))
        status_msg += "-"*(sum(maxChars) + 8*(len(maxChars)-1)) + '\n'

        print(status_msg)

    def help(self):
        """Display help message"""
        print(help(Scintillators))