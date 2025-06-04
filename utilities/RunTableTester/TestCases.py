import time
import paho.mqtt.client as paho
import json
import datetime
import sys
import os
from config import Config
from database_helper import *

def sub_handler(client, userdata, msg):
	decoded_message = str(msg.payload.decode("utf-8"))
	json_message = json.loads(decoded_message)

def build_payload(tag_number, scan_number=None):
	if(scan_number == None):
		#override case
		payload = {"tag_number": tag_number}
	else:
		payload = {"tag_number": tag_number, "scan_number": scan_number}
	return json.dumps(payload)

def build_payload_time(insert, read_count, raw_time, timestamp):
	if(insert):
		# "Created Time"
		payload = {"read_count":read_count,"raw_time":raw_time,"created_at":timestamp}
	else:
		# "Updated Time"
		payload = {"read_count":read_count,"raw_time":raw_time,"updated_at":timestamp}
	return json.dumps(payload)

class Test1:
	#  Test 1:
	#  1. Fire off startline scan
	#  2. Check that the scanned tag was translated to a car number, added to the
	#     startline scans table, and added to the run table.
	#  3. Fire off a finish line scan.
	#  4. Check that the scanned tag was translated to a car number, added to the
	#     finish line scans table, and added to the run table.
	#  5. Fire off a timer read.
	#  6. Check that the time was placed in the correct row in the run table, as 
	#     well as the raw_times table.
	def run(client, clear_schema=None):
		# 1.
		print("Step 1")
		print("SL Scan: " + 'c7272088434b87ff463ae128ab18ac5e')
		client.publish("/timing/slscan/newscan",build_payload('c7272088434b87ff463ae128ab18ac5e',0)) # car number 161
		time.sleep(0.5)
		# 2.1
		print("Step 2.1")
		response = run_query("select car_number from runtable where id = 1;")
		if(response is not None):
			if(response[0] == "161"): print("Step 1 Success, RunTable row created with correct car number")
			else: print("Row created in runtable with incorrect car number: " + str(response))
		else: print("Row was not created in RuntTable")
		# 2.2
		print("Step 2.2")
		response = run_query("select tag_number from startlinescan where id = 1;")
		if(response is not None):
			if(response[0] == "c7272088434b87ff463ae128ab18ac5e"): print("Step 1 Success, Startlinescan row created with correct tag number")
			else: print("Row created in startlinescan with incorrect tag number: " + str(response))
		else: print("Row was not created in startlinescan")
		# 3.
		print("Step 3")
		print("FL Scan: " + 'c7272088434b87ff463ae128ab18ac5e')
		client.publish("/timing/flscan/newscan",build_payload('c7272088434b87ff463ae128ab18ac5e',0))
		time.sleep(0.5)
		# 4.1
		print("Step 4.1")
		response = run_query("select finishline_scan_status from runtable where id = 1;")
		if(response is not None):
			if(response[0] == "scanned_at_finish_line"): print("Step 3 Success, RunTable row updated with correct finishline_scan_status")
			else: print("Row updated in runtable with incorrect finishline_scan_status: " + str(response))
		else: print("Row was not created in RuntTable")
		# 4.2
		print("Step 4.2")
		response = run_query("select tag_number from finishlinescan where id = 1;")
		if(response is not None):
			if(response[0] == "c7272088434b87ff463ae128ab18ac5e"): print("Step 3 Success, finishlinescan row created with correct tag number")
			else: print("Row created in finishlinescan with incorrect tag number: " + str(response))
		else: print("Row was not created in finishlinescan")
		# 5.
		print("Step 5")
		insert_rawlaptime("laptimeraw",[0,"69.420"])
		fifo_runtable_row = retrieve_oldest_active_run_by_raw_time("runtable", "raw_time")
		if (fifo_runtable_row > -1):
			# We found a row, update that row with a raw time.
			row_updated = update_runtable("runtable","raw_time",str("69.420"),fifo_runtable_row)
		client.publish("/timing/laptime/newtime",build_payload_time(True,0,"69.420",str(datetime.datetime.now())))
		time.sleep(0.5)
		# 6.1
		print("Step 6.1")
		response = run_query("select raw_time from runtable where id = 1;")
		if(response is not None):
			if(response[0] == "69.420"): print("Step 5 Success, RunTable row updated with correct raw_time")
			else: print("Row updated in runtable with incorrect raw_time: " + str(response))
		else: print("Row was not created in RuntTable")
		# 6.2
		print("Step 6.2")
		response = run_query("select raw_time from laptimeraw where run_id = 1;")
		if(response is not None):
			if(response[0] == "69.420"): print("Step 5 Success, laptimeraw row created with correct raw_time")
			else: print("Row created in laptimeraw with incorrect raw_time: " + str(response))
		else: print("Row was not created in laptimeraw")

		print("Test 1 Complete")

		if(clear_schema is not None and clear_schema):
			print("Clearing Schema")
			clear_and_create_schema()

