#/bin/python3

##################################################################
#                                                                #
#  Configuration class for Traffic Light Webcam                  #
#                                                                #
####################################### Pittsburgh Shootout LLC ##

import os

class Config:
    class MQTT:
        PORT = 1883
        USERNAME = 'username'
        PASSWORD = 'password'
        BROKER = '192.168.88.200'
        CLIENTID = 'TrafficLightWebcam'
        TESTERCLIENTID = 'TrafficLightWebcamTester'