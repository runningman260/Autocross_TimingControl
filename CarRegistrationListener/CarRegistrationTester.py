import os, sys
sys.path.insert(0, os.path.abspath(".."))
from Common.config import Config
from Common.database_helper import *
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
		client.subscribe("/timing/carreg/confirm") #This goes here to sub on reconnection
	client = paho.Client(paho.CallbackAPIVersion.VERSION2,client_id=client_id)
	client.username_pw_set(Config.MQTTUSERNAME, Config.MQTTPASSWORD)
	client.on_connect = on_connect
	client.connect(Config.CarRegistration.MQTTBROKER, Config.MQTTPORT)
	return client

def sub_handler(client, userdata, msg):
	if(msg.topic == "/timing/carreg/confirm"):
		decoded_message = str(msg.payload.decode("utf-8"))
		json_message = json.loads(decoded_message)
		if(json_message["success"] == True):
			print("Registration submitted successfully")
		else:
			print("Registration not successful, radio for Nick")

def build_payload(tag_number, car_number, team_name, scan_time):
	payload = {"tag_number": tag_number, "car_number": car_number, "team_name": team_name, "scan_time": scan_time}
	return json.dumps(payload)


test_data = [
		["McGill Formula Electric (MFE)", "aa0325a60987088f4f1f0da4ea2e22b5", "1"],
		["UQ Racing Formula SAE Team", "8fc1a5d22db85d33eb3acd8d9b586184", "2"],
		["Running Snail Racing Team", "6be2ce858c97e4f86be4682b3fab02f9", "3"],
		["UC Davis Formula Racing", "07107bc510a1b2c6dbfced0327bd636f", "4"],
		["Panther Motorsports", "9736619fb52132f7b94e01efd4dbeb45", "30"],
		["NED Racers", "ebbc7cfea65e560d948524aabb806540", "47"],
		["UBRacing", "f711a6b7289806f5e83ade6388252100", "50"],
		["CalBaptist Racing", "bbef66da516755e806f37851cbd0cbac", "54"],
		["Cardiff Racing", "51bad3fec307d4d0028d25b4c53704a5", "59"],
		["Waterloo Formula Electric", "c18590c8c575b4d9a7b5b5f8c91c01ed", "60"],
		["Michigan State Formula Racing", "de558891e409019d530f64877bf8eab4", "61"],
		["Purdue Formula SAE", "1b7338eb708f244e284cf0579296d812", "63"],
		["Queen's Formula SAE", "fa875f7a964587022a8bd6ef1ace63e2", "64"],
		["Team Swinburne", "56a7f296a8a470eb81d8d503a13a7ad3", "69"],
		["Husky Formula Racing", "a47e0b4def19d3e25e9d58ed14f03441", "70"],
		["UNI Maribor GPE", "72b0c5b29cfb7dd9e55a94e91c1a3f7e", "71"],
		["EESC USP Formula SAE", "1a75c6e5f2ea37a0952b0ca581cdc016", "72"],
		["UOW Motorsport", "466f61fe0fff8649ce9c5384e7c7514c", "75"],
		["Joanneum Racing Graz", "07aac2c2f4dee14f60db60fc1388355e", "76"],
		["DJS Racing", "78418f0223b26dffdc3a2346d8121350", "84"],
		["TEIWM Racing Team", "dee13363c25ec26f3bb3c68b9114b787", "86"],
		["CSUF Titan Racing", "e71d81e63be379e753fe2356c7790bf1", "87"],
		["GT Motorsports", "b266d2f0bed2eef5668563e04c313387", "88"],
		["Curtin University", "a6e93a2db106424d5a52f92071c3eb29", "89"],
		["Formule ETS", "0a2827915167ad25f5c2ea37573f4ae6", "90"],
		["AMZracing", "0dc04d2e702bf9b5f80b3e100bc86a7a", "91"],
		["Penn State Racing", "415ca15f2d0040449ae067c11c0824ca", "92"],
		["TaipeiTechRacing", "6a29e57976f3171cb6f901ef559457d3", "93"],
		["Team Acceleracers", "babf17f0be8800852dbb57e5eab3915e", "94"],
		["Team Defianz Racing", "8135258cbdf5600f0d8a1575a06624e3", "96"],
		["FSRacing Team", "f9981adc36dc585b6e8c197e1c867d24", "98"],
		["RMIT Racing", "0fba80e35e81300df4ec2de19ea61a2a", "105"],
		["Wisconsin Racing (Combustion & Electric", "a805720f3b1e9943064faf56b5836485", "107"],
		["RMIT Electric Racing", "0244762ea53160ef7b7ed0023f80e662", "113"],
		["Rennstall Esslingen", "691238279941d82b2b7ea391c24808f7", "114"],
		["Leeds Formula Race Team", "d884248c3b8fb169c263a6ce82f79585", "115"],
		["Strohm + Söhne", "214fdf643e0428fc0fd7def4217f993e", "116"],
		["FS Team Delft", "2815fb07c0c333b3b94b3d5ea7469c95", "117"],
		["TDU Racing", "da9bb3ff07e52e12b58f03a4dbfc56d7", "126"],
		["Concordia Formula Racing", "ab094586d770a5e5985e76876426b267", "135"],
		["Oxford Brooks Racing", "20eaad081db7cec20894fcbd82ed7b7b", "136"],
		["VT Motorsports", "9e071ed0ae8eb277f139e203a263b6a5", "137"],
		["Formula Electric Racing NUST", "dee57f2f7d8bb307a82207276619016c", "141"],
		["Gryphon Racing", "24fc82ff7bf9a928c13c4f72fdfcf6d1", "142"],
		["Carnegie Mellon Racing", "a96b57cba129b3256906884ea8b375c2", "143"],
		["Dart Racing", "67eec1d7881bb79024a0dd991af77b10", "144"],
		["Team Spark", "8da2d12908146f667360ae8db9254ae9", "146"],
		["Velox Racing", "8b201bd6f7cc4e78b4af79a2832d2458", "150"],
		["Ecurie Aix", "f297bc710b1658f1d953d97f04aa5cb2", "151"],
		["Global Formula Racing", "44e4a0a791906b1e9bbfc73c0387071c", "157"],
		["UMSAE Polar Bear Racing Electric", "19e3f973a5e6adf810702d28b0dbe39e", "160"],
		["UQ Racing Formula SAE Team", "NEWTAG", "2"],
		["Monash Motorsport", "c7272088434b87ff463ae128ab18ac5e", "161"],
		["Schulich Racing", "89fcbca1a829f299f197f5dff199181e", "162"],
		["Mines Formula", "82b03fe5d333e54a9595c8324e9eecfc", "163"],
		["TTU Motorsports", "cfcaac0458f9e89405dbd07f4e4fdd9c", "164"],
		["Wildcat Formula Racing", "6be6c7da981bee7c3c531e99637611f1", "166"],
		["Equipe Poli Racing", "d7c60488c2c3053a2c9b3b952775f36a", "167"],
		["UMSAE Polar Bear Racing", "35fdb927bab97d0988bc6bd81b7256fe", "168"],
		["Formula uOttawa", "67dbfe2d5e820e0fab424a3f0c6094b3", "173"],
		["Zurra Formula Racing", "74cc33b9aaf0dcd0b24137c53a3d8e77", "177"],
		["E.Stall Esslingen", "f16d3534027f54c2c2210257b3e8708f", "179"],
		["Tampere UAS Motorsport", "0d7336071cfea3902615dbe03f6d7e1b", "181"],
		["NUST Formula Student Team", "323f41e3d0bdb9e3633b50fac23dc000", "185"],
		["VITC Formula Electric", "b63419d16371d6d3f762b1983ed89b60", "187"],
		["AGH Racing", "14580bfb9c014a7d54b67dbdc04faab3", "191"],
		["FS ONPU", "64bbe6d0ab55d3c1f74589efd56a52f7", "192"],
		["Kettering University Formula SAE", "2f17be4ab34553d44c884e69e8de5366", "202"],
		["Rennteam", "2e791ed7770db38f413db4627bc4567d", "208"],
		["SLU - Parks Racing", "6868fe8c6b77b136d114a738f2dcfa62", "209"],
		["Crimson Racing", "62b2cc42ac286f46ca1b1689453ac37e", "210"],
		["Panther Racing", "cf0796888dba473ab032efa24241f11c", "214"],
		["Race-Ing Team", "2a9bfc059013773816ea158bbf20e856", "215"],
		["LJMU e-Racing", "c882ce08398c6c1e8a270d969453c2c3", "221"],
		["RIT Racing", "2527015defed78fb8aaf4152b3f9951c", "222"],
		["Team Bath Racing Electric", "4c7979b7cec01b2fff30351b5f10af25", "224"],
		["PWR Racing Team", "ebabf6c7d757d8f245b197d83b3a912f", "226"],
		["Pravega Racing", "75d7834749d9ad45cc2ba12292cb1e68", "236"],
		["University of Auckland", "589d6d978dfbd3ed2b77179cfa7d3dbf", "237"],
		["Clemson University Formula SAE", "83e3bc8cad4f48bb2b2f8433887b4582", "242"],
		["The Sooner Racing Team", "efe97466abe586219fe08d2bab09dfbb", "243"],
		["Rensselaer Motorsport", "6c99860210caa1a8ffcd9c34c2d97d80", "246"],
		["KSU Motorsports", "74e9b32310f950dcb96ea680f52e7efa", "247"],
		["University Racing Eindhoven", "5cbbed5cf871947b73c4d4223a670287", "248"],
		["Fierce formula India", "65582beace0fcea8b1c4675ddf5d715d", "249"],
		["Cyclone Racing", "22ecc87eee89b016040ed69ee425fe5c", "250"],
		["RoadRunner Racing", "c8c62bc766e5ec481125177cb63659f3", "251"],
		["UTFR - UofT Formula Racing", "32f2950033559531369a3de410b14790", "252"],
		["Viking Motorsports", "c419da188fdccfdecc1c967e3667e249", "256"],
		["Formula Trinity", "b97738fa0238bfc1fc6bdf92a65563aa", "257"],
		["UTA Racing Formula SAE", "b8c6839f8ee40ce03aff12f7096a60e4", "259"],
		["Team Sleipnir", "9364a87e1f0b79f08851fa2d5a991092", "261"],
		["USC Racing", "871bda8f7745660bf13626336444948f", "273"],
		["Mizzou Racing", "28f34a85d8e9a9c00679a3e7764f06a6", "280"],
		["Silesia Automotive", "468954324b97910738b32a8965a8ce1a", "281"],
		["Bruin Racing FSAE", "07c71c3e47b5c340a401abf6c9906df4", "284"],
		["Warrior Racing", "7d67df18cf17991e93b5c4f7e6607d72", "285"],
		["Jayhawk Motorsports", "b1890e32dd28e15f79d4ce77e103c87f", "293"],
		["Rutgers Formula Racing", "2f768742577c3ae7e5f42fa674056215", "296"]
	]


if __name__ == '__main__':
	client_id = Config.CarRegistration.MQTTTESTERCLIENTID
	client = create_mqtt_connection()
	client.on_message = sub_handler
	client.loop_start()

	while (not client.is_connected()):
		print("Client not connected...")
	time.sleep(2)
	
	try:
		for index,entry in enumerate(test_data):
			print(str(index) + ": " + entry[2] + "\t" + entry[1] + "\t" + entry[0])
			client.publish("/timing/carreg/newcar",build_payload(entry[1], entry[2], entry[0], str(datetime.datetime.now())))
			time.sleep(1)
	except KeyboardInterrupt:
		pass
	finally:	 
		exit_handler()