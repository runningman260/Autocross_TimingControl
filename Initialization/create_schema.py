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