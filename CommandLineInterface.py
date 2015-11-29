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

import os
from multiprocessing import *
from PUSService import *

class CommandLineInterface(Process):
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
        pass

    def __init__(self):
        # Inititalize this instance as a PUS service
        super(CommandLineInterface, self).__init__()

        # FIFOs for communication with the Ground Packet Router
        self.OBCToCLIFifo 		= open(path3, "rb")
        self.CLIToOBCFifo 		= open(path4, "rb")

if __name__ == '__main__':
    pass
