#/bin/python3

#######################################################################################
#                                                                                     #
#  Task to read in lap time data sent from the Farmtek Timing Console.                #
#  Lap times are pushed to a database table to collect the raw input for processing.  #
#  Restarts are handled in a rudimentary manner.                                      #
#                                                                                     #
############################################################ Pittsburgh Shootout LLC ##

from config import Config
import time
import atexit
import serial					# pySerial
import serial.tools.list_ports	# pySerial
from database_helper import *

def exit_handler():
	print(' Cleaning Up!')
	ser.close()
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
				run_id SERIAL PRIMARY KEY,
				read_counter VARCHAR(255),
				raw_time  VARCHAR(255),
				created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
				updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
			)
			""".format(table_name=table_name)
		create_table(sql_cmd)

	## Check if function and trigger are present. If not, create
	function_name = "trigger_set_timestamp"
	trigger_name = "set_timestamp"
	if(not check_function_exists(function_name) and not check_trigger_exists(trigger_name)):
		print("Function or trigger do not exist, creating...")
		create_timestamp_function(function_name)
		create_timestamp_trigger(table_name, function_name)
	return True

# Config check
if Config.FARMTEK_CONSOLE_PATH == "":
	print("Console path not specified! Exiting.")
	atexit.register(exit_handler)

# Wait for device connection
port_available = False
while not(port_available):
	ports = list(serial.tools.list_ports.comports())
	print("Device not found yet")
	for p in ports:
		if (p.device == Config.FARMTEK_CONSOLE_PATH):
			port_available = True
	time.sleep(0.5)
print("Device Found")
ser = serial.Serial(Config.FARMTEK_CONSOLE_PATH, Config.FARMTEK_CONSOLE_BAUD, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, timeout=1.0)


if __name__ == '__main__':
	restartStr = "^ RESTART-IGNORE TIME ^"
	lap_time_buffer = ""
	prev_lap_time = ""
	update_db_flag = False
	run_number = 0
	table_name = "laptimeraw"

	if(not environment_check):
		print("Database Schema not correct. Exiting.")
		atexit.register(exit_handler)

	try:
		while True:
			if(ser.in_waiting > 1):
				lap_time_buffer = ser.read(ser.in_waiting).decode('ascii')
				lap_time_buffer = lap_time_buffer.replace('\x0e','').replace('\x0f','').replace('\r','').strip()
				ser.reset_input_buffer()
			else:
				lap_time_buffer = ""

			if len(lap_time_buffer) > 1:
				if lap_time_buffer == restartStr:
					# Restart pressed, next incoming time should be an UPDATE rather than an INSERT
					update_db_flag = True
				elif "(M)" in lap_time_buffer:
					if update_db_flag:
						# Manual stop button was pressed AND the restart button was pressed before that, so UPDATE prev to DNF
						# Run number isn't updated since the incorrect time already incremented the run number
						print("DB UDPATE:\t" + prev_lap_time + " to\tDNF")
						update_rawlaptime(table_name,[run_number,"DNF"])
						prev_lap_time = lap_time_buffer
						update_db_flag = False
					else:
						# Manual stop button was pressed, we need to treat this as a DNF, INSERT DNF
						run_number = run_number + 1
						print("DB INSERT:\tDNF")
						insert_rawlaptime(table_name,[run_number,"DNF"])
						prev_lap_time = "DNF"
				elif update_db_flag:
					# Restart button was pressed and this is the next value, should UPDATE the previous time
					# Run number isn't updated since the incorrect time already incremented the run number
					print("DB UDPATE:\t" + prev_lap_time + " to\t" + lap_time_buffer)
					update_rawlaptime(table_name,[run_number,lap_time_buffer])
					prev_lap_time = lap_time_buffer
					update_db_flag = False
				else:
					# Typical op, valid lap time flew in
					run_number = run_number + 1
					print("DB INSERT:\t" + lap_time_buffer)
					insert_rawlaptime(table_name,[run_number,lap_time_buffer])
					prev_lap_time = lap_time_buffer
	except KeyboardInterrupt:
		pass
	finally:	 
		atexit.register(exit_handler)