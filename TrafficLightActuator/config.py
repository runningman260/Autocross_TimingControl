#/bin/python3

##################################################################
#                                                                #
#  Configuration class for Traffic Light Actuator                #
#                                                                #
####################################### Pittsburgh Shootout LLC ##

import os

class Config:
    class MQTT:
        PORT = 1883
        USERNAME = 'username'
        PASSWORD = 'password'
        BROKER = '192.168.2.200'
        CLIENTID = 'TrafficLightActuator'
        TESTERCLIENTID = 'TrafficLightActuatorTester'