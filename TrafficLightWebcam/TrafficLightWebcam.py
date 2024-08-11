#!/usr/bin/python3

#######################################################################################
#                                                                                     #
#  Task to listen for webcam actuation commands over MQTT and take a single photo     #
#  using a USB webcam plugged into the traffic light control Pi. The photo is sync'd  #
#  back to the timing server.                                                         #
#                                                                                     #
############################################################ Pittsburgh Shootout LLC ##

import time
import paho.mqtt.client as paho
import json
import atexit
import cv2
from time import gmtime, strftime
from config import Config
import datetime

def exit_handler():
	print(' Cleaning Up!')
	client.loop_stop()
	client.disconnect()
	exit(1)

def create_mqtt_connection():
	def on_connect(client, userdata, flags, reason_code, properties):
		if reason_code == 0:
			print("MQTT Client Connected")
		else:
			print("MQTT Client NOT Connected, rc= " + str(reason_code))
		client.subscribe("/timing/TLCtrl/newpattern") #This goes here to sub on reconnection
	client = paho.Client(paho.CallbackAPIVersion.VERSION2,client_id=client_id)
	client.username_pw_set(Config.MQTTUSERNAME, Config.MQTTPASSWORD)
	client.on_connect = on_connect
	client.connect(Config.MQTTBROKER, Config.MQTTPORT)
	return client

def sub_handler(client, userdata, msg):
	#print(f"{msg.topic}: {msg.payload.decode()}")
	if(msg.topic == "/timing/TLCtrl/phototrigger"):
		#decoded_message = str(msg.payload.decode("utf-8"))
		#json_message = json.loads(decoded_message)
		cam = cv2.VideoCapture(cam_port)
		result, image = cam.read()
		if result:
			cv2.imwrite("image" + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ".png", image)
		else:
			client.publish("/timing/trafficlightwebcam/BadImage",str(datetime.datetime.now()))

if __name__ == '__main__':
	client_id = Config.MQTTCLIENTID
	client = create_mqtt_connection()
	client.on_message = sub_handler
	client.loop_start()
	prev_health_check = 0
	health_check_interval = 30 #seconds
	cam_port = 0
		 

	while (not client.is_connected()):
		print("Client not connected...")
	time.sleep(2)

	prevTimestamp = round(time.time() * 1000)

	try:
		while True:
			# Send out a health check
			if((time.time() - prev_health_check) > health_check_interval):
				client.publish("/timing/trafficlightwebcam/healthcheck",str(datetime.datetime.now()))
				prev_health_check = time.time()
	except KeyboardInterrupt:
		pass
	finally:
		atexit.register(exit_handler)

client.loop_stop()
client.disconnect()