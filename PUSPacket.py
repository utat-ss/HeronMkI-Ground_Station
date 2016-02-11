"""
FILE_NAME:			PUSPacket.py

AUTHOR:				Keenan Burnett

PURPOSE:			This file houses the class which is meant to define the PUS packet object.

FILE REFERENCES: 	None

LIBRARIES USED:		os, datetime, multiprocessing

SUPERCLASS:			Process

ABNORMAL TERMINATION CONDITIONS, ERROR AND WARNING MESSAGES: None yet.

ASSUMPTIONS, CONSTRAINTS, CONDITIONS: None.

NOTES:

REQUIREMENTS:

DEVELOPMENT HISTORY:
11/21/2015              Created.

11/26/2015              Adding some attributes in order to accommodate telecommands

                        Added the method parseDataArray() which goes through the data array
                        in the packet and fills in the relevant attributes (used for TM decode).

                        I also added in the method formatDataArray() which uses the attributes which
                        should be set by the user in order to fill in the data array for this packet.
"""

class Puspacket:
    """
    Author: Keenan Burnett
    Acts as packet object for telemetry and telecommand packets.
    Attributes correspond to what you would find in standard PUS packet.
    """
    packetID            = 0
    psc                 = 0
    packetLength        = 152
    # Packet Header
    version             = 0
    type1               = 0
    dataFieldHeaderf    = 0
    apid                = 0
    sequenceFlags       = 0
    sequenceCount       = 0
    packetLengthRx      = 0
    packetSubCounter    = 0
    sender              = 0
    dest                = 0
    day                 = 0
    hour                = 0
    minute              = 0
    second              = 0
    # Data Field Header
    ccsdsFlag           = 0
    packetVersion       = 0
    ack                 = 0
    serviceType         = 0
    serviceSubType      = 0
    sourceID            = 0
    # Received Checksum Value
    pec1                = 0
    pec0                = 0
    data                = []    # The Actual data array for the packet, always 152 bytes (or ints in this case)
    appData             = []    # This is the 137 bytes which belong to the application data.
    nextPacket          = None  # Pointer to the next packet in the linked list.
    prevPacket          = None  # Pointer to the previous packet int the linked list.

    @staticmethod
    def fletcher16(self, offset, count, data):
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
        for i in range(offset, offset + count):
            num = data[i] & int(0x000000FF)
            sum1 = (sum1 + num) % 255
            sum2 = (sum2 + sum1) % 255
        return (sum2 << 8) | sum1

    @classmethod
    def parseDataArray(cls):
        cls.packetID 			= cls.data[151] << 8
        cls.packetID 			|= cls.data[150]
        cls.psc 				= cls.data[149] << 8
        cls.psc 				|= cls.data[148]
        # Packet Header
        cls.version 			= (cls.data[151] & 0xE0) >> 5
        cls.type1 			    = (cls.data[151] & 0x10) >> 4
        cls.dataFieldHeaderf 	= (cls.data[151] & 0x08) >> 3
        cls.apid				= cls.data[150]
        cls.sequenceFlags		= (cls.data[149] & 0xC0) >> 6
        cls.sequenceCount		= cls.data[148]
        cls.packetLengthRx	    = cls.data[146] + 1
        # Data Field Header
        cls.ccsdsFlag			= (cls.data[145] & 0x80) >> 7
        cls.packetVersion		= (cls.data[145] & 0x70) >> 4
        cls.ack				    = cls.data[145] & 0x0F
        cls.serviceType		    = cls.data[144]
        cls.serviceSubType	    = cls.data[143]
        cls.sourceID			= cls.data[142]
        # Received Checksum Value
        cls.pec1 				= cls.data[1] << 8
        cls.pec1 				|= cls.data[0]
        # For Checking that the packet error control was correct
        cls.pec0 				= cls.fletcher16(cls, 2, 150, cls.data)
        return

    def formatDataArray(cls):
        cls.clearDataArray()
        # Fill in the application data section first
        for i in range(0, 137):
            cls.data[i + 2] = cls.appData[i]
        # Next fill in the packet header and data field header with the given attributes
        # Packet Header
        cls.data[151]   =   ((cls.version & 0x07) << 5) | ((cls.type1 & 0x01) << 4) | 0x08
        cls.data[150]   =   cls.sender
        cls.data[149]   =   (cls.sequenceFlags & 0x03) << 6
        cls.data[148]   =   cls.sequenceCount
        cls.data[147]   =   0x00
        cls.data[146]   =   cls.packetLength - 1
        # Data Field Header
        cls.data[145]   =   ((cls.version & 0x07) << 5) | (1 << 4) | 0x09
        cls.data[144]   =   cls.serviceType
        cls.data[143]   =   cls.serviceSubType
        cls.data[142]   =   cls.packetSubCounter
        cls.data[141]   =   cls.dest
        cls.data[140]   =   ((cls.day & 0xFF) << 4) & (cls.hour & 0xFF)
        cls.data[139]   =   ((cls.minute & 0xFF) << 4) & (cls.second & 0xFF)
        cls.pec0 		=   cls.fletcher16(cls, 2, 150, cls.data)
        cls.data[1]     =   (cls.pec0 & 0xFF00) >> 8
        cls.data[0]     =   cls.pec0 & 0x00FF
        return

    def clearDataArray(cls):
        for i in range(0, 152):
            cls.data[i] = 0
        return

    def __init__(self):
        """
        @purpose: Initialization method for the Ground Packet Router Class
        """
        for i in range(0, 152):
            self.data.append(0)
            self.appData.append(0)

if __name__ == '__main__':
    pass
