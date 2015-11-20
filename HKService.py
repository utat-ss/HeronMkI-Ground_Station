"""
FILE_NAME:			HKService.py

AUTHOR:				Keenan Burnett

PURPOSE:			This class shall house the housekeeping PUS service and all related methods.

FILE REFERENCES:

LIBRARIES USED:		os, multiprocessing

SUPERCLASS:			PUSService

ABNORMAL TERMINATION CONDITIONS, ERROR AND WARNING MESSAGES: None yet.

ASSUMPTIONS, CONSTRAINTS, CONDITIONS: None.

NOTES:
					...
REQUIREMENTS:

DEVELOPMENT HISTORY:

11/17/2015			Created.

"""

import os
from multiprocessing import *
from PUSService import *

class hkService(PUSService):
	"""
	This class is meant to represent the PUS Housekeeping Service.
	"""
@classmethod
def run(self):
	"""
	@purpose:   Used to house the main program for the housekeeping service.
	@Note:		Since this class is a subclass of Process, when self.start() is executed on an 
				instance of this class, a process will be created with the contents of run() as the 
				main program.
	"""	
	inititalize()

	byteCount = 0
	newString = None
	i = 0
	while(1):
		if(os.path.getsize(self.fifoFromGPRPath) > 152):
			i = 0
			if(self.fifoFromGPR.readline() == "START\n"):
				# Start reading in the command from the GPR.
				newString = self.fifoFromGPR.readline()
				newString = newString.rstrip()
				while(newString != "STOP"):
					self.currentCommand[i] = int(newString)
					i++
					newString = self.fifoFromGPR.readline()
					newString = newString.rstrip()
				execCommands()

def initialize():
	"""
	@purpose:   - Initializes arrays to 0.
				- Sets current HK definition to default.
	"""	
	tempString = None
	for i in range(0, self.dataLength):
		self.currentHK[i] = 0
		self.currentHKDefinition[i] = 0
		self.hkDefinition0[i] = 0
		self.hkDefinition1[i] = 0
	for i in range(0, (self.dataLength + 10)):
		self.currentCommand[i] = 0

	setHKDefinitionsDefault()
	self.logEventReport(1, self.hkgroundinitialized, 0, 0, "Ground Housekeeping Service Initialized Correctly.")

def execCommands():
	"""
	@purpose:   After a command has been received in the FIFO, this function parses through it
				and performs different actions based on what is received.
	"""	
	if(self.currentCommand[146] == )
	return


def logHkParameterReport(*hkParamArray):
	"""
	@purpose:   Used to log a hk parameter report.
	"""	
	tempString = None
	self.hkLog.write("HK PARAMETER REPORT:\t")
	self.hkLog.write(str(self.absTime.day) + "/" + str(self.absTime.day) + "/" + str(self.absTime.day) + "\t,\n")
	i = 0
	errorInt = 0
	for byte in hkParamArray:
		byte = byte & 0x000000FF
		tempString = self.parameters(int(byte))
		if self.currenthkdefinitionf == 0:
			if tempString != self.paramaters(self.hkDefinition0[i]):
				errorInt = 1
			self.hkLog.write(tempString) + "\n")
		else if self.currenthkdefinitionf == 1:
			if tempString != self.parameters(self.hkDefinition1[i]):
				errorInt = 1
			self.hkLog.write(tempString) + "\n")
		i++
	if errorInt:
		logError("Local Housekeeping Parameter definition does not match satellite")
		currentCommand[146] = self.hkparamincorrect
		currentCommand[146] = 3
		# Need a FIFO from the hkservice to FDIRGround. (send message to it here.)

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

