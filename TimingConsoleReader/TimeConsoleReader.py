#/bin/python3

#######################################################################################
#                                                                                     #
#  Task to read in lap time data sent from the Farmtek Timing Console.                #
#  Lap times are pushed to a database table to collect the raw input for processing.  #
#  Restarts are handled in a rudimentary manner.                                      #
#                                                                                     #
############################################################ Pittsburgh Shootout LLC ##

import time
import atexit
import serial					# pySerial
import serial.tools.list_ports	# pySerial
import os, sys
sys.path.insert(0, os.path.abspath(".."))
from Common.config import Config
from Common.database_helper import *
import paho.mqtt.client as paho
import json
import datetime

def exit_handler():
	print(' Cleaning Up!')
	ser.close()
	client.loop_stop()
	exit(1)

def environment_check():
	return True

def create_mqtt_connection():
	def on_connect(client, userdata, flags, reason_code, properties):
		if reason_code == 0:
			print("MQTT Client Connected")
		else:
			print("MQTT Client NOT Connected, rc= " + str(reason_code))
		#client.subscribe("iotstack/mosquitto/healthcheck")
	client = paho.Client(paho.CallbackAPIVersion.VERSION2,client_id=client_id)
	client.username_pw_set(Config.MQTTUSERNAME, Config.MQTTPASSWORD)
	client.on_connect = on_connect
	client.connect(Config.TimingConsoleReader.MQTTBROKER, Config.MQTTPORT)
	return client

def sub_handler(client, userdata, msg):
    print(f"{msg.topic}: {msg.payload.decode()}")

def build_payload(insert, read_count, raw_time, timestamp):
	if(insert):
		# "Created Time"
		payload = {"read_count":read_count,"raw_time":raw_time,"created_at":timestamp}
	else:
		# "Updated Time"
		payload = {"read_count":read_count,"raw_time":raw_time,"updated_at":timestamp}
	return json.dumps(payload)

# Config check
if Config.FARMTEK_CONSOLE_PATH == "":
	print("Console path not specified! Exiting.")
	atexit.register(exit_handler)

# Wait for device connection
port_available = False
while not(port_available):
	ports = list(serial.tools.list_ports.comports())
	print("Device not found yet")
	for p in ports:
		if (p.device == Config.FARMTEK_CONSOLE_PATH):
			port_available = True
	time.sleep(0.5)
print("Device Found")
ser = serial.Serial(Config.FARMTEK_CONSOLE_PATH, Config.FARMTEK_CONSOLE_BAUD, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, timeout=1.0)


if __name__ == '__main__':
	restartStr = "^ RESTART-IGNORE TIME ^"
	lap_time_buffer = ""
	prev_lap_time = ""
	update_db_flag = False
	run_number = 0
	table_name = "laptimeraw"

	if(not environment_check()):
		print("Database Schema not correct. Exiting.")
		atexit.register(exit_handler)
	
	client_id = Config.TimingConsoleReader.MQTTCLIENTID
	client = create_mqtt_connection()
	client.on_message = sub_handler
	client.loop_start()
	prev_health_check = 0
	health_check_interval = 30 #seconds

	last_runtable_row_inserted = 0

	try:
		while True:
			if(ser.in_waiting > 1):
				lap_time_buffer = ser.read(ser.in_waiting).decode('ascii')
				lap_time_buffer = lap_time_buffer.replace('\x0e','').replace('\x0f','').replace('\r','').strip()
				ser.reset_input_buffer()
			else:
				lap_time_buffer = ""

			if len(lap_time_buffer) > 1:
				if lap_time_buffer == restartStr:
					# Restart pressed, next incoming time should be an UPDATE rather than an INSERT
					update_db_flag = True
				elif "(M)" in lap_time_buffer:
					if update_db_flag:
						# Manual stop button was pressed AND the restart button was pressed before that, so UPDATE prev to DNF
						# Run number isn't updated since the incorrect time already incremented the run number
						print("DB UDPATE:\t" + prev_lap_time + " to\tDNF")
						update_rawlaptime(table_name,[run_number,"DNF"])
						client.publish("/timing/laptime/updatetime",build_payload(False,run_number,"DNF",str(datetime.datetime.now())))
						row_updated = update_runtable("runtable","raw_time","DNF",last_runtable_row_inserted)
						print("Runtable row updated: " + str(row_updated))
						prev_lap_time = lap_time_buffer
						update_db_flag = False
					else:
						# Manual stop button was pressed, we need to treat this as a DNF, INSERT DNF
						run_number = run_number + 1
						print("DB INSERT:\tDNF")
						insert_rawlaptime(table_name,[run_number,"DNF"])
						client.publish("/timing/laptime/newtime",build_payload(True,run_number,"DNF",str(datetime.datetime.now())))

						#Find where to put this in the runtable
						fifo_runtable_row = retrieve_oldest_active_run_by_raw_time("runtable", "raw_time")
						if (fifo_runtable_row > -1):
							# We found a row, update that row with a raw time.
							row_updated = update_runtable("runtable","raw_time","DNF",fifo_runtable_row)
							print("Runtable row updated: " + str(row_updated))
						#else:
							# We did not get a row, something wrong. What do?
							# Send MQTT?
					
						#housekeeping
						last_runtable_row_inserted = fifo_runtable_row
						prev_lap_time = "DNF"
				elif update_db_flag:
					# Restart button was pressed and this is the next value, should UPDATE the previous time
					# Run number isn't updated since the incorrect time already incremented the run number
					print("DB UDPATE:\t" + prev_lap_time + " to\t" + lap_time_buffer)
					update_rawlaptime(table_name,[run_number,lap_time_buffer])
					client.publish("/timing/laptime/updatetime",build_payload(False,run_number,lap_time_buffer,str(datetime.datetime.now())))
					row_updated = update_runtable("runtable","raw_time",str(lap_time_buffer),last_runtable_row_inserted)
					print("Runtable row updated: " + str(row_updated))
					prev_lap_time = lap_time_buffer
					update_db_flag = False
				else:
					# Typical op, valid lap time flew in
					run_number = run_number + 1
					print("DB INSERT:\t" + lap_time_buffer)

					# Update laptime table
					insert_rawlaptime(table_name,[run_number,lap_time_buffer])
					client.publish("/timing/laptime/newtime",build_payload(True,run_number,lap_time_buffer,str(datetime.datetime.now())))
					
					#Find where to put this in the runtable
					fifo_runtable_row = retrieve_oldest_active_run_by_raw_time("runtable", "raw_time")
					if (fifo_runtable_row > -1):
						# We found a row, update that row with a raw time.
						row_updated = update_runtable("runtable","raw_time",str(lap_time_buffer),fifo_runtable_row)
						print("Runtable row updated: " + str(row_updated))
					#else:
						# We did not get a row, something wrong. What do?
						# Send MQTT?
					
					#housekeeping
					last_runtable_row_inserted = fifo_runtable_row
					prev_lap_time = lap_time_buffer
			if((time.time() - prev_health_check) > health_check_interval):
				client.publish("/timing/timeconsolereader/healthcheck",str(datetime.datetime.now()))
				prev_health_check = time.time()
	except KeyboardInterrupt:
		pass
	finally:	 
		atexit.register(exit_handler)