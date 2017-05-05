from datetime import datetime

import struct
import time
import traceback
import sys
import math

"""
Movement threshholds for calcualteDirection
If gps offset is too small or too large, reject coordinates
"""

NOMOVEMIN = 5 # meters
NOMOVEMAX = 100 # meters
MINSPEED = 0.9 # meters per second. approx 2MPH
MAXSPEED = 44.7 # meters per second. approx 100MPH


"""
Closeness thresholds to bus stop
If within PT4, then at stop
Else if within PT3, then arrving / departing
unit: meters
"""
PT4 = 40  # meters
PT3 = 80  # meters

"""
If the bus has not been updated with a good location in this many seconds
accept the location, no matter the distance difference
seconds
"""
JUMPINTERVAL = 15

EARTH_RADIUS = 6371000

PACKET_TYPE_EUROTECH = 0x7E
PACKET_TYPE_ADA = 0x41


class BusPositionStatus:
    ARRIVING, DEPARTING, ONROAD, ATSTOP, DETOURED = range(5)


""""
BusServer packets arrive as a:
    12 byte header followed by
    19 byte position datas
    ( [x,y) ranges )
---------------------------------------
| * Range * | ****** Meaning ******** |
---------------------------------------
|     0     |   Message Start: 0x7E   |
---------------------------------------
|   1 - 11  |     Bus Serial Ascii    |
---------------------------------------
|    11     |  Number Position datas  |
---------------------------------------
|    12     |  Sequence value 0 - 255 |
---------------------------------------
|  13 - 17  |  4 byte Time UTC s 1970 |
---------------------------------------
|    17     |        Status*          |
---------------------------------------
|    18     |       Satellites        |
---------------------------------------
|  19 - 23  |  4 byte Long Latitude   |
---------------------------------------
|  23 - 27  |  4 byte Long Longitude  |
---------------------------------------
|    27     |   psrc - G ok, N bad    |
---------------------------------------
|    28     |    1 byte Speed (mph)   |
---------------------------------------
|  29 - 31  |    Heading (Degrees)    |
---------------------------------------

Status:
    Bit 1 - No response from GPS receiver
    Bit 2 - Error in response from GPS receiver
    Bit 3 - Almanac error response from GPS receiver
    Bit 4 - Good position response from GPS receiver
    Bit 5 - UTC Time flag
    Bit 6 - Overflow flag (adding to cache deleted a cached position)
    Bit 7 - First position flag, first transmitted packet after power on
"""


class Geo(object):
    def __init__(self):
        self.currentLatitude = None
        self.currentLongitude = None
        self.previousLatitude = None
        self.previousLongitude = None
        self.nextLatitude = None
        self.nextLongitude = None
        self.previousStop = None
        self.nextStop = None
        self.previousSequence = None
        self.nextSequence = None
        self.routeID = None
        self.nextStopName = None


