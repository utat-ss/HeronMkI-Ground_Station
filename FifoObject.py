"""
FILE_NAME:			FifoObject.py

AUTHOR:				Keenan Burnett

PURPOSE:			This file houses the class which is meant to define the Fifo Object Class.

FILE REFERENCES: 	None

LIBRARIES USED:		time

SUPERCLASS:			Process

ABNORMAL TERMINATION CONDITIONS, ERROR AND WARNING MESSAGES: None yet.

ASSUMPTIONS, CONSTRAINTS, CONDITIONS: None.

NOTES:              This class was created in order to make the use of fifos more organized.

REQUIREMENTS:

DEVELOPMENT HISTORY:
12/02/2015      Created.

"""
import time

class FifoObject:
    """
    Author: Keenan Burnett
    Acts as fifo object for either receiving for sending commands with the Ground Station Software.
    """
    fifoPath = None     # Path to the FIFO at hand
    fifoFD   = None     # Open file descriptor to the fifo at hand.
    tempCommand = []
    command = []
    reading = 0
    writing = 0
    commandReady = 0
    numLines = 0
    type = 0            # 1 = This Fifo is to be used for sending commands, 0 = receiving commands.
    dataLength = 137

    @classmethod
    def writeCommandToFifo(cls, commandArray):
        """
        @purpose:   This method takes what is contained in commandArray[] and
        then place it in the given fifo defined by this object.
        @Note: We use a "START\n" code and "STOP\n" code to indicate where commands stop and start.
        @Note: Each subsequent byte is then placed in the fifo followed by a newline character.
        """
        if not cls.type:
            return -1           # Writing to a receiving Fifo is not allowed.
        if len(commandArray) < 147:
            return -1           # Length of the given commandArray was too short.

        cls.writing = 1
        cls.fifoFD.write("START\n")
        for i in range(0, cls.dataLength + 10):
            tempString = str(commandArray[i]) + "\n"
            cls.fifoFD.write(tempString)
        cls.fifoFD.write("STOP\n")
        cls.fifoFD.flush()
        cls.writing = 0
        return 1

    @classmethod
    def readCommandFromFifo(cls):
        """
        @purpose:   This method reads a single line from the FIFO that this object represents and if an entire command
            has been received, it sets commandReady to 1.
        @Note: We use a "START\n" code and "STOP\n" code to indicate where commands stop and start.
        @return: -2 is returned, a failure report should be sent to the FDIR task and printed to the command line.
            -1 usually means a usage error, 1 means it worked as intended.
        """
        maxTries = 10
        if cls.type:
            return -1           # Reading from a writing Fifo is not allowed
        if cls.commandReady:
            return -1           # The commandReady flag should be cleared by the user before attempting to read again.
        # Read a line from the FIFO.
        s = cls.fifoFD.readline()
        while (s == "") and maxTries:
            time.sleep(0.0001)
            maxTries -= 1
            s = cls.fifoFD.readline()
        if s == "":
            return 0
        if s == "START\n":
            cls.reading = 1
            cls.clearTempCommand(cls)
            return 1
        if cls.reading and (s == "STOP\n"):
            if cls.numLines != 147:
               cls.reading  = 0
               return -2
            else:
                cls.reading = 0
                return 1
        if cls.reading:
            s = s.rstrip()
            cls.numLines += 1
            cls.tempCommand[cls.numLines - 1] = int(s)
            if cls.numLines == 147:
                for i in range(0, 147):
                    cls.command[i] = cls.tempCommand[i]
                cls.clearTempCommand(cls)
                cls.commandReady = 1
            return 1
        return 0

    @staticmethod
    def clearTempCommand(self):
        for i in range(0, 147):
            self.tempCommand[i] = 0
        return

    @staticmethod
    def clearCommand(self):
        for i in range(0, 147):
            self.command[i] = 0
        return

    def __init__(self, FifoPath, Type):
        self.fifoPath = FifoPath
        self.type = Type
        if Type:
            self.fifoFD = open(FifoPath, "wb")
        if not Type:
            self.fifoID = open(FifoPath, "rb", 0)
        for i in range(0, 147):
            self.tempCommand.append(0)
            self.command.append(0)

if __name__ == '__main__':
    pass
