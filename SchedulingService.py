"""
FILE_NAME:			SchedulingService.py

AUTHOR:				Keenan Burnett

PURPOSE:			This class shall house the KService PUS service and all related methods.

FILE REFERENCES:

LIBRARIES USED:		os, multiprocessing

SUPERCLASS:			PUSService

ABNORMAL TERMINATION CONDITIONS, ERROR AND WARNING MESSAGES: None yet.

ASSUMPTIONS, CONSTRAINTS, CONDITIONS: None.

NOTES:				For the sake of human readability and computer readability, we are going to have two
					schedules. One shall be used by users to input a set of commands to be sent to the satellite.

					Human Format:

					TIME			APID		COMMAND		SEV		PARAM		COMPLETED		COMMENT
					DD/HH/MM/SS		0xFF		0xFF		0|1|2	0xFF		Y|N|E			payload stuff
																			(E = erased)
    				APID: Software ID for the process/SSM on the OBC that you are sending this command for.

    				COMMAND: Unique identifier for the command being sent (to be added in the future)

    				SEV: Severity for the command being sent, 0 = N/A, 1 = High severity -> FDIR
    					2 = Low severity -> OBC Packet Router.

    				PARAM: Anything you want that might pertain to the command (1B)

    				COMMENT: Any string you desire if it's useful to you.

    				The other shall be used by the ground scheduling service.

    				Computer Format:

    				N = Number of commands in schedule (no completed commands kept)
    				The following is repeated N times:
    				TIME
    				APID
    				COMMAND
    				SEVERITY
    				PARAM

    				For command files: These shall be added in bulk to both the human schedule and computer schedule
    				automatically for the user.

    				When "clearCommand()" is issued, the internal computer schedule is cleared, the schedule on the
    				satellite is cleared, and each of the respective commands in the human schedule is set to
    				"E" as in "erased".

    				Should the user wish to upload new commands to the schedule, simply add them to the schedule
    				document in the format provided.

    				If too many commands are requested to be placed in the schedule ( >1023) an error code will be
    				returned to the CLI and the command will be rejected.
REQUIREMENTS:

DEVELOPMENT HISTORY:

11/18/2015			Created.

11/22/2015			Started working on actually filling in the required functionality today.

"""

import os
from multiprocessing import *
from PUSService import *

