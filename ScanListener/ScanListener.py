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

	for table_name in [startline_table_name, finishline_table_name]:
		print("CHECKING if " + table_name + " EXISTS")
		if(check_table_exist(table_name)):
			print(table_name + " EXISTS")
			if(delete_if_exists):
				print("DELETING ROWS")
				delete_all_table_rows(table_name)
			else:
				print("NOT DELETING ROWS")
		else:
			print("CREATING " + table_name)
			sql_cmd ="""
				CREATE TABLE {table_name}(
					id SERIAL PRIMARY KEY,
					scan_number VARCHAR(255),
					tag_number  VARCHAR(255),
					created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
					updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
				""".format(table_name=table_name)
			if(table_name == startline_table_name ):
				sql_cmd = sql_cmd + """
					,created_by  VARCHAR(255)
				"""
			sql_cmd = sql_cmd + ")"
			create_table(sql_cmd)

		## Check if function and trigger are present. If not, create
		function_name = table_name + "_trigger_set_timestamp"
		trigger_name = table_name + "_set_timestamp"
		if(not check_function_exists(function_name) and not check_trigger_exists(trigger_name)):
			print("Function or trigger for " + table_name + " do not exist, creating...")
			create_timestamp_function(function_name)
			create_timestamp_trigger(table_name, function_name, trigger_name)
	return True

def create_mqtt_connection():
	def on_connect(client, userdata, flags, reason_code, properties):
		if reason_code == 0:
			print("MQTT Client Connected")
		else:
			print("MQTT Client NOT Connected, rc= " + str(reason_code))
		client.subscribe("/timing/slscan/newscan") #This goes here to sub on reconnection
		client.subscribe("/timing/flscan/newscan") #This goes here to sub on reconnection
		client.subscribe("/timing/webui/override") #This goes here to sub on reconnection
	client = paho.Client(paho.CallbackAPIVersion.VERSION2,client_id=client_id)
	client.username_pw_set(Config.MQTTUSERNAME, Config.MQTTPASSWORD)
	client.on_connect = on_connect
	client.connect(Config.MQTTBROKER, Config.MQTTPORT)
	return client

def sub_handler(client, userdata, msg):
	#print(f"{msg.topic}: {msg.payload.decode()}")
	if(msg.topic == "/timing/slscan/newscan"):
		decoded_message = str(msg.payload.decode("utf-8"))
		json_message = json.loads(decoded_message)
		inserted = insert_newscan(startline_table_name, json_message["tag_number"], scan_number=json_message["scan_number"], created_by="SCAN")
		print("Inserted Scan: " + str(json_message["scan_number"]) + " " + str(json_message["tag_number"]))
		## Look up tag to car number
		retreived_car_number  = get_car_number("carreg",json_message["tag_number"])
		print("Retrieved Car Number: " + str(retreived_car_number))
		if(int(retreived_car_number) > 0):
			## Insert car number into run table as new run
			run_created = create_new_run("runtable",str(retreived_car_number),"scanned at start line")
			if(run_created is None): run_created = 0
			client.publish("/timing/scanlistener/confirm_run_create",build_payload((int(run_created)>0),str(retreived_car_number),msg.topic,str(datetime.datetime.now())))
		else:
			## The Tag ID does not exist in the carreg table.
			run_created = create_new_run("runtable","car_num_not_found","scanned_at_start_line")
			if(run_created is None): run_created = 0
			client.publish("/timing/scanlistener/confirm_run_create",build_payload((int(run_created)>0),"car_num_not_found",msg.topic,str(datetime.datetime.now())))
		client.publish("/timing/scanlistener/confirm_insert",build_payload((inserted>0),str(json_message["tag_number"]),msg.topic,str(datetime.datetime.now())))

	if(msg.topic == "/timing/flscan/newscan"):
		decoded_message = str(msg.payload.decode("utf-8"))
		json_message = json.loads(decoded_message)
		inserted = insert_newscan(finishline_table_name, json_message["tag_number"], scan_number=json_message["scan_number"])
		print("Inserted Scan: " + str(json_message["scan_number"]) + " " + str(json_message["tag_number"]))
		## Need to work out how to insert these into the run table

	if(msg.topic == "/timing/webui/override"):
		# Since we don't have a tag_number, we'll put the car_number in the tag column so that we know who was inserted
		decoded_message = str(msg.payload.decode("utf-8"))
		json_message = json.loads(decoded_message)
		inserted = insert_newscan(startline_table_name, str("override_" + json_message["car_number"]),scan_number="" ,created_by="ui_override")
		print("Inserted Scan: " + "ui_override" + " " + str(json_message["car_number"]))
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
				client.publish("/timing/scanlistener/healthcheck",str(datetime.datetime.now()))
				prev_health_check = time.time()
	except KeyboardInterrupt:
		pass
	finally:	 
		atexit.register(exit_handler)