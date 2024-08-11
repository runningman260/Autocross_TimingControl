#/bin/python3

##################################################################
#                                                                #
#  Configuration class for Traffic Light Actuator                #
#                                                                #
####################################### Pittsburgh Shootout LLC ##

import os

class Config:
    MQTTBROKER = '192.168.2.200'
    MQTTPORT = 1883
    MQTTUSERNAME = 'username'
    MQTTPASSWORD = 'password'
    MQTTCLIENTID = 'TrafficLightActuator'
    MQTTTESTERCLIENTID = 'TrafficLightActuatorTester'
