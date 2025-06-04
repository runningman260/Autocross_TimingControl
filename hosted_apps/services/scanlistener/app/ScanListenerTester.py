import os, sys
from config import Config
import time
import paho.mqtt.client as paho
import json
import datetime
import sys

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
		client.subscribe("/timing/scanlistener/confirm_insert") #This goes here to sub on reconnection
		client.subscribe("/timing/scanlistener/confirm_run_create") #This goes here to sub on reconnection
	client = paho.Client(paho.CallbackAPIVersion.VERSION2,client_id=client_id)
	client.username_pw_set(Config.MQTT.USERNAME, Config.MQTT.PASSWORD)
	client.on_connect = on_connect
	client.connect(Config.MQTT.BROKER, Config.MQTT.PORT)
	return client

def sub_handler(client, userdata, msg):
	decoded_message = str(msg.payload.decode("utf-8"))
	json_message = json.loads(decoded_message)
	if(msg.topic == "/timing/scanlistener/confirm_insert"):
		if(json_message["success"] == True):
			print("Run record submitted successfully")
		else:
			print("Run record not successful, radio for Nick")
	if(msg.topic == "/timing/scanlistener/confirm_run_create"):
		if(json_message["success"] == True):
			print("Run table insert submitted successfully")
		else:
			print("Run table insert not successful, radio for Nick")

def build_payload(tag_number, scan_number=None):
	if(scan_number == None):
		#override case
		payload = {"tag_number": tag_number}
	else:
		payload = {"tag_number": tag_number, "scan_number": scan_number}
	return json.dumps(payload)


test_data = [
		["aa0325a60987088f4f1f0da4ea2e22b5"],
		["8fc1a5d22db85d33eb3acd8d9b586184"],
		["6be2ce858c97e4f86be4682b3fab02f9"],
		["07107bc510a1b2c6dbfced0327bd636f"],
		["9736619fb52132f7b94e01efd4dbeb45"],
		["ebbc7cfea65e560d948524aabb806540"],
		["f711a6b7289806f5e83ade6388252100"],
		["bbef66da516755e806f37851cbd0cbac"],
		["51bad3fec307d4d0028d25b4c53704a5"],
		["c18590c8c575b4d9a7b5b5f8c91c01ed"],
		["de558891e409019d530f64877bf8eab4"],
		["1b7338eb708f244e284cf0579296d812"],
		["fa875f7a964587022a8bd6ef1ace63e2"],
		["56a7f296a8a470eb81d8d503a13a7ad3"],
		["a47e0b4def19d3e25e9d58ed14f03441"],
		["72b0c5b29cfb7dd9e55a94e91c1a3f7e"],
		["1a75c6e5f2ea37a0952b0ca581cdc016"],
		["466f61fe0fff8649ce9c5384e7c7514c"],
		["07aac2c2f4dee14f60db60fc1388355e"],
		["78418f0223b26dffdc3a2346d8121350"],
		["dee13363c25ec26f3bb3c68b9114b787"],
		["e71d81e63be379e753fe2356c7790bf1"],
		["b266d2f0bed2eef5668563e04c313387"],
		["a6e93a2db106424d5a52f92071c3eb29"],
		["0a2827915167ad25f5c2ea37573f4ae6"],
		["0dc04d2e702bf9b5f80b3e100bc86a7a"],
		["415ca15f2d0040449ae067c11c0824ca"],
		["6a29e57976f3171cb6f901ef559457d3"],
		["babf17f0be8800852dbb57e5eab3915e"],
		["8135258cbdf5600f0d8a1575a06624e3"],
		["f9981adc36dc585b6e8c197e1c867d24"],
		["0fba80e35e81300df4ec2de19ea61a2a"],
		["a805720f3b1e9943064faf56b5836485"],
		["0244762ea53160ef7b7ed0023f80e662"],
		["691238279941d82b2b7ea391c24808f7"],
		["d884248c3b8fb169c263a6ce82f79585"],
		["214fdf643e0428fc0fd7def4217f993e"],
		["2815fb07c0c333b3b94b3d5ea7469c95"],
		["da9bb3ff07e52e12b58f03a4dbfc56d7"],
		["ab094586d770a5e5985e76876426b267"],
		["20eaad081db7cec20894fcbd82ed7b7b"],
		["9e071ed0ae8eb277f139e203a263b6a5"],
		["dee57f2f7d8bb307a82207276619016c"],
		["24fc82ff7bf9a928c13c4f72fdfcf6d1"],
		["a96b57cba129b3256906884ea8b375c2"],
		["67eec1d7881bb79024a0dd991af77b10"],
		["8da2d12908146f667360ae8db9254ae9"],
		["8b201bd6f7cc4e78b4af79a2832d2458"],
		["f297bc710b1658f1d953d97f04aa5cb2"],
		["44e4a0a791906b1e9bbfc73c0387071c"],
		["19e3f973a5e6adf810702d28b0dbe39e"],
		["c7272088434b87ff463ae128ab18ac5e"],
		["89fcbca1a829f299f197f5dff199181e"],
		["82b03fe5d333e54a9595c8324e9eecfc"],
		["cfcaac0458f9e89405dbd07f4e4fdd9c"],
		["6be6c7da981bee7c3c531e99637611f1"],
		["d7c60488c2c3053a2c9b3b952775f36a"],
		["35fdb927bab97d0988bc6bd81b7256fe"],
		["67dbfe2d5e820e0fab424a3f0c6094b3"],
		["74cc33b9aaf0dcd0b24137c53a3d8e77"],
		["f16d3534027f54c2c2210257b3e8708f"],
		["0d7336071cfea3902615dbe03f6d7e1b"],
		["323f41e3d0bdb9e3633b50fac23dc000"],
		["b63419d16371d6d3f762b1983ed89b60"],
		["14580bfb9c014a7d54b67dbdc04faab3"],
		["64bbe6d0ab55d3c1f74589efd56a52f7"],
		["2f17be4ab34553d44c884e69e8de5366"],
		["2e791ed7770db38f413db4627bc4567d"],
		["6868fe8c6b77b136d114a738f2dcfa62"],
		["62b2cc42ac286f46ca1b1689453ac37e"],
		["cf0796888dba473ab032efa24241f11c"],
		["2a9bfc059013773816ea158bbf20e856"],
		["c882ce08398c6c1e8a270d969453c2c3"],
		["2527015defed78fb8aaf4152b3f9951c"],
		["4c7979b7cec01b2fff30351b5f10af25"],
		["ebabf6c7d757d8f245b197d83b3a912f"],
		["75d7834749d9ad45cc2ba12292cb1e68"],
		["589d6d978dfbd3ed2b77179cfa7d3dbf"],
		["83e3bc8cad4f48bb2b2f8433887b4582"],
		["efe97466abe586219fe08d2bab09dfbb"],
		["6c99860210caa1a8ffcd9c34c2d97d80"],
		["74e9b32310f950dcb96ea680f52e7efa"],
		["5cbbed5cf871947b73c4d4223a670287"],
		["65582beace0fcea8b1c4675ddf5d715d"],
		["22ecc87eee89b016040ed69ee425fe5c"],
		["c8c62bc766e5ec481125177cb63659f3"],
		["32f2950033559531369a3de410b14790"],
		["c419da188fdccfdecc1c967e3667e249"],
		["b97738fa0238bfc1fc6bdf92a65563aa"],
		["b8c6839f8ee40ce03aff12f7096a60e4"],
		["9364a87e1f0b79f08851fa2d5a991092"],
		["871bda8f7745660bf13626336444948f"],
		["28f34a85d8e9a9c00679a3e7764f06a6"],
		["468954324b97910738b32a8965a8ce1a"],
		["07c71c3e47b5c340a401abf6c9906df4"],
		["7d67df18cf17991e93b5c4f7e6607d72"],
		["b1890e32dd28e15f79d4ce77e103c87f"],
		["2f768742577c3ae7e5f42fa674056215"]
	]


