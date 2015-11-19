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
import PUSService

class schedulingService(PUSService):
	"""
	This class is meant to represent the PUS KService which manages scheduling
	as well as the miscelleaneous commands that can be made by the user
	which did not fall under any of the other standard PUS services.
	"""
	@classmethod
	def run(self):
		# This is where the actual program goes.


def __init__(self, path1, path2, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock, errorLock, day, hour, minute, second):
	# Inititalize this instance as a PUS service
	super(schedulingGroundService, self).__init__(path1, path2, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock, errorLock, day, hour, minute, second)

if __name__ == '__main__':
	return
	