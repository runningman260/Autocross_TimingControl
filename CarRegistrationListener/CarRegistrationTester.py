import os, sys
from config import Config
from database_helper import *
import time
import paho.mqtt.client as paho
import json
import datetime
import sys
import csv

def exit_handler():
	print(' Cleaning Up!')
	client.loop_stop()
	sys.exit()

def create_mqtt_connection():
	def on_connect(client, userdata, flags, reason_code, properties):
		if reason_code == 0:
			print("MQTT Client Connected")
		else:
			print("MQTT Client NOT Connected, rc= " + str(reason_code))
		client.subscribe("/timing/carreg/confirm") #This goes here to sub on reconnection
	client = paho.Client(paho.CallbackAPIVersion.VERSION2,client_id=client_id)
	client.username_pw_set(Config.MQTT.USERNAME, Config.MQTT.PASSWORD)
	client.on_connect = on_connect
	client.connect(Config.MQTT.BROKER, Config.MQTT.PORT)
	return client

def sub_handler(client, userdata, msg):
	if(msg.topic == "/timing/carreg/confirm"):
		decoded_message = str(msg.payload.decode("utf-8"))
		json_message = json.loads(decoded_message)
		if(json_message["success"] == True):
			print("Registration submitted successfully")
		else:
			print("Registration not successful, radio for Nick")

def build_payload(tag_number, car_number, team_name, car_class, scan_time):
	payload = {"tag_number": tag_number, "car_number": car_number, "team_name": team_name, "class": car_class, "scan_time": scan_time,}
	return json.dumps(payload)

def getCSVData():
	with open('PS_2024_Registration.csv', newline='') as csvfile:
		reader = csv.DictReader(csvfile)
		row_index = 0
		for row in reader:
			test_data.append([test_tags[row_index],row['car_number'],row['team_name'],row['class']])
			row_index = row_index + 1

test_data = []
test_tags = [   "200070839A9D0B1F", "200070839A9D0B20", "200070839A9D0B21", "200070839A9D0B22",
				"200070839A9D0B23", "200070839A9D0B24", "200070839A9D0B25", "200070839A9D0B26",
				"200070839A9D0B27", "200070839A9D0B28", "200070839A9D0B29", "200070839A9D0B2A",
				"200070839A9D0B2B", "200070839A9D0B2C", "200070839A9D0B2D", "200070839A9D0B2E",
				"200070839A9D0B2F", "200070839A9D0B30", "200070839A9D0B31", "200070839A9D0B32",
				"200070839A9D0B33", "200070839A9D0B34", "200070839A9D0B35", "200070839A9D0B36",
				"200070839A9D0B37", "200070839A9D0B38", "200070839A9D0B39", "200070839A9D0B3A",
				"200070839A9D0B3B", "200070839A9D0B3C", "200070839A9D0B3D", "200070839A9D0B3E",
				"200070839A9D0B3F", "200070839A9D0B40", "200070839A9D0B41", "200070839A9D0B42",
				"200070839A9D0B43", "200070839A9D0B44"]

if __name__ == '__main__':
	client_id = Config.MQTT.TESTERCLIENTID
	client = create_mqtt_connection()
	client.on_message = sub_handler
	client.loop_start()

	while (not client.is_connected()):
		print("Client not connected...")
		time.sleep(0.01)
	time.sleep(1)
	print("Client Connected!")
	
	try:
		getCSVData()
		for index,entry in enumerate(test_data):
			print(str(index) + ": " + entry[2] + "\t" + entry[1] + "\t" + entry[0] + "\t" + entry[3])
			client.publish("/timing/carreg/newcar",build_payload(entry[0], entry[1], entry[2], entry[3], str(datetime.datetime.now())))
			time.sleep(1)
	except KeyboardInterrupt:
		pass
	except Exception as e:
		print(e)
	finally:	 
		exit_handler()