#/bin/python3

#######################################################################################
#                                                                                     #
#  Task to generate the schema for the Shootout database.                             #
#  Includes a switch to delete all the previous information as well.                  #
#                                                                                     #
############################################################ Pittsburgh Shootout LLC ##

import os, sys
import time
import atexit
from config import Config
from database_helper import *
import paho.mqtt.client as paho
import json
import datetime

def exit_handler():
	print(' Cleaning Up!')
	exit(1)

clear_and_create_schema()

# Create Leaderboard based on Adjusted_time
print("Creating Leaderboard")
sql = """
create or replace view leaderboard as 
Select runtable.car_number, runtable.adjusted_time, carreg.team_name 
from runtable 
join carreg on runtable.car_number=carreg.car_number 
where adjusted_time is not null and adjusted_time is distinct from 'DNF' 
ORDER BY CASE WHEN pg_input_is_valid(adjusted_time, 'decimal') THEN adjusted_time::decimal END asc;
"""
create_view(sql)