#!/usr/bin/env python
# Logging
from twisted.python import log
# For logging to a file
from twisted.python.logfile import DailyLogFile
# UDP protocol
from twisted.internet.protocol import DatagramProtocol
# Stats http server
from twisted.web import server, resource
# Event loop
from twisted.internet import reactor

# Async files
from twisted.internet import fdesc
# Async database access
from twisted.enterprise import adbapi
# For receiving database results as dictionaries instead of tuples

'''
commands out for DB usage
'''
#import MySQLdb.cursors

# Async http requests
from twisted.web.client import getPage
# POST encoding
import urllib

# Bus packet parsing
from BusPackets import BusPacket
from BusPackets import calculateDirection
import BusPackets  # To use some constantsls


# For packet stats
from PacketStats import PacketStats

# Other
import time, os, argparse
from datetime import datetime

import traceback

# Create database connection pool
# Import patched version to avoid timeout
'''
commands out for DB usage
'''
'''
from dbapiFix import ReconnectingConnectionPool
dbpool = ReconnectingConnectionPool("MySQLdb", "localhost", "smart", "22%ride", "SmartTransit", cursorclass=MySQLdb.cursors.DictCursor)
'''
packetStats = PacketStats()
BASE_NODE_URL = "http://moosmarttransit.cewit.stonybrook.edu:8080"
outdir = os.path.abspath(".")


