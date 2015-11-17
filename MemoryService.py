"""
FILE_NAME:			MemoryService.py

AUTHOR:				Keenan Burnett

PURPOSE:			This class shall house the memory management PUS service and all related methods.

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

class MemoryService(PUSService):
	"""
	This class is meant to represent the PUS Memory Management Service.
	"""
	@classmethod
	def run(self):
		# This is where the actual program goes.


def __init__(self, path1, path2, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock, errorLock, day, hour, minute, second, type):
	# Inititalize this instance as a PUS service
	super(hkService, self).__init__(path1, path2, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock, errorLock, day, hour, minute, second)

if __name__ == '__main__':
	return
	