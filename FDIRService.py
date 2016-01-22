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
from FifoObject import *

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
	path3				= None
	path4				= None
	path5				= None
	path6				= None
	path7				= None
	path8				= None

	@staticmethod
	def run1(self):
		"""
		@purpose:   Used to house the main program for the fdir service.
		@Note:		Since this class is a subclass of Process, when self.start() is executed on an
					instance of this class, a process will be created with the contents of run1() as the
					main program.
		"""
		print("The path in fdir run: %s" %str(self.p1))
		self.initializePUS(self)
		self.initialize()
		while 1:
			pass

	@classmethod
	def initialize(cls):
		# FIFOs for communication with the FDIR service
		cls.hktoFDIRFifo		= FifoObject(cls.path3, 0)
		cls.memtoFDIRFifo		= FifoObject(cls.path4, 0)
		cls.schedtoFDIRFifo		= FifoObject(cls.path5, 0)
		cls.FDIRtohkFifo		= FifoObject(cls.path6, 1)
		cls.FDIRtomemFifo		= FifoObject(cls.path7, 1)
		cls.FDIRtoschedFifo		= FifoObject(cls.path8, 1)
		return

	@staticmethod
	def initializePUS(self):
		# FIFOs Required for communication with the Ground Packet Router:
		self.fifoFromGPR			= FifoObject(self.p2, 0)
		self.fifoToGPR				= FifoObject(self.p1, 1)
		self.fifoToGPRPath			= self.p1
		self.wait					= 1
		self.fifoFromGPRPath		= self.p2
		return

	def __init__(self, path1, path2, path3, path4, path5, path6, path7, path8, tcLock, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock, errorLock, day, hour, minute, second):
		# Inititalize this instance as a PUS service
		super(FDIRService, self).__init__(path1, path2, path3, path4, tcLock, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock, errorLock, day, hour, minute, second)
		# self.processID = 0x10
		# self.serviceType = 3
		self.p1 = path1
		self.p2 = path2
		self.path3 = path3
		self.path4 = path4
		self.path5 = path5
		self.path6 = path6
		self.path7 = path7
		self.path8 = path8
		pID = os.fork()
		if pID:
			self.pID = pID
			return
		else:
			self.run1(self)

if __name__ == '__main__':
	pass
	