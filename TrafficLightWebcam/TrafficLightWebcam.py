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
import os, sys
from config import Config
import datetime

def exit_handler():
	print(' Cleaning Up!', flush=True)
	client.loop_stop()
	client.disconnect()
	exit(1)

def draw_text(img, text, font=cv2.FONT_HERSHEY_PLAIN, pos=(0, 0), font_scale=3, font_thickness=2, text_color=(0, 255, 0), text_color_bg=(0, 0, 0)):
	x, y = pos
	text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
	text_w, text_h = text_size
	cv2.rectangle(img, pos, (x + text_w, y + text_h), text_color_bg, -1)
	cv2.putText(img, text, (x, y + text_h + font_scale - 1), font, font_scale, text_color, font_thickness)
	return text_size

def create_mqtt_connection():
	def on_connect(client, userdata, flags, reason_code, properties):
		if reason_code == 0:
			print("MQTT Client Connected", flush=True)
		else:
			print("MQTT Client NOT Connected, rc= " + str(reason_code), flush=True)
		client.subscribe("/timing/TLCtrl/phototrigger") #This goes here to sub on reconnection
	client = paho.Client(paho.CallbackAPIVersion.VERSION2,client_id=client_id)
	client.username_pw_set(Config.MQTT.USERNAME, Config.MQTT.PASSWORD)
	client.on_connect = on_connect
	client.connect(Config.MQTT.BROKER, Config.MQTT.PORT)
	return client

def sub_handler(client, userdata, msg):
	#print(f"{msg.topic}: {msg.payload.decode()}")
	if(msg.topic == "/timing/TLCtrl/phototrigger"):
		#decoded_message = str(msg.payload.decode("utf-8"))
		#json_message = json.loads(decoded_message)
		cam = cv2.VideoCapture(cam_port)
		result, image = cam.read()
		if result:
			w, h = draw_text(image, strftime("%Y-%m-%d %H:%M:%S", gmtime()), pos=(10, 10))
			cv2.imwrite(os.path.join(image_folder_path , "image" + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ".png"), image)
			print("Image taken", flush=True)
		else:
			client.publish("/timing/trafficlightwebcam/BadImage",str(datetime.datetime.now()))
			print("Image not taken", flush=True)

if __name__ == '__main__':
	client_id = Config.MQTT.CLIENTID
	client = create_mqtt_connection()
	client.on_message = sub_handler
	client.loop_start()
	prev_health_check = 0
	health_check_interval = 30 #seconds
	cam_port = 0

	script_wd = os.path.abspath(os.path.dirname(__file__))
	image_folder_name = "StartLineImages"
	image_folder_path = script_wd + r"/" + image_folder_name
	if(not os.path.isdir(image_folder_path)):
		print("Does not Exist, Creating", flush=True)
		os.makedirs(image_folder_path)
	else:
		print("Image folder exists!", flush=True)

	while (not client.is_connected()):
		print("Client not connected...", flush=True)
		time.sleep(0.1)
	time.sleep(1)
	print("MQTT Client Connected", flush=True)

	try:
		while True:
			# Send out a health check
			if((time.time() - prev_health_check) > health_check_interval):
				client.publish("/timing/trafficlightwebcam/healthcheck",str(datetime.datetime.now()))
				prev_health_check = time.time()
			time.sleep(0.1)
	except KeyboardInterrupt:
		pass
	finally:
		atexit.register(exit_handler)

client.loop_stop()
client.disconnect()
