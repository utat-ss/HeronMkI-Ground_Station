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
					...
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
def initialize(self):
	"""
	@purpose: 	-Handles all file creation such as logs, fifos.
				-Synchronizes time with the satellite.
				-Initializes mutex locks
				-Creates subsidiary services for: housekeeping, memory management, failure detection isolation & recovery (FDIR)
	"""	
	absTime = datetime.timedelta(0)	# Set the absolute time to zero. (for now)
	currentTime = datetime.date()

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
	self.MemoryGroundService 	= PUSService("/fifos/memToGPR.fifo", "/fifos/GPRtomem.fifo", eventPath, hkPath, errorPath, self.eventLock, self.hkLock, self.cliLock, self.errorLock,
												absTime.day, absTime.minute, absTime.minute, absTime.second)
	self.memPID = self.MemoryGroundService.pid
	self.FDIRGround 			= PUSService("/fifos/fdirToGPR.fifo", "/fifos/GPRtofdir.fifo", eventPath, hkPath, errorPath, self.eventLock, self.hkLock, self.cliLock, self.errorLock,
												absTime.day, absTime.minute, absTime.minute, absTime.second)
	seld.FDIRPID = self.FDIRGround.pid

	return

def decode_telemetry(self):
	"""
	@purpose:   This method will decode the telemetry packet which was sent by the satellite
				(located in current_tm[]). It will either send the appropriate commands
				to the subsidiary services or it will act on the telemetry itself (if it is valid).
				For now, we will log all telemtry for safe-keeping / debugging.
	"""	


	return


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

	# Delete all the FIFO files that were created
	os.remove("/fifos/hkToGPR.fifo")
	os.remove("/fifos/GPRtohk.fifo")
	os.remove("/fifos/memToGPR.fifo")
	os.remove("/fifos/GPRtomem.fifo")
	os.remove("/fifos/GPRtomem.fifo")
	os.remove("/fifos/fdirToGPR.fifo")
	os.remove("/fifos/GPRtofdir.fifo")
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
	# Global Variables for Time
	self.abs_day				= day
	self.abs_hour				= hour
	self.abs_minute				= minute
	self.abs_second				= second

if __name__ == '__main__':
	x = groundPacketRouter()
	x.start()
	x.terminate()
