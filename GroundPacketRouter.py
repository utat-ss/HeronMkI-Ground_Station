"""
FILE_NAME:			GroundPacketRouter.py

AUTHOR:				Keenan Burnett

PURPOSE:			This program is meant to start all other ground station software and
					act as the interface between subsidiary services and the CLI / transceiver.

FILE REFERENCES: 	PUSService.py, HKService.py, MemorySerice.py, FDIRService.py
	(We write to logs located in /events /errors and /housekeeping)

LIBRARIES USED:		os, datetime, multiprocessing

SUPERCLASS:			Process

ABNORMAL TERMINATION CONDITIONS, ERROR AND WARNING MESSAGES: None yet.

ASSUMPTIONS, CONSTRAINTS, CONDITIONS: None.

NOTES:
		- Need to update logEventReport so that it prints different stuff depending on the severity.

REQUIREMENTS:
	-Python 2.7
	-Linux Operating system (Ubuntu 14 was used)
	-This class should be called via a normal terminal in Linux
	-ex: python GrounPacketRouter.py
	-For the time being, we will have a serial connection to an Arduino Uno
	which will allow us to connect to the transceiver remotely.
	-We are using the CC1120 dev board as our "transceiver" for the groundstation

DEVELOPMENT HISTORY:
11/16/2015			Created.

11/17/2015			I am adding the decode_telemetry() function.

11/18/2015			Finished decodeTelemtry(), decodeTelemtry(), verifyTelemetry().

"""


import os
from PUSService import *
from HKService import *
from datetime import *
from multiprocessing import *

class groundPacketRouter(Process):
	"""
	Author: Keenan Burnett
	Acts as the main packet router for PUS packets to/from the groundstation
	as well as the CLI.
	Creates other processes which are used to manage PUS services.
	"""

@classmethod
def run(self):
	"""
	@purpose: Represents the main program for the ground packet router and Command-Line Interface.
	"""	
	self.initialize()

	while(1):
		# Check the transceiver for an incoming packet
		# Update FIFOs
		# Check FIFOs for a required action
		# Check the CLI for required action / print to the CLI
		# Update the current time stored in the processes.
		# Make sure all te subsidiary services are still running
