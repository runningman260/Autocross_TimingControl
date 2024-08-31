#/bin/python3

#######################################################################################
#                                                                                     #
#  Task to read in registered cars.                                                   #
#  Car info is pushed to a database table to collect the input for processing.        #
#                                                                                     #
############################################################ Pittsburgh Shootout LLC ##

import time
import atexit
import os, sys
from config import Config
from database_helper import *
import paho.mqtt.client as paho
import json
import datetime

def exit_handler():
	print(' Cleaning Up!')
	client.loop_stop()
	exit(1)

def environment_check():
	delete_if_exists = False
	table_exists = False
	function_exists = False
	trigger_exists = False

	table_exists  = check_table_exist(table_name)
	function_name = table_name + "_set_timestamp"
	trigger_name  = table_name + "_trigger_set_timestamp"
	function_exists = check_function_exists(function_name) 
	trigger_exists  = check_trigger_exists(trigger_name)
	if(table_exists and delete_if_exists):
		print("Deleting all rows from " + table_name + "...", flush=True)
		delete_all_table_rows(table_name)
	print(table_name    + " Present: " + str(table_exists), flush=True)
	print(function_name + " Present: " + str(function_name), flush=True)
	print(trigger_name  + " Present: " + str(trigger_exists), flush=True)

	return (table_exists and function_exists and trigger_exists)

def create_mqtt_connection():
	def on_connect(client, userdata, flags, reason_code, properties):
		if reason_code == 0:
			print("MQTT Client Connected", flush=True)
		else:
			print("MQTT Client NOT Connected, rc= " + str(reason_code), flush=True)
		client.subscribe("/timing/carreg/newcar") #This goes here to sub on reconnection
	client = paho.Client(paho.CallbackAPIVersion.VERSION2,client_id=client_id)
	client.username_pw_set(Config.MQTT.USERNAME, Config.MQTT.PASSWORD)
	client.on_connect = on_connect
	client.connect(Config.MQTT.BROKER, Config.MQTT.PORT)
	return client

def sub_handler(client, userdata, msg):
	#print(f"{msg.topic}: {msg.payload.decode()}")
	if(msg.topic == "/timing/carreg/newcar"):
		decoded_message = str(msg.payload.decode("utf-8"))
		json_message = json.loads(decoded_message)
		json_message["team_name"] = json_message["team_name"].replace("'","")
		inserted = upsert_car(table_name, json_message["scan_time"], json_message["tag_number"], json_message["car_number"], json_message["team_name"])
		if(inserted == True):
			print("Inserted Car: " + str(json_message["car_number"]), flush=True)
			client.publish("/timing/carreg/confirm_insert",build_payload(json_message["team_name"] + ": #" + json_message["car_number"],str(datetime.datetime.now())))
		elif(inserted == False):
			print("Updated Car: " + str(json_message["car_number"]), flush=True)
			client.publish("/timing/carreg/confirm_update",build_payload(json_message["team_name"] + ": #" + json_message["car_number"],str(datetime.datetime.now())))
		else:
			print("Failed to access database table")
			client.publish("/timing/carreg/failed",build_payload(False,str(datetime.datetime.now())))

def build_payload(success, timestamp):
	payload = {"success":success,"created_at":timestamp}
	return json.dumps(payload)

if __name__ == '__main__':
	table_name = "carreg"

	if(not environment_check()):
		print("Database Schema not correct. Exiting.", flush=True)
		atexit.register(exit_handler)
	
	client_id = Config.MQTT.CLIENTID
	client = create_mqtt_connection()
	client.on_message = sub_handler
	client.loop_start()
	prev_health_check = 0
	health_check_interval = 30 #seconds

	try:
		while True:
			if((time.time() - prev_health_check) > health_check_interval):
				client.publish("/timing/carregistrationlistener/healthcheck",str(datetime.datetime.now()))
				prev_health_check = time.time()
	except KeyboardInterrupt:
		pass
	finally:	 
		atexit.register(exit_handler)