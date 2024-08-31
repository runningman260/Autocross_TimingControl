#/bin/python3

##################################################################
#                                                                #
#  TimingConsoleReader Configuration class                       #
#                                                                #
####################################### Pittsburgh Shootout LLC ##

class Config:
    class MQTT:
        PORT = 1883
        USERNAME = 'username'
        PASSWORD = 'password'
        BROKER = '192.168.2.200'
        CLIENTID = 'TimingConsoleReader'
        TESTERCLIENTID = 'TimingConsoleReader'
    
    class DB:
        HOST="192.168.2.200"
        NAME="test_scans"
        USER="nick"
        PASS="password"
    
    class FARMTEK:
        CONSOLE_PATH = '/dev/polaris'
        CONSOLE_BAUD = 9600