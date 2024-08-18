#/bin/python3

#######################################################################################
#                                                                                     #
#  Test script to emulate start line scans, finish line scans, and timing console     #
#    input, all to exercise the run table. At the end of the test, the run table      #
#    is wiped clean.                                                                  #
#                                                                                     #
############################################################ Pittsburgh Shootout LLC ##

# !! Assumes the CarReg table was previously created and populated. 
# !! Do this first by running CarRegistrationListener.py and Car RegistrationTester.py in separate windows. 
# !! CarReg does not get cleared with clear_schema=True below.

# !! Assumes ScanListener.py is running in a separate window. Do this before running the tests.

import time
import paho.mqtt.client as paho
import json
import datetime
import sys
import os
sys.path.insert(0, os.path.abspath(".."))
from Common.config import Config
from Common.database_helper import *
from TestCases import *

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
	client = paho.Client(paho.CallbackAPIVersion.VERSION2,client_id=client_id)
	client.username_pw_set(Config.MQTTUSERNAME, Config.MQTTPASSWORD)
	client.on_connect = on_connect
	client.connect(Config.RunTableTester.MQTTBROKER, Config.MQTTPORT)
	return client

if __name__ == '__main__':
	client_id = Config.RunTableTester.MQTTCLIENTID
	client = create_mqtt_connection()
	client.on_message = sub_handler
	client.loop_start()

	while (not client.is_connected()):
		print("Client not connected...")
	time.sleep(2)
	
	try:
		# set clear_schema=False to inspect the tables after the test

		# Simple 1-run entry
		Test1.run(client, clear_schema=True)

		# Simple 2-run entry
		Test2.run(client, clear_schema=True)
		
	except KeyboardInterrupt:
		pass
	except Exception as e:
		print(e)
	finally:	 
		exit_handler()