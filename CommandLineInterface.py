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
from FifoObject import *
import os

class CommandLineInterface():
    """
    This class is meant to represent the PUS FDIR Service.
    """
    GPRToCLIFifo    = None
    CLIToGPRFifo    = None
    processID       = 0x16

    @classmethod
    def run(cls):
        """
        @purpose:   Used to house the program for the command line interface.
        @Note:		Since this class is a subclass of Process, when self.start() is executed on an
                    instance of this class, a process will be created with the contents of run() as the
                    main program.
        """
        while 1:
            commandString = raw_input("Enter a command / command file: ")
            print("\nYou entered: %s\n" %commandString)
            if cls.execCommands(cls, commandString) < 0:
                return

    @classmethod
    def stop(cls):
        try:
            cls.GPRToCLIFifo.close()
            cls.CLIToGPRFifo.close()
        except:
            pass
        return

    @staticmethod
    def execCommands(self, command):
        # If the user entered the command "kill", then we should halt the operation of the CLI.
        if command == "kill":
            self.CLIToGPRFifo.writeCommandToFifo(command, 1)
            return -1
        # Otherwise, we can simply forward the command which was just received to the GPR.
        self.CLIToGPRFifo.writeCommandToFifo(command, 1)
        return 1

    def __init__(self, path1, path2):
        # FIFOs for communication with the Ground Packet Router
		# Inverse Parameter dictionary of the one shown above
        self.currentPath        = os.path.dirname(os.path.realpath(__file__))
        self.GPRToCLIFifo 		= FifoObject(self.currentPath + path1, 0)
        self.CLIToGPRFifo 		= FifoObject(self.currentPath + path2, 1)

if __name__ == '__main__':
    CLI = CommandLineInterface("/fifos/GPRToCLI.fifo", "/fifos/CLIToGPR.fifo")
    CLI.run()
    CLI.stop()
    print("THE COMMAND LINE INTERFACE HAS STOPPED")
