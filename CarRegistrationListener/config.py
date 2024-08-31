#/bin/python3

##################################################################
#                                                                #
#  CarRegistrationListener Configuration class                   #
#                                                                #
####################################### Pittsburgh Shootout LLC ##

class Config:
    class MQTT:
        PORT = 1883
        USERNAME = 'username'
        PASSWORD = 'password'
        BROKER = '192.168.2.200'
        CLIENTID = 'CarRegistrationListener'
        TESTERCLIENTID = 'CarRegistrationListenerTester'
    
    class DB:
        HOST="192.168.2.200"
        NAME="test_scans"
        USER="nick"
        PASS="password"