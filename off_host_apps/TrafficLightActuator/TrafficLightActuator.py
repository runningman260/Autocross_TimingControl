#!/usr/bin/python3

#######################################################################################
#                                                                                     #
#  Task to listen for traffic light pattern actuation commands over MQTT and          #
#  display those patterns on the traffic light via GPIO commands that run a relay     #
#  board.                                                                             #
#                                                                                     #
############################################################ Pittsburgh Shootout LLC ##

import RPi.GPIO as GPIO
import time
import paho.mqtt.client as paho
import json
import atexit
import os, sys
from config import Config
import datetime

def exit_handler():
	print(' Cleaning Up!')
	GPIO.cleanup()
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
	client.username_pw_set(Config.MQTT.USERNAME, Config.MQTT.PASSWORD)
	client.on_connect = on_connect
	client.connect(Config.MQTT.BROKER, Config.MQTT.PORT)
	return client

def sub_handler(client, userdata, msg):
	#print(f"{msg.topic}: {msg.payload.decode()}")
	if(msg.topic == "/timing/TLCtrl/newpattern"):
		decoded_message = str(msg.payload.decode("utf-8"))
		json_message = json.loads(decoded_message)
	
		global LightState
		if(json_message["RedState"] == 1):
			LightState = [1,0,0]
		if(json_message["YellowState"] == 1):
			LightState = [0,1,0]
		if(json_message["GreenState"] == 1):
			LightState = [0,0,1]
		print(LightState)

def control_LED(GPIO_Pin, state, prevTimestamp):
	interval = 250
	currentTime = round(time.time() * 1000)
	if(state == 2):
		#Do time things to blink
		if(currentTime - prevTimestamp >= interval):
			prevTimestamp = currentTime
			#if(GPIO.input(GPIO_Pin) == 1):
			#    GPIO.output(GPIO_Pin,GPIO.LOW)
			#else:
			#    GPIO.output(GPIO_Pin,GPIO.HIGH)
			print(str(GPIO_Pin) + " blink")
	if(state == 1):
		#Turn Lamp on
		GPIO.output(GPIO_Pin,GPIO.LOW)
		print(str(GPIO_Pin) + " on")
	if(state == 0):
		#Turn Lamp off
		GPIO.output(GPIO_Pin,GPIO.HIGH)
		print(str(GPIO_Pin) + " off")

if __name__ == '__main__':
	client_id = Config.MQTT.CLIENTID
	client = create_mqtt_connection()
	client.on_message = sub_handler
	client.loop_start()
	prev_health_check = 0
	health_check_interval = 30 #seconds

	while (not client.is_connected()):
		print("Client not connected...")
		time.sleep(0.01)
	time.sleep(2)
	print("Client Connected!")

	# Relay Pin Numbers
	#            [ R, G, Y]
	LightIndex = [26,20,21]
	# 2 = Blink
	# 1 = On
	# 0 = Off
	LightState = [1,0,0]
	oldLightState = [1,0,0]

	prevTimestamp = round(time.time() * 1000)

	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)

	GPIO.setup(LightIndex[0],GPIO.OUT)
	time.sleep(0.1)
	GPIO.setup(LightIndex[1],GPIO.OUT)
	time.sleep(0.1)
	GPIO.setup(LightIndex[2],GPIO.OUT)
	time.sleep(0.1)

	#startup sequence
	startSeq = [[1,1,1], #  R G Y
				[0,1,1], #  - G Y
				[0,0,1], #  - - Y
				[0,0,0], #  - - -
				[1,0,0]] #  R - -
	for seq in startSeq:
		for idx,currentLightState in enumerate(seq):
			if(currentLightState != oldLightState[idx]):
				control_LED(LightIndex[idx],currentLightState,prevTimestamp)
				oldLightState[idx] = currentLightState
		time.sleep(0.5)

	try:
		while True:
			for idx,currentLightState in enumerate(LightState):
				#print(str(currentLightState) + "\t" + str(oldLightState[idx]))
				if(currentLightState != oldLightState[idx]):
					control_LED(LightIndex[idx],currentLightState,prevTimestamp)
					oldLightState[idx] = currentLightState
			# Send out a health check
			if((time.time() - prev_health_check) > health_check_interval):
				client.publish("/timing/trafficlightactuator/healthcheck",str(datetime.datetime.now()))
				prev_health_check = time.time()
			time.sleep(0.1)
	except KeyboardInterrupt:
		pass
	except Exception as e:
		print(e)
	finally:
		atexit.register(exit_handler)
	
GPIO.cleanup()
client.loop_stop()
client.disconnect()