def initialize(self):
	"""
	@purpose: 	-Handles all file creation such as logs, fifos.
				-Synchronizes time with the satellite.
				-Initializes mutex locks
				-Creates subsidiary services for: housekeeping, memory management, failure detection isolation & recovery (FDIR)
	"""	
	absTime = datetime.timedelta(0)	# Set the absolute time to zero. (for now)
	currentTime = datetime.date()

	self.clearCurrentCommand()

	"""Get the absolute time from the satellite and update ours."""

	# Create all the required FIFOs
	os.mkfifo("/fifos/hkToGPR.fifo")
	self.hkToGPRFifo = open("/fifos/hkToGPR.fifo", "rb")
	os.mkfifo("/fifos/GPRtohk.fifo")
	self.GPRTohkFifo = open("/fifos/GPRtohk.fifo", "wb")
	os.mkfifo("/fifos/memToGPR.fifo")
	self.memToGPRFifo = open("/fifos/memToGPR.fifo", "rb")
	os.mkfifo("/fifos/GPRtomem.fifo")
	self.GPRTomemFifo = open("/fifos/GPRtomem.fifo", "wb")
	os.mkfifo("/fifos/fdirToGPR.fifo")
	self.fdirToGPRFifo = open("/fifos/fdirToGPR.fifo", "rb")
	os.mkfifo("/fifos/GPRtofdir.fifo")
	self.GPRTofdirFifo = open("/fifos/GPRtofdir.fifo", "wb")
	os.mkfifo("/fifos/GPRTosched.fifo")
	self.GPRtoschedFifo = open("/fifos/GPRTosched.fifo")
	os.mkfifo("/fifos/schedToGPR.fifo")
	self.schedToGPRFifo = open("/fifos/schedToGPR.fifo")
	# Create all the files required for logging
	self.eventLog = None
	self.hkLog = None
	self.errorLog = None
	eventPath = "/events/eventLog.%s.%s" %currentTime.month, %currentTime.day
	if os.path.exists(eventPath):
		self.eventLog = open(eventPath, "rb+")
	else:
		self.eventLog = open(eventPath, "wb")
	hkPath = "/housekeeping/logs/hkLog.%s.%s" %currentTime.month, %currentTime.day
	if os.path.exists(hkPath):
		self.hkLog = open(hkPath, "rb+")
	else:
		self.hkLog = open(hkPath, "wb")
	errorPath = "/ground_errors/errorLog.%s.%s" %currentTime.month, %currentTime.day
	if os.path.exists(errorPath):
		self.errorLog = open(errorPath, "rb+")
	else:
		self.errorLog = open(errorPath, "wb")

	# Create Mutex locks for accessing logs and printing to the CLI.
	self.hkLock = Lock()
	self.eventLock = Lock()
	self.cliLock = Lock()
	self.errorLock = Lock()

	# Create all the required PUS Services
	self.HKGroundService 		= hkService("/fifos/hkToGPR.fifo", "/fifos/GPRtohk.fifo", eventPath, hkPath, errorPath, self.eventLock, self.hkLock, self.cliLock, self.errorLock,
												absTime.day, absTime.minute, absTime.minute, absTime.second)
	self.HKPID = self.HKGroundService.pid
	self.MemoryGroundService 	= MemoryService("/fifos/memToGPR.fifo", "/fifos/GPRtomem.fifo", eventPath, hkPath, errorPath, self.eventLock, self.hkLock, self.cliLock, self.errorLock,
												absTime.day, absTime.minute, absTime.minute, absTime.second)
	self.memPID = self.MemoryGroundService.pid
	self.FDIRGround 			= FDIRService("/fifos/fdirToGPR.fifo", "/fifos/GPRtofdir.fifo", eventPath, hkPath, errorPath, self.eventLock, self.hkLock, self.cliLock, self.errorLock,
												absTime.day, absTime.minute, absTime.minute, absTime.second)
	seld.FDIRPID = self.FDIRGround.pid
	self.schedulingGround		= schedulingService("/fifos/schedToGPR.fifo", "/fifos/GPRtosched.fifo", eventPath, hkPath, errorPath, self.eventLock, self.hkLock, self.cliLock, self.errorLock,
												absTime.day, absTime.minute, absTime.minute, absTime.second)

	return

def tcVerificationDecode(self):
	"""
	@purpose:   This method is used when the PUS packet which was received is a TC
				verification packet. 
				The intent here is to route the packet to the subsidiary service that
				it is intended for (TC Acceptance Report) OR to log the verification
				to the Event Log / Alert FDIR (TC Execution Report)
	"""	
	verificationAPID = 0
	verificationPacketID = currentCommand[135] << 8
	verificationPacketID += currentCommand[134]
	verificationPSC	= currentCommand[133] << 8
	verificationPSC += currentCommand[132]
	if(self.serviceTypeRx == 1):
		verificationAPID = currentCommand[135]
		currentCommand[146] = 1
		if(verificationAPID == self.hkTaskID):
			self.sendCurrentCommandToFifo(self.GPRTohkFifo)			# Send the TC Acceptance Report to the housekeeping service.
		if(verificationAPID == self.MemoryTaskID):
			self.sendCurrentCommandToFifo(self.GPRTomemFifo)
		if(verificationAPID == self.schedulingTaskID):
			self.sendCurrentCommandToFifo(self.GPRtoschedFifo)
		if(verificationAPID == self.FDIRGroundID):
			self.sendCurrentCommandToFifo(self.GPRTofdirFifo)
	if(self.serviceTypeRx == 2)
		self.logEventReport(2, self.TMExecutionFailed, 0, 0, "Telecommand Execution Failed. for PacketID: %s, PSC: %s" %str(verificationPacketID) % str(verificationPSC))
	return

