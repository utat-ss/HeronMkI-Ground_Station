"""
FILE_NAME:			CommandLineInterface.py

AUTHOR:				Keenan Burnett

PURPOSE:			This class shall house the Command Line Interface and all related methods.

FILE REFERENCES:

LIBRARIES USED:		os, multiprocessing

SUPERCLASS:			Process

ABNORMAL TERMINATION CONDITIONS, ERROR AND WARNING MESSAGES: None yet.

ASSUMPTIONS, CONSTRAINTS, CONDITIONS: None.

NOTES:
					...
REQUIREMENTS:

DEVELOPMENT HISTORY:

11/28/2015			Created.

"""

class CommandLineInterface():
    """
    This class is meant to represent the PUS FDIR Service.
    """
    OBCToCLIFifo = None
    CLIToOBCFifo = None
    processID    = 0x16

    @classmethod
    def run(cls):
        """
        @purpose:   Used to house the program for the command line interface.
        @Note:		Since this class is a subclass of Process, when self.start() is executed on an
                    instance of this class, a process will be created with the contents of run() as the
                    main program.
        """
        while 1:
            commandString = raw_input("Enter a command / command file")
            print("\nYou entered: %s\n" %commandString)
            if commandString == "kill":
                return

    def __init__(self, path1, path2):
        # FIFOs for communication with the Ground Packet Router
        self.GPRToCLIFifo 		= open(path1, "rb")
        self.CLIToFPRFifo 		= open(path2, "wb")

if __name__ == '__main__':
    CLI = CommandLineInterface("/fifos/GPRToCLI.fifo", "fifos/CLIToGPR.fifo")
    CLI.run()
