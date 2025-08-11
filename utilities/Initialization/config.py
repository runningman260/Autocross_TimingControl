#/bin/python3

##################################################################
#                                                                #
#  SchemaMgmt Configuration class                                #
#                                                                #
####################################### Pittsburgh Shootout LLC ##

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '../../cloud_apps/.env'))

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
        NAME = os.getenv('POSTGRES_LIVE_DB')
        USER = os.getenv('POSTGRES_USER')
        PASS = os.getenv('POSTGRES_PASSWORD')
        TZ = os.getenv('TZ')