# Each element of the tmToDecode array needs to be an integer
def decodeTelemetry(self):
	"""
	@purpose:   This method will decode the telemetry packet which was sent by the satellite
				(located in tmToDecode[]). It will either send the appropriate commands
				to the subsidiary services or it will act on the telemetry itself (if it is valid).
				For now, we will log all telemtry for safe-keeping / debugging.
	"""	
	if(!self.curentTmCount):
		return -1

	self.packetID = tmToDecode[151] << 8
	self.packetID |= tmToDecode[150]
	self.psc = tmToDecode[149] << 8
	self.psc |= tmToDecode[148]
	# Packet Header
	self.version1 			= (tmToDecode[151] & 0xE0) >> 5
	self.type1 				= (tmToDecode[151] & 0x10) >> 4
	self.dataFieldHeaderf 	= (tmToDecode[151] & 0x08) >> 3
	self.apid				= tmToDecode[150]
	self.sequenceFlags1		= (tmToDecode[149] & 0xC0) >> 6
	self.sequenceCount1		= tmToDecode[148]
	self.packetLengthRx		= tmToDecode[146] + 1
	# Data Field Header
	self.ccsdsFlag			= (tmToDecode[145] & 0x80) >> 7
	self.packetVersion		= (tmToDecode[145] & 0x70) >> 4
	self.ack				= tmToDecode[145] & 0x0F
	self.serviceTypeRx		= tmToDecode[144]
	self.serviceSubTypeRx	= tmToDecode[143]
	self.sourceID			= tmToDecode[142]
	# Received Checksum Value
	self.pec1 = tmToDecode[1] << 8
	self.pec1 |= tmToDecode[0]
	# Check that the packet error control is correct
	self.pec0 = self.fletcher16(tmToDecode, 2, 150)
	x = -1
	x = self.verifyTelemetry()

	if x < 0:
		return -1

	self.decodeTelemetryH()
	return

def decodeTelemetrH(self):
	"""
	@purpose:   Helper to decodeTelemetry, this method looks at self.serviceTypeRx and 
				self.serviceSubTypeRx of the telemetry packet stored in tmToDecode[] and
				performs the actual routing of messages and executing of required actions.
	"""	
	if(!self.curentTmCount):	# Method executed out of turn
		return -1

	self.clearCurrentCommand()
	for i in range(2, self.dataLength + 2):
		currentCommand[i]
	
	self.curentTmCount--

	currentCommand[140] = self.packetID >> 8
	currentCommand[139] = self.packetID & 0x000000FF
	currentCommand[138] = self.psc >> 8
	currentCommand[137] = self.psc & 0x000000FF

	if(self.serviceTypeRx == self.tcVerifyService):
		# If TC Acceptance verification, route to the corresponding service
		# Else if TC Execution verification, make a note of it in the event log.
	if(self.serviceTypeRx == self.hkService):
		currentCommand[146] = self.serviceSubTypeRx
		currentCommand[145] = currentCommand[135]
		currentCommand[144] = currentCommand[134]
		self.sendCurrentCommandToFifo(self.GPRTohkFifo)
	if(self.serviceTypeRx == self.timeService):
		# Synch Time With satellite here.
	if(self.serviceTypeRx == self.kService):
		currentCommand[146] = self.serviceSubTypeRx
		self.sendCurrentCommandToFifo(self.GPRToschedFifo)
	if(self.serviceTypeRx == self.eventReportService):
		# Store the received event in the eventLog, check if the event was an error.
	if(self.serviceTypeRx == self.memService):
		currentCommand[146] == self.memService
		self.sendCurrentCommandToFifo(self.GPRTomemFifo)
	if(self.serviceTypeRx == self.fdirService):
		currentCommand[145] == fdirService
		self.sendCurrentCommandToFifo(self.GPRTofdirFifo)
	return

def sendCurrentCommandToFifo(self, fifo):
	tempString = None
	fifo.write("START\n")
	for i in range(0, self.dataLength + 10):
		tempString + str(currentCommand[i]) + "\n"
		fifo.write(tempString)
	fifo.write("STOP\n")
	return