class schedulingService(PUSService):
	"""
	This class is meant to represent the PUS KService which manages scheduling
	as well as the miscelleaneous commands that can be made by the user
	which did not fall under any of the other standard PUS services.
	"""
	numCommands = 0
	hSchedFile	= None
	cSchedFile	= None

	@classmethod
	def run(self):
		"""
		@purpose:   Used to house the main program for the scheduling service.
		@Note:		Since this class is a subclass of Process, when self.start() is executed on an
					instance of this class, a process will be created with the contents of run() as the
					main program.
		"""
		self.initialize(self)
		while(1):
			self.receiveCommandFromFifo(self.fifoFromGPR)
			self.execCommands(self)

	@staticmethod
	def initialize(self):
		"""
		@purpose:   - Initializes required variables for the scheduling service
		"""
		self.clearCurrentCommand()
		self.logEventReport(1, self.schedGroundInitialized, 0, 0, "Ground Scheduling Service Initialized Correctly.")
		return

	@staticmethod
	def execCommands(self):
		"""
		@purpose:   After a command has been received in the FIFO, this function parses through it
					and performs different actions based on what is received.
		"""
		if(self.currentCommand[146] == self.addSchedule):
			self.addToSchedule()
		if(self.currentCommand[146] == self.clearSchedule):
			self.clearTheSchedule()
		if(self.currentCommand[146] == self.schedReportRequest):
			self.requestSchedReport()
		if(self.currentCommand[146] == self.schedReport):
			self.processSchedReport()
		self.clearCurrentCommand()
		return

	@staticmethod
	def addToSchedule(self):
		# When this command is received from the GPR, this means that changes have been made to the human schedule
		# stored in memory.
		# This method will then add all the new commands into the computer schedule (if they fit).

		schedPath = "/scheduling/h-schedule.txt"
		self.hSchedFile = open(schedPath, "ab+")
		schedPath = "/scheduling/c-schedule.txt"
		self.cSchedFile = open(schedPath, "ab+")

		numNewCommands = self.currentCommand[145]
		if(self.numCommands + numNewCommands) > 1023:
			self.printToCLI("REQUESTED SCHEDULE ADDITION WOULD OVERFLOW SCHEDULE (>1023)\n")
			self.logError("REQUESTED SCHEDULE ADDITION WOULD OVERFLOW SCHEDULE (>1023)")
			return

		newCommandArray = []
		newCommandArray[numNewCommands * 2] = numNewCommands

		# Add the human commands into the computer schedule
		self.hSchedFile.seek(self.numCommands)
		for i in range(0, numNewCommands):
			tempString = self.hSchedFile.readline()
			tempString = tempString.rstrip()
			items = tempString.split()
			# Get rid of the whitespace in each item from the schedule.
			for item in items:
				item = item.rstrip()
				item = item.lstrip()
			# Get the time from the command
			time = items[0]
			times = time.split("/")
			commandTime = int(times[0]) << 24
			commandTime += int(times[1]) << 16
			commandTime += int(times[2]) << 8
			commandTime += int(times[3])
			# Get the remainder of the command attributes
			commandAPID = int(items[1], 16)
			commandID	= int(items[2], 16)
			commandSeverity = int(items[3])
			commandParam = int(items[4], 16)
			# Add the command to the computer schedule
			self.addCommandToSchedule(commandTime, commandAPID, commandID, commandSeverity, commandParam)
			# Put the command in an array for sending to the OBC.
			newCommandArray[(numNewCommands * 2) - (i * 2)] = commandTime
			newCommandArray[(numNewCommands * 2) - (i * 2 + 1)] = (commandAPID << 24) + (commandID << 16) + (commandSeverity << 8) + commandParam

		#Send the commands to the OBC, one packet @ a time.
		self.sendCommandsToOBC(numNewCommands, newCommandArray)
		return

	@staticmethod
	def addCommandToSchedule(self, time, apid, id, severity, param):
		byte2 = (apid << 24) & (id << 16) & (severity << 8) & param
		self.cSchedFile.write(str(time) + "\n")
		self.cSchedFile.write(str(byte2) + "\n")
		self.numCommands += 1
		return

	@staticmethod
	def sendCommandsToOBC(self, numNewCommands, commandArray):
		# The maximum number of commands that will fit into a single PUS packet is 16.
		leftOver = 0
		if(numNewCommands > 16):
			numPackets = numNewCommands / 16
			if(numNewCommands % 16):
				leftOver = numNewCommands % 16

			for i in range(0, numPackets - 1):
				self.printToCLI("SENDING COMMAND PACKET %s OF %s\n" %str(i + 1) %str(numPackets))
				self.clearCurrentCommand()
				self.currentCommand[146] = self.addSchedule
				self.currentCommand[145] = numPackets - i
				self.currentCommand[136] = 16
				for j in range(127, -1, -8):
					tempTime = commandArray[(numNewCommands * 2) - (i * 32) - ((j + 1) / 8)]
					tempInt2 = commandArray[(numNewCommands * 2) - (i * 32) - ((j + 1) / 8) - 1]
					self.currentCommand[j] 		= (tempTime & 0xFF000000) >> 24
					self.currentCommand[j - 1] 	= (tempTime & 0x00FF0000) >> 16
					self.currentCommand[j - 2] 	= (tempTime & 0x0000FF00) >> 8
					self.currentCommand[j - 3] 	= tempTime & 0x000000FF
					self.currentCommand[j - 4] 	= (tempInt2 & 0xFF000000) >> 24
					self.currentCommand[j - 5] 	= (tempInt2 & 0xFF000000) >> 16
					self.currentCommand[j - 6] 	= (tempInt2 & 0xFF000000) >> 8
					self.currentCommand[j - 7] 	= tempInt2 & 0xFF000000
				# Send the command to the GPR to be sent to the OBC
				self.sendCurrentCommandToFifo(self.fifoToGPR)

			if(leftOver):
				self.printToCLI("SENDING COMMAND PACKET %s OF %s\n" %str(i + 1) %str(numPackets))
				self.clearCurrentCommand()
				self.currentCommand[146] = self.addSchedule
				self.currentCommand[145] = 1
				self.currentCommand[136] = leftOver
				for j in range((leftOver * 8 - 1), -1, -8):
					tempTime = commandArray[(numNewCommands * 2) - ((j + 1) / 8)]
					tempInt2 = commandArray[(numNewCommands * 2) - ((j + 1) / 8) - 1]
					self.currentCommand[j] 		= (tempTime & 0xFF000000) >> 24
					self.currentCommand[j - 1] 	= (tempTime & 0x00FF0000) >> 16
					self.currentCommand[j - 2] 	= (tempTime & 0x0000FF00) >> 8
					self.currentCommand[j - 3] 	= tempTime & 0x000000FF
					self.currentCommand[j - 4] 	= (tempInt2 & 0xFF000000) >> 24
					self.currentCommand[j - 5] 	= (tempInt2 & 0xFF000000) >> 16
					self.currentCommand[j - 6] 	= (tempInt2 & 0xFF000000) >> 8
					self.currentCommand[j - 7] 	= tempInt2 & 0xFF000000
					# Send the command to the GPR to be sent to the OBC
				self.sendCurrentCommandToFifo(self.fifoToGPR)
		else:
			self.printToCLI("SENDING COMMAND PACKET %s OF %s\n" %str(1) %str(1))
			self.clearCurrentCommand()
			self.currentCommand[146] = self.addSchedule
			self.currentCommand[145] = 1
			self.currentCommand[136] = numNewCommands
			for j in range((numNewCommands * 8 - 1), -1, -8):
				tempTime = commandArray[(numNewCommands * 2) - ((j + 1) / 8)]
				tempInt2 = commandArray[(numNewCommands * 2) - ((j + 1) / 8) - 1]
				self.currentCommand[j] 		= (tempTime & 0xFF000000) >> 24
				self.currentCommand[j - 1] 	= (tempTime & 0x00FF0000) >> 16
				self.currentCommand[j - 2] 	= (tempTime & 0x0000FF00) >> 8
				self.currentCommand[j - 3] 	= tempTime & 0x000000FF
				self.currentCommand[j - 4] 	= (tempInt2 & 0xFF000000) >> 24
				self.currentCommand[j - 5] 	= (tempInt2 & 0xFF000000) >> 16
				self.currentCommand[j - 6] 	= (tempInt2 & 0xFF000000) >> 8
				self.currentCommand[j - 7] 	= tempInt2 & 0xFF000000
				# Send the command to the GPR to be sent to the OBC
			self.sendCurrentCommandToFifo(self.fifoToGPR)

		self.printToCLI("UPLOADING NEW SCHEDULE COMPLETED\n")
		return

	def __init__(self, path1, path2, path3, path4, tcLock, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock,
							errorLock, day, hour, minute, second):
		# Initialize this instance as a PUS service
		super(schedulingService, self).__init__(path1, path2, tcLock, eventPath, hkPath, errorPath, eventLock, hkLock,
							cliLock, errorLock, day, hour, minute, second)

		# FIFOs for communication with the FDIR service
		self.fifotoFDIR = open(path3, "wb")
		self.fifofromFDIR = open(path4, "rb")

if __name__ == '__main__':
	pass
	