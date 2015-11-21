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

"""

import os
from multiprocessing import *
from PUSService import *
from datetime import *

class MemoryService(PUSService):
	"""
	This class is meant to represent the PUS Memory Management Service.
	"""
	@classmethod
	def run(self):
		"""
		@purpose:   Used to house the main program for the memory management service.
		@Note:		Since this class is a subclass of Process, when self.start() is executed on an
					instance of this class, a process will be created with the contents of run() as the
					main program.
		"""
		self.initialize(self)

		while(1):
			self.receiveCommandFromFifo(self.fifoFromGPR)		# If command in FIFO, places it in self.currentCommand[]
			self.execCommands(self)										# Deals with commands from GPR
		return				# This should never be reached.

	@staticmethod
	def initialize(self):
		"""
		@purpose:   - Initializes required variables for the memory service.
		"""
		self.clearCurrentCommand()
		self.logEventReport(1, self.hkgroundinitialized, 0, 0, "Ground Memory Service Initialized Correctly.")
		return

	@staticmethod
	def execCommands(self):
		"""
		@purpose:   After a command has been received in the FIFO, this function parses through it
					and performs different actions based on what is received.
		"""
		if(self.currentCommand[146] == self.memoryLoadABS):
			self.loadToSatelliteMemory()
		if(self.currentCommand[146] == self.dumpRequestABS):
			self.sendDumpRequest()
		if(self.currentCommand[146] == self.memoryDumpABS):
			self.processMemoryDump()
		if(self.currentCommand[146] == self.checkMemRequest):
			self.sendCheckMemRequest()
		if(self.currentCommand[146] == self.memoryCheckABS):
			self.processMemoryCheck()

	@staticmethod
	def loadToSatelliteMemory(self):
		# The name of the file should be placed in currentCommand[145] ... until done
		# (obviously don't make the filename over 146 characters.)
		fileName = None
		i = 145
		x = 0
		# Load the name of the file into fileName
		while(self.currentCommand[i]):
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
		self.printToCLI("Attempting to load %s Bytes from File: %s to Address: %s in Memory: %s on the satellite...\n"
									%tempString3 %fileName %tempString2 %tempString1)
		self.logEventReport(1, self.loadingFileToSat, 0, 0,
						"Attempting to load %s Bytes from File: %s to Address: %s in Memory: %s on the satellite...\n"
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
			self.printToCLI("LOADING: %s of %s packets\n" %str(j) %numPackets)
			self.sendCurrentCommandToFifo(self.fifoToGPR)
			x = waitForTCVerification()
			if (x < 0):
				return

		if(leftOver):
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
			self.printToCLI("LOADING: %s of %s packets\n" %numPackets %numPackets)
			self.sendCurrentCommandToFifo(self.fifoToGPR)
			x = waitForTCVerification(5000)
			if (x < 0):
				return
			self.printToCLI("LOADING COMPLETE\n")
			self.logEventReport(1, self.loadCompleted, 0, 0, "LOAD COMPLETE")
		return




	def waitForTCVerification(self, timeOut):
		#TimeOut should be in terms of milliseconds.
		waitTime = datetime.timedelta(0)
		while((waitTime.milliseconds < timeOut) and (not self.tcAcceptVerification or not self.tcExecuteVerification)):
			pass
		if(waitTime > timeOut):
			self.printToCLI("THE LOAD OPERATION HAS FAILED")
			self.logError("THE LOAD OPERATION HAS FAILED.")
			self.currentCommand[146] = self.loadOperatonFailed
			self.sendCurrentCommandToFifo(self.fifotoFDIR)
			return -1
		else:
			self.tcLock.acquire()
			self.tcAcceptVerification = 0
			self.tcExecuteVerification = 0
			self.tcLock.release()
			return 1

	def __init__(self, path1, path2, path3, path4, tcLock, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock,
				 	errorLock, day, hour, minute, second):
		# Inititalize this instance as a PUS service
		super(MemoryService, self).__init__(path1, path2, tcLock, eventPath, hkPath, errorPath, eventLock, hkLock,
					cliLock, errorLock, day, hour, minute, second)
		self.processID = 0x12
		self.serviceType = 6
		self.spiChip1 = 1
		self.spiChip2 = 1
		self.spiChip3 = 1

		# FIFOs for communication with the FDIR service
		self.fifotoFDIR = open(path3, "wb")
		self.fifofromFDIR = open(path4, "rb")

if __name__ == '__main__':
	pass
	