def verifyTelemetry(self):
	"""
	@purpose:   This method is used to determine whether or not the TM packet which 
				was received is valid for decoding.
	@NOTE:		All telemetry, even telemetry that fails here is stored in memory under
				/telemetry
	@return:	-1 = packet failed the verification, 1 = good to decode
	"""	
	if(!self.curentTmCount):	# Method executed out of turn
		return -1

	if(self.packetLengthRx != self.packetLength):
		self.printToCLI("Incoming Telemetry Packet Failed\n")
		self.logError("TM PacketID: %s, PSC: %s had an incorrect packet length" %str(self.packetID) %str(self.psc))
		return -1
	
	if(self.pec0 != self.pec1)
		self.printToCLI("Incoming Telemetry Packet Failed\n")
		self.logError("TM PacketID: %s, PSC: %s failed the checksum test. PEC1: %s, PEC0: %s" 
						%str(self.packetID), %str(self.psc), %str(self.pec1), %str(self.pec0))
		return -1
	
	if((self.serviceTypeRx != 1) && (self.serviceTypeRx != 3) && (self.serviceTypeRx != 5) 
	&& (self.serviceTypeRx != 6) && (self.serviceTypeRx != 9) && (self.serviceTypeRx != 69)):
		self.printToCLI("Incoming Telemetry Packet Failed\n")
		self.logError("TM PacketID: %s, PSC: %s had an incorrect serviceType" %str(self.packetID) %str(self.psc))
		return -1

	if(self.serviceTypeRx == self.tcVerifyService):
		if((self.serviceSubTypeRx != 1) && (self.serviceSubTypeRx != 2) && (self.serviceSubTypeRx != 7) && (self.serviceSubTypeRx != 8)):
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an incorrect serviceSubType" %str(self.packetID) %str(self.psc))
			return -1

	if(self.serviceTypeRx == self.hkService):
		if((self.serviceSubTypeRx != 10) && (self.serviceSubTypeRx != 12) && (self.serviceSubTypeRx != 25) && (self.serviceSubTypeRx != 26)):
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an incorrect serviceSubType" %str(self.packetID) %str(self.psc))
			return -1
		if((self.apid != self.HKGroundID) && (self.apid != self.FDIR)):
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an invalid APID" %str(self.packetID) %str(self.psc))
			return -1

	if(self.serviceTypeRx == self.memService):
		if((self.serviceSubTypeRx != 6) && (self.serviceSubTypeRx != 10)):
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an incorrect serviceSubType" %str(self.packetID) %str(self.psc))
			return -1
		if(self.apid != self.MemGroundID)
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an invalid APID" %str(self.packetID) %str(self.psc))
			return -1
		address = tmToDecode[137] << 24
		address += tmToDecode[136] << 16
		address += tmToDecode[135] << 8
		address += tmToDecode[134]

		if(tmToDecode[138] > 1):
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an incorrect memoryID" %str(self.packetID) %str(self.psc))
			return -1
		if((tmToDecode[138] == 1) && (address > 0xFFFFF)):
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an invalid address" %str(self.packetID) %str(self.psc))
			return -1

	if(self.serviceTypeRx == self.timeService):
		if((self.serviceSubTypeRx != 2)):
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an incorrect serviceSubType" %str(self.packetID) %str(self.psc))
			return -1
		if(self.apid != self.TimeGroundID):
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an invalid APID" %str(self.packetID) %str(self.psc))
			return -1
	if(self.serviceTypeRx == self.kService):
		length = tmToDecode[136]
		if((self.serviceSubTypeRx != 4)):
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an incorrect serviceSubType" %str(self.packetID) %str(self.psc))
			return -1
		if(self.apid != self.schedGroundID):
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an invalid APID" %str(self.packetID) %str(self.psc))
			return -1

	if(self.version1 != 1)
		self.printToCLI("Incoming Telemetry Packet Failed\n")
		self.logError("TM PacketID: %s, PSC: %s had an incorrect version" %str(self.packetID) %str(self.psc))
		return -1
	if(self.ccsdsFlag != 1)
		self.printToCLI("Incoming Telemetry Packet Failed\n")
		self.logError("TM PacketID: %s, PSC: %s had an incorrect ccsdsFlag" %str(self.packetID) %str(self.psc))
		return -1
	if(self.packetVersion != 1)
		self.printToCLI("Incoming Telemetry Packet Failed\n")
		self.logError("TM PacketID: %s, PSC: %s had an incorrect packet version" %str(self.packetID) %str(self.psc))
		return -1

	self.logEventReport(1, self.incomTMSuccess, 0, 0, "Incoming Telemetry Packet Succeeded")
	return 1


