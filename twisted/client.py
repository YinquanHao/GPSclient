import os
#from gps import *
from time import *
import time
import threading
import socket
import json
import inspect
import struct
import math
import sys

#check the endianess of the client machine
print "Native byteorder: ", sys.byteorder


#the server address of the smart transit
#UDP_IP = "127.0.0.1"
#UDP_IP = "130.245.186.20"
UDP_IP = "130.245.186.15"
#the port number of the smart transit server
#UDP_PORT = 8543
#UDP_PORT = 8505
UDP_PORT = 8503
#how often the gps client send a UDP packet
POLL_TIME = 2
gpsd = None
sock = None
os.system('clear')
#fake latitude and longitude
latitude= 40.871695
longitude = -73.125243333
'''
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
'''
#class to establish the connection
class SocketConnection:
    def __init__(self):
        global sock
        sock = socket.socket(socket.AF_INET, #INTERNET
                    socket.SOCK_DGRAM) #UDP

if __name__ == '__main__':
    #gpsp = GpsPoller()
    socket = SocketConnection()
    global UDP_IP
    global UDP_PORT
    sval = 0
    stat = 88
    
    try:
        #gpsp.start()
        while True:
            os.system('clear')
            print 'GPS Reading'
            print '---------------------------------'
            '''
            print 'latitude   ' , gpsd.fix.latitude
            print 'longitude  ' , gpsd.fix.longitude
            '''
            #subtitude with fake latitude and longitide
            
            print 'latitude   ' , latitude
            print 'longitude  ' , longitude
            
            # Simple Function for packing float as int
            convert = lambda x: x * 6000000.0
            
           
            
            
            '''
            packetData = ""
            # som is constant byte
            packetData += chr(0x7E)
            # snum is serial number
            packetData += chr(9)
            packetData += chr(9)
            packetData += chr(0)
            packetData += chr(0)
            packetData += chr(0)
            packetData += chr(0)
            packetData += chr(0)
            packetData += chr(0)
            packetData += chr(0)
            packetData += chr(0)
            # + "\0"
            # npos is number of positions(just one)
            packetData += chr(1)
            # sval not sure if used
            packetData += chr(0)
            # date
            packetData += struct.pack('!i', time.time())
            # stat means good data
            packetData += chr(8)
            # num sats
            packetData += chr(1)

            
            
            #packetData += struct.pack('!i', int(convert(gpsd.fix.latitude)))
            #packetData += struct.pack('!i', gpsd.fix.latitude)
            packetData += struct.pack('!i', convert(latitude))
            print ' packed Slatitude is '
            print ':'.join(x.encode('hex') for x in struct.pack('!i', convert(latitude)))
            # long
            #packetData += struct.pack('!i',int(convert(gpsd.fix.longitude)))
            #packetData += struct.pack('!i', gpsd.fix.longitude)
            packetData += struct.pack('!i', convert(longitude))
            # End stuff
            packetData += chr(0x47)
                        #speed
            if(math.isnan(0) == False):
                                packetData += struct.pack('!b',int(0))
            else:
                                packetData += chr(0)
            packetData += chr(0)
            packetData += chr(0)
            '''
            
            #packetData1 = struct.pack('>b10bbbiBbiibbh', 126,48,48,48,48,48,48,48,48,57,57,1,0,time.time(),88,1,convert(latitude),convert(longitude),71,0,0)
            #packetData1 = struct.pack('>b10bbbiBbiibbh', 126,0,0,0,0,0,0,0,0,9,9,1,0,time.time(),88,1,convert(latitude),convert(longitude),71,0,0)
            
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
            
            
             
            packetData1 = struct.pack('!b10bBBiBbiibbh', 126,57,57,0,0,0,0,0,0,0,0,1,sval,time.time(),stat,1,convert(latitude),convert(longitude),71,0,0)
            packetData2 = struct.pack('!b10bBBiBbiibbh', 126,0,0,0,0,0,0,0,0,57,57,1,sval,time.time(),stat,1,convert(latitude),convert(longitude),71,0,0)
            packetData3 = struct.pack('!b10bBBiBbiibbh', 126,9,9,0,0,0,0,0,0,0,0,1,sval,time.time(),stat,1,convert(latitude),convert(longitude),71,0,0)
            packetData4 = struct.pack('!b10cBBiBbiibBh', 126,'0','0','0','0','0','0','0','0','9','9',1,sval,time.time(),stat,1,convert(latitude),convert(longitude),71,1,0)
            packetData5 = struct.pack('!b10bBBiBbiibbh', 126,57,57,48,48,48,48,48,48,48,48,1,sval,time.time(),stat,1,convert(latitude),convert(longitude),71,0,0)
            packetData6 = struct.pack('!b10bBBiBbiibbh', 126,48,48,48,48,48,48,48,48,57,57,1,sval,time.time(),stat,1,convert(latitude),convert(longitude),71,0,0)
            packetData7 = struct.pack('!b10bBBiBbiibbh', 126,48,48,48,48,48,48,48,48,57,57,1,sval,time.time(),8,1,convert(latitude),convert(longitude),71,0,0)
            #print repr(packetData1)
            print 'this'
            print ':'.join(z.encode('hex') for z in packetData4)
            print len(packetData4)
            print ':'.join(z.encode('hex') for z in packetData4[1:11])
            print float(struct.unpack('!i', packetData4[19:23])[0]) / 6000000.0
            print float(struct.unpack('!i', packetData4[23:27])[0]) / 6000000.0
            print struct.unpack('B', packetData4[28])[0]
            PACKET_TYPE_EUROTECH = 0x7E
            print ord(packetData4[0]) == PACKET_TYPE_EUROTECH
            sent = sock.sendto(packetData4, (UDP_IP, UDP_PORT))
            
            
            
            
            
            if sval < 255:
                sval += 1
            else:
                sval = 255
            
            stat = 24
                
            
            '''
            print '///'.join(x.encode('hex') for x in packetData)
            print 'date' , time.time()
            print 'speed' , 0
            print 'send = ' , sent
            print repr(packetData)
            '''
            print 'send = ' , sent
            time.sleep(POLL_TIME)

    except (KeyboardInterrupt, SystemExit()):
        print "\nKilling Thread..."
        '''
        gpsp.running = False
        gpsp.join()
        '''
    print "Done."