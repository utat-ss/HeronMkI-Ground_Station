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
		# Check the transceiver for an incoming packet THIS NEEDS TO PUT INCOMING TELEMETRY
		decodeTelemetry()
		# Check FIFOs for a required action
		# Check the CLI for required action
		updateServiceTime()
		# Make sure all te subsidiary services are still running
def initialize(self):
	"""
	@purpose: 	-Handles all file creation such as logs, fifos.
				-Synchronizes time with the satellite.
				-Initializes mutex locks
				-Creates subsidiary services for: housekeeping, memory management, failure detection isolation & recovery (FDIR)
	"""	
	self.absTime = datetime.timedelta(0)	# Set the absolute time to zero. (for now)
	self.oldAbsTime = self.absTime
	self.currentTime = datetime.date()

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
	self.hkDefLog = None
	self.errorLog = None
	eventPath = "/events/eventLog%s%s.csv" %currentTime.month, %currentTime.day
	if os.path.exists(eventPath):
		self.eventLog = open(eventPath, "rb+")
	else:
		self.eventLog = open(eventPath, "wb")
	hkPath = "/housekeeping/logs/hkLog%s%s.csv" %currentTime.month, %currentTime.day
	if os.path.exists(hkPath):
		self.hkLog = open(hkPath, "rb+")
	else:
		self.hkLog = open(hkPath, "wb")
	hkDefPath = "/housekeeping/logs/hkDefLog%s%s.txt" %currentTime.month, %currentTime.day
	if os.path.exists(hkDefPath):
		self.hkDefLog = open(hkDefPath, "rb+")
	else:
		self.hkDefLog  = open(hkDefPath, "wb")
	errorPath = "/ground_errors/errorLog%s%s.txt" %currentTime.month, %currentTime.day
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
												absTime.day, absTime.minute, absTime.minute, absTime.second, hkDefPath)
	self.HKPID = self.HKGroundService.pid
	self.MemoryGroundService 	= MemoryService("/fifos/memToGPR.fifo", "/fifos/GPRtomem.fifo", eventPath, hkPath, errorPath, self.eventLock, self.hkLock, self.cliLock, self.errorLock,
												absTime.day, absTime.minute, absTime.minute, absTime.second)
	self.memPID = self.MemoryGroundService.pid
	self.FDIRGround 			= FDIRService("/fifos/fdirToGPR.fifo", "/fifos/GPRtofdir.fifo", eventPath, hkPath, errorPath, self.eventLock, self.hkLock, self.cliLock, self.errorLock,
												absTime.day, absTime.minute, absTime.minute, absTime.second)
	self.FDIRPID = self.FDIRGround.pid
	self.schedulingGround		= schedulingService("/fifos/schedToGPR.fifo", "/fifos/GPRtosched.fifo", eventPath, hkPath, errorPath, self.eventLock, self.hkLock, self.cliLock, self.errorLock,
												absTime.day, absTime.minute, absTime.minute, absTime.second)
	self.schedPID = self.schedulingGround.pid
	return

def updateServiceTime():
	"""
	@purpose:   Whenever possible, GroundPacketRouter should update the time stored in the subsidiary services 
				so that everything stays in sync.
	"""	
	self.HKGroundService.absTime = self.absTime
	self.MemoryGroundService.absTime = self.absTime
	self.FDIRGround.absTime = self.absTime
	seld.schedulingGround.absTime = self.absTime
	return

def tcVerificationDecode():
	"""
	@purpose:   This function is used when the PUS packet which was received is a TC
				verification packet. 
				The intent here is to route the packet to the subsidiary service that
				it is intended for (TC Acceptance Report) OR to log the verification
				to the Event Log / Alert FDIR (TC Execution Report)
	"""	
	verificationAPID = 0
	verificationPacketID = self.currentCommand[135] << 8
	verificationPacketID += self.currentCommand[134]
	verificationPSC	= self.currentCommand[133] << 8
	verificationPSC += self.currentCommand[132]
	if(self.serviceTypeRx == 1):
		verificationAPID = self.currentCommand[135]
		self.currentCommand[146] = 1
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
		self.currentCommand[146] = self.TMExecutionFailed
		self.currentCommand[146] = 3
		self.sendCurrentCommandToFifo(self.GPRTofdirFifo)		# Alert FDIR that something is going wrong.
	return

# Each element of the tmToDecode array needs to be an integer
def decodeTelemetry():
	"""
	@purpose:   This method will decode the telemetry packet which was sent by the satellite
				(located in tmToDecode[]). It will either send the appropriate commands
				to the subsidiary services or it will act on the telemetry itself (if it is valid).
				For now, we will log all telemtry for safe-keeping / debugging.
	"""	
	if(!self.currentTmCount):
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
	self.pec0 = fletcher16(tmToDecode, 2, 150)
	x = -1
	x = verifyTelemetry()

	if x < 0:
		return -1

	decodeTelemetryH()
	return

