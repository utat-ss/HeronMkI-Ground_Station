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
		- My subsidiary services need to wait for TC Acceptance verification before
		  proceeding on with other things. I will add in this code later.
		- 

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

11/20/2015			Added in Fifos so that each service can communicate with the FDIR service 
					independently.
"""
from HKService import *
from FDIRService import *
from MemoryService import *
from SchedulingService import *
from datetime import *
from multiprocessing import *

class groundPacketRouter(Process):
	"""
	Author: Keenan Burnett
	Acts as the main packet router for PUS packets to/from the groundstation
	as well as the CLI.
	Creates other processes which are used to manage PUS services.
	"""
	# Global variables for each PUS Service Instance
	selfprocessID 			= None
	serviceType 			= None
	currentCommand 			= []
	tmToDecode				= []
	currentTmCount			= 0
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
	kickComFromSchedule		= 1
	bitFlipDetected			= 2
	memoryWashFinished		= 3
	hkgroundinitialized		= 0xFF
	memgroundinitialized	= 0xFE
	fdirgroundinitialized  	= 0xFD
	incomTMSuccess			= 0xFC
	TMExecutionFailed		= 0xFB
	timeReportReceived		= 0xFA
	timeOutOfSync			= 0xFB
	timeReportReceived		= 0xFA
	timeOutOfSync			= 0xF9
	hkParamIncorrect		= 0xF8
	hkintervalincorrect		= 0xF7
	hkNumParamsIncorrect	= 0xF6
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
	FDIRGroundID			= 0x14
	schedGroundID			= 0x15
	# Fifos used by this class are created as attributes
	hkToGPRFifo				= None
	GPRTohkFifo				= None
	memToGPRFifo			= None
	GPRTomemFifo			= None
	fdirToGPRFifo			= None
	GPRTofdirFifo			= None
	# Subsidiary services are attributes to this class
	hkGroundService			= None
	memoryGroundService		= None
	FDIRGround				= None
	schedulingGround		= None

	@classmethod
	def run(self):
		"""
		@purpose: Represents the main program for the ground packet router and Command-Line Interface.
		"""
		initialize()

		while(1):
			# Check the transceiver for an incoming packet THIS NEEDS TO PUT INCOMING TELEMETRY
			self.decodeTelemetry(self)
			# Check FIFOs for a required action
			# Check the CLI for required action
			self.updateServiceTime(self)
			# Make sure all the subsidiary services are still running

	@staticmethod
	def initialize(self):
		"""
		@purpose: 	-Handles all file creation such as logs, fifos.
					-Synchronizes time with the satellite.
					-Initializes mutex locks
					-Creates subsidiary services for: housekeeping, memory management, failure detection isolation & recovery (FDIR)
		"""
		self.absTime = datetime.timedelta(0)	# Set the absolute time to zero. (for now)
		self.oldAbsTime = self.absTime
		self.currentTime = datetime(2015, 11, 21)

		self.clearCurrentCommand()

		"""Get the absolute time from the satellite and update ours."""

		# Create all the required FIFOs for PUS communicattion
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
		self.GPRtoschedFifo = open("/fifos/GPRTosched.fifo", "wb")
		os.mkfifo("/fifos/schedToGPR.fifo")
		self.schedToGPRFifo = open("/fifos/schedToGPR.fifo", "rb")
		# Create all the required FIFOs for the FDIR service
		path1 = "/fifos/hktoFDIR.fifo"
		path2 = "/fifos/memtoFDIR.fifo"
		path3 = "/fifos/schedtoFDIR.fifo"
		path4 = "/fifos/FDIRtohk.fifo"
		path5 = "/fifos/FDIRtomem.fifo"
		path6 = "/fifos/FDIRtosched.fifo"
		os.mkfifo(path1)
		os.mkfifo(path2)
		os.mkfifo(path3)
		os.mkfifo(path4)
		os.mkfifo(path5)
		os.mkfifo(path6)
		# Create all the files required for logging
		self.eventLog = None
		self.hkLog = None
		self.hkDefLog = None
		self.errorLog = None
		eventPath = "/events/eventLog%s%s.csv" %self.currentTime.month %self.currentTime.day
		if os.path.exists(eventPath):
			self.eventLog = open(eventPath, "rb+")
		else:
			self.eventLog = open(eventPath, "wb")
		hkPath = "/housekeeping/logs/hkLog%s%s.csv" %self.currentTime.month %self.currentTime.day
		if os.path.exists(hkPath):
			self.hkLog = open(hkPath, "rb+")
		else:
			self.hkLog = open(hkPath, "wb")
		hkDefPath = "/housekeeping/logs/hkDefLog%s%s.txt" %self.currentTime.month %self.currentTime.day
		if os.path.exists(hkDefPath):
			self.hkDefLog = open(hkDefPath, "rb+")
		else:
			self.hkDefLog  = open(hkDefPath, "wb")
		errorPath = "/ground_errors/errorLog%s%s.txt" %self.currentTime.month %self.currentTime.day
		if os.path.exists(errorPath):
			self.errorLog = open(errorPath, "rb+")
		else:
			self.errorLog = open(errorPath, "wb")

		# Create Mutex locks for accessing logs and printing to the CLI.
		self.hkLock 		= Lock()
		self.eventLock 		= Lock()
		self.cliLock 		= Lock()
		self.errorLock 		= Lock()
		self.hkTCLock		= Lock()
		self.memTCLock		= Lock()
		self.schedTCLock	= Lock()
		self.fdirTCLock		= Lock()

		# Create all the required PUS Services
		self.hkGroundService 		= hkService("/fifos/hkToGPR.fifo", "/fifos/GPRtohk.fifo", path1, path4, self.hkTCLock, eventPath, hkPath, errorPath, self.eventLock, self.hkLock,
											self.cliLock, self.errorLock, self.absTime.day, self.absTime.minute, hkDefPath)
		self.memoryGroundService 	= MemoryService("/fifos/memToGPR.fifo", "/fifos/GPRtomem.fifo", path2, path5, self.memTCLock, eventPath, hkPath, errorPath, self.eventLock, self.hkLock,
											self.cliLock, self.errorLock, self.absTime.day, self.absTime.minute, self.absTime.minute, self.absTime.second)
		self.schedulingGround		= schedulingService("/fifos/schedToGPR.fifo", "/fifos/GPRtosched.fifo", path3, path6, self.schedTCLock, eventPath, hkPath, errorPath, self.eventLock, self.hkLock,
											self.cliLock, self.errorLock, self.absTime.day, self.absTime.minute, self.absTime.minute, self.absTime.second)
		self.FDIRGround 			= FDIRService("/fifos/fdirToGPR.fifo", "/fifos/GPRtofdir.fifo", path1, path2, path3, path4, path5, path6, self.fdirTCLock, eventPath, hkPath, errorPath,
											self.eventLock, self.hkLock, self.cliLock, self.errorLock, self.absTime.day, self.absTime.minute, self.absTime.minute, self.absTime.second)
		# These are the actual Linux process IDs of the services which were just created.
		self.HKPID = self.hkGroundService.pid
		self.memPID = self.memoryGroundService.pid
		self.FDIRPID = self.FDIRGround.pid
		self.schedPID = self.schedulingGround.pid
		return

	@staticmethod
	def updateServiceTime(self):
		"""
		@purpose:   Whenever possible, GroundPacketRouter should update the time stored in the subsidiary services
					so that everything stays in sync.
		"""
		self.hkGroundService.absTime = self.absTime
		self.memoryGroundService.absTime = self.absTime
		self.FDIRGround.absTime = self.absTime
		self.schedulingGround.absTime = self.absTime
		return

	@staticmethod
	def tcVerificationDecode(self):
		"""
		@purpose:   This function is used when the PUS packet which was received is a TC
					verification packet.
					The intent here is to route the packet to the subsidiary service that
					it is intended for (TC Acceptance Report) OR to log the verification
					to the Event Log / Alert FDIR (TC Execution Report)
		@Note:		If the TC verification is a success, then we set the corresponding tc verification
					attribute for that service, otherwise we send an alert to the FDIR task (and set nothing for the service)
		"""
		verificationAPID = 0
		verificationPacketID = self.currentCommand[135] << 8
		verificationPacketID += self.currentCommand[134]
		verificationPSC	= self.currentCommand[133] << 8
		verificationPSC += self.currentCommand[132]
		if((self.serviceSubTypeRx == 1) or (self.serviceSubTypeRx == 7)):				# TC verification is a successful type.
			verificationAPID = self.currentCommand[135]
			self.currentCommand[146] = 1
			if(verificationAPID == self.hkTaskID):
				self.hkTCLock.acquire()
				self.hkGroundService.tcAcceptVerification = (verificationPacketID << 16) & verificationPSC
				self.hkTCLock.release()
			if(verificationAPID == self.MemoryTaskID):
				self.memTCLock.acquire()
				self.memoryGroundService.tcAcceptVerification = (verificationPacketID << 16) & verificationPSC
				self.memTCLock.release()
			if(verificationAPID == self.schedulingTaskID):
				self.schedTCLock.acquire()
				self.schedulingGround.tcAcceptVerification = (verificationPacketID << 16) & verificationPSC
				self.schedTCLock.release()
			if(verificationAPID == self.FDIRGroundID):
				self.fdirTCLock.acquire()
				self.FDIRGround.tcAcceptVerification = (verificationPacketID << 16) & verificationPSC
				self.fdirTCLock.release()
		if((self.serviceSubTypeRx == 2) or (self.serviceSubTypeRx == 8)):				# Tc verification is a failure type.
			self.logEventReport(2, self.TMExecutionFailed, 0, 0, "Telecommand Execution Failed. for PacketID: %s, PSC: %s" %str(verificationPacketID) % str(verificationPSC))
			self.currentCommand[146] = self.TMExecutionFailed
			self.currentCommand[146] = 3
			self.sendCurrentCommandToFifo(self.GPRTofdirFifo)		# Alert FDIR that something is going wrong.

		return

	# Each element of the tmToDecode array needs to be an integer
	@staticmethod
	def decodeTelemetry(self):
		"""
		@purpose:   This method will decode the telemetry packet which was sent by the satellite
					(located in tmToDecode[]). It will either send the appropriate commands
					to the subsidiary services or it will act on the telemetry itself (if it is valid).
					For now, we will log all telemtry for safe-keeping / debugging.
		"""
		if not self.currentTmCount:
			return -1

		self.packetID = self.tmToDecode[151] << 8
		self.packetID |= self.tmToDecode[150]
		self.psc = self.tmToDecode[149] << 8
		self.psc |= self.tmToDecode[148]
		# Packet Header
		self.version1 			= (self.tmToDecode[151] & 0xE0) >> 5
		self.type1 				= (self.tmToDecode[151] & 0x10) >> 4
		self.dataFieldHeaderf 	= (self.tmToDecode[151] & 0x08) >> 3
		self.apid				= self.tmToDecode[150]
		self.sequenceFlags1		= (self.tmToDecode[149] & 0xC0) >> 6
		self.sequenceCount1		= self.tmToDecode[148]
		self.packetLengthRx		= self.tmToDecode[146] + 1
		# Data Field Header
		self.ccsdsFlag			= (self.tmToDecode[145] & 0x80) >> 7
		self.packetVersion		= (self.tmToDecode[145] & 0x70) >> 4
		self.ack				= self.tmToDecode[145] & 0x0F
		self.serviceTypeRx		= self.tmToDecode[144]
		self.serviceSubTypeRx	= self.tmToDecode[143]
		self.sourceID			= self.tmToDecode[142]
		# Received Checksum Value
		self.pec1 = self.tmToDecode[1] << 8
		self.pec1 |= self.tmToDecode[0]
		# Check that the packet error control is correct
		self.pec0 = self.fletcher16(2, 150, self.tmToDecode)
		x = -1
		x = self.verifyTelemetry()

		if x < 0:
			return -1

		self.decodeTelemetryH()
		return

	@staticmethod
	def decodeTelemetryH(self):
		"""
		@purpose:   Helper to decodeTelemetry, this method looks at self.serviceTypeRx and
					self.serviceSubTypeRx of the telemetry packet stored in tmToDecode[] and
					performs the actual routing of messages and executing of required actions.
		"""
		if not self.currentTmCount:	# Method executed out of turn
			return -1

		self.clearCurrentCommand()
		for i in range(2, self.dataLength + 2):
			self.currentCommand[i - 2] = self.tmToDecode[i]

		self.currentTmCount -= 1

		self.currentCommand[140] = self.packetID >> 8
		self.currentCommand[139] = self.packetID & 0x000000FF
		self.currentCommand[138] = self.psc >> 8
		self.currentCommand[137] = self.psc & 0x000000FF

		if(self.serviceTypeRx == self.tcVerifyService):
			self.tcVerificationDecode()
		if(self.serviceTypeRx == self.hkService):
			self.currentCommand[146] = self.serviceSubTypeRx
			self.currentCommand[145] = self.currentCommand[135]
			self.currentCommand[144] = self.currentCommand[134]
			self.sendCurrentCommandToFifo(self.GPRTohkFifo)
		if(self.serviceTypeRx == self.timeService):
			self.syncWithIncomingTime()
		if(self.serviceTypeRx == self.kService):
			self.currentCommand[146] = self.serviceSubTypeRx
			self.sendCurrentCommandToFifo(self.GPRtoschedFifo)
		if(self.serviceTypeRx == self.eventReportService):
			self.checkIncomingEventReport()
		if(self.serviceTypeRx == self.memService):
			self.currentCommand[146] = self.memService
			self.sendCurrentCommandToFifo(self.GPRTomemFifo)
		if(self.serviceTypeRx == self.fdirService):
			self.currentCommand[146] = self.fdirService
			self.sendCurrentCommandToFifo(self.GPRTofdirFifo)
		return

	@staticmethod
	def checkIncomingEventReport(self):
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
			self.sendCurrentCommandToFifo(self.GPRTofdirFifo)
		return

	@staticmethod
	def syncWithIncomingTime(self):
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
		self.logEventReport(1, self.timeReportReceived, 0, 0, "Time Report Received. D: %s H: %s M: %s" %str(incomDay) %incomHour %incomMinute)
		incomAbsMinutes = (incomDay * 24 * 60) + (incomHour * 60) + incomMinute
		localAbsMinutes = (self.absTime.day * 24 * 60) + (self.absTime.hour * 60) + self.absTime.minute

		timeDelta = abs(localAbsMinutes - incomAbsMinutes)	# Difference in minutes between ground time and satellite time

		if(timeDelta > 90):		# If the difference in time is greater than one -approximate- orbit, something is wrong.
			self.printToCLI("Satellite time is currently out of sync.\n")
			# Store the current ground time.
			self.oldAbsTime = self.absTime
			# Adopt the satellite's time
			self.absTime.day = incomDay
			self.absTime.hour = incomHour
			self.absTime.minute = incomMinute
			# Send a command to the FDIR task in order to resolve this issue
			self.currentCommand[146] = self.timeOutOfSync
			self.currentCommand[145] = 2	# Severity
			self.sendCurrentCommandToFifo(self.GPRTofdirFifo)
		return

	@staticmethod
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
			tempString = str(self.currentCommand[i]) + "\n"
			fifo.write(tempString)
		fifo.write("STOP\n")
		return

	@staticmethod
	def verifyTelemetry(self):
		"""
		@purpose:   This method is used to determine whether or not the TM packet which
					was received is valid for decoding.
		@NOTE:		All telemetry, even telemetry that fails here is stored in memory under
					/telemetry
		@return:	-1 = packet failed the verification, 1 = good to decode
		"""
		if not self.currentTmCount:	# Method executed out of turn
			return -1

		if(self.packetLengthRx != self.packetLength):
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an incorrect packet length" %str(self.packetID) %str(self.psc))
			return -1

		if(self.pec0 != self.pec1):
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s failed the checksum test. PEC1: %s, PEC0: %s"
							%str(self.packetID) %str(self.psc) %str(self.pec1) %str(self.pec0))
			return -1

		if((self.serviceTypeRx != 1) and (self.serviceTypeRx != 3) and (self.serviceTypeRx != 5)
		and (self.serviceTypeRx != 6) and (self.serviceTypeRx != 9) and (self.serviceTypeRx != 69)):
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an incorrect serviceType" %str(self.packetID) %str(self.psc))
			return -1

		if(self.serviceTypeRx == self.tcVerifyService):
			if((self.serviceSubTypeRx != 1) and (self.serviceSubTypeRx != 2) and (self.serviceSubTypeRx != 7) and (self.serviceSubTypeRx != 8)):
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an incorrect serviceSubType" %str(self.packetID) %str(self.psc))
				return -1

		if(self.serviceTypeRx == self.hkService):
			if((self.serviceSubTypeRx != 10) and (self.serviceSubTypeRx != 12) and (self.serviceSubTypeRx != 25) and (self.serviceSubTypeRx != 26)):
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an incorrect serviceSubType" %str(self.packetID) %str(self.psc))
				return -1
			if((self.apid != self.HKGroundID) and (self.apid != self.FDIRGroundID)):
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an invalid APID" %str(self.packetID) %str(self.psc))
				return -1

		if(self.serviceTypeRx == self.memService):
			if((self.serviceSubTypeRx != 6) and (self.serviceSubTypeRx != 10)):
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an incorrect serviceSubType" %str(self.packetID) %str(self.psc))
				return -1
			if(self.apid != self.MemGroundID):
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an invalid APID" %str(self.packetID) %str(self.psc))
				return -1
			address = self.tmToDecode[137] << 24
			address += self.tmToDecode[136] << 16
			address += self.tmToDecode[135] << 8
			address += self.tmToDecode[134]

			if(self.tmToDecode[138] > 1):
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an incorrect memoryID" %str(self.packetID) %str(self.psc))
				return -1
			if((self.tmToDecode[138] == 1) and (address > 0xFFFFF)):
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
			length = self.tmToDecode[136]
			if((self.serviceSubTypeRx != 4)):
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an incorrect serviceSubType" %str(self.packetID) %str(self.psc))
				return -1
			if(self.apid != self.schedGroundID):
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an invalid APID" %str(self.packetID) %str(self.psc))
				return -1

		if(self.version1 != 1):
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an incorrect version" %str(self.packetID) %str(self.psc))
			return -1
		if(self.ccsdsFlag != 1):
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an incorrect ccsdsFlag" %str(self.packetID) %str(self.psc))
			return -1
		if(self.packetVersion != 1):
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an incorrect packet version" %str(self.packetID) %str(self.psc))
			return -1

		self.logEventReport(1, self.incomTMSuccess, 0, 0, "Incoming Telemetry Packet Succeeded")
		return 1

	@staticmethod
	def fletcher16(self, offset, count, *data):
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
		if(self.hkGroundService.is_alive()):
			self.hkGroundService.terminate()
		if(self.memoryGroundService.is_alive()):
			self.memoryGroundService.terminate()
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
		os.remove("/fifos/hktoFDIR.fifo")
		os.remove("/fifos/memtoFDIR.fifo")
		os.remove("/fifos/schedtoFDIR.fifo")
		os.remove("/fifos/FDIRtohk.fifo")
		os.remove("/fifos/FDIRtomem.fifo")
		os.remove("/fifos/FDIRtosched.fifo")
		return

	@staticmethod
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
		self.eventLog.write(str(reportID) + "\t,\t")
		self.eventLog.write(str(param1) + "\t,\t")
		self.eventLog.write(str(param0) + "\t,\t")
		if(message is not None):
			self.eventLog.write(str(message) + "\n")
		if(message is None):
			self.eventLog.write("\n")
		self.eventLock.release()
		return

	@staticmethod
	def logError(self, errorString):
		self.errorLock.acquire()
		self.errorLog.write("******************ERROR START****************\n")
		self.errorLog.write("ERROR: " + str(errorString) + " \n")
		self.errorLog.write("******************ERROR STOP****************\n")
		return

	@staticmethod
	def printToCLI(self, stuff):
		self.cliLock.acquire()
		print(str(stuff))
		self.cliLock.release()
		return

	@staticmethod
	def clearCurrentCommand(self):
		i = 0
		for i in range(0, (self.dataLength + 10)):
			self.currentCommand[i] = 0
		return

	def __init__(self):
		"""
		@purpose: Initialization method for the Ground Packet Router Class
		"""
		super(groundPacketRouter, self).__init__()

if __name__ == '__main__':
	x = groundPacketRouter()
	x.start()
	x.stop()
	x.terminate()
