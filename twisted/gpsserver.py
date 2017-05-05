#!/usr/bin/python
import socket
from datetime import datetime
import sys
import pytz
import json
import logging
import time

from logging.handlers import TimedRotatingFileHandler


def create_timed_rotating_log(path):
    """"""
    logger = logging.getLogger("Rotating Log")
    logger.setLevel(logging.INFO)

    handler = TimedRotatingFileHandler(path,
                                       when="d",
                                       interval=1,
                                       backupCount=0)
    logger.addHandler(handler)

    print "Listening on " + str(UDP_IP) + " At port: " + str(UDP_PORT)

    sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
    sock.bind((UDP_IP, UDP_PORT))
    try:
        while True:
            data, addr = sock.recvfrom(BUFF_SIZE) # buffer size is 1024 bytes
            # Rebuild the JSON from the client
            # Packet has the following information
            # ['lat']
            # ['long']

            rebuild = json.loads(data)
            try:
                time = datetime.now()
                print "Logging the following data: ", data
                #logFile.write(time.strftime('%I %M %S %p') + data)
                #logFile.write("\n")
                #logFile.flush()
                logger.info(time.strftime('%I %M %S %p') + data)
            except:
               print "\nServer Shutting down"
               #logFile.close()
    except (KeyboardInterrupt, SystemExit):
       print "\nServer Shutting down. Closing log file."
       #logFile.close()

#UDP_IP = "192.168.1.8"
#UDP_IP = "172.20.249.40 "
UDP_IP = "172.20.248.108"
UDP_PORT = 5005
BUFF_SIZE = 1024

if __name__ == "__main__":
    log_file = "raspberrypi.log"
    create_timed_rotating_log(log_file)
