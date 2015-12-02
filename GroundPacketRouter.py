"""
FILE_NAME:			GroundPacketRouter.py

AUTHOR:				Keenan Burnett

PURPOSE:			This program is meant to start all other ground station software and
					act as the interface between subsidiary services and the CLI / transceiver.

FILE REFERENCES: 	PUSService.py, HKService.py, MemoryService.py, FDIRService.py
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
	-ex: python GroundPacketRouter.py
	-For the time being, we will have a serial connection to an Arduino Uno
	which will allow us to connect to the transceiver remotely.
	-We are using the CC1120 dev board as our "transceiver" for the groundstation

DEVELOPMENT HISTORY:
11/16/2015			Created.

11/17/2015			I am adding the decode_telemetry() function.

11/18/2015			Finished decodeTelemtry(), decodeTelemtry(), verifyTelemetry().

11/20/2015			Added in Fifos so that each service can communicate with the FDIR service 
					independently.

11/26/2015			Added code for packetizeSendTelecommand()

11/27/2015			Added the code for execCommands(), and started workin on the CLI.

11/28/2015			I decided it makes more sense to have a separate process which shall monitor the command line
					interface.
"""
from HKService import *
from FDIRService import *
from MemoryService import *
from SchedulingService import *
from PUSPacket import *
from datetime import datetime
from multiprocessing import *
from sys import executable
from subprocess import Popen

