#/bin/python3

##################################################################
#                                                                #
#  SchemaMgmt Configuration class                                #
#                                                                #
####################################### Pittsburgh Shootout LLC ##

import os

class Config:
    
    class DB:
        if( os.environ.get('DOCKER_HOST_IP') is not None ):
            HOST = os.environ.get('DOCKER_HOST_IP')
        else:
            HOST = 'localhost'
        NAME="test_scans"
        USER="nick"
        PASS="password"
