#/bin/python3

##################################################################
#                                                                #
#  CarRegistrationApp Configuration class                        #
#                                                                #
####################################### Pittsburgh Shootout LLC ##

class Config:
    class MQTT:
        PORT = 1883
        USERNAME = 'username'
        PASSWORD = 'password'
        BROKER = '192.168.2.200'
        CLIENTID = 'CarRegistrationApp'