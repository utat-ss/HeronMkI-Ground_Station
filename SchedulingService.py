"""
FILE_NAME:			SchedulingService.py

AUTHOR:				Keenan Burnett

PURPOSE:			This class shall house the KService PUS service and all related methods.

FILE REFERENCES:

LIBRARIES USED:		os, multiprocessing

SUPERCLASS:			PUSService

ABNORMAL TERMINATION CONDITIONS, ERROR AND WARNING MESSAGES: None yet.

ASSUMPTIONS, CONSTRAINTS, CONDITIONS: None.

NOTES:
					...
REQUIREMENTS:

DEVELOPMENT HISTORY:

11/18/2015			Created.

"""

import os
from multiprocessing import *
from PUSService import *

class schedulingService(PUSService):
	"""
	This class is meant to represent the PUS KService which manages scheduling
	as well as the miscelleaneous commands that can be made by the user
	which did not fall under any of the other standard PUS services.
	"""
	@classmethod
	def run(self):
		"""
		@purpose:   Used to house the main program for the scheduling service.
		@Note:		Since this class is a subclass of Process, when self.start() is executed on an
					instance of this class, a process will be created with the contents of run() as the
					main program.
		"""

def __init__(self, path1, path2, path3, path4, tcLock, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock,
			 			errorLock, day, hour, minute, second):
	# Inititalize this instance as a PUS service
	super(schedulingService, self).__init__(path1, path2, tcLock, eventPath, hkPath, errorPath, eventLock, hkLock,
						cliLock, errorLock, day, hour, minute, second)
	# self.processID = 0x10
	# self.serviceType = 3
	# self.currentHK[]
	# self.hkDefinition0[]
	# self.hkDefinition1[]
	# self.currentHKDefinition[]
	# self.currenthkdefinitionf = 0
	# self.collectionInterval0 = 30	# Housekeeping colleciton interval in minutes.
	# self.collectionInterval1 = 30
	# self.numParameters0 = 41
	# self.numSensors0 = 27
	# self.numVars0 = 14
	# self.numParameters1 = 41
	# self.numSensors1 = 27
	# self.numVars1 = 14

	# FIFOs for communication with the FDIR service
	self.fifotoFDIR = open(path3, "wb")
	self.fifofromFDIR = open(path4, "rb")

if __name__ == '__main__':
	pass
	