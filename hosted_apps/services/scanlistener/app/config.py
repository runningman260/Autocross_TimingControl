#/bin/python3

##################################################################
#                                                                #
#  ScanListener Configuration class                              #
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
        CLIENTID = 'ScanListener'
        TESTERCLIENTID = 'ScanListenerTester'
    
    class DB:
        if( os.environ.get('DOCKER_HOST_IP') is not None ):
            HOST = os.environ.get('DOCKER_HOST_IP')
        else:
            HOST = 'localhost'
        if(os.environ.get('POSTGRES_DB') is not None):
            NAME=os.environ.get('POSTGRES_DB')
        else:
            NAME="test_scans"
        if(os.environ.get('POSTGRES_USER') is not None):
            USER=os.environ.get('POSTGRES_USER')
        else:
            USER="nick"
        if(os.environ.get('POSTGRES_PASSWORD') is not None):
            PASS=os.environ.get('POSTGRES_PASSWORD')
        else:
            PASS="password"