class groundPacketRouter(Process):
	"""
	Author: Keenan Burnett
	Acts as the main packet router for PUS packets to/from the groundstation
	as well as the CLI.
	Creates other processes which are used to manage PUS services.
	"""
	# Global variables for each PUS Service Instance
	processID 				= None
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
	dumpCompleted			= 0xF1
	schedGroundInitialized	= 0xF0
	updatingSchedAut		= 0xEF
	scheduleCleared			= 0xEE
	schedCommandCompleted   = 0xED
	numCommandsWrong		= 0xEC
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
	# Packet object
	currentPacket			= Puspacket()
	lastPacket				= currentPacket
	sendPacket				= Puspacket()
	lastSendPacket			= sendPacket
	sendPacketCount			= 0
	# Counting Attributes for the different Telecommand packets that can be sent
	clearHKCount			= 0
	newHKCount				= 0
	enableParamCount		= 0
	disableParamCount		= 0
	requestDefReportCount	= 0
	memoryLoadCount			= 0
	DumpRequestCount		= 0
	checkMemCount			= 0
	addScheduleCount		= 0
	clearScheduleCount		= 0
	reportRequestCount		= 0
	pauseScheduleCount		= 0
	resumeScheduleCount		= 0
	currentPath				= None

	@classmethod
	def run(cls):
		"""
		@purpose: Represents the main program for the ground packet router and Command-Line Interface.
		"""
		cls.initialize(cls)

		os.system("gnome-terminal --disable-factory -e {python CommandLineInterface.py}")
		while 1:
			response = raw_input("Enter something to kill this process")
			if response:
				return

		while 1:
			# Check the transceiver for an incoming packet THIS NEEDS TO PUT INCOMING TELEMETRY INTO PACKET OBJECTS
			if cls.decodeTelemetry(cls, cls.currentPacket) < 0:
				# Send an error message to FDIRGround
				pass
			cls.execCommands(cls)
			# Check the CLI for required action
			cls.updateServiceTime(cls)
			# Make sure all the subsidiary services are still running, restart them if necessary.
			# Check if the satellite is in reach, then send commands if it is.

	@staticmethod
	def initialize(self):
		"""
		@purpose: 	-Handles all file creation such as logs, fifos.
					-Synchronizes time with the satellite.
					-Initializes mutex locks
					-Creates subsidiary services for: housekeeping, memory management, failure detection isolation & recovery (FDIR)
		"""
		self.absTime = datetime(2015, 1, 1, 0, 0, 0)# Set the absolute time to zero. (for now)
		self.oldAbsTime = self.absTime
		self.currentTime = datetime(2015, 11, 21)

		self.initCurrentCommand(self)

		"""Get the absolute time from the satellite and update ours."""
		self.currentPath = os.path.dirname(os.path.realpath(__file__))
		os.chdir(self.currentPath)
		print("Current Working Directory: %s" %self.currentPath)

		# Create all the required FIFOs for to send information to the PUS services.
		os.mkfifo(self.currentPath + "/fifos/GPRtohk.fifo")
		os.mkfifo(self.currentPath + "/fifos/GPRtomem.fifo")
		os.mkfifo(self.currentPath + "/fifos/GPRtofdir.fifo")
		os.mkfifo(self.currentPath + "/fifos/GPRtosched.fifo")
		os.mkfifo(self.currentPath + "/fifos/hkToGPR.fifo")
		os.mkfifo(self.currentPath + "/fifos/memToGPR.fifo")
		os.mkfifo(self.currentPath + "/fifos/schedToGPR.fifo")
		os.mkfifo(self.currentPath + "/fifos/fdirToGPR.fifo")
		# Create all the required FIFOs for the FDIR service
		path1 = self.currentPath + "/fifos/hktoFDIR.fifo"
		path2 = self.currentPath + "/fifos/memtoFDIR.fifo"
		path3 = self.currentPath + "/fifos/schedtoFDIR.fifo"
		path4 = self.currentPath + "/fifos/FDIRtohk.fifo"
		path5 = self.currentPath + "/fifos/FDIRtomem.fifo"
		path6 = self.currentPath + "/fifos/FDIRtosched.fifo"
		# Create the required FIFOs for the CLI
		os.mkfifo(self.currentPath + "/fifos/GPRToCLI.fifo")
		#self.GPRToCLIFifo = open(self.currentPath + "/fifos/GPRToCLI.fifo", "w")
		os.mkfifo(self.currentPath + "/fifos/CLIToGPR.fifo")
		#self.CLIToGPRFifo = open(self.currentPath + "/fifos/CLIToGPR.fifo", "r")
		# Create all the files required for logging
		self.eventLog = None
		self.hkLog = None
		self.hkDefLog = None
		self.errorLog = None
		print(self.currentTime.month)
		print(self.currentTime.day)
		eventPath = self.currentPath + "/events/eventLog%s.csv" %(str(self.currentTime.month) + str(self.currentTime.day))
		if os.path.exists(eventPath):
			self.eventLog = open(eventPath, "rb+")
		else:
			self.eventLog = open(eventPath, "wb")
		hkPath = self.currentPath + "/housekeeping/logs/hkLog%s.csv" %(str(self.currentTime.month) + str(self.currentTime.day))
		if os.path.exists(hkPath):
			self.hkLog = open(hkPath, "rb+")
		else:
			self.hkLog = open(hkPath, "wb")
		hkDefPath = self.currentPath + "/housekeeping/logs/hkDefLog%s.txt" %(str(self.currentTime.month) + str(self.currentTime.day))
		if os.path.exists(hkDefPath):
			self.hkDefLog = open(hkDefPath, "rb+")
		else:
			self.hkDefLog  = open(hkDefPath, "wb")
		errorPath = self.currentPath + "/ground_errors/errorLog%s.txt" %(str(self.currentTime.month) + str(self.currentTime.day))
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
		self.hkGroundService 		= hkService(self.currentPath + "/fifos/hkToGPR.fifo", self.currentPath + "/fifos/GPRtohk.fifo", path1, path4,
											self.hkTCLock, eventPath, hkPath, errorPath, self.eventLock, self.hkLock,
											self.cliLock, self.errorLock, self.absTime.day, self.absTime.hour,
											self.absTime.minute, self.absTime.second, hkDefPath)
		self.memoryGroundService 	= MemoryService(self.currentPath + "/fifos/memToGPR.fifo", self.currentPath + "/fifos/GPRtomem.fifo", path2, path5,
											self.memTCLock, eventPath, hkPath, errorPath, self.eventLock, self.hkLock,
											self.cliLock, self.errorLock, self.absTime.day, self.absTime.hour,
											self.absTime.minute, self.absTime.second)
		self.schedulingGround		= schedulingService(self.currentPath + "/fifos/schedToGPR.fifo", self.currentPath + "/fifos/GPRtosched.fifo", path3, path6,
											self.schedTCLock, eventPath, hkPath, errorPath, self.eventLock, self.hkLock,
											self.cliLock, self.errorLock, self.absTime.day, self.absTime.hour,
											self.absTime.minute, self.absTime.second)
		self.FDIRGround 			= FDIRService(self.currentPath + "/fifos/fdirToGPR.fifo", self.currentPath + "/fifos/GPRtofdir.fifo", path1, path2, path3,
											path4, path5, path6, self.fdirTCLock, eventPath, hkPath, errorPath,
											self.eventLock, self.hkLock, self.cliLock, self.errorLock, self.absTime.day,
											self.absTime.minute, self.absTime.minute, self.absTime.second)

		print("HK PID: %s" %str(self.hkGroundService.pID))
		print("mem PID: %s" %str(self.memoryGroundService.pID))
		print("Sched PID: %s" %str(self.schedulingGround.pID))
		print("FDIR PID: %s" %str(self.FDIRGround.pID))

		# Open all the FIFOs TO the subsidiary services for writing
		self.GPRTohkFifo = open(self.currentPath + "/fifos/GPRtohk.fifo", "wb")
		self.GPRTomemFifo = open(self.currentPath + "/fifos/GPRtomem.fifo", "wb")
		self.GPRTofdirFifo = open(self.currentPath + "/fifos/GPRtofdir.fifo", "wb")
		self.GPRtoschedFifo = open(self.currentPath + "/fifos/GPRtosched.fifo", "wb")

		# Open all the FIFOs for receiving information from the PUS services, (created by them as well)
		self.hkToGPRFifo = open(self.currentPath + "/fifos/hkToGPR.fifo", "rb", 0)
		self.memToGPRFifo = open(self.currentPath + "/fifos/memToGPR.fifo", "rb", 0)
		self.fdirToGPRFifo = open(self.currentPath + "/fifos/fdirToGPR.fifo", "rb", 0)
		self.schedToGPRFifo = open(self.currentPath + "/fifos/schedToGPR.fifo", "rb", 0)

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
		verificationPacketID = self.currentCommand[135] << 8
		verificationPacketID += self.currentCommand[134]
		verificationPSC	= self.currentCommand[133] << 8
		verificationPSC += self.currentCommand[132]
		if (self.serviceSubType == 1) or (self.serviceSubType == 7):				# TC verification is a successful type.
			verificationAPID = self.currentCommand[135]
			self.currentCommand[146] = 1
			if verificationAPID == self.hkTaskID:
				self.hkTCLock.acquire()
				self.hkGroundService.tcAcceptVerification = (verificationPacketID << 16) & verificationPSC
				self.hkTCLock.release()
			if verificationAPID == self.MemoryTaskID:
				self.memTCLock.acquire()
				self.memoryGroundService.tcAcceptVerification = (verificationPacketID << 16) & verificationPSC
				self.memTCLock.release()
			if verificationAPID == self.schedulingTaskID:
				self.schedTCLock.acquire()
				self.schedulingGround.tcAcceptVerification = (verificationPacketID << 16) & verificationPSC
				self.schedTCLock.release()
			if verificationAPID == self.FDIRGroundID:
				self.fdirTCLock.acquire()
				self.FDIRGround.tcAcceptVerification = (verificationPacketID << 16) & verificationPSC
				self.fdirTCLock.release()
		if (self.serviceSubType == 2) or (self.serviceSubType == 8):				# Tc verification is a failure type.
			self.logEventReport(2, self.TMExecutionFailed, 0, 0, "Telecommand Execution Failed. for PacketID: %s, PSC: %s" %str(verificationPacketID) % str(verificationPSC))
			self.currentCommand[146] = self.TMExecutionFailed
			self.currentCommand[146] = 3
			self.sendCurrentCommandToFifo(self.GPRTofdirFifo)		# Alert FDIR that something is going wrong.

		return

	@staticmethod
	def checkTransceiver(self):
		# Do some stuff with the serial ports & communicating with the transceiver through the Arduino.
		# This method should check if self.currentPacket is None, and if not, add the new packet object
		# to the end of the linked list.
		pass

	# Each element of the tmToDecode array needs to be an integer
	@staticmethod
	def decodeTelemetry(self, currentPacket):
		"""
		@purpose:   This method will decode the telemetry packet which was sent by the satellite
					(located in tmToDecode[]). It will either send the appropriate commands
					to the subsidiary services or it will act on the telemetry itself (if it is valid).
					For now, we will log all telemetry for safe-keeping / debugging.
		"""
		if not currentPacket:
			return -1

		# This parses through the data array and places the appropriate
		# information in the attributes of this packet.
		currentPacket.parseDataArray()

		if self.verifyTelemetry(currentPacket) < 0:
			return -1
		if self.decodeTelemetryH(currentPacket) < 0:
			return -1
		return 1

	@staticmethod
	def decodeTelemetryH(self, currentPacket):
		"""
		@purpose:   Helper to decodeTelemetry, this method looks at self.serviceType and
					self.serviceSubType of the telemetry packet stored in tmToDecode[] and
					performs the actual routing of messages and executing of required actions.
		"""
		if not currentPacket:	# Method executed out of turn
			return -1

		self.clearCurrentCommand()
		for i in range(2, self.dataLength + 2):
			self.currentCommand[i - 2] = currentPacket.data[i]

		self.currentCommand[140] = currentPacket.packetID >> 8
		self.currentCommand[139] = currentPacket.packetID & 0x000000FF
		self.currentCommand[138] = currentPacket.psc >> 8
		self.currentCommand[137] = self.psc & 0x000000FF

		if currentPacket.serviceType == self.tcVerifyService:
			self.tcVerificationDecode()
		if currentPacket.serviceType == self.hkService:
			self.currentCommand[146] = currentPacket.serviceSubType
			self.currentCommand[145] = self.currentCommand[135]
			self.currentCommand[144] = self.currentCommand[134]
			self.sendCurrentCommandToFifo(self.GPRTohkFifo)
		if currentPacket.serviceType == self.timeService:
			self.syncWithIncomingTime()
		if currentPacket.serviceType == self.kService:
			self.currentCommand[146] = currentPacket.serviceSubType
			self.sendCurrentCommandToFifo(self.GPRtoschedFifo)
		if currentPacket.serviceType == self.eventReportService:
			self.checkIncomingEventReport()
		if currentPacket.serviceType == self.memService:
			self.currentCommand[146] = self.memService
			self.currentCommand[145] = currentPacket.packetID
			self.currentCommand[144] = currentPacket.psc
			self.currentCommand[143] = currentPacket.sequenceFlags
			self.currentCommand[142] = currentPacket.sequenceCount
			self.sendCurrentCommandToFifo(self.GPRTomemFifo)
		if currentPacket.serviceType == self.fdirService:
			self.currentCommand[146] = self.fdirService
			self.sendCurrentCommandToFifo(self.GPRTofdirFifo)

		self.currentPacket = self.currentPacket.nextPacket		# Move to the next packet in the linked list, may be None.
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
		if self.serviceSubType > 1:
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

		if timeDelta > 90:		# If the difference in time is greater than one -approximate- orbit, something is wrong.
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
		fifo.write("START\n")
		for i in range(0, self.dataLength + 10):
			tempString = str(self.currentCommand[i]) + "\n"
			fifo.write(tempString)
		fifo.write("STOP\n")
		return

	@staticmethod
	def verifyTelemetry(self, currentPacket):
		"""
		@purpose:   This method is used to determine whether or not the TM packet which
					was received is valid for decoding.
		@NOTE:		All telemetry, even telemetry that fails here is stored in memory under
					/telemetry
		@return:	-1 = packet failed the verification, 1 = good to decode
		"""
		if not currentPacket:	# Method executed out of turn
			return -1

		if currentPacket.packetLengthRx != self.packetLength:
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an incorrect packet length" %str(currentPacket.packetID) %str(currentPacket.psc))
			return -1

		if currentPacket.pec0 != currentPacket.pec1:
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s failed the checksum test. PEC1: %s, PEC0: %s"
							%str(currentPacket.packetID) %str(currentPacket.psc) %str(currentPacket.pec1) %str(currentPacket.pec0))
			return -1

		if((currentPacket.serviceType != 1) and (currentPacket.serviceType != 3) and (currentPacket.serviceType != 5)
		and (currentPacket.serviceType != 6) and (currentPacket.serviceType != 9) and (currentPacket.serviceType != 69)):
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an incorrect serviceType" %str(currentPacket.packetID) %str(currentPacket.psc))
			return -1

		if currentPacket.serviceType == self.tcVerifyService:
			if (currentPacket.serviceSubType != 1) and (currentPacket.serviceSubType != 2) and (currentPacket.serviceSubType != 7) and (currentPacket.serviceSubType != 8):
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an incorrect serviceSubType" %str(currentPacket.packetID) %str(currentPacket.psc))
				return -1

		if currentPacket.serviceType == self.hkService:
			if (currentPacket.serviceSubType != 10) and (currentPacket.serviceSubType != 12) and (currentPacket.serviceSubType != 25) and (currentPacket.serviceSubType != 26):
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an incorrect serviceSubType" %str(currentPacket.packetID) %str(currentPacket.psc))
				return -1
			if(currentPacket.apid != self.HKGroundID) and (currentPacket.apid != self.FDIRGroundID):
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an invalid APID" %str(currentPacket.packetID) %str(currentPacket.psc))
				return -1

		if currentPacket.serviceType == self.memService:
			if(currentPacket.serviceSubType != 6) and (currentPacket.serviceSubType != 10):
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an incorrect serviceSubType" %str(currentPacket.packetID) %str(currentPacket.psc))
				return -1
			if currentPacket.apid != self.MemGroundID:
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an invalid APID" %str(currentPacket.packetID) %str(currentPacket.psc))
				return -1
			address = currentPacket.data[137] << 24
			address += currentPacket.data[136] << 16
			address += currentPacket.data[135] << 8
			address += currentPacket.data[134]

			if currentPacket.data[138] > 1:
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an incorrect memoryID" %str(currentPacket.packetID) %str(currentPacket.psc))
				return -1
			if (currentPacket.data[138] == 1) and (address > 0xFFFFF):
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an invalid address" %str(currentPacket.packetID) %str(currentPacket.psc))
				return -1

		if currentPacket.serviceType == self.timeService:
			if currentPacket.serviceSubType != 2:
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an incorrect serviceSubType" %str(currentPacket.packetID) %str(currentPacket.psc))
				return -1
			if currentPacket.apid != self.TimeGroundID:
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an invalid APID" %str(currentPacket.packetID) %str(currentPacket.psc))
				return -1
		if currentPacket.serviceType == self.kService:
			if currentPacket.serviceSubType != 4:
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an incorrect serviceSubType" %str(currentPacket.packetID) %str(currentPacket.psc))
				return -1
			if currentPacket.apid != self.schedGroundID:
				self.printToCLI("Incoming Telemetry Packet Failed\n")
				self.logError("TM PacketID: %s, PSC: %s had an invalid APID" %str(currentPacket.packetID) %str(currentPacket.psc))
				return -1

		if currentPacket.version != 1:
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an incorrect version" %str(currentPacket.packetID) %str(currentPacket.psc))
			return -1
		if currentPacket.ccsdsFlag != 1:
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an incorrect ccsdsFlag" %str(currentPacket.packetID) %str(currentPacket.psc))
			return -1
		if currentPacket.packetVersion != 1:
			self.printToCLI("Incoming Telemetry Packet Failed\n")
			self.logError("TM PacketID: %s, PSC: %s had an incorrect packet version" %str(currentPacket.packetID) %str(currentPacket.psc))
			return -1

		self.logEventReport(1, self.incomTMSuccess, 0, 0, "Incoming Telemetry Packet Succeeded")
		return 1

	@classmethod
	def stop(cls):
		# Close all the files which were opened
		cls.hkToGPRFifo.close()
		cls.GPRTohkFifo.close()
		cls.memToGPRFifo.close()
		cls.GPRTomemFifo.close()
		cls.fdirToGPRFifo.close()
		cls.GPRTofdirFifo.close()
		# Kill all the children
		if cls.hkGroundService.is_alive():
			cls.hkGroundService.terminate()
		if cls.memoryGroundService.is_alive():
			cls.memoryGroundService.terminate()
		if cls.FDIRGround.is_alive():
			cls.FDIRGround.terminate()
		if cls.schedulingGround.as_alive():
			cls.schedulingGround.terminate()

		# Delete all the FIFO files that were created
		os.remove(self.currentPath + "/fifos/hkToGPR.fifo")
		os.remove(self.currentPath + "/fifos/GPRtohk.fifo")
		os.remove(self.currentPath + "/fifos/memToGPR.fifo")
		os.remove(self.currentPath + "/fifos/GPRtomem.fifo")
		os.remove(self.currentPath + "/fifos/GPRtomem.fifo")
		os.remove(self.currentPath + "/fifos/fdirToGPR.fifo")
		os.remove(self.currentPath + "/fifos/GPRtofdir.fifo")
		os.remove(self.currentPath + "/fifos/GPRTosched.fifo")
		os.remove(self.currentPath + "/fifos/schedToGPR.fifo")
		os.remove(self.currentPath + "/fifos/hktoFDIR.fifo")
		os.remove(self.currentPath + "/fifos/memtoFDIR.fifo")
		os.remove(self.currentPath + "/fifos/schedtoFDIR.fifo")
		os.remove(self.currentPath + "/fifos/FDIRtohk.fifo")
		os.remove(self.currentPath + "/fifos/FDIRtomem.fifo")
		os.remove(self.currentPath + "/fifos/FDIRtosched.fifo")
		os.remove(self.currentPath + "/fifos/CLIToGPR.fifo")
		os.remove(self.currentPath + "/fifos/GPRToCLI.fifo")
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
		if message is not None:
			self.eventLog.write(str(message) + "\n")
		if message is None:
			self.eventLog.write("\n")
		self.eventLock.release()
		return

	@staticmethod
	def execCommands(self):
		self.clearCurrentCommand()
		if self.receiveCommandFromFifo(self.hkToGPRFifo) > 0:
			if self.currentCommand[146] == self.clearHKDefinition:
				self.clearHKCount += 1
				self.packetizeSendTelecommand(self.HKGroundID, self.hkTaskID, self.hkService, self.clearHKDefinition,
											  self.clearHKCount, 1, self.currentCommand)
			if self.currentCommand[146] == self.newHKDefinition:
				self.newHKCount += 1
				self.packetizeSendTelecommand(self.HKGroundID, self.hkTaskID, self.hkService, self.newHKDefinition,
											  self.newHKCount, 1, self.currentCommand)
			if self.currentCommand[146] == self.enableParamReport:
				self.enableParamCount += 1
				self.packetizeSendTelecommand(self.HKGroundID, self.hkTaskID, self.hkService, self.enableParamReport,
											  self.enableParamCount, 1, self.currentCommand)
			if self.currentCommand[146] == self.disableParamReport:
				self.disableParamCount += 1
				self.packetizeSendTelecommand(self.HKGroundID, self.hkTaskID, self.hkService, self.disableParamReport,
											  self.disableParamCount, 1, self.currentCommand)
			if self.currentCommand[146] == self.reportHKDefinitions:
				self.requestDefReportCount += 1
				self.packetizeSendTelecommand(self.HKGroundID, self.hkTaskID, self.hkService, self.reportHKDefinitions,
											  self.requestDefReportCount, 1, self.currentCommand)
		if self.receiveCommandFromFifo(self.memToGPRFifo) > 0:
			if self.currentCommand[146] == self.memoryLoadABS:
				self.memoryLoadCount += 1
				self.packetizeSendTelecommand(self.MemGroundID, self.MemoryTaskID, self.memService, self.memoryLoadABS,
											  self.memoryLoadCount, self.currentCommand[145], self.currentCommand)
			if self.currentCommand[146] == self.dumpRequestABS:
				self.dumpRequestCount += 1
				self.packetizeSendTelecommand(self.MemGroundID, self.MemoryTaskID, self.memService, self.dumpRequestABS,
											  self.dumpRequestCount, 1, self.currentCommand)
			if self.currentCommand[146] == self.checkMemRequest:
				self.checkMemCount += 1
				self.packetizeSendTelecommand(self.MemGroundId, self.MemoryTaskID, self.memService, self.checkMemRequest,
											  self.checkMemCount, 1, self.currentCommand)
		if self.receiveCommandFromFifo(self.fdirToGPRFifo) > 0:
			# Deal with incoming commands from the FDIR task
			pass
		if self.receiveCommandFromFifo(self.schedToGPRFifo) > 0:
			if self.currentCommand[146] == self.addSchedule:
				self.addScheduleCount += 1
				self.packetizeSendTelecommand(self.SchedGroundId, self.SchedulingTaskID, self.kService, self.addSchedule,
											  self.addScheduleCount, 1, self.currentCommand)
			if self.currentCommand[146] == self.clearSchedule:
				self.clearScheduleCount += 1
				self.packetizeSendTelecommand(self.SchedGroundId, self.SchedulingTaskID, self.kService, self.clearSchedule,
											  self.clearScheduleCount, 1, self.currentCommand)
			if self.currentCommand[146] == self.schedReportRequest:
				self.reportRequestCount += 1
				self.packetizeSendTelecommand(self.SchedGroundId, self.SchedulingTaskID, self.kService, self.schedReportRequest,
											  self.reportRequestCount, 1, self.currentCommand)
			if self.currentCommand[146] == self.pauseScheduling:
				self.pauseScheduleCount += 1
				self.packetizeSendTelecommand(self.SchedGroundId, self.SchedulingTaskID, self.kService, self.pauseScheduling,
											  self.pauseScheduleCount, 1, self.currentCommand)
			if self.currentCommand[146] == self.resumeScheduling:
				self.resumeScheduleCount += 1
				self.packetizeSendTelecommand(self.SchedGroundId, self.SchedulingTaskID, self.kService, self.resumeScheduling,
											  self.resumeScheduleCount, 1, self.currentCommand)
		return

	@staticmethod
	def packetizeSendTelecommand(self, sender, dest, serviceType, serviceSubType, packetSubCounter, numPackets, appDataArray):

		sequenceCount = 1
		packetTime =  self.absTime.day << 12
		packetTime += self.absTime.hour << 8
		packetTime += self.absTime.minute << 4
		packetTime += self.absTime.second

		if numPackets > 1:
			sequenceFlags = 0x01
		else:
			sequenceFlags = 0x03

		# Put the new packet into a linked list of packets.
		newSendPacket = Puspacket()
		if self.sendPacketCount == 0:
			self.sendPacket = newSendPacket
			self.sendPacketCount += 1
		if self.sendPacketCount == 1:
			self.lastSendPacket = newSendPacket
			self.sendPacket.nextPacket = self.lastSendPacket
			self.lastSendPacket.prevPacket = self.sendPacket
			self.sendPacketCount += 1
		elif self.sendPacketCount > 1:
			self.lastSendPacket.nextPacket = newSendPacket
			newSendPacket.prevPacket = self.lastSendPacket
			self.lastSendPacket = newSendPacket
			self.sendPacketCount += 1
		# Get the application data for the new packet
		for i in range(0, self.dataLength):
			newSendPacket.appData[i] = appDataArray[i]
		# Fill in the attributes for the new packet
		newSendPacket.version = 0	# Default is 0
		newSendPacket.type1 = 1		# TC = 1
		newSendPacket.ccsdsFlag = 1
		newSendPacket.sender = sender
		newSendPacket.sequenceFlags = sequenceFlags
		newSendPacket.sequenceCount = sequenceCount
		newSendPacket.serviceType = serviceType
		newSendPacket.serviceSubType = serviceSubType
		newSendPacket.packetSubCounter = packetSubCounter
		newSendPacket.dest = dest
		newSendPacket.day = self.absTime.day
		newSendPacket.hour = self.absTime.hour
		newSendPacket.minute = self.absTime.minute
		newSendPacket.second = self.absTime.second
		# Format the actual data array for the packet.
		newSendPacket.formatDataArray()

		if numPackets == 1:
			return 1

		# numPackets != 1
		for i in range(0, numPackets):
			newSendPacket.data[148] = sequenceCount
			sequenceCount += 1
			if i > 1:
				sequenceFlags = 0x00
			if i == (numPackets - 1):
				sequenceFlags = 0x02
			newSendPacket.data[149] = (sequenceFlags & 0x03) << 6
			for j in range(2, (self.packetLength - 13)):
				newSendPacket.data[j] = appDataArray[j + i * 128]
			# Format the packet again.
			newSendPacket.formatDataArray()
			# Insert the new packet into the linked list for sending
			self.lastSendPacket.nextPacket = newSendPacket
			newSendPacket.prevPacket = self.lastSendPacket
			self.lastSendPacket = newSendPacket
			self.sendPacketCount += 1
			# Create a new pus packet object to work with
			newSendPacket = Puspacket()
		return

	@staticmethod
	def sendPusPacketTC(self):
		# To be implemented later.
		pass

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
		for i in range(0, (self.dataLength + 10)):
			self.currentCommand[i] = 0
		return

	@staticmethod
	def initCurrentCommand(self):
		for i in range(0, (self.dataLength + 10)):
			self.currentCommand.append(0)
		return

	@staticmethod
	def receiveCommandFromFifo(self, fifo):
		"""
		@purpose:   This method takes a command from the the fifo "fifo" which should have a
		length of 147 bytes & places it into the array self.currentCommand[].
		@Note: We use a "START\n" code and "STOP\n" code to indicate where commands stop and start.
		"""
		self.clearCurrentCommand()
		if os.path.getsize(fifo) > 152:
			i = 0
			if fifo.readline() == "START\n":
				# Start reading in the command.
				newString = fifo.readline()
				newString = newString.rstrip()
				while (newString != "STOP") and (i < (self.dataLength + 11)):
					self.currentCommand[i] = int(newString)
					newString = fifo.readline()
					newString = newString.rstrip()
					i += 1
				return 1
		return -1

	def __init__(self):
		"""
		@purpose: Initialization method for the Ground Packet Router Class
		"""
		super(groundPacketRouter, self).__init__()
		self.currentPacket = Puspacket()				# Create an empty PUS Packet.
		self.lastPacket = self.currentPacket

if __name__ == '__main__':
	x = groundPacketRouter()
	x.run()
