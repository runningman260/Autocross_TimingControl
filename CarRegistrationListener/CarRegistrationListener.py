#/bin/python3

#######################################################################################
#                                                                                     #
#  Task to read in registered cars.                                                   #
#  Car info is pushed to a database table to collect the input for processing.        #
#                                                                                     #
############################################################ Pittsburgh Shootout LLC ##

from config import Config
import time
import atexit
from database_helper import *
import paho.mqtt.client as paho
import json
import datetime

def exit_handler():
	print(' Cleaning Up!')
	client.loop_stop()
	exit(1)

def environment_check():
	## Check if table exists
	## If EXISTS, clear rows if desired
	## If !EXISTS, create

	delete_if_exists = False

	print("CHECKING")
	if(check_table_exist(table_name)):
		print("TABLE EXISTS")
		if(delete_if_exists):
			print("DELETING ROWS")
			delete_all_table_rows(table_name)
		else:
			print("NOT DELETING ROWS")
	else:
		print("CREATING")
		sql_cmd ="""
			CREATE TABLE {table_name}(
				id SERIAL PRIMARY KEY,
				scan_time VARCHAR(255),
				tag_number  VARCHAR(255),
				car_number VARCHAR(255),
				team_name VARCHAR(255),
				created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
				updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
				UNIQUE (car_number)
			)
			""".format(table_name=table_name)
		create_table(sql_cmd)

	## Check if function and trigger are present. If not, create
	function_name = table_name + "_trigger_set_timestamp"
	trigger_name = table_name + "_set_timestamp"
	if(not check_function_exists(function_name) and not check_trigger_exists(trigger_name)):
		print("Function or trigger do not exist, creating...")
		create_timestamp_function(function_name)
		create_timestamp_trigger(table_name, function_name, trigger_name)
	return True

def create_mqtt_connection():
	def on_connect(client, userdata, flags, reason_code, properties):
		if reason_code == 0:
			print("MQTT Client Connected")
		else:
			print("MQTT Client NOT Connected, rc= " + str(reason_code))
		client.subscribe("/timing/carreg/newcar") #This goes here to sub on reconnection
	client = paho.Client(paho.CallbackAPIVersion.VERSION2,client_id=client_id)
	client.username_pw_set(Config.MQTTUSERNAME, Config.MQTTPASSWORD)
	client.on_connect = on_connect
	client.connect(Config.MQTTBROKER, Config.MQTTPORT)
	return client

def sub_handler(client, userdata, msg):
	#print(f"{msg.topic}: {msg.payload.decode()}")
	if(msg.topic == "/timing/carreg/newcar"):
		decoded_message = str(msg.payload.decode("utf-8"))
		json_message = json.loads(decoded_message)
		json_message["team_name"] = json_message["team_name"].replace("'","")
		inserted = upsert_car(table_name, json_message["scan_time"], json_message["tag_number"], json_message["car_number"], json_message["team_name"])
		if(inserted):
			print("Inserted Car: " + str(json_message["car_number"]))
			client.publish("/timing/carreg/confirm_insert",build_payload(True,str(datetime.datetime.now())))
		else:
			print("Updated Car: " + str(json_message["car_number"]))
			client.publish("/timing/carreg/confirm_update",build_payload(True,str(datetime.datetime.now())))

def build_payload(success, timestamp):
	payload = {"success":success,"created_at":timestamp}
	return json.dumps(payload)

if __name__ == '__main__':
	table_name = "carreg"

	if(not environment_check()):
		print("Database Schema not correct. Exiting.")
		atexit.register(exit_handler)
	
	client_id = Config.MQTTCLIENTID
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