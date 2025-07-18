#/bin/python3

##################################################################
#                                                                #
#  SchemaMgmt Configuration class                                #
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
        CLIENTID = 'SchemaMgmt'
        TESTERCLIENTID = 'SchemaMgmtTester'
    
    class DB:
        if( os.environ.get('DOCKER_HOST_IP') is not None ):
            HOST = os.environ.get('DOCKER_HOST_IP')
        else:
            HOST = 'localhost'
        NAME = os.environ.get('POSTGRES_DB', 'test_scans')
        USER = os.environ.get('POSTGRES_USER', 'nick')
        PASS = os.environ.get('POSTGRES_PASSWORD', 'password')
        TZ = os.environ.get('TZ', 'America/New_York')
