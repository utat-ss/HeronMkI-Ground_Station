"""
FILE_NAME:			FDIRService.py

AUTHOR:				Keenan Burnett

PURPOSE:			This class shall house the FDIR service and all related methods.

FILE REFERENCES:

LIBRARIES USED:		os, multiprocessing

SUPERCLASS:			PUSService

ABNORMAL TERMINATION CONDITIONS, ERROR AND WARNING MESSAGES: None yet.

ASSUMPTIONS, CONSTRAINTS, CONDITIONS: None.

NOTES:
					...
REQUIREMENTS:

DEVELOPMENT HISTORY:

11/17/2015			Created.

"""

import os
from multiprocessing import *
import PUSService

class FDIRService(PUSService):
	"""
	This class is meant to represent the PUS FDIR Service.
	"""
	@classmethod
	def run(self):
	"""
	@purpose:   Used to house the main program for the fdir service.
	@Note:		Since this class is a subclass of Process, when self.start() is executed on an 
				instance of this class, a process will be created with the contents of run() as the 
				main program.
	"""	


def __init__(self, path1, path2, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock, errorLock, day, hour, minute, second):
	# Inititalize this instance as a PUS service
	super(FDIRService, self).__init__(path1, path2, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock, errorLock, day, hour, minute, second)

if __name__ == '__main__':
	return
	