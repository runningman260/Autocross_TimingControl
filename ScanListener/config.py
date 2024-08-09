#/bin/python3

##################################################################
#                                                                #
#  Configuration class for Scan Listener                         #
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

    DATABASE = load_config()
    MQTTBROKER = 'localhost'
    MQTTPORT = 1883
    MQTTUSERNAME = 'username'
    MQTTPASSWORD = 'password'
    MQTTCLIENTID = 'ScanListener'
    MQTTTESTERCLIENTID = 'ScanListenerTester'