def fletcher16(self, *data, offset, count):
	"""
	@purpose:   This method is to be used to compute a 16-bit checksum in the exact same
				manner that it is computed on the satellite.
	@param: 	*data: int array of the data you want to run the checksum on.
	@param:		offset: Where in the array you would like to start running the checksum on.
	@param:		count: How many elements (ints) of the array to include in the checksum.
	@NOTE:		IMPORTANT: even though *data is an int array, each integer is only using
				the last 8 bits (since this is meant to be used on incoming PUS packets)
				Hence, you should create a new method if this is not the functionality you desire.

	@return 	(int) The desired checksum is returned (only the lower 16 bits are used)
	"""	
	sum1 = 0
	sum2 = 0
	num = 0
	i = 0
	for i in range(offset, offset + count):
		num = data[i] & int(0x000000FF)
		sum1 = (sum1 + num) % 255
		sum2 = (sum2 + sum1) % 255
	return (sum2 << 8) | sum1

@classmethod
def stop(self):
	# Close all the files which were opened
	self.hkToGPRFifo.close()
	self.GPRTohkFifo.close()
	self.memToGPRFifo.close()
	self.GPRTomemFifo.close()
	self.fdirToGPRFifo.close()
	self.GPRTofdirFifo.close()

	# Kill all the children
	if(self.HKGroundService.is_alive()):
		self.HKGroundService.terminate()
	if(self.MemoryGroundService.is_alive()):
		self.MemoryGroundService.terminate()
	if(self.FDIRGround.is_alive()):
		self.FDIRGround.terminate()
	if(self.schedulingGround.as_alive()):
		self.schedulingGround.terminate()

	# Delete all the FIFO files that were created
	os.remove("/fifos/hkToGPR.fifo")
	os.remove("/fifos/GPRtohk.fifo")
	os.remove("/fifos/memToGPR.fifo")
	os.remove("/fifos/GPRtomem.fifo")
	os.remove("/fifos/GPRtomem.fifo")
	os.remove("/fifos/fdirToGPR.fifo")
	os.remove("/fifos/GPRtofdir.fifo")
	os.remove("/fifos/GPRTosched.fifo")
	os.remove("/fifos/schedToGPR.fifo")
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
	self.eventLock.acquire()
	self.hkLog.write("**************EVENTLOG START*****************\n")
	self.eventLog.write(str(self.currentTime.day) + "/" + str(self.currentTime.hour) + "/" + str(self.currentTime.minute) + "\t,\t")
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

@classmethod
def clearCurrentCommand(self):
	i = 0
	for i in range(0, (self.dataLength + 10)):
		self.currentCommand[i] = 0
	return

def __init__(self):
	"""
	@purpose: Initialization method for the Ground Packet Router Class
	"""
	# Global variables for each PUS Service Instance
	self.processID 				= None
	self.serviceType 			= None
	self.currentCommand 		= []
	# Definitions to clarify which services represent what
	self.dataLength 			= 137			# Length of the data section of PUS packets
	self.packetLength 			= 152			# Length (in bytes) of the entire PUS packet
	self.tcVerifyService 		= 1
	self.hkService 				= 3
	self.eventReportService 	= 5
	self.memService 			= 6
	self.timeService			= 9
	self.kService				= 69
	self.fdirService 			= 70
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
	self.hkgroundinitialized	= 0xFF
	self.memgroundinitialized	= 0xFE
	self.fdirgroundinitialized  = 0xFD
	self.incomTMSuccess			= 0xFC
	self.TMExecutionFailed		= 0xFB
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
	self.FDIRGroundID			= 0x14
	self.schedGroundID		= 0x15
	# Global Variables for Time
	self.abs_day				= day
	self.abs_hour				= hour
	self.abs_minute				= minute
	self.abs_second				= second

if __name__ == '__main__':
	x = groundPacketRouter()
	x.start()
	x.terminate()
