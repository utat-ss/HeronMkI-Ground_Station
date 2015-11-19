"""
FILE_NAME:			PUSService.py

AUTHOR:				Keenan Burnett

PURPOSE:			This class shall house all the common methods and atributes of PUS services.

FILE REFERENCES:

LIBRARIES USED:		os, multiprocessing

SUPERCLASS:			Process

ABNORMAL TERMINATION CONDITIONS, ERROR AND WARNING MESSAGES: None yet.

ASSUMPTIONS, CONSTRAINTS, CONDITIONS: None.

NOTES:
					...
REQUIREMENTS:

DEVELOPMENT HISTORY:
11/16/2015			Created.

11/17/2015			Added some more methods to this class for printing to logs.

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
	for i in range(0, (self.dataLength + 10)):
		self.currentCommand[i] = 0
	return

@classmethod
def logEventReport(self, severity, reportID, param1, param0, day, hour, minute, message=None):
	"""
	@purpose: This method writes a event report to the event log.
	@param: severity: 1 = Normal, 2-4 = different levels of failure
	@param: reportID: Unique to the event report, ex: self.bitFlipDetected
	@param: param1,0: extra information sent from the satellite.
	"""
	# Event logs include time, which may have come from the satellite.
	self.eventLock.acquire()
	self.hkLog.write("**************EVENTLOG START*****************\n")
	self.eventLog.write(str(day) + "/" + str(hour) + "/" + str(minute) + "\t,\t")
	self.eventLog.write(str(severity) + "\t,\t")
	self.eventLog.write(str(reportID) + "\t,\t")
	self.eventLog.write(str(param1) + "\t,\t")
	self.eventLog.write(str(param0) + "\t,\n")
	if(message is not None):
		self.evenLog.write(str(message) + "\n")
	self.hkLog.write("**************EVENTLOG STOP******************\n")
	self.eventLock.release()
	return

@classmethod
def logHKReport(*hkArray, day, hour, minute):
	self.hkLock.acquire()
	self.hkLog.write("***********HOUSEKEEPING START****************\n")
	self.hkLog.write(str(day) + "/" + str(hour) + "/" + str(minute) + "\n")
	for byte in hkArray:
		self.hkLog.write(str(byte) + "\n")
	self.hkLog.write("***********HOUSEKEEPING STOP*****************\n")
	self.hkLock.release()
	return

@classmethod
def logError(self, errorString):
	self.errorLock.acquire()
	self.errorLog.write("******************ERROR START****************\n")
	self.errorLog.write("ERROR: " + str(errorString) + " \n")
	self.errorLog.write("******************ERROR STOP****************\n")
	return

@classmethod
def printToCLI(self, stuff):
	self.cliLock.acquire()
	print(str(stuff))
	self.cliLock.release()
	return

def __init__(self, path1, path2, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock, errorLock, day, hour, minute, second):
	"""
	@purpose: Initialization method for the PUS service class.
	@param: path1: path to the file being used as a one-way fifo TO this PUS Service Instance
	@param: path2: path to the file being used as a one-way fifo FROM this PUS service Instance
	@param: day, hour, minute, second: Time to be set & subsequently updated by the Ground Packet Router
	"""
	# Global variables for each PUS Service Instance
	self.processID 				= 0
	self.serviceType 			= 0
	self.currentCommand 		= []
	# FIFOs Required for communication witht the Ground Packet Router:
	self.fifoToGPR				= open(path1, "wb")
	self.fifoToGPRPath			= path1
	self.fifoFromGPR			= open(path1, "rb")
	self.fifoFromGPRPath		= path2
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
	self.kickComFromSchedule	= 0x01
	self.bitFlipDetected		= 0x02
	self.memoryWashFinished		= 0x03
	self.hkgroundinitialized	= 0xFF
	self.memgroundinitialized	= 0xFE
	self.fdirgroundinitialized  = 0xFD
	# IDs for Communication:
	self.comsID					= 0x00
	self.epsID					= 0x01
	self.payID					= 0x02
	self.obcID					= 0x03
	self.hkTaskID				= 0x04
	self.dataTaskID				= 0x05
	self.timeTaskID				= 0x06
	self.comsTaskID				= 0x07
	self.epsTaskID				= 0x08
	self.payTaskID				= 0x09
	self.OBCPacketRouterID		= 0x0A
	self.schedulingTaskID		= 0x0B
	self.FDIRTaskID				= 0x0C
	self.WDResetTaskID			= 0x0D
	self.MemoryTaskID			= 0x0E
	self.HKGroundID				= 0x10
	self.TimeGroundID			= 0x11
	seld.MemGroundID			= 0x12
	self.GroundPacketRouterID	= 0x13
	# Parameter Names:
	self.parameters =
	{
		# Sensor Names
		0x01	: 			'PANELX_V',
		0x02	:			'PANELX_I',
		0x03	:			'PANELY_V',
		0x04	:			'PANELY_I',
		0x05	:			'BATTM_V',
		0x06	:			'BATT_V',
		0x07	:			'BATTIN_I',
		0x08	:			'BATTOUT_I',
		0x09	:			'BATT_TEMP',
		0x0A	:			'EPS_TEMP',
		0x0B	:			'COMS_V',
		0x0C	:			'COMS_I',
		0x0D	:			'PAY_V',
		0x0E	:			'PAY_I',
		0x0F	:			'OBC_V',
		0x10	:			'OBC_I',
		0x11	:			'BATT_I',
		0x12	:			'COMS_TEMP',
		0x13	:			'OBC_TEMP',
		0x14	:			'PAY_TEMP0',
		0x15	:			'PAY_TEMP1',
		0x16	:			'PAY_TEMP2',
		0x17	:			'PAY_TEMP3',
		0x18	:			'PAY_TEMP4',
		0x19	:			'PAY_HUM',
		0x1A	:			'PAY_PRESS',
		0x1B	:			'PAY_ACCEL',
		# Variable Names
		0xFF	:			'MPPTA',
		0xFE	:			'MPPTB',
		0xFD	:			'COMS_MODE',
		0xFC	:			'EPS_MODE',
		0xFB	:			'PAY_MODE',
		0xFA	:			'OBC_MODE',
		0xF9	:			'PAY_STATE',
		0xF8	:			'ABS_TIME_D',
		0xF7	:			'ABS_TIME_H',
		0xF6	:			'ABS_TIME_M',
		0xF5	:			'ABS_TIME_S',
		0xF4	:			'SPI_CHIP_1',
		0xF3	:			'SPI_CHIP_2',
		0xF2	:			'SPI_CHIP_3'
	}
	# Inverse Parameter dictionary of the one shown above
	self.invParameters = {v : k for k,v in self.parameters.items()}

	# Global Variables for Time
	self.abs_day				= day
	self.abs_hour				= hour
	self.abs_minute				= minute
	self.abs_second				= second
	# Files to be used for logging and housekeeping
	self.eventLog = open(eventPath, a+)						# Open the logs for appending
	self.hkLog = open(hkPath, a+)
	self.errorLog = open(errorPath, a+)
	# Mutex Locks for accessing logs and the CLI
	self.eventLock = eventLock
	self.hkLock = hkLock
	self.cliLock = cliLock
	self.errorLock = errorLock
	return

if __name__ == '__main__':
	return
