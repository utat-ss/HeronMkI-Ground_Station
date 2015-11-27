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
from PUSService import *

class FDIRService(PUSService):
	"""
	This class is meant to represent the PUS FDIR Service.
	"""
	hktoFDIRFifo		= None
	memtoFDIRFifo 		= None
	schedtoFDIRFifo 	= None
	FDIRtohkFifo		= None
	FDIRtomemFifo		= None
	FDIRtoschedFifo		= None

	@classmethod
	def run(cla):
		"""
		@purpose:   Used to house the main program for the fdir service.
		@Note:		Since this class is a subclass of Process, when self.start() is executed on an
					instance of this class, a process will be created with the contents of run() as the
					main program.
		"""


	def __init__(self, path1, path2, path3, path4, path5, path6, path7, path8, tcLock, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock, errorLock, day, hour, minute, second):
		# Inititalize this instance as a PUS service
		super(FDIRService, self).__init__(path1, path2, tcLock, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock, errorLock, day, hour, minute, second)
		# self.processID = 0x10
		# self.serviceType = 3

		# FIFOs for communication with the FDIR service
		self.hktoFDIRFifo 		= open(path3, "rb")
		self.memtoFDIRFifo 		= open(path4, "rb")
		self.schedtoFDIRFifo 	= open(path5, "rb")
		self.FDIRtohkFifo		= open(path6, "wb")
		self.FDIRtomemFifo		= open(path7, "wb")
		self.FDIRtoschedFifo	= open(path8, "wb")

if __name__ == '__main__':
	pass
	