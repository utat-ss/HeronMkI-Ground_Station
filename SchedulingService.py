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
					DD/HH/MM/SS		0xFF		0xFF		0|1|2	0xFF		Y|N|E|F			payload stuff
																			(E = erased, F = failed)
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

11/23/2015			Adding some code for clearTheSchedule()

11/24/2025			Finishing up writing the initial draft for this code today.

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
	localSequence = 0
	localFlags = -1
	packetsRequested = 0
	sequenceOffset = 0
	schedReportCount = 0
	hSchedFile	= None
	cSchedFile	= None
	incomingSatelliteSchedule = []
	numIncomingCommands = 0
	schedWaitTime = datetime.timedelta(0)
	schedOperations ={
		0x01			: "ADD SCHEDULE",
		0x02			: "CLEAR SCHEDULE",
		0x03			: "SCHEDULE REPORT REQUEST",
		0x05			: "UPDATING SCHEDULE"
	}

	@classmethod
	def run(self):
		"""
		@purpose:   Used to house the main program for the scheduling service.
		@Note:		Since this class is a subclass of Process, when self.start() is executed on an
					instance of this class, a process will be created with the contents of run() as the
					main program.
		@Note:		The scheduling service shall ask for a schedule report from the satellite in order to update
					the schedule roughly once every minute.
		"""
		self.initialize(self)
		while 1:
			self.receiveCommandFromFifo(self.fifoFromGPR)
			self.execCommands(self)
			self.updateScheduleAutomatically(self)

	@staticmethod
	def initialize(self):
		"""
		@purpose:   - Initializes required variables for the scheduling service
		"""
		self.clearCurrentCommand()
		self.clearIncomingSatSchedule()
		self.logEventReport(1, self.schedGroundInitialized, 0, 0, "Ground Scheduling Service Initialized Correctly.")
		return

	@staticmethod
	def execCommands(self):
		"""
		@purpose:   After a command has been received in the FIFO, this function parses through it
					and performs different actions based on what is received.
		"""
		if self.currentCommand[146] == self.addSchedule:
			self.addToSchedule()
		if self.currentCommand[146] == self.clearSchedule:
			self.clearTheSchedule()
		if self.currentCommand[146] == self.schedReportRequest:
			self.requestSchedReport()
		if self.currentCommand[146] == self.schedReport:
			self.processSchedReport()
		if self.currentCommand[146] == self.schedCommandCompleted:		# Event reports on completed command should be going here.
			self.updateScheduleWithCommandStatus()
		self.clearCurrentCommand()
		return

	@staticmethod
	def addToSchedule(self):
		"""
		@purpose: 	This method is used
		@param:		timeOut: This method will wait for a maximum of 'timeOut' milliseconds for the verification to be
					received.
		@param:		operation: is the code for the operation to be completed
		"""
		# When this command is received from the GPR, this means that changes have been made to the human schedule
		# stored in memory.
		# This method will then add all the new commands into the computer schedule (if they fit).

		schedPath = "/scheduling/h-schedule.txt"
		self.hSchedFile = open(schedPath, "wb+")
		schedPath = "/scheduling/c-schedule.txt"
		self.cSchedFile = open(schedPath, "wb+")

		numNewCommands = self.currentCommand[145]
		if(self.numCommands + numNewCommands) > 1023:
			self.printToCLI("REQUESTED SCHEDULE ADDITION WOULD OVERFLOW SCHEDULE (>1023)\n")
			self.logError("REQUESTED SCHEDULE ADDITION WOULD OVERFLOW SCHEDULE (>1023)")
			return

		newCommandArray = []
		newCommandArray[numNewCommands * 2] = numNewCommands
		# Add the human commands into the computer schedule
		self.hSchedFile.seek(0)
		for line in self.hSchedFile:
			tempString = line.rstrip()
			items = tempString.split()
			# Get rid of the whitespace in each item from the schedule.
			i = 0
			items1 = []
			for item in items:
				item = item.rstrip()
				item = item.lstrip()
				items1[i] = item
				i += 1
			# Check to make sure the command is one that is yet to be completed (completed = "N")
			if items1[5] == "N":
				# Get the time from the command
				time = items1[0]
				times = time.split("/")
				commandTime = int(times[0]) << 24
				commandTime += int(times[1]) << 16
				commandTime += int(times[2]) << 8
				commandTime += int(times[3])
				# Get the remainder of the command attributes
				commandAPID = int(items1[1], 16)
				commandID	= int(items1[2], 16)
				commandSeverity = int(items1[3])
				commandParam = int(items1[4], 16)
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
		"""
		@purpose: 	This method is used to write a single command to the computer schedule with the given parameters.
		@param:		time: time for the command
		@param:		apid: Process ID for which the command is meant for.
		@param: 	severity: See file header for details.
		@param:		param: Anything you want, can be utilized on the OBC if necessary.
		"""
		byte2 = (apid << 24) & (id << 16) & (severity << 8) & param
		self.cSchedFile.seek(0, 2)	# Go to the end of the file.
		self.cSchedFile.write(str(time) + "\n")
		self.cSchedFile.write(str(byte2) + "\n")
		self.numCommands += 1
		return

	@staticmethod
	def sendCommandsToOBC(self, numNewCommands, commandArray):
		"""
		@purpose: 	Takes a given number of new commands, and the array that contains them, and proceeds to
					parse them into individual command Arrays that the GPR can easily telecommand to the satellite.
		@param:		numNewCommands: self-evident
		@param:		commandArray: An array of ints where 2 adjacent INTs correspond to TIME and INT2 which together
					form a command that can be stored in the computer schedule on either the ground station or OBC.
		@Note: The maximum number of commands that will fit into a single PUS packet is 16.
		"""
		leftOver = 0
		if numNewCommands > 16 :
			numPackets = numNewCommands / 16
			if numNewCommands % 16:
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
				if self.waitForTCVerification(1000, self.addSchedule) < 0:
					return

			if leftOver:
				self.printToCLI("SENDING COMMAND PACKET %s OF %s\n" %str(numPackets) %str(numPackets))
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
				if self.waitforTCVerification(1000, self.addSchedule) < 0:
					return
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
			if self.waitforTCVerication(1000, self.addSchedule) < 0:
				return

		self.printToCLI("UPLOADING NEW SCHEDULE COMPLETED\n")
		return

	@staticmethod
	def clearTheSchedule(self):
		tempWait = datetime.timedelta(0)
		# First get a schedule report from the satellite in case some actions were completed very recently.
		self.requestSchedReport()
		self.clearCurrentCommand()
		# Continue on with regular operation here for a maximum of one minute.
		while (tempWait.seconds < 59) and (self.currentCommand[146] != self.schedReport):
			self.receiveCommandFromFifo(self.fifoFromGPR)
			self.execCommands()

		if self.currentCommand[146] != self.schedReport:
			self.printToCLI("CANNOT CLEAR SCHEDULE, SCHEDULE REPORT TOOK TOO LONG TO COME BACK.\n")
			self.logError("CANNOT CLEAR SCHEDULE, SCHEDULE REPORT TOOK TOO LONG TO COME BACK.")
			self.execCommands() # Run the command which we might currently have.
			self.clearCurrentCommand()
			self.currentCommand[146] = self.clearSchedule
			self.sendCurrentCommandToFifo(self.fifotoFDIR)		# Send the command to the FDIR task.
		# Next, update the schedule.
		elif self.currentCommand[146] == self.schedReport:
				self.processSchedReport()						# Updates the schedule with the incoming schedule report
		# Next, attempt to clear the schedule on the satellite.
		if self.clearTheScheduleH() < 0:
			return
		# Next, erase all the commands from the computer schedule
		self.clearComputerSchedule()
		# Next, set all commands which haven't been completed yet to E in the schedule
		self.eraseCommandsInHumanSchedule()
		# Lastly, send a command to the satellite to clear the schedule.
		self.currentCommand[146] = self.clearSchedule
		self.sendCurrentCommandToFifo()
		if self.waitForTCVerification(10000, self.clearSchedule) > 0:		# Erasing can take a long time
			self.printToCLI("SCHEDULE HAS BEEN CLEARED ON SATELLITE AND GROUND\n")
			self.logEventReport(1, self.scheduleCleared, 0, 0, "SCHEDULE HAS BEEN CLEARED ON SATELLITE AND GROUND")
		return

	@staticmethod
	def eraseCommandsInHumanSchedule(self):
		lCount = 0
		for line in self.hSchedFile:
			tempString = line.rstrip()
			tempString = tempString.lstrip()
			items = tempString.split()
			# Get rid of the whitespace in each item from this line in the schedule.
			i = 0
			items1 = []
			for item in items:
				item = item.rstrip()
				item = item.lstrip()
				items1[i] = item
				i += 1
			completeString = items1[5]
			# Set all incomplete commands (ones that are set to "N") to "erased" or "E"
			if completeString == "N":
				items1[5] = "E"
				self.hSchedFile.seek(lCount)
				self.hSchedFile.write(items1[0] + "\t\t" + items1[1] + "\t\t" + items1[2] + "\t\t" +
									  items1[3] + "\t\t" + items1[4] + "\t\t" + items1[5] + "\t\t\t" + items1[6] + "\n")
			lCount += 1
		return

	@staticmethod
	def clearTheScheduleH(self):
		self.currentCommand[146] = self.clearSchedule
		self.sendCurrentCommandToFifo(self.fifotoGPR)
		if self.waitForTCVerification(5000, self.clearSchedule) < 0:	# Wait max of 5s for the TC verification
			return -1
		else:
			return 1

	@staticmethod
	def requestSchedReport(self):
		self.currentCommand[146] = self.schedReportRequest
		self.sendCurrentCommandToFifo(self.fifotoGPR)
		self.waitForTCVerification(5000, self.schedReportRequest)
		return

	@staticmethod
	def clearComputerSchedule(self):
		self.cSchedFile.seek(0)
		self.cSchedFile.truncate()
		return

	@staticmethod
	def updateScheduleAutomatically(self):
		if self.schedWaitTime.seconds > 60:
			self.schedWaitTime = datetime.timedelta(0)
			self.requestSchedReport()
			if self.waitForTCVerification(5000, self.updatingSchedule) < 0:
				return
			self.printToCLI("SCHEDULE TO BE UPDATED AUTOMATICALLY\n")
			self.logEventReport(1, self.updatingSchedAut, 0, 0, "SCHEDULE TO BE UPDATED AUTOMATICALLY")
		return

	@staticmethod
	def processSchedReport(self):

		# Figure out approximately how many packets there are going to be.
		self.cSchedFile.seek(0)
		tempString = self.cSchedFile.readline()
		tempString = tempString.rstrip()
		self.packetsRequested = int(tempString) / 16
		if self.processSchedReportH() < 1:
			return
		elif self.numIncomingCommands != self.numCommands:
			# Satellite schedule and ground schedule are out of sync, fix it.
			self.printToCLI("THE NUMBER OF COMMANDS ON THE SATELLITE DOES NOT MATCH THE NUMBER OF COMMANDS ON GROUND\n")
			self.logError("THE NUMBER OF COMMANDS ON THE SATELLITE DOES NOT MATCH THE NUMBER OF COMMANDS ON GROUND")
			self.currentCommand[146] = self.numCommandsWrong
			self.sendCurrentCommandToFifo(self.fifoToFDIR)
			# Attempting to Fix it: (Essentially just rewrite the entire schedule on the OBC.):
			# 1. Clear the schedule on the satellite
			self.clearTheSchedule()
			newArray = []
			i = 0
			# 2. Load the computer schedule into an array.
			for line in self.cSchedFile:
				tempString = line.rstrip()
				newArray[self.numCommands - i] = int(tempString)
				i += 1
			# 3. use the method sendCommandsToOBC()
			self.sendCommandsToOBC(self.numCommands, newArray)
		else:
			self.printTOCLI("SCHEDULE REPORT RECEIVED, MATCHES UP WITH SATELLITE.\n")
			# Now we want to store the report which was retrieved in a report file.
			self.turnCommandArrayIntoSchedReport()

	@staticmethod
	def turnCommandArrayIntoSchedReport(self, numCommands, commandArray):

		newPath = "schedule/reports/schedReport%s" %str(self.schedReportCount)
		schedFile = open(newPath, "wb")
		schedFile.seek(0)
		schedFile.truncate()
		schedFile.write("TIME			APID		COMMAND		SEV		PARAM		COMPLETED		COMMENT\n")
		sub = 0
		pos = 1
		for i in range(1, numCommands + 1, 2):
			pos = i - sub
			sub += 1
			schedFile.seek(pos)
			day 		=	(commandArray[i] & 0xFF000000) >> 24
			hour		=	(commandArray[i] & 0x00FF0000) >> 16
			minute		=	(commandArray[i] & 0x0000FF00) << 8
			second		=	commandArray[i] & 0x000000FF
			apid		=	(commandArray[i + 1] & 0xFF000000) >> 24
			command		=	(commandArray[i + 1] & 0x00FF0000) >> 16
			severity	=	(commandArray[i + 1] & 0x0000FF00) << 8
			param		=	commandArray[i + 1] & 0x000000FF
			schedFile.write(str(day)+ "/" + str(hour) + "/" + str(minute) + "/" + str(second) + "\t\t" + str(apid) +
							"\t\t" + str(command) + "\t\t" + str(severity) + "\t\t" + str(param) + "\t\t\tSHEDREPORT")
		return

	@staticmethod
	def processSchedReportH(self):
		# This array is going to contain all the commands currently being stored on the schedule in the satellite.
		obcSequenceFlags	= (self.currentCommand[143] & 0xC0) >> 6
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
				return -1
		if obcSequenceFlags == 0x11:
			if self.localFlags == -1:	# The First packet of several.
				self.localSequence = obcSequenceCount
				self.localFlags = obcSequenceFlags
			else:
				self.currentCommand[146] = self.dumpPacketWrong
				self.sendCurrentCommandToFifo(self.fifotoFDIR)
				self.localSequence = 0
				self.localFlags = -1
				return -1
		if obcSequenceFlags == 0x00:
			if (self.localFlags == 0x01) or (self.localFlags == 0x00) and (self.localSequence < obcSequenceCount):
				self.localSequence = obcSequenceCount
				self.localFlags = obcSequenceFlags
			else:
				self.currentCommand[146] = self.dumpPacketWrong
				self.sendCurrentCommandToFifo(self.fifotoFDIR)
				self.localSequence = 0
				self.localFlags = -1
				return -1
		if obcSequenceFlags == 0x11:
			if (self.localFlags == 0x00) and (self.localSequence < obcSequenceCount):
				self.localSequence = obcSequenceCount
				self.localFlags = obcSequenceFlags
			else:
				self.currentCommand[146] = self.dumpPacketWrong
				self.sendCurrentCommandToFifo(self.fifotoFDIR)
				self.localSequence = 0
				self.localFlags = -1
				return -1
		# Print something meaningful to the CLI.
		if self.localFlags == 0x01:
			self.printToCLI("DOWNLOADING PACKET 1 OF %s FOR SCHEDULE\n" %str(self.packetsRequested))
		if self.localFlags == 0x11:
			self.printToCLI("DOWNLOADING PACKET 1 of 1 FOR SCHEDULE\n")
		if self.localFlags == 0x00:
			packetNum = obcSequenceCount - self.sequenceOffset + 1
			self.printToCLI("DOWNLOADING PACKET %s OF %s FOR SCHEDULE\n" %str(packetNum) %str(self.packetsRequested))
		if self.localFlags == 0x10:
			packetNum = obcSequenceCount - self.sequenceOffset + 1
			self.printToCLI("DOWNLOADING PACKET %s OF %s FOR SCHEDULE\n" %str(packetNum) %str(self.packetsRequested))
			self.printToCLI("DOWNLOAD COMPLETE FOR SCHEDULE %s\n" %str(self.dumpCount))
			self.logEventReport(1, self.dumpCompleted, 0, 0, "DOWNLOAD COMPLETE FOR SCHEDULE %s" %str(self.dumpCount))
		# Put the contents of the incoming PUS packet into the array.
		numNewCommands = self.currentCommand[136]
		for i in range (0, numNewCommands):
			self.incomingSatelliteSchedule[self.numIncomingCommands + i] = self.currentCommand[i]
		self.numIncomingCommands += numNewCommands

		if self.localFlags == 0x10:
			self.localSequence = 0
			self.localFlags = -1
			self.dumpCount += 1
			self.numIncomingCommands = 0
			self.clearIncomingSatSchedule()
			return 2
		else:
			return 1

	@staticmethod
	def clearIncomingSatSchedule(self):
		for i in range(0, 1023):
			self.incomingSatelliteSchedule[i] = 0
		return

	@staticmethod
	def updateScheduleWithCommandStatus(self):
		pass

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
		while (waitTime.milliseconds < timeOut) and not self.tcAcceptVerification:
			pass
		if waitTime > timeOut:
			self.printToCLI("SCHEDULING SERVICE OPERATION: %s HAS FAILED\n" %self.schedOperations[operation])
			self.logError("SCHEDULING SERVICE OPERATION: %s HAS FAILED" %self.schedOperations[operation])
			self.currentCommand[146] = operation
			self.sendCurrentCommandToFifo(self.fifotoFDIR)
			return -1
		else:
			self.logEventReport(1, operation, 0, 0,
								"SCHEDULING SERVICE OPERATION: %s HAS SUCCEEDED" %self.schedOperations[operation])
			self.tcLock.acquire()
			self.tcAcceptVerification = 0
			self.tcExecuteVerification = 0
			self.tcLock.release()
			return 1

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
	