class Test2:
	#  Test 2:
	#  1. Fire off startline scan
	#  2. Check that the scanned tag was translated to a car number, added to the
	#     startline scans table, and added to the run table.
	#  3. Fire off a second startline scan
	#  4. Check that the second scanned tag was translated to a car number, added to the
	#     startline scans table, and added to the run table.
	#  5. Fire off a finish line scan.
	#  6. Check that the scanned tag was translated to a car number, added to the
	#     finish line scans table, and added to the run table at the first scan's row index.
	#  7. Fire off a timer read.
	#  8. Check that the time was placed in the correct row in the run table, as 
	#     well as the raw_times table.
	#  9. Fire off a second finish line scan.
	# 10. Check that the scanned tag was translated to a car number, added to the
	#     finish line scans table, and added to the run table at the second scan's row index.
	# 11. Fire off a timer read.
	# 12. Check that the time was placed in the correct row in the run table, as 
	#     well as the raw_times table.
	def run(client, clear_schema=None):
		# 1.
		print("Step 1")
		print("SL Scan: " + 'c7272088434b87ff463ae128ab18ac5e')
		client.publish("/timing/slscan/newscan",build_payload('c7272088434b87ff463ae128ab18ac5e',0)) # car number 161
		time.sleep(0.5)
		# 2.1
		print("Step 2.1")
		response = run_query("select car_number from runtable where id = 1;")
		if(response is not None):
			if(response[0] == "161"): print("Step 1 Success, RunTable row created with correct car number")
			else: print("Row created in runtable with incorrect car number: " + str(response))
		else: print("Row was not created in RuntTable")
		# 2.2
		print("Step 2.2")
		response = run_query("select tag_number from startlinescan where id = 1;")
		if(response is not None):
			if(response[0] == "c7272088434b87ff463ae128ab18ac5e"): print("Step 1 Success, Startlinescan row created with correct tag number")
			else: print("Row created in startlinescan with incorrect tag number: " + str(response))
		else: print("Row was not created in startlinescan")
		# 3.
		print("Step 3")
		print("SL Scan: " + 'c18590c8c575b4d9a7b5b5f8c91c01ed')
		client.publish("/timing/slscan/newscan",build_payload('c18590c8c575b4d9a7b5b5f8c91c01ed',1)) # car number 60
		time.sleep(0.5)
		# 4.1
		print("Step 4.1")
		response = run_query("select car_number from runtable where id = 2;")
		if(response is not None):
			if(response[0] == "60"): print("Step 3 Success, RunTable row created with correct car number")
			else: print("Row created in runtable with incorrect car number: " + str(response))
		else: print("Row was not created in RuntTable")
		# 4.2
		print("Step 4.2")
		response = run_query("select tag_number from startlinescan where id = 2;")
		if(response is not None):
			if(response[0] == "c18590c8c575b4d9a7b5b5f8c91c01ed"): print("Step 3 Success, Startlinescan row created with correct tag number")
			else: print("Row created in startlinescan with incorrect tag number: " + str(response))
		else: print("Row was not created in startlinescan")
		# 5.
		print("Step 5")
		print("FL Scan: " + 'c7272088434b87ff463ae128ab18ac5e')
		client.publish("/timing/flscan/newscan",build_payload('c7272088434b87ff463ae128ab18ac5e',0))
		time.sleep(0.5)
		# 6.1
		print("Step 6.1")
		response = run_query("select finishline_scan_status from runtable where id = 1;")
		if(response is not None):
			if(response[0] == "scanned_at_finish_line"): print("Step 5 Success, RunTable row updated with correct finishline_scan_status")
			else: print("Row updated in runtable with incorrect finishline_scan_status: " + str(response))
		else: print("Row was not created in RuntTable")
		# 6.2
		print("Step 6.2")
		response = run_query("select tag_number from finishlinescan where id = 1;")
		if(response is not None):
			if(response[0] == "c7272088434b87ff463ae128ab18ac5e"): print("Step 5 Success, finishlinescan row created with correct tag number")
			else: print("Row created in finishlinescan with incorrect tag number: " + str(response))
		else: print("Row was not created in finishlinescan")
		# 7.
		print("Step 7")
		insert_rawlaptime("laptimeraw",[0,"69.420"])
		fifo_runtable_row = retrieve_oldest_active_run_by_raw_time("runtable", "raw_time")
		if (fifo_runtable_row > -1):
			# We found a row, update that row with a raw time.
			row_updated = update_runtable("runtable","raw_time",str("69.420"),fifo_runtable_row)
		client.publish("/timing/laptime/newtime",build_payload_time(True,0,"69.420",str(datetime.datetime.now())))
		time.sleep(0.5)
		# 8.1
		print("Step 8.1")
		response = run_query("select raw_time from runtable where id = 1;")
		if(response is not None):
			if(response[0] == "69.420"): print("Step 7 Success, RunTable row updated with correct raw_time")
			else: print("Row updated in runtable with incorrect raw_time: " + str(response))
		else: print("Row was not created in RuntTable")
		# 8.2
		print("Step 8.2")
		response = run_query("select raw_time from laptimeraw where run_id = 1;")
		if(response is not None):
			if(response[0] == "69.420"): print("Step 7 Success, laptimeraw row created with correct raw_time")
			else: print("Row created in laptimeraw with incorrect raw_time: " + str(response))
		else: print("Row was not created in laptimeraw")
		# 9.
		print("Step 9")
		print("FL Scan: " + 'c18590c8c575b4d9a7b5b5f8c91c01ed')
		client.publish("/timing/flscan/newscan",build_payload('c18590c8c575b4d9a7b5b5f8c91c01ed',1))
		time.sleep(0.5)
		# 10.1
		print("Step 10.1")
		response = run_query("select finishline_scan_status from runtable where id = 2;")
		if(response is not None):
			if(response[0] == "scanned_at_finish_line"): print("Step 5 Success, RunTable row updated with correct finishline_scan_status")
			else: print("Row updated in runtable with incorrect finishline_scan_status: " + str(response))
		else: print("Row was not created in RuntTable")
		# 10.2
		print("Step 10.2")
		response = run_query("select tag_number from finishlinescan where id = 2;")
		if(response is not None):
			if(response[0] == "c18590c8c575b4d9a7b5b5f8c91c01ed"): print("Step 5 Success, finishlinescan row created with correct tag number")
			else: print("Row created in finishlinescan with incorrect tag number: " + str(response))
		else: print("Row was not created in finishlinescan")
		# 11.
		print("Step 11")
		insert_rawlaptime("laptimeraw",[0,"22.333"])
		fifo_runtable_row = retrieve_oldest_active_run_by_raw_time("runtable", "raw_time")
		if (fifo_runtable_row > -1):
			# We found a row, update that row with a raw time.
			row_updated = update_runtable("runtable","raw_time",str("22.333"),fifo_runtable_row)
		client.publish("/timing/laptime/newtime",build_payload_time(True,0,"22.333",str(datetime.datetime.now())))
		time.sleep(0.5)
		# 12.1
		print("Step 12.1")
		response = run_query("select raw_time from runtable where id = 2;")
		if(response is not None):
			if(response[0] == "69.420"): print("Step 7 Success, RunTable row updated with correct raw_time")
			else: print("Row updated in runtable with incorrect raw_time: " + str(response))
		else: print("Row was not created in RuntTable")
		# 12.2
		print("Step 12.2")
		response = run_query("select raw_time from laptimeraw where run_id = 2;")
		if(response is not None):
			if(response[0] == "22.333"): print("Step 7 Success, laptimeraw row created with correct raw_time")
			else: print("Row created in laptimeraw with incorrect raw_time: " + str(response))
		else: print("Row was not created in laptimeraw")
		
		print("Test 2 Complete")

		if(clear_schema is not None and clear_schema):
			print("Clearing Schema")
			clear_and_create_schema()