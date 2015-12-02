"""
FILE_NAME:			MemoryService.py

AUTHOR:				Keenan Burnett

PURPOSE:			This class shall house the memory management PUS service and all related methods.

FILE REFERENCES:

LIBRARIES USED:		os, multiprocessing, datetime

SUPERCLASS:			PUSService

ABNORMAL TERMINATION CONDITIONS, ERROR AND WARNING MESSAGES: None yet.

ASSUMPTIONS, CONSTRAINTS, CONDITIONS: None.

NOTES:
		For memory loads and memory dumps, the following format should be followed:
		1. Place the file in the correct directory: /memory/load/ for uploading files
			and /memory/dump for files that you want satellite memory to be download to.
		2. The first line shall contain the memoryID on the satellite that you want to write to.
			0 == OBC Main memory. 1 == EXternal SPI Memory.
		2. The second line of the file shall contain the absolute starting address in the 
			satellite's memory that you wish to load/dump at. NOTE: That the address should
			be listed in hexadecimal ex: 0x00000000, or 0x12345678
		3. The third line of the file shall contain the number of INTEGERS you want to load.
		4. The remainder of the file shall be each INTEGER that you wish to load into the. (use decimal notation here)
			satellite's memory, followed by a newline character after each.
		5. Do not place an empty line at the end of the file.
		6. The first Integer to be loaded to into satellite memory is on line 4.

		To execute a memory load / dump, you may use the specified CLI command or command
		file followed by the filename you placed in /memory/.. (filename should include the extension)

		For TC verification, what we're going to do is use special .tcVerification attributes which the GPR has access to.
		-Services can then loop on this attribute being 0 with a generous timeout
		-GPR then inserts the PacketID/PSC into the attribute when a TC Acceptance/Execution Report is received.

REQUIREMENTS:

DEVELOPMENT HISTORY:

11/17/2015			Created.

11/20/2015			Currently working on the bulk of this service's functionality including loadToSatelliteMemory()

11/21/2015			Finished writing the majority of the code that was required for this service today.

"""

import os
from multiprocessing import *
from PUSService import *
from datetime import *