class BusPacket(object):
    def __init__(self, packet=None):
        """Makes a new bus packet.
        If raw supplied, decodes a bus packet according to the specification above.

        Keyword Arguments:
        packet - string in above format

        """
        self.serial = None
        self.positions = None
        self.sequence = None
        self.ptime = None
        self.status = None
        self.satellites = None
        self.latitude = None
        self.longitude = None
        self.psrc = None
        self.speed = None
        self.heading = None
        self.type = None
        self.engineOn = None
        if packet:
            self.decodePacket(packet)

    def decodePacket(self, packet):
        """
        Decode a packet using the specification above.

        Keyword Arguments:
        packet - string in above format

        """
        try:
            if ord(packet[0]) == PACKET_TYPE_EUROTECH:
                self.decodeEurotechPacket(packet)
            elif ord(packet[0]) == PACKET_TYPE_ADA:
                self.decodeADAPacket(packet)
            else:
                raise Exception()
        except:
            traceback.print_exc()
            # traceback.print_exc(file=sys.stdout)
            raise Exception("Parse Error")

    def decodeEurotechPacket(self, packet):
        # Store the type of packet we are processing
        self.type = PACKET_TYPE_EUROTECH
        # Get the equipment ID
        self.serial = packet[1:11]
        #positions = struct.unpack('B', packet[11])[0]
        #sequence = struct.unpack('B', packet[12])[0]
        # Time discarded in order to use server time in ms
        self.ptime = int(time.time() * 1000)
        #status = packet[17]
        #satellites = struct.unpack('B', packet[18])[0]
        # Unpack the 4 bytes into long integers
        self.latitude = float(struct.unpack('!i', packet[19:23])[0]) / 6000000.0
        self.longitude = float(struct.unpack('!i', packet[23:27])[0]) / 6000000.0
        #psrc = packet[27]
        self.speed = struct.unpack('B', packet[28])[0]
        #heading = struct.unpack('!h', packet[29:31])[0]

    def decodeADAPacket(self, packet):
        """
        Packet format for ADA vehicles.

        Ranges are [x,y)
        +---------------------------------------------+
        | Range | Meaning                             |
        +-------+-------------------------------------+
        |   0   | Magic Number (0x41)                 |
        +-------+-------------------------------------+
        | 1-11  | 10 digit Equipment ID as a string   |
        +-------+-------------------------------------+
        | 11-15 | 4 byte Latitude encoded as an int   |
        +-------+-------------------------------------+
        | 15-19 | 4 byte Longitude encoded as an int  |
        +-------+-------------------------------------+
        | 19-23 | 4 byte direction encoded as an int  |
        +-------+-------------------------------------+
        | 23-27 | 4 byte Time UTC s 1970 as an int    |
        +-------+-------------------------------------+
        |  27   | 1 byte Speed in MPH as an int       |
        +-------+-------------------------------------+
        |  28   | 1 byte EngineOn as a Boolean        |
        +-------+-------------------------------------+
        """
        # Store the type of packet we are processing
        self.type = PACKET_TYPE_ADA
        # Get the equipment ID - Should Start with an 'S' (silent passenger)
        self.serial = packet[1:11]
        # Extract lat and long values
        self.latitude = float(struct.unpack('!i', packet[11:15])[0]) / 6000000.0
        self.longitude = float(struct.unpack('!i', packet[15:19])[0]) / 6000000.0
        # Extract the heading (direction)
        self.heading = int(struct.unpack('!i', packet[19:23])[0])
        # Extract the time
        self.ptime = int(struct.unpack('!i', packet[23:27])[0])
        # Extract the speed
        self.speed = int(struct.unpack('B', packet[27])[0])
        # Extract the status of the engine
        self.engineOn = bool(struct.unpack('?', packet[28])[0])

    def encodePacket(self):
        """
        Byte encode the values of this packet into a string.

        Keyword Arguments:
        """
        pass


"""
BusPassenger packets arrive as variable length strings with CSV
in the following order:
--------------------------------------------
| **** Field *****  | ****** Format ****** |
--------------------------------------------
|     VehicleID     |        String        |
--------------------------------------------
|   Arrival Date    |       YYYYMMDD       |
--------------------------------------------
|   Arrival Time    |   HHMMSS (24 clock)  |
--------------------------------------------
| Arrival Latitude  |       Decimal        |
--------------------------------------------
| Arrival Longitude |       Decimal        |
--------------------------------------------
|   Arrival Speed   |   Decimal (mph ?? )  |
--------------------------------------------
|   Departure Date  |       YYYYMMDD       |
--------------------------------------------
|   Departure Time  |   HHMMSS (24 clock)  |
--------------------------------------------
|  Departure Speed  |   Decimal (mph ?? )  |
--------------------------------------------
|      Counter      | Integer (front/back) |
--------------------------------------------
|   Passengers In   |        Integer       |
--------------------------------------------
|   Passengers Out  |        Integer       |
--------------------------------------------
"""

def decodePassengerPacket(packet):
    pass

