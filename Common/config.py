#/bin/python3

##################################################################
#                                                                #
#  Common Configuration class                                    #
#                                                                #
####################################### Pittsburgh Shootout LLC ##

import os
from configparser import ConfigParser
import pathlib

class Config:
    def load_config(filename=pathlib.Path(__file__).parent.absolute() / 'database.ini', section='postgresql'):
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
    
    MQTTPORT = 1883
    MQTTUSERNAME = 'username'
    MQTTPASSWORD = 'password'
    DATABASE = load_config()

    class CarRegistration:
        MQTTBROKER = 'localhost'
        MQTTCLIENTID = 'CarRegistrationListener'
        MQTTTESTERCLIENTID = 'CarRegistrationListenerTester'
    
    class SchemaMgmt:
        MQTTBROKER = 'localhost'
        MQTTCLIENTID = 'SchemaMgmt'
        MQTTTESTERCLIENTID = 'SchemaMgmtTester'
    
    class ScanListener:
        MQTTBROKER = 'localhost'
        MQTTCLIENTID = 'ScanListener'
        MQTTTESTERCLIENTID = 'ScanListenerTester'

    class RunTableTester:
        MQTTBROKER = 'localhost'
        MQTTCLIENTID = 'RunTableTester'

    class TimingConsoleReader:
        MQTTBROKER = 'localhost'
        FARMTEK_CONSOLE_PATH = '/dev/ttyUSB98'
        FARMTEK_CONSOLE_BAUD = 9600
        # FARMTEK_CONSOLE_SYMLINK = ""
        # ^^- requires udev rule
        #SQLALCHEMY_DATABASE_URI = 'postgresql://nick:password@localhost/test_raw_lap_times'
        MQTTCLIENTID = 'TimingConsoleReader'
    
    class TrafficLightActuator:
        MQTTBROKER = '192.168.2.200'
        MQTTCLIENTID = 'TrafficLightActuator'
        MQTTTESTERCLIENTID = 'TrafficLightActuatorTester'

    class TrafficLightWebcam:
        MQTTBROKER = '192.168.2.200'
        MQTTCLIENTID = 'TrafficLightWebcam'
        MQTTTESTERCLIENTID = 'TrafficLightWebcamTester'