if __name__ == '__main__':
	client_id = Config.MQTT.TESTERCLIENTID
	client = create_mqtt_connection()
	client.on_message = sub_handler
	client.loop_start()

	while (not client.is_connected()):
		print("Client not connected...")
	time.sleep(2)
	
	try:
		#print("Start Line Entries Test")
		#for index,entry in enumerate(test_data):
		#	print(str(index) + ": " + entry[0])
		#	client.publish("/timing/slscan/newscan",build_payload(entry[0],index+1))
		#	time.sleep(0.5)
		#
		#print("Finish Line Entries Test")
		#for index,entry in enumerate(test_data):
		#	print(str(index) + ": " + entry[0])
		#	client.publish("/timing/flscan/newscan",build_payload(entry[0],index+1))
		#	time.sleep(0.5)
#
		#print("Override Start Line Entries Test")
		#for index,entry in enumerate(test_data):
		#	print(str(index) + ": " + entry[0])
		#	client.publish("/timing/webui/override",build_payload(entry[0]))
		#	time.sleep(0.5)		

		## Testing RunTable Car Number Entry with VALID tag number and VALID scan number
		#print("Scanning in: " + "200070839A9D0B1F")
		#client.publish("/timing/slscan/newscan",build_payload("200070839A9D0B1F",0))
		#client.publish("/timing/TLCtrl/phototrigger",json.dumps("A"))
		#
		#time.sleep(0.5)

		#print("Scanning in: " + "200070839A9D0B20")
		#client.publish("/timing/slscan/newscan",build_payload("200070839A9D0B20",0))
		#client.publish("/timing/TLCtrl/phototrigger",json.dumps("A"))
		#
		#time.sleep(0.5)
#
		print("Scanning in: " + "200070839A9D0B20")
		client.publish("/timing/slscan/newscan",build_payload("200070839A9D0B24",0))
		client.publish("/timing/TLCtrl/phototrigger",json.dumps("A"))
		
		time.sleep(0.5)
#
		#print("Scanning in: " + "200070839A9D0B20")
		#client.publish("/timing/slscan/newscan",build_payload("200070839A9D0B31",0))
		#client.publish("/timing/TLCtrl/phototrigger",json.dumps("A"))
		#
		#time.sleep(0.5)

		## Testing RunTable Car Number Entry with VALID tag number and VALID scan number
		#print("Scanning in: " + 'c7272088434b87ff463ae128ab18ac5e')
		#client.publish("/timing/flscan/newscan",build_payload('c7272088434b87ff463ae128ab18ac5e',0))
		#time.sleep(0.5)

		### Testing RunTable Car Number Entry with INVALID tag number and VALID scan number
		#print("Scanning in: " + '7')
		#client.publish("/timing/slscan/newscan",build_payload('7',1))
		#time.sleep(0.5)
#
		### Testing RunTable Car Number Entry with VALID tag number and INVALID scan number
		#print("Scanning in: " + 'c7272088434b87ff463ae128ab18ac5e')
		#client.publish("/timing/slscan/newscan",build_payload('c7272088434b87ff463ae128ab18ac5e',0))
		#time.sleep(0.5)
	except KeyboardInterrupt:
		pass
	finally:	 
		exit_handler()