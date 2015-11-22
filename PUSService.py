"""
FILE_NAME:			PUSService.py

AUTHOR:				Keenan Burnett

PURPOSE:			This class shall house all the common methods and atributes of PUS services.

FILE REFERENCES:

LIBRARIES USED:		os, multiprocessing, datetime

SUPERCLASS:			Process

ABNORMAL TERMINATION CONDITIONS, ERROR AND WARNING MESSAGES: None yet.

ASSUMPTIONS, CONSTRAINTS, CONDITIONS: None.

NOTES:
					...
REQUIREMENTS:

DEVELOPMENT HISTORY:
11/16/2015			Created.

11/17/2015			Added some more methods to this class for printing to logs.

11/20/2015			Added a couple class methods for sending and receiving commands
					from a FIFO.
"""

import os
from multiprocessing import *
from datetime import *

class PUSService(Process):
	"""
	Superclass for all PUS services so that we can easily have some common methods and attributes.
	"""
	# Attributes for each PUS Service Instance
	processID 				= 0
	serviceType 			= 0
	currentCommand 			= []
	# FIFOs Required for communication with the Ground Packet Router:
	fifoToGPR				= None
	fifoToGPRPath			= None
	fifoFromGPR				= None
	fifoFromGPRPath			= None
	# Definitions to clarify which services represent what
	dataLength 				= 137			# Length of the data section of PUS packets
	packetLength 			= 152			# Length (in bytes) of the entire PUS packet
	tcVerifyService 		= 1
	hkService 				= 3
	eventReportService 		= 5
	memService 				= 6
	timeService				= 9
	kService				= 69
	fdirService 			= 70
	# Definitions to clarify which service subtypes represent what
	# HOUSEKEEPING
	newHKDefinition 		= 1
	clearHKDefinition 		= 3
	enableParamReport		= 5
	disableParamReport 		= 6
	reportHKDefinitions		= 9
	hkDefinitionReport		= 10
	hkReport 				= 25
	# TIME
	updateReportFreq		= 1
	timeReport				= 2
	# MEMORY
	memoryLoadABS			= 2
	dumpRequestABS			= 5
	memoryDumpABS			= 6
	checkMemRequest			= 9
	memoryCheckABS			= 10
	#K-SERVICE
	addSchedule				= 1
	clearSchedule			= 2
	schedReportRequest		= 3
	schedReport 			= 4
	# Event Report ID
	kickComFromSchedule		= 0x01
	bitFlipDetected			= 0x02
	memoryWashFinished		= 0x03
	hkgroundinitialized		= 0xFF
	memgroundinitialized	= 0xFE
	fdirgroundinitialized  	= 0xFD
	incomTMSuccess			= 0xFC
	TMExecutionFailed		= 0xFB
	timeReportReceived		= 0xFA
	timeOutOfSync			= 0xF9
	hkParamIncorrect		= 0xF8
	hkIntervalIncorrect		= 0xF7
	hkNumParamsIncorrect	= 0xF6
	loadingFileToSat		= 0xF5
	loadOperatonFailed		= 0xF4
	loadCompleted			= 0xF3
	dumpPacketWrong			= 0xF2
	# IDs for Communication:
	comsID					= 0x00
	epsID					= 0x01
	payID					= 0x02
	obcID					= 0x03
	hkTaskID				= 0x04
	dataTaskID				= 0x05
	timeTaskID				= 0x06
	comsTaskID				= 0x07
	epsTaskID				= 0x08
	payTaskID				= 0x09
	OBCPacketRouterID		= 0x0A
	schedulingTaskID		= 0x0B
	FDIRTaskID				= 0x0C
	WDResetTaskID			= 0x0D
	MemoryTaskID			= 0x0E
	HKGroundID				= 0x10
	TimeGroundID			= 0x11
	MemGroundID				= 0x12
	GroundPacketRouterID	= 0x13
	# Parameter Names:
	parameters ={
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
	invParameters 			= None
	# Global Variables for Time
	absTime 				= datetime.timedelta(0)
	# Files to be used for logging and housekeeping
	eventLog 				= None
	hkLog 					= None
	errorLog 				= None
	# Mutex Locks for accessing logs and the CLI
	eventLock 				= None
	hkLock 					= None
	cliLock 				= None
	errorLock 				= None
	tcLock 					= None
	# TC Verification Attribute used for letting the services know when a TC verification was received.
	tcAcceptVerification = 0			# 0 = None received, should be cleared by the service.
	tcExecuteVerification = 0

	@classmethod
	def clearCurrentCommand(self):
		"""
		@purpose:   Clears the array currentCommand[]
		"""
		i = 0
		for i in range(0, (self.dataLength + 10)):
			self.currentCommand[i] = 0
		return

	@classmethod
	def logEventReport(self, severity, reportID, param1, param0, message=None):
		"""
		@purpose: This method writes a event report to the event log.
		@param: severity: 1 = Normal, 2-4 = different levels of failure
		@param: reportID: Unique to the event report, ex: self.bitFlipDetected
		@param: param1,0: extra information sent from the satellite.
		"""
		# Event logs include time, which may have come from the satellite.
		tempString  = None
		if severity == 1:
			tempString = "NORMAL REPORT (SEV 1)\t"
		if severity == 2:
			tempString = "ERROR  REPORT (SEV 2)\t"
		if severity == 3:
			tempString = "ERROR  REPORT (SEV 3)\t"
		if severity == 4:
			tempString = "ERROR  REPORT (SEV 4)\t"
		self.eventLock.acquire()
		self.eventLog.write(tempString)
		self.eventLog.write(str(self.absTime.day) + "/" + str(self.absTime.hour) + "/" + str(self.absTime.minute) + "\t,\t")
		self.eventLog.write(str(severity) + "\t,\t")
		self.eventLog.write(str(reportID) + "\t,\t")
		self.eventLog.write(str(param1) + "\t,\t")
		self.eventLog.write(str(param0) + "\t,\t")
		if(message is not None):
			self.eventLog.write(str(message) + "\n")
		if(message is None):
			self.eventLog.write("\n")
		self.eventLock.release()
		return

	@classmethod
	def logHKReport(self, *hkArray):
		"""
		@purpose:   Used to log the housekeeping report which was received.
		@Note:		Contains a mutex lock for exclusive access.
		@Note:		Housekeeping reports are created in a manner that is more convenient
					for excel or Matlab to parse but not really that great for human consumption.
		"""
		self.hkLock.acquire()
		self.hkLog.write("HKLOG:\t")
		self.hkLog.write(str(self.absTime.day) + "/" + str(self.absTime.day) + "/" + str(self.absTime.day) + "\t,\t")
		for byte in hkArray:
			byte = byte & 0x000000FF
			self.hkLog.write(str(byte) + "\t,\t")
		self.hkLog.write("\n")
		self.hkLock.release()
		return

	@classmethod
	def logError(self, errorString):
		"""
		@purpose:   Used to log an error report (ground errors), contains a mutex lock for exclusive access.
		"""
		self.errorLock.acquire()
		self.errorLog.write("******************ERROR START****************\n")
		self.errorLog.write("ERROR: " + str(errorString) + " \n")
		self.errorLog.write("******************ERROR STOP****************\n")
		return

	@classmethod
	def printToCLI(self, stuff):
		"""
		@purpose:   Used to print something to the CLI, contains a mutex lock for exclusive access.
		"""
		self.cliLock.acquire()
		print(str(stuff))
		self.cliLock.release()
		return

	@classmethod
	def sendCurrentCommandToFifo(self, fifo):
		"""
		@purpose:   This method is takes what is contained in currentCommand[] and
		then place it in the given fifo "fifo".
		@Note: We use a "START\n" code and "STOP\n" code to indicate where commands stop and start.
		@Note: Each subsequent byte is then placed in the fifo followed by a newline character.
		"""
		fifo.write("START\n")
		for i in range(0, self.dataLength + 10):
			tempString = str(self.currentCommand[i]) + "\n"
			fifo.write(tempString)
		fifo.write("STOP\n")
		return

	@classmethod
	def receiveCommandFromFifo(self, fifo):
		"""
		@purpose:   This method takes a command from the the fifo "fifo" which should have a
		length of 147 bytes & places it into the array self.currentCommand[].
		@Note: We use a "START\n" code and "STOP\n" code to indicate where commands stop and start.
		"""
		i = 0
		if(os.path.getsize(fifo) > 152):
			i = 0
			if(self.fifoFromGPR.readline() == "START\n"):
				# Start reading in the command.
				newString = fifo.readline()
				newString = newString.rstrip()
				while((newString != "STOP") and (i < (self.dataLength + 11))):
					self.currentCommand[i] = int(newString)
					newString = self.fifoFromGPR.readline()
					newString = newString.rstrip()
					i += 1
		return

	def __init__(self, path1, path2, tcLock, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock, errorLock, day, hour, minute, second):
		"""
		@purpose: Initialization method for the PUS service class.
		@param: path1: path to the file being used as a one-way fifo TO this PUS Service Instance
		@param: path2: path to the file being used as a one-way fifo FROM this PUS service Instance
		@param: day, hour, minute, second: Time to be set & subsequently updated by the Ground Packet Router
		"""
		super(PUSService, self).__init__()					# Initialize self as a process

		# FIFOs Required for communication with the Ground Packet Router:
		self.fifoToGPR				= open(path1, "wb")
		self.fifoToGPRPath			= path1
		self.fifoFromGPR			= open(path1, "rb")
		self.fifoFromGPRPath		= path2
		# Inverse Parameter dictionary of the one shown above
		self.invParameters = {v : k for k,v in self.parameters.items()}

		# Global Variables for Time
		self.absTime 					= datetime.timedelta(0)
		self.absTime.day				= day
		self.absTime.day				= hour
		self.absTime.minute				= minute
		self.absTime.second				= second
		# Files to be used for logging and housekeeping
		self.eventLog = open(eventPath, "a+")						# Open the logs for appending
		self.hkLog = open(hkPath, "a+")
		self.errorLog = open(errorPath, "a+")
		# Mutex Locks for accessing logs and the CLI
		self.eventLock = eventLock
		self.hkLock = hkLock
		self.cliLock = cliLock
		self.errorLock = errorLock
		self.tcLock = tcLock
		# TC Verification Attribute used for letting the services know when a TC verification was received.
		self.tcAcceptVerification = 0			# 0 = None received, should be cleared by the service.
		self.tcExecuteVerification = 0
		return

if __name__ == '__main__':
	pass