def encodePassengerPacket(packet):
    pass

def calculateDistance(toLat, toLon, fromLat, fromLon):
    """
    Return the distance between two lat/lon points

    Keyword arguments:
    toLat - latitude of position A
    toLon - longitude of position A
    fromLat - latitude of position B
    fromLon - longitude of position B

    Return:
    absolute distance between two points in meters

    """
    dLatitude = math.radians(toLat - fromLat)
    dLongitude = math.radians(toLon - fromLon)
    latitude_1 = math.radians(toLat)
    latitude_2 = math.radians(fromLat)
    a = math.sin(dLatitude/2.0) ** 2 + math.sin(dLongitude/2.0) ** 2 * math.cos(latitude_1) * math.cos(latitude_2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return math.fabs(EARTH_RADIUS * c)

def calculateSpeed(toLat, toLon, fromLat, fromLon, time):
    """
    Return the speed 

    Keyword arguments:
    toLat - latitude of position A
    toLon - longitude of position A
    fromLat - latitude of position B
    fromLon - longitude of position B
    time - time in seconds between A & B

    Return:
    absolute speed between two points in meters per second
    """
    dist = calculateDistance(toLat, toLon, fromLat, fromLon)
    return (dist / time)

def deg2Rad(deg):
    """
    Convert degrees to radians.

    Keyword arguments:
    deg - degrees

    Return:
    value in radians

    """
    return (deg * math.pi / 180.0)


def rad2Deg(rad):
    """
    Convert radians to degrees.

    Keyword arguments:
    rad - radians

    Return:
    value in degrees

    """
    return (rad * 180.0 / math.pi)


def calculateDirection(toLat, toLon, fromLat, fromLon, goodUpdated):
    """
    Calculate the direction of the bus.

    Magic?

    Return:
    -1 if bad
    0-31 clockwise
    """
    distance = calculateDistance(toLat, toLon, fromLat, fromLon)

    seconds_since_update = 0
    try:
        seconds_since_update = (datetime.now() - goodUpdated).total_seconds()
    except TypeError:
        # TypeError because goodUpdated was never set, so lets take in
        # this position
        seconds_since_update = JUMPINTERVAL * 2

    speed = calculateSpeed(toLat, toLon, fromLat, fromLon, seconds_since_update)

    # We say a direction is "bad" if:
    #    The bus has moved less then the minimum threshhold or,
    #    The bus has moved too much and it has been updated recently
    if distance < NOMOVEMIN or (speed > MAXSPEED and (seconds_since_update < JUMPINTERVAL)):
        return -1

    dLon = deg2Rad(fromLon) - deg2Rad(toLon)
    dPhi = math.log(math.tan(deg2Rad(fromLat) / 2 + math.pi / 4) / math.tan(deg2Rad(toLat) / 2 + math.pi / 4 ))

    if(abs(dLon) > math.pi):
        if(dLon > 0):
            dLon = (2 * math.pi - dLon) * -1
        else:
            dLon = 2 * math.pi + dLon

    angle = (rad2Deg(math.atan2(dLon, dPhi)) + 180) % 360

    rounded = int(math.floor(angle/11.25))
    return rounded


def checkBusPositionStatus(geo):
    """
    Calculate the distance of the bus to next and from previous stops

    Keyword arguments:
    geo - a Geo object

    Return:
    Status value (Arriving, Departing, OnRoad, AtStop

    """
    busToNext = calculateDistance(geo.currentLatitude, geo.currentLongitude, geo.nextLatitude, geo.nextLongitude)
    busToPrev = calculateDistance(geo.currentLatitude, geo.currentLongitude, geo.previousLatitude, geo.previousLongitude)
    if busToNext <= PT4:
        return BusPositionStatus.ATSTOP
    elif busToNext <= PT3:
        return BusPositionStatus.ARRIVING
    elif busToPrev <= PT3:
        return BusPositionStatus.DEPARTING
    else:
        return BusPositionStatus.ONROAD
