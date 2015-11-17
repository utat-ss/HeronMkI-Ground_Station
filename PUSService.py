"""
FILE_NAME:			PUSService.py

AUTHOR:				Keenan Burnett

PURPOSE:			This class shall house all the common methods and atributes of PUS services.

FILE REFERENCES:

LIBRARIES USED:		os, multiprocessing

ABNORMAL TERMINATION CONDITIONS, ERROR AND WARNING MESSAGES: None yet.

ASSUMPTIONS, CONSTRAINTS, CONDITIONS: None.

NOTES:
					...
REQUIREMENTS:

DEVELOPMENT HISTORY:
11/16/2015			Created.

"""

import os
from multiprocessing import *

class PUSService(Process):
	"""
	Superclass for all PUS services so that we can easily have some common methods and attributes.
	"""
@classmethod
def clearCurrentCommand(self):
	i = 0
	for i = 0 to (self.dataLength + 10):
		self.currentCommand[i] = 0
	return

@classmethod
def logEventReport(severity, reportID, param1, param0, day, hour, minute):
	"""
	@purpose: This method writes a event report to the event log.
	@param: severity: 1 = Normal, 2-4 = different levels of failure
	@param: reportID: Unique to the event report, ex: self.bitFlipDetected
	@param: param1,0: extra information sent from the satellite.
	"""
	# Event logs include time, which may have come from the satellite.
	self.eventLock.acquire()
	self.eventLog.write(str(day) + "/" + str(hour) + "/" + str(minute) + "\t,\t")
	self.eventLog.write(str(severity) + "\t,\t")
	self.eventLog.write(str(reportID) + "\t,\t")
	self.eventLog.write(str(param1) + "\t,\t")
	self.eventLog.write(str(param0) + "\t,\n")
	self.eventLock.release()

@classmethod
def printToCLI(stuff):
	self.cliLock.acquire()
	print(str(stuff))
	self.cliLock.release()

def __init__(self, path1, path2, eventPath, hkPath, eventLock, hkLock, cliLock, day, hour, minute, second, type):
	"""
	@purpose: Initialization method for the PUS service class.
	@param: path1: path to the file being used as a one-way fifo TO this PUS Service Instance
	@param: path2: path to the file being used as a one-way fifo FROM this PUS service Instance
	@param: day, hour, minute, second: Time to be set & subsequently updated by the Ground Packet Router
	"""
	# Global variables for each PUS Service Instance
	self.processID 				= None
	self.serviceType 			= None
	self.currentCommand 		= []
	# FIFOs Required for communication witht the Ground Packet Router:
	self.fifoToGPR				= open(path1, "wb")
	self.fifoFromGPR			= open(path1, "rb")
	# Definitions to clarify which services represent what
	self.dataLength 			= 137			# Length of the data section of PUS packets
	self.packetLength 			= 152			# Length (in bytes) of the entire PUS packet
	self.tcVerifyService 		= 1
	self.hkService 				= 3
	self.eventReportService 	= 5
	self.timeService			= 9
	self.kService				= 69
	# Definitions to clarify which service subtypes represent what
	# HOUSEKEEPING
	self.newHKDefinition 		= 1
	self.clearHKDefinition 		= 3
	self.enableParamReport		= 5
	self.disableParamReport 	= 6
	self.reportHKDefinitions	= 9
	self.hkDefinitionReport		= 10
	self.hkReport 				= 25
	# TIME
	self.updateReportFreq		= 1
	self.timeReport				= 2
	# MEMORY
	self.memoryLoadABS			= 2
	self.dumpRequestABS			= 5
	self.memoryDumpABS			= 6
	self.checkMemRequest		= 9
	self.memoryCheckABS			= 10
	#K-SERVICE
	self.addSchedule			= 1
	self.clearSchedule			= 2
	self.schedReportRequest		= 3
	self.schedReport 			= 4
	# Event Report ID
	self.kickComFromSchedule	= 1
	self.bitFlipDetected		= 2
	self.memoryWashFinished		= 3
	# Global Variables for Time
	self.abs_day				= day
	self.abs_hour				= hour
	self.abs_minute				= minute
	self.abs_second				= second
	# Files to be used for logging and housekeeping
	self.eventLog = open(eventPath, a+)
	self.hkLog = open(hkPath, a+)
	# Mutex Locks for accessing logs and the CLI
	self.eventLock = eventLock
	self.hkLock = hkLock
	self.cliLock = cliLock

if __name__ == '__main__':
	return