class Bus(DatagramProtocol):

    """Bus extends Protocol and processes incoming requests.

    Be careful using self variables in this class.
    reactor.listenUDP() creates only 1 instance of Bus() and reuses it
    throughout the life of the server. Because of this, if we use self
    variables, and we receive a lot of packets at once, the data from packets
    gets jumbeled or lost. Most times from testing it seems that the last
    packet received in the burst will become the packet that gets the defferred
    tasks ran on many times.
    """

    def __init__(self):
        # print "Creating instance of Bus"
        pass

    ################################################################################
    ############################ Incoming Request ##################################
    ################################################################################
    def datagramReceived(self, data, (host, port)):
        """Processe the received data.

        Keyword Arguments:
        data - Twisted TCP Data
        (host, port) - Packet source

        """
        # Increment counter
        packetStats.PACKETS_RECEIVED += 1

        # Process packet data
        try:
            packet = BusPacket(data)
        except:
            traceback.print_exc()
            log.err("400 - Bad Request")
            return

        # Check that a bus made the request
        if(not self.validateRequest()):
            log.err("401 - Unauthorized")
            return

        # Start sequence of callbacks
        self.start_callbacks(packet)

    def validateRequest(self):
        """NOT IMPLEMENTED.

        Checks the request data via a secret + hash
        of sent paramaters
        """
        return True

    ################################################################################
    ############################# Callback tasks ###################################
    ################################################################################
    """
    Callback order. '\ ' is a branch. '.' is a termination
    | start_callbacks
    | activeTask
      \ logTask
     / .
    |
    | locationAndDirectionTask
      \
     / .
    |
    | stopCountTask
    | routeTask
    | statusTask
    | updateNode
    | updateNodeNextStop
    .

    All sql commands are run asynchronously: after the command finishes, the next
    part of processing the packet data happens.
    The functions are defined in order of execution. Stick to that format.
    """
    def start_callbacks(self, packet):
        """
        Start callback sequence
        Get bus information and pass on to activeTask
        """
        # Create a dictionary that is passed along with the asyc calls instead
        # of using self variables
        data = {}
        dbpool.runQuery("""SELECT b.busNum, b.lat, b.lon, b.routeID, b.inservice, b.prevseq, b.updated, b.goodUpdated
            FROM bus b, Equipment e
            WHERE b.busNum=e.BusID AND e.EquipmentID=%s""", packet.serial).addCallback(self.activeTask, packet, data)

    def activeTask(self, dictList, packet, data):
        """
        Check if a bus is active. Return if not.
        Get bus position information from database and
        pass on to LocationsAndDirectionsTask
        """
        if len(dictList) == 0:
            log.err("No such bus: %s" % packet.serial)
        else:
            data['busNum'] = dictList[0]['busNum']
            data['lat'] = float(dictList[0]['lat'])
            data['lon'] = float(dictList[0]['lon'])
            data['routeID'] = dictList[0]['routeID']
            data['inservice'] = dictList[0]['inservice'] == 1
            data['prevseq'] = dictList[0]['prevseq']
            data['updated'] = dictList[0]['updated']
            data['goodUpdated'] = dictList[0]['goodUpdated']
            # Time since last update if updated is None then default to 0
            if data['updated'] is None:
                data['timeDifference'] = 0
            else:
                data['timeDifference'] = (datetime.now() - data['updated']).total_seconds()
            # Log the recieved packet
            self.logTask(packet, data)
            # Continue callbacks
            self.locationAndDirectionTask(packet, data)

    def logTask(self, packet, data):
        """
        Log the data from the packet
        """
        fileDate = time.strftime('%Y-%m-%d')
        # I disagree with ^%&*@# PM but I had to keep it for compatibility
        logDate = time.strftime('%Y.%m.%d %I:%M:%S %p')
        # TODO
        # Map of file descriptors
        fileName = '%s/%s-%s' % (outdir, data['busNum'], fileDate)
        try:
            if(os.path.realpath(fileName).startswith(outdir)):
                with open(fileName, 'a') as output:
                    fdesc.setNonBlocking(output)
                    output.write('%s:%s, %s\n' % (logDate, packet.latitude, packet.longitude))
            else:
                log.err("Escalation attempt")
        except:
            log.err("Error logging packets")

    def locationAndDirectionTask(self, packet, data):
        """
        Calculate direction with some checks
        Update locations in database
        Get  route stop count from database and pass on to stopCount
        """
        # Log wifi on if last update > 2 minutes and the engine is on
        if data['timeDifference'] >= 120 and \
                (packet.type == BusPackets.PACKET_TYPE_ADA and
                 packet.engineOn) or packet.type != BusPackets.PACKET_TYPE_ADA:
            dbpool.runQuery("""INSERT INTO driverLog (busID, event, routeID) VALUES (%s,%s,%s)""", (data['busNum'], "wifiOn", data['routeID']))

        # For ADA packets we can use the heading as the direction
        # But Eurotech packets we need to calculate the direction ourselves
        if packet.type == BusPackets.PACKET_TYPE_ADA:
            data['direction'] = packet.heading
        else:
            data['direction'] = calculateDirection(packet.latitude, packet.longitude, data['lat'], data['lon'], data['goodUpdated'])

        if data['direction'] == -1:
            # ADA vehicles will never have direction == -1
            dbpool.runQuery("""UPDATE bus b
                SET b.updated=NOW(), b.delay=IF(b.delay - 3 < 0, 0, b.delay-3)
                WHERE b.busNum=%s""", (data['busNum']))
            packetStats.PACKETS_PROCESSED += 1
        else:
            # Update the vehicle's coordinates and direction
            dbpool.runQuery("""UPDATE bus b
                SET b.prevlat=b.lat, b.prevlon=b.lon, b.lat=%s, b.lon=%s, b.direction=%s, b.delay=IF(b.delay - 3 < 0, 0, b.delay-3)
                WHERE b.busNum=%s""", (packet.latitude, packet.longitude, data['direction'], data['busNum']))
            # If the ADA engine is on OR it is a EUROTECH packet update times
            if packet.engineOn == 1 or packet.engineOn is None:
                dbpool.runQuery("""UPDATE bus
                    SET updated=NOW(), goodUpdated=NOW()
                    WHERE busNum=%s""", (data['busNum']))

            if packet.type == BusPackets.PACKET_TYPE_ADA and not data['routeID']:
                # ADA Vehicles dont need to be processed any further.
                # If the engine is on, set it to 1 else zero
                engineStatus = 1 if packet.engineOn else 0
                # Update the inservice field for ada vehicle
                dbpool.runQuery("""
                    UPDATE bus
                        SET inservice = %s
                        WHERE busNum = %s
                    """, (engineStatus, data['busNum']))
                packetStats.PACKETS_PROCESSED += 1
            else:
                dbpool.runQuery("""SELECT COUNT(*)
                    FROM route_stop rs JOIN bus b ON rs.routeID=b.routeID
                    WHERE b.busNum=%s""", (data['busNum'])).addCallback(self.stopCountTask, packet, data)

    def stopCountTask(self, dictList, packet, data):
        """
        Check that we have a route to look up
        """
        # 'COUNT(*)' is the key for the result of the above COUNT(*) query
        data['stopCount'] = dictList[0]['COUNT(*)']
        if data['stopCount'] > 0:
            # This queries the RouteDescription table for all entries along
            # this routeID such that the current direction is within 45 degrees
            # It returns all the entries that have roughly the same direction
            # as the current bus.
            dbpool.runQuery("""SELECT seq, lat, lon, bus_status, direction, prevStopSeq
                FROM RouteDescription
                WHERE routeID=%s
                AND (
                    ABS(%s - direction) < 5
                    OR
                    ABS(%s - direction) > 27
                );""", (data['routeID'], data['direction'], data['direction'])).addCallback(self.routeTask, packet, data)
        else:
            # Bus is not on a route or has incorrect routeID
            pass

    def routeTask(self, dictList, packet, data):
        """

        :param dictList: result list containing RouteDescription entries with
            the same direction as the current bus
        """
        # Find the entry that is closest to the current bus location
        minDist = BusPackets.calculateDistance(packet.latitude, packet.longitude, dictList[0]['lat'], dictList[0]['lon'])
        closestRouteEntry = dictList[0]
        for i in range(1, len(dictList)):
            dist = BusPackets.calculateDistance(packet.latitude, packet.longitude, dictList[i]['lat'], dictList[i]['lon'])
            if dist < minDist:
                minDist = dist
                closestRouteEntry = dictList[i]

        # If the bus is too far from the route because it is detoured we set
        # the status to 4 for "detoured" instead of the status from the
        # closest route point
        if minDist > 100:
            closestRouteEntry['bus_status'] = BusPackets.BusPositionStatus.DETOURED

        # Update the bus with the info from the closest route point
        dbpool.runQuery("""UPDATE bus
            SET bus_status=%s, prevseq=%s, updated=NOW(), goodUpdated=NOW(), closestRouteSeq=%s
            WHERE busNum=%s;""", (closestRouteEntry['bus_status'], closestRouteEntry['prevStopSeq'], closestRouteEntry['seq'], data['busNum']))

        if closestRouteEntry['bus_status'] == BusPackets.BusPositionStatus.ATSTOP and closestRouteEntry['prevStopSeq'] != data['prevseq']:
            # The bus just arrived at a stop, so update prevseqtime
            dbpool.runQuery("""UPDATE bus
                SET prevseqtime=NOW()
                WHERE busNum=%s;""", data['busNum'])
            # Update the last time a bus arrived at this stop
            dbpool.runQuery("""UPDATE stops
                SET last_arrived_time=NOW()
                WHERE id=%s""", (closestRouteEntry['prevStopSeq']))
            # If the bus is not in service set it because it just got to a stop
            if not data['inservice']:
                dbpool.runQuery("""UPDATE bus
                    SET inservice=1
                    WHERE busNum=%s""", (data['busNum']))

            # Select the name of the next stop and pass the result to updateNodeNextStop
            nextStopSeq = (closestRouteEntry['prevStopSeq'] + 1) % data['stopCount']

        packetStats.PACKETS_PROCESSED += 1

    def updateNode(self, dictList, packet, data):
        """
        Call the nodejs server to update the tablets
        """
        # Tell node that this bus is in service
        getPage("%s/%s" % (BASE_NODE_URL, "UpdateServiceStatus"),
                method="POST",
                postdata=urllib.urlencode({"vehicleId": data['busNum'], "isInService": 1}),
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )

    def updateNodeNextStop(self, dictList, packet, data):
        # Error getting next stop
        if len(dictList) == 0:
            log.err("Error getting next stop for: %s @ %s" % (data['busNum'], data['nextStopName']))
            return
        # Tell node the name of the bus's next stop
        getPage("%s/%s" % (BASE_NODE_URL, "UpdateNextStop"),
                method="POST",
                postdata=urllib.urlencode({"vehicleId": data['busNum'], "nextStop": dictList[0]['name']}),
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Launch bus packet server')
    parser.add_argument('--port', dest='port', type=int, default=8503, help="Listen port")
    parser.add_argument('--addr', dest='addr', type=str, default='0.0.0.0', help="Listen addr")
    parser.add_argument('--odir', dest='odir', type=str, required=True, help="Directory to store packet files")
    parser.add_argument('--debug', dest='debug', action='store_true', default=False, help="Run in debug mode")
    parser.add_argument('--logdir', dest='logdir', type=str, required=True, help="Directory to store log files")
    args = parser.parse_args()
    outdir = os.path.abspath(args.odir)
    debug = args.debug
    # Start logging all output to the logfile rotated every day
    # ie, logfile is today, logfile.1 is yesterday, logfile.2 is 2 days ago
    log.startLogging(DailyLogFile('TwistedBusServer.log', args.logdir))
    reactor.listenTCP(args.port, server.Site(packetStats), interface=args.addr)
    reactor.listenUDP(args.port, Bus(), interface=args.addr)
    reactor.run()
