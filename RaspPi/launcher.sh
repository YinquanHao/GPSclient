#!/bin/sh
SERVICE='gpsd'

if ps -ef | grep $SERVICE
then 
	echo "$SERVICE service is running, everything is fine"
	sudo killall gpsd
	sudo gpsd /dev/ttyAMA0 -F /var/run/gpsd.sock
	sudo service gpsd restart
	sudo python /home/pi/Desktop/client.py
else
	echo "$SERVICE is not running"
fi