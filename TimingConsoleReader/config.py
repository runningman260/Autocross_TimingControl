#/bin/python3

##################################################################
#                                                                #
#  Configuration class to represent the Farmtek Timing Console.  #
#                                                                #
####################################### Pittsburgh Shootout LLC ##

import os
#from dotenv import load_dotenv
from configparser import ConfigParser

class Config:
    def load_config(filename='database.ini', section='postgresql'):
        parser = ConfigParser()
        parser.read(filename)

        # get section, default to postgresql
        config = {}
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                config[param[0]] = param[1]
        else:
            raise Exception('Section {0} not found in the {1} file'.format(section, filename))

        return config

    FARMTEK_CONSOLE_PATH = '/dev/ttyUSB98'
    FARMTEK_CONSOLE_BAUD = 9600
    # FARMTEK_CONSOLE_SYMLINK = ""
    # ^^- requires udev rule
    #SQLALCHEMY_DATABASE_URI = 'postgresql://nick:password@localhost/test_raw_lap_times'
    #ELASTICSEARCH_URL = None
    DATABASE = load_config()
    MQTTBROKER = 'localhost'
    MQTTPORT = 1883
    MQTTUSERNAME = 'username'
    MQTTPASSWORD = 'password'
    MQTTCLIENTID = 'TimingConsoleReader'
