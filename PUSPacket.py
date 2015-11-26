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
"""

class Puspacket:
    """
    Author: Keenan Burnett
    Acts as packet object for telemetry and telecommand packets.
    Attributes correspond to what you would find in standard PUS packet.
    """
    packetID            = 0
    psc                 = 0
    # Packet Header
    version             = 0
    type1               = 0
    dataFieldHeaderf    = 0
    apid                = 0
    sequenceFlags       = 0
    sequenceCount       = 0
    packetLengthRx      = 0
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
    nextPacket          = None  # Pointer to the next packet in the linked list.
    prevPacket          = None  # Pointer to the previous packet int the linked list.

    def __init__(self):
        """
        @purpose: Initialization method for the Ground Packet Router Class
        """
        pass

if __name__ == '__main__':
    pass