def decodeTelemetryH():
	"""
	@purpose:   Helper to decodeTelemetry, this method looks at self.serviceTypeRx and 
				self.serviceSubTypeRx of the telemetry packet stored in tmToDecode[] and
				performs the actual routing of messages and executing of required actions.
	"""	
	if(!self.currentTmCount):	# Method executed out of turn
		return -1

	self.clearCurrentCommand()
	for i in range(2, self.dataLength + 2):
		self.currentCommand[i - 2] = self.tmToDecode[i]
	
	self.currentTmCount--

	self.currentCommand[140] = self.packetID >> 8
	self.currentCommand[139] = self.packetID & 0x000000FF
	self.currentCommand[138] = self.psc >> 8
	self.currentCommand[137] = self.psc & 0x000000FF

	if(self.serviceTypeRx == self.tcVerifyService):
		tcVerificationDecode()
	if(self.serviceTypeRx == self.hkService):
		self.currentCommand[146] = self.serviceSubTypeRx
		self.currentCommand[145] = self.currentCommand[135]
		self.currentCommand[144] = self.currentCommand[134]
		self.sendCurrentCommandToFifo(self.GPRTohkFifo)
	if(self.serviceTypeRx == self.timeService):
		syncWithIncomingTime()
	if(self.serviceTypeRx == self.kService):
		self.currentCommand[146] = self.serviceSubTypeRx
		self.sendCurrentCommandToFifo(self.GPRToschedFifo)
	if(self.serviceTypeRx == self.eventReportService):
		checkIncomingEventReport()
	if(self.serviceTypeRx == self.memService):
		self.currentCommand[146] == self.memService
		self.sendCurrentCommandToFifo(self.GPRTomemFifo)
	if(self.serviceTypeRx == self.fdirService):
		self.currentCommand[145] == fdirService
		self.sendCurrentCommandToFifo(self.GPRTofdirFifo)
	return

def checkIncomingEventReport():
	"""
	@purpose:   This function stores the received event in the eventLog. If there was an error,
				then this function will send an alert to FDIRGround for it to deal with the issue.
	"""	
	severity = self.currentCommand[3]
	reportID = self.currentCommand[2]
	p1 = self.currentCommand[1]
	p0 = self.currentCommand[0]

	self.logEventReport(severity, reportID, p1, p0, "Satellite event report received.")
	# If the event report was a failure, forward it to the FDIR task.
	if(self.serviceSubTypeRx > 1):
		self.currentCommand[146] = reportID
		self.currentCommand[145] = severity
		self.sendCurrentCommandToFifo(self.GPRtofdir)
	return

def syncWithIncomingTime():
	# Needs to save the old absolute time so that we can go back to it if we want to.
	"""
	@purpose:   This function looks at the incoming time and computes the difference between
				satellite time and ground time. If the difference is greater than 90 minutes,
				then the time between the ground and the satellite is considered to be out of
				sync. In this case, we adopt the satellite's time, store self.absTime in self.oldAbsTime
				and then we send an alert to FDIRGround.
	"""	
	incomDay = self.currentCommand[0]
	incomHour = self.currentCommand[1]
	incomMinute = self.currentCommand[2]
	logEventReport(1, self.timeReportReceived, 0, 0, "Time Report Received. D: %S H: %s M: %s" %incomDay %incomHour %incomMinute)
	incomAbsMinutes = (incomDay * 24 * 60) + (incomHour * 60) + incomMinute
	localAbsMinutes = (self.absTime.day * 24 * 60) + (self.absTime.hour * 60) + self.absTime.minute

	timeDelta = abs(localAbsTime - incomAbsTime)	# Difference in minutes between ground time and satellite time

	if(timeDelta > 90):		# If the difference in time is greater than one -approximate- orbit, something is wrong.
		self.printToCLI("Satellite time is currently out of sync.\n")
		# Store the current ground time.
		self.oldAbsTime self.absTime
		# Adopt the satellite's time
		absTime.day = incomDay
		absTime.hour = incomHour
		absTime.minute = incomMinute
		# Send a command to the FDIR task in order to resolve this issue
		self.currentCommand[146] = self.timeOutOfSync
		self.currentCommand[145] = 2	# Severity
		self.sendCurrentCommandToFifo(self.GPRTofdirFifo)
	return

def sendCurrentCommandToFifo(self, fifo):
	"""
	@purpose:   This method is takes what is contained in currentCommand[] and
	then place it in the given fifo "fifo".
	We use a "START\n" code and "STOP\n" code to indicate where commands stop and start.
	Each subquesequent byte is then placed in the fifo followed by a newline character.
	"""	
	tempString = None
	fifo.write("START\n")
	for i in range(0, self.dataLength + 10):
		tempString + str(self.currentCommand[i]) + "\n"
		fifo.write(tempString)
	fifo.write("STOP\n")
	return

def verifyTelemetry():
	"""
	@purpose:   This method is used to determine whether or not the TM packet which 
				was received is valid for decoding.
	@NOTE:		All telemetry, even telemetry that fails here is stored in memory under
				/telemetry
	@return:	-1 = packet failed the verification, 1 = good to decode
	"""	
	if(!self.currentTmCount):	# Method executed out of turn
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


def fletcher16(*data, offset, count):
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
	self.evenLog.write(tempString)
	self.eventLog.write(str(self.absTime.day) + "/" + str(self.absTime.hour) + "/" + str(self.absTime.minute) + "\t,\t")
	self.eventLog.write(str(reportID) + "\t,\t")
	self.eventLog.write(str(param1) + "\t,\t")
	self.eventLog.write(str(param0) + "\t,\t")
	if(message is not None):
		self.evenLog.write(str(message) + "\n")
	if(message is None):
		self.eventLog.write("\n")
	self.eventLock.release()
	return

@classmethod
def logHKReport(*hkArray):
	# Note that Housekeeping reports are created in a manner that is more convenient
	# for Excel or Matlab to parse but not really that great for human consumption
	self.hkLock.acquire()
	self.hkLog.write("HKLOG:\t")
	self.hkLog.write(str(self.absTime.day) + "/" + str(self.absTime.day) + "/" + str(self.absTime.day) + "\t,\t")
	for byte in hkArray:
		byte = byte & 0x000000FF
		self.hkLog.write(str(byte) + "\t,\t")
	self.hkLog.write("\n")
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
def clearCurrentCommand():
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
	self.timeReportReceived		= 0xFA
	self.timeOutOfSync			= 0xFB
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

if __name__ == '__main__':
	x = groundPacketRouter()
	x.start()
	x.terminate()
