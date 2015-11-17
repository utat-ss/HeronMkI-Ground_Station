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

	self.inititalize()

	byteCount = 0
	newString = None
	i = 0
	while(1):
		if(os.path.getsize(self.fifoFromGPRPath) > 152):
			if(self.fifoFromGPR.readline() == "START\n"):
				# Start reading in the command from the GPR.
				newString = self.fifoFromGPR.readline()
				newString = newString.rstrip()
				while(newString != "STOP"):
					self.currentCommand[i] = int(newString)
					i++
					newString = self.fifoFromGPR.readline()
					newString = newString.rstrip()
				#self.execCommands()

def initialize(self):
	tempString = None
	for i = 0 to self.dataLength:
		self.currentHK[i] = 0
		self.currentHKDefinition[i] = 0
		self.hkDefinition0[i] = 0
		self.hkDefinition1[i] = 0
	for i = 0 to (self.dataLength + 10):
		self.currentCommand[i] = 0

	self.setHKDefinitionsDefault()
	self.logEventReport(1, self.hkgroundinitialized, 0, 0, self.abs_day, self.abs_minute, self.abs_second, 
						"Ground Housekeeping Service Initialized Correctly.")

def execCommands(self):
	#This should parse through the command sent by the Ground Packet Router and do something with it.
	return

# Parameters are stored in the housekeeping definition in decreasing order for variables followed by
# increasing order for sensors (starting at hkDefinition[0])
# Note: If the satellite experiences a reset, it will go back to this definition for housekeeping.
def setHKDefinitionsDefault(self):
	paramNum = 0xFF
	self.hkDefinition0[136] 	= 0
	self.hkDefinition0[135] 	= self.collectionInterval0
	self.hkDefinition0[134] 	= self.numParameters0
	for i = 0 to (self.numVars0 - 1):
		self.hkDefinition0[i] = paramNum - i
		paramNum = 1
	for i = self.numVars0 to (self.numParameters0 - 1):
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
		for i = (self.numParameters0 * 2 - 1 ) to 0:
			paramNum = self.hkDefinition0[i]
			hkdef.write(self.parameters[paramNum])

	# Send a PUS Packet to the satellite setting the hk def to default
	# Send a PUS packet to the satellite requesting a parameter report

	return

def setAlternateHKDefinition(self):
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
		for i = (self.numParameters1 * 2 - 1 ) to 0:
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

def __init__(self, path1, path2, eventPath, hkPath, errorPath, eventLock, hkLock, cliLock, errorLock, day, hour, minute, second):
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

	# Acquire some values from the satellite.

if __name__ == '__main__':
	return
