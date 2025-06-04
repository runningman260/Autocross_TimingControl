#/bin/python3

##################################################################
#                                                                #
#  TimingConsoleReader Configuration class                       #
#                                                                #
####################################### Pittsburgh Shootout LLC ##

import os

class Config:
    class MQTT:
        PORT = 1883
        USERNAME = 'username'
        PASSWORD = 'password'
        if( os.environ.get('DOCKER_HOST_IP') is not None ):
            BROKER = os.environ.get('DOCKER_HOST_IP')
        else:
            BROKER = 'localhost'
        CLIENTID = 'TimingConsoleReader'
        TESTERCLIENTID = 'TimingConsoleReader'
    
    class DB:
        if( os.environ.get('DOCKER_HOST_IP') is not None ):
            HOST = os.environ.get('DOCKER_HOST_IP')
        else:
            HOST = 'localhost'
        NAME="test_scans"
        USER="nick"
        PASS="password"
    
    class FARMTEK:
        CONSOLE_PATH = '/dev/polaris'
        CONSOLE_BAUD = 9600