class MemoryService(PUSService):
	"""
	This class is meant to represent the PUS Memory Management Service.
	"""
	localSequence 	= 0		# These shall be used to keep track of the sequence of incoming PUS dump packets.
	localFlags	  	= -1
	dumpCount	 	= 0		# Counter for the number of memory dumps that have been created so far.
	checkCount		= 0
	sequenceOffset	= 0
	packetsRequested = 0
	dumpFile		= None
	checkFile		= None
	memoryOperations ={
		0x02		:	"MEMORY LOAD (ABSOLUTE)",
		0X05		:	"DUMP REQUEST (ABSOLUTE)",
		0x06		:	"MEMORY DUMP (ABSOLUTE)",
		0X09		:	"CHECK MEMORY REQUEST (ABSOLUTE)",
		0X0A 		:	"MEMORY CHECK (ABSOLUTE)"
	}

	@staticmethod
	def run1(self):
		"""
		@purpose:   Used to house the main program for the memory management service.
		@Note:		Since this class is a subclass of Process, when self.start() is executed on an
					instance of this class, a process will be created with the contents of run1() as the
					main program.
		"""
		print("The path in mem run: %s" %str(self.p1))
		self.initializePUS(self)
		self.initialize(self)
		while 1:
			self.receiveCommandFromFifo(self.fifoFromGPR)		# If command in FIFO, places it in self.currentCommand[]
			self.execCommands(self)								# Deals with commands from GPR
		return				# This should never be reached.

	@staticmethod
	def initialize(self):
		"""
		@purpose:   - Initializes required variables for the memory service.
		"""
		self.clearCurrentCommand()
		self.logEventReport(1, self.memgroundinitialized, 0, 0, "Ground Memory Service Initialized Correctly.")
		return

	@staticmethod
	def initializePUS(self):
		# FIFOs Required for communication with the Ground Packet Router:
		self.fifoFromGPR			= open(self.p2, "rb", 0)
		#os.mkfifo(self.p1)
		self.fifoToGPR				= open(self.p1, "wb")
		self.fifoToGPRPath			= self.p1
		self.wait					= 1
		self.fifoFromGPRPath		= self.p2
		self.createAndOpenFifoToFDIR()
		self.openFifoFromFDIR()
		return

	@staticmethod
	def execCommands(self):
		"""
		@purpose:   After a command has been received in the FIFO, this function parses through it
					and performs different actions based on what is received.
		"""
		if self.currentCommand[146] == self.memoryLoadABS:
			self.loadToSatelliteMemory()
		if self.currentCommand[146] == self.dumpRequestABS:
			self.sendDumpRequest()
		if self.currentCommand[146] == self.memoryDumpABS:
			self.processMemoryDump()
		if self.currentCommand[146] == self.checkMemRequest:
			self.sendCheckMemRequest()
		if self.currentCommand[146] == self.memoryCheckABS:
			self.processMemoryCheck()
		self.clearCurrentCommand()
		return

	@staticmethod
	def loadToSatelliteMemory(self):
		"""
		@purpose: 	When a command is received to load some data to the memory on the OBC, this method will handle
					breaking up the data into individual packets, sending them to GPR so they may be telecommanded,
					and keeping track of packets being recevied.
		@Note: 		The GPR should place the name of the file being read in currentCommand[145] ... until done.
					(obviously you shouldn't make the length of the filename over 146 characters.
		"""
		fileName = None
		i = 145
		x = 0
		# Load the name of the file into fileName
		while self.currentCommand[i]:
			fileName += self.currentCommand[i]
			i -= 1

		filePath = "/memory/load/" + fileName
		fileToLoad = open(filePath, "rb")

		tempString1		= (fileToLoad.readline()).rstrip()
		memoryID 		= int(tempString1)
		tempString2 	= (fileToLoad.readline()).rstrip()
		startingAddress = int(tempString2, 16)
		tempString3		= (fileToLoad.readline()).rstrip()
		lengthToLoad	= int(tempString3)
		self.printToCLI("Attempting to upload %s Bytes from File: %s to Address: %s in Memory: %s on the satellite...\n"
									%tempString3 %fileName %tempString2 %tempString1)
		self.logEventReport(1, self.loadingFileToSat, 0, 0,
						"Attempting to upload %s Bytes from File: %s to Address: %s in Memory: %s on the satellite...\n"
									%tempString3 %fileName %tempString2 %tempString1)

		lengthToLoadInBytes = lengthToLoad * 4
		numPackets = lengthToLoadInBytes / 128
		leftOver = lengthToLoadInBytes % 128

		for i in range(0, numPackets):
			self.clearCurrentCommand()
			self.currentCommand[146] = self.memoryLoadABS
			self.currentCommand[145] = numPackets - i
			self.currentCommand[136] = memoryID
			self.currentCommand[135] = ((startingAddress + i * 128) & 0xFF000000) >> 24
			self.currentCommand[134] = ((startingAddress + i * 256) & 0x00FF0000) >> 16
			self.currentCommand[133] = ((startingAddress + i * 256) & 0x0000FF00) >> 8
			self.currentCommand[132] = (startingAddress + i * 256) & 0x000000FF
			self.currentCommand[131] = ((lengthToLoadInBytes - i * 256) & 0xFF000000) >> 24
			self.currentCommand[130] = ((lengthToLoadInBytes - i * 256) & 0x00FF0000) >> 16
			self.currentCommand[129] = ((lengthToLoadInBytes - i * 256) & 0x0000FF00) >> 8
			self.currentCommand[128] = (lengthToLoadInBytes - i * 256) & 0x000000FF
			for j in range(0, self.dataLength, 4):
				num = int((fileToLoad.readline()).rstrip())
				self.currentCommand[j] = (num & 0x000000FF)
				self.currentCommand[j + 1] = (num & 0x0000FF00) >> 8
				self.currentCommand[j + 2] = (num & 0x0000FF00) >> 16
				self.currentCommand[j + 3] = (num & 0x0000FF00) >> 24
			# Send the currentCommand[] to GPR.
			self.printToCLI("UPLOADING: %s OF %s PACKETS FOR MEM LOAD\n" %str(numPackets) %str(numPackets))
			self.sendCurrentCommandToFifo(self.fifoToGPR)
			if self.waitForTCVerification(5000, self.memoryLoadABS) < 0:
				return

		if leftOver:
			self.currentCommand[146] = self.memoryLoadABS
			self.currentCommand[145] = numPackets - i
			self.currentCommand[136] = memoryID
			self.currentCommand[135] = ((startingAddress + i * 128) & 0xFF000000) >> 24
			self.currentCommand[134] = ((startingAddress + i * 256) & 0x00FF0000) >> 16
			self.currentCommand[133] = ((startingAddress + i * 256) & 0x0000FF00) >> 8
			self.currentCommand[132] = (startingAddress + i * 256) & 0x000000FF
			self.currentCommand[131] = (leftOver & 0xFF000000) >> 24
			self.currentCommand[130] = (leftOver & 0x00FF0000) >> 16
			self.currentCommand[129] = (leftOver & 0x0000FF00) >> 8
			self.currentCommand[128] = leftOver & 0x000000FF
			for j in range(0, leftOver, 4):
				num = int((fileToLoad.readline()).rstrip())
				self.currentCommand[j] = (num & 0x000000FF)
				self.currentCommand[j + 1] = (num & 0x0000FF00) >> 8
				self.currentCommand[j + 2] = (num & 0x0000FF00) >> 16
				self.currentCommand[j + 3] = (num & 0x0000FF00) >> 24
			# Send the currentCommand[] to GPR.
			self.printToCLI("UPLOADING: %s OF %s PACKETS FOR MEM LOAD\n" %str(numPackets) %str(numPackets))
			self.sendCurrentCommandToFifo(self.fifoToGPR)
			x = self.waitForTCVerification(5000, self.memoryLoadABS)
			if x < 0:
				return
			self.printToCLI("UPLOADING COMPLETE FOR MEM LOAD\n")
			self.logEventReport(1, self.loadCompleted, 0, 0, "UPLOAD COMPLETE FOR MEM LOAD")
		return

	@staticmethod
	def sendDumpRequest(self):
		"""
		@purpose: 	This method will send a command array to the GPR so that a telecommand may be created
					requested a memory dump.
		"""
		self.printToCLI("SENDING A DUMP REQUEST TO THE SATELLITE...\n")
		# Store the number of packets which are being requested.
		length = self.currentCommand[131] << 24
		length += self.currentCommand[130] << 16
		length += self.currentCommand[129] << 8
		length += self.currentCommand[128]
		lengthToLoadInBytes = length * 4
		numPackets = lengthToLoadInBytes / 128
		if lengthToLoadInBytes % 128:
			numPackets += 1
		self.packetsRequested = numPackets
		self.currentCommand[146] = self.dumpRequestABS
		self.sendCurrentCommandToFifo(self.fifoToGPR)
		x = self.waitForTCVerification(5000, self.dumpRequestABS)	# Wait <= 5s for the command to be accepted/executed
		if x > 0:
			self.printToCLI("DUMP REQUEST ACCEPTED AND STARTED...\n")
		return

	@staticmethod
	def processMemoryDump(self):
		"""
		@purpose: 	When a memory-dump packet is received, this method is tasked with checking if we can/should
					store it in memory. Things that need be checked include the sequence flags / count.
		"""
		obcSequenceFlags	= self.currentCommand[143]
		obcSequenceCount	= self.currentCommand[142]

		if obcSequenceFlags == 0x01:
			if self.localFlags == -1:	# The First packet of several.
				self.localSequence = obcSequenceCount
				self.sequenceOffset = obcSequenceCount
				self.localFlags = obcSequenceFlags
			else:
				self.currentCommand[146] = self.dumpPacketWrong				# Packet is rejected.
				self.sendCurrentCommandToFifo(self.fifotoFDIR)
				self.localSequence = 0
				self.localFlags = -1
				return
		if obcSequenceFlags == 0x11:
			if self.localFlags == -1:	# The First packet of several.
				self.localSequence = obcSequenceCount
				self.localFlags = obcSequenceFlags
			else:
				self.currentCommand[146] = self.dumpPacketWrong
				self.sendCurrentCommandToFifo(self.fifotoFDIR)
				self.localSequence = 0
				self.localFlags = -1
				return
		if obcSequenceFlags == 0x00:
			if (self.localFlags == 0x01) or (self.localFlags == 0x00) and (self.localSequence < obcSequenceCount):
				self.localSequence = obcSequenceCount
				self.localFlags = obcSequenceFlags
			else:
				self.currentCommand[146] = self.dumpPacketWrong
				self.sendCurrentCommandToFifo(self.fifotoFDIR)
				self.localSequence = 0
				self.localFlags = -1
				return
		if obcSequenceFlags == 0x11:
			if (self.localFlags == 0x00) and (self.localSequence < obcSequenceCount):
				self.localSequence = obcSequenceCount
				self.localFlags = obcSequenceFlags
			else:
				self.currentCommand[146] = self.dumpPacketWrong
				self.sendCurrentCommandToFifo(self.fifotoFDIR)
				self.localSequence = 0
				self.localFlags = -1
				return

		# Print something meaningful to the CLI.
		if self.localFlags == 0x01:
			self.printToCLI("DOWNLOADING PACKET 1 OF %s FOR MEM DUMP\n" %str(self.packetsRequested))
		if self.localFlags == 0x11:
			self.printToCLI("DOWNLOADING PACKET 1 of 1 FOR MEM DUMP\n")
		if self.localFlags == 0x00:
			packetNum = obcSequenceCount - self.sequenceOffset + 1
			self.printToCLI("DOWNLOADING PACKET %s OF %s FOR MEM DUMP\n" %str(packetNum) %str(self.packetsRequested))
		if self.localFlags == 0x10:
			packetNum = obcSequenceCount - self.sequenceOffset + 1
			self.printToCLI("DOWNLOADING PACKET %s OF %s FOR MEM DUMP\n" %str(packetNum) %str(self.packetsRequested))
			self.printToCLI("DOWNLOAD COMPLETE FOR MEM DUMP %s\n" %str(self.dumpCount))
			self.logEventReport(1, self.dumpCompleted, 0, 0, "DOWNLOAD COMPLETE FOR MEM DUMP %s" %str(self.dumpCount))
		# Write the contents of the incoming PUS packet into a memory dump file.
		if self.localFlags == 0x01 or self.localFlags == 0x11:
			memPath = "/memory/dumps/memdump%s" %str(self.dumpCount)		#Create a new file for the mem dump.
			if os.path.exists(memPath):
				self.dumpFile = open(memPath, "ab+")
			else:
				self.dumpFile = open(memPath, "ab")

			self.dumpFile.write(str(self.currentCommand[136]) + "\n")		# The memoryID goes @ the top of the file
			address = self.currentCommand[135] << 24
			address += self.currentCommand[134] << 16
			address += self.currentCommand[133] << 8
			address += self.currentCommand[132]
			length = self.currentCommand[131] << 24
			length += self.currentCommand[130] << 16
			length += self.currentCommand[129] << 8
			length += self.currentCommand[128]
			self.dumpFile.write(str(hex(address)) + "\n")					# Followed by address (in hex)
			self.dumpFile.write(str(length) + "\n")							# And then length (in bytes, decimal)
			for i in range(0, 128):
				self.dumpFile.write(str(self.currentCommand[i]) + "\n")
		if self.localFlags == 0x00 or self.localFlags == 0x10:
			for i in range(0, 128):
				self.dumpFile.write(str(self.currentCommand[i]) + "\n")
		if self.localFlags == 0x10:
			self.localSequence = 0
			self.localFlags = -1
			self.dumpCount += 1
		return

	@staticmethod
	def sendCheckMemRequest(self):
		"""
		@purpose: 	This method sends a command to the GPR for a telecommand of this king to be sent to the satellite
		"""
		self.currentCommand[146] = self.checkMemRequest
		self.sendCurrentCommandToFifo(self.fifoToGPR)
		self.waitForTCVerification(5000, self.checkMemRequest)

	@staticmethod
	def processMemoryCheck(self):
		"""
		@purpose: 	When a memory-check packet is received, this method parses through it and stores it in memory.
		@Note:		The file in which the checksum is stored : "/memory/checks/memcheck%s" %str(self.checkCount)
		"""
		self.currentCommand[146] = self.memoryCheckABS
		# Get the address and length of the checksum that was computed
		address = self.currentCommand[135] << 24
		address += self.currentCommand[134] << 16
		address += self.currentCommand[133] << 8
		address += self.currentCommand[132]
		length = self.currentCommand[131] << 24
		length += self.currentCommand[130] << 16
		length += self.currentCommand[129] << 8
		length += self.currentCommand[128]
		# Load the value of the checksum into the checkSum variable
		checkSum	=  long(self.currentCommand[7]	<< 56)
		checkSum	+= long(self.currentCommand[6]	<< 48)
		checkSum	+= long(self.currentCommand[5]	<< 40)
		checkSum	+= long(self.currentCommand[4]	<< 32)
		checkSum	+= long(self.currentCommand[3]	<< 24)
		checkSum	+= long(self.currentCommand[2]	<< 16)
		checkSum	+= long(self.currentCommand[1]	<< 8)
		checkSum	+= long(self.currentCommand[0])
		# Store the checksum in memory.
		checkPath = "/memory/checks/memcheck%s" %str(self.checkCount)		#Create a new file for the mem check.
		if os.path.exists(checkPath):
			self.checkFile = open(checkPath, "wb+")
		else:
			self.checkFile = open(checkPath, "ab")

		self.dumpFile.write(str(self.currentCommand[136]) + "\n")		# The memoryID goes @ the top of the file
		self.dumpFile.write(str(hex(address)) + "\n")					# Followed by address (in hex)
		self.dumpFile.write(str(length) + "\n")							# And then length (in bytes)
		self.printToCLI()

		self.checkCount += 1
		return

	@staticmethod
	def waitForTCVerification(self, timeOut, operation):
		"""
		@purpose: 	This method is used to put the current service on hold until a successful TC Acceptance
					report and TC Execution report have been received.
		@param:		timeOut: This method will wait for a maximum of 'timeOut' milliseconds for the verification to be
					received.
		@param:		operation: is the code for the operation to be completed
		"""
		waitTime = datetime.timedelta(0)
		while (waitTime.milliseconds < timeOut) and (not self.tcAcceptVerification or not self.tcExecuteVerification):
			pass
		if waitTime > timeOut:
			self.printToCLI("MEMORY SERVICE OPERATION: %s HAS FAILED\n" %self.memoryOperations[operation])
			self.logError("MEMORY SERVICE OPERATION: %s HAS FAILED" %self.memoryOperations[operation])
			self.currentCommand[146] = operation
			self.sendCurrentCommandToFifo(self.fifotoFDIR)
			return -1
		else:
			self.logEventReport(1, operation, 0, 0,
								"MEMORY SERVICE OPERATION: %s HAS SUCCEEDED" %self.memoryOperations[operation])
			self.tcLock.acquire()
			self.tcAcceptVerification = 0
			self.tcExecuteVerification = 0
			self.tcLock.release()
			return 1

	def __init__(self, path1, path2, path3, path4, tcLock, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock,
				 	errorLock, day, hour, minute, second):
		# Initialize this instance as a PUS service
		super(MemoryService, self).__init__(path1, path2, path3, path4, tcLock, eventPath, hkPath, errorPath, eventLock, hkLock,
					cliLock, errorLock, day, hour, minute, second)
		self.processID = 0x12
		self.serviceType = 6
		self.spiChip1 = 1
		self.spiChip2 = 1
		self.spiChip3 = 1
		self.p1 = path1
		self.p2 = path2
		pID = os.fork()
		if pID:

			self.pID = pID
			return
		else:
			self.run1(self)

if __name__ == '__main__':
	pass
	