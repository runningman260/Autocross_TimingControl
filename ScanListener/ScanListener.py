#/bin/python3

#######################################################################################
#                                                                                     #
#  Task to read in registered cars.                                                   #
#  Car info is pushed to a database table to collect the input for processing.        #
#                                                                                     #
############################################################ Pittsburgh Shootout LLC ##

import os, sys
import time
import atexit
from config import Config
from database_helper import *
import paho.mqtt.client as paho
import json
import datetime

def exit_handler():
	print(' Cleaning Up!', flush=True)
	client.loop_stop()
	exit(1)

def create_mqtt_connection():
	def on_connect(client, userdata, flags, reason_code, properties):
		if reason_code == 0:
			print("MQTT Client Connected", flush=True)
		else:
			print("MQTT Client NOT Connected, rc= " + str(reason_code), flush=True)
		client.subscribe("/timing/slscan/newscan") #This goes here to sub on reconnection
		client.subscribe("/timing/flscan/newscan") #This goes here to sub on reconnection
		client.subscribe("/timing/webui/override") #This goes here to sub on reconnection
	client = paho.Client(paho.CallbackAPIVersion.VERSION2,client_id=client_id)
	client.username_pw_set(Config.MQTT.USERNAME, Config.MQTT.PASSWORD)
	client.on_connect = on_connect
	client.connect(Config.MQTT.BROKER, Config.MQTT.PORT)
	return client

def sub_handler(client, userdata, msg):
	#print(f"{msg.topic}: {msg.payload.decode()}")
	if(msg.topic == "/timing/slscan/newscan"):
		decoded_message = str(msg.payload.decode("utf-8"))
		json_message = json.loads(decoded_message)
		json_message["tag_number"] = json_message["tag_number"].replace('\r','')
		inserted = insert_newscan(startline_table_name, json_message["tag_number"], created_by="SCAN")
		print("Inserted Scan into SLScans table: " + str(json_message["tag_number"]), flush=True)
		## Look up tag to car number
		retreived_car_number = -1
		retreived_car_number = get_car_number("carreg",json_message["tag_number"])
		print("Retrieved Car Number: " + str(retreived_car_number), flush=True)
		if(int(retreived_car_number) > -1):
			## Insert car number into run table as new run
			run_created = create_new_run("runtable",str(retreived_car_number),"scanned_at_start_line")
			if(run_created is None): run_created = 0
			client.publish("/timing/scanlistener/confirm_run_create",build_payload((int(run_created)>0),str(retreived_car_number),msg.topic,str(datetime.datetime.now())))
		else:
			## The Tag ID does not exist in the carreg table.
			#run_created = create_new_run("runtable","car_num_not_found","scanned_at_start_line")
			#if(run_created is None): run_created = 0
			client.publish("/timing/scanlistener/confirm_run_create",build_payload(False,"car_num_not_found",msg.topic,str(datetime.datetime.now())))
		client.publish("/timing/scanlistener/confirm_insert",build_payload((inserted>0),str(json_message["tag_number"]),msg.topic,str(datetime.datetime.now())))

	if(msg.topic == "/timing/flscan/newscan"):
		decoded_message = str(msg.payload.decode("utf-8"))
		json_message = json.loads(decoded_message)
		inserted = insert_newscan(finishline_table_name, json_message["tag_number"])
		print("Inserted Scan in FLSCans table: " + str(json_message["tag_number"]), flush=True)
		## Need to work out how to insert these into the run table
		# SELECT id FROM runtable WHERE raw_time is null ORDER BY id LIMIT 1 RETURNING id;
		# SELECT id FROM runtable WHERE finishline_scan_status is null ORDER BY id LIMIT 1 RETURNING id;
		fifo_runtable_row = retrieve_oldest_active_run_by_scan_status("runtable", "finishline_scan_status")
		print(fifo_runtable_row)
		if (fifo_runtable_row > -1):
			# We found a row, update that row with a scan status.
			row_updated = update_runtable("runtable","finishline_scan_status","scanned_at_finish_line",fifo_runtable_row)
			print("Runtable row updated: " + str(row_updated), flush=True)
		#else:
			# We did not get a row, something wrong. What do?
			# Send MQTT?


	if(msg.topic == "/timing/webui/override"):
		# Since we don't have a tag_number, we'll put the car_number in the tag column so that we know who was inserted
		decoded_message = str(msg.payload.decode("utf-8"))
		json_message = json.loads(decoded_message)
		inserted = insert_newscan(startline_table_name, str("override_" + json_message["car_number"]),created_by="ui_override")
		print("Inserted Scan: " + "ui_override" + " " + str(json_message["car_number"]), flush=True)
		## Insert car number into run table as new run
		run_created = create_new_run("runtable",json_message["car_number"],"ui_override")
		if(run_created is None): run_created = 0
		client.publish("/timing/scanlistener/confirm_run_create",build_payload((int(run_created)>0),json_message["car_number"],msg.topic,str(datetime.datetime.now())))
		client.publish("/timing/scanlistener/confirm_insert",build_payload((inserted>0),str(json_message["tag_number"]),msg.topic,str(datetime.datetime.now())))


def build_payload(success, tag_number, source, timestamp):
	payload = {"success":success,"tag":tag_number,"source":source,"created_at":timestamp}
	return json.dumps(payload)

if __name__ == '__main__':
	startline_table_name = "startlinescan"
	finishline_table_name = "finishlinescan"
	runtable_name = "runtable"

	#if(not environment_check([startline_table_name, finishline_table_name, runtable_name])):
	#	print("Database Schema not correct. Exiting.")
	#	atexit.register(exit_handler)
	
	client_id = Config.MQTT.CLIENTID
	client = create_mqtt_connection()
	client.on_message = sub_handler
	client.loop_start()
	prev_health_check = 0
	health_check_interval = 30 #seconds

	try:
		while True:
			if((time.time() - prev_health_check) > health_check_interval):
				client.publish("/timing/scanlistener/healthcheck",str(datetime.datetime.now()))
				prev_health_check = time.time()
	except KeyboardInterrupt:
		pass
	except Exception as e:
		print(e)
		pass
	finally:	 
		atexit.register(exit_handler)
