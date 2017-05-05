import os
from gps import *
from time import *
import ConfigParser
import time
import threading
import socket
import json
import inspect
import struct
import math
import sys

configParser = ConfigParser.RawConfigParser()
configFilePath = r'/home/pi/Desktop/config.cfg'
configParser.read(configFilePath)
UDP_PORT = int(configParser.get('config', 'PORT'))
UDP_IP = configParser.get('config', 'ADDRESS')
ID = configParser.get('config', 'BUSID')

#how often the gps client send a UDP packet
POLL_TIME = 2
gpsd = None
sock = None
os.system('clear')


class GpsPoller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        global gpsd
        gpsd = gps(mode=WATCH_ENABLE)
        self.current_value = None
        self.running = True
    def run(self):
        global gpsd
        while gpsp.running:
            gpsd.next()

#class to establish the connection
class SocketConnection:
    def __init__(self):
        global sock
        sock = socket.socket(socket.AF_INET, #INTERNET
                    socket.SOCK_DGRAM) #UDP

if __name__ == '__main__':
    gpsp = GpsPoller()
    socket = SocketConnection()
    global UDP_IP
    global UDP_PORT
    sval = 0
    stat = 88
    
    try:
        gpsp.start()
        while True:
            try:
                os.system('clear')
                print 'GPS Reading'
                print '---------------------------------'
                print 'latitude   ' , gpsd.fix.latitude
                print 'longitude  ' , gpsd.fix.longitude
                latitude = gpsd.fix.latitude
                longitude = gpsd.fix.longitude
            # Simple Function for packing float as int
                convert = lambda x: x * 6000000.0
                if math.isnan(gpsd.fix.latitude):
                    latitude = 0
                    longitude = 0
            #to wrap the packet Data in Arcom format following is the arcom format of Data.
            
            # > in the format sting of struct.pack method means the data is in big-endian 
            
            #(som, 1 byte,  Start of message indicator. Always set to 0x7E)
            # b is signed char(One Byte), corresponding to 126 which is 0x7e 
            
            # (snum, 10 bytes, Unit serial number in ASCII left justified and null(0) filled to the right.)
            # 10b is 10 of signed char(One Byte for each and 10 bytes total), corresponding to 57,57,0,0,0,0,0,0,0,0 which is digits 9900000000 in ascii
            
            # (npos, 1 byte, Number of positions in this message)
            # b is signed char(One Byte), corresponding to 1 which is 0x01, because we have only one position in the packet
            
            #(sval, 1 byte, Sequence value for each position transmitted. The sequence value for the first position transmitted is 0. The sequence value is incremented by 1 for each subsequent position transmitted. Since this value is only one byte, the maximum sequence value is 255)
            # B is unsigned char(One Byte), corresponding to 0 which is 0x00, because the first position transmitted is 0
            
            #(time, 4 bytes, UTC time stamp of the GPS position. This value is in seconds since1/1/1970)
            # i is signed integer(four bytes), we get it from function time.time() which gives us the value is in seconds since1/1/1970 of the system time
            
            #(stat, 1 byte, This field contains a code representing status of the position from the GPS receiver. In addition, bits 5-7 are used as flags for other conditions
            # Status Codes: 
            #Bit: 1 Condition: No response from GPS receiver. 
            #Bit: 2 Condition: Error in response from GPS receiver. 
            #Bit: 3 Condition: Almanac error response from GPS receiver 
            #Bit: 4 Condition: Good position response from GSP receiver  
            #Flag Bits: 
            #Bit 5: UTC TIME FLAG - This bit must be set to indicate that the TIMETAG represents UTC time.
            #Bit 6: OVERFLOW FLAG - This bit is set to indicate that this position, after being added to the store and forward cache,  existing position in the store and forward cache to be deleted.
            #Bit 7: FIRST POSITION FLAG - This bit is set to indicate that this is the first position to be transmitted after the device was powered on.For all subsequent positions, this bit must be cleared)
            #B is unsigned char (One Byte),corresponding to 88 which is 0x58 or 0101 1000 in binary, initially it means Bit: 4 Condition: Good position response from GSP receiver & UTC TIME FLAG & FIRST POSITION FLAG
            
            #(sats, 1 byte, Number of satellites currently being tracked)
            # b is signed char(One Byte), corresponding to 1 which is 0x01, one satellite currently being tracked
            
            #(lat, 4 bytes, Latitude of the position in 1/100,000 minutes. For example, the'North 26 Degrees 8.767840 Minutes' is represented as (26 * 60 *100000 + 8.767840 * 100000) = 156876784 )
            # i is signed integer(four bytes), we get it from convert(latitude) function
            
            #(lon, 4 bytes, Longitude of the position in 1/100,000 minutes. For example, the'WEST 80 Degrees 15.222400 Minutes' is represented as - (80 * 60 *100000 + 15.222400 * 100000) = - 481522240)
            # i is signed integer(four bytes), we get it from convert(longitude) function
             
            #(psrc, 1 byte, ASCII 'G'(0x47) if this is a valid GPS position, otherwise ASCII'N'(0x4E))
            # always valid position? 
            # b is signed char(One Byte), corresponding to 71 which is 0x47 means valid position
            
            #(speed, 1 byte, Speed in miles per hour.)
            #b is signed char(One Byte), corresponding to speed fake 0
            
            #(head, 2 bytes, Heading in degrees)
            #h is short(2 bytes), currently 0
            
                packetData = struct.pack('!b10cBBiBbiibBh', 126,ID[0],ID[1],ID[2],ID[3],ID[4],ID[5],ID[6],ID[7],ID[8],ID[9],1,sval,time.time(),stat,1,convert(latitude),convert(longitude),71,1,0)
            #print repr(packetData1)
                print 'this'
                print ':'.join(z.encode('hex') for z in packetData)
                print len(packetData)
                print ':'.join(z.encode('hex') for z in packetData[1:11])
                print float(struct.unpack('!i', packetData[19:23])[0]) / 6000000.0
                print float(struct.unpack('!i', packetData[23:27])[0]) / 6000000.0
                print struct.unpack('B', packetData[28])[0]
                PACKET_TYPE_EUROTECH = 0x7E
                print ord(packetData[0]) == PACKET_TYPE_EUROTECH
                print 'IP' ,UDP_IP
                print 'UDP_PORT' ,UDP_PORT
                print 'ID',ID[0]

                sent = sock.sendto(packetData, (UDP_IP, UDP_PORT))
                if sval < 255:
                    sval += 1
                else:
                    sval = 255
            
                stat = 24
                print 'send = ' , sent
                time.sleep(POLL_TIME)
            except:
                pass

    except (KeyboardInterrupt, SystemExit()):
        print "\nKilling Thread..."
        
        gpsp.running = False
        gpsp.join()
        
    print "Done."