def setHKDefinitionsDefault():
	"""
	@purpose:   Sets the hk definition which is being used to the default.
	@Note:		For default, parameters are stored in the housekeeping definition in decreasing order for variables
				followed by increasing order for sensors (starting at hkDefinition[numParameters - 1] and descending)
	@Note:		Note: If the satellite experiences a reset, it will go back to this definition for housekeeping.
	"""	
	paramNum = 0xFF
	self.hkDefinition0[136] 	= 0
	self.hkDefinition0[135] 	= self.collectionInterval0
	self.hkDefinition0[134] 	= self.numParameters0
	for i in range(0, self.numVars0):
		self.hkDefinition0[i] = paramNum - i
		paramNum = 1
	for i in range (self.numVars0, self.numParameters0):
		self.hkDefinition0[i] = paramNum
		paramNum++
	self.currenthkdefinitionf = 0
	defPath = "/housekeeping/definitions/hkDefinition0.txt"

	# Create the hkDefinition0.txt file if it doesn't exist yet.
	if (!os.path.exists(defPath)):
		hkdef = open(defPath, "ab")
		hkdef.write(str(0))
		hkdef.write(str(self.collectionInterval0))
		hkdef.write(str(self.numParameters0))
		for i in range((self.numParameters0 * 2 - 1 ), 0, -1):
			paramNum = self.hkDefinition0[i]
			hkdef.write(self.parameters[paramNum])

	# Send a PUS Packet to the satellite setting the hk def to default
	# Send a PUS packet to the satellite requesting a parameter report

	return

def setAlternateHKDefinition():
	"""
	@purpose:   Sets the hk definition which is being used to the alternate definition.
	@Note:		The format of hk definitions should be known before changing the existing one.
	@Note:		The new housekeeping parameter report should replace hkDefinition1.txt & have an sID of 1.
	"""	
	defPath = "/housekeeping/definitions/hkDefinition1.txt"
	sID = 0
	tempString = None
	paramNum = 0
	if os.path.exists(defPath):
		hkdef = open(defPath, "rb")
		sId = int(hkdef.read(1))
		if(sID != 1):
			self.printtoCLI("sID in hkDefinition1.txt was not 1")
			self.logError("sID in hkDefinition1.txt was not 1\n")
		self.hkDefinition1[136] = 1
		hkdef.seek(1)
		self.collectionInterval1 = int(hkdef.read(2))
		self.hkDefinition1[135] = self.collectionInterval1
		hkdef.seek(2)
		self.numParameters1 = int(hkdef.read(2))
		self.hkDefinition1[134] = self.numParameters1
		hkdef.seek(3)
		# Read the housekeeping definition from the file.
		for i in range((self.numParameters1 * 2 - 1 ), 0, -1):
			tempString = hkdef.readline()
			tempString = tempString.rstrip()
			paramNum = int(self.invParameters(tempString))
			hkDefinition1[i] = paramNum

	# Send a PUS Packet to the satellite setting the hk def to the alternate one
	# Send a PUS packet to the satellite requesting a parameter report
	return

	else:
		self.printtoCLI("hkDefinition1.txt does not exist")
		self.logError("hkDefinition1.txt does not exist\n")
		return

def __init__(self, path1, path2, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock, errorLock, day, hour, minute, second, hkDefPath):
	# Inititalize this instance as a PUS service
	super(hkService, self).__init__(path1, path2, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock, errorLock, day, hour, minute, second)
	self.processID = 0x10
	self.serviceType = 3
	self.currentHK[]
	self.hkDefinition0[]
	self.hkDefinition1[]
	self.currentHKDefinition[]
	self.currenthkdefinitionf = 0
	self.collectionInterval0 = 30	# Housekeeping colleciton interval in minutes.
	self.collectionInterval1 = 30
	self.numParameters0 = 41
	self.numSensors0 = 27
	self.numVars0 = 14
	self.numParameters1 = 41
	self.numSensors1 = 27
	self.numVars1 = 14

	# Log for Housekeeping Parameter Reports
	self.hkDefLog = open(hkDefPath, a+)

	# Acquire some values from the satellite.

if __name__ == '__main__':
	return
